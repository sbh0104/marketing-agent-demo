"""결과 화면 테스트 — report.py 가 저장소와 로그만 읽고, 로그의 이유는 이름표로만 옮기는지.

계약 '결과 화면 — `report.py` (Phase 7D)' 절. 표시 글 mark() 는 `<script>` · `"` · `&` 를 담아 화면에
날 글자로 나오면 바로 보이고, `~` 로 끝나 어느 표시도 다른 표시의 일부가 되지 않습니다.
"""
from __future__ import annotations

import html
import os
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import agent.run as run
from agent.guard import decide_post
from agent.logbook import REQUIRED_FIELDS, Event, format_line, parse_line
from agent.models import CommentDraft, Judgement, PostAttempt, Verdict, VideoRecord, ViewSample
from agent.poster import DRY_RUN, NO_COMMENT, WATCH_URL
from agent.report import (
    FAILED,
    LOG_UNREADABLE,
    NO_DRAFT,
    NO_POST,
    NOT_JUDGED,
    NOT_TIMED,
    OTHER,
    POSTED,
    REASON_LABELS,
    REASON_PREFIXES,
    REHEARSED,
    RESERVED,
    WHERE_LABELS,
    LogLine,
    badges,
    judge_of,
    late_lines,
    reason_label,
    render_report,
    where_label,
    write_report,
)
from agent.trigger import views_per_hour
from agent.writer import NO_CONCERN, NO_SCENE

T = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
S = timedelta(seconds=1)
HOUR = timedelta(hours=1)
MS = timedelta(milliseconds=1)
A = "AAAAAAAAAAA"
B = "BBBBBBBBBBB"
C = "CCCCCCCCCCC"
D = "DDDDDDDDDDD"
START = {"mode": "test", "allowed": 1, "interval_min": 120}
JUDGED = Judgement(Verdict.YES, "연애 고민 상담", T)
WARNING = (
    '<p class="warning">로그를 읽지 못해 이유 배지 · 리허설 · 판단한 쪽 칸을 채우지 못했습니다'
    " — logs/agent.log 의 ERROR where=report 줄을 보세요.</p>"
)


def mark(field: str) -> str:
    """표시 글 — 화면에 나오면 이스케이프된 꼴로만 나와야 합니다."""
    return f'<script>"&MRK-{field}~'


def record(video_id: str, **parts: object) -> VideoRecord:
    """영상 기록 하나 — parts 로 바꾸지 않은 칸은 평범한 값입니다."""
    fields: dict[str, object] = {
        "channel_id": "UC1",
        "title": f"연애 고민 {video_id}",
        "description": "설명",
        "published_at": T - 2 * HOUR,
        "detected_at": T,
        "keyword": "연애",
    }
    fields.update(parts)
    return VideoRecord(video_id=video_id, **fields)


def drafted(at: datetime) -> CommentDraft:
    return CommentDraft("썸 상대의 답장이 늦어 불안한 마음", "답장 늦는 장면에 뜨끔했어요.", at)


def attempt(at: datetime, mode: str, result: str, reason: str) -> PostAttempt:
    return PostAttempt(at, mode, result, reason)


def line(at: datetime, event: Event, **fields: object) -> LogLine:
    """진짜 로그 모양의 줄 — format_line 으로 쓰고 parse_line 으로 되읽습니다(시각은 초 단위)."""
    return parse_line(format_line(at, event, fields))


def rehearsal(
    at: datetime, video_id: str = A, *, reason: str = DRY_RUN, **extra: object
) -> LogLine:
    """poster 의 리허설 줄 모양 — POST mode=test result=rehearsed."""
    return line(
        at, Event.POST, video=video_id, mode="test", result="rehearsed", reason=reason, **extra
    )


def row(page: str, video_id: str) -> str:
    match = re.search(rf'<tr id="v-{video_id}">.*?</tr>', page)
    if match is None:
        raise AssertionError(f"영상 줄이 없습니다: {video_id}")
    return match.group()


def cells(row_text: str) -> list[str]:
    """한 줄의 칸 일곱 — 영상 · 판별 · 판단한 쪽 · 타이밍 · 고민 · 댓글 · 게시 결과."""
    return re.findall(r"<td>(.*?)</td>", row_text)


def scene() -> tuple[list[VideoRecord], list[LogLine]]:
    """평범한 화면 하나 — 게시된 A, 저장만 한 B, 리허설한 C, 작성을 건너뛴 D."""
    records = [
        record(
            A,
            classification=JUDGED,
            comment=drafted(T + S),
            attempts=[attempt(T + 2 * S, "live", "posted", "allowlisted")],
        ),
        record(
            B,
            detected_at=T + S,
            classification=JUDGED,
            comment=drafted(T + S),
            attempts=[attempt(T + 3 * S, "test", "saved", "not_in_allowlist")],
        ),
        record(C, detected_at=T + 2 * S, classification=JUDGED, comment=drafted(T + S)),
        record(D, detected_at=T + 3 * S, classification=JUDGED),
    ]
    events = [
        line(T, Event.START, judge="jev", **START),
        *(
            line(T, Event.CLASSIFY, video=v, verdict="yes", reason="연애 고민 상담")
            for v in (A, B, C, D)
        ),
        rehearsal(T + 4 * S, C),
        line(T + 5 * S, Event.SKIP, video=D, reason=f"{NO_SCENE} — 1차: 답을 읽을 수 없습니다"),
        line(T + 6 * S, Event.SKIP, video=B, reason="duplicate_video"),
        line(T + 7 * S, Event.CYCLE, n=1),
    ]
    return records, events


class TestLabels(unittest.TestCase):
    """이름표 목록 — 정해 둔 코드 · 머리말만 이름표, 나머지는 OTHER (헌법 12조 근접 표본)."""

    def test_listed_codes_get_labels(self) -> None:
        expected = {
            "channel_cooldown": "같은 채널 대기 중",
            "daily_cap": "하루 상한에 닿음",
            "duplicate_video": "이미 처리한 영상",
            "not_in_allowlist": "허용 목록 밖이라 게시하지 않음",
            "invalid_video": "영상 주소를 읽을 수 없음",
            "dry_run": "테스트 실행 — 저장만",
            "no_comment": "댓글 없음",
            "config_rejected": "설정 거절로 저장만",
            "unavailable": "영상을 볼 수 없음",
        }
        self.assertEqual(REASON_LABELS, expected)
        for code, label in expected.items():
            with self.subTest(code=code):
                self.assertEqual(reason_label(code), label)
        # 트래커 결정 1 의 문장 그대로
        self.assertEqual(reason_label("not_in_allowlist"), "허용 목록 밖이라 게시하지 않음")

    def test_display_texts_are_literal(self) -> None:
        # 계약의 글자 그대로 — 상수끼리 견주면 상수가 바뀌어도 초록이라 글자를 적어 둡니다
        cases = (
            (NO_POST, "게시 기록 없음"),
            (NO_DRAFT, "댓글 안 씀"),
            (OTHER, "기타 — 로그 참고"),
            (RESERVED, "게시 결과 모름 — 로그 참고"),
            (FAILED, "게시 실패 — 로그 참고"),
            (NOT_JUDGED, "아직 판별 안 함"),
            (NOT_TIMED, "아직 안 봄"),
            (REHEARSED, "리허설 — 게시 버튼 앞에서 멈춤"),
            (POSTED, "게시됨"),
            (LOG_UNREADABLE, "로그를 읽지 못함"),
        )
        for text, letters in cases:
            with self.subTest(letters=letters):
                self.assertEqual(text, letters)

    def test_producer_constants_are_listed(self) -> None:
        prefixes = [prefix for prefix, _ in REASON_PREFIXES]
        self.assertIn(NO_SCENE, prefixes)
        self.assertIn(NO_CONCERN, prefixes)
        codes = (
            NO_COMMENT,
            DRY_RUN,
            run.CONFIG_REJECTED,
            decide_post("not a url", (), True).reason,
            decide_post("abcdefghijk", (), True).reason,
        )
        for code in codes:
            with self.subTest(code=code):
                self.assertIn(code, REASON_LABELS)
        stages = (run.STAGE_CLASSIFY, run.STAGE_TRIGGER, run.STAGE_WRITE, run.STAGE_POST)
        for stage in stages:
            with self.subTest(stage=stage):
                self.assertIn(stage, WHERE_LABELS)

    def test_writer_reason_shapes_get_labels(self) -> None:
        cases = (
            (f"{NO_SCENE} — 1차: 답을 읽을 수 없습니다", "작성 건너뜀 — 짚을 장면 없음"),
            (
                "검사 두 번 탈락 — 1차: 글자 수 30자 — 40–120자여야 합니다 / 2차: …",
                "검사 두 번 탈락",
            ),
            ("claude 호출 실패: " + mark("server"), "AI 호출 오류 (Claude)"),
            ("jev 검사 호출 실패: " + mark("server"), "AI 호출 오류 (jev 검사)"),
            ("jev 검사 응답 이상: " + mark("q"), "AI 응답 이상 (jev 검사)"),
        )
        for reason, label in cases:
            with self.subTest(reason=reason):
                self.assertEqual(reason_label(reason), label)
                self.assertNotIn("MRK", reason_label(reason))

    def test_near_miss_reasons_fall_to_other(self) -> None:
        samples = (
            "channel_cooldown2",
            " channel_cooldown",
            "channel_cooldown ",
            "Channel_cooldown",
            "channel-cooldown",
            "ｃhannel_cooldown",  # 전각 c (U+FF43)
            " 재료에 장면 없음",
            "재료에장면 없음",
            "재료에 장면",
            "검사 두 번 통과 못함",
            "jev 검사 실패",
            "Claude 호출 실패: X",
        )
        for reason in samples:
            with self.subTest(reason=reason):
                self.assertEqual(reason_label(reason), OTHER)

    def test_near_miss_green_reasons(self) -> None:
        samples = (
            ("channel_cooldown", "같은 채널 대기 중"),
            ("daily_cap", "하루 상한에 닿음"),
            ("unavailable", "영상을 볼 수 없음"),
            ("재료에 장면 없음 — 1차: 답을 읽을 수 없습니다", "작성 건너뜀 — 짚을 장면 없음"),
            ("claude 호출 실패: RuntimeError: " + mark("server"), "AI 호출 오류 (Claude)"),
            ("재료에 장면 없음표", "작성 건너뜀 — 짚을 장면 없음"),
        )
        for reason, label in samples:
            with self.subTest(reason=reason):
                self.assertEqual(reason_label(reason), label)
                self.assertNotIn("MRK", reason_label(reason))

    def test_where_labels_and_near_misses(self) -> None:
        self.assertEqual(
            WHERE_LABELS,
            {
                "classify": "판별 단계 오류",
                "run.classify": "판별 단계 오류",
                "run.trigger": "타이밍 단계 오류",
                "commentThreads.list": "인기 댓글을 받지 못함",
                "writer.claude": "AI 호출 오류 (Claude)",
                "writer.jev": "AI 호출 오류 (jev 검사)",
                "run.write": "작성 단계 오류",
                "poster": "게시 단계 오류",
                "run.post": "게시 단계 오류",
            },
        )
        self.assertEqual(where_label("writer.claude"), "AI 호출 오류 (Claude)")
        self.assertEqual(where_label("run.post"), "게시 단계 오류")
        samples = (
            "writer.claude2",
            " run.post",
            "Run.post",
            "run_post",
            "ｒun.post",  # 전각 r (U+FF52)
            mark("where"),
            "videos.list",  # 감시기 _fail 의 ERROR 에는 video= 가 없습니다
        )
        for where in samples:
            with self.subTest(where=where):
                self.assertEqual(where_label(where), OTHER)
                self.assertNotIn("MRK", where_label(where))


class TestLateLines(unittest.TestCase):
    """늦은 로그 줄과 배지 — badges 는 (결과, 결과 시각, 이유) 입니다."""

    def test_line_before_store_result_is_not_a_reason(self) -> None:
        commented = record(A, comment=drafted(T + 10 * S))
        early = line(T + 9 * S, Event.SKIP, video=A, reason="channel_cooldown")
        self.assertEqual(late_lines(commented, [early]), [])
        self.assertEqual(badges(commented, [early]), (NO_POST, None, None))
        same = line(T + 10 * S, Event.SKIP, video=A, reason="channel_cooldown")
        self.assertEqual(late_lines(commented, [early, same]), [same])
        self.assertEqual(badges(commented, [early, same]), (NO_POST, None, "같은 채널 대기 중"))
        # 댓글과 마지막 시도 중 늦은 쪽이 기준
        saved = record(
            A,
            comment=drafted(T + 10 * S),
            attempts=[attempt(T + 20 * S, "test", "saved", "not_in_allowlist")],
        )
        between = line(T + 15 * S, Event.SKIP, video=A, reason="daily_cap")
        self.assertEqual(
            badges(saved, [between]), ("허용 목록 밖이라 게시하지 않음", T + 20 * S, None)
        )
        # 댓글도 시도도 없으면 그 영상의 그런 줄 모두
        self.assertEqual(late_lines(record(A), [early]), [early])

    def test_same_second_counts_as_later(self) -> None:
        commented = record(A, comment=drafted(T + timedelta(seconds=10, microseconds=400_000)))
        skip = line(
            T + timedelta(seconds=10, microseconds=600_000),
            Event.SKIP,
            video=A,
            reason="channel_cooldown",
        )
        self.assertEqual(skip[0], T + 10 * S)  # 로그 시각은 초 단위
        self.assertEqual(badges(commented, [skip])[2], "같은 채널 대기 중")

    def test_no_store_result_counts_every_line(self) -> None:
        skip = line(
            T - HOUR, Event.SKIP, video=A, reason=f"{NO_SCENE} — 1차: 답을 읽을 수 없습니다"
        )
        self.assertEqual(
            badges(record(A), [skip]), (NO_DRAFT, None, "작성 건너뜀 — 짚을 장면 없음")
        )

    def test_last_line_in_file_order_wins(self) -> None:
        commented = record(A, comment=drafted(T))
        rehearsed = rehearsal(T + 20 * S)
        skip = line(T + 30 * S, Event.SKIP, video=A, reason="channel_cooldown")
        self.assertEqual(badges(commented, [rehearsed, skip]), (NO_POST, None, "같은 채널 대기 중"))
        later = rehearsal(T + 40 * S)
        self.assertEqual(badges(commented, [skip, later]), (REHEARSED, later[0], None))
        self.assertEqual(later[0], T + 40 * S)

    def test_rehearsal_needs_test_mode_and_rehearsed_result(self) -> None:
        commented = record(A, comment=drafted(T))
        others = [
            line(T + S, Event.POST, video=A, mode="live", result="rehearsed", reason=DRY_RUN),
            line(T + 2 * S, Event.POST, video=A, mode="test", result="saved", reason=DRY_RUN),
        ]
        self.assertEqual(late_lines(commented, others), [])
        self.assertEqual(badges(commented, others), (NO_POST, None, None))

    def test_other_video_lines_ignored(self) -> None:
        commented = record(A, comment=drafted(T))
        others = [
            line(T + S, Event.SKIP, video=B, reason="daily_cap"),
            line(T + 2 * S, Event.ERROR, where="run.post", reason="ValueError: x", video=B),
            rehearsal(T + 3 * S, B),
            line(T + 4 * S, Event.ERROR, where="cycle", reason="ValueError: x"),
        ]
        self.assertEqual(late_lines(commented, others), [])
        self.assertEqual(badges(commented, others), (NO_POST, None, None))

    def test_posted_then_duplicate_keeps_posted(self) -> None:
        posted = record(
            A, comment=drafted(T), attempts=[attempt(T + HOUR, "live", "posted", "allowlisted")]
        )
        duplicate = line(T + 3 * HOUR, Event.SKIP, video=A, reason="duplicate_video")
        self.assertEqual(badges(posted, [duplicate]), (POSTED, T + HOUR, "이미 처리한 영상"))

    def test_saved_attempt_outcomes_carry_their_time(self) -> None:
        cases = (
            ("not_in_allowlist", "허용 목록 밖이라 게시하지 않음"),
            ("config_rejected", "설정 거절로 저장만"),
            ("dry_run", "테스트 실행 — 저장만"),
        )
        for reason, label in cases:
            with self.subTest(reason=reason):
                saved = record(
                    A, comment=drafted(T), attempts=[attempt(T + 5 * S, "test", "saved", reason)]
                )
                self.assertEqual(badges(saved, []), (label, T + 5 * S, None))

    def test_live_outcomes(self) -> None:
        for result, label in (("reserved", RESERVED), ("failed", FAILED)):
            with self.subTest(result=result):
                tried = record(
                    A, comment=drafted(T), attempts=[attempt(T + S, "live", result, "allowlisted")]
                )
                self.assertEqual(badges(tried, []), (label, T + S, None))

    def test_error_line_labelled_by_where_only(self) -> None:
        commented = record(A, comment=drafted(T))
        error = line(T + S, Event.ERROR, where="writer.claude", reason=mark("e"), video=A)
        self.assertEqual(badges(commented, [error]), (NO_POST, None, "AI 호출 오류 (Claude)"))

    def test_unreadable_log_badges(self) -> None:
        posted = record(
            A, comment=drafted(T), attempts=[attempt(T + HOUR, "live", "posted", "allowlisted")]
        )
        self.assertEqual(badges(posted, None)[2], "로그를 읽지 못함")
        self.assertEqual(badges(posted, None), (POSTED, T + HOUR, LOG_UNREADABLE))


class TestJudgedFloor(unittest.TestCase):
    """판별 · 타이밍 시각도 늦은 줄의 기준 — 판별 보류 영상만 타이밍 시각을 세지 않습니다 (트래커 Phase 7H 결정 1)."""

    def test_classify_error_then_judged_no_has_no_reason(self) -> None:
        held = line(T, Event.ERROR, where="classify", reason="API 오류: 503", video=A)
        first = record(A, trigger=Judgement(Verdict.HOLD, "too_few_samples", T + 5 * MS))
        self.assertEqual(badges(first, [held]), (NO_DRAFT, None, "판별 단계 오류"))
        second = record(
            A,
            classification=Judgement(Verdict.NO, "연애 고민 아님", T + HOUR),
            trigger=Judgement(Verdict.HOLD, "too_few_samples", T + HOUR + 5 * MS),
        )
        self.assertEqual(late_lines(second, [held]), [])
        self.assertEqual(badges(second, [held]), (NO_DRAFT, None, None))

    def test_claude_failure_then_timing_no_has_no_reason(self) -> None:
        failed = [
            line(
                T + S,
                Event.SKIP,
                video=A,
                reason="claude 호출 실패: RuntimeError: " + mark("server"),
            ),
            line(T + S, Event.ERROR, where="writer.claude", reason=mark("e"), video=A),
        ]
        timed_yes = record(
            A, classification=JUDGED, trigger=Judgement(Verdict.YES, "규칙 통과", T)
        )
        self.assertEqual(badges(timed_yes, failed), (NO_DRAFT, None, "AI 호출 오류 (Claude)"))
        timed_no = record(
            A, classification=JUDGED, trigger=Judgement(Verdict.NO, "규칙 미달", T + HOUR)
        )
        self.assertEqual(late_lines(timed_no, failed), [])
        self.assertEqual(badges(timed_no, failed), (NO_DRAFT, None, None))

    def test_unavailable_shown_until_seen_again(self) -> None:
        gone = line(T + HOUR, Event.SKIP, video=A, reason="unavailable", call="videos.list")
        waiting = record(
            A, classification=JUDGED, trigger=Judgement(Verdict.NO, "규칙 미달", T)
        )
        self.assertEqual(badges(waiting, [gone]), (NO_DRAFT, None, "영상을 볼 수 없음"))
        again = record(
            A, classification=JUDGED, trigger=Judgement(Verdict.NO, "규칙 미달", T + 2 * HOUR)
        )
        self.assertEqual(late_lines(again, [gone]), [])
        self.assertEqual(badges(again, [gone]), (NO_DRAFT, None, None))

    def test_hold_keeps_classify_error_when_timing_ticks_second(self) -> None:
        error = line(
            T + 10 * S + 999 * MS, Event.ERROR, where="classify", reason="API 오류: 503", video=A
        )
        self.assertEqual(error[0], T + 10 * S)  # 로그 시각은 초 단위
        held = record(A, trigger=Judgement(Verdict.HOLD, "too_few_samples", T + 11 * S + 4 * MS))
        self.assertEqual(late_lines(held, [error]), [error])
        self.assertEqual(badges(held, [error]), (NO_DRAFT, None, "판별 단계 오류"))

    def test_classification_time_counts_alone(self) -> None:
        judged = record(
            A, classification=Judgement(Verdict.YES, "연애 고민 상담", T + 10 * S + 400 * MS)
        )
        early = line(T + 9 * S, Event.SKIP, video=A, reason="daily_cap")
        same = line(T + 10 * S + 600 * MS, Event.SKIP, video=A, reason="channel_cooldown")
        self.assertEqual(late_lines(judged, [early, same]), [same])
        self.assertEqual(badges(judged, [early]), (NO_DRAFT, None, None))
        self.assertEqual(badges(judged, [early, same]), (NO_DRAFT, None, "같은 채널 대기 중"))

    def test_rehearsal_before_new_timing_is_not_the_outcome(self) -> None:
        again = record(
            A,
            classification=JUDGED,
            trigger=Judgement(Verdict.YES, "allowlisted", T + HOUR),
            comment=drafted(T),
        )
        old = rehearsal(T + S)
        self.assertEqual(badges(again, [old]), (NO_POST, None, None))
        fresh = rehearsal(T + HOUR)
        self.assertEqual(badges(again, [old, fresh]), (REHEARSED, T + HOUR, None))

    def test_rerecorded_reason_after_new_timing_keeps_badge(self) -> None:
        """다시 다룬 주기에 다시 적힌 이유는 남습니다 — Phase 7C 가 기억한 건너뜀을 SKIP 으로 다시 남기는 자리."""
        again = record(
            A,
            classification=JUDGED,
            trigger=Judgement(Verdict.YES, "규칙 통과", T + HOUR + 400 * MS),
        )
        dropped = "검사 두 번 탈락 — 1차: 글자 수 30자 — 40–120자여야 합니다 / 2차: …"
        first = line(T + S, Event.SKIP, video=A, reason=dropped)
        self.assertEqual(badges(again, [first]), (NO_DRAFT, None, None))
        rerecorded = line(T + HOUR + 600 * MS, Event.SKIP, video=A, reason=dropped)
        self.assertEqual(late_lines(again, [first, rerecorded]), [rerecorded])
        self.assertEqual(
            badges(again, [first, rerecorded]), (NO_DRAFT, None, "검사 두 번 탈락")
        )


class TestRender(unittest.TestCase):
    def test_same_records_and_log_same_screen(self) -> None:
        records, events = scene()
        first = render_report(records, events, generated_at=T)
        again_records, again_events = scene()
        self.assertEqual(first, render_report(again_records, again_events, generated_at=T))
        later = render_report(records, events, generated_at=T + HOUR).split("\n")
        lines = first.split("\n")
        self.assertEqual(len(lines), len(later))
        changed = [(old, new) for old, new in zip(lines, later) if old != new]
        self.assertEqual(
            changed,
            [
                (
                    '<p class="generated">만든 시각 2026-10-12T21:00:00+09:00</p>',
                    '<p class="generated">만든 시각 2026-10-12T22:00:00+09:00</p>',
                )
            ],
        )

    def test_rows_newest_detection_first(self) -> None:
        records = [
            record(A, detected_at=T),
            record(B, detected_at=T + 2 * HOUR),
            record(C, detected_at=T + HOUR),
            record(D, detected_at=T + 2 * HOUR),
        ]
        page = render_report(records, [], generated_at=T)
        self.assertEqual(re.findall(r'<tr id="v-([^"]+)">', page), [D, B, C, A])

    def test_judge_from_classify_then_start_else_blank(self) -> None:
        records = [record(v, classification=JUDGED) for v in (A, B, C, D)]
        events = [
            line(T, Event.START, **START),
            line(T + S, Event.CLASSIFY, video=C, verdict="yes", reason="연애 고민 상담"),
            line(T + 2 * S, Event.START, judge="jev", **START),
            line(T + 3 * S, Event.CLASSIFY, video=A, verdict="yes", reason="연애 고민 상담"),
            line(
                T + 4 * S,
                Event.CLASSIFY,
                video=B,
                verdict="yes",
                reason="연애 고민 상담",
                judge="claude",
            ),
        ]
        page = render_report(records, events, generated_at=T)
        self.assertEqual(cells(row(page, A))[2], "jev")
        self.assertEqual(cells(row(page, B))[2], "claude")
        self.assertEqual(cells(row(page, C))[2], "")  # 그 줄 앞 START 에 judge= 가 없음
        self.assertEqual(cells(row(page, D))[2], "")  # CLASSIFY 줄이 없음
        self.assertEqual(judge_of(A, events), "jev")
        self.assertEqual(judge_of(D, events), "")

    def test_judge_blank_while_unclassified(self) -> None:
        events = [
            line(T, Event.CLASSIFY, video=A, verdict="hold", reason="API 오류: 503", judge="jev")
        ]
        page = render_report([record(A)], events, generated_at=T)
        self.assertEqual(cells(row(page, A))[1:3], [NOT_JUDGED, ""])

    def test_outcome_time_under_badge(self) -> None:
        saved = record(
            A,
            comment=drafted(T),
            attempts=[attempt(T + 5 * S, "test", "saved", "not_in_allowlist")],
        )
        page = render_report([saved], [], generated_at=T)
        self.assertEqual(
            cells(row(page, A))[6],
            '<span class="badge">허용 목록 밖이라 게시하지 않음</span>'
            "<br><small>2026-10-12T21:00:05+09:00</small>",
        )

    def test_timing_cell_shows_allowlisted_and_per_hour(self) -> None:
        listed = record(
            A,
            view_history=[ViewSample(T, 2000)],
            trigger=Judgement(Verdict.YES, "allowlisted", T),
        )
        self.assertEqual(views_per_hour(listed), 1000.0)
        unmeasured = record(C, trigger=Judgement(Verdict.HOLD, "too_few_samples", T))
        self.assertIsNone(views_per_hour(unmeasured))
        page = render_report([listed, record(B), unmeasured], [], generated_at=T)
        self.assertEqual(cells(row(page, A))[3], "yes · allowlisted · 시간당 1000.00회")
        self.assertEqual(cells(row(page, B))[3], NOT_TIMED)
        self.assertEqual(cells(row(page, C))[3], "hold · too_few_samples")

    def test_unreadable_log_banner_and_badges(self) -> None:
        records, events = scene()
        healthy = render_report(records, events, generated_at=T)
        self.assertNotIn(WARNING, healthy)
        self.assertIn(f'<span class="badge">{REHEARSED}</span>', row(healthy, C))
        self.assertEqual(cells(row(healthy, A))[2], "jev")
        page = render_report(records, None, generated_at=T)
        self.assertIn(WARNING, page.split("\n"))
        for video_id in (A, B, C, D):
            with self.subTest(video=video_id):
                shown = row(page, video_id)
                self.assertIn('<span class="badge reason">로그를 읽지 못함</span>', shown)
                self.assertEqual(cells(shown)[2], "")
                self.assertNotIn(REHEARSED, shown)

    def test_empty_store_row(self) -> None:
        lines = render_report([], [], generated_at=T).split("\n")
        style = [text for text in lines if text.startswith("<style>")]
        self.assertEqual(len(style), 1)
        self.assertTrue(style[0].endswith("</style>"))
        self.assertEqual(
            [text for text in lines if not text.startswith("<style>")],
            [
                "<!doctype html>",
                '<html lang="ko">',
                "<head>",
                '<meta charset="utf-8">',
                "<title>결과 화면 — 마케팅 에이전트</title>",
                "</head>",
                "<body>",
                "<h1>결과 화면</h1>",
                '<p class="generated">만든 시각 2026-10-12T21:00:00+09:00</p>',
                '<p class="summary">영상 0개 — data/videos.json 과 logs/agent.log 로 만듦</p>',
                "<table>",
                "<thead><tr><th>영상</th><th>판별</th><th>판단한 쪽</th><th>타이밍</th>"
                "<th>고민 한 줄</th><th>댓글</th><th>게시 결과</th></tr></thead>",
                "<tbody>",
                '<tr><td colspan="7">아직 영상이 없습니다.</td></tr>',
                "</tbody>",
                "</table>",
                "</body>",
                "</html>",
                "",
            ],
        )

    def test_one_physical_line_per_row(self) -> None:
        text = "첫 줄\n둘째 줄\u2028셋째 줄"
        commented = record(A, comment=CommentDraft("고민", text, T))
        page = render_report([commented], [], generated_at=T)
        lines = page.split("\n")
        (shown,) = [text for text in lines if text.startswith('<tr id="v-')]
        self.assertTrue(shown.endswith("</tr>"))
        self.assertEqual(cells(shown)[5], "첫 줄<br>둘째 줄<br>셋째 줄")
        self.assertNotIn("\u2028", page)
        self.assertEqual(page.splitlines(), lines[:-1])


MARKED_IDS = ("MRKvideo001", "MRKvideo002", "MRKvideo003")


def marked_scene() -> tuple[list[VideoRecord], list[LogLine], list[str], list[str]]:
    """모든 글 칸에 표시 글을 심은 저장소와 로그 — (기록, 로그 줄, 보일 표시, 숨을 표시).

    보일 표시는 제목 · 판별 이유 · 타이밍 이유 · 고민 · 댓글 · CLASSIFY 와 START 의 judge 이고,
    나머지(설명 · 채널 · 검색어 · 자체 검사 이유 · 시도 이유 · 시도 캡처 · judge 밖의 모든 로그 칸)는
    숨을 표시입니다. 영상 ID 는 11자 모양이 정해져 있어 MRK 모양 ID 입니다.
    """
    shown: list[str] = []
    hidden: list[str] = []

    def m(field: str, show: bool = False) -> str:
        (shown if show else hidden).append(field)
        return mark(field)

    outcomes = (("test", "saved"), ("live", "posted"), ("live", "reserved"))
    records = []
    for n, (video_id, (mode, result)) in enumerate(zip(MARKED_IDS, outcomes), start=1):
        records.append(
            VideoRecord(
                video_id=video_id,
                channel_id=m(f"channel-{n}"),
                title=m(f"title-{n}", True),
                description=m(f"description-{n}"),
                published_at=T - 2 * HOUR,
                detected_at=T + n * S,
                keyword=m(f"keyword-{n}"),
                view_history=[ViewSample(T, 2000)],
                classification=Judgement(Verdict.YES, m(f"classification-{n}", True), T),
                trigger=Judgement(Verdict.YES, m(f"trigger-{n}", True), T),
                comment=CommentDraft(
                    m(f"concern-{n}", True),
                    m(f"comment-{n}", True),
                    T,
                    Judgement(Verdict.YES, m(f"self-check-{n}"), T),
                ),
                attempts=[
                    PostAttempt(
                        T + S, mode, result, m(f"attempt-reason-{n}"), m(f"attempt-shot-{n}")
                    )
                ],
            )
        )
    first, second, third = MARKED_IDS
    at = T + 10 * S
    events: list[LogLine] = []
    for k, event in enumerate(Event):
        fields: dict[str, object] = {
            name: first if name == "video" else m(f"log-{event.value}-{name}")
            for name in REQUIRED_FIELDS[event]
        }
        if event is Event.START:
            fields["judge"] = m("start-judge", True)
        if event is Event.CLASSIFY:
            fields["judge"] = m("classify-judge", True)
        events.append(line(at + k * S, event, **fields))
    at += 20 * S
    events += [
        # judge= 가 없는 CLASSIFY — 둘째 영상의 판단한 쪽은 START 의 judge
        line(at, Event.CLASSIFY, video=second, verdict=m("c2-verdict"), reason=m("c2-reason")),
        rehearsal(
            at + S,
            third,
            reason=m("rehearsal-reason"),
            screenshot=m("rehearsal-shot"),
            detail=m("rehearsal-detail"),
            page_url=m("rehearsal-page-url"),
            judge=m("rehearsal-judge"),
        ),
        line(
            at + 2 * S,
            Event.SKIP,
            video=second,
            reason=m("skip-reason"),
            detail=m("skip-detail"),
            call=m("skip-call"),
            judge=m("skip-judge"),
        ),
        line(
            at + 3 * S,
            Event.ERROR,
            where=m("error-where"),
            reason=m("error-reason"),
            video=first,
            stage=m("error-stage"),
            call=m("error-call"),
            detail=m("error-detail"),
            screenshot=m("error-shot"),
            page_url=m("error-page-url"),
            judge=m("error-judge"),
        ),
    ]
    return records, events, shown, hidden


class TestBoundary(unittest.TestCase):
    """헌법 9조 짝 — 저장소 · 로그의 모든 글 칸에 표시 글을 심고 화면에서 찾습니다."""

    def setUp(self) -> None:
        self.records, self.events, self.shown, self.hidden = marked_scene()
        self.page = render_report(self.records, self.events, generated_at=T)

    def test_marked_store_and_log_fields_never_raw(self) -> None:
        self.assertNotIn("<script", self.page.lower())
        self.assertEqual(len(self.shown), 17)  # 기록 셋 × 다섯 + judge 둘
        for field in self.shown:
            with self.subTest(shown=field):
                escaped = html.escape(mark(field), quote=True)
                self.assertIn(escaped, self.page)
                self.assertNotIn(mark(field), self.page)
                self.assertEqual(self.page.count(f"MRK-{field}~"), self.page.count(escaped))
        for field in self.hidden:
            with self.subTest(hidden=field):
                self.assertNotIn(f"MRK-{field}~", self.page)
        # 늦은 로그 줄이 정말 쓰였는지 — 셋째는 리허설, 둘째 · 첫째는 이름표 OTHER
        self.assertIn(f'<span class="badge">{REHEARSED}</span>', row(self.page, MARKED_IDS[2]))
        for video_id in MARKED_IDS[:2]:
            self.assertIn(f'<span class="badge reason">{OTHER}</span>', row(self.page, video_id))

    def test_links_are_built_from_ids_only(self) -> None:
        hrefs = re.findall(r'href="([^"]*)"', self.page)
        self.assertEqual(
            sorted(hrefs), sorted(WATCH_URL.format(video_id=video_id) for video_id in MARKED_IDS)
        )

    def test_no_external_resources(self) -> None:
        lowered = self.page.lower()
        for needle in ("<script", "<link", "src=", "@import", "url("):
            with self.subTest(needle=needle):
                self.assertNotIn(needle, lowered)


class TestWrite(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def test_write_creates_folder_and_replaces(self) -> None:
        path = self.root / "data" / "report.html"
        with mock.patch.object(os, "replace", wraps=os.replace) as replace:
            write_report(path, "첫 화면\n")
        replace.assert_called_once_with(path.with_name("report.html.tmp"), path)
        self.assertEqual(path.read_text(encoding="utf-8"), "첫 화면\n")
        write_report(path, "둘째 화면\n")
        self.assertEqual(path.read_text(encoding="utf-8"), "둘째 화면\n")
        self.assertEqual([child.name for child in path.parent.iterdir()], ["report.html"])

    def test_write_is_utf8_lf(self) -> None:
        path = self.root / "report.html"
        write_report(path, "한글 화면\n둘째 줄\n")
        self.assertEqual(path.read_bytes(), "한글 화면\n둘째 줄\n".encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
