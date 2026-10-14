"""크롬 쪽 테스트 — 프로필 위치 검사(켤 때) · 켤 명령 · 출력만 하는 CLI · 세션 · 유튜브 페이지.

진짜 Playwright 도 네트워크도 쓰지 않습니다 — 세션은 sys.modules 에 가짜(또는 None) 모듈을 넣고,
페이지는 선택자별 가짜 locator 로 시험합니다.
"""
from __future__ import annotations

import io
import ntpath
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from agent.chrome import (
    COMMENT_INPUT,
    COMMENT_PLACEHOLDER,
    COMMENT_TEXTS,
    COMMENTS,
    COMMENTS_DISABLED_MSG,
    CONFIRM_POLL_MS,
    CONFIRM_POLLS,
    CONFIRM_SCAN,
    SIGNED_IN,
    SUBMIT_BUTTON,
    ChromeSession,
    ChromeSetupError,
    YouTubePage,
    check_profile_dir,
    debug_port,
    default_user_data_dirs,
    launch_command,
    main,
)
from agent.config import load_config
from agent.poster import PageError
from tests.test_config import TEXT_VALUES, variant, write_config

ROOT = Path(__file__).resolve().parent.parent
WARNING_PHRASE = "로그인된 계정의 쿠키를 읽을 수 있습니다"
TEXT = "연락 텀이 길어질 때 불안한 마음, 저도 겪어 봐서 알아요."
# Phase 1C 인터뷰의 크롬 주소 재현 입력 두 줄(폭 없는 공백 · 끝 스페이스)
URL_ROWS = tuple(bad for bad in TEXT_VALUES if bad.label.startswith("debug_url_"))


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

    def test_debug_url_bad_text_exits_2_naming_the_key(self) -> None:
        self.assertEqual(len(URL_ROWS), 2)
        for bad in URL_ROWS:
            with self.subTest(bad.label):
                write_config(self.repo, variant(bad.old, bad.new))
                self.out = io.StringIO()
                self.err = io.StringIO()
                self.assert_refused(self.run_cli())
                self.assertEqual(self.err.getvalue(), f"크롬 실행 준비 실패: {bad.needle}\n")


class ChromeModuleEntryTest(unittest.TestCase):
    """진짜 `python3 -m agent.chrome` — 모듈 입구까지 같은 설정 오류로 끝납니다(Popen 을 막지 않음)."""

    def test_module_run_ends_with_the_config_error(self) -> None:
        self.assertEqual(len(URL_ROWS), 2)
        for bad in URL_ROWS:
            with self.subTest(bad.label), tempfile.TemporaryDirectory() as tmp:
                path = write_config(Path(tmp), variant(bad.old, bad.new))
                result = subprocess.run(
                    [sys.executable, "-m", "agent.chrome", "--config", str(path)],
                    capture_output=True,
                    encoding="utf-8",
                    env={
                        **os.environ,
                        "PYTHONPATH": str(ROOT / "src"),
                        "PYTHONIOENCODING": "utf-8",
                    },
                    cwd=tmp,
                    check=False,
                    timeout=60,
                )
                self.assertEqual(
                    (result.returncode, result.stdout, result.stderr),
                    (2, "", f"크롬 실행 준비 실패: {bad.needle}\n"),
                )


class FakeTimeout(Exception):
    """가짜 playwright.sync_api.TimeoutError."""


class FakeLocator:
    """선택자 하나의 가짜 locator — 부른 것을 페이지의 calls 에 적습니다."""

    def __init__(
        self,
        page: FakeBrowserPage,
        selector: str,
        *,
        present: bool = True,
        enabled: bool = True,
        texts: tuple[str, ...] = (),
        wait_error: BaseException | None = None,
    ) -> None:
        self._page = page
        self._selector = selector
        self._present = present
        self._enabled = enabled
        self._texts = texts
        self._wait_error = wait_error

    @property
    def first(self) -> FakeLocator:
        return self

    def wait_for(self, *, state: str, timeout: int) -> None:
        self._page.calls.append(("wait_for", self._selector, state, timeout))
        if self._wait_error is not None:
            raise self._wait_error
        if not self._present:
            raise FakeTimeout(f"{self._selector}: {timeout}ms")

    def count(self) -> int:
        self._page.calls.append(("count", self._selector))
        return 1 if self._present else 0

    def scroll_into_view_if_needed(self, *, timeout: int) -> None:
        self._page.calls.append(("scroll", self._selector, timeout))

    def click(self, *, timeout: int) -> None:
        self._page.calls.append(("click", self._selector, timeout))

    def fill(self, text: str) -> None:
        self._page.calls.append(("fill", self._selector, text))

    def is_enabled(self) -> bool:
        self._page.calls.append(("is_enabled", self._selector))
        return self._enabled

    def all_inner_texts(self) -> list[str]:
        self._page.calls.append(("all_inner_texts", self._selector))
        return list(self._texts)


class FakeBrowserPage:
    """Playwright Page 가짜 — locators 에 없는 선택자는 화면에 없는 것으로 봅니다."""

    def __init__(self, locators: dict[str, dict[str, object]] | None = None) -> None:
        self.url = "https://www.youtube.com/watch?v=AAAAAAAAAAA"
        self.calls: list[tuple[object, ...]] = []
        self._locators = {
            selector: FakeLocator(self, selector, **options)
            for selector, options in (locators or {}).items()
        }

    def locator(self, selector: str) -> FakeLocator:
        found = self._locators.get(selector)
        return found if found is not None else FakeLocator(self, selector, present=False)

    def goto(self, url: str, **kwargs: object) -> None:
        self.calls.append(("goto", url, kwargs))

    def wait_for_timeout(self, ms: int) -> None:
        self.calls.append(("wait_for_timeout", ms))

    def screenshot(self, *, path: str) -> None:
        self.calls.append(("screenshot", path))

    def close(self) -> None:
        self.calls.append(("close",))


def full_page(**overrides: dict[str, object] | None) -> FakeBrowserPage:
    """댓글을 달 수 있는 화면. overrides 의 값이 None 이면 그 선택자를 화면에서 뺍니다."""
    locators: dict[str, dict[str, object]] = {
        SIGNED_IN: {},
        COMMENTS: {},
        COMMENT_PLACEHOLDER: {},
        COMMENT_INPUT: {},
        SUBMIT_BUTTON: {},
    }
    names = {
        "signed_in": SIGNED_IN,
        "comments": COMMENTS,
        "disabled_msg": COMMENTS_DISABLED_MSG,
        "placeholder": COMMENT_PLACEHOLDER,
        "input": COMMENT_INPUT,
        "submit": SUBMIT_BUTTON,
        "texts": COMMENT_TEXTS,
    }
    for name, options in overrides.items():
        if options is None:
            locators.pop(names[name], None)
        else:
            locators[names[name]] = options
    return FakeBrowserPage(locators)


class FakeContext:
    def __init__(self) -> None:
        self.pages: list[FakeBrowserPage] = []

    def new_page(self) -> FakeBrowserPage:
        page = FakeBrowserPage()
        self.pages.append(page)
        return page


class FakeBrowser:
    def __init__(self, contexts: list[FakeContext]) -> None:
        self.contexts = contexts
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


class FakePlaywright:
    def __init__(
        self, browser: FakeBrowser | None = None, error: BaseException | None = None
    ) -> None:
        self._browser = browser
        self._error = error
        self.connect_calls: list[str] = []
        self.stop_calls = 0
        self.chromium = types.SimpleNamespace(connect_over_cdp=self._connect_over_cdp)

    def _connect_over_cdp(self, url: str) -> FakeBrowser:
        self.connect_calls.append(url)
        if self._error is not None:
            raise self._error
        return self._browser

    def stop(self) -> None:
        self.stop_calls += 1


def fake_playwright_modules(playwright: FakePlaywright) -> dict[str, types.ModuleType]:
    api = types.ModuleType("playwright.sync_api")
    api.TimeoutError = FakeTimeout
    api.sync_playwright = lambda: types.SimpleNamespace(start=lambda: playwright)
    return {"playwright": types.ModuleType("playwright"), "playwright.sync_api": api}


class ChromeSessionTest(unittest.TestCase):
    URL = "http://127.0.0.1:9333"

    def new_page_error(self, modules: dict[str, object]) -> PageError:
        with mock.patch.dict(sys.modules, modules):
            with self.assertRaises(PageError) as caught:
                ChromeSession(self.URL).new_page()
        return caught.exception

    def test_playwright_missing(self) -> None:
        error = self.new_page_error({"playwright": None, "playwright.sync_api": None})
        self.assertEqual(error.reason, "playwright_missing")

    def test_connect_failure_is_chrome_unreachable_and_stops(self) -> None:
        playwright = FakePlaywright(error=ConnectionRefusedError("connect ECONNREFUSED"))
        error = self.new_page_error(fake_playwright_modules(playwright))
        self.assertEqual(error.reason, "chrome_unreachable")
        self.assertIn("ConnectionRefusedError", error.detail)
        self.assertEqual(playwright.stop_calls, 1)

    def test_no_contexts_is_chrome_unreachable(self) -> None:
        playwright = FakePlaywright(FakeBrowser([]))
        error = self.new_page_error(fake_playwright_modules(playwright))
        self.assertEqual(error.reason, "chrome_unreachable")
        self.assertEqual(playwright.stop_calls, 1)

    def test_attaches_to_default_context_once_and_only_disconnects(self) -> None:
        default, other = FakeContext(), FakeContext()
        browser = FakeBrowser([default, other])
        playwright = FakePlaywright(browser)
        with mock.patch.dict(sys.modules, fake_playwright_modules(playwright)):
            session = ChromeSession(self.URL)
            first = session.new_page()
            second = session.new_page()
            self.assertEqual(playwright.connect_calls, [self.URL])
            self.assertIsInstance(first, YouTubePage)
            self.assertIsInstance(second, YouTubePage)
            self.assertEqual(len(default.pages), 2)
            self.assertEqual(other.pages, [])
            # 주입된 시간 초과 종류가 페이지까지 갑니다 — 빈 화면은 login_required
            with self.assertRaises(PageError) as caught:
                first.prepare_comment(TEXT)
            self.assertEqual(caught.exception.reason, "login_required")
            session.close()
        self.assertEqual(playwright.stop_calls, 1)
        self.assertEqual(browser.close_calls, 0)


class YouTubePageTest(unittest.TestCase):
    def adapter(self, page: FakeBrowserPage) -> YouTubePage:
        return YouTubePage(page, FakeTimeout)

    def prepare_reason(self, page: FakeBrowserPage) -> str:
        with self.assertRaises(PageError) as caught:
            self.adapter(page).prepare_comment(TEXT)
        return caught.exception.reason

    def test_url_and_open(self) -> None:
        page = FakeBrowserPage()
        adapter = self.adapter(page)
        self.assertEqual(adapter.url, page.url)
        adapter.open("https://www.youtube.com/watch?v=AAAAAAAAAAA")
        self.assertEqual(
            page.calls,
            [
                (
                    "goto",
                    "https://www.youtube.com/watch?v=AAAAAAAAAAA",
                    {"wait_until": "domcontentloaded", "timeout": 30000},
                )
            ],
        )

    def test_prepare_missing_avatar_is_login_required(self) -> None:
        self.assertEqual(self.prepare_reason(full_page(signed_in=None)), "login_required")

    def test_prepare_missing_comments_section(self) -> None:
        self.assertEqual(self.prepare_reason(full_page(comments=None)), "comment_box_missing")

    def test_prepare_comments_disabled_message(self) -> None:
        page = full_page(placeholder=None, disabled_msg={})
        self.assertEqual(self.prepare_reason(page), "comments_disabled")

    def test_prepare_missing_placeholder_without_message(self) -> None:
        self.assertEqual(self.prepare_reason(full_page(placeholder=None)), "comment_box_missing")

    def test_prepare_missing_input(self) -> None:
        self.assertEqual(self.prepare_reason(full_page(input=None)), "comment_box_missing")

    def test_prepare_disabled_button(self) -> None:
        page = full_page(submit={"enabled": False})
        self.assertEqual(self.prepare_reason(page), "post_button_missing")

    def test_prepare_fills_exact_text(self) -> None:
        page = full_page()
        self.adapter(page).prepare_comment(TEXT)
        self.assertEqual(
            [call for call in page.calls if call[0] == "fill"], [("fill", COMMENT_INPUT, TEXT)]
        )
        self.assertIn(("click", COMMENT_PLACEHOLDER, 10000), page.calls)

    def assert_no_waiting(self, page: FakeBrowserPage) -> None:
        waits = [c for c in page.calls if c[0] in ("wait_for", "goto", "wait_for_timeout")]
        self.assertEqual(waits, [])

    def test_submit_absent_button_raises_without_click(self) -> None:
        page = full_page(submit=None)
        with self.assertRaises(PageError) as caught:
            self.adapter(page).submit()
        self.assertEqual(caught.exception.reason, "post_button_missing")
        self.assertEqual([c for c in page.calls if c[0] == "click"], [])
        self.assert_no_waiting(page)

    def test_submit_disabled_button_raises_without_click(self) -> None:
        page = full_page(submit={"enabled": False})
        with self.assertRaises(PageError) as caught:
            self.adapter(page).submit()
        self.assertEqual(caught.exception.reason, "post_button_missing")
        self.assertEqual([c for c in page.calls if c[0] == "click"], [])
        self.assert_no_waiting(page)

    def test_submit_clicks_once_without_waiting(self) -> None:
        page = full_page()
        self.adapter(page).submit()
        self.assertEqual(
            [c for c in page.calls if c[0] == "click"], [("click", SUBMIT_BUTTON, 3000)]
        )
        self.assert_no_waiting(page)

    def test_confirm_matches_whitespace_variant(self) -> None:
        shown = ("다른 사람 댓글", "  연락 텀이\n길어질 때  불안한 마음,  저도 겪어 봐서 알아요. ")
        page = full_page(texts={"texts": shown})
        self.assertTrue(self.adapter(page).confirm_posted(TEXT))

    def test_confirm_gives_up_after_polls(self) -> None:
        page = full_page(texts={"texts": ("다른 사람 댓글",)})
        self.assertFalse(self.adapter(page).confirm_posted(TEXT))
        waits = [c for c in page.calls if c[0] == "wait_for_timeout"]
        self.assertEqual(waits, [("wait_for_timeout", CONFIRM_POLL_MS)] * CONFIRM_POLLS)

    def test_confirm_rejects_longer_text_containing_ours(self) -> None:
        page = full_page(texts={"texts": (TEXT + " 그리고 덧붙인 말",)})
        self.assertFalse(self.adapter(page).confirm_posted(TEXT))

    def test_confirm_only_scans_first_confirm_scan_texts(self) -> None:
        page = full_page(texts={"texts": ("다른 사람 댓글",) * CONFIRM_SCAN + (TEXT,)})
        self.assertFalse(self.adapter(page).confirm_posted(TEXT))

    def test_present_lets_other_errors_propagate(self) -> None:
        page = full_page(
            signed_in={
                "wait_error": RuntimeError("Target page, context or browser has been closed")
            }
        )
        with self.assertRaises(RuntimeError):
            self.adapter(page).prepare_comment(TEXT)

    def test_screenshot_and_close_delegate(self) -> None:
        page = FakeBrowserPage()
        adapter = self.adapter(page)
        adapter.screenshot(Path("logs/screenshots/x.png"))
        adapter.close()
        self.assertEqual(
            page.calls, [("screenshot", str(Path("logs/screenshots/x.png"))), ("close",)]
        )


if __name__ == "__main__":
    unittest.main()
