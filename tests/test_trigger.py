"""트리거 판정 테스트 — 세 조건, 판단 보류, 경계, 순서, 음수 속도 없음, 첫 표본 판정, 최소 표본 간격."""
from __future__ import annotations

import copy
import dataclasses
import itertools
import unittest
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path

from agent.config import TriggerConfig, load_config
from agent.logbook import Event, format_line
from agent.models import Verdict, VideoRecord, ViewSample
from agent.trigger import judge_trigger, views_per_hour

ROOT = Path(__file__).resolve().parent.parent
UTC = timezone.utc
KST = timezone(timedelta(hours=9))
T0 = datetime(2026, 10, 12, 3, 0, tzinfo=UTC)  # 업로드 시각
H = timedelta(hours=1)
M = timedelta(minutes=1)
S = timedelta(seconds=1)
DEFAULTS = TriggerConfig(min_views=1000, max_views=5000, max_age_hours=12.0, min_views_per_hour=150.0)
GOOD = ((2 * H, 1200), (2 * H + 30 * M, 1450))  # 2시간 30분에 1450회, 시간당 500회
REASONS = {
    ("hold", "too_few_samples"), ("no", "views_below_min"), ("no", "views_above_max"),
    ("hold", "published_in_future"), ("no", "too_old"), ("hold", "views_decreased"),
    ("no", "too_slow"), ("yes", "views_per_hour"),
}


def video(*samples, published_at=T0, detected_at=None) -> VideoRecord:
    """업로드(T0) 뒤 (경과, 조회수) 기록들로 영상 기록을 만듭니다."""
    return VideoRecord(
        video_id="abcdefghijk", channel_id="UC123", title="제목", description="",
        published_at=published_at, detected_at=detected_at or published_at, keyword="썸",
        view_history=[ViewSample(T0 + offset, count) for offset, count in samples],
    )


def judged(record, after, config=DEFAULTS) -> tuple[str, str]:
    judgement = judge_trigger(record, config, T0 + after)
    return judgement.verdict.value, judgement.reason


AT = 2 * H + 30 * M  # 따로 적지 않으면 이 시각에 판정합니다


class HoldTests(unittest.TestCase):
    def test_empty_history_is_hold(self) -> None:
        self.assertEqual(judged(video(), 1 * H), ("hold", "too_few_samples"))

    def test_single_sample_is_hold(self) -> None:
        # 업로드 시각이 그 기록 시각이면 잴 시간이 없습니다(나이 0 — 질문 3 B 뒤의 1행 보류)
        record = video((2 * H, 1450), published_at=T0 + 2 * H)
        self.assertEqual(judged(record, AT), ("hold", "too_few_samples"))

    def test_single_sample_holds_even_when_other_conditions_fail(self) -> None:
        # 나이 0 표본(잴 시간 없음)을 18시간 뒤에 판정 — 조회수 상한 · too_old 도 함께 걸립니다
        record = video((2 * H, 6000), published_at=T0 + 2 * H)
        self.assertEqual(judged(record, 20 * H), ("hold", "too_few_samples"))

    def test_same_instant_samples_count_as_one(self) -> None:
        # 같은 시각 두 기록은 한 기록 — 직전은 업로드 시각의 0, 최신은 그 시각의 큰 쪽(1450회 ÷ 2시간)
        record = video((2 * H, 1200), (2 * H, 1450))
        at_725 = dataclasses.replace(DEFAULTS, min_views_per_hour=725.0)
        at_726 = dataclasses.replace(DEFAULTS, min_views_per_hour=726.0)
        self.assertEqual(judged(record, AT, at_725), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, AT, at_726), ("no", "too_slow"))

    def test_decrease_is_hold(self) -> None:
        record = video((2 * H, 1450), (2 * H + 30 * M, 1300))
        self.assertEqual(judged(record, AT), ("hold", "views_decreased"))

    def test_decrease_holds_even_with_zero_min_rate(self) -> None:
        record = video((2 * H, 1450), (2 * H + 30 * M, 1300))
        config = dataclasses.replace(DEFAULTS, min_views_per_hour=0.0)
        self.assertEqual(judged(record, AT, config), ("hold", "views_decreased"))

    def test_future_published_at_is_hold(self) -> None:
        record = video(*GOOD, published_at=T0 + 2 * H + 31 * M)
        self.assertEqual(judged(record, AT), ("hold", "published_in_future"))


class NoTests(unittest.TestCase):
    def test_below_min_views(self) -> None:
        record = video((2 * H, 900), (2 * H + 30 * M, 999))
        self.assertEqual(judged(record, AT), ("no", "views_below_min"))

    def test_above_max_views(self) -> None:
        record = video((2 * H, 4900), (2 * H + 30 * M, 5001))
        self.assertEqual(judged(record, AT), ("no", "views_above_max"))

    def test_too_old(self) -> None:
        record = video((11 * H + 30 * M, 1200), (12 * H, 1450))
        self.assertEqual(judged(record, 12 * H + S), ("no", "too_old"))

    def test_too_slow(self) -> None:
        record = video((2 * H, 1200), (2 * H + 30 * M, 1274))  # 시간당 148회
        self.assertEqual(judged(record, AT), ("no", "too_slow"))

    def test_flat_count_is_too_slow(self) -> None:
        record = video((2 * H, 1450), (2 * H + 30 * M, 1450))
        self.assertEqual(judged(record, AT), ("no", "too_slow"))

    def test_views_checked_before_age(self) -> None:
        old = video((19 * H + 30 * M, 900), (20 * H, 999))
        self.assertEqual(judged(old, 20 * H), ("no", "views_below_min"))
        future = video((2 * H, 900), (2 * H + 30 * M, 999), published_at=T0 + 3 * H)
        self.assertEqual(judged(future, AT), ("no", "views_below_min"))

    def test_age_checked_before_decrease_and_speed(self) -> None:
        decreased = video((19 * H + 30 * M, 1450), (20 * H, 1300))
        self.assertEqual(judged(decreased, 20 * H), ("no", "too_old"))
        slow = video((19 * H + 30 * M, 1200), (20 * H, 1274))
        self.assertEqual(judged(slow, 20 * H), ("no", "too_old"))

    def test_age_counts_from_published_not_detected(self) -> None:
        record = video((11 * H + 30 * M, 1200), (12 * H, 1450), detected_at=T0 + 11 * H)
        self.assertEqual(judged(record, 12 * H + S), ("no", "too_old"))


class YesTests(unittest.TestCase):
    """경계는 모두 통과입니다."""

    def test_all_three_met(self) -> None:
        self.assertEqual(judged(video(*GOOD), AT), ("yes", "views_per_hour"))

    def test_min_views_bound_is_inclusive(self) -> None:
        record = video((2 * H, 900), (2 * H + 30 * M, 1000))
        self.assertEqual(judged(record, AT), ("yes", "views_per_hour"))

    def test_max_views_bound_is_inclusive(self) -> None:
        record = video((2 * H, 4800), (2 * H + 30 * M, 5000))
        self.assertEqual(judged(record, AT), ("yes", "views_per_hour"))

    def test_age_bound_is_inclusive(self) -> None:
        record = video((11 * H + 30 * M, 1200), (12 * H, 1450))
        self.assertEqual(judged(record, 12 * H), ("yes", "views_per_hour"))

    def test_rate_bound_is_inclusive(self) -> None:
        record = video((2 * H, 1200), (2 * H + 30 * M, 1275))  # 시간당 정확히 150회
        self.assertEqual(judged(record, AT), ("yes", "views_per_hour"))

    def test_flat_count_meets_zero_min_rate(self) -> None:
        record = video((2 * H, 1450), (2 * H + 30 * M, 1450))
        config = dataclasses.replace(DEFAULTS, min_views_per_hour=0.0)
        self.assertEqual(judged(record, AT, config), ("yes", "views_per_hour"))

    def test_published_exactly_now_passes_age(self) -> None:
        record = video(*GOOD, published_at=T0 + 2 * H + 30 * M)
        self.assertEqual(judged(record, AT), ("yes", "views_per_hour"))

    def test_single_value_range(self) -> None:
        config = TriggerConfig(1450, 1450, 12.0, 150.0)
        self.assertEqual(judged(video(*GOOD), AT, config), ("yes", "views_per_hour"))

    def test_contract_example_record_is_yes(self) -> None:
        record = video(
            (0 * H, 1200), (30 * M, 1450), published_at=datetime(2026, 10, 11, 23, 0, tzinfo=UTC)
        )
        self.assertEqual(judged(record, 30 * M), ("yes", "views_per_hour"))


class OrderTests(unittest.TestCase):
    def test_list_order_does_not_matter(self) -> None:
        samples = [(1 * H, 1000), (2 * H, 1200), (2 * H + 30 * M, 1440), (2 * H + 30 * M, 1450)]
        at_500 = dataclasses.replace(DEFAULTS, min_views_per_hour=500.0)
        at_501 = dataclasses.replace(DEFAULTS, min_views_per_hour=501.0)
        for order in itertools.permutations(samples):
            with self.subTest(order=order):
                record = video(*order)
                self.assertEqual(judged(record, AT, at_500), ("yes", "views_per_hour"))
                self.assertEqual(judged(record, AT, at_501), ("no", "too_slow"))

    def test_order_is_by_instant_across_time_zones(self) -> None:
        rec = video()
        rec.view_history = [
            ViewSample(T0 + 30 * M, 1450),
            ViewSample(datetime(2026, 10, 12, 12, 0, tzinfo=KST), 1200),  # 03:00Z
        ]
        self.assertEqual(judged(rec, 30 * M), ("yes", "views_per_hour"))


class SpeedTests(unittest.TestCase):
    def test_rate_uses_latest_two_samples(self) -> None:
        record = video((1 * H, 1000), (2 * H, 1100), (2 * H + 30 * M, 1450))
        at_699 = dataclasses.replace(DEFAULTS, min_views_per_hour=699.0)
        at_701 = dataclasses.replace(DEFAULTS, min_views_per_hour=701.0)
        self.assertEqual(judged(record, AT, at_699), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, AT, at_701), ("no", "too_slow"))

    def test_short_gap_after_restart_skips_to_earlier_sample(self) -> None:
        # 20초 사이 1회(시간당 180)가 아니라 30분 20초 앞의 기록과 잽니다 — 1회 ÷ 30분 20초
        last = 2 * H + 30 * M + 20 * S
        record = video((2 * H, 1200), (2 * H + 30 * M, 1200), (last, 1201))
        self.assertEqual(judged(record, last), ("no", "too_slow"))
        self.assertEqual(views_per_hour(record), 3600 / 1820)

    def test_rate_never_negative_over_generated_pairs(self) -> None:
        counts = (0, 1, 999, 1000, 1450, 5000, 5001)
        offsets = ((1 * H, 2 * H), (2 * H, 2 * H + 30 * M), (1 * H, 2 * H + 30 * M))
        speed_only = TriggerConfig(0, 10**9, 12.0, 0.0)
        for earlier_count, later_count in itertools.product(counts, repeat=2):
            for earlier_at, later_at in offsets:
                pair = ((earlier_at, earlier_count), (later_at, later_count))
                for samples in (pair, pair[::-1]):
                    with self.subTest(samples=samples):
                        record = video(*samples)
                        expected = (
                            ("hold", "views_decreased")
                            if later_count < earlier_count
                            else ("yes", "views_per_hour")
                        )
                        self.assertEqual(judged(record, later_at, speed_only), expected)
                        self.assertIn(judged(record, later_at), REASONS)


class ConfigTests(unittest.TestCase):
    def test_each_threshold_comes_from_config(self) -> None:
        record = video(*GOOD)
        self.assertEqual(judged(record, AT), ("yes", "views_per_hour"))
        variants = (
            ({"min_views": 1451}, ("no", "views_below_min")),
            ({"max_views": 1449}, ("no", "views_above_max")),
            ({"max_age_hours": 2.0}, ("no", "too_old")),
            ({"min_views_per_hour": 501.0}, ("no", "too_slow")),
        )
        for change, expected in variants:
            with self.subTest(change=change):
                config = dataclasses.replace(DEFAULTS, **change)
                self.assertEqual(judged(record, AT, config), expected)

    def test_shipped_config_is_assignment_values(self) -> None:
        shipped = load_config(ROOT / "config.yaml").trigger
        self.assertEqual(shipped, DEFAULTS)
        self.assertEqual(judged(video(*GOOD), AT, shipped), ("yes", "views_per_hour"))


class ContractTests(unittest.TestCase):
    def test_judgement_at_is_now(self) -> None:
        judgement = judge_trigger(video(*GOOD), DEFAULTS, T0 + 2 * H + 30 * M)
        self.assertIs(judgement.verdict, Verdict.YES)
        self.assertEqual(judgement.at, T0 + 2 * H + 30 * M)

    def test_judgement_at_is_now_when_later_than_latest_sample(self) -> None:
        judgement = judge_trigger(video(*GOOD), DEFAULTS, T0 + 3 * H)
        self.assertIs(judgement.verdict, Verdict.YES)
        self.assertEqual(judgement.at, T0 + 3 * H)

    def test_same_input_same_judgement(self) -> None:
        now = T0 + AT
        first = judge_trigger(video(*GOOD), DEFAULTS, now)
        second = judge_trigger(video(*GOOD), DEFAULTS, now)
        self.assertEqual(first, second)

    def test_record_is_not_changed(self) -> None:
        rec = video(*GOOD)
        before = copy.deepcopy(rec)
        judge_trigger(rec, DEFAULTS, T0 + AT)
        self.assertEqual(rec, before)
        self.assertIsNone(rec.trigger)
        shuffled = video((2 * H + 30 * M, 1450), (2 * H, 1200))
        before = copy.deepcopy(shuffled)
        judge_trigger(shuffled, DEFAULTS, T0 + AT)
        self.assertEqual(shuffled, before)

    def test_earlier_sample_is_the_largest_at_the_previous_instant(self) -> None:
        record = video((2 * H, 1200), (2 * H, 1300), (2 * H + 30 * M, 1450))
        at_300 = dataclasses.replace(DEFAULTS, min_views_per_hour=300.0)
        at_301 = dataclasses.replace(DEFAULTS, min_views_per_hour=301.0)
        self.assertEqual(judged(record, AT, at_300), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, AT, at_301), ("no", "too_slow"))

    def test_rate_is_not_floored(self) -> None:
        record = video((1 * H, 1000), (11 * H, 2505))  # 시간당 150.5회
        at_150_5 = dataclasses.replace(DEFAULTS, min_views_per_hour=150.5)
        at_150_6 = dataclasses.replace(DEFAULTS, min_views_per_hour=150.6)
        self.assertEqual(judged(record, 11 * H, at_150_5), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, 11 * H, at_150_6), ("no", "too_slow"))

    def test_naive_now_is_rejected(self) -> None:
        now = datetime(2026, 10, 12, 5, 30)
        for record in (video(*GOOD), video()):
            with self.subTest(record=record):
                with self.assertRaisesRegex(ValueError, "now 에 시간대가 없습니다"):
                    judge_trigger(record, DEFAULTS, now)

    def test_every_reason_logs_unquoted(self) -> None:
        scenarios = (
            (video((2 * H, 1450), published_at=T0 + 2 * H), AT),
            (video((2 * H, 900), (2 * H + 30 * M, 999)), AT),
            (video((2 * H, 4900), (2 * H + 30 * M, 5001)), AT),
            (video(*GOOD, published_at=T0 + 2 * H + 31 * M), AT),
            (video((11 * H + 30 * M, 1200), (12 * H, 1450)), 12 * H + S),
            (video((2 * H, 1450), (2 * H + 30 * M, 1300)), AT),
            (video((2 * H, 1200), (2 * H + 30 * M, 1274)), AT),
            (video(*GOOD), AT),
        )
        seen = set()
        for rec, after in scenarios:
            now = T0 + after
            j = judge_trigger(rec, DEFAULTS, now)
            verdict, reason = j.verdict.value, j.reason
            seen.add((verdict, reason))
            with self.subTest(verdict=verdict, reason=reason):
                self.assertEqual(j.at, now)
                fields ={"video": rec.video_id, "verdict": j.verdict, "reason": j.reason}
                line = format_line(now, Event.TRIGGER, fields)
                self.assertTrue(line.endswith(f"verdict={verdict} reason={reason}"), line)
        self.assertEqual(seen, REASONS)


class TestFirstSample(unittest.TestCase):
    """최신보다 10분 이상 앞선 기록이 없으면 업로드 시각의 조회수 0 을 직전 기록으로 칩니다(2026-10-15 질문 3 B)."""

    def test_single_sample_judged_from_upload_zero(self) -> None:
        record = video((2 * H, 2000))  # 업로드 2시간 뒤 2000회 — 시간당 1000회
        self.assertEqual(judged(record, 2 * H), ("yes", "views_per_hour"))
        self.assertEqual(views_per_hour(record), 1000.0)
        at_1000 = dataclasses.replace(DEFAULTS, min_views_per_hour=1000.0)
        at_1001 = dataclasses.replace(DEFAULTS, min_views_per_hour=1001.0)
        self.assertEqual(judged(record, 2 * H, at_1000), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, 2 * H, at_1001), ("no", "too_slow"))

    def test_single_sample_slow_is_too_slow(self) -> None:
        record = video((10 * H, 1200))  # 시간당 120회
        self.assertEqual(judged(record, 10 * H), ("no", "too_slow"))
        self.assertEqual(views_per_hour(record), 120.0)

    def test_age_zero_single_sample_holds_too_few_samples(self) -> None:
        # 업로드 시각 = 기록 시각 = 지금 — 0 으로 나누지 않고 보류합니다
        record = video((2 * H, 2000), published_at=T0 + 2 * H)
        self.assertEqual(judged(record, 2 * H), ("hold", "too_few_samples"))
        self.assertIsNone(views_per_hour(record))

    def test_future_upload_single_sample_holds_too_few_samples(self) -> None:
        # 업로드 시각이 그 기록보다 뒤 — 표의 1행이 '미래 업로드' 행보다 앞입니다
        record = video((2 * H, 2000), published_at=T0 + 2 * H + M)
        self.assertEqual(judged(record, 2 * H), ("hold", "too_few_samples"))
        self.assertIsNone(views_per_hour(record))

    def test_empty_history_holds_too_few_samples(self) -> None:
        record = video()
        self.assertEqual(judged(record, 2 * H), ("hold", "too_few_samples"))
        self.assertIsNone(views_per_hour(record))

    def test_same_instant_samples_use_upload_zero(self) -> None:
        record = video((2 * H, 1450), (2 * H, 1200))
        self.assertEqual(judged(record, AT), ("yes", "views_per_hour"))
        self.assertEqual(views_per_hour(record), 725.0)

    def test_two_samples_ignore_upload_zero(self) -> None:
        # 업로드 뒤 평균이면 시간당 509.6회지만, 시각이 다른 두 기록 사이는 148회입니다
        record = video((2 * H, 1200), (2 * H + 30 * M, 1274))
        self.assertEqual(judged(record, AT), ("no", "too_slow"))
        self.assertEqual(views_per_hour(record), 148.0)

    def test_views_per_hour_matches_judgement_pair(self) -> None:
        records = (
            video((2 * H, 2000)),
            video((2 * H, 1200), (2 * H, 1450)),
            video(*GOOD),
            video((1 * H, 1000), (2 * H, 1100), (2 * H + 30 * M, 1450)),
            video((2 * H + 30 * M, 1450), (2 * H, 1200)),
            video((1 * H - 20 * S, 1180), (1 * H, 1200)),
            video((2 * H, 1200), (2 * H + 25 * M, 1500), (2 * H + 30 * M, 1450)),
        )
        for record in records:
            with self.subTest(record=record.view_history):
                rate = views_per_hour(record)
                self.assertIsNotNone(rate)
                at_rate = dataclasses.replace(DEFAULTS, min_views_per_hour=rate)
                above = dataclasses.replace(DEFAULTS, min_views_per_hour=rate + 1.0)
                self.assertEqual(judged(record, AT, at_rate), ("yes", "views_per_hour"))
                self.assertEqual(judged(record, AT, above), ("no", "too_slow"))

    def test_views_per_hour_none_when_unmeasurable(self) -> None:
        records = {
            "empty": video(),
            "age_zero": video((2 * H, 2000), published_at=T0 + 2 * H),
            "decreased": video((2 * H, 1450), (2 * H + 30 * M, 1300)),
        }
        for label, record in records.items():
            with self.subTest(label):
                self.assertIsNone(views_per_hour(record))


class TestJudgementStability(unittest.TestCase):
    """판정이 바뀔 수 있나 — 계약 '트리거 판정' 절의 고친 문장(2026-10-15 질문 5 A)."""

    def test_closed_window_never_yes_even_with_more_samples(self) -> None:
        # 13시간 · 800회 영상 — 기록을 더해도 yes 가 아닙니다
        rising = ((13 * H, 800), (14 * H, 1200), (15 * H, 2500), (16 * H, 4000))
        verdicts = []
        for count in range(1, len(rising) + 1):
            samples = rising[:count]
            verdicts.append(judged(video(*samples), samples[-1][0]))
        self.assertEqual(
            verdicts,
            [("no", "views_below_min"), ("no", "too_old"), ("no", "too_old"), ("no", "too_old")],
        )
        self.assertEqual(judged(video((13 * H, 6000)), 13 * H), ("no", "views_above_max"))

    def test_decreased_below_min_is_no_views_below_min(self) -> None:
        record = video((2 * H, 1200), (2 * H + 30 * M, 900))
        self.assertEqual(judged(record, AT), ("no", "views_below_min"))

    def test_raising_max_age_hours_reopens_too_old(self) -> None:
        record = video((12 * H, 1200), (13 * H, 1450))  # 시간당 250회, 13시간
        self.assertEqual(judged(record, 13 * H), ("no", "too_old"))
        wider = dataclasses.replace(DEFAULTS, max_age_hours=14.0)
        self.assertEqual(judged(record, 13 * H, wider), ("yes", "views_per_hour"))

    def test_decreased_views_verdict_by_row(self) -> None:
        any_rate = dataclasses.replace(DEFAULTS, min_views_per_hour=0.0)
        rows = (
            ("in_range_in_window", ((2 * H, 1450), (2 * H + 30 * M, 1300)), AT,
             ("hold", "views_decreased")),
            ("below_min", ((2 * H, 1450), (2 * H + 30 * M, 999)), AT,
             ("no", "views_below_min")),
            ("above_max", ((2 * H, 6000), (2 * H + 30 * M, 5001)), AT,
             ("no", "views_above_max")),
            ("in_range_after_window", ((19 * H + 30 * M, 1450), (20 * H, 1300)), 20 * H,
             ("no", "too_old")),
        )
        for label, samples, after, expected in rows:
            with self.subTest(label):
                self.assertEqual(judged(video(*samples), after, any_rate), expected)

    def test_second_judgement_uses_latest_pair_not_first_sample_average(self) -> None:
        # 100 → 1100 → 1200 (한 시간 간격) — 첫 기록부터의 평균(550)이나 업로드 뒤 평균(400)이 아니라 100
        samples = ((1 * H, 100), (2 * H, 1100), (3 * H, 1200))
        record = video(*samples)
        self.assertEqual(judged(record, 3 * H), ("no", "too_slow"))
        self.assertEqual(views_per_hour(record), 100.0)


class TestMinimumGap(unittest.TestCase):
    """최소 표본 간격 10분 — 최신보다 10분 이상 앞선 가장 늦은 기록과 잽니다(트래커 Phase 7G 질문 1 A · 2 A)."""

    def test_gap_of_exactly_ten_minutes_is_used(self) -> None:
        record = video((50 * M, 1200), (1 * H, 1250))
        at_300 = dataclasses.replace(DEFAULTS, min_views_per_hour=300.0)
        at_301 = dataclasses.replace(DEFAULTS, min_views_per_hour=301.0)
        self.assertEqual(views_per_hour(record), 300.0)
        self.assertEqual(judged(record, 1 * H, at_300), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, 1 * H, at_301), ("no", "too_slow"))

    def test_gap_one_second_short_skips_to_upload_zero(self) -> None:
        record = video((50 * M + S, 1200), (1 * H, 1250))
        at_1250 = dataclasses.replace(DEFAULTS, min_views_per_hour=1250.0)
        at_1251 = dataclasses.replace(DEFAULTS, min_views_per_hour=1251.0)
        self.assertEqual(views_per_hour(record), 1250.0)
        self.assertEqual(judged(record, 1 * H, at_1250), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, 1 * H, at_1251), ("no", "too_slow"))

    def test_restart_with_no_far_sample_uses_upload_zero(self) -> None:
        record = video((1 * H - 20 * S, 1180), (1 * H, 1200))
        at_1200 = dataclasses.replace(DEFAULTS, min_views_per_hour=1200.0)
        at_1201 = dataclasses.replace(DEFAULTS, min_views_per_hour=1201.0)
        self.assertEqual(views_per_hour(record), 1200.0)
        self.assertEqual(judged(record, 1 * H, at_1200), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, 1 * H, at_1201), ("no", "too_slow"))

    def test_skips_near_sample_and_uses_latest_far_enough(self) -> None:
        record = video(
            (1 * H, 1000), (2 * H, 1100), (2 * H + 25 * M, 1400), (2 * H + 30 * M, 1450)
        )
        at_700 = dataclasses.replace(DEFAULTS, min_views_per_hour=700.0)
        at_701 = dataclasses.replace(DEFAULTS, min_views_per_hour=701.0)
        self.assertEqual(views_per_hour(record), 700.0)
        self.assertEqual(judged(record, AT, at_700), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, AT, at_701), ("no", "too_slow"))

    def test_decrease_is_seen_on_the_measured_pair_only(self) -> None:
        with self.subTest("skipped_higher"):
            record = video((2 * H, 1200), (2 * H + 25 * M, 1500), (2 * H + 30 * M, 1450))
            self.assertEqual(judged(record, AT), ("yes", "views_per_hour"))
            self.assertEqual(views_per_hour(record), 500.0)
        with self.subTest("measured_lower"):
            record = video((2 * H, 1500), (2 * H + 25 * M, 1400), (2 * H + 30 * M, 1450))
            self.assertEqual(judged(record, AT), ("hold", "views_decreased"))
            self.assertIsNone(views_per_hour(record))

    def test_skipped_near_sample_is_not_used_as_latest_on_the_upload_zero_path(self) -> None:
        # 5분 앞선 더 큰 기록(1500)은 건너뜀 — 업로드 0 과 최신(1450 · 65분)으로 잽니다
        record = video((1 * H, 1500), (1 * H + 5 * M, 1450))
        at_1338 = dataclasses.replace(DEFAULTS, min_views_per_hour=1338.0)
        at_1339 = dataclasses.replace(DEFAULTS, min_views_per_hour=1339.0)
        self.assertEqual(views_per_hour(record), 1450 * 60 / 65)
        self.assertEqual(judged(record, 1 * H + 5 * M, at_1338), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, 1 * H + 5 * M, at_1339), ("no", "too_slow"))

    def test_upload_zero_side_has_no_gap(self) -> None:
        record = video((1 * M, 1100))
        self.assertEqual(judged(record, 1 * M), ("yes", "views_per_hour"))
        self.assertEqual(views_per_hour(record), 66000.0)

    def test_gap_is_measured_by_instant_across_time_zones(self) -> None:
        with self.subTest("exact"):
            rec = video()
            rec.view_history = [
                ViewSample(T0 + 50 * M, 1200),
                ViewSample(datetime(2026, 10, 12, 13, 0, tzinfo=KST), 1250),  # T0 + 1시간
            ]
            self.assertEqual(views_per_hour(rec), 300.0)
        with self.subTest("one_second_short"):
            rec = video()
            rec.view_history = [
                ViewSample(datetime(2026, 10, 12, 12, 50, 1, tzinfo=KST), 1200),
                ViewSample(T0 + 1 * H, 1250),
            ]
            self.assertEqual(views_per_hour(rec), 1250.0)


class _NewYork(tzinfo):
    """2026년 뉴욕 — 3월 8일 02시에 한 시간을 건너뛰고, 11월 1일 01시대를 두 번 지납니다.

    tzdata 없이도(Windows) 돌도록 손으로 적었습니다. fold=1 은 두 번째 01시대입니다.
    """

    def utcoffset(self, dt: datetime) -> timedelta:
        wall = dt.replace(tzinfo=None)
        if datetime(2026, 3, 8, 2) <= wall < datetime(2026, 11, 1, 2):
            if dt.fold == 1 and wall >= datetime(2026, 11, 1, 1):
                return -5 * H
            return -4 * H
        return -5 * H

    def dst(self, dt: datetime) -> None:
        return None

    def tzname(self, dt: datetime) -> None:
        return None


NY = _NewYork()  # 모든 시각이 같은 시간대 객체를 씁니다 — 그래야 벽시계 비교가 드러납니다


def ny_video(published_at, *samples) -> VideoRecord:
    """뉴욕 시각 (시각, 조회수) 기록들로 영상 기록을 만듭니다."""
    return VideoRecord(
        video_id="abcdefghijk", channel_id="UC123", title="제목", description="",
        published_at=published_at, detected_at=published_at, keyword="썸",
        view_history=[ViewSample(at, count) for at, count in samples],
    )


class InstantTests(unittest.TestCase):
    """같은 시간대 객체끼리도 벽시계가 아니라 순간으로 비교합니다."""

    def judged_at(self, record, now, config=DEFAULTS) -> tuple[str, str]:
        judgement = judge_trigger(record, config, now)
        self.assertIs(judgement.at, now)
        return judgement.verdict.value, judgement.reason

    def test_fall_overlap_samples_are_an_hour_apart(self) -> None:
        samples = (
            (datetime(2026, 11, 1, 1, 30, tzinfo=NY), 1200),  # 05:30Z
            (datetime(2026, 11, 1, 1, 30, fold=1, tzinfo=NY), 1650),  # 06:30Z, 시간당 450회
        )
        published = datetime(2026, 11, 1, 0, 0, tzinfo=NY)
        now = datetime(2026, 11, 1, 1, 45, fold=1, tzinfo=NY)
        for order in (samples, samples[::-1]):
            with self.subTest(order=order):
                record = ny_video(published, *order)
                self.assertEqual(self.judged_at(record, now), ("yes", "views_per_hour"))

    def test_spring_skip_rate_is_over_the_real_hour(self) -> None:
        record = ny_video(
            datetime(2026, 3, 8, 0, 0, tzinfo=NY),
            (datetime(2026, 3, 8, 1, 30, tzinfo=NY), 1200),  # 06:30Z
            (datetime(2026, 3, 8, 3, 30, tzinfo=NY), 1400),  # 07:30Z, 시간당 200회
        )
        now = datetime(2026, 3, 8, 3, 30, tzinfo=NY)
        self.assertEqual(self.judged_at(record, now), ("yes", "views_per_hour"))

    def test_spring_skip_age_is_the_real_age(self) -> None:
        record = ny_video(
            datetime(2026, 3, 8, 0, 0, tzinfo=NY),  # 05:00Z, 실제 나이 2시간 30분
            (datetime(2026, 3, 8, 1, 30, tzinfo=NY), 1200),
            (datetime(2026, 3, 8, 3, 30, tzinfo=NY), 1400),
        )
        now = datetime(2026, 3, 8, 3, 30, tzinfo=NY)
        config = dataclasses.replace(DEFAULTS, max_age_hours=3.0)
        self.assertEqual(self.judged_at(record, now, config), ("yes", "views_per_hour"))

    def test_spring_skip_gap_is_the_real_five_minutes(self) -> None:
        # 벽시계로는 65분이지만 실제 간격은 5분 — 건너뛰고 업로드 0 과 잽니다(1250회 ÷ 2시간)
        record = ny_video(
            datetime(2026, 3, 8, 0, 0, tzinfo=NY),
            (datetime(2026, 3, 8, 1, 55, tzinfo=NY), 1200),
            (datetime(2026, 3, 8, 3, 0, tzinfo=NY), 1250),
        )
        now = datetime(2026, 3, 8, 3, 0, tzinfo=NY)
        at_625 = dataclasses.replace(DEFAULTS, min_views_per_hour=625.0)
        at_626 = dataclasses.replace(DEFAULTS, min_views_per_hour=626.0)
        self.assertEqual(views_per_hour(record), 625.0)
        self.assertEqual(self.judged_at(record, now, at_625), ("yes", "views_per_hour"))
        self.assertEqual(self.judged_at(record, now, at_626), ("no", "too_slow"))

    def test_fall_publish_before_now_is_not_future(self) -> None:
        record = ny_video(
            datetime(2026, 11, 1, 1, 50, tzinfo=NY),  # 05:50Z, 지금보다 50분 전
            (datetime(2026, 11, 1, 1, 20, tzinfo=NY), 1200),  # 05:20Z
            (datetime(2026, 11, 1, 1, 40, fold=1, tzinfo=NY), 1700),  # 06:40Z
        )
        now = datetime(2026, 11, 1, 1, 40, fold=1, tzinfo=NY)
        self.assertEqual(self.judged_at(record, now), ("yes", "views_per_hour"))


if __name__ == "__main__":
    unittest.main()
