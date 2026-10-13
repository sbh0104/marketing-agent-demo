"""실제 호출 실행기 테스트 — 판정 줄 · 요약 · 키 가림 · 결과 파일 쓰기 · --verdict · 맨 위 문(cli).

진짜 jev · Claude · YouTube 는 부르지 않습니다. 판정 줄은 가짜 결과(healthy_result 의 변형)로
경우마다 잠그고, 같은 변형을 파일로 써 --verdict 가 같은 줄을 다시 세는지 봅니다. 키는 가짜
문자열입니다. 계약 '실제 호출 실행기' 절.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from agent.classifier import LANGUAGES, build_questions
from agent.config import load_config
from agent.models import Verdict
from agent.writer import CHECK_QUESTIONS
from tests import live_check
from tests.classifier_examples import EXAMPLES
from tests.jev_accuracy import PASS_CORRECT, REPO_CONFIG

NOW = datetime(2026, 10, 14, 3, 0, tzinfo=timezone.utc)
KEYS = {
    "YOUTUBE_API_KEY": "ytFAKEKEY0123456789abcdefXYZ",
    "TYPESAFE_API_KEY": "tsFAKEKEY-9876543210-zyxwv",
    "ANTHROPIC_API_KEY": "sk-ant-FAKEKEY-ABCDEFGHIJKLMNOP",
}
SONNET, HAIKU = live_check.MODEL_NAMES
ON = "연애 고민 상담"
OFF = "연애와 관계없음"
# 판정 줄 시험은 config.yaml 이 아니라 결과 파일의 지문을 읽습니다 — 기준값이 바뀌어도 이 표는 그대로입니다.
CLASSIFIER = {
    "model": "jev-latest",
    "noul_yes_min": 0.8,
    "noul_no_max": 0.2,
    "choice_min_confidence": 0.5,
    "on_topic_reasons": ["연애 고민 상담", "연애 경험담", "썸 · 소개팅 이야기", "이별 · 재회 고민"],
    "off_topic_reasons": [
        "키워드만 겹침: 게임",
        "키워드만 겹침: 음악",
        "키워드만 겹침: 예능 · 드라마",
        "연애와 관계없음",
    ],
}
UNMEASURED_HINT = " — 재지 못함은 위 오류 줄(서비스 · 단계 · 상태: 키 · 크레딧 · API 설정)을 먼저 봅니다"


def example_rows() -> list[dict]:
    rows = []
    for index, example in enumerate(EXAMPLES, 1):
        yes = example.label is Verdict.YES
        rows.append(
            {
                "index": index,
                "kind": example.kind,
                "label": example.label.value,
                "verdict": example.label.value,
                "error": False,
                "noul": 0.96 if yes else 0.05,
                "choice": ON if yes else OFF,
                "probability": 0.9,
                "confidence": 0.9,
                "untrusted": {"reason": "예시 판정 이유"},
            }
        )
    return rows


def draft(attempt: int, *, passed: bool, grade: str = "ok") -> dict:
    return {
        "attempt": attempt,
        "parsed": True,
        "scores": {
            "mentions_scene": 0.9,
            "reads_like_ad": 0.1 if passed else 0.6,
            "follows_concern": 0.9,
        },
        "self_check_pass": passed,
        "code_pass": True,
        "passed": passed,
        "grade": {
            "scene_in_material": grade == "ok",
            "reads_like_ad": False,
            "follows_concern": True,
        },
        "claude_grade": grade,
        "grade_error": None,
        "human": "",
        "untrusted": {
            "concern": "연락 텀이 길어 불안한 썸",
            "comment": "답장 기다리며 마음 졸이던 장면이 꼭 제 얘기 같았어요. 저도 연애사주 보고 조급함을 내려놨어요.",
            "code_failures": [],
        },
    }


def video(
    number: int, result: str, *, window: str = "operation", error_cause: str | None = None
) -> dict:
    written = result != "not_written"
    drafts = {
        "comment": [draft(1, passed=True)],
        "skip": [draft(1, passed=False, grade="bad"), draft(2, passed=False, grade="bad")],
    }.get(result, [])
    return {
        "video_id": f"vid{number:08d}",
        "window": window,
        "keyword": "연애",
        "published_at": (NOW - timedelta(hours=5)).isoformat(),
        "age_hours": 5.0,
        "views": 2500,
        "classification": {
            "verdict": "yes" if written else "no",
            "error": False,
            "noul": 0.95 if written else 0.05,
            "choice": ON if written else OFF,
            "probability": 0.9,
            "confidence": 0.9,
        },
        "material": "top_comments" if written else None,
        "top_comment_count": 10 if written else 0,
        "comments_disabled": False,
        "result": result,
        "error_cause": error_cause,
        "drafts": drafts,
        "untrusted": {
            "title": "썸 타는 사람 연락 텀, 이렇게 해 보세요",
            "description": "답장이 늦을 때 마음을 다스리는 법",
            "classification_reason": "연애 고민 상담 (0.90) · 일치 0.95 · 확신 0.90",
            "top_comments": ["저도 그랬어요", "공감합니다"] if written else [],
            "skip_reason": "검사 두 번 탈락" if result == "skip" else None,
        },
    }


def error_entry(
    service: str, stage: str, error: str, status: int | None, video_id: str | None = None
) -> dict:
    return {
        "service": service,
        "stage": stage,
        "error": error,
        "status": status,
        "video_id": video_id,
    }


def window(searches: int, found: int, in_range: int, classified: int, hours: int) -> dict:
    return {
        "published_after": (NOW - timedelta(hours=hours)).isoformat(),
        "published_before": None if hours == 12 else (NOW - timedelta(hours=12)).isoformat(),
        "searches": searches,
        "found": found,
        "in_range": in_range,
        "classified": classified,
    }


def healthy_result() -> dict:
    """모양이 맞는 건강한 결과 — 언어마다 22개 모두 맞음, 쓴 영상 4개(comment 3 · skip 1),
    두 모델 accepted, errors 비어 있음."""
    config = load_config(REPO_CONFIG)
    examples_json = json.dumps(
        [[e.title, e.description, e.label.value, e.kind] for e in EXAMPLES],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "schema_version": live_check.RESULT_SCHEMA_VERSION,
        "notice": live_check.UNTRUSTED_NOTICE,
        "run_at": NOW.isoformat(),
        "verdict": "6B: go",
        "stopped": None,
        "calls": {"jev": 55, "claude": 12, "youtube": 14},
        "ceilings": dict(live_check.CEILINGS),
        "example_count": len(EXAMPLES),
        "fingerprint": {
            "classifier": json.loads(json.dumps(CLASSIFIER)),
            "questions": {language: build_questions(config, language) for language in LANGUAGES},
            "examples_sha256": hashlib.sha256(examples_json.encode("utf-8")).hexdigest(),
            "jev_models": ["jev-1.13.0"],
            "check_questions": dict(CHECK_QUESTIONS),
            "self_check_criteria": dict(live_check.SELF_CHECK_CRITERIA),
            "check_min_probability": 0.7,
            "trigger": {"min_views": 1000, "max_views": 5000, "max_age_hours": 12},
            "grade_system": live_check.GRADE_SYSTEM,
            "margin": live_check.MARGIN,
            "pass_correct": PASS_CORRECT,
            "target_drafts": live_check.TARGET_DRAFTS,
            "wide_window_hours": live_check.WIDE_WINDOW_HOURS,
            "claude_max_retries": live_check.CLAUDE_MAX_RETRIES,
        },
        "models": {
            SONNET: {"status": "accepted", "error": None},
            HAIKU: {"status": "accepted", "error": None},
        },
        "writer_model": SONNET,
        "grader_model": HAIKU,
        "accuracy": {language: example_rows() for language in LANGUAGES},
        "accuracy_tally": {
            language: {"correct": 22, "false_yes": 0, "false_no": 0, "hold": 0, "error": 0}
            for language in LANGUAGES
        },
        "windows": {"operation": window(5, 20, 6, 6, 12)},
        "videos": [
            video(1, "comment"),
            video(2, "comment"),
            video(3, "comment"),
            video(4, "skip"),
            video(5, "not_written"),
            video(6, "not_written"),
        ],
        "errors": [],
    }


def yes_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row["label"] == "yes" and not row["error"]]


def no_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row["label"] == "no"]


def mark_error(row: dict) -> None:
    row.update(
        verdict="hold", error=True, noul=None, choice=None, probability=None, confidence=None
    )
    row["untrusted"]["reason"] = "API 오류: 429"


def hold_yes(rows: list[dict], count: int) -> None:
    for row in yes_rows(rows)[:count]:
        row.update(noul=0.5, verdict="hold")


# ── 판정 줄의 경우마다 하나 — VerdictTest 가 줄을 잠그고 VerdictFlagTest 가 파일로 다시 셉니다 ──


def example_error() -> dict:
    result = healthy_result()
    mark_error(result["accuracy"]["ko"][0])
    return result


def call_error() -> dict:
    result = healthy_result()
    result["errors"].append(error_entry("youtube", "search", "YouTubeError", 403))
    return result


def rejected_probe() -> dict:
    result = healthy_result()
    result["models"][SONNET] = {"status": "rejected", "error": "NotFoundError 404"}
    result["writer_model"] = result["grader_model"] = HAIKU
    result["errors"].append(error_entry("claude", "probe", "NotFoundError", 404))
    return result


def video_error() -> dict:
    result = healthy_result()
    # 오류 영상을 SKIP 으로 세면 2/3 로 작성 막힘이 되는 짝 — 세지 않아야 1/2 로 go 입니다.
    result["videos"] = [
        video(1, "comment"),
        video(2, "skip"),
        video(3, "error", error_cause="jev"),
    ]
    return result


def ceiling_stop() -> dict:
    result = healthy_result()
    result["stopped"] = {"kind": "ceiling", "service": "jev", "limit": 120}
    return result


def quota_stop() -> dict:
    result = healthy_result()
    result["stopped"] = {
        "kind": "quota",
        "call": "search.list",
        "counter": "searches",
        "used": 90,
        "limit": 90,
    }
    return result


def aborted() -> dict:
    result = healthy_result()
    result["stopped"] = {"kind": "aborted", "error": "KeyboardInterrupt"}
    return result


def below_floor() -> dict:
    result = healthy_result()
    hold_yes(result["accuracy"]["ko"], 5)
    hold_yes(result["accuracy"]["en"], 4)
    return result


def one_language_passing() -> dict:
    result = healthy_result()
    hold_yes(result["accuracy"]["ko"], 5)
    return result


def false_yes_within_margin() -> dict:
    result = healthy_result()
    for language in LANGUAGES:
        no_rows(result["accuracy"][language])[0].update(noul=0.90, choice=ON, verdict="yes")
    return result


def floor_above_one() -> dict:
    result = healthy_result()
    for language in LANGUAGES:
        no_rows(result["accuracy"][language])[0].update(
            noul=0.97, choice=ON, confidence=0.98, verdict="yes"
        )
    return result


def no_max_moved() -> dict:
    result = healthy_result()
    for language in LANGUAGES:
        for row in no_rows(result["accuracy"][language])[:3]:
            row.update(noul=0.3, verdict="hold")
    return result


def skip_half() -> dict:
    result = healthy_result()
    result["videos"] = [
        video(1, "comment"),
        video(2, "comment"),
        video(3, "skip"),
        video(4, "skip"),
    ]
    return result


def skip_over_half() -> dict:
    result = healthy_result()
    result["videos"] = [
        video(1, "comment"),
        video(2, "comment"),
        video(3, "skip"),
        video(4, "skip"),
        video(5, "skip"),
    ]
    return result


def nothing_written() -> dict:
    result = healthy_result()
    result["videos"] = [video(5, "not_written")]
    return result


def widened_skips() -> dict:
    result = healthy_result()
    result["windows"]["widened"] = window(5, 8, 2, 2, 72)
    result["videos"] = [
        video(1, "comment"),
        video(2, "skip", window="widened"),
        video(3, "skip", window="widened"),
    ]
    return result


def one_model_rejected() -> dict:
    result = healthy_result()
    result["models"][HAIKU] = {"status": "rejected", "error": "NotFoundError 404"}
    result["grader_model"] = SONNET
    result["errors"].append(error_entry("claude", "probe", "NotFoundError", 404))
    return result


def both_models_rejected() -> dict:
    result = healthy_result()
    for name in (SONNET, HAIKU):
        result["models"][name] = {"status": "rejected", "error": "NotFoundError 404"}
        result["errors"].append(error_entry("claude", "probe", "NotFoundError", 404))
    result["writer_model"] = result["grader_model"] = None
    result["windows"] = {}
    result["videos"] = []
    return result


def human_filled() -> dict:
    result = skip_over_half()
    for item in result["videos"]:
        for entry in item["drafts"]:
            entry["human"] = "ok" if entry["claude_grade"] == "bad" else "bad"
    return result


def all_cases() -> dict:
    result = healthy_result()
    ko, en = result["accuracy"]["ko"], result["accuracy"]["en"]
    mark_error(yes_rows(ko)[0])
    hold_yes(ko, 5)
    hold_yes(en, 4)
    for name in (SONNET, HAIKU):
        result["models"][name] = {"status": "rejected", "error": "NotFoundError 404"}
        result["errors"].append(error_entry("claude", "probe", "NotFoundError", 404))
    result["errors"].append(error_entry("youtube", "search", "YouTubeError", 403))
    result["videos"] = [
        video(1, "comment"),
        video(2, "comment"),
        video(3, "skip"),
        video(4, "skip"),
        video(5, "skip"),
        video(6, "error", error_cause="jev"),
    ]
    result["stopped"] = {"kind": "ceiling", "service": "claude", "limit": 70}
    return result


G1_CASES: tuple[Callable[[], dict], ...] = (
    healthy_result,
    example_error,
    call_error,
    rejected_probe,
    video_error,
    ceiling_stop,
    quota_stop,
    aborted,
    below_floor,
    one_language_passing,
    false_yes_within_margin,
    floor_above_one,
    no_max_moved,
    skip_half,
    skip_over_half,
    nothing_written,
    widened_skips,
    one_model_rejected,
    both_models_rejected,
    human_filled,
    all_cases,
)


def assert_no_key(case: unittest.TestCase, text: str) -> None:
    for name, value in KEYS.items():
        case.assertNotIn(value[: live_check.KEY_FRAGMENT_MIN], text, name)


class RedactorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.redactor = live_check.Redactor(KEYS)

    def test_masks_whole_key_and_prefix_fragments(self) -> None:
        url = f"https://www.googleapis.com/youtube/v3/search?key={KEYS['YOUTUBE_API_KEY']}&q=x"
        self.assertEqual(
            self.redactor(url),
            "https://www.googleapis.com/youtube/v3/search?key=<YOUTUBE_API_KEY>&q=x",
        )
        message = ("x" * 190 + KEYS["ANTHROPIC_API_KEY"] + " 뒤 글")[:200]
        self.assertEqual(self.redactor(message), "x" * 190 + "<ANTHROPIC_API_KEY>")
        every = " · ".join(KEYS.values())
        self.assertEqual(
            self.redactor(every),
            "<YOUTUBE_API_KEY> · <TYPESAFE_API_KEY> · <ANTHROPIC_API_KEY>",
        )

    def test_short_fragment_is_left_alone(self) -> None:
        for value in KEYS.values():
            text = f"앞 {value[:7]} 뒤"
            self.assertEqual(self.redactor(text), text)
            self.assertFalse(self.redactor.leaks(text))

    def test_leaks_finds_fragment(self) -> None:
        for value in KEYS.values():
            text = f"오류 글 {value[:8]} 끝"
            self.assertTrue(self.redactor.leaks(text))
            self.assertFalse(self.redactor.leaks(self.redactor(text)))
        self.assertFalse(self.redactor.leaks("키가 없는 글"))


class VerdictTest(unittest.TestCase):
    def line(self, result: dict) -> str:
        return live_check.verdict_line(result)

    def test_healthy_result_is_go(self) -> None:
        self.assertEqual(self.line(healthy_result()), "6B: go")

    def test_example_error_is_unmeasured(self) -> None:
        self.assertEqual(self.line(example_error()), "6B: stop — 재지 못함(예시 오류 1)")

    def test_call_error_outside_examples_is_unmeasured(self) -> None:
        self.assertEqual(self.line(call_error()), "6B: stop — 재지 못함(호출 오류 1)")

    def test_rejected_probe_is_not_a_call_error(self) -> None:
        self.assertEqual(self.line(rejected_probe()), "6B: go")

    def test_video_error_is_unmeasured(self) -> None:
        line = self.line(video_error())
        self.assertEqual(line, "6B: stop — 재지 못함(영상 오류 1)")
        self.assertNotIn("작성 막힘", line)

    def test_ceiling_stop_is_unmeasured(self) -> None:
        self.assertEqual(self.line(ceiling_stop()), "6B: stop — 재지 못함(천장 jev 120)")

    def test_quota_stop_is_unmeasured(self) -> None:
        self.assertEqual(
            self.line(quota_stop()), "6B: stop — 재지 못함(쿼터 search.list searches 90/90)"
        )

    def test_abort_is_unmeasured(self) -> None:
        self.assertEqual(self.line(aborted()), "6B: stop — 재지 못함(중단 KeyboardInterrupt)")

    def test_below_floor_in_both_languages_stops(self) -> None:
        self.assertEqual(self.line(below_floor()), "6B: stop — 판별 미달(ko 17/22 · en 18/22)")

    def test_one_language_passing_is_go(self) -> None:
        self.assertEqual(self.line(one_language_passing()), "6B: go")

    def test_false_yes_blocked_with_margin_is_go(self) -> None:
        result = false_yes_within_margin()
        base = live_check.classifier_config(result["fingerprint"]["classifier"])
        for language in LANGUAGES:
            self.assertEqual(live_check.best_correct(result["accuracy"][language], base), 21)
        self.assertEqual(self.line(result), "6B: go")

    def test_raised_floor_above_one_cannot_block(self) -> None:
        result = floor_above_one()
        base = live_check.classifier_config(result["fingerprint"]["classifier"])
        self.assertIsNone(live_check.best_correct(result["accuracy"]["ko"], base))
        line = self.line(result)
        self.assertIn("ko 잘못된 일치 못 막음", line)
        self.assertEqual(
            line, "6B: stop — 판별 미달(ko 잘못된 일치 못 막음 · en 잘못된 일치 못 막음)"
        )

    def test_noul_no_max_moves_freely(self) -> None:
        result = no_max_moved()
        base = live_check.classifier_config(result["fingerprint"]["classifier"])
        for language in LANGUAGES:
            self.assertEqual(live_check.best_correct(result["accuracy"][language], base), 22)
        self.assertEqual(self.line(result), "6B: go")

    def test_skip_exactly_half_is_go(self) -> None:
        self.assertEqual(self.line(skip_half()), "6B: go")

    def test_skip_more_than_half_stops(self) -> None:
        self.assertEqual(self.line(skip_over_half()), "6B: stop — 작성 막힘(SKIP 3/5)")

    def test_no_measured_video_is_go_when_calls_are_clean(self) -> None:
        result = nothing_written()
        self.assertEqual(result["errors"], [])
        self.assertEqual(self.line(result), "6B: go")

    def test_widened_videos_count_in_skip_ratio(self) -> None:
        self.assertEqual(self.line(widened_skips()), "6B: stop — 작성 막힘(SKIP 2/3)")

    def test_one_model_rejected_is_go(self) -> None:
        self.assertEqual(self.line(one_model_rejected()), "6B: go")

    def test_both_models_rejected_stops(self) -> None:
        self.assertEqual(
            self.line(both_models_rejected()),
            "6B: stop — 모델 이름(claude-sonnet-5-5 · claude-haiku-5-5 둘 다 거절)",
        )

    def test_human_column_does_not_change_verdict(self) -> None:
        self.assertEqual(self.line(human_filled()), self.line(skip_over_half()))
        result = healthy_result()
        for item in result["videos"]:
            for entry in item["drafts"]:
                entry["human"] = "bad"
        self.assertEqual(self.line(result), "6B: go")

    def test_cases_join_in_order(self) -> None:
        self.assertEqual(
            self.line(all_cases()),
            "6B: stop — 재지 못함(예시 오류 1 · 호출 오류 1 · 영상 오류 1 · 천장 claude 70); "
            "판별 미달(ko 16/22 · en 18/22); 작성 막힘(SKIP 3/5); "
            "모델 이름(claude-sonnet-5-5 · claude-haiku-5-5 둘 다 거절)",
        )


class SummaryTest(unittest.TestCase):
    def summary(self, result: dict) -> list[str]:
        result["verdict"] = live_check.verdict_line(result)
        text = live_check.render_summary(result)
        self.assertTrue(text.endswith("\n"))
        return text.split("\n")[:-1]

    def test_first_line_is_verdict(self) -> None:
        for build in (healthy_result, all_cases, skip_over_half):
            with self.subTest(build.__name__):
                result = build()
                lines = self.summary(result)
                self.assertEqual(lines[0], result["verdict"])
                self.assertEqual(lines[0], live_check.verdict_line(result))
                self.assertEqual(lines[1], "")

    def test_summary_lists_counts_per_language_and_window(self) -> None:
        result = healthy_result()
        hold_yes(result["accuracy"]["en"], 2)
        result["accuracy_tally"]["en"] = {
            "correct": 20,
            "false_yes": 0,
            "false_no": 0,
            "hold": 2,
            "error": 0,
        }
        result["windows"]["widened"] = window(5, 8, 2, 2, 72)
        result["videos"][0]["drafts"] = [{"attempt": 1, "parsed": False}, draft(2, passed=True)]
        result["videos"][0]["drafts"][1]["human"] = "bad"
        result["videos"][1]["drafts"][0].update(grade=None, claude_grade=None, grade_error="응답 모양")
        result["videos"] += [
            video(7, "skip", window="widened"),
            video(8, "error", window="widened", error_cause="comments"),
        ]
        lines = self.summary(result)
        self.assertEqual(
            lines[2:],
            [
                "- 실행: 2026-10-14T03:00:00+00:00 · 스키마 1",
                "- 실행기 호출(SDK 안의 다시 시도 제외): jev 55/120 · claude 12/70 · youtube 14/50",
                "- 멈춤: 없음",
                "- 오류: 영상 오류 1",
                "- 모델: claude-sonnet-5-5 accepted · claude-haiku-5-5 accepted"
                " — 작성 claude-sonnet-5-5 · 채점 claude-haiku-5-5",
                "- 판별 지금 기준값 ko: 맞음 22/22 · 잘못된 일치 0 · 잘못된 불일치 0 · 보류 0 · 오류 0",
                "- 판별 지금 기준값 en: 맞음 20/22 · 잘못된 일치 0 · 잘못된 불일치 0 · 보류 2 · 오류 0",
                "- 판별 올리기만 범위 최다 맞음: ko 22/22 · en 20/22",
                "- 창 operation: 검색 5 · 찾음 20 · 조회수 범위 안 6 · 판별 6 · 쓴 영상 4 · SKIP 1"
                " · 영상 오류 0",
                "- 창 widened: 검색 5 · 찾음 8 · 조회수 범위 안 2 · 판별 2 · 쓴 영상 1 · SKIP 1"
                " · 영상 오류 1",
                "- 초안: 7 · 채점 ok 2 · bad 4 · 채점 오류 1 · 사람 칸 1/7",
                "- 다음: 결과 두 파일을 커밋하고 Phase 6B 대신 인터뷰로 옵니다" + UNMEASURED_HINT,
            ],
        )
        del result["accuracy_tally"]["en"]
        self.assertIn("- 판별 지금 기준값 en: 없음", self.summary(result))

    def test_errors_line_and_unmeasured_hint(self) -> None:
        result = healthy_result()
        result["models"][SONNET] = {"status": "rejected", "error": "NotFoundError 404"}
        result["videos"][0].update(result="error", error_cause="claude", drafts=[])
        result["videos"][1].update(result="error", error_cause="claude", drafts=[])
        result["errors"] = [
            error_entry("claude", "probe", "NotFoundError", 404),
            error_entry("claude", "write", "AuthenticationError", 401, "vid00000001"),
            error_entry("jev", "accuracy", "JevError", None),
            error_entry("claude", "write", "AuthenticationError", 401, "vid00000002"),
        ]
        lines = self.summary(result)
        self.assertIn(
            "- 오류: claude/probe NotFoundError 404 ×1 · claude/write AuthenticationError 401 ×2"
            " · jev/accuracy JevError ×1 · 영상 오류 2",
            lines,
        )
        self.assertIn(
            "- 모델: claude-sonnet-5-5 rejected (NotFoundError 404) · claude-haiku-5-5 accepted"
            " — 작성 claude-sonnet-5-5 · 채점 claude-haiku-5-5",
            lines,
        )
        self.assertTrue(lines[0].startswith("6B: stop — 재지 못함("))
        self.assertEqual(
            lines[-1],
            "- 다음: 결과 두 파일을 커밋하고 Phase 6B 대신 인터뷰로 옵니다" + UNMEASURED_HINT,
        )

        blocked = self.summary(skip_over_half())
        self.assertEqual(blocked[0], "6B: stop — 작성 막힘(SKIP 3/5)")
        self.assertIn("- 오류: 없음", blocked)
        self.assertEqual(blocked[-1], "- 다음: 결과 두 파일을 커밋하고 Phase 6B 대신 인터뷰로 옵니다")
        self.assertNotIn("오류 줄", blocked[-1])

        go = self.summary(healthy_result())
        self.assertEqual(go[-1], "- 다음: 결과 두 파일을 커밋하고 Phase 6B 를 시작합니다")


class WriteOutputsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "docs" / "live-check"

    def keyed_result(self) -> dict:
        result = healthy_result()
        result["videos"][0]["untrusted"]["title"] = f"제목 {KEYS['YOUTUBE_API_KEY']} 끝\ud800"
        result["videos"][0]["untrusted"]["top_comments"] = [KEYS["ANTHROPIC_API_KEY"][:12]]
        result["verdict"] = live_check.verdict_line(result)
        return result

    def test_writes_sorted_json_and_summary_atomically(self) -> None:
        result = self.keyed_result()
        with mock.patch.object(live_check.os, "replace", wraps=os.replace) as replace:
            paths = live_check.write_outputs(result, self.out, live_check.Redactor(KEYS))
        json_path, summary_path = self.out / "result.json", self.out / "summary.md"
        self.assertEqual(paths, [json_path, summary_path])
        self.assertEqual(
            [call.args for call in replace.call_args_list],
            [
                (self.out / "result.json.tmp", json_path),
                (self.out / "summary.md.tmp", summary_path),
            ],
        )
        self.assertEqual(
            sorted(path.name for path in self.out.iterdir()), ["result.json", "summary.md"]
        )
        raw = json_path.read_bytes()
        self.assertNotIn(b"\r", raw)
        text = raw.decode("utf-8")
        data = json.loads(text)
        self.assertEqual(
            text, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        self.assertIn("썸 타는 사람", text)
        untrusted = data["videos"][0]["untrusted"]
        self.assertEqual(untrusted["title"], "제목 <YOUTUBE_API_KEY> 끝�")
        self.assertEqual(untrusted["top_comments"], ["<ANTHROPIC_API_KEY>"])
        summary = summary_path.read_text(encoding="utf-8")
        # 키와 서로게이트는 untrusted 안에만 있고 요약은 그 칸을 읽지 않으므로 원래 결과와 같은 글입니다.
        self.assertEqual(summary, live_check.render_summary(result))
        self.assertEqual(summary.split("\n")[0], result["verdict"])
        assert_no_key(self, text + summary)

    def test_leaked_files_are_deleted(self) -> None:
        class Leaky(live_check.Redactor):
            def __call__(self, text: str) -> str:
                return text

        with self.assertRaises(live_check.KeyLeak) as raised:
            live_check.write_outputs(self.keyed_result(), self.out, Leaky(KEYS))
        self.assertEqual(list(self.out.iterdir()), [])
        assert_no_key(self, str(raised.exception))


class VerdictFlagTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "result.json"

    def recount(self, argv: list[str]) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        code = live_check.main(argv, stdout=stdout, stderr=stderr)
        return code, stdout.getvalue(), stderr.getvalue()

    def store(self, result: dict) -> None:
        self.path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")

    def test_recount_matches_stored_verdict(self) -> None:
        for build in G1_CASES:
            with self.subTest(build.__name__):
                result = build()
                result["verdict"] = live_check.verdict_line(result)
                self.store(result)
                code, out, err = self.recount(["--verdict", str(self.path)])
                self.assertEqual(out, result["verdict"] + "\n")
                self.assertEqual(err, "")
                self.assertEqual(code, 0 if result["verdict"] == "6B: go" else 1)

    def test_mismatched_stored_verdict_adds_a_line(self) -> None:
        result = ceiling_stop()
        self.store(result)  # 저장된 판정은 healthy_result 의 "6B: go" 그대로
        code, out, err = self.recount(["--verdict", str(self.path)])
        self.assertEqual(
            out, "6B: stop — 재지 못함(천장 jev 120)\n저장된 판정과 다릅니다: 6B: go\n"
        )
        self.assertEqual(err, "")
        self.assertEqual(code, 1)

    def test_unreadable_file_exits_2(self) -> None:
        cases = {
            "FileNotFoundError": None,
            "JSONDecodeError": b"{",
            "UnicodeDecodeError": b"\xff\xfe",
            "TypeError": b"[]",
            "KeyError": b"{}",
        }
        for name, content in cases.items():
            with self.subTest(name):
                self.path.unlink(missing_ok=True)
                if content is not None:
                    self.path.write_bytes(content)
                code, out, err = self.recount(["--verdict", str(self.path)])
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertEqual(err, f"결과 파일을 읽을 수 없습니다: {name}\n")

    def test_bad_arguments_exit_2(self) -> None:
        for argv in (["--verdict"], ["--verdict", "a.json", "b.json"], ["--bogus"], ["a.json"]):
            with self.subTest(argv):
                code, out, err = self.recount(argv)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertEqual(err, live_check.USAGE + "\n")


class CliTest(unittest.TestCase):
    def call(self, target: Callable[[], object]) -> tuple[object, str, str, bool]:
        """target 을 부르고 (값, stdout, stderr, KeyboardInterrupt 가 빠져나왔는지)를 돌려줍니다."""
        stdout, stderr = io.StringIO(), io.StringIO()
        value: object = None
        escaped = False
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                value = target()
            except SystemExit as exc:
                value = exc.code
            except KeyboardInterrupt:
                escaped = True
        return value, stdout.getvalue(), stderr.getvalue(), escaped

    def test_cli_catches_unexpected(self) -> None:
        def run(argv: object) -> int:
            try:
                raise OSError(f"연결 실패 key={KEYS['YOUTUBE_API_KEY']}")
            except OSError as exc:
                raise RuntimeError(KEYS["ANTHROPIC_API_KEY"]) from exc

        code, out, err, escaped = self.call(lambda: live_check.cli(["--verdict", "x"], run=run))
        self.assertFalse(escaped)
        self.assertEqual(code, 3)
        self.assertEqual(out, "")
        self.assertEqual(
            err, "실행기 오류 — RuntimeError (내용은 키가 섞일 수 있어 찍지 않습니다)\n"
        )
        assert_no_key(self, out + err)

    def test_cli_catches_keyboard_interrupt(self) -> None:
        def run(argv: object) -> int:
            try:
                raise OSError(KEYS["TYPESAFE_API_KEY"])
            except OSError:
                raise KeyboardInterrupt(KEYS["TYPESAFE_API_KEY"])

        code, out, err, escaped = self.call(lambda: live_check.cli([], run=run))
        self.assertFalse(escaped, "KeyboardInterrupt 가 cli 를 빠져나갔습니다")
        self.assertEqual(code, 3)
        self.assertEqual(
            err.splitlines(),
            ["실행기 오류 — KeyboardInterrupt (내용은 키가 섞일 수 있어 찍지 않습니다)"],
        )
        self.assertNotIn("Traceback", out + err)
        assert_no_key(self, out + err)

    def test_entry_routes_through_cli(self) -> None:
        seen: list[list[str]] = []

        def fake_main(argv: list[str]) -> int:
            seen.append(list(argv))
            raise KeyboardInterrupt(KEYS["YOUTUBE_API_KEY"])

        argv = ["tests.live_check", "--verdict", "x.json"]
        with mock.patch.object(live_check, "main", fake_main), mock.patch.object(
            sys, "argv", argv
        ):
            code, out, err, escaped = self.call(live_check._entry)
        self.assertFalse(escaped, "_entry 가 cli 를 거치지 않았습니다")
        self.assertEqual(code, 3)
        self.assertEqual(seen, [["--verdict", "x.json"]])
        self.assertEqual(
            err.splitlines(),
            ["실행기 오류 — KeyboardInterrupt (내용은 키가 섞일 수 있어 찍지 않습니다)"],
        )
        assert_no_key(self, out + err)


if __name__ == "__main__":
    unittest.main()
