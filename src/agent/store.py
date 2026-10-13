"""영상 기록 저장소 — data/videos.json 한 파일.

영상당 댓글 1개, 최근 24시간 게시 상한, 같은 채널 대기 시간을 모두 이 저장소와
호출자가 넘긴 now 로만 계산합니다. 숨은 시계가 없으므로 같은 입력이면 같은 결과입니다.

게시 시도 기록은 저장소만 바꿉니다. 실제 게시는 클릭 *전에* reserve_live 로 예약하고
클릭 뒤 resolve_live 로 확정합니다. 테스트 모드 저장은 save_test 입니다. put 은 시도
기록이 저장된 것과 다른 기록을 거부합니다. 확정되지 않은 예약(클릭 뒤 중단)은 게시로
셉니다 — 그래서 에이전트를 중간에 멈춰도 같은 영상에 두 번째 댓글이 달리지 않습니다.

파일이 깨졌거나 버전이 다르면 StoreError 를 냅니다. 중복 방지 기록이 지워지므로
절대로 초기화하지 않습니다.
"""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from agent.config import LimitsConfig
from agent.models import PostAttempt, VideoRecord

SCHEMA_VERSION = 1
COUNTED_RESULTS = ("posted", "reserved")  # 성공 + 결과를 모르는 예약(중단된 게시)


class StoreError(Exception):
    """저장소 파일을 믿을 수 없을 때 — 파일은 그대로 두고 멈춥니다."""


@dataclass(frozen=True)
class PostCheck:
    """게시 가능 여부. reason 은 ok · duplicate_video · daily_cap · channel_cooldown 중 하나."""

    allowed: bool
    reason: str


def _is_duplicate(record: VideoRecord, live: bool) -> bool:
    if live:
        return any(a.mode == "live" for a in record.attempts)
    return bool(record.attempts)


class Store:
    """data/videos.json 을 읽고 쓰는 저장소. 파일이 없으면 첫 변경 때 만듭니다."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._videos: dict[str, VideoRecord] = {}
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StoreError(f"저장소 파일이 올바른 JSON 이 아닙니다: {self.path}: {exc}") from exc
        if not isinstance(data, dict):
            raise StoreError(f"저장소 파일의 최상위가 객체가 아닙니다: {self.path}")
        if data.get("schema_version") != SCHEMA_VERSION:
            raise StoreError(
                f"저장소 버전이 다릅니다 (기대 {SCHEMA_VERSION}, 실제 "
                f"{data.get('schema_version')!r}): {self.path}"
            )
        videos = data.get("videos")
        if not isinstance(videos, dict):
            raise StoreError(f"저장소 파일에 videos 객체가 없습니다: {self.path}")
        for video_id, raw in videos.items():
            try:
                record = VideoRecord.from_dict(raw)
            except ValueError as exc:
                raise StoreError(f"영상 기록을 읽을 수 없습니다 ({video_id}): {exc}: {self.path}") from exc
            if record.video_id != video_id:
                raise StoreError(
                    f"영상 기록의 키와 video_id 가 다릅니다 ({video_id} ≠ {record.video_id}): "
                    f"{self.path}"
                )
            self._videos[video_id] = record

    def get(self, video_id: str) -> VideoRecord | None:
        """저장된 기록의 사본. 사본을 바꿔도 저장소는 바뀌지 않습니다."""
        record = self._videos.get(video_id)
        return copy.deepcopy(record) if record is not None else None

    def records(self) -> list[VideoRecord]:
        """모든 기록의 사본 — (detected_at, video_id) 순."""
        ordered = sorted(self._videos.values(), key=lambda rec: (rec.detected_at, rec.video_id))
        return [copy.deepcopy(record) for record in ordered]

    def comments(self) -> list[str]:
        """작성한 댓글 본문 — (comment.at, video_id) 순. 같은 댓글 반복을 막는 데 씁니다."""
        drafted = [rec for rec in self._videos.values() if rec.comment is not None]
        drafted.sort(key=lambda rec: (rec.comment.at, rec.video_id))
        return [rec.comment.text for rec in drafted]

    def put(self, record: VideoRecord) -> None:
        """기록을 넣거나 바꿉니다. 게시 시도(attempts)는 바꿀 수 없습니다."""
        current = self._videos.get(record.video_id)
        current_attempts = current.attempts if current is not None else []
        if record.attempts != current_attempts:
            raise ValueError("게시 시도 기록은 put 으로 바꿀 수 없습니다 — reserve_live / resolve_live / save_test 를 쓰세요")
        self._videos[record.video_id] = copy.deepcopy(record)
        self.save()

    def reserve_live(self, video_id: str, now: datetime) -> None:
        """클릭 *전에* 실제 게시를 예약합니다. 이 호출이 오류를 내면 클릭하면 안 됩니다."""
        record = self._require(video_id)
        if any(att.mode == "live" for att in record.attempts):
            raise ValueError("이미 실제 게시를 시도한 영상입니다")
        record.attempts.append(PostAttempt(now, "live", "reserved"))
        self.save()

    def resolve_live(
        self,
        video_id: str,
        result: str,
        now: datetime,
        reason: str = "",
        screenshot: str | None = None,
    ) -> None:
        """클릭 뒤 예약을 posted 또는 failed 로 확정합니다."""
        if result not in ("posted", "failed"):
            raise ValueError(f"확정 결과는 posted 또는 failed 여야 합니다: {result!r}")
        record = self._require(video_id)
        if not record.attempts or record.attempts[-1].result != "reserved":
            raise ValueError("확정할 게시 예약이 없습니다")
        record.attempts[-1] = PostAttempt(now, "live", result, reason, screenshot)
        self.save()

    def save_test(self, video_id: str, now: datetime, reason: str) -> None:
        """테스트 모드 저장 — 게시하지 않고 시도만 남깁니다."""
        record = self._require(video_id)
        record.attempts.append(PostAttempt(now, "test", "saved", reason))
        self.save()

    def _require(self, video_id: str) -> VideoRecord:
        record = self._videos.get(video_id)
        if record is None:
            raise ValueError("저장소에 없는 영상입니다")
        return record

    def save(self) -> None:
        """임시 파일에 쓴 뒤 바꿔 끼웁니다. 같은 기록이면 언제나 같은 바이트입니다."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        videos = {video_id: record.to_dict() for video_id, record in self._videos.items()}
        text = json.dumps(
            {"schema_version": SCHEMA_VERSION, "videos": videos},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, self.path)

    def check_post(
        self, video_id: str, channel_id: str, now: datetime, limits: LimitsConfig, live: bool
    ) -> PostCheck:
        """게시해도 되는지 — 중복 영상, 최근 24시간 상한, 채널 대기 순으로 봅니다."""
        if now.utcoffset() is None:
            raise ValueError("now 에 시간대가 없습니다")
        record = self._videos.get(video_id)
        if record is not None and _is_duplicate(record, live):
            return PostCheck(False, "duplicate_video")
        counted = [(rec.channel_id, att.at) for rec in self._videos.values() for att in rec.attempts if att.result in COUNTED_RESULTS]
        day_start = now - timedelta(hours=24)
        recent = [at for _, at in counted if at > day_start]
        if len(recent) >= limits.daily_max_comments:
            return PostCheck(False, "daily_cap")
        cooldown_start = now - timedelta(hours=limits.channel_cooldown_hours)
        if any(channel == channel_id and at > cooldown_start for channel, at in counted):
            return PostCheck(False, "channel_cooldown")
        return PostCheck(True, "ok")
