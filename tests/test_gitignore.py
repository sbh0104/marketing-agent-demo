"""비밀 파일 무시 규칙 테스트 — 계약 8절의 이름 목록을 임의 폴더 아래에서 git check-ignore 로 확인합니다."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SECRET_NAMES = (
    "Cookies",
    "Cookies-journal",
    "Login Data",
    "Login Data For Account",
    "Web Data",
    "Web Data-journal",
    "Local State",
    "Local Storage/leveldb/000003.log",
    "Session Storage/000003.log",
    "Preferences",
    "Secure Preferences",
    "History",
    "History-journal",
    "IndexedDB/https_www.youtube.com_0.indexeddb.leveldb/LOG",
    "Sessions/Session_13300000000000000",
    "Extension Cookies",
    "Account Web Data",
    "cookies.json",
    "youtube_storage_state.json",
    ".env",
    ".env.local",
    ".envrc",
    ".env-local",
    "client_secret_1234-abc.apps.googleusercontent.com.json",
    "token.json",
)

# chrome-profile/ 밖의 임의 폴더 — 사람이 위치 규칙을 어긴 경우
FOLDERS = ("my-profile/Default", "deep/a/b")

# 커밋해야 하는 파일 — 무시되면 안 됩니다 (양성 대조)
KEPT = (
    ".env.example",
    "config.yaml",
    "logs/sample.log",
    "logs/.gitkeep",
    "data/.gitkeep",
    "src/agent/guard.py",
    "docs/live-check/README.md",
    "docs/live-check/result.json",
    "docs/live-check/summary.md",
)


def check_ignore(paths: list[str]) -> dict[str, tuple[str, str]]:
    """git 에게 직접 묻습니다 — {경로: (규칙이 나온 파일, 규칙)}. 맞는 규칙이 없으면 빈 글자."""
    completed = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin", "-z", "-v", "-n"],
        cwd=REPO,
        input="\0".join(paths) + "\0",
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode not in (0, 1):
        raise AssertionError(completed.stderr)
    fields = completed.stdout.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    matches: dict[str, tuple[str, str]] = {}
    for i in range(0, len(fields), 4):
        source, _line, pattern, path = fields[i : i + 4]
        matches[path] = (source, pattern)
    return matches


@unittest.skipUnless(shutil.which("git") and (REPO / ".git").exists(), "git 저장소에서만 확인합니다")
class GitignoreTest(unittest.TestCase):
    def assert_ignored_by_repo(self, matches: dict[str, tuple[str, str]], path: str) -> None:
        source, pattern = matches.get(path, ("", ""))
        self.assertEqual(source, ".gitignore", f"무시되지 않습니다: {path}")
        self.assertFalse(pattern.startswith("!"), f"되살리는 규칙에 걸립니다: {path} ({pattern})")

    def test_profile_secrets_are_ignored_under_any_folder(self) -> None:
        paths = [f"{folder}/{name}" for folder in FOLDERS for name in SECRET_NAMES]
        matches = check_ignore(paths)
        for path in paths:
            with self.subTest(path=path):
                self.assert_ignored_by_repo(matches, path)

    def test_chrome_profile_folder_is_ignored_whole(self) -> None:
        path = "chrome-profile/Default/Bookmarks"
        self.assert_ignored_by_repo(check_ignore([path]), path)

    def test_submitted_files_are_not_ignored(self) -> None:
        matches = check_ignore(list(KEPT))
        for path in KEPT:
            with self.subTest(path=path):
                source, pattern = matches.get(path, ("", ""))
                self.assertTrue(
                    source != ".gitignore" or pattern.startswith("!"),
                    f"제출할 파일이 무시됩니다: {path} ({pattern})",
                )


if __name__ == "__main__":
    unittest.main()
