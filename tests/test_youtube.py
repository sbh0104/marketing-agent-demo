"""쿼터 가드 · YouTube 클라이언트 테스트 — 가짜 전송으로, 네트워크 없이."""
from __future__ import annotations

import http.client
import json
import os
import tempfile
import unittest
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest import mock

from agent.config import LimitsConfig
from agent.youtube import (
    COMMENTS_DISABLED,
    DAILY_QUOTA_UNITS,
    QuotaError,
    QuotaExhausted,
    QuotaLedger,
    Usage,
    YouTubeClient,
    YouTubeError,
    http_get,
)
from tests.loopback import RawServer, no_proxies, response

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


def thread(
    text: object, author: str = "작성자이름", channel: str = "UCauthor0000000000000000"
) -> dict[str, object]:
    """commentThreads.list 항목 하나 — 작성자 이름 · 채널 ID 까지 갖춘 실제 모양."""
    return {
        "kind": "youtube#commentThread",
        "id": "thread0001",
        "snippet": {
            "videoId": "abcdefghijk",
            "topLevelComment": {
                "kind": "youtube#comment",
                "snippet": {
                    "textDisplay": text,
                    "textOriginal": text,
                    "authorDisplayName": author,
                    "authorChannelId": {"value": channel},
                    "likeCount": 7,
                },
            },
            "totalReplyCount": 0,
        },
    }


def threads(*items: object) -> tuple[int, bytes]:
    return 200, json.dumps({"items": list(items)}).encode("utf-8")


def google_error(reason: str) -> bytes:
    """403 본문 — error.errors[0].reason 에 Google 의 이유를 담습니다."""
    body = {"error": {"code": 403, "errors": [{"reason": reason}]}}
    return json.dumps(body).encode("utf-8")


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


class _OddError(Exception):
    """전송이 낼 수 있는, 이름을 미리 알 수 없는 예외 하나."""


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
                with self.assertRaises(QuotaError) as caught:
                    QuotaLedger(self.path)
                message = str(caught.exception)
                self.assertIn("쿼터 기록 파일을 믿을 수 없습니다", message)
                self.assertIn(str(self.path), message)
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

    def test_bom_prefixed_ledger_is_read_s043(self) -> None:
        # 윈도우 메모장이 붙이는 BOM 이 앞에 있어도 유효한 기록으로 읽습니다
        seed(self.path, searches(1, NOW - SECOND))
        self.path.write_bytes(b"\xef\xbb\xbf" + self.path.read_bytes())
        self.assertEqual(QuotaLedger(self.path).usage(NOW), Usage(1, 100))

    def test_saved_ledger_is_sorted_indented_and_utc_s043(self) -> None:
        # KST now 로 적어도 at 은 +00:00 — 키 정렬 · 2칸 들여쓰기 · 끝 줄바꿈 한 번
        QuotaLedger(self.path).reserve("search.list", NOW.astimezone(KST), limits(90))
        self.assertEqual(
            self.path.read_bytes().decode("utf-8"),
            "{\n"
            '  "calls": [\n'
            "    {\n"
            '      "at": "2026-10-12T12:00:00+00:00",\n'
            '      "call": "search.list",\n'
            '      "units": 100\n'
            "    }\n"
            "  ],\n"
            '  "schema_version": 1\n'
            "}\n",
        )

    def test_unbuildable_url_is_neither_reserved_nor_fetched_s043(self) -> None:
        # URL 을 만들 수 없는 호출(외톨이 서로게이트 pageToken)은 장부에 적기 전에 멈춥니다
        fetch = FakeFetch()
        client = self.client(fetch)
        with self.assertRaises(UnicodeEncodeError):
            client.search("연애", WINDOW_START, "\ud800", NOW, limits(90))
        self.assertEqual(fetch.urls, [])
        self.assertFalse(self.path.exists())
        self.assertEqual(self.ledger.usage(NOW), Usage(0, 0))

    def test_unknown_call_is_refused_s043(self) -> None:
        ledger = QuotaLedger(self.path)
        with self.assertRaises(ValueError) as caught:
            ledger.reserve("comments.list", NOW, limits(90))
        self.assertEqual(str(caught.exception), "모르는 호출입니다: 'comments.list'")
        self.assertFalse(self.path.exists())

    def test_ledger_is_written_through_a_tmp_file_s045(self) -> None:
        ledger = QuotaLedger(self.path)
        with mock.patch("os.replace", wraps=os.replace) as replace:
            ledger.reserve("search.list", NOW, limits(90))
        replace.assert_called_once()
        source, target = replace.call_args.args
        self.assertTrue(str(source).endswith("quota.json.tmp"), source)
        self.assertEqual(Path(source), self.path.with_name("quota.json.tmp"))
        self.assertEqual(Path(target), self.path)
        self.assertFalse(Path(source).exists())
        self.assertEqual(len(self.stored()), 1)


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
        # _fetch 의 예외는 무엇이든 ERROR 한 줄 — 깨진 덩어리 틀 · 리다이렉트 · 시간 상한도 (트래커 7A ③(가))
        rows = (
            (lambda url: OSError(f"연결 실패: {url}"), "network OSError: 연결 실패: ", True),
            (http.client.IncompleteRead(b"partial"), "network IncompleteRead: ", False),
            (
                ValueError("read length must be non-negative or -1"),
                "network ValueError: read length must be non-negative or -1",
                False,
            ),
            (
                lambda url: TypeError(f"gethostbyname() argument 1 must be str: {url}"),
                "network TypeError: gethostbyname()",
                True,
            ),
            (UnicodeError("label empty or too long"), "network UnicodeError: label empty", False),
            (OverflowError("port must be 0-65535."), "network OverflowError: port must", False),
            (MemoryError(), "network MemoryError: ", False),
            (
                TimeoutError("요청 전체가 30초 상한을 넘었습니다"),
                "network TimeoutError: 요청 전체가 30초 상한을 넘었습니다",
                False,
            ),
            (lambda url: _OddError(f"이상한 실패 {url}"), "network _OddError: 이상한 실패 ", True),
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

    def test_interrupt_from_fetch_is_not_wrapped(self) -> None:
        # Ctrl+C 는 BaseException 이라 ERROR 줄로 바뀌지 않고 그대로 올라갑니다 — 장부에는 이미 적혔습니다
        client = self.client(FakeFetch(KeyboardInterrupt()))
        with self.assertRaises(KeyboardInterrupt):
            client.videos(["abcdefghijk"], NOW, limits(90))
        self.assertEqual(self.ledger.usage(NOW), Usage(0, 1))

    def test_fetch_gets_the_whole_request_cap(self) -> None:
        # _fetch 에 넘기는 값은 요청 전체의 상한 30초입니다 (계약 '탐지 · 조회수 추적' 절 'API 오류')
        seen: list[float] = []

        def fetch(url: str, timeout: float) -> tuple[int, bytes]:
            seen.append(timeout)
            return OK

        YouTubeClient(KEY, QuotaLedger(self.path), fetch).videos(["abcdefghijk"], NOW, limits(90))
        self.assertEqual(seen, [30.0])

    def test_url_echoed_twice_is_masked_twice_s043(self) -> None:
        client = self.client(FakeFetch(lambda url: OSError(f"{url} 다시 {url}")))
        with self.assertRaises(YouTubeError) as caught:
            client.videos(["abcdefghijk"], NOW, limits(90))
        reason = caught.exception.reason
        self.assertEqual(reason.count("key=<YOUTUBE_API_KEY>"), 2, reason)
        self.assertNotIn(KEY, reason)
        self.assertNotIn(KEY, str(caught.exception))

    def test_non_200_status_is_an_error_s043(self) -> None:
        # 2xx · 3xx 라도 200 이 아니면 오류 — Google reason 이 없으면 "HTTP 302" 만 남습니다
        client = self.client(FakeFetch((302, b'{"items": []}')))
        with self.assertRaises(YouTubeError) as caught:
            client.search("연애", WINDOW_START, None, NOW, limits(90))
        exc = caught.exception
        self.assertEqual((exc.call, exc.reason), ("search.list", "HTTP 302"))

    def test_non_string_google_reason_is_left_out_s045(self) -> None:
        for reason in (5, None):
            with self.subTest(reason=reason):
                body = json.dumps({"error": {"errors": [{"reason": reason}]}}).encode("utf-8")
                client = self.client(FakeFetch((404, body)), name=f"reason-{reason}")
                with self.assertRaises(YouTubeError) as caught:
                    client.search("연애", WINDOW_START, None, NOW, limits(90))
                self.assertEqual(caught.exception.reason, "HTTP 404")

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

    def test_search_sends_published_before_when_given(self) -> None:
        # 넓힌 창: 72시간 전부터 운영 창(12시간)이 시작되기 전까지
        fetch = FakeFetch()
        client = self.client(fetch)
        after = NOW - timedelta(hours=72)
        client.search("연애", after, None, NOW, limits(90), WINDOW_START.astimezone(KST))
        client.search("연애", after, None, NOW, limits(90))
        widened, plain = query_of(fetch.urls[0]), query_of(fetch.urls[1])
        self.assertEqual(widened["publishedBefore"], "2026-10-12T00:00:00Z")
        self.assertEqual(widened["publishedAfter"], "2026-10-09T12:00:00Z")
        self.assertNotIn("publishedBefore", plain)
        self.assertEqual({k: v for k, v in widened.items() if k != "publishedBefore"}, plain)
        self.assertEqual(
            set(plain),
            {
                "part", "type", "order", "q", "regionCode", "relevanceLanguage",
                "maxResults", "publishedAfter", "key",
            },
        )

    def test_search_published_before_must_be_aware_and_later(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        rows = (
            ("naive", datetime(2026, 10, 12, 0, 0)),
            ("equal", WINDOW_START),
            ("earlier", WINDOW_START - SECOND),
        )
        for label, before in rows:
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    client.search("연애", WINDOW_START, None, NOW, limits(90), before)
        self.assertEqual(fetch.urls, [])
        self.assertFalse(self.path.exists())


class CommentsTest(YouTubeCase):
    """top_comments — commentThreads.list 한 번, 관련도순, 댓글 글만."""

    def comments(
        self, client: YouTubeClient, max_results: int = 10
    ) -> tuple[str, ...] | None:
        return client.top_comments("abcdefghijk", NOW, limits(90), max_results)

    def test_comment_threads_url_carries_relevance_order_and_count(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        self.comments(client)
        parts = urllib.parse.urlsplit(fetch.urls[0])
        self.assertEqual(
            (parts.scheme, parts.netloc, parts.path),
            ("https", "www.googleapis.com", "/youtube/v3/commentThreads"),
        )
        self.assertEqual(
            query_of(fetch.urls[0]),
            {
                "part": "snippet",
                "videoId": "abcdefghijk",
                "order": "relevance",
                "maxResults": "10",
                "textFormat": "plainText",
                "key": "test-key",
            },
        )

    def test_comment_threads_cost_one_unit_through_ledger(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch, searches(1, NOW - SECOND))
        self.assertEqual(self.ledger.usage(NOW), Usage(1, 100))
        self.comments(client)
        self.assertEqual(self.ledger.usage(NOW), Usage(1, 101))
        self.assertEqual(
            self.stored()[-1],
            {"at": "2026-10-12T12:00:00+00:00", "call": "commentThreads.list", "units": 1},
        )
        self.assertEqual(len(fetch.urls), 1)

    def test_comment_threads_held_by_unit_ceiling(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch, searches(99, NOW - SECOND) + videos(100, NOW - SECOND))
        with self.assertRaises(QuotaExhausted) as caught:
            self.comments(client)
        self.assert_held(
            caught.exception, "commentThreads.list", "units", 10000, DAILY_QUOTA_UNITS
        )
        self.assertEqual(fetch.urls, [])
        self.assertEqual(len(self.stored()), 199)

    def test_comments_disabled_returns_none_and_still_counts(self) -> None:
        fetch = FakeFetch((403, google_error("commentsDisabled")))
        client = self.client(fetch)
        self.assertIsNone(self.comments(client))
        self.assertEqual(COMMENTS_DISABLED, "HTTP 403 commentsDisabled")
        self.assertEqual(self.ledger.usage(NOW), Usage(0, 1))
        self.assertEqual([entry["call"] for entry in self.stored()], ["commentThreads.list"])

    def test_other_403_on_comments_raises(self) -> None:
        client = self.client(FakeFetch((403, google_error("quotaExceeded"))))
        with self.assertRaises(YouTubeError) as caught:
            self.comments(client)
        exc = caught.exception
        self.assertEqual((exc.call, exc.reason), ("commentThreads.list", "HTTP 403 quotaExceeded"))
        self.assertEqual(self.ledger.usage(NOW), Usage(0, 1))

    def test_top_comments_returns_texts_only(self) -> None:
        fetch = FakeFetch(
            threads(
                thread("첫 댓글", author="가나다", channel="UCfirst00000000000000000"),
                thread("둘째 댓글", author="라마바", channel="UCsecond0000000000000000"),
            )
        )
        result = self.comments(self.client(fetch))
        self.assertEqual(result, ("첫 댓글", "둘째 댓글"))
        self.assertIsInstance(result, tuple)
        flat = repr(result)
        for hidden in ("가나다", "라마바", "UCfirst", "UCsecond", "작성자이름", "UCauthor"):
            self.assertNotIn(hidden, flat)

    def test_malformed_comment_items_are_skipped(self) -> None:
        no_top = thread("x")
        no_top["snippet"] = {"videoId": "abcdefghijk"}
        top_not_dict = thread("x")
        top_not_dict["snippet"] = {"topLevelComment": "글"}
        inner_not_dict = thread("x")
        inner_not_dict["snippet"] = {"topLevelComment": {"snippet": ["글"]}}
        fetch = FakeFetch(
            threads(
                thread("하나"),
                "항목이 글자",
                {"snippet": None},
                no_top,
                top_not_dict,
                inner_not_dict,
                thread(42),
                thread(None),
                thread(["목록"]),
                thread("둘"),
            )
        )
        self.assertEqual(self.comments(self.client(fetch)), ("하나", "둘"))

    def test_comment_items_not_a_list_raise(self) -> None:
        body = json.dumps({"items": {"0": thread("하나")}}).encode("utf-8")
        client = self.client(FakeFetch((200, body)))
        with self.assertRaises(YouTubeError) as caught:
            self.comments(client)
        exc = caught.exception
        self.assertEqual(
            (exc.call, exc.reason), ("commentThreads.list", "HTTP 200 items 가 목록이 아닙니다")
        )

    def test_comment_lone_surrogate_becomes_replacement(self) -> None:
        fetch = FakeFetch(threads(thread("앞\ud800뒤")))
        self.assertEqual(self.comments(self.client(fetch)), ("앞�뒤",))

    def test_max_results_out_of_bounds_calls_nothing(self) -> None:
        fetch = FakeFetch()
        client = self.client(fetch)
        for bad in (0, 101, True):
            with self.subTest(max_results=bad):
                with self.assertRaises(ValueError):
                    self.comments(client, bad)
        self.assertEqual(fetch.urls, [])
        self.assertFalse(self.path.exists())
        self.comments(client, 100)
        self.assertEqual(query_of(fetch.urls[0])["maxResults"], "100")

    def test_comment_network_error_hides_key(self) -> None:
        client = self.client(FakeFetch(lambda url: OSError(f"연결 실패: {url}")))
        with self.assertRaises(YouTubeError) as caught:
            self.comments(client)
        exc = caught.exception
        self.assertEqual(exc.call, "commentThreads.list")
        self.assertIn("key=<YOUTUBE_API_KEY>", exc.reason)
        self.assertNotIn(KEY, exc.reason)
        self.assertNotIn(KEY, str(exc))
        self.assertIsNone(exc.__cause__)
        self.assertTrue(exc.__suppress_context__)

    def test_ledger_file_with_comment_calls_loads(self) -> None:
        seed(self.path, [(NOW - SECOND, "commentThreads.list", 1)] + searches(1, NOW - SECOND))
        self.assertEqual(QuotaLedger(self.path).usage(NOW), Usage(1, 101))


GET_PATH = "/youtube/v3/videos?id=abcdefghijk&key=test-key"


class HttpGetTest(unittest.TestCase):
    """http_get — 날 바이트로 답하는 루프백 서버(tests/loopback.py)에 실제로 요청합니다."""

    def setUp(self) -> None:
        no_proxies(self)

    def serve(self, route: Callable[[str], bytes | None], **kw: Any) -> RawServer:
        server = RawServer(route, **kw)
        self.addCleanup(server.close)
        return server

    def assert_request(self, server: RawServer) -> None:
        self.assertEqual(len(server.heads), 1, server.heads)
        [head] = server.heads
        self.assertTrue(head.startswith(b"GET " + GET_PATH.encode() + b" HTTP/1.1\r\n"), head)
        self.assertIn(b"\r\nAccept: application/json\r\n", head)

    def test_http_error_becomes_its_code_and_body_s037(self) -> None:
        body = b'{"error": {"code": 403, "errors": [{"reason": "quotaExceeded"}]}}'
        server = self.serve(lambda target: response(403, body, reason="Forbidden"))
        result = http_get(server.url + GET_PATH, 12.5)
        self.assertEqual(result, (403, body))
        self.assert_request(server)

    def test_ok_response_becomes_its_status_and_body_s037(self) -> None:
        body = b'{"items": []}'
        server = self.serve(lambda target: response(200, body))
        result = http_get(server.url + GET_PATH, 12.5)
        self.assertEqual(result, (200, body))
        self.assert_request(server)

    def test_no_content_response_keeps_its_status_s047(self) -> None:
        # 200 이 아닌 2xx — 상태를 200 으로 바꾸지 않고 응답의 것 그대로 돌려줍니다
        server = self.serve(lambda target: response(204))
        result = http_get(server.url + GET_PATH, 12.5)
        self.assertEqual(result, (204, b""))
        self.assert_request(server)


if __name__ == "__main__":
    unittest.main()
