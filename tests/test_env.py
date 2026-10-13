"""비밀 값 읽기 테스트 — .env 의 한 줄 규칙과 환경 변수 우선."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent.env import EnvError, read_env_file, require_secret


class EnvCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = self.dir / ".env"

    def write(self, text: str) -> Path:
        self.path.write_text(text, encoding="utf-8", newline="\n")
        return self.path


class ReadEnvFileTest(EnvCase):
    def test_reads_names_values_comments_blanks_and_quotes(self) -> None:
        self.write(
            "# 유튜브 키\n"
            "\n"
            "YOUTUBE_API_KEY=abc-123_XYZ\n"
            "  SPACED  =  값 둘레 공백  \n"
            "DOUBLE=\"따옴표 안 # 그대로\"\n"
            "SINGLE='홑따옴표'\n"
            "INLINE=값 # 주석도 값\n"
            "EMPTY=\n"
            "MISMATCHED='반쪽\"\n"
            "LONE=\"\n"
            "EQUALS=a=b\r\n"
        )
        self.assertEqual(
            read_env_file(self.path),
            {
                "YOUTUBE_API_KEY": "abc-123_XYZ",
                "SPACED": "값 둘레 공백",
                "DOUBLE": "따옴표 안 # 그대로",
                "SINGLE": "홑따옴표",
                "INLINE": "값 # 주석도 값",
                "EMPTY": "",
                "MISMATCHED": "'반쪽\"",
                "LONE": "\"",
                "EQUALS": "a=b",
            },
        )

    def test_bom_is_stripped(self) -> None:
        self.path.write_bytes("﻿YOUTUBE_API_KEY=abc\n".encode("utf-8"))
        self.assertEqual(read_env_file(self.path), {"YOUTUBE_API_KEY": "abc"})

    def test_missing_file_reads_as_empty(self) -> None:
        self.assertEqual(read_env_file(self.dir / "없는.env"), {})

    def test_malformed_line_names_the_line_never_the_value(self) -> None:
        for text in (
            "YOUTUBE_API_KEY=abc\nsecret-value-123\n",
            "YOUTUBE_API_KEY=abc\n1BAD=secret-value-123\n",
            "YOUTUBE_API_KEY=abc\nBAD-NAME=secret-value-123\n",
        ):
            with self.subTest(text=text):
                self.write(text)
                with self.assertRaises(EnvError) as caught:
                    read_env_file(self.path)
                message = str(caught.exception)
                self.assertIn("2번째 줄", message)
                self.assertIn(str(self.path), message)
                self.assertNotIn("secret-value-123", message)

    def test_duplicate_name_is_rejected(self) -> None:
        self.write("YOUTUBE_API_KEY=first-secret\nYOUTUBE_API_KEY=second-secret\n")
        with self.assertRaises(EnvError) as caught:
            read_env_file(self.path)
        message = str(caught.exception)
        self.assertIn("2번째 줄", message)
        self.assertIn("YOUTUBE_API_KEY", message)
        self.assertNotIn("first-secret", message)
        self.assertNotIn("second-secret", message)

    def test_non_utf8_file_is_env_error(self) -> None:
        self.path.write_bytes("YOUTUBE_API_KEY=abc\n".encode("utf-16"))
        with self.assertRaises(EnvError) as caught:
            read_env_file(self.path)
        self.assertIn("UTF-8", str(caught.exception))


class RequireSecretTest(EnvCase):
    def test_environment_variable_wins_over_file(self) -> None:
        self.write("YOUTUBE_API_KEY=from-file\n")
        self.assertEqual(
            require_secret("YOUTUBE_API_KEY", self.path, {"YOUTUBE_API_KEY": "from-env"}),
            "from-env",
        )
        self.assertEqual(
            require_secret("YOUTUBE_API_KEY", self.path, {"YOUTUBE_API_KEY": ""}),
            "from-file",
        )
        self.assertEqual(require_secret("YOUTUBE_API_KEY", self.path, {}), "from-file")

    def test_missing_or_empty_secret_names_key_and_file(self) -> None:
        for label, text in (
            ("no file", None),
            ("empty value", "YOUTUBE_API_KEY=\n"),
            ("name absent", "OTHER_KEY=abc\n"),
        ):
            with self.subTest(label):
                if text is None:
                    self.path.unlink(missing_ok=True)
                else:
                    self.write(text)
                with self.assertRaises(EnvError) as caught:
                    require_secret("YOUTUBE_API_KEY", self.path, {})
                message = str(caught.exception)
                self.assertIn("YOUTUBE_API_KEY", message)
                self.assertIn(str(self.path), message)


if __name__ == "__main__":
    unittest.main()
