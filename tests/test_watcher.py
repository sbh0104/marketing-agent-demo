"""탐지 · 조회수 추적 테스트 — 가짜 API 로 한 사이클을 돌립니다 (네트워크 없음)."""
from __future__ import annotations

import dataclasses
import json
import tempfile
import unittest
import urllib.parse
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.config import ClassifierConfig, CommentConfig, Config, LimitsConfig, TriggerConfig
from agent.logbook import Event, Logbook, parse_line
from agent.models import VideoRecord, ViewSample
from agent.store import Store
from agent.watcher import CycleReport, Watcher
from agent.youtube import QuotaLedger, Usage, YouTubeClient

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)
PUBLISHED = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)
A = "aaaaaaaaaaa"
B = "bbbbbbbbbbb"
C = "ccccccccccc"
K = "kkkkkkkkkkk"

CONFIG = Config(
    topic="연애",
    keywords=("연애",),
    poll_interval_min=120,
    trigger=TriggerConfig(1000, 5000, 12.0, 150.0),
    limits=LimitsConfig(10, 24.0, 90),
    comment=CommentConfig(40, 120, "claude-sonnet-5-5", 0.7),
    classifier=ClassifierConfig("jev-latest", 0.8, 0.2, 0.5, ("연애 고민 상담",), ("연애와 관계없음",)),
    chrome_debug_url="http://localhost:9222",
    allowed_videos=(),
)

Fields = dict[str, str]


def with_cap(searches: int) -> Config:
    return dataclasses.replace(CONFIG, limits=LimitsConfig(10, 24.0, searches))


def with_keywords(*keywords: str) -> Config:
    return dataclasses.replace(CONFIG, keywords=keywords)


def search_page(ids: list[object], token: str | None = None) -> dict[str, object]:
    page: dict[str, object] = {
        "kind": "youtube#searchListResponse",
        "items": [{"id": {"kind": "youtube#video", "videoId": video_id}} for video_id in ids],
    }
    if token is not None:
        page["nextPageToken"] = token
    return page


def video_item(
    video_id: str,
    views: int,
    title: str = "연락 텀 때문에 불안한 썸",
    published: str = "2026-10-12T10:00:00Z",
    channel: str = "UC1",
) -> dict[str, object]:
    return {
        "id": video_id,
        "snippet": {
            "channelId": channel,
            "title": title,
            "description": "설명",
            "publishedAt": published,
        },
        "statistics": {"viewCount": str(views)},
    }


def google_error(status: int) -> dict[str, object]:
    reason = "quotaExceeded" if status == 403 else "backendError"
    return {"error": {"code": status, "errors": [{"reason": reason}]}}


class FakeApi:
    """URL 경로 끝(search · videos)으로 나눠 답하는 가짜 YouTube.

    pages[(q, pageToken)] 은 검색 한 페이지(또는 (상태, 본문) 짝), videos[id] 는 영상 정보,
    status[끝] 은 그 끝의 모든 호출을 오류 상태로, payload[끝] 은 그 끝의 모든 본문을 바꿉니다.
    endless=True 면 검색마다 새 ID 두 개와 다음 페이지 토큰을, videos 는 묻는 ID 모두를 답합니다.
    본문은 ASCII JSON 이라 외톨이 서로게이트는 Google 처럼 \\udXXX 이스케이프로 갑니다.
    """

    def __init__(self, endless: bool = False) -> None:
        self.pages: dict[tuple[str, str | None], object] = {}
        self.videos: dict[str, object] = {}
        self.status: dict[str, int] = {}
        self.payload: dict[str, object] = {}
        self.calls: list[tuple[str, dict[str, str]]] = []
        self.endless = endless
        self._served = 0

    def __call__(self, url: str, timeout: float) -> tuple[int, bytes]:
        parts = urllib.parse.urlsplit(url)
        endpoint = parts.path.rsplit("/", 1)[-1]
        query = dict(urllib.parse.parse_qsl(parts.query))
        self.calls.append((endpoint, query))
        if endpoint in self.status:
            status, payload = self.status[endpoint], google_error(self.status[endpoint])
        elif endpoint in self.payload:
            status, payload = 200, self.payload[endpoint]
        elif endpoint == "search":
            status, payload = self._search(query)
        else:
            status, payload = self._videos(query)
        return status, json.dumps(payload).encode("ascii")

    def _search(self, query: dict[str, str]) -> tuple[int, object]:
        if self.endless:
            self._served += 1
            k = self._served
            return 200, search_page([f"n{2 * k - 1:010d}", f"n{2 * k:010d}"], f"P{k}")
        entry = self.pages.get((query["q"], query.get("pageToken")), search_page([]))
        if isinstance(entry, tuple):
            return entry
        return 200, entry

    def _videos(self, query: dict[str, str]) -> tuple[int, object]:
        ids = query["id"].split(",")
        if self.endless:
            return 200, {"items": [video_item(video_id, 1000) for video_id in ids]}
        return 200, {"items": [self.videos[video_id] for video_id in ids if video_id in self.videos]}

    def searches(self) -> list[tuple[str, str | None]]:
        return [(q["q"], q.get("pageToken")) for endpoint, q in self.calls if endpoint == "search"]

    def video_batches(self) -> list[list[str]]:
        return [q["id"].split(",") for endpoint, q in self.calls if endpoint == "videos"]


class WatcherCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.reset("main")

    def reset(self, name: str, endless: bool = False) -> None:
        """subTest 마다 새 저장소 · 로그 · 쿼터 기록 · 가짜 API."""
        base = self.root / name
        self.store_path = base / "data" / "videos.json"
        self.quota_path = base / "data" / "quota.json"
        self.log_path = base / "logs" / "agent.log"
        self.api = FakeApi(endless)
        self.store = Store(self.store_path)

    def watcher(self, clock: Callable[[], datetime] = lambda: NOW) -> Watcher:
        logbook = Logbook(self.log_path, clock)
        client = YouTubeClient("test-key", QuotaLedger(self.quota_path), self.api)
        return Watcher(self.store, logbook, client, clock)

    def run_cycle(self, config: Config = CONFIG) -> CycleReport:
        return self.watcher().run(config, NOW)

    def raw_lines(self) -> list[str]:
        if not self.log_path.exists():
            return []
        return self.log_path.read_text(encoding="utf-8").splitlines()

    def log_lines(self) -> list[tuple[datetime, Event, Fields]]:
        return [parse_line(line) for line in self.raw_lines()]

    def events(self) -> list[tuple[Event, Fields]]:
        return [(event, fields) for _, event, fields in self.log_lines()]

    def event_names(self) -> list[Event]:
        return [event for _, event, _ in self.log_lines()]

    def seed(self, video_id: str, published: datetime = NOW - 2 * HOUR, views: int = 1000) -> None:
        self.store.put(
            VideoRecord(
                video_id=video_id,
                channel_id="UC9",
                title="이전 제목",
                description="",
                published_at=published,
                detected_at=NOW - HOUR,
                keyword="연애",
                view_history=[ViewSample(NOW - HOUR, views)],
            )
        )

    def seed_quota(self, searches: int, at: datetime) -> None:
        calls = [{"at": at.isoformat(), "call": "search.list", "units": 100}] * searches
        self.quota_path.parent.mkdir(parents=True, exist_ok=True)
        self.quota_path.write_text(
            json.dumps({"calls": calls, "schema_version": 1}), encoding="utf-8"
        )

    def counts(self, video_id: str) -> list[int]:
        record = self.store.get(video_id)
        assert record is not None
        return [sample.count for sample in record.view_history]


def quota(used: int, limit: int, call: str, counter: str, **extra: str) -> tuple[Event, Fields]:
    fields = {"used": str(used), "limit": str(limit), "call": call, "counter": counter}
    fields.update(extra)
    return Event.QUOTA, fields


def views(video_id: str, count: int, prev: int | None = None) -> tuple[Event, Fields]:
    return Event.VIEWS, {
        "video": video_id,
        "views": str(count),
        "prev": "-" if prev is None else str(prev),
        "delta": "-" if prev is None else str(count - prev),
    }


def detect(video_id: str, title: str = "연락 텀 때문에 불안한 썸") -> tuple[Event, Fields]:
    return Event.DETECT, {"video": video_id, "channel": "UC1", "keyword": "연애", "title": title}


def skip(video: str, reason: str, call: str, **extra: str) -> tuple[Event, Fields]:
    fields = {"video": video, "reason": reason, "call": call}
    fields.update(extra)
    return Event.SKIP, fields


class DetectTest(WatcherCase):
    def test_new_video_is_stored_with_its_first_view_sample(self) -> None:
        self.api.pages[("연애", None)] = search_page([A])
        self.api.videos[A] = video_item(A, 1200)
        report = self.run_cycle()
        expected = VideoRecord(
            video_id=A,
            channel_id="UC1",
            title="연락 텀 때문에 불안한 썸",
            description="설명",
            published_at=PUBLISHED,
            detected_at=NOW,
            keyword="연애",
            view_history=[ViewSample(NOW, 1200)],
        )
        self.assertEqual(self.store.get(A), expected)
        self.assertEqual(Store(self.store_path).get(A), expected)
        self.assertEqual(self.events(), [detect(A), views(A, 1200)])
        self.assertEqual(self.api.video_batches(), [[A]])
        self.assertEqual(
            report,
            CycleReport(
                searches=1, detected=(A,), sampled=1, truncated=0, held=False, failed=False
            ),
        )

    def test_known_video_gets_one_more_sample_and_keeps_its_attempts(self) -> None:
        self.seed(K, views=1000)
        self.store.save_test(K, NOW - HOUR / 2, "dry_run")
        self.api.pages[("연애", None)] = search_page([K])
        self.api.videos[K] = video_item(K, 1450, title="바뀐 제목")
        report = self.run_cycle()
        record = self.store.get(K)
        assert record is not None
        self.assertEqual(record.view_history, [ViewSample(NOW - HOUR, 1000), ViewSample(NOW, 1450)])
        self.assertEqual(record.title, "이전 제목")
        self.assertEqual([(a.mode, a.result) for a in record.attempts], [("test", "saved")])
        self.assertEqual(self.events(), [views(K, 1450, prev=1000)])
        self.assertEqual(report, CycleReport(1, (), 1, 0, False, False))

    def test_only_videos_inside_the_age_window_are_tracked(self) -> None:
        outside, inside = "ooooooooooo", "iiiiiiiiiii"
        self.seed(outside, published=NOW - 13 * HOUR)
        self.seed(inside, published=NOW - 11 * HOUR)
        self.api.videos[outside] = video_item(outside, 2000)
        self.api.videos[inside] = video_item(inside, 2000)
        self.run_cycle()
        self.assertEqual(self.api.video_batches(), [[inside]])
        self.assertEqual(self.counts(outside), [1000])
        self.assertEqual(self.counts(inside), [1000, 2000])
        self.assertEqual(self.api.searches(), [("연애", None)])
        query = self.api.calls[0][1]
        self.assertEqual(query["publishedAfter"], "2026-10-12T00:00:00Z")

    def test_video_found_by_two_keywords_keeps_the_first_keyword(self) -> None:
        self.api.pages[("연애", None)] = search_page([A])
        self.api.pages[("썸", None)] = search_page([A])
        self.api.videos[A] = video_item(A, 1200)
        report = self.run_cycle(with_keywords("연애", "썸"))
        record = self.store.get(A)
        assert record is not None
        self.assertEqual(record.keyword, "연애")
        self.assertEqual(self.api.video_batches(), [[A]])
        self.assertEqual(self.events(), [detect(A), views(A, 1200)])
        self.assertEqual((report.searches, report.detected), (2, (A,)))

    def test_duplicate_keywords_are_searched_once(self) -> None:
        self.run_cycle(with_keywords("연애", "썸", "연애"))
        self.assertEqual(self.api.searches(), [("연애", None), ("썸", None)])

    def test_second_videos_batch_is_sampled_s033(self) -> None:
        # 추적 51개 → videos.list 두 번(50 · 1), 두 묶음 모두 200
        tracked = [f"t{n:010d}" for n in range(51)]
        for video_id in tracked:
            self.seed(video_id)
            self.api.videos[video_id] = video_item(video_id, 2000)
        report = self.run_cycle()
        batches = self.api.video_batches()
        self.assertEqual([len(batch) for batch in batches], [50, 1])
        sent = [video_id for batch in batches for video_id in batch]
        self.assertEqual(sorted(sent), tracked)
        self.assertEqual(self.events(), [views(video_id, 2000, prev=1000) for video_id in sent])
        self.assertEqual(self.counts(batches[1][0]), [1000, 2000])
        self.assertEqual(report, CycleReport(1, (), 51, 0, False, False))


class PaginationTest(WatcherCase):
    def test_next_page_follows_an_all_new_page_with_a_token(self) -> None:
        self.api.pages[("연애", None)] = search_page([A], "P1")
        self.api.pages[("연애", "P1")] = search_page([B])
        self.api.videos[A] = video_item(A, 1200)
        self.api.videos[B] = video_item(B, 1300)
        report = self.run_cycle()
        self.assertEqual(self.api.searches(), [("연애", None), ("연애", "P1")])
        self.assertEqual(self.event_names(), [Event.DETECT, Event.VIEWS] * 2)
        self.assertEqual(report, CycleReport(2, (A, B), 2, 0, False, False))

    def test_pages_stop_at_a_video_known_before_the_cycle(self) -> None:
        self.seed(K)
        self.api.pages[("연애", None)] = search_page([A, K], "P1")
        self.api.pages[("연애", "P1")] = search_page([B])
        self.api.videos[A] = video_item(A, 1200)
        self.api.videos[K] = video_item(K, 1100)
        report = self.run_cycle()
        self.assertEqual(self.api.searches(), [("연애", None)])
        self.assertEqual(self.events(), [detect(A), views(A, 1200), views(K, 1100, prev=1000)])
        self.assertEqual(report, CycleReport(1, (A,), 2, 0, False, False))

    def test_pages_stop_without_a_token(self) -> None:
        self.api.pages[("연애", None)] = search_page([A])
        self.api.pages[("연애", "P1")] = search_page([B])
        self.api.videos[A] = video_item(A, 1200)
        report = self.run_cycle()
        self.assertEqual(self.api.searches(), [("연애", None)])
        self.assertEqual(self.event_names(), [Event.DETECT, Event.VIEWS])
        self.assertEqual(report, CycleReport(1, (A,), 1, 0, False, False))

    def test_pages_stop_at_the_page_cap(self) -> None:
        self.reset("endless", endless=True)
        report = self.run_cycle(with_cap(10))
        self.assertEqual(self.api.searches(), [("연애", None), ("연애", "P1"), ("연애", "P2")])
        self.assertEqual(
            self.events()[0], quota(3, 3, "search.list", "pages", keyword="연애")
        )
        self.assertEqual(
            self.raw_lines()[0].split(" ", 1)[1],
            "QUOTA used=3 limit=3 call=search.list counter=pages keyword=연애",
        )
        self.assertEqual(self.event_names()[1:], [Event.DETECT, Event.VIEWS] * 6)
        self.assertEqual(report.truncated, 1)
        self.assertIs(report.held, False)
        self.assertIs(report.failed, False)
        self.assertEqual(len(report.detected), 6)

    def test_next_page_goes_through_the_guard(self) -> None:
        self.reset("endless", endless=True)
        report = self.run_cycle(with_cap(2))
        self.assertEqual(self.api.searches(), [("연애", None), ("연애", "P1")])
        self.assertEqual(
            self.events()[0], quota(2, 2, "search.list", "searches", keyword="연애")
        )
        self.assertEqual(self.event_names()[1:], [Event.DETECT, Event.VIEWS] * 4)
        self.assertIs(report.held, True)
        self.assertEqual(report.truncated, 0)
        self.assertIs(report.failed, False)


class QuotaTest(WatcherCase):
    def test_zero_search_cap_logs_quota_and_still_tracks_views(self) -> None:
        self.seed(K)
        self.api.videos[K] = video_item(K, 1100)
        report = self.run_cycle(with_cap(0))
        self.assertEqual(self.api.searches(), [])
        self.assertEqual(
            self.events(),
            [quota(0, 0, "search.list", "searches", keyword="연애"), views(K, 1100, prev=1000)],
        )
        self.assertEqual(self.api.video_batches(), [[K]])
        self.assertEqual(report, CycleReport(0, (), 1, 0, True, False))

    def test_unit_ceiling_on_videos_logs_quota(self) -> None:
        self.seed(K)
        self.seed_quota(100, NOW - HOUR)
        self.api.videos[K] = video_item(K, 1100)
        report = self.run_cycle()
        self.assertEqual(
            self.events(),
            [
                quota(100, 90, "search.list", "searches", keyword="연애"),
                quota(10000, 10000, "videos.list", "units"),
            ],
        )
        self.assertEqual(self.api.calls, [])
        self.assertEqual(self.counts(K), [1000])
        self.assertEqual(report, CycleReport(0, (), 0, 0, True, False))

    def test_search_hold_stops_the_remaining_keywords_s034(self) -> None:
        # 검색 상한 1 — 첫 키워드의 다음 페이지에서 막히면 둘째 키워드는 묻지도 않습니다
        config = dataclasses.replace(with_cap(1), keywords=("연애", "썸"))
        self.api.pages[("연애", None)] = search_page([A], "P1")
        self.api.videos[A] = video_item(A, 1200)
        report = self.run_cycle(config)
        self.assertEqual(self.api.searches(), [("연애", None)])
        self.assertEqual(
            self.events(),
            [quota(1, 1, "search.list", "searches", keyword="연애"), detect(A), views(A, 1200)],
        )
        self.assertEqual(report, CycleReport(1, (A,), 1, 0, True, False))

    def test_videos_hold_stops_the_remaining_batches_s034(self) -> None:
        # 9,800 단위 + 검색 둘(200) = 10,000 — 첫 videos 묶음부터 막히고 둘째 묶음은 묻지 않습니다
        config = dataclasses.replace(with_cap(100), keywords=("연애", "썸"))
        tracked = [f"t{n:010d}" for n in range(51)]
        for video_id in tracked:
            self.seed(video_id)
            self.api.videos[video_id] = video_item(video_id, 2000)
        self.seed_quota(98, NOW - HOUR)
        report = self.run_cycle(config)
        self.assertEqual(self.api.searches(), [("연애", None), ("썸", None)])
        self.assertEqual(self.api.video_batches(), [])
        self.assertEqual(self.events(), [quota(10000, 10000, "videos.list", "units")])
        self.assertEqual([self.counts(video_id) for video_id in tracked], [[1000]] * 51)
        self.assertEqual(report, CycleReport(2, (), 0, 0, True, False))


class ApiErrorTest(WatcherCase):
    def test_search_error_is_logged_and_views_are_still_tracked(self) -> None:
        error = (
            Event.ERROR,
            {"where": "search.list", "reason": "HTTP 403 quotaExceeded", "keyword": "연애"},
        )
        with self.subTest("first page"):
            self.reset("first page")
            self.seed(K)
            self.api.status["search"] = 403
            self.api.videos[K] = video_item(K, 1100)
            report = self.run_cycle()
            self.assertEqual(self.events(), [error, views(K, 1100, prev=1000)])
            self.assertEqual(
                self.raw_lines()[0].split(" ", 1)[1],
                'ERROR where=search.list reason="HTTP 403 quotaExceeded" keyword=연애',
            )
            self.assertEqual(self.api.video_batches(), [[K]])
            self.assertEqual(report, CycleReport(0, (), 1, 0, False, True))
        with self.subTest("next page"):
            self.reset("next page")
            self.api.pages[("연애", None)] = search_page([A], "P1")
            self.api.pages[("연애", "P1")] = (403, google_error(403))
            self.api.videos[A] = video_item(A, 1200)
            report = self.run_cycle()
            self.assertEqual(self.api.searches(), [("연애", None), ("연애", "P1")])
            self.assertEqual(self.events(), [error, detect(A), views(A, 1200)])
            self.assertEqual(report, CycleReport(1, (A,), 1, 0, False, True))

    def test_search_error_stops_the_remaining_keywords_s034(self) -> None:
        self.api.status["search"] = 403
        report = self.run_cycle(with_keywords("연애", "썸"))
        self.assertEqual(self.api.searches(), [("연애", None)])
        self.assertEqual(
            self.events(),
            [
                (
                    Event.ERROR,
                    {"where": "search.list", "reason": "HTTP 403 quotaExceeded", "keyword": "연애"},
                )
            ],
        )
        self.assertEqual(report, CycleReport(0, (), 0, 0, False, True))

    def test_lone_surrogate_in_the_error_reason_is_replaced_s035(self) -> None:
        body = {"error": {"code": 403, "errors": [{"reason": "bad\ud800"}]}}
        self.api.pages[("연애", None)] = (403, body)
        report = self.run_cycle()
        self.assertEqual(
            self.events(),
            [
                (
                    Event.ERROR,
                    {
                        "where": "search.list",
                        "reason": "HTTP 403 bad\N{REPLACEMENT CHARACTER}",
                        "keyword": "연애",
                    },
                )
            ],
        )
        self.assertEqual(report, CycleReport(0, (), 0, 0, False, True))

    def test_videos_error_stops_tracking(self) -> None:
        tracked = [f"t{n:010d}" for n in range(51)]
        for video_id in tracked:
            self.seed(video_id)
        self.api.status["videos"] = 500
        report = self.run_cycle()
        self.assertEqual(len(self.api.video_batches()), 1)
        self.assertEqual(len(self.api.video_batches()[0]), 50)
        self.assertEqual(
            self.events(),
            [(Event.ERROR, {"where": "videos.list", "reason": "HTTP 500 backendError"})],
        )
        self.assertEqual(report, CycleReport(1, (), 0, 0, False, True))

    def test_items_not_a_list_is_an_error(self) -> None:
        reason = "HTTP 200 items 가 목록이 아닙니다"
        with self.subTest("search.list"):
            self.reset("search")
            self.api.payload["search"] = {"items": {}}
            report = self.run_cycle()
            self.assertEqual(
                self.events(),
                [(Event.ERROR, {"where": "search.list", "reason": reason, "keyword": "연애"})],
            )
            self.assertEqual(report, CycleReport(1, (), 0, 0, False, True))
        with self.subTest("videos.list"):
            self.reset("videos")
            self.seed(K)
            self.api.payload["videos"] = {"items": "x"}
            report = self.run_cycle()
            self.assertEqual(
                self.events(), [(Event.ERROR, {"where": "videos.list", "reason": reason})]
            )
            self.assertEqual(self.counts(K), [1000])
            self.assertEqual(report, CycleReport(1, (), 0, 0, False, True))


def bad_item(**changes: object) -> dict[str, object]:
    """A 의 정상 항목에서 snippet · statistics 칸 하나를 바꾸거나(값 ...) 지웁니다."""
    item = video_item(A, 1200)
    for key, value in changes.items():
        section, _, name = key.partition("__")
        if not name:
            del item[section]
        elif value is ...:
            del item[section][name]  # type: ignore[attr-defined]
        else:
            item[section][name] = value  # type: ignore[index]
    return item


INVALID_ITEMS: tuple[tuple[str, dict[str, object]], ...] = (
    ("viewCount -5", bad_item(statistics__viewCount="-5")),
    ("viewCount 1_000", bad_item(statistics__viewCount="1_000")),
    ("viewCount ' 12'", bad_item(statistics__viewCount=" 12")),
    ("viewCount arabic-indic", bad_item(statistics__viewCount="١٢٣")),
    ("viewCount 20 digits", bad_item(statistics__viewCount="1" * 20)),
    ("viewCount int", bad_item(statistics__viewCount=1200)),
    ("viewCount missing", bad_item(statistics__viewCount=...)),
    ("publishedAt 어제", bad_item(snippet__publishedAt="어제")),
    ("publishedAt None", bad_item(snippet__publishedAt=None)),
    ("publishedAt +09:00", bad_item(snippet__publishedAt="2026-10-12T10:00:00+09:00")),
    ("publishedAt year 1 +14:00", bad_item(snippet__publishedAt="0001-01-01T00:00:00+14:00")),
    ("publishedAt 9999 -01:00", bad_item(snippet__publishedAt="9999-12-31T23:59:59-01:00")),
    ("publishedAt basic", bad_item(snippet__publishedAt="20261012T100000+0000")),
    ("publishedAt week date", bad_item(snippet__publishedAt="2026-W41-1T10:00:00+00:00")),
    ("publishedAt no zone", bad_item(snippet__publishedAt="2026-10-12T10:00:00")),
    ("publishedAt month 13", bad_item(snippet__publishedAt="2026-13-01T00:00:00Z")),
    ("channelId empty", bad_item(snippet__channelId="")),
    ("no snippet", bad_item(snippet="")),
    ("no statistics", bad_item(statistics="")),
)


class IntakeTest(WatcherCase):
    def test_unavailable_video_is_skipped(self) -> None:
        self.seed(K)
        self.api.pages[("연애", None)] = search_page([A])
        report = self.run_cycle()
        self.assertEqual(self.api.video_batches(), [[A, K]])
        self.assertEqual(
            self.events(),
            [skip(A, "unavailable", "videos.list"), skip(K, "unavailable", "videos.list")],
        )
        self.assertIsNone(self.store.get(A))
        self.assertEqual(self.counts(K), [1000])
        self.assertEqual(report, CycleReport(1, (), 0, 0, False, False))

    def test_invalid_items_are_skipped_not_stored(self) -> None:
        for n, (label, item) in enumerate(INVALID_ITEMS):
            with self.subTest(label):
                self.reset(f"invalid-{n}")
                self.api.pages[("연애", None)] = search_page([A])
                self.api.videos[A] = item
                report = self.run_cycle()
                [(event, fields)] = self.events()
                self.assertEqual(event, Event.SKIP)
                self.assertTrue(fields.pop("detail"))
                self.assertEqual(
                    fields, {"video": A, "reason": "invalid_item", "call": "videos.list"}
                )
                self.assertIsNone(self.store.get(A))
                self.assertIsNone(Store(self.store_path).get(A))
                self.assertEqual(report, CycleReport(1, (), 0, 0, False, False))
        with self.subTest("known video, viewCount -5"):
            self.reset("known")
            self.seed(K)
            item = video_item(K, 0)
            item["statistics"] = {"viewCount": "-5"}
            self.api.videos[K] = item
            report = self.run_cycle()
            self.assertEqual(
                [(event, {k: v for k, v in fields.items() if k != "detail"})
                 for event, fields in self.events()],
                [skip(K, "invalid_item", "videos.list")],
            )
            self.assertEqual(self.counts(K), [1000])
            self.assertEqual(report.sampled, 0)

    def test_invalid_search_id_is_skipped(self) -> None:
        page = search_page(["short", 12345, B])
        page["items"].insert(2, {"id": {"kind": "youtube#video"}})  # type: ignore[union-attr]
        self.api.pages[("연애", None)] = page
        self.api.videos[B] = video_item(B, 1200)
        report = self.run_cycle()
        self.assertEqual(
            self.events(),
            [
                skip("short", "invalid_item", "search.list", keyword="연애"),
                skip("-", "invalid_item", "search.list", keyword="연애"),
                skip("-", "invalid_item", "search.list", keyword="연애"),
                detect(B),
                views(B, 1200),
            ],
        )
        self.assertEqual(self.api.video_batches(), [[B]])
        self.assertEqual(report.detected, (B,))

    def test_published_at_accepts_only_the_utc_z_form(self) -> None:
        self.api.pages[("연애", None)] = search_page([A, B])
        self.api.videos[A] = video_item(A, 1200, published="2026-10-12T10:00:00Z")
        self.api.videos[B] = video_item(B, 1300, published="2026-10-12T10:00:00.123Z")
        report = self.run_cycle()
        for video_id in (A, B):
            record = Store(self.store_path).get(video_id)
            assert record is not None
            self.assertEqual(record.published_at, PUBLISHED)
            self.assertEqual(record.published_at.utcoffset(), timedelta(0))
        self.assertEqual(report.detected, (A, B))

    def test_offset_at_the_date_limit_does_not_poison_the_store(self) -> None:
        self.api.pages[("연애", None)] = search_page([B, C])
        self.api.videos[B] = video_item(B, 1200, published="0001-01-01T00:00:00+14:00")
        self.api.videos[C] = video_item(C, 1300)
        report = self.run_cycle()
        self.assertEqual(self.event_names(), [Event.SKIP, Event.DETECT, Event.VIEWS])
        self.assertEqual(self.events()[0][1]["video"], B)
        self.assertEqual([r.video_id for r in Store(self.store_path).records()], [C])
        self.store.save_test(C, NOW, "dry_run")
        reloaded = Store(self.store_path)
        self.assertIsNone(reloaded.get(B))
        record = reloaded.get(C)
        assert record is not None
        self.assertEqual([(a.mode, a.result) for a in record.attempts], [("test", "saved")])
        self.assertEqual(report.detected, (C,))

    def test_lone_surrogate_title_is_replaced_and_the_store_reloads(self) -> None:
        item = video_item(A, 1200, title="\ud800연애")
        item["snippet"]["description"] = "\udfff"  # type: ignore[index]
        self.api.pages[("연애", None)] = search_page([A])
        self.api.videos[A] = item
        self.run_cycle()
        record = Store(self.store_path).get(A)
        assert record is not None
        self.assertEqual(record.title, "\N{REPLACEMENT CHARACTER}연애")
        self.assertEqual(record.description, "\N{REPLACEMENT CHARACTER}")
        self.assertEqual(self.events()[0], detect(A, title="\N{REPLACEMENT CHARACTER}연애"))

    def test_lone_surrogates_outside_title_are_replaced_s035(self) -> None:
        bad, fixed = "\ud800", "\N{REPLACEMENT CHARACTER}"
        with self.subTest("channelId"):
            self.reset("channel")
            self.api.pages[("연애", None)] = search_page([A])
            self.api.videos[A] = video_item(A, 1200, channel="UC" + bad)
            report = self.run_cycle()
            self.assertEqual(
                self.events(),
                [(Event.DETECT, {**detect(A)[1], "channel": "UC" + fixed}), views(A, 1200)],
            )
            record = Store(self.store_path).get(A)
            assert record is not None
            self.assertEqual(record.channel_id, "UC" + fixed)
            self.assertEqual(report, CycleReport(1, (A,), 1, 0, False, False))
        with self.subTest("keyword"):
            self.reset("keyword")
            self.api.pages[("연애" + fixed, None)] = search_page([A])
            self.api.videos[A] = video_item(A, 1200)
            report = self.run_cycle(with_keywords("연애" + bad))
            self.assertEqual(self.api.searches(), [("연애" + fixed, None)])
            self.assertEqual(
                self.events(),
                [(Event.DETECT, {**detect(A)[1], "keyword": "연애" + fixed}), views(A, 1200)],
            )
            record = Store(self.store_path).get(A)
            assert record is not None
            self.assertEqual(record.keyword, "연애" + fixed)
            self.assertEqual(report, CycleReport(1, (A,), 1, 0, False, False))
        with self.subTest("search videoId"):
            self.reset("search id")
            self.api.pages[("연애", None)] = search_page(["x" + bad])
            report = self.run_cycle()
            self.assertEqual(
                self.events(), [skip("x" + fixed, "invalid_item", "search.list", keyword="연애")]
            )
            self.assertEqual(report, CycleReport(1, (), 0, 0, False, False))
        with self.subTest("viewCount detail"):
            # detail 은 값을 repr(!r)로 적어 서로게이트가 이미 `\ud800` 여섯 글자로 바뀌어 옵니다
            self.reset("detail")
            self.api.pages[("연애", None)] = search_page([A])
            self.api.videos[A] = bad_item(statistics__viewCount="1" + bad)
            report = self.run_cycle()
            self.assertEqual(
                self.events(),
                [
                    skip(
                        A,
                        "invalid_item",
                        "videos.list",
                        detail="statistics.viewCount: 0 이상의 10진수 글자가 아닙니다: '1\\ud800'",
                    )
                ],
            )
            self.assertEqual(report, CycleReport(1, (), 0, 0, False, False))


class ClockTest(WatcherCase):
    def test_cycle_uses_the_injected_clock(self) -> None:
        later = NOW + 3 * HOUR
        self.api.pages[("연애", None)] = search_page([A])
        self.api.videos[A] = video_item(A, 1200)
        self.watcher(lambda: later).cycle(CONFIG)
        record = self.store.get(A)
        assert record is not None
        self.assertEqual((record.detected_at, record.view_history), (later, [ViewSample(later, 1200)]))
        self.assertEqual(self.api.calls[0][1]["publishedAfter"], "2026-10-12T03:00:00Z")
        self.assertEqual(QuotaLedger(self.quota_path).usage(later), Usage(1, 101))
        self.assertEqual(QuotaLedger(self.quota_path).usage(later + 24 * HOUR), Usage(0, 0))

    def test_naive_now_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.watcher().run(CONFIG, datetime(2026, 10, 12, 12, 0))
        self.assertEqual(self.api.calls, [])
        self.assertEqual(self.raw_lines(), [])


if __name__ == "__main__":
    unittest.main()
