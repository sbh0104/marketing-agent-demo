"""크롬 쪽 — 전용 프로필 위치 검사와 켤 명령 안내.

크롬은 전용 프로필(`--user-data-dir` 를 기본 데이터 폴더가 아닌 곳으로)로 켜야 합니다 —
Chrome 136+ 는 기본 데이터 폴더에서 원격 디버깅 포트를 무시합니다. 프로필 위치는 저장소의
`chrome-profile/` 이거나 저장소 밖이어야 합니다(계약 8절).

check_profile_dir 는 **켤 때** 하는 검사이고, `python3 -m agent.chrome` CLI 가 부릅니다.
에이전트는 붙은 크롬의 프로필 위치를 실행 중에 확인하지 않습니다. CLI 는 위치를 검사하고
켤 명령을 보여 줄 뿐, 크롬을 직접 켜지 않습니다.

디버깅 포트가 열려 있는 동안 이 컴퓨터의 어떤 프로그램이든 로그인된 계정의 쿠키를 읽을 수
있습니다 — 전용 유튜브(브랜드) 계정으로 로그인하고, 쓰지 않을 때는 그 크롬을 닫습니다.

ChromeSession 은 이미 켜진 크롬에 connect_over_cdp 로 붙고, Playwright 는 연결할 때에만
불러옵니다(테스트는 Playwright 없이 돕니다). 유튜브 선택자는 이 파일 위쪽의 상수들입니다 —
화면 구성이 바뀌면 거기를 고칩니다.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TextIO
from urllib.parse import urlsplit

from agent.config import ConfigError, load_config
from agent.poster import (
    CHROME_UNREACHABLE,
    COMMENT_BOX_MISSING,
    COMMENTS_DISABLED,
    LOGIN_REQUIRED,
    PLAYWRIGHT_MISSING,
    POST_BUTTON_MISSING,
    PageError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR_NAME = "chrome-profile"
PORT_WARNING = (
    "주의: 이 포트가 열려 있는 동안 이 컴퓨터의 어떤 프로그램이든 로그인된 계정의 쿠키를 읽을 수 있습니다 — "
    "본 구글 계정이 아닌 전용 유튜브(브랜드) 계정으로 로그인하고, 에이전트를 쓰지 않을 때는 이 크롬을 닫으세요."
)

# 유튜브 선택자 — 화면 구성이 바뀌면 여기를 고칩니다 (R8 사람 확인이 실제 화면과 맞춰 봄)
SIGNED_IN = "button#avatar-btn"
COMMENTS = "ytd-comments#comments"
COMMENTS_DISABLED_MSG = "ytd-comments#comments ytd-message-renderer"
COMMENT_PLACEHOLDER = "#simplebox-placeholder"
COMMENT_INPUT = "#contenteditable-root"
SUBMIT_BUTTON = "ytd-commentbox #submit-button button"
COMMENT_TEXTS = "ytd-comment-thread-renderer #content-text"

# 기다리는 시간(밀리초)과 게시 확인 횟수
NAV_TIMEOUT_MS = 30000
WAIT_MS = 10000
CLICK_TIMEOUT_MS = 3000
CONFIRM_POLLS = 30
CONFIRM_POLL_MS = 500
CONFIRM_SCAN = 20


class ChromeSetupError(ValueError):
    """크롬을 켤 준비가 안 됐을 때 — 프로필 위치나 디버깅 주소가 틀림."""


def default_user_data_dirs(platform: str, env: Mapping[str, str], home: Path) -> tuple[Path, ...]:
    """운영체제별 크롬 · 크로미움 기본 데이터 폴더."""
    if platform == "win32":
        base = Path(env["LOCALAPPDATA"]) if env.get("LOCALAPPDATA") else home / "AppData" / "Local"
        return (base / "Google" / "Chrome" / "User Data", base / "Chromium" / "User Data")
    if platform == "darwin":
        support = home / "Library" / "Application Support"
        return (support / "Google" / "Chrome", support / "Chromium")
    cfg = Path(env["XDG_CONFIG_HOME"]) if env.get("XDG_CONFIG_HOME") else home / ".config"
    return (cfg / "google-chrome", cfg / "chromium")


def _same_or_inside(path: Path, base: Path) -> bool:
    target = os.path.normcase(str(path))
    root = os.path.normcase(str(base))
    return target == root or target.startswith(root.rstrip(os.sep) + os.sep)


def check_profile_dir(
    profile_dir: str | Path, repo_root: Path, *, defaults: Iterable[str | Path]
) -> Path:
    """켤 때의 프로필 위치 검사 — 통과하면 실제 위치(심볼릭 링크를 따라간 절대 경로)를 돌려줍니다.

    크롬 기본 데이터 폴더(그 안 포함)와, 저장소 안이면서 chrome-profile/ 밖인 곳은
    ChromeSetupError 로 거부합니다. 상대 경로는 저장소 뿌리 기준입니다. 에이전트가 실행 중에
    붙은 크롬의 프로필을 확인하는 검사가 아닙니다.
    """
    path = Path(profile_dir).expanduser()
    if not path.is_absolute():
        path = Path(repo_root) / path
    path = path.resolve()
    for default in defaults:
        if _same_or_inside(path, Path(default).expanduser().resolve()):
            raise ChromeSetupError(
                "크롬 기본 데이터 폴더는 쓸 수 없습니다 — "
                f"Chrome 136+ 는 이 폴더에서 원격 디버깅 포트를 열지 않습니다: {path}"
            )
    repo = Path(repo_root).resolve()
    if _same_or_inside(path, repo) and not _same_or_inside(path, repo / PROFILE_DIR_NAME):
        raise ChromeSetupError(f"프로필은 저장소의 {PROFILE_DIR_NAME}/ 또는 저장소 밖에만 둡니다: {path}")
    return path


def debug_port(chrome_debug_url: str) -> int:
    """chrome_debug_url 의 포트 번호."""
    try:
        port = urlsplit(chrome_debug_url).port
    except ValueError as exc:
        raise ChromeSetupError(
            f"chrome_debug_url 의 포트를 읽을 수 없습니다: {chrome_debug_url}"
        ) from exc
    if port is None:
        raise ChromeSetupError(f"chrome_debug_url 에 포트가 없습니다: {chrome_debug_url}")
    return port


def launch_command(chrome: str, profile_dir: Path, port: int) -> list[str]:
    """전용 프로필과 디버깅 포트로 크롬을 켜는 명령(인자 목록)."""
    return [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]


def default_chrome_executable(platform: str) -> str:
    """운영체제별 크롬 실행 파일의 흔한 위치."""
    if platform == "win32":
        return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return "google-chrome"


def main(
    argv: list[str] | None = None,
    *,
    repo_root: Path = REPO_ROOT,
    platform: str = sys.platform,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    """프로필 위치를 검사하고 크롬을 켤 명령을 보여 줍니다 — 크롬을 직접 켜지는 않습니다."""
    out = out if out is not None else sys.stdout
    err = err if err is not None else sys.stderr
    parser = argparse.ArgumentParser(prog="python3 -m agent.chrome")
    parser.add_argument("--profile", default=PROFILE_DIR_NAME)
    parser.add_argument("--chrome", default=None)
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args(argv)
    try:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = Path(repo_root) / config_path
        config = load_config(config_path)
        port = debug_port(config.chrome_debug_url)
        defaults = default_user_data_dirs(platform, env or os.environ, home or Path.home())
        profile = check_profile_dir(args.profile, repo_root, defaults=defaults)
    except (ConfigError, ChromeSetupError, OSError) as exc:
        print(f"크롬 실행 준비 실패: {exc}", file=err)
        return 2
    command = launch_command(args.chrome or default_chrome_executable(platform), profile, port)
    shown = subprocess.list2cmdline(command) if platform == "win32" else shlex.join(command)
    print(
        "아래 명령으로 크롬을 켠 뒤, 그 창에서 유튜브에 한 번 로그인하세요 (이 도구는 크롬을 켜지 않습니다):",
        file=out,
    )
    print(shown, file=out)
    print(PORT_WARNING, file=out)
    return 0


def _normalize(text: str) -> str:
    return " ".join(text.split())


class YouTubePage:
    """유튜브 영상 탭 하나 — agent.poster.CommentPage 를 따릅니다.

    timeout_error 로 받은 시간 초과 종류만 "화면에 없음"으로 보고, 다른 예외는 그대로 올립니다.
    """

    def __init__(self, page: object, timeout_error: type[BaseException]) -> None:
        self._page = page
        self._timeout_error = timeout_error

    @property
    def url(self) -> str:
        return self._page.url

    def open(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)

    def prepare_comment(self, text: str) -> None:
        """로그인 · 댓글 칸 · 입력 · 버튼을 차례로 보고, 빠진 것이 있으면 그 원인으로 멈춥니다."""
        if not self._present(SIGNED_IN, WAIT_MS):
            raise PageError(LOGIN_REQUIRED, SIGNED_IN)
        if not self._present(COMMENTS, WAIT_MS):
            raise PageError(COMMENT_BOX_MISSING, COMMENTS)
        self._page.locator(COMMENTS).first.scroll_into_view_if_needed(timeout=WAIT_MS)
        if not self._present(COMMENT_PLACEHOLDER, WAIT_MS):
            if self._page.locator(COMMENTS_DISABLED_MSG).count() > 0:
                raise PageError(COMMENTS_DISABLED, COMMENTS_DISABLED_MSG)
            raise PageError(COMMENT_BOX_MISSING, COMMENT_PLACEHOLDER)
        self._page.locator(COMMENT_PLACEHOLDER).first.click(timeout=WAIT_MS)
        if not self._present(COMMENT_INPUT, WAIT_MS):
            raise PageError(COMMENT_BOX_MISSING, COMMENT_INPUT)
        self._page.locator(COMMENT_INPUT).first.fill(text)
        if (
            not self._present(SUBMIT_BUTTON, WAIT_MS)
            or not self._page.locator(SUBMIT_BUTTON).first.is_enabled()
        ):
            raise PageError(POST_BUTTON_MISSING, SUBMIT_BUTTON)

    def submit(self) -> None:
        """게시 버튼을 누릅니다 — 기다림도 이동도 없이. 누르는 중의 예외는 그대로 올립니다."""
        button = self._page.locator(SUBMIT_BUTTON)
        if button.count() == 0 or not button.first.is_enabled():
            raise PageError(POST_BUTTON_MISSING, SUBMIT_BUTTON)
        button.first.click(timeout=CLICK_TIMEOUT_MS)

    def confirm_posted(self, text: str) -> bool:
        """맨 위 댓글들 가운데 같은 글(공백만 다른 것 포함)이 보이면 True."""
        for _ in range(CONFIRM_POLLS):
            texts = self._page.locator(COMMENT_TEXTS).all_inner_texts()
            if any(_normalize(t) == _normalize(text) for t in texts[:CONFIRM_SCAN]):
                return True
            self._page.wait_for_timeout(CONFIRM_POLL_MS)
        return False

    def screenshot(self, path: Path) -> None:
        self._page.screenshot(path=str(path))

    def close(self) -> None:
        self._page.close()

    def _present(self, selector: str, timeout_ms: int) -> bool:
        try:
            self._page.locator(selector).first.wait_for(state="attached", timeout=timeout_ms)
        except self._timeout_error:
            return False
        return True


class ChromeSession:
    """켜져 있는 크롬에 붙는 연결 — 영상마다 새 탭을 엽니다. close() 는 연결만 끊습니다."""

    def __init__(self, debug_url: str) -> None:
        self._debug_url = debug_url
        self._playwright = None
        self._context = None
        self._timeout_error = None

    def new_page(self) -> YouTubePage:
        if self._context is None:
            self._connect()
        return YouTubePage(self._context.new_page(), self._timeout_error)

    def _connect(self) -> None:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeout, sync_playwright
        except ImportError as exc:
            raise PageError(PLAYWRIGHT_MISSING, "pip install -r requirements.txt") from exc
        playwright = sync_playwright().start()
        try:
            browser = playwright.chromium.connect_over_cdp(self._debug_url)
        except Exception as exc:
            playwright.stop()
            raise PageError(CHROME_UNREACHABLE, f"{type(exc).__name__}: {exc}"[:200]) from exc
        if not browser.contexts:
            playwright.stop()
            raise PageError(CHROME_UNREACHABLE, "기본 컨텍스트가 없습니다")
        self._playwright = playwright
        self._context = browser.contexts[0]  # 기본 컨텍스트 — 로그인 쿠키가 여기 있습니다
        self._timeout_error = PlaywrightTimeout

    def close(self) -> None:
        """연결만 끊습니다 — browser.close() 를 부르지 않으므로 크롬과 사용자 탭은 그대로입니다."""
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
            self._context = None
            self._timeout_error = None


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
