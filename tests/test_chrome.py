"""크롬 쪽 테스트 — 프로필 위치 검사(켤 때) · 켤 명령 · 출력만 하는 CLI."""
from __future__ import annotations

import io
import ntpath
import os
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from agent.chrome import (
    ChromeSetupError,
    check_profile_dir,
    debug_port,
    default_user_data_dirs,
    launch_command,
    main,
)
from agent.config import load_config

ROOT = Path(__file__).resolve().parent.parent
WARNING_PHRASE = "로그인된 계정의 쿠키를 읽을 수 있습니다"


class DefaultDirsTest(unittest.TestCase):
    HOME = Path("/home/user")

    def test_linux_with_xdg_config_home(self) -> None:
        dirs = default_user_data_dirs("linux", {"XDG_CONFIG_HOME": "/cfg"}, self.HOME)
        self.assertEqual(dirs, (Path("/cfg/google-chrome"), Path("/cfg/chromium")))

    def test_linux_without_xdg_config_home(self) -> None:
        dirs = default_user_data_dirs("linux", {}, self.HOME)
        self.assertEqual(
            dirs,
            (self.HOME / ".config" / "google-chrome", self.HOME / ".config" / "chromium"),
        )

    def test_darwin(self) -> None:
        support = self.HOME / "Library" / "Application Support"
        dirs = default_user_data_dirs("darwin", {}, self.HOME)
        self.assertEqual(dirs, (support / "Google" / "Chrome", support / "Chromium"))

    def test_win32_with_localappdata(self) -> None:
        local = "C:/Users/user/AppData/Local"
        dirs = default_user_data_dirs("win32", {"LOCALAPPDATA": local}, self.HOME)
        self.assertEqual(
            dirs,
            (
                Path(local) / "Google" / "Chrome" / "User Data",
                Path(local) / "Chromium" / "User Data",
            ),
        )

    def test_win32_falls_back_to_home(self) -> None:
        local = self.HOME / "AppData" / "Local"
        dirs = default_user_data_dirs("win32", {}, self.HOME)
        self.assertEqual(
            dirs,
            (local / "Google" / "Chrome" / "User Data", local / "Chromium" / "User Data"),
        )


class ProfileCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.home = self.base / "home"
        self.home.mkdir()
        self.default = self.home / ".config" / "google-chrome"
        self.defaults = (self.default, self.home / ".config" / "chromium")

    def check(self, profile: str | Path) -> Path:
        return check_profile_dir(profile, self.repo, defaults=self.defaults)

    def symlink(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"심볼릭 링크를 만들 수 없습니다: {exc}")


class ProfileDirTest(ProfileCase):
    # 받는 위치

    def test_accepts_chrome_profile(self) -> None:
        self.assertEqual(self.check("chrome-profile"), self.repo / "chrome-profile")

    def test_accepts_inside_chrome_profile(self) -> None:
        self.assertEqual(self.check("chrome-profile/work"), self.repo / "chrome-profile" / "work")

    def test_accepts_absolute_path_outside_repo(self) -> None:
        outside = self.base / "elsewhere" / "agent-chrome"
        self.assertEqual(self.check(outside), outside)

    def test_accepts_home_relative_path_outside_repo(self) -> None:
        with mock.patch.dict(os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)}):
            self.assertEqual(self.check("~/agent-chrome"), self.home / "agent-chrome")

    def test_accepts_repo_symlink_pointing_outside(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        self.symlink(self.repo / "link", outside)
        self.assertEqual(self.check("link"), outside)

    # 저장소 안 다른 폴더 — 거부

    def assert_refused_repo(self, profile: str | Path) -> None:
        with self.assertRaises(ChromeSetupError) as caught:
            self.check(profile)
        self.assertIn("chrome-profile/", str(caught.exception))

    def test_refuses_repo_root(self) -> None:
        self.assert_refused_repo(".")
        self.assert_refused_repo(self.repo)

    def test_refuses_other_repo_folder(self) -> None:
        self.assert_refused_repo("profiles/x")

    def test_refuses_dot_dot_out_of_chrome_profile(self) -> None:
        self.assert_refused_repo("chrome-profile/../other")

    def test_refuses_sibling_prefix(self) -> None:
        self.assert_refused_repo("chrome-profile-evil")

    def test_refuses_chrome_profile_symlinked_into_repo(self) -> None:
        (self.repo / "other").mkdir()
        self.symlink(self.repo / "chrome-profile", self.repo / "other")
        self.assert_refused_repo("chrome-profile")

    # 크롬 기본 데이터 폴더 — 거부

    def assert_refused_default(self, profile: str | Path) -> None:
        with self.assertRaises(ChromeSetupError) as caught:
            self.check(profile)
        self.assertIn("136", str(caught.exception))

    def test_refuses_default_dir(self) -> None:
        self.assert_refused_default(self.default)

    def test_refuses_inside_default_dir(self) -> None:
        self.assert_refused_default(self.default / "Default")

    def test_refuses_default_dir_in_other_case_with_windows_normcase(self) -> None:
        windows_os = types.SimpleNamespace(
            path=types.SimpleNamespace(normcase=ntpath.normcase), sep="\\"
        )
        upper = self.home / ".config" / "Google-Chrome"
        with mock.patch("agent.chrome.os", windows_os):
            self.assert_refused_default(upper)
            self.assert_refused_default(upper / "Default")


class DebugPortTest(unittest.TestCase):
    def test_reads_port(self) -> None:
        self.assertEqual(debug_port("http://localhost:9222"), 9222)

    def test_missing_port(self) -> None:
        with self.assertRaises(ChromeSetupError):
            debug_port("http://localhost")

    def test_bad_port(self) -> None:
        with self.assertRaises(ChromeSetupError):
            debug_port("http://localhost:abc")


class LaunchCommandTest(unittest.TestCase):
    def test_exact_argv(self) -> None:
        self.assertEqual(
            launch_command("google-chrome", Path("/p/chrome-profile"), 9222),
            [
                "google-chrome",
                "--remote-debugging-port=9222",
                "--user-data-dir=/p/chrome-profile",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )


class ChromeCliTest(ProfileCase):
    def setUp(self) -> None:
        super().setUp()
        shutil.copy(ROOT / "config.yaml", self.repo / "config.yaml")
        popen = mock.patch("subprocess.Popen", side_effect=AssertionError("Popen 을 부르면 안 됩니다"))
        self.popen = popen.start()
        self.addCleanup(popen.stop)
        self.out = io.StringIO()
        self.err = io.StringIO()

    def run_cli(self, *argv: str) -> int:
        code = main(
            list(argv),
            repo_root=self.repo,
            platform="linux",
            env={"XDG_CONFIG_HOME": str(self.home / ".config")},
            home=self.home,
            out=self.out,
            err=self.err,
        )
        self.popen.assert_not_called()
        return code

    def assert_refused(self, code: int) -> None:
        self.assertEqual(code, 2)
        self.assertIn("크롬 실행 준비 실패", self.err.getvalue())
        self.assertEqual(self.out.getvalue(), "")

    def test_default_profile_prints_command_and_warning(self) -> None:
        port = debug_port(load_config(ROOT / "config.yaml").chrome_debug_url)
        self.assertEqual(self.run_cli(), 0)
        printed = self.out.getvalue()
        self.assertIn(f"--user-data-dir={self.repo / 'chrome-profile'}", printed)
        self.assertIn(f"--remote-debugging-port={port}", printed)
        self.assertTrue(any(WARNING_PHRASE in line for line in printed.splitlines()))
        self.assertEqual(self.err.getvalue(), "")

    def test_repo_folder_profile_exits_2(self) -> None:
        self.assert_refused(self.run_cli("--profile", "profiles/x"))

    def test_default_data_dir_exits_2(self) -> None:
        self.assert_refused(
            self.run_cli("--profile", str(self.home / ".config" / "google-chrome"))
        )

    def test_missing_config_exits_2(self) -> None:
        self.assert_refused(self.run_cli("--config", "missing.yaml"))


if __name__ == "__main__":
    unittest.main()
