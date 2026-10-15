"""제출 문서 테스트 — README · PROCESS.md 가 코드의 프롬프트와 진입점을 그대로 옮겼는지 확인합니다."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import agent.run
from agent.classifier import build_questions
from agent.config import ConfigError, load_config
from agent.writer import (
    CHECK_QUESTIONS,
    REWRITE_PROMPT,
    SELF_CHECK_CRITERIA,
    SYSTEM_PROMPT,
    USER_INSTRUCTION,
    WRITE_TOOL,
)

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
PROCESS = REPO / "PROCESS.md"
CONFIG = REPO / "config.yaml"

RUN_COMMAND = "PYTHONPATH=src python3 -m agent.run"
SUITE_COMMAND = (
    "python3 -X warn_default_encoding -W error::EncodingWarning -m unittest discover -s tests -t ."
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ProcessPromptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.process = read(PROCESS)

    def test_writer_prompts_are_quoted_verbatim(self) -> None:
        for name, text in (
            ("SYSTEM_PROMPT", SYSTEM_PROMPT),
            ("USER_INSTRUCTION", USER_INSTRUCTION),
            ("REWRITE_PROMPT", REWRITE_PROMPT),
            ("WRITE_TOOL", json.dumps(WRITE_TOOL, ensure_ascii=False, indent=2)),
        ):
            with self.subTest(name=name):
                self.assertIn(text, self.process)

    def test_jev_questions_are_quoted_verbatim(self) -> None:
        questions = build_questions(load_config(CONFIG))
        self.assertIn(json.dumps(questions, ensure_ascii=False, indent=2), self.process)
        for name, text in {**CHECK_QUESTIONS, **SELF_CHECK_CRITERIA}.items():
            with self.subTest(name=name):
                self.assertIn(text, self.process)


class ReadmeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = read(README)

    def test_run_command_is_the_entry_point(self) -> None:
        self.assertIn(f"{RUN_COMMAND} --once --dry-run", self.readme)
        self.assertIn(RUN_COMMAND, agent.run.__doc__ or "")

    def test_run_lines_are_locked_line_by_line(self) -> None:
        """맥 첫 실행 줄과 녹화 3단계 줄이 둘 다, 윈도우 줄은 두 조각이 한 줄에 함께 있어야 합니다."""
        self.assertGreaterEqual(self.readme.count(f"{RUN_COMMAND} --once --dry-run"), 2)
        windows = [
            line
            for line in self.readme.splitlines()
            if '$env:PYTHONPATH = "src"' in line and "python -m agent.run --once --dry-run" in line
        ]
        self.assertTrue(windows)

    def test_suite_command_is_the_contract_one(self) -> None:
        self.assertIn(SUITE_COMMAND, self.readme)

    def test_mode_lines_are_test_mode(self) -> None:
        lines = [line for line in self.readme.splitlines() if "mode=" in line]
        self.assertGreaterEqual(len(lines), 2)
        for line in lines:
            with self.subTest(line=line):
                self.assertIn("mode=test", line)

    def test_zwj_keyword_is_refused(self) -> None:
        emoji = "👩‍💻"
        lines = read(CONFIG).split("\n")
        changed = [
            f"keywords: [연애, {emoji}]" if line.startswith("keywords:") else line for line in lines
        ]
        self.assertNotEqual(changed, lines)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.yaml"
            path.write_text("\n".join(changed), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)
        self.assertIn("ZWJ", self.readme)


if __name__ == "__main__":
    unittest.main()
