"""설정 계약 — config.yaml 을 읽고 엄격하게 검사합니다.

모든 키가 필요하고, 모르는 키는 오류이며, 타입은 정확해야 합니다. 그래서 YAML 1.1 이 글자
자리에 몰래 바꿔 넣는 값(`no`/`yes` → bool, 날짜, 따옴표 없는 숫자 ID)은 조용히 지나가지 않고
오류가 됩니다. 숫자 자리의 YAML 1.1 숫자 표기(`017` → 15, `1:30` → 90)는 그대로 읽고 범위만
검사합니다. 숫자는 유한값만 받고 키마다 상한이 있습니다 — 계약 2절.
"""
from __future__ import annotations

import collections.abc
import math
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
class ClassifierConfig:
    model: str
    noul_yes_min: float
    noul_no_max: float
    choice_min_confidence: float
    on_topic_reasons: tuple[str, ...]
    off_topic_reasons: tuple[str, ...]


@dataclass(frozen=True)
class Config:
    topic: str
    keywords: tuple[str, ...]
    poll_interval_min: int
    trigger: TriggerConfig
    limits: LimitsConfig
    comment: CommentConfig
    classifier: ClassifierConfig
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
    "classifier",
    "chrome_debug_url",
    "allowed_videos",
)
_SECTION_KEYS = {
    "trigger": ("min_views", "max_views", "max_age_hours", "min_views_per_hour"),
    "limits": ("daily_max_comments", "channel_cooldown_hours", "daily_max_searches"),
    "comment": ("min_chars", "max_chars"),
    "classifier": (
        "model",
        "noul_yes_min",
        "noul_no_max",
        "choice_min_confidence",
        "on_topic_reasons",
        "off_topic_reasons",
    ),
}
# 시간 키의 상한 — 100 × 365 × 24 시간(약 100년, 주기 대기의 상한과 같은 크기). 이 안의 값은
# now − timedelta(hours=…) 가 날짜 범위를 벗어나지 않습니다(2026년 기준 약 1800만 시간부터 OverflowError).
_MAX_HOURS = 876_000.0
# 시간당 조회수 하한의 상한 — 실제 영상이 닿지 않는 값. 숫자 키는 모두 상한을 둡니다.
_MAX_VIEWS_PER_HOUR = 1_000_000_000.0
# 이유 보기 수 · 이름 길이 상한 — 50개 × 40자면 가장 긴 질문이 1만 바이트를 넘지 않아 state 에 2만 2천 바이트 이상이 남습니다(계약 '주제 판별' 절).
_MAX_REASONS = 50
_MAX_REASON_CHARS = 40


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


def _number(
    value: object, path: str, minimum: float, maximum: float, *, inclusive: bool = True
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"숫자여야 합니다: {path}")
    number = float(value)
    if not math.isfinite(number):
        raise ConfigError(f"유한한 숫자여야 합니다: {path}")
    if inclusive and not number >= minimum:
        raise ConfigError(f"{minimum:g} 이상이어야 합니다: {path}")
    if not inclusive and not number > minimum:
        raise ConfigError(f"{minimum:g} 보다 커야 합니다: {path}")
    if not number <= maximum:
        raise ConfigError(f"{maximum:.0f} 이하여야 합니다: {path}")
    return number


def _text(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"비어 있지 않은 글자여야 합니다: {path}")
    return value


def _reasons(value: object, path: str, seen: set[str]) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError(f"보기가 하나 이상 필요합니다: {path}")
    names: list[str] = []
    for i, item in enumerate(value):
        name = _text(item, f"{path}[{i}]")
        if len(name) > _MAX_REASON_CHARS:
            raise ConfigError(f"{_MAX_REASON_CHARS}자 이하여야 합니다: {path}[{i}]")
        if name in seen:
            raise ConfigError(f"보기 이름이 겹칩니다: {path}[{i}]")
        seen.add(name)
        names.append(name)
    return tuple(names)


def _classifier(data: Mapping[str, object]) -> ClassifierConfig:
    section = _section(data, "classifier")
    model = _text(section["model"], "classifier.model")
    noul_yes_min = _number(
        section["noul_yes_min"], "classifier.noul_yes_min", 0.5, 1.0, inclusive=False
    )
    noul_no_max = _number(section["noul_no_max"], "classifier.noul_no_max", 0, 1.0)
    if not noul_no_max < noul_yes_min:
        raise ConfigError("noul_yes_min 보다 작아야 합니다: classifier.noul_no_max")
    choice_min_confidence = _number(
        section["choice_min_confidence"], "classifier.choice_min_confidence", 0, 1.0
    )
    seen: set[str] = set()
    on_topic_reasons = _reasons(
        section["on_topic_reasons"], "classifier.on_topic_reasons", seen
    )
    off_topic_reasons = _reasons(
        section["off_topic_reasons"], "classifier.off_topic_reasons", seen
    )
    if len(on_topic_reasons) + len(off_topic_reasons) > _MAX_REASONS:
        raise ConfigError(f"보기는 모두 {_MAX_REASONS}개 이하여야 합니다: classifier")
    return ClassifierConfig(
        model=model,
        noul_yes_min=noul_yes_min,
        noul_no_max=noul_no_max,
        choice_min_confidence=choice_min_confidence,
        on_topic_reasons=on_topic_reasons,
        off_topic_reasons=off_topic_reasons,
    )


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
            trigger["max_age_hours"], "trigger.max_age_hours", 0, _MAX_HOURS, inclusive=False
        ),
        min_views_per_hour=_number(
            trigger["min_views_per_hour"], "trigger.min_views_per_hour", 0, _MAX_VIEWS_PER_HOUR
        ),
    )

    limits = _section(data, "limits")
    limits_config = LimitsConfig(
        daily_max_comments=_int(limits["daily_max_comments"], "limits.daily_max_comments", 0),
        channel_cooldown_hours=_number(
            limits["channel_cooldown_hours"], "limits.channel_cooldown_hours", 0, _MAX_HOURS
        ),
        daily_max_searches=_int(limits["daily_max_searches"], "limits.daily_max_searches", 0),
    )

    comment = _section(data, "comment")
    min_chars = _int(comment["min_chars"], "comment.min_chars", 1)
    comment_config = CommentConfig(
        min_chars=min_chars,
        max_chars=_int(comment["max_chars"], "comment.max_chars", min_chars),
    )
    classifier_config = _classifier(data)

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
        classifier=classifier_config,
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
