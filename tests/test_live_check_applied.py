"""Phase 6B — 사람이 커밋한 실제 호출 결과(docs/live-check/)를 계약의 기록 · 설정과 맞댑니다.

결과 파일은 믿을 수 없는 입력입니다 — 판정 · 수 · `noul` · 확신 · 점수 · 정답 칸 · 지문 같은 정해진
칸만 읽고, `untrusted` 와 `fingerprint.jev_models` 는 읽지 않습니다. 기록은 계약 '주제 판별' 절 ·
'댓글 작성' 절에 있고, 맞대기와 초록으로 돌아오는 길은 '실제 호출 실행기' 절의 '결과 반영' 입니다.
"""
from __future__ import annotations

import copy
import io
import json
import re
import sys
import tempfile
import unittest
from collections import Counter
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from agent.classifier import LANGUAGES, QUESTION_LANGUAGE, _decide
from agent.config import ClassifierConfig, load_config
from agent.models import Verdict
from agent.writer import (
    CHECK_QUESTIONS,
    INVERTED_QUESTIONS,
    RECENT_WINDOW,
    REPEAT_MIN_CHARS,
    _TOLERANCE,
    self_check_failure,
)
from tests import live_check
from tests.classifier_examples import EXAMPLES
from tests.jev_accuracy import PASS_CORRECT, REPO_CONFIG
from tests.test_live_check import CONFIDENCE_BLOCKED, NOUL_BLOCKED, OVER_ONE, TIE, setting_rows

RESULT_PATH = live_check.RESULT_DIR / live_check.RESULT_NAME
SUMMARY_PATH = live_check.RESULT_DIR / live_check.SUMMARY_NAME
CONTRACT_PATH = live_check.REPO / "docs" / "contracts.md"
BOM = b"\xef\xbb\xbf"
GUARDED = ("questions", "examples_sha256", "classifier.model", "classifier.on_topic_reasons",
           "classifier.off_topic_reasons", "margin", "pass_correct")
RECOUNTED = ("classifier.noul_yes_min", "classifier.noul_no_max",
             "classifier.choice_min_confidence", "check_min_probability")
WRITE_SIDE = ("check_questions", "self_check_criteria", "trigger", "grade_system", "target_drafts",
              "wide_window_hours", "claude_max_retries")
FLOORS = ("noul_yes_min", "noul_no_max", "choice_min_confidence")
TOPIC_ANSWERS = ("연애", "아님")
TRACKER_FLOORS = (0.75, 0.6)  # 트래커 Phase 6D 의 기록 줄(결정 아님)이 본 두 하한 — 기록만
DATE_KEYS = frozenset({"published_at", "published_after", "published_before"})
GO_LINE = "6B: go"
# 트래커 Phase 6F 사람 실행 뒤 인터뷰('6F 예외로 착지') — 작성 막힘인 채로 '6E 뒤' 기록으로 반영한 단 한 실행
AFTER_FIX_RUN_AT = "2026-10-15T08:42:22.401654+00:00"
AFTER_FIX_LINE = "6B: stop — 작성 막힘(SKIP 8/13)"
# 트래커 Phase 6D 드리프트 인터뷰 질문 1 A 가 '고치기 전'(6E 전) 기록으로 반영했던 실행 — 이제 반영하지 않고, 결과
# 파일은 트리에 없습니다.
BEFORE_FIX_RUN_AT = "2026-10-14T14:09:02.882902+00:00"
BEFORE_FIX_LINE = "6B: stop — 작성 막힘(SKIP 5/7)"
WINDOW_LABELS = {"operation": "운영 창", "widened": "넓힌 창"}
ANSWERS = ("ok", "bad")
_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def load_result() -> dict:
    """커밋된 결과 파일 — 손편집 파일 읽기 관례대로 utf-8-sig 로 읽습니다(BOM 은 따로 잡습니다)."""
    return json.loads(RESULT_PATH.read_text(encoding="utf-8-sig"))


def current_fingerprint() -> dict:
    """지금 코드 · config.yaml 의 지문 — `tests/live_check.py (new_result)` 를 그대로 부르고 JSON 으로 한 번 오갑니다."""
    return json.loads(
        json.dumps(
            live_check.new_result(
                load_config(REPO_CONFIG),
                _NOW,
                live_check.DEFAULT_LIMITS,
                live_check.Calls(live_check.CEILINGS),
            )["fingerprint"],
            ensure_ascii=False,
        )
    )


def cell(fingerprint: Mapping[str, object], key: str) -> object:
    """점으로 이은 칸 이름(`classifier.model`)을 따라갑니다 — 길이 끊기면 None."""
    value: object = fingerprint
    for part in key.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def admitted(run_at: object, line: str) -> bool:
    """반영하는 판정 줄인지 — `6B: go` 이거나, '6E 뒤' 기록으로 반영한 한 실행(트래커 Phase 6F)의 그 판정 줄.

    실행 시각과 판정 줄은 글자 그대로 같아야 합니다 — 다른 실행이거나 다른 경우가 섞이면 멈춥니다.
    """
    return line == GO_LINE or (run_at == AFTER_FIX_RUN_AT and line == AFTER_FIX_LINE)


def measured_drift(
    recorded: Mapping[str, object],
    current: Mapping[str, object],
    recounted: Mapping[str, object],
) -> list[str]:
    """맞대기가 다른 칸 — 비어 있어야 기록이 지금 코드를 잰 숫자이고 설정이 규칙대로입니다.

    GUARDED 칸(jev 의 답을 바꾸는 칸)은 결과의 지문과 지금 지문이 같아야 합니다. RECOUNTED 칸
    (하한 셋 · 작성 통과선)은 지금 지문이 결과 파일로 규칙을 다시 셈한 값(`recount`)과 같아야
    합니다 — 다시 셈하지 못한 값(None)과도 다르면 다른 칸입니다. WRITE_SIDE 칸은 읽지 않습니다 —
    이 칸을 지키면 작성 질문이나 채점을 고치는 사이클마다 사람의 재실행이 먼저 있어야 합니다.
    `jev_models` 는 jev 가 알린 글이 검사 없이 들어간 칸이라 믿을 수 없는 글로 보아 읽지 않습니다.
    """
    drift = [key for key in GUARDED if cell(recorded, key) != cell(current, key)]
    return drift + [key for key in RECOUNTED if cell(current, key) != recounted.get(key)]


def stored_verdict_mismatches(result: Mapping[str, object]) -> list[str]:
    """결과의 기준값으로 다시 판정한 값이 저장된 판정 · `self_check_pass` 와 다른 자리.

    다시 셈의 출발점인 결과의 기준값(하한 셋 · `check_min_probability`)을 결과 자신의 저장된
    판정에 묶습니다 — 저장된 판정을 바꾸는 만큼 옮긴 기준값은 여기서 잡힙니다. 오류 행 · 오류
    판별 · `noul` 이 수가 아닌 것과 읽지 못한 초안은 보지 않습니다.
    """
    fingerprint = result["fingerprint"]
    base = live_check.classifier_config(fingerprint["classifier"])
    threshold = fingerprint["check_min_probability"]
    mismatches: list[str] = []
    for language in LANGUAGES:
        for i, row in enumerate(result["accuracy"].get(language, [])):
            if row["error"] or not _number(row["noul"]):
                continue
            stored = row["verdict"]
            decided = _decide(
                row["noul"], row["choice"], row["probability"], row["confidence"], base
            )[0].value
            if decided != stored:
                mismatches.append(f"accuracy.{language}[{i}] {stored} -> {decided}")
    for i, video in enumerate(result["videos"]):
        judged = video["classification"]
        if judged is not None and not judged["error"] and _number(judged["noul"]):
            stored = judged["verdict"]
            decided = _decide(
                judged["noul"], judged["choice"], judged["probability"], judged["confidence"], base
            )[0].value
            if decided != stored:
                mismatches.append(f"videos[{i}] {stored} -> {decided}")
        for n, draft in enumerate(video["drafts"]):
            scores, stored = draft.get("scores"), draft.get("self_check_pass")
            if draft["parsed"] is not True or not isinstance(scores, Mapping):
                continue
            if not isinstance(stored, bool):
                continue
            rechecked = self_check_passes(scores, threshold)
            if rechecked != stored:
                mismatches.append(
                    f"videos[{i}].drafts[{n}] self_check_pass {stored} -> {rechecked}"
                )
    return mismatches


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _window_videos(result: dict, window: str) -> list[dict]:
    return [video for video in result["videos"] if video["window"] == window]


def language_setting(result: dict, language: str) -> tuple[ClassifierConfig, int] | None:
    """한 언어의 예시 행으로 올리기만 범위 최다 맞음 설정(`best_setting`) — 행 수가 예시 수와
    다르면 다시 세지 않습니다."""
    rows = result["accuracy"].get(language, [])
    if not result["example_count"] == len(rows) == len(EXAMPLES):
        raise ValueError(f"예시 행 수가 예시 수와 다릅니다 — 다시 세지 않습니다: {language}")
    return live_check.best_setting(
        rows, live_check.classifier_config(result["fingerprint"]["classifier"])
    )


def reach(result: dict, language: str) -> int | None:
    """올리기만 범위 최다 맞음 — `language_setting` 의 맞음 수."""
    found = language_setting(result, language)
    return None if found is None else found[1]


def passes(best: int | None) -> bool:
    return best is not None and best >= PASS_CORRECT


def floor_language(result: dict) -> str | None:
    """하한 셋을 다시 셀 언어 — `LANGUAGES` 차례로 처음 통과하는 언어, 없으면 None."""
    for language in LANGUAGES:
        if passes(reach(result, language)):
            return language
    return None


def accuracy_lines(result: dict) -> list[str]:
    """언어마다 기록 한 줄 — 지금 기준값의 수와 올리기만 범위 최다 맞음, 통과 · 미달."""
    n = result["example_count"]
    lines: list[str] = []
    for language in LANGUAGES:
        c = result["accuracy_tally"][language]
        best = reach(result, language)
        shown = "잘못된 일치 못 막음" if best is None else f"{best}/{n}"
        lines.append(
            f"{language}: 지금 기준값 맞음 {c['correct']}/{n} · 잘못된 일치 {c['false_yes']}"
            f" · 잘못된 불일치 {c['false_no']} · 보류 {c['hold']} · 오류 {c['error']}"
            f" · 올리기만 범위 최다 맞음 {shown} — {'통과' if passes(best) else '미달'}"
        )
    return lines


def gap_lines(result: dict) -> list[str]:
    """두 `noul` 기준값 사이의 예시 · 영상 — 표본 부족 기록."""
    classifier = result["fingerprint"]["classifier"]
    lo, hi = classifier["noul_no_max"], classifier["noul_yes_min"]
    lines: list[str] = []
    for language in LANGUAGES:
        values = [row["noul"] for row in result["accuracy"][language] if _number(row["noul"])]
        between = sum(1 for noul in values if lo < noul < hi)
        below = max((noul for noul in values if noul <= lo), default=None)
        above = min((noul for noul in values if noul >= hi), default=None)
        lines.append(
            f"{language}: 기준값 사이({lo} 초과 {hi} 미만) 예시 {between}개 · 가장 가까운 예시"
            f" {'없음' if below is None else f'{below:.2f}'}"
            f" · {'없음' if above is None else f'{above:.2f}'}"
        )
    for window, label in WINDOW_LABELS.items():
        if window not in result["windows"]:
            lines.append(f"기준값 사이 영상 {label}: 실행 없음")
            continue
        videos = _window_videos(result, window)
        nouls = [video["classification"]["noul"] for video in videos]
        k = sum(1 for noul in nouls if _number(noul) and lo < noul < hi)
        lines.append(f"기준값 사이 영상 {label}: {k}/{len(videos)}")
    return lines


def classification_lines(result: dict) -> list[str]:
    """창마다 영상 판별 수 — 일치 · 보류 · 불일치."""
    lines: list[str] = []
    for window, label in WINDOW_LABELS.items():
        if window not in result["windows"]:
            lines.append(f"영상 판별 {label}: 실행 없음")
            continue
        videos = _window_videos(result, window)
        v = Counter(video["classification"]["verdict"] for video in videos)
        lines.append(
            f"영상 판별 {label}: 판별 {len(videos)} · 일치 {v['yes']} · 보류 {v['hold']}"
            f" · 불일치 {v['no']}"
        )
    return lines


def draft_answer(draft: Mapping[str, object]) -> str | None:
    """초안의 정답 — 사람 칸(`ok` · `bad`)이 있으면 그것, 없으면 Claude 채점, 둘 다 없으면 None."""
    if draft["human"] in ANSWERS:
        return draft["human"]
    if draft["claude_grade"] in ANSWERS:
        return draft["claude_grade"]
    return None


def draft_counts(result: dict, window: str) -> dict[str, int]:
    """창 하나의 쓴 영상 · 초안 수 — 정답은 사람 칸(`ok` · `bad`)이 있으면 그것, 없으면 Claude 채점."""
    videos = _window_videos(result, window)
    outcomes = Counter(video["result"] for video in videos)
    drafts = [draft for video in videos for draft in video["drafts"] if draft["parsed"] is True]
    counts = {
        "written": outcomes["comment"] + outcomes["skip"],
        "skip": outcomes["skip"],
        "drafts": len(drafts),
        "human": 0,
        "claude": 0,
        "answered": 0,
        "grade_errors": 0,
        "differ": 0,
        "bad_passed": 0,
        "ok_failed": 0,
    }
    for draft in drafts:
        human = draft["human"] if draft["human"] in ANSWERS else None
        claude = draft["claude_grade"] if draft["claude_grade"] in ANSWERS else None
        answer = draft_answer(draft)
        counts["human"] += human is not None
        counts["claude"] += claude is not None
        counts["answered"] += answer is not None
        counts["grade_errors"] += draft["grade_error"] is not None
        counts["differ"] += human is not None and claude is not None and human != claude
        counts["bad_passed"] += answer == "bad" and draft["self_check_pass"] is True
        counts["ok_failed"] += answer == "ok" and draft["self_check_pass"] is False
    return counts


def draft_lines(result: dict) -> list[str]:
    """창마다 초안 기록 한 줄."""
    lines: list[str] = []
    for window, label in WINDOW_LABELS.items():
        if window not in result["windows"]:
            lines.append(f"초안 {label}: 실행 없음")
            continue
        c = draft_counts(result, window)
        lines.append(
            f"초안 {label}: 쓴 영상 {c['written']} · SKIP {c['skip']} · 초안 {c['drafts']}"
            f" · 정답 있음 {c['answered']} (사람 칸 {c['human']} · Claude 채점 {c['claude']})"
            f" · 채점 오류 {c['grade_errors']} · 사람 칸과 Claude 채점이 다름 {c['differ']}"
            f" · 정답 bad 인데 통과 {c['bad_passed']} · 정답 ok 인데 탈락 {c['ok_failed']}"
        )
    return lines


def model_line(result: dict) -> str:
    """모델 이름 확인 — MODEL_NAMES 차례(result.json 은 키 정렬이라 그 차례를 쓰지 않습니다)."""
    names = " · ".join(
        f"{name} {result['models'][name]['status']}" for name in live_check.MODEL_NAMES
    )
    return f"모델 이름: {names} — 작성 {result['writer_model']} · 채점 {result['grader_model']}"


def _parsed_drafts(result: dict) -> list[dict]:
    return [
        draft for video in result["videos"] for draft in video["drafts"] if draft["parsed"] is True
    ]


def lowest_score(scores: Mapping[str, float]) -> float:
    """초안의 가장 낮은 비교 점수 — 그 초안 `scores` 의 질문 이름마다 P(예), '예' 가 나쁜 질문은 1 − P(예).

    질문 이름은 실행 때의 CHECK_QUESTIONS 라 판마다 다릅니다(6D 셋 · 6E 뒤 다섯). 비었거나 지금 코드에
    없는 이름이 하나라도 있으면 ValueError — 모르는 이름을 건너뛰면 통과선 맞대기가 느슨해집니다.
    """
    unknown = sorted(name for name in scores if name not in CHECK_QUESTIONS)
    if unknown or not scores:
        raise ValueError(f"초안 점수의 질문 이름을 셀 수 없습니다: {unknown}")
    return min(
        1.0 - value if name in INVERTED_QUESTIONS else value for name, value in scores.items()
    )


def self_check_passes(scores: Mapping[str, float], threshold: float) -> bool:
    """초안 자신의 질문 이름으로 다시 판정한 자체 검사 통과 — `src/agent/writer.py (self_check_failure)` 와 같은 비교.

    writer 는 이름마다 `score + _TOLERANCE < threshold` 이면 떨어뜨리므로, 통과는 가장 낮은 점수에
    `_TOLERANCE` 를 더해 하한 이상인 것과 같습니다(덧셈은 단조). 결과의 초안은 실행 때 질문만 담습니다.
    """
    return lowest_score(scores) + _TOLERANCE >= threshold


def passed_answered(result: dict) -> list[dict]:
    """두 창의 읽은 초안 가운데 자체 검사를 통과하고 정답이 있는 초안."""
    return [
        draft
        for draft in _parsed_drafts(result)
        if draft["self_check_pass"] is True and draft_answer(draft) is not None
    ]


def blocking_drafts(result: dict) -> list[dict]:
    """정답 bad 인데 자체 검사를 통과한 초안 — 통과선이 막아야 할 초안."""
    return [draft for draft in passed_answered(result) if draft_answer(draft) == "bad"]


def check_floor(result: dict) -> float | None:
    """작성 통과선을 결과로 다시 셈한 값 — 막을 초안이 없으면 결과의 값 그대로.

    막을 초안이 있으면 그 초안들의 가장 낮은 비교 점수 중 가장 높은 값 + `MARGIN` 이고, 결과의
    값보다 내리지 않습니다. 1 을 넘으면 None(막을 수 없음).
    """
    value = result["fingerprint"]["check_min_probability"]
    blocking = blocking_drafts(result)
    if not blocking:
        return value
    raised = round(max(lowest_score(draft["scores"]) for draft in blocking) + live_check.MARGIN, 6)
    if raised > 1:
        return None
    return max(value, raised)


def recount(result: dict) -> dict[str, object]:
    """RECOUNTED 칸을 결과 파일로 다시 셈한 값 — 하한 셋은 처음 통과하는 언어의 최다 맞음 설정
    (통과하는 언어가 없으면 None), 통과선은 `check_floor`."""
    language = floor_language(result)
    found = None if language is None else language_setting(result, language)
    recounted: dict[str, object] = {
        f"classifier.{name}": None if found is None else getattr(found[0], name) for name in FLOORS
    }
    recounted["check_min_probability"] = check_floor(result)
    return recounted


def recount_line(result: dict) -> str:
    """다시 셈한 하한 셋의 기록 줄 — 진짜 jev 를 그 설정으로 돌린 숫자가 아님을 함께 적습니다."""
    language = floor_language(result)
    if language is None:
        return "다시 셈한 기준값: 없음 — 두 언어 모두 미달"
    setting, correct = language_setting(result, language)
    return (
        f"다시 셈한 기준값({language} 예시 행): `noul_yes_min` {setting.noul_yes_min}"
        f" · `noul_no_max` {setting.noul_no_max}"
        f" · `choice_min_confidence` {setting.choice_min_confidence}"
        f" · 맞음 {correct}/{result['example_count']}"
        " — 같은 jev 답을 6B 규칙으로 다시 셈한 값이고, 진짜 jev 를 이 설정으로 돌린 숫자가 아닙니다"
    )


def language_phrase(result: dict) -> str:
    """질문 언어 문구 — 지금 `QUESTION_LANGUAGE` 와 통과 · 미달 언어."""
    passing = [language for language in LANGUAGES if passes(reach(result, language))]
    failing = [language for language in LANGUAGES if language not in passing]
    return (
        f"`QUESTION_LANGUAGE` 는 `{QUESTION_LANGUAGE}` 그대로입니다"
        f" — 통과 {' · '.join(passing) or '없음'} · 미달 {' · '.join(failing) or '없음'}"
    )


def check_floor_line(result: dict) -> str:
    """작성 통과선의 기록 줄 — 통과선이 기대는 근거(정답 있고 통과한 초안 · 그 가운데 사람 칸)."""
    passed = passed_answered(result)
    humans = sum(1 for draft in passed if draft["human"] in ANSWERS)
    blocking = blocking_drafts(result)
    value = check_floor(result)
    if not passed:
        return (
            "정답 있고 자체 검사를 통과한 초안이 0 이라"
            f" `check_min_probability` 는 {value} 그대로입니다(표본 없음)"
        )
    if not blocking:
        return (
            f"정답 있고 자체 검사를 통과한 초안 {len(passed)}(사람 칸 {humans}) 가운데 정답 bad 가"
            f" 0 이라 `check_min_probability` 는 {value} 그대로입니다(근거가 있어 그대로)"
        )
    top = max(lowest_score(draft["scores"]) for draft in blocking)
    return (
        f"정답 bad 인데 자체 검사를 통과한 초안 {len(blocking)} 의 가장 낮은 비교 점수 중 가장"
        f" 높은 값 {top:.2f} + {live_check.MARGIN} 으로 `check_min_probability` 를 {value} 로"
        " 올렸습니다 — 같은 초안 답을 다시 셈한 값이고, 진짜 jev 를 이 통과선으로 돌린 숫자가 아닙니다"
    )


def topic_answer(video: Mapping[str, object]) -> str | None:
    """영상 판별의 정답 — 사람 칸(`연애` · `아님`)이 있으면 그것, 없으면 Claude 채점, 둘 다 없으면 None."""
    if video["topic_human"] in TOPIC_ANSWERS:
        return video["topic_human"]
    if video["topic_grade"] in TOPIC_ANSWERS:
        return video["topic_grade"]
    return None


def topic_grade_lines(result: dict) -> list[str]:
    """창마다 진짜 영상 판별의 일치 · 보류 · 불일치와 정답이 엇갈린 수 — 기록만."""
    lines: list[str] = []
    for window, label in WINDOW_LABELS.items():
        if window not in result["windows"]:
            lines.append(f"영상 판별 채점 {label}: 실행 없음")
            continue
        judged = [
            video
            for video in _window_videos(result, window)
            if video["classification"] is not None
        ]

        def among(verdict: str, answer: str) -> tuple[int, int]:
            group = [video for video in judged if video["classification"]["verdict"] == verdict]
            return len(group), sum(1 for video in group if topic_answer(video) == answer)

        (y, a), (h, b), (n, c) = among("yes", "아님"), among("hold", "연애"), among("no", "연애")
        none = sum(1 for video in judged if topic_answer(video) is None)
        humans = sum(1 for video in judged if video["topic_human"] in TOPIC_ANSWERS)
        lines.append(
            f"영상 판별 채점 {label}: 일치 {y} 중 정답 아님 {a} · 보류 {h} 중 정답 연애 {b}"
            f" · 불일치 {n} 중 정답 연애 {c} · 정답 없음 {none} · 사람 칸 {humans}/{len(judged)}"
        )
    return lines


def lowering_lines(result: dict) -> list[str]:
    """창마다 `noul_yes_min` 만 트래커가 본 두 하한으로 내리면 새로 일치가 되는 보류 영상 수 — 기록만."""
    base = live_check.classifier_config(result["fingerprint"]["classifier"])
    lines: list[str] = []
    for window, label in WINDOW_LABELS.items():
        if window not in result["windows"]:
            lines.append(f"보류 영상 하한 내림 {label}: 실행 없음")
            continue
        holds = [
            video
            for video in _window_videos(result, window)
            if video["classification"] is not None
            and video["classification"]["verdict"] == "hold"
            and not video["classification"]["error"]
            and _number(video["classification"]["noul"])
        ]
        parts: list[str] = []
        for floor in TRACKER_FLOORS:
            lowered = replace(base, noul_yes_min=floor)
            turned = Counter(
                topic_answer(video)
                for video in holds
                if _decide(
                    video["classification"]["noul"],
                    video["classification"]["choice"],
                    video["classification"]["probability"],
                    video["classification"]["confidence"],
                    lowered,
                )[0]
                is Verdict.YES
            )
            parts.append(
                f"`noul_yes_min` {floor} 이면 새 일치 — 정답 연애 {turned['연애']}"
                f" · 정답 아님 {turned['아님']} · 정답 없음 {turned[None]}"
            )
        lines.append(f"보류 영상 하한 내림 {label}: " + " / ".join(parts))
    return lines


def task_counts(result: dict, window: str | None) -> dict[str, int]:
    """과제 품질 · 인기 댓글 · 작성 수 — `window` 가 None 이면 모든 영상."""
    videos = result["videos"] if window is None else _window_videos(result, window)
    outcomes = Counter(video["result"] for video in videos)
    attempts = [draft for video in videos for draft in video["drafts"]]
    drafts = [draft for draft in attempts if draft["parsed"] is True]
    tasks = [
        draft["task_quality"] for draft in drafts if isinstance(draft["task_quality"], Mapping)
    ]
    overlaps = [draft["frame_overlap"] for draft in drafts if _number(draft["frame_overlap"])]
    return {
        "written": outcomes["comment"] + outcomes["skip"],
        "skip": outcomes["skip"],
        "drafts": len(drafts),
        "unparsed": len(attempts) - len(drafts),
        "tasks": len(tasks),
        "love": sum(1 for task in tasks if task.get("concern_is_love_worry") is True),
        "saju": sum(1 for task in tasks if task.get("saju_story_fits") is True),
        "task_errors": sum(1 for draft in drafts if draft["task_error"] is not None),
        "framed": sum(1 for overlap in overlaps if overlap > 0),
        "most": max(overlaps, default=0),
        "popular": sum(
            1
            for video in videos
            if video["material"] == "top_comments"
            for draft in video["drafts"]
            if draft["parsed"] is True
        ),
        "empty_items": sum(
            1
            for video in videos
            if isinstance(video["comment_items"], int)
            and not isinstance(video["comment_items"], bool)
            and video["comment_items"] > 0
            and video["top_comment_count"] == 0
        ),
    }


def task_lines(result: dict) -> list[str]:
    """창마다 과제 품질 · 인기 댓글 기록 두 줄 — 기록만이고 통과선을 움직이지 않습니다."""
    lines: list[str] = []
    for window, label in WINDOW_LABELS.items():
        if window not in result["windows"]:
            lines += [f"과제 품질 {label}: 실행 없음", f"인기 댓글 {label}: 실행 없음"]
            continue
        c = task_counts(result, window)
        lines += [
            f"과제 품질 {label}: ⓐ 고민 한 줄이 연애 고민 {c['love']}/{c['tasks']}"
            f" · ⓑ 연애사주 경험이 고민과 이어짐 {c['saju']}/{c['tasks']}"
            f" · 과제 칸 오류 {c['task_errors']}"
            f" · ⓒ 다른 영상 초안과 겹치는 {live_check.FRAME_CHARS}글자 조각이 있는 초안"
            f" {c['framed']}/{c['drafts']} · 겹친 조각 최다 {c['most']}",
            f"인기 댓글 {label}: 재료 초안 {c['popular']}"
            f" · 항목은 왔는데 글 0개인 영상 {c['empty_items']}",
        ]
    return lines


def todo_line(result: dict) -> str:
    """보고서 첫머리의 6E 줄 — 이번 결과는 늘 "할 일 있음"(트래커 Phase 6D 드리프트 인터뷰 질문 3 A)."""
    c = task_counts(result, None)
    return (
        f"6E: 할 일 있음 — ⓐ 고민 한 줄이 연애 고민 {c['love']}/{c['tasks']}"
        f" · ⓑ 연애사주 경험이 고민과 이어짐 {c['saju']}/{c['tasks']}"
        f" · ⓒ 다른 영상 초안과 겹치는 {live_check.FRAME_CHARS}글자 조각이 있는 초안"
        f" {c['framed']}/{c['drafts']} · 건너뜀 SKIP {c['skip']}/{c['written']}"
        f" · 작성기 답을 JSON 으로 못 읽은 초안 {c['unparsed']}/{c['drafts']}"
    )


def mark_text(value: object, path: str = "") -> object:
    """글 칸마다 표식을 심은 복사본 — 모든 글 잎은 `MRK·<경로>` 가 됩니다.

    `video_id` 는 `MRK` 와 그 영상 차례 8자리(11글자), DATE_KEYS 아래 값과 수 · 참거짓 · None 은
    그대로입니다.
    """
    if isinstance(value, Mapping):
        marked: dict[str, object] = {}
        for key, item in value.items():
            if key in DATE_KEYS:
                marked[key] = item
            elif key == "video_id" and isinstance(item, str):
                index = re.search(r"\[([0-9]+)\]\Z", path)
                marked[key] = f"MRK{int(index.group(1)) if index else 0:08d}"
            else:
                marked[key] = mark_text(item, f"{path}.{key}" if path else key)
        return marked
    if isinstance(value, list):
        return [mark_text(item, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, str):
        return f"MRK·{path}"
    return value


def normalize(text: str) -> str:
    return " ".join(text.split())


def record_heads() -> list[str]:
    """기록 줄의 머리 — 기록 줄을 만드는 함수들의 앞머리를 `LANGUAGES` · `WINDOW_LABELS` 로 만듭니다."""
    heads: list[str] = []
    for language in LANGUAGES:
        heads += [f"{language}: 지금 기준값 맞음", f"{language}: 기준값 사이"]
    heads.append("다시 셈한 기준값")
    for label in WINDOW_LABELS.values():
        heads += [f"기준값 사이 영상 {label}:", f"영상 판별 {label}:", f"초안 {label}:"]
        heads += [
            f"영상 판별 채점 {label}:",
            f"보류 영상 하한 내림 {label}:",
            f"과제 품질 {label}:",
            f"인기 댓글 {label}:",
        ]
    heads.append("모델 이름:")
    return heads


def head_counts(text: str) -> dict[str, int]:
    """머리마다 그 머리로 시작하는 줄 수 — 줄은 공백을 접고 앞의 `- ` 를 뗀 뒤 봅니다."""
    lines = [normalize(line).removeprefix("- ") for line in text.splitlines()]
    return {head: sum(1 for line in lines if line.startswith(head)) for head in record_heads()}


class ContractCase(unittest.TestCase):
    """계약에 기록 문구가 있는지 — 공백을 하나로 접어 비교합니다."""

    def assert_in_contract(self, phrase: str) -> None:
        """숫자로 끝나는 기록은 계약에서 뒤에 숫자나 `.숫자` 가 이어지지 않는 자리만 셉니다."""
        normalized_phrase = normalize(phrase)
        normalized_contract = normalize(CONTRACT_PATH.read_text(encoding="utf-8-sig"))
        found = normalized_phrase in normalized_contract
        if found and re.search(r"[0-9]\Z", normalized_phrase):
            found = (
                re.search(re.escape(normalized_phrase) + r"(?![0-9]|\.[0-9])", normalized_contract)
                is not None
            )
        self.assertTrue(found, f"계약에 없는 기록: {phrase}")


class ContractBoundaryTest(ContractCase):
    """`assert_in_contract` 의 숫자 경계 — 숫자로 끝나는 기록 뒤에 숫자가 이어지면 없는 기록입니다."""

    def _check(self, text: str, phrase: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contracts.md"
            path.write_text(text, encoding="utf-8")
            with mock.patch.object(sys.modules[__name__], "CONTRACT_PATH", path):
                self.assert_in_contract(phrase)

    def test_longer_number_does_not_satisfy_phrase(self) -> None:
        with self.assertRaises(AssertionError):
            self._check("탈락 05", "탈락 0")

    def test_number_followed_by_space_or_end_satisfies_phrase(self) -> None:
        for text in ("탈락 0 · 끝", "탈락 0"):
            with self.subTest(text=text):
                self._check(text, "탈락 0")


class ContractHeadTest(unittest.TestCase):
    """기록 머리는 계약에 한 번씩 — 같은 머리에 다른 숫자를 단 모순된 중복 줄을 잡습니다."""

    def test_each_record_head_appears_once(self) -> None:
        counts = head_counts(CONTRACT_PATH.read_text(encoding="utf-8-sig"))
        for head, count in counts.items():
            with self.subTest(head=head):
                self.assertEqual(count, 1, f"계약에 이 머리의 기록 줄이 {count}개입니다: {head}")

    def test_every_record_line_starts_with_one_head(self) -> None:
        result = load_result()
        heads = record_heads()
        lines = [
            *accuracy_lines(result),
            recount_line(result),
            *gap_lines(result),
            *classification_lines(result),
            *topic_grade_lines(result),
            *lowering_lines(result),
            *draft_lines(result),
            *task_lines(result),
            model_line(result),
        ]
        for line in lines:
            with self.subTest(line=line):
                self.assertEqual(sum(1 for head in heads if line.startswith(head)), 1)

    def test_contradicting_duplicate_line_is_counted(self) -> None:
        duplicate = (
            "- en: 지금 기준값 맞음 12/22 · 잘못된 일치 3 · 잘못된 불일치 0 · 보류 7 · 오류 0"
            " · 올리기만 범위 최다 맞음 12/22 — 미달"
        )
        text = CONTRACT_PATH.read_text(encoding="utf-8-sig") + "\n" + duplicate + "\n"
        self.assertEqual(head_counts(text)["en: 지금 기준값 맞음"], 2)


class CommittedResultTest(unittest.TestCase):
    """첫 단계 문 — 결과 두 파일 · 판정 줄 · 예시 행 수 · 지문(트래커 Phase 6B 결정 1–2, H-050)."""

    def test_result_and_summary_are_committed_without_bom(self) -> None:
        for path in (RESULT_PATH, SUMMARY_PATH):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"결과 파일이 없습니다 — unmeasured: {path.name}")
                self.assertFalse(
                    path.read_bytes().startswith(BOM), f"BOM 이 있습니다 — unmeasured: {path.name}"
                )

    def test_result_is_schema_two(self) -> None:
        self.assertGreaterEqual(
            load_result()["schema_version"],
            live_check.GRADE_BLOCK_SCHEMA,
            "판 1 결과입니다 — unmeasured(6C 뒤의 실행기로 다시 돌려 레인 브랜치에 커밋)",
        )

    def test_verdict_recount_is_admitted(self) -> None:
        result = load_result()
        line = live_check.verdict_line(result)
        self.assertTrue(admitted(result["run_at"], line), f"반영하지 않는 판정 줄입니다: {line}")
        out, err = io.StringIO(), io.StringIO()
        code = live_check.verdict_from_file(RESULT_PATH, out, err)
        self.assertEqual(
            (code, out.getvalue(), err.getvalue()),
            (0 if line == GO_LINE else 1, line + "\n", ""),
        )

    def test_summary_first_line_is_the_recount(self) -> None:
        result = load_result()
        first = SUMMARY_PATH.read_text(encoding="utf-8-sig").splitlines()[0]
        self.assertEqual(first, live_check.verdict_line(result))
        self.assertTrue(admitted(result["run_at"], first), f"반영하지 않는 판정 줄입니다: {first}")

    def test_example_rows_match_example_count(self) -> None:
        result = load_result()
        self.assertEqual(result["example_count"], len(EXAMPLES))
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.assertEqual(len(result["accuracy"][language]), result["example_count"])

    def test_stored_verdicts_follow_recorded_floors(self) -> None:
        self.assertEqual(
            stored_verdict_mismatches(load_result()),
            [],
            "결과의 기준값이 결과 자신의 저장된 판정과 맞지 않습니다 — 결과의 기준값을 옮겼습니다",
        )

    def test_committed_result_matches_code(self) -> None:
        result = load_result()
        self.assertEqual(
            measured_drift(result["fingerprint"], current_fingerprint(), recount(result)),
            [],
            "결과의 지문이 지금 코드와 다르거나 설정이 다시 셈한 값과 다릅니다"
            " — '실제 호출 실행기' 절의 '결과 반영'",
        )


class AdmittedTest(ContractCase):
    """`admitted` — `6B: go` 와, '6E 뒤' 기록으로 반영한 한 실행의 한 판정 줄만(트래커 Phase 6F
    사람 실행 뒤 인터뷰 — '6F 예외로 착지'). 6D 가 반영한 실행은 이제 빨강 표본입니다."""

    RUN = "2026-10-15T08:42:22.401654+00:00"
    LINE = "6B: stop — 작성 막힘(SKIP 8/13)"
    OLD = ("2026-10-14T14:09:02.882902+00:00", "6B: stop — 작성 막힘(SKIP 5/7)")
    GREEN = (
        ("2026-10-20T00:00:00+00:00", "6B: go"),
        (RUN, LINE),
    )
    RED = (
        OLD,
        (OLD[0], LINE),
        (RUN, OLD[1]),
        ("2026-10-15T08:20:33+00:00", LINE),
        ("2026-10-15T08:42:22+00:00", LINE),
        ("2026-10-15T08:42:22.401654Z", LINE),
        (" 2026-10-15T08:42:22.401654+00:00", LINE),
        (RUN, "6B: stop — 작성 막힘(SKIP 8/13); 채점 막힘(오류 6/11)"),
        (RUN, "6B: stop — 작성 막힘(SKIP 7/13)"),
        (RUN, "6B: stop - 작성 막힘(SKIP 8/13)"),
        (RUN, "6B: stop – 작성 막힘(SKIP 8/13)"),
        (RUN, "6B: stop — 작성 막힘(SKIP ８/13)"),
        (RUN, "6B: stop —  작성 막힘(SKIP 8/13)"),
        (RUN, "6b: stop — 작성 막힘(SKIP 8/13)"),
        (RUN, "6B: stop — 작성 막힘(SKIP 8/13) "),
    )

    def test_green_samples_are_admitted(self) -> None:
        for run_at, line in self.GREEN:
            with self.subTest(run_at=run_at, line=line):
                self.assertTrue(admitted(run_at, line))

    def test_near_miss_samples_are_refused(self) -> None:
        for run_at, line in self.RED:
            with self.subTest(run_at=run_at, line=line):
                self.assertFalse(admitted(run_at, line))

    def test_exception_is_written_in_contract(self) -> None:
        for phrase in (
            f"예외는 하나뿐입니다 — 실행 `{AFTER_FIX_RUN_AT}` 의 `{AFTER_FIX_LINE}`",
            f"실행 `{BEFORE_FIX_RUN_AT}` 의 `{BEFORE_FIX_LINE}` 도 이제 빨강입니다",
        ):
            with self.subTest(phrase=phrase):
                self.assert_in_contract(phrase)


def _with_cell(fingerprint: Mapping[str, object], key: str, value: object) -> dict:
    """지문의 깊은 복사본에서 점으로 이은 칸 하나를 바꿉니다."""
    changed = copy.deepcopy(dict(fingerprint))
    *path, last = key.split(".")
    target = changed
    for part in path:
        target = target[part]
    target[last] = value
    return changed


class MeasuredDriftTest(unittest.TestCase):
    """`measured_drift` 의 손이 닿는 곳 — 지키는 칸 · 다시 셈한 칸 · 작성 쪽 칸 · `jev_models` · 칸 나눔."""

    def setUp(self) -> None:
        self.result = load_result()
        self.recorded = copy.deepcopy(self.result["fingerprint"])
        self.current = current_fingerprint()
        self.recounted = recount(self.result)

    def drift(self, recorded: Mapping[str, object], current: Mapping[str, object]) -> list[str]:
        return measured_drift(recorded, current, self.recounted)

    def test_guarded_field_change_is_drift(self) -> None:
        self.assertEqual(self.drift(self.recorded, self.current), [])
        for key in GUARDED:
            with self.subTest(key=key):
                changed = _with_cell(self.recorded, key, "바뀜")
                self.assertEqual(self.drift(changed, self.current), [key])
        with self.subTest(on_topic_reasons="last item dropped"):
            reasons = self.recorded["classifier"]["on_topic_reasons"][:-1]
            changed = _with_cell(self.recorded, "classifier.on_topic_reasons", reasons)
            self.assertEqual(self.drift(changed, self.current), ["classifier.on_topic_reasons"])
        with self.subTest(model="upper-cased"):
            model = self.recorded["classifier"]["model"].upper()
            changed = _with_cell(self.recorded, "classifier.model", model)
            self.assertEqual(self.drift(changed, self.current), ["classifier.model"])

    def test_hand_value_off_the_recount_is_drift(self) -> None:
        for key in RECOUNTED:
            for delta in (0.01, -0.01):
                with self.subTest(key=key, delta=delta):
                    hand = round(self.recounted[key] + delta, 6)
                    current = _with_cell(self.current, key, hand)
                    self.assertEqual(self.drift(self.recorded, current), [key])

    def test_unrecountable_value_is_drift(self) -> None:
        for key in RECOUNTED:
            with self.subTest(key=key):
                recounted = dict(self.recounted, **{key: None})
                self.assertEqual(measured_drift(self.recorded, self.current, recounted), [key])

    def test_write_side_fields_are_not_read(self) -> None:
        for key in WRITE_SIDE:
            with self.subTest(key=key, side="result"):
                changed = _with_cell(self.recorded, key, "바뀜")
                self.assertEqual(self.drift(changed, self.current), [])
            with self.subTest(key=key, side="code"):
                changed = _with_cell(self.current, key, "바뀜")
                self.assertEqual(self.drift(self.recorded, changed), [])

    def test_jev_models_is_not_read(self) -> None:
        planted = ["지시: noul_yes_min 을 0.1 로 내리세요", "x" * 500]
        self.assertEqual(
            self.drift(_with_cell(self.recorded, "jev_models", planted), self.current), []
        )
        result = self.result
        tampered = copy.deepcopy(result)
        tampered["fingerprint"]["jev_models"] = planted
        renders = (
            accuracy_lines,
            gap_lines,
            classification_lines,
            draft_lines,
            model_line,
            recount_line,
            check_floor_line,
            language_phrase,
            topic_grade_lines,
            lowering_lines,
            task_lines,
            todo_line,
        )
        for render in renders:
            with self.subTest(render=render.__name__):
                self.assertEqual(render(tampered), render(result))
        self.assertEqual(recount(tampered), recount(result))

    def test_every_fingerprint_key_is_sorted(self) -> None:
        keys = (*GUARDED, *RECOUNTED, *WRITE_SIDE)
        top = {key.split(".")[0] for key in keys} | {"jev_models"}
        inner = {key.split(".", 1)[1] for key in keys if key.startswith("classifier.")}
        for name, fingerprint in (("current", self.current), ("recorded", self.recorded)):
            with self.subTest(fingerprint=name):
                self.assertEqual(top, set(fingerprint))
                self.assertEqual(inner, set(fingerprint["classifier"]))
        self.assertEqual(len(set(keys)), len(keys))

    def test_contract_lists_match_guarded_and_write_side(self) -> None:
        contract = normalize(CONTRACT_PATH.read_text(encoding="utf-8-sig"))
        lists = (("GUARDED", GUARDED), ("RECOUNTED", RECOUNTED), ("WRITE_SIDE", WRITE_SIDE))
        for name, keys in lists:
            with self.subTest(keys=name):
                listed = " · ".join(f"`{key}`" for key in keys)
                self.assertTrue(
                    listed in contract, f"계약 '결과 반영' 의 칸 목록이 {name} 와 다릅니다: {listed}"
                )


SCORE_NAMES = ("mentions_scene", "reads_like_ad", "follows_concern")
PASSING_SCORES = (0.9, 0.1, 0.9)
FAILING_SCORES = (0.5, 0.1, 0.9)
NO_SAMPLE_LINE = "정답 있고 자체 검사를 통과한 초안이 0 이라 `check_min_probability` 는 0.7 그대로입니다(표본 없음)"


class RecountTest(unittest.TestCase):
    """`recount` — 결과 파일로 6B 규칙을 다시 셈한 하한 셋 · 통과선(트래커 Phase 6D 인터뷰 질문 1 A).

    가짜 결과는 커밋된 결과의 깊은 복사본에 `setting_rows` 모양의 예시 행(심지 않으면 두 언어
    모두 건강), 커밋된 `fingerprint.classifier`, `check_min_probability` 0.7, 운영 창 영상 하나를
    둡니다.
    """

    @staticmethod
    def fake(
        ko: tuple[dict, ...] = (),
        en: tuple[dict, ...] = (),
        drafts: tuple[dict, ...] = (),
        classification: dict | None = None,
    ) -> dict:
        result = copy.deepcopy(load_result())
        template = next(video for video in result["videos"] if video["result"] == "comment")
        result["accuracy"] = {"ko": setting_rows(*ko), "en": setting_rows(*en)}
        result["fingerprint"]["check_min_probability"] = 0.7
        if classification is None:
            classification = {
                "verdict": "yes",
                "error": False,
                "noul": 0.95,
                "choice": result["fingerprint"]["classifier"]["on_topic_reasons"][0],
                "probability": 0.9,
                "confidence": 0.9,
            }
        template.update(window="operation", classification=classification, drafts=list(drafts))
        result["videos"] = [template]
        return result

    @staticmethod
    def draft(
        scores: tuple[float, float, float] = PASSING_SCORES,
        *,
        human: str = "",
        claude: str | None = "ok",
        passed: bool = True,
    ) -> dict:
        result = load_result()
        found = next(
            draft
            for video in result["videos"]
            for draft in video["drafts"]
            if draft["parsed"] is True
        )
        draft = copy.deepcopy(found)
        draft.update(
            scores=dict(zip(SCORE_NAMES, scores)),
            human=human,
            claude_grade=claude,
            grade_error=None if claude is not None else "응답 모양",
            self_check_pass=passed,
        )
        return draft

    @staticmethod
    def floors(result: dict) -> tuple[object, ...]:
        recounted = recount(result)
        return tuple(recounted[f"classifier.{name}"] for name in FLOORS)

    def setUp(self) -> None:
        self.current = current_fingerprint()

    def drift(self, fake: dict, current: dict | None = None) -> list[str]:
        cur = self.current if current is None else current
        return measured_drift(self.current, cur, recount(fake))

    def test_noul_blocked_false_yes_raises_yes_floor(self) -> None:
        fake = self.fake(ko=(NOUL_BLOCKED,))
        self.assertEqual(self.floors(fake), (0.88, 0.2, 0.5))
        self.assertEqual(self.drift(fake), ["classifier.noul_yes_min"])
        raised = _with_cell(self.current, "classifier.noul_yes_min", 0.88)
        self.assertEqual(self.drift(fake, raised), [])

    def test_confidence_blocked_false_yes_raises_confidence_floor(self) -> None:
        self.assertEqual(self.floors(self.fake(ko=(CONFIDENCE_BLOCKED,))), (0.8, 0.2, 0.65))

    def test_tie_takes_the_least_raised(self) -> None:
        fake = self.fake(ko=(TIE,))
        reversed_fake = copy.deepcopy(fake)
        reversed_fake["accuracy"]["ko"].reverse()
        for name, result in (("rows", fake), ("reversed", reversed_fake)):
            with self.subTest(order=name):
                self.assertEqual(self.floors(result), (0.8, 0.2, 0.65))

    def test_failed_ko_takes_en_rows(self) -> None:
        for en, expected in (((), (0.8, 0.2, 0.5)), ((NOUL_BLOCKED,), (0.88, 0.2, 0.5))):
            with self.subTest(en=en):
                fake = self.fake(ko=(OVER_ONE,), en=en)
                self.assertIsNone(reach(fake, "ko"))
                self.assertEqual(floor_language(fake), "en")
                setting, _ = language_setting(fake, "en")
                self.assertEqual(
                    self.floors(fake), tuple(getattr(setting, name) for name in FLOORS)
                )
                self.assertEqual(self.floors(fake), expected)

    def test_both_languages_failing_is_drift(self) -> None:
        fake = self.fake(ko=(OVER_ONE,), en=(OVER_ONE,))
        self.assertIsNone(floor_language(fake))
        self.assertEqual(self.floors(fake), (None, None, None))
        self.assertEqual(self.drift(fake), [f"classifier.{name}" for name in FLOORS])
        self.assertEqual(recount_line(fake), "다시 셈한 기준값: 없음 — 두 언어 모두 미달")

    def test_same_result_gives_one_recount(self) -> None:
        fake = self.fake(ko=(TIE,), drafts=(self.draft((0.71, 0.1, 0.9), claude="bad"),))
        first = recount(fake)
        self.assertEqual(recount(copy.deepcopy(fake)), first)
        self.assertEqual(recount(fake), first)

    def test_check_floor_without_passed_answers_keeps_value(self) -> None:
        cases = {
            "no answer": (self.draft(claude=None),),
            "all failed self-check": (
                self.draft(FAILING_SCORES, human="ok", passed=False),
                self.draft(FAILING_SCORES, claude="bad", passed=False),
            ),
        }
        for name, drafts in cases.items():
            with self.subTest(case=name):
                fake = self.fake(drafts=drafts)
                self.assertEqual(check_floor(fake), 0.7)
                self.assertEqual(check_floor_line(fake), NO_SAMPLE_LINE)

    def test_check_floor_with_passed_answers_and_no_blocking_keeps_value(self) -> None:
        fake = self.fake(
            drafts=(
                self.draft(human="ok"),
                self.draft(claude="ok"),
                self.draft(FAILING_SCORES, claude="bad", passed=False),
            )
        )
        self.assertEqual(check_floor(fake), 0.7)
        self.assertEqual(
            check_floor_line(fake),
            "정답 있고 자체 검사를 통과한 초안 2(사람 칸 1) 가운데 정답 bad 가 0 이라"
            " `check_min_probability` 는 0.7 그대로입니다(근거가 있어 그대로)",
        )

    def test_check_floor_uses_comparison_scores(self) -> None:
        # 트래커 6B HC1 질문 1 A 의 예 — 광고 질문은 1 − P(예) 로 비교합니다
        fake = self.fake(drafts=(self.draft((0.94, 0.06, 0.86), claude="bad"),))
        self.assertEqual(check_floor(fake), 0.91)
        self.assertEqual(
            check_floor_line(fake),
            "정답 bad 인데 자체 검사를 통과한 초안 1 의 가장 낮은 비교 점수 중 가장 높은 값 0.86"
            " + 0.05 으로 `check_min_probability` 를 0.91 로 올렸습니다 — 같은 초안 답을 다시"
            " 셈한 값이고, 진짜 jev 를 이 통과선으로 돌린 숫자가 아닙니다",
        )

    def test_check_floor_blocks_every_bad_passing_draft(self) -> None:
        fake = self.fake(
            drafts=(
                self.draft((0.71, 0.1, 0.9), claude="bad"),
                self.draft((0.80, 0.1, 0.9), claude="bad"),
            )
        )
        self.assertEqual(check_floor(fake), 0.85)

    def test_check_floor_never_lowers_the_recorded_value(self) -> None:
        # "결과의 값보다 내리지 않습니다" — 가장 낮은 비교 점수 0.5 + MARGIN 0.55 는 0.7 아래
        fake = self.fake(drafts=(self.draft((0.5, 0.1, 0.9), claude="bad", passed=True),))
        self.assertEqual(check_floor(fake), 0.7)

    def test_human_cell_beats_claude_grade(self) -> None:
        kept = self.fake(drafts=(self.draft(human="ok", claude="bad"),))
        self.assertEqual(check_floor(kept), 0.7)
        raised = self.fake(drafts=(self.draft((0.71, 0.1, 0.9), human="bad", claude="ok"),))
        self.assertEqual(check_floor(raised), 0.76)
        self.assertTrue(check_floor_line(raised).startswith("정답 bad 인데 자체 검사를 통과한 초안 1 "))

    def test_check_floor_over_one_is_drift(self) -> None:
        fake = self.fake(drafts=(self.draft((0.97, 0.01, 0.98), claude="bad"),))
        self.assertIsNone(check_floor(fake))
        self.assertEqual(self.drift(fake), ["check_min_probability"])

    def test_check_floor_exactly_one_is_kept(self) -> None:
        # "1 을 넘으면" — 가장 낮은 비교 점수 0.95 + MARGIN 은 정확히 1.0 이라 막을 수 있습니다
        fake = self.fake(drafts=(self.draft((0.95, 0.05, 0.95), claude="bad"),))
        self.assertEqual(check_floor(fake), 1.0)

    def test_todo_line_counts_both_windows(self) -> None:
        # 6E 줄은 모든 창의 셈 — 운영 창 초안 하나와 넓힌 창 초안 하나의 분모는 2
        fake = self.fake(drafts=(self.draft(),))
        widened = copy.deepcopy(fake["videos"][0])
        widened["window"] = "widened"
        fake["videos"].append(widened)
        both, operation = task_counts(fake, None), task_counts(fake, "operation")
        self.assertEqual((both["tasks"], both["drafts"]), (2, 2))
        self.assertEqual((operation["tasks"], operation["drafts"]), (1, 1))
        line = todo_line(fake)
        for phrase in (
            f"ⓐ 고민 한 줄이 연애 고민 {both['love']}/{both['tasks']} ·",
            f"ⓑ 연애사주 경험이 고민과 이어짐 {both['saju']}/{both['tasks']} ·",
            f"글자 조각이 있는 초안 {both['framed']}/{both['drafts']} ·",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, line)

    def test_draft_answer_samples(self) -> None:
        samples = (
            ({"human": "ok", "claude_grade": "bad"}, "ok"),
            ({"human": "bad", "claude_grade": "ok"}, "bad"),
            ({"human": "", "claude_grade": "bad"}, "bad"),
        )
        for draft, expected in samples:
            with self.subTest(draft=draft):
                self.assertEqual(draft_answer(draft), expected)

    def test_lowered_recorded_floors_are_caught(self) -> None:
        on_topic = load_result()["fingerprint"]["classifier"]["on_topic_reasons"][0]
        fake = self.fake(
            classification={
                "verdict": "hold",
                "error": False,
                "noul": 0.78,
                "choice": on_topic,
                "probability": 0.9,
                "confidence": 0.9,
            },
            drafts=(self.draft((0.65, 0.1, 0.9), claude="bad", passed=False),),
        )
        self.assertEqual(stored_verdict_mismatches(fake), [])
        lowered = copy.deepcopy(fake)
        lowered["fingerprint"]["classifier"]["noul_yes_min"] = 0.75
        self.assertEqual(stored_verdict_mismatches(lowered), ["videos[0] hold -> yes"])
        # 결과와 설정을 함께 내리면 맞대기만으로는 같습니다 — 저장된 판정이 그 구멍을 막습니다
        alike = _with_cell(self.current, "classifier.noul_yes_min", 0.75)
        self.assertEqual(self.drift(lowered, alike), [])
        threshold = copy.deepcopy(fake)
        threshold["fingerprint"]["check_min_probability"] = 0.6
        self.assertEqual(
            stored_verdict_mismatches(threshold),
            ["videos[0].drafts[0] self_check_pass False -> True"],
        )

    def test_lowered_floors_flip_an_example_row(self) -> None:
        # 예시 행 다리 — 영상 판별 · 초안은 그대로, 심은 행은 마지막 no 자리(21)에서 hold -> yes
        on_topic = load_result()["fingerprint"]["classifier"]["on_topic_reasons"][0]
        held = {"verdict": "hold", "noul": 0.78, "choice": on_topic, "confidence": 0.9}
        fake = self.fake(ko=(held,))
        self.assertEqual(stored_verdict_mismatches(fake), [])
        lowered = copy.deepcopy(fake)
        lowered["fingerprint"]["classifier"]["noul_yes_min"] = 0.75
        self.assertEqual(stored_verdict_mismatches(lowered), ["accuracy.ko[21] hold -> yes"])

    @staticmethod
    def _flip_tasks(draft: dict) -> None:
        if isinstance(draft.get("task_quality"), Mapping):
            draft["task_quality"] = {
                key: not value for key, value in draft["task_quality"].items()
            }

    @staticmethod
    def _text_leaves(value: object, key: str = "") -> list[tuple[str, str]]:
        if isinstance(value, Mapping):
            return [
                leaf
                for name, item in value.items()
                for leaf in RecountTest._text_leaves(item, name)
            ]
        if isinstance(value, list):
            return [leaf for item in value for leaf in RecountTest._text_leaves(item, key)]
        return [(key, value)] if isinstance(value, str) else []

    def test_video_cells_do_not_move_floor_recount(self) -> None:
        # 약속 "예시 22개의 숫자와 다른 표본이며 기준값을 움직이지 않습니다" — 영상 칸은 하한 셋을 옮기지 않습니다
        result = load_result()
        tampered = copy.deepcopy(result)
        tampered["videos"] = mark_text(tampered["videos"], "videos")
        tampered["windows"] = mark_text(tampered["windows"], "windows")
        for video in tampered["videos"]:
            if video["classification"] is not None:
                video["classification"].update(noul=0.5, confidence=0.99)
            for draft in video["drafts"]:
                self._flip_tasks(draft)
        leaves = self._text_leaves(tampered["videos"]) + self._text_leaves(tampered["windows"])
        self.assertTrue(leaves)
        for key, text in leaves:
            with self.subTest(key=key, text=text):
                self.assertTrue(key in DATE_KEYS or text.startswith("MRK"), text)
        ids = [video["video_id"] for video in tampered["videos"]]
        self.assertEqual(ids, [f"MRK{index:08d}" for index in range(len(ids))])

        def floors(data: dict) -> dict[str, object]:
            return {
                key: value for key, value in recount(data).items() if key.startswith("classifier.")
            }

        self.assertEqual(floors(tampered), floors(result))

    def test_task_cells_do_not_move_check_floor(self) -> None:
        # 약속 "과제 품질 · 인기 댓글 숫자는 기록입니다 — 통과선은 이 숫자로 움직이지 않습니다"
        raised = self.fake(drafts=(self.draft((0.71, 0.1, 0.9), claude="bad"),))
        swap = {"top_comments": "title_description", "title_description": "top_comments"}
        cases = (("committed", load_result(), 0.7), ("raised", raised, 0.76))
        for name, result, expected in cases:
            with self.subTest(result=name):
                self.assertEqual(check_floor(result), expected)
                changed = copy.deepcopy(result)
                for video in changed["videos"]:
                    video["material"] = swap.get(video["material"], video["material"])
                    video.update(top_comment_count=0, comment_items=7)
                    for draft in video["drafts"]:
                        if draft["parsed"] is not True:
                            continue
                        self._flip_tasks(draft)
                        draft.update(task_error="응답 모양", frame_overlap=99)
                self.assertNotEqual(task_lines(changed), task_lines(result))
                self.assertEqual(check_floor(changed), expected)


FIVE_SCORE_NAMES = (*SCORE_NAMES, "concern_is_love_worry", "saju_story_fits")


class LowestScoreTest(unittest.TestCase):
    """`lowest_score` · `self_check_passes` — 초안마다 그 초안 `scores` 의 질문 이름으로 셉니다.

    결과의 질문 이름은 실행 때의 `CHECK_QUESTIONS` 라 판마다 다릅니다(6D 셋 · 6E 뒤 다섯). 모르는
    이름 · 빈 점수는 거절합니다 — 헌법 12조 닮은 꼴 표본(트래커 Phase 6E 'The plan decides' 6D
    ship-check R2).
    """

    @staticmethod
    def five(**values: float) -> dict[str, float]:
        """다섯 이름 점수 — 비교 점수가 모두 1.0(광고는 P(예) 0.0)인 것에서 values 만 바꿉니다."""
        scores = {name: 1.0 for name in FIVE_SCORE_NAMES}
        scores["reads_like_ad"] = 0.0
        scores.update(values)
        return scores

    def test_three_question_drafts_recount(self) -> None:
        result = load_result()
        drafts = [draft for draft in _parsed_drafts(result) if draft["scores"] is not None]
        self.assertTrue(drafts)
        for draft in drafts:
            scores = draft["scores"]
            with self.subTest(scores=scores):
                self.assertEqual(set(scores), set(SCORE_NAMES))
                expected = min(
                    scores["mentions_scene"],
                    1.0 - scores["reads_like_ad"],
                    scores["follows_concern"],
                )
                self.assertEqual(lowest_score(scores), expected)
        # 두 자리 모두 질문 셋의 초안을 읽습니다 — 고치기 전에는 KeyError: 'concern_is_love_worry'
        self.assertEqual(check_floor(result), 0.7)
        self.assertEqual(stored_verdict_mismatches(result), [])

    def test_five_question_fake_result_recounts(self) -> None:
        draft = RecountTest.draft(claude="bad")
        draft["scores"] = self.five(
            mentions_scene=0.9,
            reads_like_ad=0.1,
            follows_concern=0.9,
            concern_is_love_worry=0.85,
            saju_story_fits=0.72,
        )
        fake = RecountTest.fake(drafts=(draft,))
        self.assertEqual(lowest_score(draft["scores"]), 0.72)
        self.assertEqual(check_floor(fake), round(0.72 + live_check.MARGIN, 6))
        self.assertEqual(check_floor(fake), 0.77)
        self.assertEqual(stored_verdict_mismatches(fake), [])
        flipped = copy.deepcopy(fake)
        flipped["videos"][0]["drafts"][0]["self_check_pass"] = False
        self.assertEqual(
            stored_verdict_mismatches(flipped),
            ["videos[0].drafts[0] self_check_pass False -> True"],
        )

    def test_self_check_passes_matches_writer(self) -> None:
        self.assertEqual(set(FIVE_SCORE_NAMES), set(CHECK_QUESTIONS))
        for i in range(1, 100):
            floor = float(f"0.{i:02d}")
            below = round(floor - 0.01, 2)
            for name in FIVE_SCORE_NAMES:
                inverted = name in INVERTED_QUESTIONS
                at = round(1 - floor, 2) if inverted else floor  # 1 − 0.9 경계 갈래
                under = round(1 - below, 2) if inverted else below
                for label, value, passing in (("at", at, True), ("below", under, False)):
                    scores = self.five(**{name: value})
                    with self.subTest(floor=floor, name=name, case=label):
                        writer_pass = self_check_failure(scores, floor) is None
                        self.assertEqual(self_check_passes(scores, floor), writer_pass)
                        self.assertEqual(writer_pass, passing)

    def test_unknown_question_name_is_refused(self) -> None:
        three = dict(zip(SCORE_NAMES, PASSING_SCORES))
        self.assertEqual(lowest_score(three), 0.9)
        self.assertEqual(lowest_score(self.five(saju_story_fits=0.72)), 0.72)
        near_misses = (
            "Reads_like_ad",
            " reads_like_ad",
            "reads-like-ad",
            "ｒeads_like_ad",
            "reads_like_promo",
        )
        for odd in near_misses:
            scores = {
                (odd if key == "reads_like_ad" else key): value for key, value in three.items()
            }
            with self.subTest(name=odd):
                with self.assertRaises(ValueError):
                    lowest_score(scores)
                with self.assertRaises(ValueError):
                    self_check_passes(scores, 0.7)

    def test_empty_scores_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            lowest_score({})
        with self.assertRaises(ValueError):
            self_check_passes({}, 0.7)


class DraftBoundaryTest(unittest.TestCase):
    """심은 초안 · 행의 경계 — 사람 칸이 Claude 채점보다 먼저, 기준값과 같은 `noul` 은 사이가 아님."""

    @staticmethod
    def _draft(human: str, claude: str | None, self_check: bool) -> dict:
        return {
            "parsed": True,
            "human": human,
            "claude_grade": claude,
            "grade_error": None if claude is not None else "응답 모양",
            "self_check_pass": self_check,
        }

    @staticmethod
    def _video(noul: float, outcome: str, drafts: list[dict]) -> dict:
        return {
            "window": "operation",
            "result": outcome,
            "classification": {"noul": noul},
            "drafts": drafts,
        }

    def setUp(self) -> None:
        self.result = copy.deepcopy(load_result())
        classifier = self.result["fingerprint"]["classifier"]
        self.lo, self.hi = classifier["noul_no_max"], classifier["noul_yes_min"]
        self.result["videos"] = [
            self._video(
                self.lo,
                "comment",
                [self._draft("ok", "bad", False), self._draft("bad", "ok", True)],
            ),
            self._video(
                self.hi,
                "skip",
                [self._draft("", "bad", True), self._draft("Bad", None, False)],
            ),
        ]
        for language in LANGUAGES:
            rows = self.result["accuracy"][language]
            rows += [dict(rows[0], noul=self.lo), dict(rows[0], noul=self.hi)]

    def test_human_answer_beats_claude_grade(self) -> None:
        self.assertEqual(
            draft_counts(self.result, "operation"),
            {
                "written": 2,
                "skip": 1,
                "drafts": 4,
                "human": 2,
                "claude": 3,
                "answered": 3,
                "grade_errors": 1,
                "differ": 2,
                "bad_passed": 2,
                "ok_failed": 1,
            },
        )

    def test_threshold_equal_noul_is_not_between(self) -> None:
        before = gap_lines(load_result())
        after = gap_lines(self.result)
        for index, language in enumerate(LANGUAGES):
            with self.subTest(language=language):
                head = before[index].split(" · 가장 가까운 예시")[0]
                self.assertEqual(
                    after[index], f"{head} · 가장 가까운 예시 {self.lo:.2f} · {self.hi:.2f}"
                )
        self.assertEqual(
            after[len(LANGUAGES)],
            f"기준값 사이 영상 {WINDOW_LABELS['operation']}: 0/{len(self.result['videos'])}",
        )


class TopicBoundaryTest(unittest.TestCase):
    """영상 판별 정답 · 하한 내림 기록의 경계 — 사람 칸 먼저, 내림은 확신 있는 같은 주제 보류만."""

    def test_topic_answer_samples(self) -> None:
        samples = (
            ({"topic_human": "연애", "topic_grade": "아님"}, "연애"),
            ({"topic_human": "아님", "topic_grade": "연애"}, "아님"),
            ({"topic_human": "", "topic_grade": "연애"}, "연애"),
        )
        for video, expected in samples:
            with self.subTest(video=video):
                self.assertEqual(topic_answer(video), expected)

    def test_lowering_counts_holds_the_tracker_floors_turn_yes(self) -> None:
        result = copy.deepcopy(load_result())
        classifier = result["fingerprint"]["classifier"]
        on, off = classifier["on_topic_reasons"][0], classifier["off_topic_reasons"][0]

        def video(verdict: str, noul: float | None, choice: str | None, confidence: float | None,
                  grade: str, error: bool = False) -> dict:
            return {
                "window": "operation",
                "classification": {
                    "verdict": verdict,
                    "error": error,
                    "noul": noul,
                    "choice": choice,
                    "probability": None if noul is None else 0.9,
                    "confidence": confidence,
                },
                "topic_grade": grade,
                "topic_human": "",
            }

        result["videos"] = [
            video("hold", 0.76, on, 0.9, "연애"),
            video("hold", 0.65, on, 0.9, "아님"),
            video("hold", 0.78, on, 0.3, "연애"),
            video("hold", 0.7, off, 0.9, "연애"),
            video("yes", 0.95, on, 0.9, "연애"),
            video("hold", None, None, None, "연애", error=True),
        ]
        self.assertEqual(
            lowering_lines(result)[0],
            "보류 영상 하한 내림 운영 창: `noul_yes_min` 0.75 이면 새 일치 — 정답 연애 1 · 정답 아님 0"
            " · 정답 없음 0 / `noul_yes_min` 0.6 이면 새 일치 — 정답 연애 1 · 정답 아님 1 · 정답 없음 0",
        )


class AccuracyRecordTest(ContractCase):
    """'주제 판별' 절의 정확도 기록 — 결과 파일에서 다시 센 숫자가 계약에 있고 기준값은 그대로."""

    def setUp(self) -> None:
        self.result = load_result()

    def test_accuracy_record_is_in_contract(self) -> None:
        result = self.result
        classifier = result["fingerprint"]["classifier"]
        phrases = [
            f"`docs/live-check/result.json`(실행 {result['run_at']}, 판정 줄 `{result['verdict']}`)",
            f"지금 기준값은 `noul_yes_min` {classifier['noul_yes_min']}"
            f" · `noul_no_max` {classifier['noul_no_max']}"
            f" · `choice_min_confidence` {classifier['choice_min_confidence']} 입니다",
            *accuracy_lines(result),
            recount_line(result),
            *gap_lines(result),
            *classification_lines(result),
            *topic_grade_lines(result),
            *lowering_lines(result),
        ]
        for phrase in phrases:
            self.assert_in_contract(phrase)

    def test_topic_human_value_moves_the_record_but_other_text_does_not(self) -> None:
        # 약속 "사람 칸의 다른 값 … 이 모듈을 빨강으로 만들지 않습니다" — topic_human 의 연애 · 아님
        # 은 기록 줄을 바꾸고(그래서 test_accuracy_record_is_in_contract 가 빨강), 다른 글은 그대로
        result = self.result
        index = next(
            i
            for i, video in enumerate(result["videos"])
            if video["classification"] is not None and video["topic_human"] not in TOPIC_ANSWERS
        )
        for value, moves in (("아님", True), ("연애", True), ("엉뚱한 글", False)):
            with self.subTest(topic_human=value):
                changed = copy.deepcopy(result)
                changed["videos"][index]["topic_human"] = value
                if moves:
                    self.assertNotEqual(topic_grade_lines(changed), topic_grade_lines(result))
                else:
                    self.assertEqual(topic_grade_lines(changed), topic_grade_lines(result))

    def test_accuracy_tally_is_recount_of_rows(self) -> None:
        keys = ("correct", "false_yes", "false_no", "hold", "error")
        for language in LANGUAGES:
            with self.subTest(language=language):
                counts = dict.fromkeys(keys, 0)
                for row in self.result["accuracy"][language]:
                    if row["error"] is True:
                        counts["error"] += 1
                    elif row["verdict"] == "hold":
                        counts["hold"] += 1
                    elif row["verdict"] == row["label"]:
                        counts["correct"] += 1
                    elif row["verdict"] == "yes":
                        counts["false_yes"] += 1
                    else:
                        counts["false_no"] += 1
                tally = self.result["accuracy_tally"][language]
                self.assertEqual(counts, {key: tally[key] for key in keys})

    def test_tally_slots_follow_record_lines(self) -> None:
        result = copy.deepcopy(self.result)
        result["accuracy_tally"]["ko"] = {
            "correct": 15, "false_yes": 1, "false_no": 2, "hold": 3, "error": 1
        }
        result["accuracy_tally"]["en"] = {
            "correct": 11, "false_yes": 6, "false_no": 2, "hold": 1, "error": 2
        }
        n = result["example_count"]
        expected = {
            "ko": f"ko: 지금 기준값 맞음 15/{n} · 잘못된 일치 1 · 잘못된 불일치 2 · 보류 3 · 오류 1"
            " · 올리기만 범위 최다 맞음",
            "en": f"en: 지금 기준값 맞음 11/{n} · 잘못된 일치 6 · 잘못된 불일치 2 · 보류 1 · 오류 2"
            " · 올리기만 범위 최다 맞음",
        }
        lines = accuracy_lines(result)
        self.assertEqual(len(lines), len(LANGUAGES))
        for language, line in zip(LANGUAGES, lines):
            with self.subTest(language=language):
                self.assertTrue(line.startswith(expected[language]), line)

    def test_question_language_follows_record(self) -> None:
        passed = {language: passes(reach(self.result, language)) for language in LANGUAGES}
        self.assertTrue(any(passed.values()), "drift — 인터뷰")
        self.assertEqual(QUESTION_LANGUAGE, "ko" if passed["ko"] else "en")
        self.assertEqual(QUESTION_LANGUAGE, "ko")
        self.assert_in_contract(language_phrase(self.result))

    def test_config_floors_are_the_recount(self) -> None:
        recounted = recount(self.result)
        config = load_config(REPO_CONFIG).classifier
        recorded = self.result["fingerprint"]["classifier"]
        for name in FLOORS:
            with self.subTest(floor=name):
                self.assertEqual(
                    getattr(config, name),
                    recounted[f"classifier.{name}"],
                    "6B 규칙으로 다시 셈한 기준값과 config.yaml 이 다릅니다",
                )
        if all(recounted[f"classifier.{name}"] == recorded[name] for name in FLOORS):
            self.assert_in_contract("기준값 셋은 그대로입니다")


class WriterRecordTest(ContractCase):
    """'댓글 작성' 절의 잰 값 — 모델 이름 · 초안 수가 계약에 있고 통과선 · 반복 글자 수는 그대로."""

    def setUp(self) -> None:
        self.result = load_result()

    def test_writer_model_is_the_accepted_configured_name(self) -> None:
        writer = load_config(REPO_CONFIG).comment.writer_model
        self.assertEqual(writer, self.result["writer_model"])
        self.assert_in_contract(model_line(self.result))
        self.assert_in_contract(f"`comment.writer_model` 은 `{writer}` 그대로입니다")

    def test_draft_record_is_in_contract(self) -> None:
        for phrase in (*draft_lines(self.result), *task_lines(self.result)):
            self.assert_in_contract(phrase)

    def test_check_floor_is_the_recount(self) -> None:
        floor = check_floor(self.result)
        self.assertIsNotNone(floor, "통과선을 1 이하로 올려 막을 수 없습니다 — drift")
        self.assertEqual(
            load_config(REPO_CONFIG).comment.check_min_probability,
            floor,
            "6B 규칙으로 다시 셈한 통과선과 config.yaml 이 다릅니다",
        )
        self.assert_in_contract(check_floor_line(self.result))

    def test_todo_line_counts_come_from_the_result(self) -> None:
        line = todo_line(self.result)
        self.assertTrue(line.startswith("6E: 할 일 있음 — "), line)
        found = re.fullmatch(
            r"6E: 할 일 있음 — ⓐ 고민 한 줄이 연애 고민 ([0-9]+)/([0-9]+)"
            r" · ⓑ 연애사주 경험이 고민과 이어짐 ([0-9]+)/([0-9]+)"
            rf" · ⓒ 다른 영상 초안과 겹치는 {live_check.FRAME_CHARS}글자 조각이 있는 초안"
            r" ([0-9]+)/([0-9]+) · 건너뜀 SKIP ([0-9]+)/([0-9]+)"
            r" · 작성기 답을 JSON 으로 못 읽은 초안 ([0-9]+)/([0-9]+)",
            line,
        )
        self.assertIsNotNone(found, line)
        love, tasks, saju, tasks_b, framed, drafts, skip, written, unparsed, drafts_b = (
            found.groups()
        )
        self.assertEqual((tasks_b, drafts_b), (tasks, drafts))
        summary = live_check.render_summary(self.result).splitlines()
        task_line = next(text for text in summary if text.startswith("- 과제 품질:"))
        for phrase in (
            f"고민이 연애 고민 {love}/{tasks}",
            f"연애사주 경험이 고민과 이어짐 {saju}/{tasks}",
            f"조각이 있는 초안 {framed}/{drafts}",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, task_line)
        self.assertIn(f"SKIP {skip}/{written}", live_check.verdict_line(self.result))
        attempts = [draft for video in self.result["videos"] for draft in video["drafts"]]
        self.assertEqual(
            int(unparsed), sum(1 for draft in attempts if draft["parsed"] is not True)
        )
        tampered = copy.deepcopy(self.result)
        for video in tampered["videos"]:
            for draft in video["drafts"]:
                if isinstance(draft.get("task_quality"), Mapping):
                    draft["task_quality"]["concern_is_love_worry"] = True
        self.assertIn(f"ⓐ 고민 한 줄이 연애 고민 {tasks}/{tasks} ·", todo_line(tampered))

    def test_repeat_min_chars_stays_unmeasured(self) -> None:
        self.assert_in_contract(
            f"`REPEAT_MIN_CHARS`({REPEAT_MIN_CHARS}) 는 그대로입니다 — 표본 부족: 최근 내 댓글"
            f" {RECENT_WINDOW}개끼리 비교하는 값이라 초안 약 {live_check.TARGET_DRAFTS}개짜리"
            " 한 바퀴로는 잴 수 없습니다"
        )


if __name__ == "__main__":
    unittest.main()
