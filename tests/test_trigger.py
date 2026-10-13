"""트리거 판정 테스트 — 세 조건, 판단 보류, 경계, 순서, 음수 속도 없음."""
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
from agent.trigger import judge_trigger

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
        self.assertEqual(judged(video((2 * H, 1450)), AT), ("hold", "too_few_samples"))

    def test_single_sample_holds_even_when_other_conditions_fail(self) -> None:
        self.assertEqual(judged(video((20 * H, 6000)), 20 * H), ("hold", "too_few_samples"))

    def test_same_instant_samples_count_as_one(self) -> None:
        record = video((2 * H, 1200), (2 * H, 1450))
        self.assertEqual(judged(record, AT), ("hold", "too_few_samples"))

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

    def test_short_gap_after_restart_is_measured_as_is(self) -> None:
        last = 2 * H + 30 * M + 20 * S
        record = video((2 * H, 1200), (2 * H + 30 * M, 1200), (last, 1201))
        at_180 = dataclasses.replace(DEFAULTS, min_views_per_hour=180.0)
        at_181 = dataclasses.replace(DEFAULTS, min_views_per_hour=181.0)
        self.assertEqual(judged(record, last), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, last, at_180), ("yes", "views_per_hour"))
        self.assertEqual(judged(record, last, at_181), ("no", "too_slow"))

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
            (video((2 * H, 1450)), AT),
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
