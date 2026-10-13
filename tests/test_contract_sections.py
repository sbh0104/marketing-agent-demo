"""계약 절 이름 규칙 테스트 — 계약 10절: 1–10절은 번호로, 그 뒤에 더한 절은 번호 없이 제목으로 가리킵니다.

빨강이 되는 꼴 둘을 잽니다. docs/contracts.md 의 `## <숫자>.` 제목 번호가 차례대로 1–10 이 아닌 것(10절
뒤에 번호 붙은 제목이 오면 여기에 걸립니다), 그리고 src/ · tests/ · docs/contracts.md 에서 10보다 큰
번호를 단 절 인용(ASCII 숫자 바로 뒤에 '절'). 이 파일도 훑는 범위 안이라, 큰 번호 예시는 section() 으로
실행 중에 만들어 이 파일 글자에는 그 꼴이 없습니다.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTRACT = REPO / "docs" / "contracts.md"
SCAN_DIRS = ("src", "tests")
LAST_NUMBERED = 10
NUMBERED = [str(number) for number in range(1, LAST_NUMBERED + 1)]

HEADING_RE = re.compile(r"^## ([0-9]+)\.", re.MULTILINE)
CITATION_RE = re.compile(r"(?<![0-9])([0-9]+)절")


def section(number: int) -> str:
    """번호 붙은 절 인용 글자를 실행 중에 만듭니다."""
    return f"{number}절"


def numbered_headings(text: str) -> list[str]:
    """줄 맨 앞 `## <숫자>.` 제목의 번호 — 나온 차례대로."""
    return HEADING_RE.findall(text)


def high_citations(text: str) -> list[tuple[int, str]]:
    """10보다 큰 번호를 단 절 인용이 든 줄 — (1부터 센 줄 번호, 앞뒤 공백을 뗀 줄)."""
    return [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), 1)
        if any(int(match.group(1)) > LAST_NUMBERED for match in CITATION_RE.finditer(line))
    ]


def scanned_files() -> list[Path]:
    """계약서, 그리고 src/ · tests/ 아래 모든 파일(__pycache__ 제외) — 빼 주는 파일은 없습니다."""
    files = [CONTRACT]
    for name in SCAN_DIRS:
        files.extend(
            sorted(
                path
                for path in (REPO / name).rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            )
        )
    return files


# 1–10절 제목 — 번호만 봅니다
FIRST_TEN = "".join(f"## {number}. 번호 붙은 절\n" for number in range(1, LAST_NUMBERED + 1))

# 고치기 전 main 의 계약서 — 레인마다 제 사본의 "마지막 번호 + 1" 로 매겨 `## 11.` 이 겹쳤습니다
OLD_MAIN = FIRST_TEN + (
    "## 탐지 · 조회수 추적 — env.py · youtube.py · watcher.py (Phase 2)\n"
    "## 11. 댓글 작성 — `writer.py` (Phase 5)\n"
    "## 11. 트리거 판정 — `trigger.py`\n"
    "## 12. 주제 판별 — `classifier.py` (Phase 3)\n"
)
TITLED = OLD_MAIN.replace("## 11. ", "## ").replace("## 12. ", "## ")

# 10보다 큰 번호의 인용 — 고치기 전 watcher.py · 주제 판별 절에 있던 꼴
HIGH = "\n".join(
    (
        f"탐지 · 조회수 추적 — 한 사이클 = 검색, 그다음 추적 (계약 {section(11)}).",
        f"run_loop 의 사이클 자리에 맞습니다 (계약 9절 · {section(11)}).",
        f"다른 갈래가 자기 {section(11)}을 먼저 들였으면",
        f"계약 {section(12)}",
    )
)

# 남는 인용 — 1–10절 번호, 제목 인용, 풀이 줄의 글
LOW = "\n".join(
    (
        "주소는 계약 5절의 형식만 정확히 읽습니다",
        "테스트 모드 저장(계약 6절 4)",
        "비밀 값 읽기 (계약 8절 · '탐지 · 조회수 추적' 절).",
        "run_loop 의 사이클 자리에 맞습니다 (계약 9절 · '탐지 · 조회수 추적' 절).",
        "10절의 음성 대조가 계속 1 로 끝나는지",
        "- 1–10절은 번호로, 그 뒤에 더하는 절은 번호 없이 제목만 달고 제목으로 가리킵니다",
        "옛 번호 11 · 12 로 가리킨 절은, 기록이 그 자리에서 제목이나 함수 · 모듈 이름으로 밝힌 절입니다",
        "계약 '주제 판별' 절",
    )
)


class ContractSectionNamesTest(unittest.TestCase):
    maxDiff = None  # 빨강일 때 찾은 줄을 모두 보여 줍니다

    def test_old_main_headings_are_red(self) -> None:
        self.assertEqual(numbered_headings(OLD_MAIN), NUMBERED + ["11", "11", "12"])

    def test_number_above_ten_before_ten_is_red(self) -> None:
        self.assertNotEqual(numbered_headings("## 11. 먼저 더한 절\n" + FIRST_TEN), NUMBERED)

    def test_titled_headings_are_green(self) -> None:
        self.assertEqual(numbered_headings(TITLED), NUMBERED)

    def test_citations_above_ten_are_red(self) -> None:
        self.assertEqual([number for number, _ in high_citations(HIGH)], [1, 2, 3, 4])

    def test_citations_up_to_ten_and_titles_are_green(self) -> None:
        self.assertEqual(high_citations(LOW), [])

    def test_contract_numbers_are_one_to_ten(self) -> None:
        self.assertEqual(numbered_headings(CONTRACT.read_text(encoding="utf-8")), NUMBERED)

    def test_no_citation_above_ten_in_scope(self) -> None:
        found = [
            f"{path.relative_to(REPO).as_posix()}:{number}: {line}"
            for path in scanned_files()
            for number, line in high_citations(path.read_text(encoding="utf-8", errors="replace"))
        ]
        self.assertEqual(found, [])

    def test_scope_includes_contract_watcher_and_this_file(self) -> None:
        files = scanned_files()
        for path in (CONTRACT, Path(__file__).resolve(), REPO / "src" / "agent" / "watcher.py"):
            with self.subTest(path=path.name):
                self.assertIn(path, files)


if __name__ == "__main__":
    unittest.main()
