"""과제 문장 대조표 — 계약 '댓글 작성' 절의 표가 과제 ④ 여덟 문장과 평가 '댓글 품질' 세 문장을 하나씩
막는 자리 · 짝 테스트와 함께 적는지 봅니다(트래커 Phase 6E 인터뷰 질문 1 A).

표의 이름은 지금 코드에서 되묻습니다 — 규칙 번호는 `SYSTEM_PROMPT` 의 줄, jev 질문은 `CHECK_QUESTIONS`,
코드 검사는 `code_failures` 가 부르는 이름, 스스로 건너뜀은 작성기의 두 이유, 짝 테스트는 그 파일의
함수입니다. 뒤 페이즈가 검사를 빼거나 이름을 바꾸면 그 사이클 안에서 빨강입니다. 표는 막는 자리가
있는지만 지키고, 그 검사가 잘 판단하는지는 실제 실행이 잽니다.
"""
from __future__ import annotations

import ast
import copy
import re
import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path

from agent.writer import CHECK_QUESTIONS, NO_CONCERN, NO_SCENE, SYSTEM_PROMPT, code_failures

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs" / "contracts.md"
SECTION = "## 댓글 작성 — `writer.py` (Phase 5)"
HEADER = (
    "번호",
    "과제 문장",
    "프롬프트 규칙",
    "jev 질문",
    "코드 검사",
    "스스로 건너뜀",
    "짝 테스트",
    "막지 않음",
)
NONE = "—"
# 과제 안내 4쪽 ④ 여덟 문장과 7쪽 평가표 '댓글 품질' 세 문장 — 트래커 Phase 6E 인터뷰 질문 1 A 의 인용
TASK_SENTENCES = (
    "자막(없으면 제목·설명)과 인기 댓글을 읽고",
    "영상이 다루는 연애 고민을 먼저 한 줄로 정리",
    "그 고민과 연결해 '비슷한 고민이 있었을 때 연애사주를 봤던 경험'을 담은 댓글 … 자연스럽게"
    " 이어지는 형태",
    "40 ~ 120자",
    "영상 속 구체적인 장면이나 말을 하나 이상 언급",
    "링크 금지",
    "이전 댓글과 같은 문장 반복 금지",
    "영상 내용과 댓글이 잘 맞는지 AI가 다시 검사하는 단계를 두면 가점",
    "영상 속 고민을 정확히 짚고",
    "연애사주 경험과 자연스럽게 연결되는가",
    "영상마다 다르게 쓰이는가",
)
PLACE_COLUMNS = ("프롬프트 규칙", "jev 질문", "코드 검사", "스스로 건너뜀")
RULES_RE = re.compile(r"규칙 \d+( · 규칙 \d+)*")


def section_text(text: str) -> str:
    """계약에서 '댓글 작성' 절 — 제목 줄부터 다음 `## ` 제목 앞까지."""
    start = text.index(SECTION)
    end = text.find("\n## ", start + len(SECTION))
    return text[start:] if end < 0 else text[start:end]


def _cells(line: str) -> list[str]:
    """표 한 줄의 칸 — 바깥 `|` 사이의 글, 앞뒤 공백을 뗍니다."""
    inner = line.strip()
    inner = inner[1:] if inner.startswith("|") else inner
    inner = inner[:-1] if inner.endswith("|") else inner
    return [cell.strip() for cell in inner.split("|")]


def table_rows(section: str) -> list[dict[str, str]]:
    """머리 칸이 HEADER 와 같은 표의 행들 — 구분 줄(`|---|`)은 건너뜁니다."""
    lines = section.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("|") and tuple(_cells(line)) == HEADER:
            rows: list[dict[str, str]] = []
            for body in lines[index + 1 :]:
                if not body.strip().startswith("|"):
                    break
                cells = _cells(body)
                if all(set(cell) <= set("-: ") for cell in cells):
                    continue
                rows.append(dict(zip(HEADER, cells)))
            return rows
    return []


def _names(cell: str) -> list[str] | None:
    """이름 칸의 이름들 — `—` 는 빈 목록, 그 밖은 `` `이름` · `이름` `` 꼴만 읽고 다른 꼴은 None."""
    if cell == NONE:
        return []
    names = re.findall(r"`([^`]*)`", cell)
    if not names or cell != " · ".join(f"`{name}`" for name in names):
        return None
    return names


def _rule_exists(number: str) -> bool:
    return any(line.startswith(f"{number}. ") for line in SYSTEM_PROMPT.splitlines())


_FUNCTIONS: dict[Path, set[str]] = {}


def _test_exists(pair: str) -> bool:
    """`<경로>::<함수>` — 저장소 뿌리에서 그 파일이 있고 그 이름의 함수 정의가 있는지."""
    path_text, sep, name = pair.partition("::")
    if not sep or not path_text or not name:
        return False
    path = ROOT / path_text
    if not path.is_file():
        return False
    if path not in _FUNCTIONS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        _FUNCTIONS[path] = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
    return name in _FUNCTIONS[path]


def table_problems(rows: Sequence[Mapping[str, str]]) -> list[str]:
    """대조표의 문제 — 비어 있어야 열한 문장이 하나씩 막는 자리 · 짝 테스트와 함께 있습니다."""
    problems: list[str] = []
    for sentence in TASK_SENTENCES:
        if sum(1 for row in rows if row.get("과제 문장") == sentence) != 1:
            problems.append(f"없는 문장: {sentence}")
    checks = {
        "jev 질문": lambda name: name in CHECK_QUESTIONS,
        "코드 검사": lambda name: name in code_failures.__code__.co_names,
        "스스로 건너뜀": lambda name: name in (NO_SCENE, NO_CONCERN),
        "짝 테스트": _test_exists,
    }
    for row in rows:
        label = row.get("번호", "")
        blank = [column for column in HEADER if not row.get(column, "").strip()]
        for column in blank:
            problems.append(f"빈 칸: {label} {column}")
        rules = row.get("프롬프트 규칙", "")
        if "프롬프트 규칙" not in blank and rules != NONE:
            if not RULES_RE.fullmatch(rules):
                problems.append(f"{label} 프롬프트 규칙: 모양이 다른 칸")
            else:
                for number in re.findall(r"\d+", rules):
                    if not _rule_exists(number):
                        problems.append(f"{label} 프롬프트 규칙: 없는 규칙 {number}")
        for column, known in checks.items():
            if column in blank:
                continue
            names = _names(row[column])
            if names is None:
                problems.append(f"{label} {column}: 모양이 다른 칸")
                continue
            if column == "짝 테스트" and not names:
                problems.append(f"{label} 짝 테스트: 없음")
            for name in names:
                if not known(name):
                    problems.append(f"{label} {column}: 없는 이름 {name}")
        unplaced = all(row.get(column) == NONE for column in PLACE_COLUMNS)
        if unplaced and row.get("막지 않음") == NONE:
            problems.append(f"{label} 막는 자리도 이유도 없음")
    return problems


def contract_rows() -> list[dict[str, str]]:
    return table_rows(section_text(CONTRACT.read_text(encoding="utf-8")))


class TaskTableTest(unittest.TestCase):
    """대조표 판정 — 지금 표는 초록, 닮은 꼴로 고친 표는 빨강(헌법 12조 표본)."""

    def edited(self, number: str, column: str, value: str) -> list[dict[str, str]]:
        """계약 표의 깊은 복사본에서 그 번호 행의 한 칸을 바꿉니다."""
        rows = copy.deepcopy(contract_rows())
        [row] = [row for row in rows if row["번호"] == number]
        row[column] = value
        return rows

    def assert_red(self, rows: list[dict[str, str]], named: str) -> None:
        problems = table_problems(rows)
        self.assertTrue(problems)
        self.assertTrue(any(named in problem for problem in problems), problems)

    def test_contract_table_is_complete(self) -> None:
        rows = contract_rows()
        self.assertTrue(rows, "계약 '댓글 작성' 절에 과제 문장 대조표가 없습니다")
        self.assertEqual(table_problems(rows), [])

    def test_deleted_sentence_is_red(self) -> None:
        rows = [row for row in copy.deepcopy(contract_rows()) if row["번호"] != "④-3"]
        self.assert_red(rows, f"없는 문장: {TASK_SENTENCES[2]}")

    def test_respaced_sentence_is_red(self) -> None:
        for respaced in ("40  ~ 120자", "40~120자"):
            with self.subTest(respaced=respaced):
                self.assert_red(self.edited("④-4", "과제 문장", respaced), "없는 문장: 40 ~ 120자")

    def test_unknown_jev_question_is_red(self) -> None:
        for odd in ("Mentions_scene", "ｍentions_scene", " mentions_scene", "mentions-scene"):
            with self.subTest(name=odd):
                self.assert_red(self.edited("④-5", "jev 질문", f"`{odd}`"), "④-5 jev 질문")

    def test_unknown_code_check_is_red(self) -> None:
        for odd in ("self_check_failure", "Repeated_run"):
            with self.subTest(name=odd):
                cell = f"`{odd}` · `shared_frame`"
                self.assert_red(self.edited("④-7", "코드 검사", cell), "④-7 코드 검사")

    def test_unknown_pair_test_is_red(self) -> None:
        for odd in (
            "tests/test_writer.py::test_Length_bounds_come_from_config",
            "test_writer.py::test_length_bounds_come_from_config",
        ):
            with self.subTest(pair=odd):
                self.assert_red(self.edited("④-4", "짝 테스트", f"`{odd}`"), "④-4 짝 테스트")

    def test_unquoted_name_is_red(self) -> None:
        self.assert_red(self.edited("④-5", "jev 질문", "mentions_scene"), "④-5 jev 질문")

    def test_blank_unblocked_reason_is_red(self) -> None:
        for blank in ("", "   "):
            with self.subTest(blank=repr(blank)):
                self.assert_red(self.edited("④-1", "막지 않음", blank), "빈 칸: ④-1 막지 않음")

    def test_row_without_any_place_is_red(self) -> None:
        rows = self.edited("④-8", "jev 질문", NONE)
        [row] = [row for row in rows if row["번호"] == "④-8"]
        self.assertEqual([row[column] for column in PLACE_COLUMNS], [NONE] * 4)
        self.assert_red(rows, "④-8 막는 자리도 이유도 없음")

    def test_partial_row_may_carry_a_reason(self) -> None:
        rows = self.edited("④-4", "막지 않음", "글자 수는 설정 `comment` 의 두 값입니다")
        self.assertEqual(table_problems(rows), [])


if __name__ == "__main__":
    unittest.main()
