"""로그 형식 — 사건 하나에 한 줄: `<KST ISO-8601 초> <EVENT> key=value …`.

값 안에 날 글자로 남는 것은 유니코드 범주 L · M · N · P · S 와 U+0020 뿐입니다. 그런 글자로만 되어
있고 공백 · `"` · `=` · `\\` 가 없는 값은 그대로, 나머지는 JSON 따옴표로 쓰며, 따옴표 안에서 그 밖의
글자(제어 · 서식 · 다른 공백 · 줄 경계 · 서로게이트 …)는 모두 \\uXXXX 로 씁니다. 그래서 로그 파일에는
날 제어 문자도 서로게이트도 없습니다. 로그를 읽는 단 하나의 방법은 read_log 입니다 — UTF-8 로 풀고
`\\n` 에서만 나눠 줄마다 parse_line 으로 정확히 되읽습니다.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import TextIO

KST = timezone(timedelta(hours=9), "KST")


class Event(str, Enum):
    START = "START"
    CYCLE = "CYCLE"
    DETECT = "DETECT"
    VIEWS = "VIEWS"
    CLASSIFY = "CLASSIFY"
    TRIGGER = "TRIGGER"
    COMMENT = "COMMENT"
    POST = "POST"
    SKIP = "SKIP"
    QUOTA = "QUOTA"
    ERROR = "ERROR"
    STOP = "STOP"


REQUIRED_FIELDS: dict[Event, tuple[str, ...]] = {
    Event.START: ("mode", "allowed", "interval_min"),
    Event.CYCLE: ("n",),
    Event.DETECT: ("video", "channel", "keyword", "title"),
    Event.VIEWS: ("video", "views", "prev", "delta"),
    Event.CLASSIFY: ("video", "verdict", "reason"),
    Event.TRIGGER: ("video", "verdict", "reason"),
    Event.COMMENT: ("video", "concern", "text"),
    Event.POST: ("video", "mode", "result", "reason"),
    Event.SKIP: ("video", "reason"),
    Event.QUOTA: ("used", "limit"),
    Event.ERROR: ("where", "reason"),
    Event.STOP: ("reason",),
}

_KEY_RE = re.compile(r"[a-z][a-z0-9_]*")
_BARE_RE = re.compile(r'[^\s"=\\]+')
_DECODER = json.JSONDecoder()
# 값 안에 날 글자로 남기는 유니코드 범주(첫 글자) — 글자 · 결합 표시 · 숫자 · 문장부호 · 기호. 이것과 U+0020
# 밖의 글자(제어 · 서식 · 다른 공백 · 줄 경계 · 사용자 정의 · 미할당 · 서로게이트)는 언제나 따옴표 안의
# \uXXXX 입니다. 막을 글자 대신 남길 글자를 적어, 아직 아무도 찾지 않은 글자도 바꿔 쓰는 쪽에 떨어집니다.
_RAW_CATEGORIES = frozenset("LMNPS")


def _stamp(at: datetime) -> str:
    if at.utcoffset() is None:
        raise ValueError("시간대가 없는 시각은 기록할 수 없습니다")
    return at.astimezone(KST).isoformat(timespec="seconds")


def _is_raw(char: str) -> bool:
    """값 안에 날 글자로 남겨도 되는 글자 — 범주 L · M · N · P · S 와 U+0020 (계약 7절)."""
    return char == " " or unicodedata.category(char)[0] in _RAW_CATEGORIES


def _render_str(value: str) -> str:
    if value != "-" and _BARE_RE.fullmatch(value) and all(map(_is_raw, value)):
        return value
    quoted = json.dumps(value, ensure_ascii=False)
    return "".join(char if _is_raw(char) else json.dumps(char)[1:-1] for char in quoted)


def _render(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Enum):
        return _render_str(str(value.value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, datetime):
        return _stamp(value)
    if isinstance(value, str):
        return _render_str(value)
    raise TypeError(f"로그에 쓸 수 없는 값의 종류입니다: {type(value).__name__}")


def format_line(at: datetime, event: Event, fields: Mapping[str, object]) -> str:
    """사건 한 줄을 만듭니다. 필요한 필드가 먼저(정해진 순서), 나머지는 키 이름 순."""
    event = Event(event)
    stamp = _stamp(at)
    for key in fields:
        if not isinstance(key, str) or not _KEY_RE.fullmatch(key):
            raise ValueError(f"필드 이름이 잘못되었습니다: {key!r}")
    required = REQUIRED_FIELDS[event]
    for key in required:
        if key not in fields:
            raise ValueError(f"{event.value} 에 필요한 필드가 없습니다: {key}")
    extras = sorted(key for key in fields if key not in required)
    tokens = [stamp, event.value]
    tokens.extend(f"{key}={_render(fields[key])}" for key in (*required, *extras))
    return " ".join(tokens)


def parse_line(line: str) -> tuple[datetime, Event, dict[str, str]]:
    """format_line 의 정확한 역. 값은 글자로 돌려줍니다. 형식이 틀리면 ValueError.
    이 규칙 전에 쓰인 줄(맨 값 속 날 제어 문자 등)도 읽습니다."""
    if line.endswith("\n"):
        line = line[:-1]
    stamp, sep, rest = line.partition(" ")
    if not sep:
        raise ValueError("로그 줄 형식이 아닙니다")
    at = datetime.fromisoformat(stamp)
    if at.utcoffset() is None:
        raise ValueError("로그 시각에 시간대가 없습니다")
    name, sep, rest = rest.partition(" ")
    try:
        event = Event(name)
    except ValueError:
        raise ValueError(f"모르는 사건입니다: {name!r}") from None
    fields: dict[str, str] = {}
    pos = 0
    while sep:
        match = _KEY_RE.match(rest, pos)
        if match is None or rest[match.end():match.end() + 1] != "=":
            raise ValueError(f"필드 형식이 잘못되었습니다: {rest[pos:]!r}")
        key = match.group()
        if key in fields:
            raise ValueError(f"필드가 두 번 나옵니다: {key}")
        start = match.end() + 1
        if rest.startswith('"', start):
            value, end = _DECODER.raw_decode(rest, start)
        else:
            end = rest.find(" ", start)
            end = len(rest) if end < 0 else end
            value = rest[start:end]
            if not _BARE_RE.fullmatch(value):
                raise ValueError(f"값 형식이 잘못되었습니다: {key}")
        fields[key] = value
        if end == len(rest):
            break
        if rest[end] != " ":
            raise ValueError(f"값 뒤에 공백이 없습니다: {key}")
        pos = end + 1
    for key in REQUIRED_FIELDS[event]:
        if key not in fields:
            raise ValueError(f"{event.value} 에 필요한 필드가 없습니다: {key}")
    return at, event, fields


def read_log(path: Path | str) -> list[tuple[datetime, Event, dict[str, str]]]:
    """로그 파일을 읽는 단 하나의 방법 — 로그 증명(Phase 7 · 8)은 이것으로 읽습니다.

    바이트를 UTF-8 로 엄격히 풀고 `\\n` 에서만 줄을 나눠, 빈 줄을 뺀 모든 줄을 parse_line 으로
    읽어 파일 순서대로 돌려줍니다. 잘못된 UTF-8 바이트 · 해석할 수 없는 줄 · 끝 `\\n` 이 없는
    마지막 줄(쓰기 중 끊긴 줄)은 건너뛰지 않고 `<n>번째 줄: …` ValueError 입니다. 파일을 열 수
    없으면 OSError 그대로입니다. 계약 7절.
    """
    data = Path(path).read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        number = data.count(b"\n", 0, exc.start) + 1
        raise ValueError(f"{number}번째 줄: UTF-8 이 아닌 바이트가 있습니다") from exc
    *lines, tail = text.split("\n")
    if tail:
        raise ValueError(f"{len(lines) + 1}번째 줄: 끝에 줄바꿈이 없습니다 (쓰기 중 끊긴 줄)")
    events: list[tuple[datetime, Event, dict[str, str]]] = []
    for number, line in enumerate(lines, start=1):
        if not line:
            continue
        try:
            events.append(parse_line(line))
        except ValueError as exc:
            raise ValueError(f"{number}번째 줄: {exc}") from exc
    return events


class Logbook:
    """로그 파일에 한 줄씩 덧붙이고, 같은 줄을 화면(echo)에도 냅니다."""

    def __init__(
        self, path: Path, clock: Callable[[], datetime], echo: TextIO | None = None
    ) -> None:
        self.path = Path(path)
        self._clock = clock
        self._echo = echo

    def write(self, event: Event, **fields: object) -> str:
        line = format_line(self._clock(), event, fields)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
        if self._echo is not None:
            self._echo.write(line + "\n")
            self._echo.flush()
        return line
