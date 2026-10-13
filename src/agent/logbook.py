"""로그 형식 — 사건 하나에 한 줄: `<KST ISO-8601 초> <EVENT> key=value …`.

공백 · `"` · `=` · `\\` 가 없는 값은 그대로, 나머지는 JSON 따옴표로 씁니다. 따옴표 안에서는
str.splitlines() 가 줄 경계로 세는 글자(U+0085 · U+2028 · U+2029 포함)를 모두 이스케이프하므로,
여러 줄짜리 댓글도 줄 경계를 숨긴 영상 제목도 한 줄에 남고, parse_line 으로 정확히 되읽을 수
있습니다.
"""
from __future__ import annotations

import json
import re
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
# str.splitlines() 가 줄 경계로 세는 글자 — 따옴표 값 안에서 모두 \uXXXX 로 씁니다. 0x20 미만은
# json.dumps 가 이미 바꾸므로 실제로 바뀌는 것은 U+0085 · U+2028 · U+2029 입니다.
_LINE_BREAKS = "\n\v\f\r\x1c\x1d\x1e\x85\u2028\u2029"
_LINE_BREAK_ESCAPES = {ord(char): f"\\u{ord(char):04x}" for char in _LINE_BREAKS}


def _stamp(at: datetime) -> str:
    if at.utcoffset() is None:
        raise ValueError("시간대가 없는 시각은 기록할 수 없습니다")
    return at.astimezone(KST).isoformat(timespec="seconds")


def _render_str(value: str) -> str:
    if value != "-" and _BARE_RE.fullmatch(value):
        return value
    return json.dumps(value, ensure_ascii=False).translate(_LINE_BREAK_ESCAPES)


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
    """format_line 의 정확한 역. 값은 글자로 돌려줍니다. 형식이 틀리면 ValueError."""
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
