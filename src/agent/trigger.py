"""트리거 판정 — 뜨기 직전인 영상인지 세 조건으로 정합니다 (계약의 '트리거 판정' 절).

조회수(min_views ~ max_views), 업로드 뒤 나이(max_age_hours 이내), 시간당 조회수
(min_views_per_hour 이상)를 모두 만족하면 대상(yes)입니다. 기준은 부를 때마다 받은
TriggerConfig 에서 읽고, 지금 시각도 인자로 받아 같은 입력이면 언제나 같은 판정입니다.
시각은 벽시계가 아니라 순간으로 비교합니다.
시간당 조회수는 시각이 다른 가장 늦은 두 기록으로 재며, 조회수가 줄었으면 재지 않습니다 —
음수 속도는 없습니다. 판정만 돌려주고 저장 · 로그는 부르는 쪽이 합니다.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from agent.config import TriggerConfig
from agent.models import Judgement, Verdict, VideoRecord, ViewSample

_MICROSECOND = timedelta(microseconds=1)
_US_PER_HOUR = 3_600_000_000


def _utc(moment: datetime) -> datetime:
    """같은 시간대 객체끼리도 벽시계가 아니라 순간으로 비교하도록 UTC 로 옮깁니다."""
    return moment.astimezone(timezone.utc)


def _latest_pair(history: Sequence[ViewSample]) -> tuple[ViewSample, ViewSample] | None:
    """(직전, 최신) — 시각이 다른 가장 늦은 두 기록. 목록 순서는 보지 않습니다."""
    ordered = sorted(history, key=lambda sample: (_utc(sample.at), sample.count))
    if not ordered:
        return None
    latest = ordered[-1]
    earlier = [sample for sample in ordered if _utc(sample.at) < _utc(latest.at)]
    if not earlier:
        return None
    return earlier[-1], latest


def _rate(previous: ViewSample, latest: ViewSample) -> float | None:
    """두 기록 사이의 시간당 조회수. 조회수가 줄었으면(삭제 · 비공개 · 정정) None."""
    gained = latest.count - previous.count
    if gained < 0:
        return None
    # 정수끼리 한 번만 나눠, 정확히 기준값인 속도가 반올림으로 흔들리지 않게 합니다.
    return gained * _US_PER_HOUR / ((_utc(latest.at) - _utc(previous.at)) // _MICROSECOND)


def judge_trigger(record: VideoRecord, config: TriggerConfig, now: datetime) -> Judgement:
    """지금 대상으로 볼지 — 정해진 차례대로 보고 처음 걸린 판정을 돌려줍니다. 기록은 바꾸지 않습니다."""
    if now.utcoffset() is None:
        raise ValueError("now 에 시간대가 없습니다")
    pair = _latest_pair(record.view_history)
    if pair is None:
        return Judgement(Verdict.HOLD, "too_few_samples", now)
    previous, latest = pair
    if latest.count < config.min_views:
        return Judgement(Verdict.NO, "views_below_min", now)
    if latest.count > config.max_views:
        return Judgement(Verdict.NO, "views_above_max", now)
    if _utc(record.published_at) > _utc(now):
        return Judgement(Verdict.HOLD, "published_in_future", now)
    if _utc(now) - _utc(record.published_at) > timedelta(hours=config.max_age_hours):
        return Judgement(Verdict.NO, "too_old", now)
    rate = _rate(previous, latest)
    if rate is None:
        return Judgement(Verdict.HOLD, "views_decreased", now)
    if rate < config.min_views_per_hour:
        return Judgement(Verdict.NO, "too_slow", now)
    return Judgement(Verdict.YES, "views_per_hour", now)
