"""허용 목록 가드 — 실제 게시를 정하는 유일한 함수 decide_post 가 여기 있습니다.

게시 버튼을 누르기 바로 직전에 decide_post 를 불러야 합니다. 허용 목록 밖의 영상은
언제나 테스트 모드이고, 이 판단을 건너뛰게 하는 설정 · 인자 · 환경 변수는 없습니다.
허용 목록 항목은 11자 영상 ID 로 바꿔 비교하며, 읽을 수 없는 항목은 어떤 영상과도
맞지 않습니다.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import parse_qs, urlsplit

from agent.models import VIDEO_ID_RE

_YOUTUBE_HOSTS = frozenset({"youtube.com", "www.youtube.com", "m.youtube.com"})


@dataclass(frozen=True)
class PostDecision:
    """게시 판단. live 가 거짓이면 테스트 모드(저장만 하고 게시하지 않음)입니다."""

    video_id: str | None
    live: bool
    reason: str

    @property
    def mode(self) -> str:
        return "live" if self.live else "test"


def video_id_from_ref(ref: str) -> str | None:
    """영상 ID 나 유튜브 주소에서 11자 영상 ID 를 꺼냅니다. 못 꺼내면 None."""
    text = ref.strip()
    if VIDEO_ID_RE.fullmatch(text):
        return text
    try:
        parts = urlsplit(text)
    except ValueError:
        return None
    if parts.scheme not in ("http", "https"):
        return None
    host = (parts.hostname or "").lower()
    segments = parts.path.split("/")
    if host == "youtu.be":
        candidate = segments[1] if len(segments) > 1 else ""
    elif host in _YOUTUBE_HOSTS and parts.path == "/watch":
        candidate = parse_qs(parts.query).get("v", [""])[0]
    elif host in _YOUTUBE_HOSTS and parts.path.startswith("/shorts/"):
        candidate = segments[2]
    else:
        return None
    return candidate if VIDEO_ID_RE.fullmatch(candidate) else None


def allowed_video_ids(allowed_videos: Iterable[str]) -> frozenset[str]:
    """허용 목록을 영상 ID 집합으로 바꿉니다. 읽을 수 없는 항목은 버립니다."""
    ids = (video_id_from_ref(entry) for entry in allowed_videos)
    return frozenset(video_id for video_id in ids if video_id is not None)


def decide_post(video_ref: str, allowed_videos: Iterable[str], dry_run: bool) -> PostDecision:
    """실제 게시 여부를 정합니다: 읽을 수 없는 영상 → 허용 목록 밖 → 테스트 모드 플래그 순."""
    video_id = video_id_from_ref(video_ref)
    if video_id is None:
        return PostDecision(None, False, "invalid_video")
    allowed = allowed_video_ids(allowed_videos)
    if video_id not in allowed:
        return PostDecision(video_id, False, "not_in_allowlist")
    if dry_run:
        return PostDecision(video_id, False, "dry_run")
    return PostDecision(video_id, True, "allowlisted")
