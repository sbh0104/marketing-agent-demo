"""설정 계약 — config.yaml 을 읽고 엄격하게 검사합니다.

모든 키가 필요하고, 모르는 키는 오류이며, 타입은 정확해야 합니다. 그래서 YAML 1.1 이
몰래 바꾸는 값(`no`/`yes` → bool, 날짜, 따옴표 없는 숫자 ID)도 조용히 지나가지 않고
오류가 됩니다.
"""
from __future__ import annotations

import collections.abc
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml


class ConfigError(Exception):
    """설정 파일을 쓸 수 없을 때 — 메시지에 줄 번호나 점으로 이은 키 경로가 들어갑니다."""

    def __init__(self, message: str, line: int | None = None) -> None:
        self.message = message
        self.line = line
        super().__init__(f"{line}번째 줄: {message}" if line is not None else message)


@dataclass(frozen=True)
class TriggerConfig:
    min_views: int
    max_views: int
    max_age_hours: float
    min_views_per_hour: float


@dataclass(frozen=True)
class LimitsConfig:
    daily_max_comments: int
    channel_cooldown_hours: float
    daily_max_searches: int


@dataclass(frozen=True)
class CommentConfig:
    min_chars: int
    max_chars: int


@dataclass(frozen=True)
class Config:
    topic: str
    keywords: tuple[str, ...]
    poll_interval_min: int
    trigger: TriggerConfig
    limits: LimitsConfig
    comment: CommentConfig
    chrome_debug_url: str
    allowed_videos: tuple[str, ...]


class _StrictLoader(yaml.SafeLoader):
    """같은 키가 두 번 나오면 줄 번호와 함께 거부하는 SafeLoader."""


def _construct_mapping(loader: _StrictLoader, node: yaml.MappingNode) -> dict[object, object]:
    loader.flatten_mapping(node)
    seen: set[object] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, collections.abc.Hashable):
            raise ConfigError("키 형식이 잘못되었습니다", key_node.start_mark.line + 1)
        if key in seen:
            raise ConfigError(f"키가 두 번 나옵니다: {key}", key_node.start_mark.line + 1)
        seen.add(key)
    return loader.construct_mapping(node, deep=True)


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def parse_yaml(text: str) -> dict[str, object]:
    """YAML 글을 최상위 '키: 값' 묶음으로 읽습니다. 문법 오류는 ConfigError 가 됩니다.

    값을 만들다 나는 ValueError · RecursionError 등은 그대로 올라가며, load_config 가
    ConfigError 로 바꿉니다.
    """
    try:
        data = yaml.load(text, Loader=_StrictLoader)
    except yaml.MarkedYAMLError as exc:
        line = exc.problem_mark.line + 1 if exc.problem_mark else None
        raise ConfigError(f"YAML 문법 오류: {exc.problem}", line) from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML 문법 오류: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("최상위는 '키: 값' 형식이어야 합니다")
    return data


_TOP_KEYS = (
    "topic",
    "keywords",
    "poll_interval_min",
    "trigger",
    "limits",
    "comment",
    "chrome_debug_url",
    "allowed_videos",
)
_SECTION_KEYS = {
    "trigger": ("min_views", "max_views", "max_age_hours", "min_views_per_hour"),
    "limits": ("daily_max_comments", "channel_cooldown_hours", "daily_max_searches"),
    "comment": ("min_chars", "max_chars"),
}


def _check_keys(data: Mapping[object, object], allowed: tuple[str, ...], prefix: str) -> None:
    for key in data:
        if key not in allowed:
            raise ConfigError(f"알 수 없는 설정입니다: {prefix}{key}")
    for key in allowed:
        if key not in data:
            raise ConfigError(f"필수 설정이 없습니다: {prefix}{key}")


def _section(data: Mapping[str, object], name: str) -> Mapping[object, object]:
    value = data[name]
    if not isinstance(value, Mapping):
        raise ConfigError(f"'키: 값' 묶음이어야 합니다: {name}")
    _check_keys(value, _SECTION_KEYS[name], f"{name}.")
    return value


def _int(value: object, path: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"정수여야 합니다: {path}")
    if value < minimum:
        raise ConfigError(f"{minimum} 이상이어야 합니다: {path}")
    return value


def _number(value: object, path: str, minimum: float, *, inclusive: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"숫자여야 합니다: {path}")
    number = float(value)
    if inclusive and not number >= minimum:
        raise ConfigError(f"{minimum:g} 이상이어야 합니다: {path}")
    if not inclusive and not number > minimum:
        raise ConfigError(f"{minimum:g} 보다 커야 합니다: {path}")
    return number


def _text(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"비어 있지 않은 글자여야 합니다: {path}")
    return value


def config_from_mapping(data: Mapping[str, object]) -> Config:
    """읽은 묶음을 검사해 Config 로 바꿉니다. 메시지는 점으로 이은 키 경로를 말합니다."""
    _check_keys(data, _TOP_KEYS, "")

    keywords = data["keywords"]
    if not isinstance(keywords, list) or not keywords:
        raise ConfigError("검색어 목록에 하나 이상이 필요합니다: keywords")
    keyword_items = tuple(_text(item, f"keywords[{i}]") for i, item in enumerate(keywords))

    trigger = _section(data, "trigger")
    min_views = _int(trigger["min_views"], "trigger.min_views", 0)
    trigger_config = TriggerConfig(
        min_views=min_views,
        max_views=_int(trigger["max_views"], "trigger.max_views", min_views),
        max_age_hours=_number(
            trigger["max_age_hours"], "trigger.max_age_hours", 0, inclusive=False
        ),
        min_views_per_hour=_number(
            trigger["min_views_per_hour"], "trigger.min_views_per_hour", 0
        ),
    )

    limits = _section(data, "limits")
    limits_config = LimitsConfig(
        daily_max_comments=_int(limits["daily_max_comments"], "limits.daily_max_comments", 0),
        channel_cooldown_hours=_number(
            limits["channel_cooldown_hours"], "limits.channel_cooldown_hours", 0
        ),
        daily_max_searches=_int(limits["daily_max_searches"], "limits.daily_max_searches", 0),
    )

    comment = _section(data, "comment")
    min_chars = _int(comment["min_chars"], "comment.min_chars", 1)
    comment_config = CommentConfig(
        min_chars=min_chars,
        max_chars=_int(comment["max_chars"], "comment.max_chars", min_chars),
    )

    url = data["chrome_debug_url"]
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise ConfigError("http:// 또는 https:// 로 시작해야 합니다: chrome_debug_url")

    allowed = data["allowed_videos"]
    if allowed is None:
        allowed_items: tuple[str, ...] = ()
    elif isinstance(allowed, list):
        for i, item in enumerate(allowed):
            if not isinstance(item, str):
                raise ConfigError(f"글자여야 합니다 (따옴표로 감싸세요): allowed_videos[{i}]")
        allowed_items = tuple(allowed)
    else:
        raise ConfigError("영상 목록이어야 합니다: allowed_videos")

    return Config(
        topic=_text(data["topic"], "topic"),
        keywords=keyword_items,
        poll_interval_min=_int(data["poll_interval_min"], "poll_interval_min", 1),
        trigger=trigger_config,
        limits=limits_config,
        comment=comment_config,
        chrome_debug_url=url,
        allowed_videos=allowed_items,
    )


def load_config(path: Path | str) -> Config:
    """설정 파일을 읽어 검사합니다. 윈도우 메모장이 붙이는 BOM 은 떼어 냅니다.

    run_loop 가 이전 설정을 유지하려면 읽기 중 나는 오류가 모두 ConfigError 여야 합니다 —
    UTF-8 이 아닌 저장(메모장의 ANSI·Unicode), 날짜 모양의 틀린 값(`2026-02-30` → ValueError),
    4300자를 넘는 정수(ValueError), 실수로 바꿀 수 없는 큰 정수(OverflowError), 아주 깊은
    중첩(RecursionError) 등 그 밖의 모든 Exception 이 ConfigError 가 됩니다.
    KeyboardInterrupt 같은 BaseException 은 그대로 올라갑니다.
    """
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ConfigError(f"설정 파일을 읽을 수 없습니다: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ConfigError(f"설정 파일이 UTF-8 이 아닙니다 (UTF-8 로 다시 저장하세요): {path}") from exc
    try:
        return config_from_mapping(parse_yaml(text))
    except ConfigError:
        raise
    except Exception as exc:
        raise ConfigError(f"설정 값을 읽을 수 없습니다 ({type(exc).__name__}: {exc}): {path}") from exc
