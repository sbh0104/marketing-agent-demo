"""공개용 사본 테스트 — 작은 가짜 저장소로 검사마다 빨강 · 초록 표본을 봅니다(헌법 12조)."""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import public_copy as pc

REPO = Path(__file__).resolve().parent.parent

GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test",
}

# 표본 — 알려진 가짜 밖의 표본은 실행 때 이어 붙여, 이 파일의 글자 하나하나는 어느 모양에도 걸리지 않습니다
PHONE_KNOWN = "010-0000-1234"
PHONE_NEAR = "".join(("010-0000-", "1235"))
EMAIL_KNOWN = "fake.owner@example.com"
EMAIL_CASE = "".join(("Fake.Owner", "@example.com"))

KEY_KNOWN = "sk-ant-FAKEKEY-ABCDEFGHIJKLMNOP"
KEY_NEAR = "".join(("sk-ant-FAKEKEY-", "ABCDEFGHIJKLMNOQ"))
KEY_SK = "".join(("sk-", "ant-", "Q" * 30))
KEY_AIZA = "".join(("AI", "za", "Bc" * 17, "D"))
KEY_ENV = "".join(("TYPESAFE_API_KEY", "=", "k" * 24))
KEY_SPACED = "".join(("TYPESAFE_API_KEY", ' = "', "k" * 24, '"'))
KEY_EMPTY = "TYPESAFE_API_KEY=\n"

HOME_LINUX = "".join(("/ho", "me/", "someone/x"))
HOME_MAC = "".join(("/Us", "ers/", "someone/x"))
HOME_WIN = "".join(("C:", "\\Users\\", "someone\\x"))
HOME_ESCAPED = "".join(("C:", "\\\\Users\\\\", "someone\\\\x"))
HOME_TILDE = "~/.local/bin/python3.12"
HOME_KNOWN = "C:/Users/user/"
HOME_NEAR = "".join(("C:/Users/", "usex/"))

# 비밀 값 표본 — 세 키의 표지 값, 24글자씩
MARKS = {
    "YOUTUBE_API_KEY": "".join(("MRKyt", "Qw" * 9, "Z")),
    "TYPESAFE_API_KEY": "".join(("MRKjev", "Rt" * 9)),
    "ANTHROPIC_API_KEY": "".join(("MRKclaude", "Pm" * 7, "X")),
}
# 역사에 없는 표지 값 — 초록 실행용
ABSENT_MARKS = {
    "YOUTUBE_API_KEY": "".join(("ABSyt", "Lk" * 9, "W")),
    "TYPESAFE_API_KEY": "".join(("ABSjev", "Nv" * 9)),
    "ANTHROPIC_API_KEY": "".join(("ABSclaude", "Jh" * 7, "Y")),
}

PASSING_TEST = (
    "import unittest\n\n\nclass OkTest(unittest.TestCase):\n"
    "    def test_ok(self):\n        self.assertTrue(True)\n"
)
FAILING_TEST = (
    "import unittest\n\n\nclass OkTest(unittest.TestCase):\n"
    "    def test_ok(self):\n        self.fail('빨강')\n"
)


class Fake:
    """`git init -q -b main` 으로 만든 작은 가짜 저장소 — init=False 면 이미 있는 저장소(사본 · 복제본)를 봅니다."""

    def __init__(self, root: Path, init: bool = True) -> None:
        self.root = root
        if init:
            root.mkdir(parents=True, exist_ok=True)
            self.git("init", "-q", "-b", "main")

    def git(self, *args: str, env: dict[str, str] | None = None) -> str:
        done = subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            encoding="utf-8",
            check=False,
            env={**os.environ, **(env or {})},
        )
        if done.returncode:
            raise AssertionError(f"git {' '.join(args)}: {done.stderr}")
        return done.stdout

    def write(self, path: str, text: str = "x\n") -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def remove(self, path: str) -> None:
        self.git("rm", "-q", "--", path)

    def commit(
        self, message: str = "커밋", *, force: tuple[str, ...] = (), env: dict[str, str] | None = None
    ) -> None:
        self.git("add", "-A")
        if force:
            self.git("add", "-f", "--", *force)
        self.git("commit", "-q", "--allow-empty", "-m", message, env=env)

    def gitignore(self) -> None:
        shutil.copyfile(REPO / ".gitignore", self.root / ".gitignore")

    def suite(self, passing: bool = True) -> None:
        self.write("tests/__init__.py", "")
        self.write("tests/test_ok.py", PASSING_TEST if passing else FAILING_TEST)

    def messages(self, rev: str = "main") -> list[str]:
        return [m for m in self.git("log", "-z", "--format=%B", rev).split("\0") if m]

    def state(self) -> tuple[str, str, str]:
        """원본이 그대로인지 볼 것 — 참조 · 작업 폴더 상태 · HEAD."""
        return (
            self.git("for-each-ref"),
            self.git("status", "--porcelain"),
            self.git("rev-parse", "HEAD"),
        )


def write_known(path: Path, contacts=(), keys=(), homes=()) -> Path:
    data = {"contacts": list(contacts), "keys": list(keys), "homes": list(homes)}
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def write_env(path: Path, values: dict[str, str]) -> Path:
    path.write_text("".join(f"{name}={value}\n" for name, value in values.items()), encoding="utf-8")
    return path


def run_main(*args: object) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = pc.main([str(arg) for arg in args])
    return code, out.getvalue()


def last_line(out: str) -> str:
    lines = [line for line in out.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def joined(check: pc.Check) -> str:
    return "\n".join(check.details)


def where_paths(check: pc.Check) -> set[str]:
    """경로 검사의 자리 줄에서 경로만 — `  <경로> @ <커밋>`."""
    return {line.strip().rsplit(" @ ", 1)[0] for line in check.details}


@unittest.skipUnless(shutil.which("git"), "git 이 있어야 합니다")
class GitCase(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(os.environ, GIT_ENV)
        patcher.start()
        self.addCleanup(patcher.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.known = write_known(self.tmp / "known.json")

    def fake(self, name: str = "src") -> Fake:
        return Fake(self.tmp / name)

    def texts(self, fake: Fake, rev: str = "main") -> list[pc.Text]:
        return pc.history_texts(fake.root, pc.walk(fake.root, rev))

    def scan_only(self, fake: Fake, *extra: object) -> tuple[int, str]:
        return run_main("--scan-only", "--source", fake.root, "--known", self.known, *extra)


class HarnessPathTest(GitCase):
    RED = (".claude/settings.json", "docs/agents.html", ".adw/cycle.yml")
    GREEN = (".adw/constitution.md", ".adw/permissions.json")

    def setUp(self) -> None:
        super().setUp()
        self.src = self.fake()
        for path in (*self.RED, *self.GREEN, "README.md"):
            self.src.write(path)
        self.src.commit("처음")
        for path in self.RED:
            self.src.remove(path)
        self.src.commit("하네스를 뺌")

    def harness(self) -> pc.Check:
        return pc.check_harness(pc.walk(self.src.root, "main"), pc.harness_paths(self.src.root))

    def test_harness_paths_in_older_commit_are_red(self) -> None:
        check = self.harness()
        self.assertTrue(check.failed)
        self.assertEqual(where_paths(check), set(self.RED))

    def test_harness_path_in_tip_is_red(self) -> None:
        self.src.write(".adw/workflow.yml")
        self.src.commit("끝 판에 하네스")
        self.assertIn(".adw/workflow.yml", where_paths(self.harness()))

    def test_kept_adw_records_are_green(self) -> None:
        paths = where_paths(self.harness())
        for path in self.GREEN:
            with self.subTest(path=path):
                self.assertNotIn(path, paths)

    def test_clean_fake_is_green(self) -> None:
        clean = self.fake("clean")
        for path in (*self.GREEN, "README.md"):
            clean.write(path)
        clean.commit()
        check = pc.check_harness(pc.walk(clean.root, "main"), pc.harness_paths(clean.root))
        self.assertFalse(check.failed)

    def test_untracked_list_adds_paths(self) -> None:
        self.src.write(".adw/extra.yml")
        self.src.commit("더함")
        self.assertNotIn(".adw/extra.yml", where_paths(self.harness()))
        self.src.write(".adw/harness-paths", "# 주석\n.adw/extra.yml/\n\n.claude\n")
        entries = pc.harness_paths(self.src.root)
        self.assertEqual(entries[: len(pc.HARNESS_PATHS)], pc.HARNESS_PATHS)
        self.assertEqual(entries[len(pc.HARNESS_PATHS) :], (".adw/extra.yml",))
        self.assertIn(".adw/extra.yml", where_paths(self.harness()))


class IgnoredPathTest(GitCase):
    RED = (".env", "docs/marketing-agent.pdf", "my-profile/Default/Cookies")
    GREEN = (".env.example", "logs/sample.log")

    def ignored(self, fake: Fake) -> pc.Check:
        return pc.check_ignored(pc.walk(fake.root, "main"), fake.root)

    def test_env_pdf_and_cookies_in_older_commit_are_red(self) -> None:
        src = self.fake()
        src.gitignore()
        for path in (*self.RED, *self.GREEN):
            src.write(path)
        src.commit("처음", force=self.RED)
        for path in self.RED:
            src.remove(path)
        src.commit("뺌")
        check = self.ignored(src)
        self.assertTrue(check.failed)
        self.assertEqual(where_paths(check), set(self.RED))

    def test_env_in_tip_is_red(self) -> None:
        src = self.fake()
        src.gitignore()
        src.write(".env", KEY_EMPTY)
        src.commit("처음", force=(".env",))
        self.assertEqual(where_paths(self.ignored(src)), {".env"})

    def test_env_example_and_sample_log_are_green(self) -> None:
        src = self.fake()
        src.gitignore()
        for path in (*self.GREEN, "README.md"):
            src.write(path)
        src.commit()
        self.assertEqual(src.git("ls-files", *self.GREEN).split(), sorted(self.GREEN))
        self.assertFalse(self.ignored(src).failed)


class ContactTest(GitCase):
    def contacts(self, fake: Fake, known=()) -> pc.Check:
        return pc.check_contacts(self.texts(fake), known)

    def test_clean_fake_is_green(self) -> None:
        src = self.fake()
        src.write("a.txt", "연락처 없음\n")
        src.commit()
        self.assertFalse(self.contacts(src).failed)

    def test_contact_in_tip_file_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f"전화 {PHONE_KNOWN}\n")
        src.commit()
        check = self.contacts(src)
        self.assertTrue(check.failed)
        self.assertIn(f"{json.dumps(PHONE_KNOWN)} ← a.txt @ ", joined(check))

    def test_contact_only_in_older_commit_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f"전화 {PHONE_KNOWN}\n")
        src.commit()
        src.write("a.txt", "지움\n")
        src.commit()
        self.assertIn(json.dumps(PHONE_KNOWN), joined(self.contacts(src)))

    def test_contact_only_in_message_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", "깨끗\n")
        src.commit(f"전화 {PHONE_KNOWN}")
        check = self.contacts(src)
        self.assertTrue(check.failed)
        self.assertRegex(joined(check), r"← 커밋 [0-9a-f]+ 메시지")

    def test_known_contact_is_green(self) -> None:
        src = self.fake()
        src.write("a.txt", f"전화 {PHONE_KNOWN} · 메일 {EMAIL_KNOWN}\n")
        src.commit()
        self.assertFalse(self.contacts(src, {PHONE_KNOWN, EMAIL_KNOWN}).failed)

    def test_one_edit_from_known_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f"전화 {PHONE_NEAR}\n")
        src.write("b.txt", f"메일 {EMAIL_CASE}\n")
        src.commit()
        check = self.contacts(src, {PHONE_KNOWN, EMAIL_KNOWN})
        self.assertIn(json.dumps(PHONE_NEAR), joined(check))
        self.assertIn(json.dumps(EMAIL_CASE), joined(check))

    def test_author_email_is_not_scanned(self) -> None:
        src = self.fake()
        src.write("a.txt", "깨끗\n")
        identity = {"GIT_AUTHOR_EMAIL": EMAIL_KNOWN, "GIT_COMMITTER_EMAIL": EMAIL_KNOWN}
        src.commit("이름표만 메일", env=identity)
        self.assertIn(EMAIL_KNOWN, src.git("log", "--format=%ae %ce"))
        self.assertFalse(self.contacts(src).failed)
        src.commit(f"메시지에 {EMAIL_KNOWN}", env=identity)
        check = self.contacts(src)
        self.assertEqual(check.details, [line for line in check.details if "메시지" in line])
        self.assertIn(json.dumps(EMAIL_KNOWN), joined(check))

    def test_scan_only_finds_older_contact(self) -> None:
        src = self.fake()
        src.write("a.txt", f"전화 {PHONE_NEAR}\n")
        src.commit()
        src.write("a.txt", "지움\n")
        src.commit()
        code, out = self.scan_only(src, "--no-env")
        self.assertEqual(code, pc.EXIT_FAILED)
        self.assertIn("✗ 연락처 모양 — 1곳", out)
        self.assertTrue(last_line(out).startswith("공개 전 검사 실패 — 검사 1개"))


class KeyTest(GitCase):
    RED = (KEY_SK, KEY_AIZA, KEY_ENV, KEY_SPACED)

    def keys(self, fake: Fake, known=()) -> pc.Check:
        return pc.check_keys(self.texts(fake), known)

    def test_shapes_are_red(self) -> None:
        src = self.fake()
        for i, sample in enumerate(self.RED):
            src.write(f"k{i}.txt", f"값 {sample}\n")
        src.commit()
        check = self.keys(src)
        for i, sample in enumerate(self.RED):
            with self.subTest(sample=sample):
                self.assertIn(f"← k{i}.txt @ ", joined(check))
        self.assertEqual(len(check.details), len(self.RED))

    def test_empty_env_line_is_green(self) -> None:
        src = self.fake()
        src.write(".env.example", KEY_EMPTY)
        src.commit()
        self.assertFalse(self.keys(src).failed)

    def test_known_fake_is_green(self) -> None:
        src = self.fake()
        src.write("a.txt", f"가짜 {KEY_KNOWN}\n")
        src.commit()
        self.assertTrue(self.keys(src).failed)
        self.assertFalse(self.keys(src, {KEY_KNOWN}).failed)

    def test_one_edit_from_known_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f"가짜 {KEY_NEAR}\n")
        src.commit()
        self.assertIn(json.dumps(KEY_NEAR), joined(self.keys(src, {KEY_KNOWN})))

    def test_key_in_older_commit_and_message_are_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f"값 {KEY_SK}\n")
        src.commit()
        src.write("a.txt", "지움\n")
        src.commit(f"메시지 {KEY_AIZA}")
        text = joined(self.keys(src))
        self.assertIn(f"{json.dumps(KEY_SK)} ← a.txt @ ", text)
        self.assertRegex(text, json.dumps(KEY_AIZA) + r" ← 커밋 [0-9a-f]+ 메시지")

    def test_scan_only_finds_key(self) -> None:
        src = self.fake()
        src.write("a.txt", f"값 {KEY_SK}\n")
        src.commit()
        code, out = self.scan_only(src, "--no-env")
        self.assertEqual(code, pc.EXIT_FAILED)
        self.assertIn("✗ 키 모양 — 1곳", out)


class SecretValueTest(GitCase):
    def setUp(self) -> None:
        super().setUp()
        self.env = write_env(self.tmp / "secrets.env", MARKS)

    def values(self, fake: Fake, env: Path | None) -> pc.Check:
        return pc.check_secret_values(self.texts(fake), env)

    def test_value_in_older_blob_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f"{MARKS['TYPESAFE_API_KEY']}\n")
        src.commit()
        src.write("a.txt", "지움\n")
        src.commit()
        check = self.values(src, self.env)
        self.assertTrue(check.failed)
        self.assertIn("TYPESAFE_API_KEY 값 ← a.txt @ ", joined(check))

    def test_value_in_message_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", "깨끗\n")
        src.commit(f"키 {MARKS['ANTHROPIC_API_KEY']}")
        self.assertRegex(joined(self.values(src, self.env)), r"ANTHROPIC_API_KEY 값 ← 커밋 [0-9a-f]+ 메시지")

    def test_eight_char_prefix_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f"조각 {MARKS['YOUTUBE_API_KEY'][:8]} 끝\n")
        src.commit()
        self.assertIn("YOUTUBE_API_KEY 값 ← a.txt @ ", joined(self.values(src, self.env)))

    def test_yaml_form_is_red(self) -> None:
        src = self.fake()
        src.write("a.yaml", f"TYPESAFE_API_KEY: {MARKS['TYPESAFE_API_KEY']}\n")
        src.commit()
        self.assertIn("TYPESAFE_API_KEY 값 ← a.yaml @ ", joined(self.values(src, self.env)))

    def test_clean_history_is_green(self) -> None:
        src = self.fake()
        src.write("a.txt", "깨끗\n")
        src.commit("깨끗한 메시지")
        check = self.values(src, self.env)
        self.assertFalse(check.failed)
        self.assertFalse(check.skipped)

    def test_missing_env_fails_and_no_env_skips(self) -> None:
        src = self.fake()
        src.write("a.txt", "깨끗\n")
        src.commit()
        missing = self.values(src, self.tmp / "none.env")
        self.assertTrue(missing.failed)
        self.assertIn("--no-env", joined(missing))
        empty = write_env(self.tmp / "empty.env", dict.fromkeys(MARKS, ""))
        self.assertTrue(self.values(src, empty).failed)
        skipped = self.values(src, None)
        self.assertTrue(skipped.skipped)
        self.assertFalse(skipped.failed)

    def test_value_is_never_printed(self) -> None:
        src = self.fake()
        src.suite()
        src.write("a.txt", f"{MARKS['TYPESAFE_API_KEY']}\n")
        src.write("b.txt", f"조각 {MARKS['YOUTUBE_API_KEY'][:8]}\n")
        src.commit(f"키 {MARKS['ANTHROPIC_API_KEY']}")
        src.write("a.txt", "지움\n")
        src.commit()
        runs = (
            ("--scan-only",),
            ("--dest", self.tmp / "copy"),
        )
        for mode in runs:
            with self.subTest(mode=mode[0]):
                done = subprocess.run(
                    [sys.executable, "-m", "tests.public_copy", *map(str, mode)]
                    + ["--source", str(src.root), "--known", str(self.known), "--env", str(self.env)],
                    cwd=REPO,
                    capture_output=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertEqual(done.returncode, pc.EXIT_FAILED, done.stdout + done.stderr)
                shown = done.stdout + done.stderr
                for name in MARKS:
                    self.assertIn(f"{name} 값 ← ", shown)
                for value in MARKS.values():
                    for end in range(8, len(value) + 1):
                        self.assertNotIn(value[:end], shown)


class HomeTest(GitCase):
    RED = (HOME_LINUX, HOME_MAC, HOME_WIN, HOME_ESCAPED)

    def homes(self, fake: Fake, known=(), messages: bool = False) -> pc.Check:
        walked = pc.walk(fake.root, "main")
        texts = pc.tip_texts(fake.root, walked)
        if messages:
            texts += pc.message_texts(walked)
        return pc.check_homes(texts, known)

    def test_home_shapes_in_tip_are_red(self) -> None:
        src = self.fake()
        for i, sample in enumerate(self.RED):
            src.write(f"h{i}.txt", f"경로 {sample}\n")
        src.commit()
        check = self.homes(src)
        for i, sample in enumerate(self.RED):
            with self.subTest(sample=sample):
                self.assertIn(f"← h{i}.txt @ ", joined(check))

    def test_tilde_path_is_green(self) -> None:
        src = self.fake()
        src.write("a.txt", f"경로 {HOME_TILDE}\n")
        src.commit()
        self.assertFalse(self.homes(src).failed)

    def test_known_fake_is_green_and_one_edit_is_red(self) -> None:
        src = self.fake()
        src.write("a.txt", f'local = "{HOME_KNOWN}AppData/Local"\n')
        src.commit()
        self.assertFalse(self.homes(src, {HOME_KNOWN}).failed)
        src.write("b.txt", f'local = "{HOME_NEAR}AppData/Local"\n')
        src.commit()
        self.assertIn(f"{json.dumps(HOME_NEAR)} ← b.txt @ ", joined(self.homes(src, {HOME_KNOWN})))

    def test_home_path_in_message_is_red_in_copy_scope_only(self) -> None:
        src = self.fake()
        src.write("a.txt", "깨끗\n")
        src.commit(f"설명 {HOME_LINUX}/y.md")
        self.assertRegex(joined(self.homes(src, messages=True)), r"← 커밋 [0-9a-f]+ 메시지")
        self.assertFalse(self.homes(src).failed)
        code, out = self.scan_only(src, "--no-env")
        self.assertEqual(code, pc.EXIT_OK, out)
        self.assertIn("✓ 홈 경로", out)

    def test_home_path_only_in_older_blob_is_green_in_scan_only(self) -> None:
        src = self.fake()
        src.write("notes.md", f"경로 {HOME_LINUX}\n")
        src.commit()
        src.write("notes.md", "지움\n")
        src.commit()
        code, out = self.scan_only(src, "--no-env")
        self.assertEqual(code, pc.EXIT_OK, out)
        self.assertIn("✓ 홈 경로", out)

    def test_home_path_only_in_older_blob_stays_in_copy(self) -> None:
        src = self.fake()
        src.suite()
        src.write("notes.md", f"경로 {HOME_LINUX}\n")
        src.commit()
        src.write("notes.md", "지움\n")
        src.commit()
        dest = self.tmp / "copy"
        code, out = run_main(
            "--source", src.root, "--dest", dest, "--known", self.known, "--no-env"
        )
        self.assertEqual(code, pc.EXIT_OK, out)
        self.assertIn("✓ 홈 경로", out)
        self.assertTrue(last_line(out).startswith("공개용 사본 검사 통과"))
        copy = Fake(dest, init=False)
        first = copy.git("rev-list", "--max-parents=0", "main").strip()
        self.assertEqual(copy.git("show", f"{first}:notes.md"), f"경로 {HOME_LINUX}\n")


class MessageRewriteTest(GitCase):
    def test_message_home_path_is_rewritten(self) -> None:
        src = self.fake()
        src.suite()
        src.commit("처음 — 홈 없음")
        src.write("a.txt", "둘째\n")
        src.commit(f"설명 {HOME_LINUX}/y.md 끝\n\n본문 {HOME_MAC} · {HOME_WIN}\n")
        src.write("a.txt", "셋째\n")
        src.commit("그대로 — ~/x 는 이미 짧은 꼴")
        dest = self.tmp / "copy"
        code, out = run_main(
            "--source", src.root, "--dest", dest, "--known", self.known, "--no-env"
        )
        self.assertEqual(code, pc.EXIT_OK, out)
        self.assertIn("✓ 홈 경로", out)
        before = src.messages()
        expected = [
            message.replace(HOME_LINUX[:-1], "~/")
            .replace(HOME_MAC[:-1], "~/")
            .replace(HOME_WIN[:-1], "~/")
            for message in before
        ]
        copy = Fake(dest, init=False)
        after = copy.messages()
        self.assertNotEqual(after, before)
        self.assertEqual(after, expected)
        self.assertIn("설명 ~/x/y.md 끝", after[1])


class SuiteCheckTest(GitCase):
    def test_failing_suite_is_red(self) -> None:
        src = self.fake()
        src.suite(passing=False)
        check = pc.check_suite(src.root)
        self.assertTrue(check.failed)
        self.assertIn("FAILED", joined(check))

    def test_passing_suite_is_green(self) -> None:
        src = self.fake()
        src.suite()
        self.assertFalse(pc.check_suite(src.root).failed)


class HistoryCheckTest(GitCase):
    def setUp(self) -> None:
        super().setUp()
        self.src = self.fake()
        identity = {"GIT_AUTHOR_EMAIL": EMAIL_KNOWN, "GIT_COMMITTER_EMAIL": EMAIL_KNOWN}
        self.src.write("a.txt", "하나\n")
        self.src.commit("하나", env=identity)
        self.src.write("a.txt", "둘\n")
        self.src.commit("둘", env=identity)
        self.dest = self.tmp / "clone"
        self.src.git("clone", "-q", str(self.src.root), str(self.dest))
        self.copy = Fake(self.dest, init=False)

    def history(self) -> pc.Check:
        return pc.check_history(self.src.root, "main", self.dest)

    def test_plain_clone_is_green(self) -> None:
        self.assertFalse(self.history().failed)

    def test_amended_author_is_red(self) -> None:
        self.copy.git("commit", "-q", "--amend", "--no-edit", "--author=other <test>")
        check = self.history()
        self.assertTrue(check.failed)
        self.assertNotIn("@", joined(check))

    def test_amended_older_author_is_red(self) -> None:
        """끝 판은 그대로 두고 앞 커밋의 작성자 이름만 바꿉니다 — 날짜와 다른 이름표는 원본 그대로."""
        fmt = "--format=%an%x00%ae%x00%ad%x00%cn%x00%ce%x00%cd"
        first, second = self.copy.git("rev-list", "--reverse", "main").split()

        def identity(commit: str) -> dict[str, str]:
            fields = self.copy.git("log", "-1", fmt, "--date=raw", commit).strip("\n").split("\0")
            names = ("NAME", "EMAIL", "DATE")
            return {
                **{f"GIT_AUTHOR_{n}": v for n, v in zip(names, fields[:3])},
                **{f"GIT_COMMITTER_{n}": v for n, v in zip(names, fields[3:])},
            }

        older = {**identity(first), "GIT_AUTHOR_NAME": "other"}
        new_first = self.copy.git(
            "commit-tree", f"{first}^{{tree}}", "-m", "하나", env=older
        ).strip()
        new_second = self.copy.git(
            "commit-tree", f"{second}^{{tree}}", "-p", new_first, "-m", "둘", env=identity(second)
        ).strip()
        self.copy.git("update-ref", "refs/heads/main", new_second)
        check = self.history()
        self.assertTrue(check.failed)
        self.assertIn("2번째", joined(check))
        self.assertNotIn("@", joined(check))

    def test_extra_commit_is_red(self) -> None:
        self.copy.git("commit", "-q", "--allow-empty", "-m", "더")
        check = self.history()
        self.assertTrue(check.failed)
        self.assertIn("커밋 수", joined(check))


class RemoteCheckTest(GitCase):
    def test_remote_is_red_until_removed(self) -> None:
        src = self.fake()
        src.commit()
        dest = self.tmp / "clone"
        src.git("clone", "-q", str(src.root), str(dest))
        check = pc.check_remote(dest)
        self.assertTrue(check.failed)
        self.assertIn("origin", joined(check))
        src.git("-C", str(dest), "remote", "remove", "origin")
        self.assertFalse(pc.check_remote(dest).failed)


class SetupTest(GitCase):
    def setUp(self) -> None:
        super().setUp()
        self.src = self.fake()
        self.src.suite()
        self.src.commit()

    def test_dest_not_empty_exits_2_and_writes_nothing(self) -> None:
        dest = self.tmp / "dest"
        dest.mkdir()
        (dest / "keep.txt").write_text("그대로\n", encoding="utf-8")
        before = self.src.state()
        code, out = run_main("--source", self.src.root, "--dest", dest, "--known", self.known)
        self.assertEqual(code, pc.EXIT_SETUP)
        self.assertTrue(last_line(out).startswith("준비 실패 — "))
        self.assertEqual(sorted(p.name for p in dest.iterdir()), ["keep.txt"])
        self.assertEqual(self.src.state(), before)

    def test_dest_inside_source_exits_2(self) -> None:
        for dest in (self.src.root / "copy", self.src.root):
            with self.subTest(dest=dest.name):
                before = self.src.state()
                code, out = run_main("--source", self.src.root, "--dest", dest, "--known", self.known)
                self.assertEqual(code, pc.EXIT_SETUP)
                self.assertTrue(last_line(out).startswith("준비 실패 — "))
                self.assertFalse((self.src.root / "copy").exists())
                self.assertEqual(self.src.state(), before)

    def test_missing_known_file_exits_2(self) -> None:
        dest = self.tmp / "dest"
        code, out = run_main("--source", self.src.root, "--dest", dest, "--known", self.tmp / "none.json")
        self.assertEqual(code, pc.EXIT_SETUP)
        self.assertTrue(last_line(out).startswith("준비 실패 — "))
        self.assertFalse(dest.exists())

    def test_known_file_with_wrong_keys_exits_2(self) -> None:
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({"contacts": [], "keys": []}), encoding="utf-8")
        dest = self.tmp / "dest"
        code, out = run_main("--source", self.src.root, "--dest", dest, "--known", bad)
        self.assertEqual(code, pc.EXIT_SETUP)
        self.assertFalse(dest.exists())

    def test_scan_only_refuses_bad_known_and_dest(self) -> None:
        before = self.src.state()
        for mode in ("--scan-only", "--print-known"):
            with self.subTest(mode=mode):
                code, out = run_main(mode, "--source", self.src.root, "--dest", self.tmp / "d")
                self.assertEqual(code, pc.EXIT_SETUP)
                self.assertTrue(last_line(out).startswith("준비 실패 — "))
                self.assertFalse((self.tmp / "d").exists())
        code, out = run_main("--scan-only", "--source", self.src.root, "--known", self.tmp / "none.json")
        self.assertEqual(code, pc.EXIT_SETUP)
        self.assertTrue(last_line(out).startswith("준비 실패 — "))
        self.assertEqual(self.src.state(), before)

    def test_env_and_no_env_together_exit_2(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            run_main("--source", self.src.root, "--env", self.tmp / "a.env", "--no-env")
        self.assertEqual(raised.exception.code, pc.EXIT_SETUP)


@unittest.skipUnless(shutil.which("git"), "git 이 있어야 합니다")
class PublicCopyRunTest(unittest.TestCase):
    """초록 실행 하나를 함께 봅니다 — 첫 커밋에 하네스 경로, 추적 안 되는 목록에 더한 경로."""

    STRIPPED = (".claude/settings.json", "docs/agents.html", ".adw/.gitignore", ".adw/extra.yml")

    @classmethod
    def setUpClass(cls) -> None:
        patcher = mock.patch.dict(os.environ, GIT_ENV)
        patcher.start()
        cls.addClassCleanup(patcher.stop)
        tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.tmp = Path(tmp.name)
        src = Fake(cls.tmp / "src")
        src.gitignore()
        src.suite()
        for path in (".claude/settings.json", "docs/agents.html", ".adw/constitution.md", ".adw/extra.yml"):
            src.write(path)
        src.write(".adw/.gitignore", "harness-paths\n")
        src.write("README.md", "처음\n")
        src.commit("처음", env={"GIT_AUTHOR_EMAIL": EMAIL_KNOWN})
        src.write("README.md", "둘째\n")
        src.commit("둘째")
        src.write(".adw/harness-paths", ".adw/extra.yml\n")
        cls.src = src
        cls.before = src.state()
        env = write_env(cls.tmp / "secrets.env", ABSENT_MARKS)
        known = write_known(cls.tmp / "known.json")
        cls.dest = cls.tmp / "copy"
        cls.code, cls.out = run_main(
            "--source", src.root, "--dest", cls.dest, "--known", known, "--env", env
        )
        cls.copy = Fake(cls.dest, init=False)

    def test_green_copy_strips_harness_and_keeps_history(self) -> None:
        self.assertEqual(self.code, pc.EXIT_OK, self.out)
        self.assertEqual(self.out.splitlines()[0], f"사본: {self.dest}")
        self.assertTrue(last_line(self.out).startswith("공개용 사본 검사 통과"), self.out)
        self.assertNotIn("비밀 값 건너뜀", self.out)
        for commit in self.copy.git("rev-list", "main").split():
            paths = self.copy.git("ls-tree", "-r", "--name-only", commit).split("\n")
            for path in self.STRIPPED:
                with self.subTest(commit=commit, path=path):
                    self.assertNotIn(path, paths)
        self.assertIn(".adw/constitution.md", self.copy.git("ls-tree", "-r", "--name-only", "main"))

    def test_history_keeps_count_and_identity(self) -> None:
        fmt = "--format=%an%x00%ae%x00%cn%x00%ce%x00%at%x00%ct"
        self.assertEqual(self.copy.git("log", fmt, "main"), self.src.git("log", fmt, "main"))
        self.assertEqual(len(self.copy.git("rev-list", "main").split()), 2)

    def test_copy_has_main_only_and_no_remote(self) -> None:
        refs = self.copy.git("for-each-ref", "--format=%(refname)").split()
        self.assertEqual(refs, ["refs/heads/main"])
        self.assertEqual(self.copy.git("remote"), "")

    def test_source_is_left_untouched(self) -> None:
        self.assertEqual(self.src.state(), self.before)
        self.assertEqual(self.before[1], "")
        self.assertTrue((self.src.root / ".claude" / "settings.json").is_file())

    def test_red_check_exits_1_and_keeps_copy(self) -> None:
        red = Fake(self.tmp / "red")
        red.gitignore()
        red.suite()
        red.write(".env", KEY_EMPTY)
        red.commit("처음", force=(".env",))
        red.remove(".env")
        red.commit("뺌")
        known = write_known(self.tmp / "red-known.json")
        dest = self.tmp / "red-copy"
        code, out = run_main("--source", red.root, "--dest", dest, "--known", known, "--no-env")
        self.assertEqual(code, pc.EXIT_FAILED, out)
        self.assertIn("✗ 무시 규칙 경로 — 1곳", out)
        self.assertTrue(last_line(out).startswith("공개용 사본 검사 실패"))
        self.assertTrue((dest / ".git").is_dir())


class ScanOnlyTest(GitCase):
    def test_contact_only_in_harness_file_is_green(self) -> None:
        src = self.fake()
        src.write(".claude/notes.md", f"전화 {PHONE_NEAR}\n")
        src.write("README.md", "깨끗\n")
        src.commit()
        self.assertTrue(self.texts(src) and pc.check_contacts(self.texts(src), ()).failed)
        code, out = self.scan_only(src, "--no-env")
        self.assertEqual(code, pc.EXIT_OK, out)
        self.assertIn("✓ 연락처 모양", out)
        self.assertTrue(last_line(out).startswith("공개 전 검사 통과 — main"))

    def test_env_in_older_commit_is_red(self) -> None:
        src = self.fake()
        src.gitignore()
        src.write(".env", KEY_EMPTY)
        src.commit("처음", force=(".env",))
        src.remove(".env")
        src.commit("뺌")
        code, out = self.scan_only(src, "--no-env")
        self.assertEqual(code, pc.EXIT_FAILED, out)
        self.assertIn("✗ 무시 규칙 경로 — 1곳", out)
        self.assertIn("– 비밀 값 — 건너뜀 (--no-env)", out)
        self.assertTrue(last_line(out).startswith("공개 전 검사 실패 — 검사 1개"))

    def test_source_is_unchanged_after_scan_only(self) -> None:
        src = self.fake()
        src.gitignore()
        src.write(".env", KEY_EMPTY)
        src.commit("처음", force=(".env",))
        before = src.state()
        listing = sorted(p.relative_to(src.root) for p in src.root.rglob("*"))
        self.scan_only(src, "--no-env")
        self.assertEqual(src.state(), before)
        self.assertEqual(sorted(p.relative_to(src.root) for p in src.root.rglob("*")), listing)

    def test_print_known_lists_without_judging(self) -> None:
        src = self.fake()
        src.write("a.txt", f"{PHONE_KNOWN} {KEY_KNOWN} {HOME_LINUX}\n")
        src.commit()
        home = HOME_LINUX[:-1]
        known = write_known(self.tmp / "all.json", [PHONE_KNOWN], [KEY_KNOWN], [home])
        code, out = run_main("--print-known", "--source", src.root, "--known", known)
        self.assertEqual(code, pc.EXIT_OK, out)
        printed = json.loads(out)
        self.assertEqual(list(printed), ["contacts", "keys", "homes"])
        self.assertIn(PHONE_KNOWN, printed["contacts"])
        self.assertEqual(printed["keys"], [KEY_KNOWN])
        self.assertEqual(printed["homes"], [home])


class KnownFileTest(unittest.TestCase):
    def test_real_known_file_shape(self) -> None:
        data = json.loads(pc.KNOWN_FILE.read_text(encoding="utf-8"))
        self.assertEqual(list(data), ["contacts", "keys", "homes"])
        for name, items in data.items():
            with self.subTest(name=name):
                self.assertIsInstance(items, list)
                self.assertTrue(all(isinstance(item, str) and item for item in items))
                self.assertEqual(items, sorted(set(items)))


if __name__ == "__main__":
    unittest.main()
