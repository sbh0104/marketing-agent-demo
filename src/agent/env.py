"""비밀 값 읽기 — 저장소 뿌리의 .env 파일과 환경 변수 (계약 8절 · '탐지 · 조회수 추적' 절).

.env 는 `이름=값` 줄, `#` 로 시작하는 주석 줄, 빈 줄만 받습니다. 값 둘레의 같은 따옴표 한 쌍
(`'…'` 또는 `"…"`)은 떼어 내고, 값 뒤의 `#` 은 주석이 아니라 값의 일부입니다. 형식이 틀린 줄이나
두 번 나온 이름은 EnvError 이고, 메시지는 파일과 줄 번호를 말하지만 값은 **절대** 담지 않습니다.
파일이 없으면 빈 것으로 읽습니다. 비어 있지 않은 환경 변수가 .env 보다 앞섭니다.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path


class EnvError(Exception):
    """.env 를 읽을 수 없거나 필요한 비밀 값이 비었을 때 — 메시지에 값은 없습니다."""


_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def read_env_file(path: Path | str) -> dict[str, str]:
    """.env 를 `{이름: 값}` 으로 읽습니다. 윈도우 메모장이 붙이는 BOM 은 떼어 냅니다."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise EnvError(f".env 를 읽을 수 없습니다: {path}") from exc
    except UnicodeDecodeError as exc:
        raise EnvError(f".env 가 UTF-8 이 아닙니다 (UTF-8 로 다시 저장하세요): {path}") from exc
    values: dict[str, str] = {}
    for n, raw in enumerate(text.split("\n"), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        name = name.strip()
        if not sep or not _NAME_RE.fullmatch(name):
            raise EnvError(f"{path} {n}번째 줄: 이름=값 형식이 아닙니다")
        if name in values:
            raise EnvError(f"{path} {n}번째 줄: 이름이 두 번 나옵니다: {name}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] in "'\"":
            value = value[1:-1]
        values[name] = value
    return values


def require_secret(name: str, env_path: Path | str, environ: Mapping[str, str]) -> str:
    """비밀 값 하나 — 환경 변수, 없으면 .env. 둘 다 비었으면 EnvError."""
    value = environ.get(name, "")
    if value:
        return value
    value = read_env_file(env_path).get(name, "")
    if value:
        return value
    raise EnvError(f"{name} 가 비어 있습니다 — {env_path} 에 {name}=<키> 를 적으세요")
