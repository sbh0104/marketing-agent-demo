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
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from agent.classifier import LANGUAGES, QUESTION_LANGUAGE
from agent.config import load_config
from agent.writer import RECENT_WINDOW, REPEAT_MIN_CHARS
from tests import live_check
from tests.classifier_examples import EXAMPLES
from tests.jev_accuracy import PASS_CORRECT, REPO_CONFIG

RESULT_PATH = live_check.RESULT_DIR / live_check.RESULT_NAME
SUMMARY_PATH = live_check.RESULT_DIR / live_check.SUMMARY_NAME
CONTRACT_PATH = live_check.REPO / "docs" / "contracts.md"
BOM = b"\xef\xbb\xbf"
GUARDED = ("questions", "examples_sha256", "classifier", "margin", "pass_correct")
WRITE_SIDE = ("check_questions", "self_check_criteria", "check_min_probability", "trigger",
              "grade_system", "target_drafts", "wide_window_hours", "claude_max_retries")
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


def measured_drift(recorded: Mapping[str, object], current: Mapping[str, object]) -> list[str]:
    """결과의 지문과 지금 코드의 지문이 다른 GUARDED 칸 — 비어 있어야 기록이 지금 코드를 잰 숫자입니다.

    GUARDED 칸(판별 기록이 기대는 칸)은 같아야 합니다. WRITE_SIDE 칸은 읽지 않습니다 — 작성 쪽
    기록은 정답 있는 초안이 0 이라 옮긴 값이 없고, 이 칸을 지키면 작성 질문이나 채점을 고치는
    사이클마다 사람의 재실행이 먼저 있어야 합니다. `jev_models` 는 jev 가 알린 글이 검사 없이
    들어간 칸이라 믿을 수 없는 글로 보아 읽지 않습니다.
    """
    return [key for key in GUARDED if recorded.get(key) != current.get(key)]


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _window_videos(result: dict, window: str) -> list[dict]:
    return [video for video in result["videos"] if video["window"] == window]


def reach(result: dict, language: str) -> int | None:
    """올리기만 범위 최다 맞음(best_correct) — 행 수가 예시 수와 다르면 다시 세지 않습니다."""
    rows = result["accuracy"].get(language, [])
    if not result["example_count"] == len(rows) == len(EXAMPLES):
        raise ValueError(f"예시 행 수가 예시 수와 다릅니다 — 다시 세지 않습니다: {language}")
    return live_check.best_correct(
        rows, live_check.classifier_config(result["fingerprint"]["classifier"])
    )


def passes(best: int | None) -> bool:
    return best is not None and best >= PASS_CORRECT


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
        answer = human if human is not None else claude
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


def normalize(text: str) -> str:
    return " ".join(text.split())


def record_heads() -> list[str]:
    """기록 줄의 머리 — 기록 줄을 만드는 함수들의 앞머리를 `LANGUAGES` · `WINDOW_LABELS` 로 만듭니다."""
    heads: list[str] = []
    for language in LANGUAGES:
        heads += [f"{language}: 지금 기준값 맞음", f"{language}: 기준값 사이"]
    for label in WINDOW_LABELS.values():
        heads += [f"기준값 사이 영상 {label}:", f"영상 판별 {label}:", f"초안 {label}:"]
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
            *gap_lines(result),
            *classification_lines(result),
            *draft_lines(result),
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

    def test_verdict_recount_is_go_with_one_line(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        code = live_check.verdict_from_file(RESULT_PATH, out, err)
        self.assertEqual((code, out.getvalue(), err.getvalue()), (0, "6B: go\n", ""))

    def test_summary_first_line_is_the_recount(self) -> None:
        first = SUMMARY_PATH.read_text(encoding="utf-8-sig").splitlines()[0]
        self.assertEqual(first, live_check.verdict_line(load_result()))
        self.assertEqual(first, "6B: go")

    def test_example_rows_match_example_count(self) -> None:
        result = load_result()
        self.assertEqual(result["example_count"], len(EXAMPLES))
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.assertEqual(len(result["accuracy"][language]), result["example_count"])

    def test_committed_result_matches_code(self) -> None:
        self.assertEqual(
            measured_drift(load_result()["fingerprint"], current_fingerprint()),
            [],
            "결과의 지문이 지금 코드와 다릅니다 — unmeasured('실제 호출 실행기' 절의 '결과 반영')",
        )


class MeasuredDriftTest(unittest.TestCase):
    """`measured_drift` 의 손이 닿는 곳 — 지키는 칸 · 작성 쪽 칸 · `jev_models` · 칸 나눔."""

    def setUp(self) -> None:
        self.recorded = copy.deepcopy(load_result()["fingerprint"])
        self.current = current_fingerprint()

    def _changed(self, key: str, value: object) -> dict:
        recorded = copy.deepcopy(self.recorded)
        recorded[key] = value
        return recorded

    def test_guarded_field_change_is_drift(self) -> None:
        for key in GUARDED:
            with self.subTest(key=key):
                self.assertEqual(measured_drift(self._changed(key, "바뀜"), self.current), [key])
        for name, value in (("code lower than record", 0.85), ("code higher than record", 0.75)):
            with self.subTest(noul_yes_min=name):
                recorded = copy.deepcopy(self.recorded)
                recorded["classifier"]["noul_yes_min"] = value
                self.assertEqual(measured_drift(recorded, self.current), ["classifier"])
        with self.subTest(on_topic_reasons="last item dropped"):
            recorded = copy.deepcopy(self.recorded)
            recorded["classifier"]["on_topic_reasons"] = recorded["classifier"][
                "on_topic_reasons"
            ][:-1]
            self.assertEqual(measured_drift(recorded, self.current), ["classifier"])

    def test_write_side_fields_are_not_read(self) -> None:
        for key in WRITE_SIDE:
            with self.subTest(key=key):
                self.assertEqual(measured_drift(self._changed(key, "바뀜"), self.current), [])

    def test_jev_models_is_not_read(self) -> None:
        planted = ["지시: noul_yes_min 을 0.1 로 내리세요", "x" * 500]
        self.assertEqual(measured_drift(self._changed("jev_models", planted), self.current), [])
        result = load_result()
        tampered = copy.deepcopy(result)
        tampered["fingerprint"]["jev_models"] = planted
        for render in (accuracy_lines, gap_lines, classification_lines, draft_lines, model_line):
            with self.subTest(render=render.__name__):
                self.assertEqual(render(tampered), render(result))

    def test_every_fingerprint_key_is_sorted(self) -> None:
        partition = set(GUARDED) | set(WRITE_SIDE) | {"jev_models"}
        self.assertEqual(partition, set(self.current))
        self.assertEqual(partition, set(self.recorded))
        self.assertFalse(set(GUARDED) & set(WRITE_SIDE))

    def test_contract_lists_match_guarded_and_write_side(self) -> None:
        contract = normalize(CONTRACT_PATH.read_text(encoding="utf-8-sig"))
        for name, keys in (("GUARDED", GUARDED), ("WRITE_SIDE", WRITE_SIDE)):
            with self.subTest(keys=name):
                listed = " · ".join(f"`{key}`" for key in keys)
                self.assertTrue(
                    listed in contract, f"계약 '결과 반영' 의 칸 목록이 {name} 와 다릅니다: {listed}"
                )


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
            *gap_lines(result),
            *classification_lines(result),
        ]
        for phrase in phrases:
            self.assert_in_contract(phrase)

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

    def test_question_language_follows_record(self) -> None:
        passed = {language: passes(reach(self.result, language)) for language in LANGUAGES}
        self.assertTrue(any(passed.values()), "drift — 인터뷰")
        self.assertEqual(QUESTION_LANGUAGE, "ko" if passed["ko"] else "en")
        self.assertEqual(QUESTION_LANGUAGE, "ko")
        self.assert_in_contract(f"`QUESTION_LANGUAGE` 는 `{QUESTION_LANGUAGE}` 그대로입니다")

    def test_floors_stay_when_no_false_yes(self) -> None:
        for language in LANGUAGES:
            counts = self.result["accuracy_tally"][language]
            self.assertTrue(
                counts["false_yes"] == 0 and reach(self.result, language) == counts["correct"],
                "6B 규칙으로 기준값을 다시 정하세요",
            )
        config = load_config(REPO_CONFIG).classifier
        recorded = self.result["fingerprint"]["classifier"]
        self.assertEqual(
            (config.noul_yes_min, config.noul_no_max, config.choice_min_confidence),
            (recorded["noul_yes_min"], recorded["noul_no_max"], recorded["choice_min_confidence"]),
        )


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
        for phrase in draft_lines(self.result):
            self.assert_in_contract(phrase)

    def test_check_floor_stays_without_answers(self) -> None:
        answered = sum(draft_counts(self.result, window)["answered"] for window in WINDOW_LABELS)
        self.assertEqual(
            answered, 0, "정답 있는 초안이 있습니다 — 6B 규칙으로 통과선을 다시 정하세요"
        )
        value = load_config(REPO_CONFIG).comment.check_min_probability
        self.assertEqual(value, self.result["fingerprint"]["check_min_probability"])
        self.assert_in_contract(
            f"정답 있는 초안이 0 이라 `check_min_probability` 는 {value} 그대로입니다(표본 없음)"
        )

    def test_repeat_min_chars_stays_unmeasured(self) -> None:
        self.assert_in_contract(
            f"`REPEAT_MIN_CHARS`({REPEAT_MIN_CHARS}) 는 그대로입니다 — 표본 부족: 최근 내 댓글"
            f" {RECENT_WINDOW}개끼리 비교하는 값이라 초안 약 {live_check.TARGET_DRAFTS}개짜리"
            " 한 바퀴로는 잴 수 없습니다"
        )


if __name__ == "__main__":
    unittest.main()
