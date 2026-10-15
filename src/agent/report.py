"""결과 화면 — 사이클마다 다시 쓰는 정적 HTML 한 장을 저장소 기록과 로그 줄로만 그립니다.

화면은 저장소와 로그(read_log 로 읽은 줄)를 읽기만 하고 판단 · 게시 · 저장소를 바꾸지 않습니다.
로그의 이유 칸과 단계 이름은 정해 둔 이름표로만 옮기고 원문은 한 글자도 옮기지 않습니다 — 정해 둔
코드와 같거나 정해 둔 머리말로 시작하지 않으면 "기타 — 로그 참고" 입니다. 제목 · 판별 이유 · 고민 ·
댓글 같은 바깥 글은 모두 HTML 이스케이프를 거친 글자로만 들어가고, 영상 링크는 코드가 영상 ID 로
새로 만듭니다. 외부 스크립트 · 글꼴 · 스타일 파일은 불러오지 않습니다.
계약 '결과 화면 — report.py (Phase 7D)' 절.
"""
from __future__ import annotations

import html
import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from agent.logbook import KST, Event
from agent.models import VideoRecord
from agent.poster import DRY_RUN, NO_COMMENT, WATCH_URL
from agent.trigger import views_per_hour
from agent.writer import NO_CONCERN, NO_SCENE

LogLine = tuple[datetime, Event, dict[str, str]]

OTHER = "기타 — 로그 참고"

# 이유 코드 → 이름표 — 이유 글이 이 키와 정확히 같을 때만
REASON_LABELS: dict[str, str] = {
    "channel_cooldown": "같은 채널 대기 중",
    "daily_cap": "하루 상한에 닿음",
    "duplicate_video": "이미 처리한 영상",
    "not_in_allowlist": "허용 목록 밖이라 게시하지 않음",
    "invalid_video": "영상 주소를 읽을 수 없음",
    DRY_RUN: "테스트 실행 — 저장만",
    NO_COMMENT: "댓글 없음",
    "config_rejected": "설정 거절로 저장만",
    "unavailable": "영상을 볼 수 없음",
}
# 이유 머리말 → 이름표 — 이유 글이 이 머리말로 시작할 때, 앞에서부터 처음 맞는 것
REASON_PREFIXES: tuple[tuple[str, str], ...] = (
    (NO_SCENE, "작성 건너뜀 — 짚을 장면 없음"),
    (NO_CONCERN, "작성 건너뜀 — 연애 고민 없음"),
    ("검사 두 번 탈락", "검사 두 번 탈락"),
    ("claude 호출 실패", "AI 호출 오류 (Claude)"),
    ("jev 검사 호출 실패", "AI 호출 오류 (jev 검사)"),
    ("jev 검사 응답 이상", "AI 응답 이상 (jev 검사)"),
)
# ERROR 줄의 where= → 이름표 — video= 를 다는 단계만, 정확히 같을 때만
WHERE_LABELS: dict[str, str] = {
    "classify": "판별 단계 오류",
    "run.classify": "판별 단계 오류",
    "run.trigger": "타이밍 단계 오류",
    "commentThreads.list": "인기 댓글을 받지 못함",
    "writer.claude": "AI 호출 오류 (Claude)",
    "writer.jev": "AI 호출 오류 (jev 검사)",
    "run.write": "작성 단계 오류",
    "poster": "게시 단계 오류",
    "run.post": "게시 단계 오류",
}


def reason_label(reason: str) -> str:
    """이유 글의 이름표 — 정해 둔 코드와 같거나 정해 둔 머리말로 시작하면 그 이름표, 아니면 OTHER.

    받은 글은 돌려주지 않습니다 — 머리말 뒤의 세부 · 초안 인용 · 오류 원문은 화면에 가지 않습니다.
    """
    label = REASON_LABELS.get(reason)
    if label is not None:
        return label
    for prefix, label in REASON_PREFIXES:
        if reason.startswith(prefix):
            return label
    return OTHER


def where_label(where: str) -> str:
    """ERROR 줄 where= 의 이름표 — 정해 둔 단계와 정확히 같을 때만, 아니면 OTHER."""
    return WHERE_LABELS.get(where, OTHER)
