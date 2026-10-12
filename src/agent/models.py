"""영상 기록 모양 — 영상 한 개를 탐지부터 게시 시도까지 담는 기록.

모든 시각은 시간대가 있어야 하고, JSON 으로는 UTC ISO 8601 글자로 나갑니다.
from_dict 는 모르는 키나 빠진 필수 키가 있으면 ValueError 를 냅니다.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")


class Verdict(str, Enum):
    YES = "yes"
    NO = "no"
    HOLD = "hold"


MODES = ("live", "test")
RESULTS = {"live": ("reserved", "posted", "failed"), "test": ("saved",)}


def _aware(value: object, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{name}: 시각이어야 합니다")
    if value.utcoffset() is None:
        raise ValueError(f"{name}: 시간대가 없는 시각입니다")
    return value


def _text(value: object, name: str, *, non_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name}: 글자여야 합니다")
    if non_empty and not value:
        raise ValueError(f"{name}: 비어 있으면 안 됩니다")
    return value


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: object, name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{name}: ISO 8601 시각 글자여야 합니다")
    return _aware(datetime.fromisoformat(value), name)


def _keys(
    data: object, required: tuple[str, ...], optional: tuple[str, ...], name: str
) -> Mapping[str, object]:
    if not isinstance(data, Mapping):
        raise ValueError(f"{name}: '키: 값' 묶음이어야 합니다")
    allowed = required + optional
    unknown = [str(key) for key in data if key not in allowed]
    if unknown:
        raise ValueError(f"{name}: 알 수 없는 키입니다: {', '.join(unknown)}")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{name}: 필요한 키가 없습니다: {', '.join(missing)}")
    return data


def _items(value: object, kind: type, name: str) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name}: 목록이어야 합니다")
    for item in value:
        if not isinstance(item, kind):
            raise ValueError(f"{name}: {kind.__name__} 만 담을 수 있습니다")


def _optional(value: object, kind: type, name: str) -> None:
    if value is not None and not isinstance(value, kind):
        raise ValueError(f"{name}: {kind.__name__} 이거나 None 이어야 합니다")


def _list_of(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{name}: 목록이어야 합니다")
    return value


@dataclass
class ViewSample:
    """어느 시각에 본 조회수 한 번."""

    at: datetime
    count: int

    def __post_init__(self) -> None:
        _aware(self.at, "ViewSample.at")
        if isinstance(self.count, bool) or not isinstance(self.count, int) or self.count < 0:
            raise ValueError("ViewSample.count: 0 이상의 정수여야 합니다")

    def to_dict(self) -> dict[str, object]:
        return {"at": _iso(self.at), "count": self.count}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ViewSample":
        data = _keys(data, ("at", "count"), (), "ViewSample")
        return cls(_parse_time(data["at"], "ViewSample.at"), data["count"])


@dataclass
class Judgement:
    """판정 한 번 — 주제 판별 · 트리거 · 댓글 자체 점검에 씁니다."""

    verdict: Verdict
    reason: str
    at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.verdict, Verdict):
            raise ValueError("Judgement.verdict: Verdict 값이어야 합니다")
        _text(self.reason, "Judgement.reason")
        _aware(self.at, "Judgement.at")

    def to_dict(self) -> dict[str, object]:
        return {"verdict": self.verdict.value, "reason": self.reason, "at": _iso(self.at)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "Judgement":
        data = _keys(data, ("verdict", "reason", "at"), (), "Judgement")
        return cls(
            Verdict(data["verdict"]),
            data["reason"],
            _parse_time(data["at"], "Judgement.at"),
        )


@dataclass
class CommentDraft:
    """작성한 댓글 — 짚은 고민과 본문, 자체 점검 결과."""

    concern: str
    text: str
    at: datetime
    self_check: Judgement | None = None

    def __post_init__(self) -> None:
        _text(self.concern, "CommentDraft.concern")
        _text(self.text, "CommentDraft.text")
        _aware(self.at, "CommentDraft.at")
        _optional(self.self_check, Judgement, "CommentDraft.self_check")

    def to_dict(self) -> dict[str, object]:
        return {
            "concern": self.concern,
            "text": self.text,
            "at": _iso(self.at),
            "self_check": self.self_check.to_dict() if self.self_check is not None else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CommentDraft":
        data = _keys(data, ("concern", "text", "at"), ("self_check",), "CommentDraft")
        self_check = data.get("self_check")
        return cls(
            data["concern"],
            data["text"],
            _parse_time(data["at"], "CommentDraft.at"),
            Judgement.from_dict(self_check) if self_check is not None else None,
        )


@dataclass
class PostAttempt:
    """게시 시도 한 번.

    live: reserved(클릭 전 예약, 결과 모름) → posted | failed.  test: saved.
    reason 은 실패 원인이나 PostDecision.reason, screenshot 은 저장소 기준 상대 경로입니다.
    """

    at: datetime
    mode: str
    result: str
    reason: str = ""
    screenshot: str | None = None

    def __post_init__(self) -> None:
        _aware(self.at, "PostAttempt.at")
        if self.mode not in MODES:
            raise ValueError(f"PostAttempt.mode: {MODES} 중 하나여야 합니다")
        if self.result not in RESULTS[self.mode]:
            raise ValueError(
                f"PostAttempt.result: {self.mode} 에서는 {RESULTS[self.mode]} 중 하나여야 합니다"
            )
        _text(self.reason, "PostAttempt.reason")
        if self.screenshot is not None:
            _text(self.screenshot, "PostAttempt.screenshot")

    def to_dict(self) -> dict[str, object]:
        return {
            "at": _iso(self.at),
            "mode": self.mode,
            "result": self.result,
            "reason": self.reason,
            "screenshot": self.screenshot,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "PostAttempt":
        data = _keys(data, ("at", "mode", "result"), ("reason", "screenshot"), "PostAttempt")
        return cls(
            _parse_time(data["at"], "PostAttempt.at"),
            data["mode"],
            data["result"],
            data.get("reason", ""),
            data.get("screenshot"),
        )


_RECORD_REQUIRED = (
    "video_id",
    "channel_id",
    "title",
    "description",
    "published_at",
    "detected_at",
    "keyword",
)
_RECORD_OPTIONAL = ("view_history", "classification", "trigger", "comment", "attempts")


@dataclass
class VideoRecord:
    """영상 한 개의 기록. 게시 시도(attempts)는 저장소만 바꿉니다."""

    video_id: str
    channel_id: str
    title: str
    description: str
    published_at: datetime
    detected_at: datetime
    keyword: str
    view_history: list[ViewSample] = field(default_factory=list)
    classification: Judgement | None = None
    trigger: Judgement | None = None
    comment: CommentDraft | None = None
    attempts: list[PostAttempt] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.video_id, str) or not VIDEO_ID_RE.fullmatch(self.video_id):
            raise ValueError(f"VideoRecord.video_id: 11자 영상 ID 가 아닙니다: {self.video_id!r}")
        _text(self.channel_id, "VideoRecord.channel_id", non_empty=True)
        _text(self.title, "VideoRecord.title")
        _text(self.description, "VideoRecord.description")
        _aware(self.published_at, "VideoRecord.published_at")
        _aware(self.detected_at, "VideoRecord.detected_at")
        _text(self.keyword, "VideoRecord.keyword")
        _items(self.view_history, ViewSample, "VideoRecord.view_history")
        _optional(self.classification, Judgement, "VideoRecord.classification")
        _optional(self.trigger, Judgement, "VideoRecord.trigger")
        _optional(self.comment, CommentDraft, "VideoRecord.comment")
        _items(self.attempts, PostAttempt, "VideoRecord.attempts")

    def to_dict(self) -> dict[str, object]:
        return {
            "video_id": self.video_id,
            "channel_id": self.channel_id,
            "title": self.title,
            "description": self.description,
            "published_at": _iso(self.published_at),
            "detected_at": _iso(self.detected_at),
            "keyword": self.keyword,
            "view_history": [sample.to_dict() for sample in self.view_history],
            "classification": _dump(self.classification),
            "trigger": _dump(self.trigger),
            "comment": _dump(self.comment),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "VideoRecord":
        data = _keys(data, _RECORD_REQUIRED, _RECORD_OPTIONAL, "VideoRecord")
        classification = data.get("classification")
        trigger = data.get("trigger")
        comment = data.get("comment")
        return cls(
            video_id=data["video_id"],
            channel_id=data["channel_id"],
            title=data["title"],
            description=data["description"],
            published_at=_parse_time(data["published_at"], "VideoRecord.published_at"),
            detected_at=_parse_time(data["detected_at"], "VideoRecord.detected_at"),
            keyword=data["keyword"],
            view_history=[
                ViewSample.from_dict(item)
                for item in _list_of(data.get("view_history", []), "VideoRecord.view_history")
            ],
            classification=(
                Judgement.from_dict(classification) if classification is not None else None
            ),
            trigger=Judgement.from_dict(trigger) if trigger is not None else None,
            comment=CommentDraft.from_dict(comment) if comment is not None else None,
            attempts=[
                PostAttempt.from_dict(item)
                for item in _list_of(data.get("attempts", []), "VideoRecord.attempts")
            ],
        )


def _dump(value: Judgement | CommentDraft | None) -> dict[str, object] | None:
    return value.to_dict() if value is not None else None
