"""쿼터 가드 · YouTube 클라이언트 테스트 — 가짜 전송으로, 네트워크 없이."""
from __future__ import annotations

import http.client
import json
import tempfile
import unittest
import urllib.parse
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.config import LimitsConfig
from agent.youtube import (
    DAILY_QUOTA_UNITS,
    QuotaError,
    QuotaExhausted,
    QuotaLedger,
    Usage,
    YouTubeClient,
    YouTubeError,
)

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
DAY = timedelta(hours=24)
SECOND = timedelta(seconds=1)
WINDOW_START = NOW - timedelta(hours=12)
KST = timezone(timedelta(hours=9))
KEY = "test-key"
OK = (200, b'{"items": []}')
SITES = ("first page", "next page", "videos")
SITE_CALL = {"first page": "search.list", "next page": "search.list", "videos": "videos.list"}

Entry = tuple[datetime, str, int]


def limits(n: int) -> LimitsConfig:
    return LimitsConfig(10, 24.0, n)


def searches(n: int, at: datetime) -> list[Entry]:
    return [(at, "search.list", 100)] * n


def videos(n: int, at: datetime) -> list[Entry]:
    return [(at, "videos.list", 1)] * n


def seed(path: Path, entries: list[Entry]) -> None:
    calls = [{"at": at.isoformat(), "call": call, "units": units} for at, call, units in entries]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"calls": calls, "schema_version": 1}), encoding="utf-8")


class FakeFetch:
    """URL 을 기록하고, 쌓아 둔 (상태, 본문)을 돌려주거나 쌓아 둔 예외를 냅니다.

    쌓아 둔 것이 URL 을 받는 함수면 그 결과를 씁니다. 다 쓰면 빈 200 입니다.
    """

    def __init__(self, *responses: object, on_call: Callable[[str], None] | None = None) -> None:
        self.urls: list[str] = []
        self._responses = list(responses)
        self._on_call = on_call

    def __call__(self, url: str, timeout: float) -> tuple[int, bytes]:
        self.urls.append(url)
        if self._on_call is not None:
            self._on_call(url)
        response = self._responses.pop(0) if self._responses else OK
        if callable(response):
            response = response(url)
        if isinstance(response, BaseException):
            raise response
        return response


def query_of(url: str) -> dict[str, str]:
    pairs = urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query, keep_blank_values=True)
    result = dict(pairs)
    if len(result) != len(pairs):
        raise AssertionError(f"같은 매개변수가 두 번 나옵니다: {url}")
    return result


class YouTubeCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = self.dir / "data" / "quota.json"

    def client(
        self, fetch: FakeFetch, entries: list[Entry] | None = None, name: str = "data"
    ) -> YouTubeClient:
        self.path = self.dir / name / "quota.json"
        if entries is not None:
            seed(self.path, entries)
        self.ledger = QuotaLedger(self.path)
        return YouTubeClient(KEY, self.ledger, fetch)

    def call(
        self, client: YouTubeClient, site: str, cap: int = 90, now: datetime = NOW
    ) -> dict[str, object]:
        if site == "first page":
            return client.search("연애", WINDOW_START, None, now, limits(cap))
        if site == "next page":
            return client.search("연애", WINDOW_START, "P2", now, limits(cap))
        return client.videos(["abcdefghijk"], now, limits(cap))

    def assert_held(
        self, caught: QuotaExhausted, call: str, counter: str, used: int, limit: int
    ) -> None:
        self.assertEqual(
            (caught.call, caught.counter, caught.used, caught.limit), (call, counter, used, limit)
        )

    def stored(self) -> list[dict[str, object]]:
        return json.loads(self.path.read_text(encoding="utf-8"))["calls"]


class LedgerTest(YouTubeCase):
    def test_search_cap_holds_before_fetch(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        client.search("연애", WINDOW_START, None, NOW, limits(2))
        client.search("썸", WINDOW_START, None, NOW, limits(2))
        with self.assertRaises(QuotaExhausted) as caught:
            client.search("이별", WINDOW_START, None, NOW, limits(2))
        self.assert_held(caught.exception, "search.list", "searches", 2, 2)
        self.assertEqual(len(fetch.urls), 2)
        self.assertEqual(self.ledger.usage(NOW), Usage(2, 200))
        self.assertEqual(len(self.stored()), 2)

    def test_zero_cap_holds_the_first_search(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        with self.assertRaises(QuotaExhausted) as caught:
            client.search("연애", WINDOW_START, None, NOW, limits(0))
        self.assert_held(caught.exception, "search.list", "searches", 0, 0)
        self.assertEqual(fetch.urls, [])
        self.assertFalse(self.path.exists())

    def test_next_page_is_counted_like_a_first_page(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        client.search("연애", WINDOW_START, "P2", NOW, limits(90))
        self.assertEqual(self.ledger.usage(NOW).searches, 1)
        with self.assertRaises(QuotaExhausted) as caught:
            client.search("연애", WINDOW_START, "P3", NOW, limits(1))
        self.assert_held(caught.exception, "search.list", "searches", 1, 1)
        self.assertEqual(len(fetch.urls), 1)

    def test_videos_cost_one_unit_and_no_search(self) -> None:
        # 검색 상한 0 에서도 조회수 호출은 지나갑니다 — 검색 상한은 search.list 만 셉니다
        fetch = FakeFetch()
        client = self.client(fetch)
        client.videos(["abcdefghijk"], NOW, limits(0))
        self.assertEqual(self.ledger.usage(NOW), Usage(0, 1))
        self.assertEqual(len(fetch.urls), 1)

    def test_unit_ceiling_holds_videos(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch, searches(99, NOW - SECOND) + videos(100, NOW - SECOND))
        with self.assertRaises(QuotaExhausted) as caught:
            client.videos(["abcdefghijk"], NOW, limits(90))
        self.assert_held(caught.exception, "videos.list", "units", 10000, DAILY_QUOTA_UNITS)
        self.assertEqual(fetch.urls, [])
        self.assertEqual(len(self.stored()), 199)

    def test_last_unit_under_the_ceiling_is_allowed_s036(self) -> None:
        # 9,999 단위 — videos.list(1단위) 하나는 10,000 에 딱 닿아 지나가고, 다음 것은 막힙니다
        fetch = FakeFetch()
        client = self.client(fetch, searches(99, NOW - SECOND) + videos(99, NOW - SECOND))
        self.assertEqual(self.ledger.usage(NOW), Usage(99, 9999))
        client.videos(["abcdefghijk"], NOW, limits(90))
        self.assertEqual(len(fetch.urls), 1)
        self.assertEqual(self.ledger.usage(NOW), Usage(99, 10000))
        with self.assertRaises(QuotaExhausted) as caught:
            client.videos(["abcdefghijk"], NOW, limits(90))
        self.assert_held(caught.exception, "videos.list", "units", 10000, DAILY_QUOTA_UNITS)
        self.assertEqual(len(fetch.urls), 1)

    def test_unit_ceiling_holds_search_under_a_raised_search_cap(self) -> None:
        for site in ("first page", "next page"):
            with self.subTest(site):
                fetch = FakeFetch()
                entries = searches(99, NOW - SECOND) + videos(1, NOW - SECOND)
                client = self.client(fetch, entries, name=site)
                with self.assertRaises(QuotaExhausted) as caught:
                    self.call(client, site, cap=200)
                self.assert_held(caught.exception, "search.list", "units", 9901, 10000)
                self.assertEqual(fetch.urls, [])

    def test_entry_exactly_24h_old_is_not_counted(self) -> None:
        # 검색은 90개로 검색 상한을, 조회수는 100개(10,000 단위)로 단위 상한을 경계에 세웁니다
        for site in SITES:
            count, cap = (100, 90) if site == "videos" else (90, 90)
            with self.subTest(site, at="now - 24h"):
                fetch = FakeFetch()
                client = self.client(fetch, searches(count, NOW - DAY), name=f"{site}-old")
                self.call(client, site, cap=cap)
                self.assertEqual(len(fetch.urls), 1)
            with self.subTest(site, at="now - 24h + 1s"):
                fetch = FakeFetch()
                entries = searches(count if site == "videos" else 1, NOW - DAY + SECOND)
                client = self.client(fetch, entries, name=f"{site}-young")
                with self.assertRaises(QuotaExhausted):
                    self.call(client, site, cap=cap if site == "videos" else 1)
                self.assertEqual(fetch.urls, [])

    def test_call_is_on_disk_before_fetch(self) -> None:
        for site in SITES:
            with self.subTest(site):
                seen: list[list[dict[str, object]]] = []
                fetch = FakeFetch(on_call=lambda url: seen.append(self.stored()))
                client = self.client(fetch, name=site)
                self.call(client, site)
                self.assertEqual(len(seen), 1)
                self.assertEqual([entry["call"] for entry in seen[0]], [SITE_CALL[site]])
                self.assertEqual(seen[0][0]["at"], "2026-10-12T12:00:00+00:00")

    def test_failed_fetch_still_counts(self) -> None:
        for site in SITES:
            with self.subTest(site):
                fetch = FakeFetch((500, b"{}"))
                client = self.client(fetch, name=site)
                with self.assertRaises(YouTubeError):
                    self.call(client, site)
                expected = Usage(0, 1) if site == "videos" else Usage(1, 100)
                self.assertEqual(self.ledger.usage(NOW), expected)
                self.assertEqual(QuotaLedger(self.path).usage(NOW), expected)

    def test_usage_survives_a_restart(self) -> None:
        client = self.client(FakeFetch())
        client.search("연애", WINDOW_START, None, NOW, limits(90))
        client.videos(["abcdefghijk"], NOW, limits(90))
        self.assertEqual(QuotaLedger(self.path).usage(NOW + SECOND), Usage(1, 101))

    def test_old_entries_are_pruned_on_write(self) -> None:
        old = NOW - timedelta(hours=30)
        client = self.client(FakeFetch(), searches(1, old) + searches(1, NOW - SECOND))
        client.search("연애", WINDOW_START, None, NOW, limits(90))
        self.assertEqual(
            [entry["at"] for entry in self.stored()],
            ["2026-10-12T11:59:59+00:00", "2026-10-12T12:00:00+00:00"],
        )

    def test_unreadable_ledger_refuses_and_keeps_the_file(self) -> None:
        def entry(**changes: object) -> bytes:
            item: dict[str, object] = {
                "at": "2026-10-12T11:00:00+00:00",
                "call": "search.list",
                "units": 100,
            }
            item.update(changes)
            item = {key: value for key, value in item.items() if value is not ...}
            return json.dumps({"calls": [item], "schema_version": 1}).encode("utf-8")

        valid = json.dumps({"calls": [], "schema_version": 1})
        rows = (
            ("not JSON", b"{not json"),
            ("top level list", b"[]"),
            ("version 2", json.dumps({"calls": [], "schema_version": 2}).encode("utf-8")),
            ("no version", json.dumps({"calls": []}).encode("utf-8")),
            ("calls not a list", json.dumps({"calls": {}, "schema_version": 1}).encode("utf-8")),
            ("entry not a dict", json.dumps({"calls": [1], "schema_version": 1}).encode("utf-8")),
            ("entry missing units", entry(units=...)),
            ("entry with an extra key", entry(note="x")),
            ("naive at", entry(at="2026-10-12T11:00:00")),
            ("at not ISO", entry(at="어제")),
            ("at not a string", entry(at=1760000000)),
            ("unknown call", entry(call="channels.list")),
            ("bool units", entry(units=True)),
            ("negative units", entry(units=-1)),
            ("float units", entry(units=1.0)),
            ("utf-16 bytes", valid.encode("utf-16")),
        )
        for label, raw in rows:
            with self.subTest(label):
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_bytes(raw)
                fetch = FakeFetch()
                with self.assertRaises(QuotaError) as caught:
                    YouTubeClient(KEY, QuotaLedger(self.path), fetch)
                message = str(caught.exception)
                self.assertIn("쿼터 기록 파일을 믿을 수 없습니다", message)
                self.assertIn(str(self.path), message)
                self.assertEqual(fetch.urls, [])
                self.assertEqual(self.path.read_bytes(), raw)

    def test_naive_now_is_rejected(self) -> None:
        naive = datetime(2026, 10, 12, 12, 0)
        fetch = FakeFetch()
        client = self.client(fetch)
        with self.assertRaises(ValueError):
            self.ledger.usage(naive)
        for site in SITES:
            with self.subTest(site):
                with self.assertRaises(ValueError):
                    self.call(client, site, now=naive)
        with self.assertRaises(ValueError):
            client.search("연애", datetime(2026, 10, 12, 0, 0), None, NOW, limits(90))
        self.assertEqual(fetch.urls, [])
        self.assertFalse(self.path.exists())


class ClientTest(YouTubeCase):
    def test_search_url_carries_region_language_window_and_order(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        client.search("연애", WINDOW_START.astimezone(KST), None, NOW, limits(90))
        parts = urllib.parse.urlsplit(fetch.urls[0])
        self.assertEqual(
            (parts.scheme, parts.netloc, parts.path),
            ("https", "www.googleapis.com", "/youtube/v3/search"),
        )
        self.assertEqual(
            query_of(fetch.urls[0]),
            {
                "part": "snippet",
                "type": "video",
                "order": "date",
                "q": "연애",
                "regionCode": "KR",
                "relevanceLanguage": "ko",
                "maxResults": "50",
                "publishedAfter": "2026-10-12T00:00:00Z",
                "key": "test-key",
            },
        )

    def test_page_token_is_sent_only_when_given(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        client.search("연애", WINDOW_START, "P2", NOW, limits(90))
        client.search("연애", WINDOW_START, None, NOW, limits(90))
        self.assertEqual(query_of(fetch.urls[0])["pageToken"], "P2")
        self.assertNotIn("pageToken", query_of(fetch.urls[1]))

    def test_videos_url_joins_ids(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        client.videos(["aaaaaaaaaaa", "bbbbbbbbbbb"], NOW, limits(90))
        self.assertEqual(urllib.parse.urlsplit(fetch.urls[0]).path, "/youtube/v3/videos")
        self.assertEqual(
            query_of(fetch.urls[0]),
            {"part": "snippet,statistics", "id": "aaaaaaaaaaa,bbbbbbbbbbb", "key": "test-key"},
        )

    def test_videos_batch_size_is_checked_before_reserving(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        for ids in ([], [f"v{n:010d}" for n in range(51)]):
            with self.subTest(count=len(ids)):
                with self.assertRaises(ValueError):
                    client.videos(ids, NOW, limits(90))
        self.assertEqual(self.ledger.usage(NOW), Usage(0, 0))
        self.assertEqual(fetch.urls, [])
        self.assertFalse(self.path.exists())
        client.videos([f"v{n:010d}" for n in range(50)], NOW, limits(90))
        self.assertEqual(len(fetch.urls), 1)

    def test_http_error_reason_names_google_reason(self) -> None:
        quota = {"error": {"code": 403, "errors": [{"reason": "quotaExceeded"}]}}
        echoed = {"error": {"errors": [{"reason": f"keyInvalid {KEY}"}]}}
        rows = (
            ((403, json.dumps(quota).encode("utf-8")), "HTTP 403 quotaExceeded"),
            ((500, b"<html>"), "HTTP 500"),
            ((404, b'{"error": {"errors": []}}'), "HTTP 404"),
            ((400, json.dumps(echoed).encode("utf-8")), "HTTP 400 keyInvalid <YOUTUBE_API_KEY>"),
        )
        for response, reason in rows:
            with self.subTest(reason):
                client = self.client(FakeFetch(response))
                with self.assertRaises(YouTubeError) as caught:
                    client.search("연애", WINDOW_START, None, NOW, limits(90))
                exc = caught.exception
                self.assertEqual((exc.call, exc.reason), ("search.list", reason))
                self.assertEqual(str(exc), f"search.list: {reason}")

    def test_network_error_never_carries_the_key(self) -> None:
        rows = (
            (lambda url: OSError(f"연결 실패: {url}"), "network OSError: 연결 실패: ", True),
            (http.client.IncompleteRead(b"partial"), "network IncompleteRead: ", False),
        )
        for response, prefix, echoes_url in rows:
            with self.subTest(prefix):
                client = self.client(FakeFetch(response))
                with self.assertRaises(YouTubeError) as caught:
                    client.videos(["abcdefghijk"], NOW, limits(90))
                exc = caught.exception
                self.assertEqual(exc.call, "videos.list")
                self.assertTrue(exc.reason.startswith(prefix), exc.reason)
                self.assertNotIn(KEY, exc.reason)
                self.assertNotIn(KEY, str(exc))
                if echoes_url:
                    self.assertIn("key=<YOUTUBE_API_KEY>", exc.reason)
                # 원래 예외(키가 든 URL)는 traceback 에도 붙지 않습니다
                self.assertIsNone(exc.__cause__)
                self.assertTrue(exc.__suppress_context__)

    def test_invalid_json_is_an_error(self) -> None:
        for body in (b"not json", b"[1, 2]", b'"text"', b"[" * 100_000, b"\xff\xfe"):
            with self.subTest(body=body[:10]):
                client = self.client(FakeFetch((200, body)))
                with self.assertRaises(YouTubeError) as caught:
                    client.search("연애", WINDOW_START, None, NOW, limits(90))
                self.assertEqual(caught.exception.reason, "HTTP 200 invalid JSON")

    def test_api_key_outside_the_key_alphabet_is_rejected(self) -> None:
        # 메시지는 어떤 입력에도 같은 글자입니다 — 그래서 키가 섞일 자리가 없습니다
        ledger = QuotaLedger(self.path)
        for key in ("", "abc\r", "a b", "키", None):
            with self.subTest(key=key):
                with self.assertRaises(ValueError) as caught:
                    YouTubeClient(key, ledger, FakeFetch())  # type: ignore[arg-type]
                self.assertEqual(
                    str(caught.exception), "API 키 형식이 아닙니다 — 영문자 · 숫자 · _ · - 만 씁니다"
                )


if __name__ == "__main__":
    unittest.main()
