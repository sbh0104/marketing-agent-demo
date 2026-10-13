"""탐지 · 조회수 추적 — 한 사이클 = 검색, 그다음 추적 (계약 '탐지 · 조회수 추적' 절).

- 검색: 키워드마다(설정 순서, 중복 한 번) 최신순 검색. 다음 페이지는 그 페이지에
  nextPageToken 이 있고, 사이클 시작 때 저장소에 있던 영상이 없고, 그 키워드에서 받은 페이지가
  `MAX_PAGES_PER_KEYWORD` 보다 적을 때만 받습니다. 페이지 상한이 토큰을 남긴 채 키워드를 끝내면
  그 뒤 결과를 보지 못한 것이므로 `QUOTA … counter=pages` 줄을 남깁니다.
- 추적: 새 영상과 `trigger.max_age_hours` 안에 올라온 저장 영상 모두에 조회수 한 번씩. 새 영상은
  `DETECT` · `VIEWS`, 아는 영상은 표본을 하나 덧붙이고 `VIEWS`.
- 쿼터 가드가 막은 단계는 `QUOTA`, API 오류로 멈춘 단계는 `ERROR` 줄을 남깁니다 — 빈 사이클과
  막힌 사이클이 조용히 같아 보이지 않습니다. 검색이 막혀도 추적은 돕니다.
- 밖에서 온 글자의 외톨이 서로게이트는 U+FFFD 로 바꿉니다(HC1-2 R3). 영상 ID · 조회수 ·
  올린 시각은 허용한 모양(fullmatch)만 받고, 그 밖의 항목은 `SKIP` 으로 건너뜁니다.
- 저장소 쓰기 오류는 잡지 않고 run_loop 까지 올라갑니다 (계약 9절).
"""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from agent.config import Config
from agent.logbook import Event, Logbook
from agent.models import VIDEO_ID_RE, VideoRecord, ViewSample
from agent.store import Store
from agent.youtube import MAX_IDS_PER_CALL, QuotaExhausted, YouTubeClient, YouTubeError

MAX_PAGES_PER_KEYWORD = 3
_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")
_REPLACEMENT = chr(0xFFFD)
_COUNT_RE = re.compile(r"[0-9]{1,19}")
_PUBLISHED_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,9})?Z")


def _clean(text: str) -> str:
    return _SURROGATE_RE.sub(_REPLACEMENT, text)


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name}: 묶음이 아닙니다")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name}: 글자가 아닙니다")
    return _clean(value)


def _published(value: object) -> datetime:
    # UTC `Z` 모양만 — 다른 시간대 표기는 날짜 끝에서 Store.save 를 넘치게 할 수 있습니다 (계약 '탐지 · 조회수 추적' 절)
    if not isinstance(value, str) or not _PUBLISHED_RE.fullmatch(value):
        raise ValueError(f"snippet.publishedAt: UTC 'YYYY-MM-DDTHH:MM:SSZ' 모양이 아닙니다: {value!r:.40}")
    return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def _views(item: Mapping[str, object]) -> int:
    statistics = _mapping(item.get("statistics"), "statistics")
    value = statistics.get("viewCount")
    if not (isinstance(value, str) and _COUNT_RE.fullmatch(value)):
        raise ValueError(f"statistics.viewCount: 0 이상의 10진수 글자가 아닙니다: {value!r:.40}")
    return int(value)


def _new_record(
    video_id: str, keyword: str, item: Mapping[str, object], now: datetime
) -> VideoRecord:
    snippet = _mapping(item.get("snippet"), "snippet")
    return VideoRecord(
        video_id=video_id,
        channel_id=_string(snippet.get("channelId"), "snippet.channelId"),
        title=_string(snippet.get("title"), "snippet.title"),
        description=_string(snippet.get("description", ""), "snippet.description"),
        published_at=_published(snippet.get("publishedAt")),
        detected_at=now,
        keyword=keyword,
        view_history=[ViewSample(now, _views(item))],
    )


def _items_by_id(data: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    items = data.get("items", [])
    if not isinstance(items, list):
        raise YouTubeError("videos.list", "HTTP 200 items 가 목록이 아닙니다")
    return {
        item["id"]: item
        for item in items
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }


@dataclass(frozen=True)
class CycleReport:
    """한 사이클의 결과. held · truncated 가 "빈 사이클" 과 "막힌 사이클" 을 가릅니다.

    searches: 받은 검색 페이지 수 · detected: 새로 저장한 영상 ID(순서대로) · sampled: 조회수를
    남긴 영상 수 · truncated: 페이지 상한에서 끊긴 키워드 수(`QUOTA … counter=pages` 한 줄씩) ·
    held: 쿼터 가드가 호출을 막았는지(`QUOTA` 줄) · failed: `ERROR` 줄을 남겼는지.
    """

    searches: int
    detected: tuple[str, ...]
    sampled: int
    truncated: int
    held: bool
    failed: bool


@dataclass
class _Tally:
    searches: int = 0
    found: dict[str, str] = field(default_factory=dict)  # 새 ID → 처음 찾은 검색어
    detected: list[str] = field(default_factory=list)
    sampled: int = 0
    truncated: int = 0
    held: bool = False
    failed: bool = False

    def report(self) -> CycleReport:
        return CycleReport(
            searches=self.searches,
            detected=tuple(self.detected),
            sampled=self.sampled,
            truncated=self.truncated,
            held=self.held,
            failed=self.failed,
        )


class Watcher:
    """탐지 사이클 — `cycle(config)` 이 run_loop 의 사이클 자리에 맞습니다 (계약 9절 · '탐지 · 조회수 추적' 절)."""

    def __init__(
        self,
        store: Store,
        logbook: Logbook,
        client: YouTubeClient,
        clock: Callable[[], datetime],
    ) -> None:
        self._store = store
        self._logbook = logbook
        self._client = client
        self._clock = clock

    def cycle(self, config: Config) -> CycleReport:
        return self.run(config, self._clock())

    def run(self, config: Config, now: datetime) -> CycleReport:
        if now.utcoffset() is None:
            raise ValueError("now 에 시간대가 없습니다")
        window_start = now - timedelta(hours=config.trigger.max_age_hours)
        known = {r.video_id for r in self._store.records()}
        tally = _Tally()
        self._search(config, now, window_start, known, tally)
        self._track(config, now, window_start, tally)
        return tally.report()

    def _search(
        self,
        config: Config,
        now: datetime,
        window_start: datetime,
        known: set[str],
        tally: _Tally,
    ) -> None:
        for query in dict.fromkeys(_clean(keyword) for keyword in config.keywords):
            token: str | None = None
            for _ in range(MAX_PAGES_PER_KEYWORD):
                try:
                    data = self._client.search(query, window_start, token, now, config.limits)
                    tally.searches += 1
                    ids, token = self._page_ids(data, query)
                except QuotaExhausted as exc:
                    self._hold(exc, keyword=query)
                    tally.held = True
                    return
                except YouTubeError as exc:
                    self._fail(exc, keyword=query)
                    tally.failed = True
                    return
                for video_id in ids:
                    if video_id not in known:
                        tally.found.setdefault(video_id, query)
                if token is None or any(video_id in known for video_id in ids):
                    break
            else:
                # 페이지 상한이 토큰을 남긴 채 끝냄 — 정한 한도도 다른 한도처럼 남깁니다 (계약 '탐지 · 조회수 추적' 절)
                tally.truncated += 1
                self._logbook.write(Event.QUOTA, used=MAX_PAGES_PER_KEYWORD, limit=MAX_PAGES_PER_KEYWORD, call="search.list", counter="pages", keyword=query)

    def _page_ids(
        self, data: Mapping[str, object], query: str
    ) -> tuple[list[str], str | None]:
        items = data.get("items", [])
        if not isinstance(items, list):
            raise YouTubeError("search.list", "HTTP 200 items 가 목록이 아닙니다")
        ids: list[str] = []
        for item in items:
            ident = item.get("id") if isinstance(item, Mapping) else None
            raw = ident.get("videoId") if isinstance(ident, Mapping) else None
            if isinstance(raw, str) and VIDEO_ID_RE.fullmatch(raw):
                ids.append(raw)
                continue
            self._logbook.write(
                Event.SKIP,
                video=_clean(raw[:40]) if isinstance(raw, str) else None,
                reason="invalid_item",
                call="search.list",
                keyword=query,
            )
        token = data.get("nextPageToken")
        return ids, token if isinstance(token, str) and token else None

    def _track(
        self, config: Config, now: datetime, window_start: datetime, tally: _Tally
    ) -> None:
        queue = [
            *tally.found,
            *[r.video_id for r in self._store.records() if r.published_at > window_start],
        ]
        for start in range(0, len(queue), MAX_IDS_PER_CALL):
            batch = queue[start:start + MAX_IDS_PER_CALL]
            try:
                data = self._client.videos(batch, now, config.limits)
                items = _items_by_id(data)
            except QuotaExhausted as exc:
                self._hold(exc)
                tally.held = True
                return
            except YouTubeError as exc:
                self._fail(exc)
                tally.failed = True
                return
            for video_id in batch:
                self._record(video_id, items.get(video_id), now, tally)

    def _record(
        self,
        video_id: str,
        item: Mapping[str, object] | None,
        now: datetime,
        tally: _Tally,
    ) -> None:
        if item is None:
            self._logbook.write(
                Event.SKIP, video=video_id, reason="unavailable", call="videos.list"
            )
            return
        keyword = tally.found.get(video_id)
        try:
            if keyword is not None:
                record = _new_record(video_id, keyword, item, now)
            else:
                record = self._store.get(video_id)
                if record is None:
                    self._logbook.write(
                        Event.SKIP, video=video_id, reason="unavailable", call="videos.list"
                    )
                    return
                record.view_history.append(ViewSample(now, _views(item)))
        except ValueError as exc:
            self._logbook.write(
                Event.SKIP,
                video=video_id,
                reason="invalid_item",
                call="videos.list",
                detail=_clean(str(exc)),
            )
            return
        self._store.put(record)
        tally.sampled += 1
        views = record.view_history[-1].count
        prev = record.view_history[-2].count if len(record.view_history) > 1 else None
        if keyword is not None:
            tally.detected.append(video_id)
            self._logbook.write(
                Event.DETECT,
                video=video_id,
                channel=record.channel_id,
                keyword=keyword,
                title=record.title,
            )
        self._logbook.write(
            Event.VIEWS,
            video=video_id,
            views=views,
            prev=prev,
            delta=views - prev if prev is not None else None,
        )

    def _hold(self, exc: QuotaExhausted, **extra: object) -> None:
        self._logbook.write(Event.QUOTA, used=exc.used, limit=exc.limit, call=exc.call, counter=exc.counter, **extra)

    def _fail(self, exc: YouTubeError, **extra: object) -> None:
        self._logbook.write(Event.ERROR, where=exc.call, reason=_clean(exc.reason), **extra)
