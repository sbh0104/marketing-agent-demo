"""커밋된 실제 호출 결과 두 파일(docs/live-check)에 연락처 모양이 없는지 늘 봅니다.

실행기 끝 줄과 같은 목록입니다 — `tests/live_check.py (contact_places)`. 트래커 Phase 6G
(2026-10-15 6G 인터뷰 질문 1 A). 이 테스트를 지우거나 건너뛰기로 바꾸지 않습니다.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path

from tests import live_check

RESULT_PATH = live_check.RESULT_DIR / live_check.RESULT_NAME
SUMMARY_PATH = live_check.RESULT_DIR / live_check.SUMMARY_NAME


def committed_places(paths: Sequence[Path]) -> int:
    """있는 파일만 셉니다 — 없는 파일은 커밋되지 않아 공개될 글이 없습니다(그 파일이 있는지는 test_live_check_applied 가 봅니다)"""
    return live_check.contact_places([path for path in paths if path.exists()])


class PublishedResultTest(unittest.TestCase):
    def test_committed_result_has_no_contact_shape(self) -> None:
        self.assertEqual(committed_places((RESULT_PATH, SUMMARY_PATH)), 0)

    def test_planted_fake_result_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            result_path = Path(folder) / live_check.RESULT_NAME
            summary_path = Path(folder) / live_check.SUMMARY_NAME
            planted = {
                "videos": [{"untrusted": {"description": "문의 fake.owner@example.com"}}],
                "fingerprint": {"jev_models": ["jev 010-0000-1234"]},
            }
            result_path.write_text(json.dumps(planted, ensure_ascii=False), encoding="utf-8")
            summary_path.write_text("요약\n후원 000-000-123456\n", encoding="utf-8")
            self.assertEqual(committed_places((result_path, summary_path)), 3)

    def test_missing_files_count_zero(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            missing = (
                Path(folder) / live_check.RESULT_NAME,
                Path(folder) / live_check.SUMMARY_NAME,
            )
            self.assertEqual(committed_places(missing), 0)


if __name__ == "__main__":
    unittest.main()
