"""탐지 주기 × 실제 http_get — 루프백 서버의 날 바이트로 깨진 응답 틀 · 리다이렉트 · 느린 응답을 잽니다 (트래커 Phase 7A ③ · R5 의 테스트 입력)."""
from __future__ import annotations

import json
import time
import unittest
import urllib.parse
from collections.abc import Mapping

from agent.logbook import Event
from agent.watcher import CycleReport
from agent.youtube import http_get
from tests.loopback import NEGATIVE_CHUNK, RawServer, chunked, no_proxies, response
from tests.test_watcher import CONFIG, NOW, K, WatcherCase, search_page, video_item, views

ORIGIN = "https://www.googleapis.com"
REDIRECTS = (301, 302, 303, 307, 308)
MARKS = ("MRKmoved", "MRKheader", "MRKelsewhere", "MRKftp", "MRKv6")


class LoopbackFetch:
    """YouTubeClient 의 fetch 자리 — Google 주소를 끝점(search · videos)의 루프백 서버로 돌려
    실제 http_get 으로 보냅니다."""

    def __init__(self, servers: Mapping[str, RawServer], cap: float | None = None) -> None:
        self.servers = servers
        self.cap = cap
        # 주소 가드가 걸린 기록 — _call 이 AssertionError 를 YouTubeError 로 삼키므로 시험 끝에 봅니다
        self.guard_hits: list[str] = []

    def __call__(self, url: str, timeout: float) -> tuple[int, bytes]:
        if not url.startswith(ORIGIN):
            self.guard_hits.append(f"Google 밖의 주소입니다: {url}")
            raise AssertionError(f"Google 밖의 주소입니다: {url}")
        endpoint = urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1]
        target = self.servers[endpoint].url + url[len(ORIGIN):]
        return http_get(target, timeout if self.cap is None else self.cap)


def ok(payload: object) -> bytes:
    return response(200, json.dumps(payload).encode("ascii"))


class WatcherNetworkTest(WatcherCase):
    def setUp(self) -> None:
        super().setUp()
        no_proxies(self)
        self.addCleanup(self.assert_no_guard_hits)

    def assert_no_guard_hits(self) -> None:
        """시험 끝의 self.api 가 LoopbackFetch 면 그 주소 가드가 한 번도 걸리지 않았어야 합니다."""
        if isinstance(self.api, LoopbackFetch):
            self.assertEqual(self.api.guard_hits, [])

    def serve(self, reply: bytes | None, **kw: float) -> RawServer:
        server = RawServer(lambda target: reply, **kw)
        self.addCleanup(server.close)
        return server

    def test_negative_chunk_size_ends_in_one_error_line(self) -> None:
        # 트래커 7A ③ — 덩어리 크기 -2 인 chunked 응답이 주기를 깨뜨리지 않고 ERROR 한 줄입니다
        known_views = ok({"items": [video_item(K, 1100)]})
        empty_search = ok(search_page([]))
        with self.subTest("search 200"):
            self.reset("search 200")
            self.seed(K)
            self.api = LoopbackFetch({
                "search": self.serve(chunked(200, NEGATIVE_CHUNK)),
                "videos": self.serve(known_views),
            })
            report = self.run_cycle()
            [(event, fields), tracked] = self.events()
            self.assertEqual(event, Event.ERROR)
            self.assertEqual((fields["where"], fields["keyword"]), ("search.list", "연애"))
            self.assertTrue(fields["reason"].startswith("network "), fields["reason"])
            self.assertEqual(set(fields), {"where", "reason", "keyword"})
            self.assertEqual(tracked, views(K, 1100, prev=1000))
            self.assertNotIn("test-key", "\n".join(self.raw_lines()))
            self.assertEqual(report, CycleReport(0, (), 1, 0, False, True))
        with self.subTest("search 403"):
            self.reset("search 403")
            self.seed(K)
            self.api = LoopbackFetch({
                "search": self.serve(chunked(403, NEGATIVE_CHUNK)),
                "videos": self.serve(known_views),
            })
            self.run_cycle()
            error = {"where": "search.list", "reason": "HTTP 403", "keyword": "연애"}
            self.assertEqual(self.events(), [(Event.ERROR, error), views(K, 1100, prev=1000)])
        with self.subTest("videos 200"):
            self.reset("videos 200")
            self.seed(K)
            self.api = LoopbackFetch({
                "search": self.serve(empty_search),
                "videos": self.serve(chunked(200, NEGATIVE_CHUNK)),
            })
            report = self.run_cycle()
            [(event, fields)] = self.events()
            self.assertEqual(event, Event.ERROR)
            self.assertEqual(set(fields), {"where", "reason"})
            self.assertEqual(fields["where"], "videos.list")
            self.assertTrue(fields["reason"].startswith("network "), fields["reason"])
            self.assertNotIn("test-key", "\n".join(self.raw_lines()))
            self.assertEqual(self.counts(K), [1000])
            self.assertEqual(report, CycleReport(1, (), 0, 0, False, True))

    def test_redirects_are_not_followed(self) -> None:
        # 트래커 7A ③(나) — 다섯 코드 × 깨진 · 다른 호스트 Location 모두 HTTP 3xx 의 ERROR 한 줄이고,
        # 다른 호스트는 요청을 하나도 받지 않습니다. 표시한 칸 중 Google reason 만 줄에 남습니다.
        elsewhere = self.serve(ok(search_page([])))
        literal = ("ftp://%00/", "http://[", f"{elsewhere.url}/elsewhere")
        marked = (f"{elsewhere.url}/MRKelsewhere", "ftp://%00/MRKftp", "http://[MRKv6")
        google = json.dumps({"error": {"errors": [{"reason": "MRKbody"}]}}).encode("ascii")
        for code in REDIRECTS:
            rows = [
                (location, response(code, headers=[f"Location: {location}"]), f"HTTP {code}")
                for location in literal
            ] + [
                (
                    location,
                    response(
                        code,
                        google,
                        reason="MRKmoved",
                        headers=["X-Mrk: MRKheader", f"Location: {location}"],
                    ),
                    f"HTTP {code} MRKbody",
                )
                for location in marked
            ]
            for n, (location, reply, reason) in enumerate(rows):
                with self.subTest(code=code, location=location, reason=reason):
                    self.reset(f"{code}-{n}")
                    with RawServer(lambda target, reply=reply: reply) as server:
                        self.api = LoopbackFetch({"search": server})
                        self.run_cycle()
                    error = {"where": "search.list", "reason": reason, "keyword": "연애"}
                    self.assertEqual(self.events(), [(Event.ERROR, error)])
                    for line in self.raw_lines():
                        for mark in MARKS:
                            self.assertNotIn(mark, line)
        self.assertEqual(elsewhere.targets, [])
        self.assertEqual(elsewhere.connections, 0)

    def test_drip_fed_response_ends_within_the_cap(self) -> None:
        # R5 — 상한보다 오래 몇 바이트씩 흘려 보내는 검색 응답도 상한 안에 ERROR 한 줄로 끝나고 추적은 돕니다
        self.seed(K)
        body = json.dumps(search_page([])).encode("ascii") + b" " * 200
        slow = response(200, body)
        self.api = LoopbackFetch(
            {
                "search": self.serve(slow, drip_s=0.02, burst=len(slow) - len(body)),
                "videos": self.serve(ok({"items": [video_item(K, 1100)]})),
            },
            cap=1.0,
        )
        started = time.monotonic()
        self.watcher().run(CONFIG, NOW)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 1.8)
        error = {
            "where": "search.list",
            "reason": "network TimeoutError: 요청 전체가 1초 상한을 넘었습니다",
            "keyword": "연애",
        }
        self.assertEqual(self.events(), [(Event.ERROR, error), views(K, 1100, prev=1000)])


if __name__ == "__main__":
    unittest.main()
