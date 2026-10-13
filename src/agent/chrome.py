"""크롬 쪽 — 전용 프로필 위치 검사와 켤 명령 안내.

크롬은 전용 프로필(`--user-data-dir` 를 기본 데이터 폴더가 아닌 곳으로)로 켜야 합니다 —
Chrome 136+ 는 기본 데이터 폴더에서 원격 디버깅 포트를 무시합니다. 프로필 위치는 저장소의
`chrome-profile/` 이거나 저장소 밖이어야 합니다(계약 8절).

check_profile_dir 는 **켤 때** 하는 검사이고, `python3 -m agent.chrome` CLI 가 부릅니다.
에이전트는 붙은 크롬의 프로필 위치를 실행 중에 확인하지 않습니다. CLI 는 위치를 검사하고
켤 명령을 보여 줄 뿐, 크롬을 직접 켜지 않습니다.

디버깅 포트가 열려 있는 동안 이 컴퓨터의 어떤 프로그램이든 로그인된 계정의 쿠키를 읽을 수
있습니다 — 전용 유튜브(브랜드) 계정으로 로그인하고, 쓰지 않을 때는 그 크롬을 닫습니다.
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

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR_NAME = "chrome-profile"
PORT_WARNING = (
    "주의: 이 포트가 열려 있는 동안 이 컴퓨터의 어떤 프로그램이든 로그인된 계정의 쿠키를 읽을 수 있습니다 — "
    "본 구글 계정이 아닌 전용 유튜브(브랜드) 계정으로 로그인하고, 에이전트를 쓰지 않을 때는 이 크롬을 닫으세요."
)


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


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
