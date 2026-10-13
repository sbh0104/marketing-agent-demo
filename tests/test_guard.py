"""허용 목록 가드 테스트 — 행 G1–G7, 영상 주소 읽기, 엄격한 주소 읽기(ship-check · HC1 재현 입력)."""
from __future__ import annotations

import inspect
import unittest

from agent.guard import PostDecision, allowed_video_ids, decide_post, video_id_from_ref

VID = "abcdefghijk"
OTHER = "zyxwvutsrqp"
PLACEHOLDER = "https://youtu.be/내-테스트-영상-ID"
ALLOWED = [f"https://youtu.be/{VID}"]
REPRO_A = "AAAAAAAAAAA"  # ship-check 재현의 허용된 데모 영상
REPRO_B = "BBBBBBBBBBB"  # ship-check 재현의 남의 영상

# 계약 5절 형식의 이웃 모양 — 허용 목록에 A 가 있어도 모두 invalid_video
REJECTED_REFS = (
    f"https://youtu.be/{REPRO_A}/../{REPRO_B}",
    f"https://youtu.be/{REPRO_A}/%2e%2e/{REPRO_B}",
    f"https://www.youtube.com/watch?v={REPRO_A}&v={REPRO_B}",
    f"https://www.youtube.com/shorts/{REPRO_A}/../../watch?v={REPRO_B}",
    f"https://evil.com\\@youtu.be/{REPRO_A}",
    f"https://youtu.be/{REPRO_A}/x",
    f"https://www.youtube.com/shorts/{REPRO_A}/x",
    f"https://www.youtube.com/shorts/{REPRO_A}//",
    f"https://youtu.be/./{REPRO_A}",
    f"https://www.youtube.com/./watch?v={REPRO_A}",
    f"https://www.youtube.com/watch?v=&v={REPRO_A}",
    f"https://youtu.be/%41{REPRO_A[1:]}",
    f"https://www.youtube.com/watch?%76={REPRO_B}&v={REPRO_A}",
    f"https://www.youtube.com/watch?v={REPRO_A}%26v%3D{REPRO_B}",
    f"https://www.youtube.com/watch?v={REPRO_A}&x=a\\b",
    f"https://evil.example@youtu.be/{REPRO_A}",
    f"https://youtu.be:443/{REPRO_A}",
    # HC1 인터뷰(2026-10-13) 재현 입력 — 유튜브는 쿼리의 v(B)를 재생합니다
    "https://youtu.be/AAAAAAAAAAA?v=BBBBBBBBBBB",
    "https://www.youtube.com/shorts/AAAAAAAAAAA?v=BBBBBBBBBBB",
    "https://youtu.be/AAAAAAAAAAA?%76=BBBBBBBBBBB",
    "https://youtu.be/AAAAAAAAAAA?si=x&v=BBBBBBBBBBB",
    f"https://youtu.be/{REPRO_A}?v=",
    f"https://m.youtube.com/shorts/{REPRO_A}/?feature=share&v={REPRO_B}",
    # 쿼리의 ; 도 & 처럼 나눕니다 — 서버가 ; 로 나누면 B 가 숨어 있는 모양 (HTML 복사의 &amp; 포함)
    f"https://youtu.be/{REPRO_A}?x=1;v={REPRO_B}",
    f"https://youtu.be/{REPRO_A}?si=x&amp;v={REPRO_B}",
    f"https://www.youtube.com/shorts/{REPRO_A}?feature=share;v={REPRO_B}",
    f"https://www.youtube.com/watch?x=1;v={REPRO_B}&v={REPRO_A}",
    f"https://youtu.be/{REPRO_A}?x=1;y=2;v={REPRO_B}",
    f"https://www.youtube.com/shorts/{REPRO_A}?a=1;b=2;v={REPRO_B}",
    # ship-report R7 — 경로가 정확히 /watch 가 아닌 watch 닮은꼴
    f"https://www.youtube.com/watchx?v={REPRO_A}",
    f"https://www.youtube.com/watch/?v={REPRO_A}",
)

# 계약 5절 형식 — 모두 REPRO_A 로 읽혀야 합니다 (양성 대조)
ACCEPTED_REFS = (
    REPRO_A,
    f"https://youtu.be/{REPRO_A}",
    f"https://youtu.be/{REPRO_A}?si=abc123",
    f"HTTPS://YOUTU.BE/{REPRO_A}",
    f"https://www.youtube.com/watch?v={REPRO_A}&t=30s",
    f"https://www.youtube.com/watch?feature=share&v={REPRO_A}",
    f"https://www.youtube.com/watch?v=%41{REPRO_A[1:]}",
    f"https://www.youtube.com/watch?v={REPRO_A}&ab_channel=%EC%97%B0%EC%95%A0",
    f"https://www.youtube.com/watch?v={REPRO_A}&pp=ygUJ7Jew7JWg%3D%3D",
    f"https://youtube.com/watch?v={REPRO_A}",
    f"https://m.youtube.com/watch?v={REPRO_A}",
    f"https://www.youtube.com/shorts/{REPRO_A}",
    f"https://www.youtube.com/shorts/{REPRO_A}/",
    f"http://youtube.com/shorts/{REPRO_A}?feature=share",
    # HC1 — v 가 아닌 매개변수는 계속 무시하고, ; 는 & 와 같은 구분
    "https://youtu.be/AAAAAAAAAAA?si=xYz12",
    f"https://youtu.be/{REPRO_A}?si=x&t=30&feature=shared",
    f"https://www.youtube.com/shorts/{REPRO_A}?si=x&feature=share",
    f"https://www.youtube.com/watch?v={REPRO_A};x=1",
)


class GuardRowsTest(unittest.TestCase):
    def assert_decision(self, decision: PostDecision, live: bool, reason: str) -> None:
        self.assertIs(decision.live, live)
        self.assertEqual(decision.reason, reason)
        self.assertEqual(decision.mode, "live" if live else "test")

    def test_g1_allowlisted_dry_run_off_is_live(self) -> None:
        decision = decide_post(VID, ALLOWED, dry_run=False)
        self.assert_decision(decision, True, "allowlisted")
        self.assertEqual(decision.video_id, VID)

    def test_g2_allowlisted_dry_run_on_is_test(self) -> None:
        decision = decide_post(VID, ALLOWED, dry_run=True)
        self.assert_decision(decision, False, "dry_run")
        self.assertEqual(decision.video_id, VID)

    def test_g3_not_allowlisted_dry_run_off_is_test(self) -> None:
        decision = decide_post(OTHER, ALLOWED, dry_run=False)
        self.assert_decision(decision, False, "not_in_allowlist")
        self.assertEqual(decision.video_id, OTHER)

    def test_g4_not_allowlisted_dry_run_on_reports_allowlist_cause(self) -> None:
        self.assert_decision(decide_post(OTHER, ALLOWED, dry_run=True), False, "not_in_allowlist")

    def test_g5_placeholder_allowlist_allows_nothing(self) -> None:
        self.assertEqual(allowed_video_ids([PLACEHOLDER]), frozenset())
        for ref in (VID, f"https://youtu.be/{VID}", PLACEHOLDER):
            for dry_run in (False, True):
                with self.subTest(ref=ref, dry_run=dry_run):
                    decision = decide_post(ref, [PLACEHOLDER], dry_run=dry_run)
                    self.assertFalse(decision.live)
                    self.assertEqual(decision.mode, "test")
                    self.assertIn(decision.reason, ("not_in_allowlist", "invalid_video"))
        self.assert_decision(decide_post(VID, [PLACEHOLDER], False), False, "not_in_allowlist")

    def test_g5_empty_allowlist_allows_nothing(self) -> None:
        self.assert_decision(decide_post(VID, [], dry_run=False), False, "not_in_allowlist")

    def test_g6_entry_and_ref_in_different_url_forms(self) -> None:
        forms = (
            VID,
            f"https://youtu.be/{VID}",
            f"https://www.youtube.com/watch?v={VID}",
            f"https://youtube.com/watch?v={VID}&t=42s",
            f"https://m.youtube.com/watch?v={VID}",
            f"https://www.youtube.com/shorts/{VID}",
        )
        for entry in forms:
            for ref in forms:
                with self.subTest(entry=entry, ref=ref):
                    self.assert_decision(decide_post(ref, [entry], False), True, "allowlisted")

    def test_g7_unparseable_or_foreign_ref_is_test(self) -> None:
        allowed = [VID]
        refs = (
            "",
            "not a video",
            "abcdefghij",
            f"https://evil.example/watch?v={VID}",
            f"https://youtube.com.evil.example/watch?v={VID}",
            f"https://youtube.com@evil.example/watch?v={VID}",
            f"ftp://youtube.com/watch?v={VID}",
            f"https://www.youtube.com/embed/{VID}",
            "AAAAAAAAAAAB",
            "AAAAAAAAAAA&v=BBBBBBBBBBB",
            "https://youtube-nocookie.com/watch?v=AAAAAAAAAAA",
        )
        for ref in refs:
            for dry_run in (False, True):
                with self.subTest(ref=ref, dry_run=dry_run):
                    decision = decide_post(ref, allowed, dry_run)
                    self.assert_decision(decision, False, "invalid_video")
                    self.assertIsNone(decision.video_id)

    def test_signature_has_exactly_three_parameters(self) -> None:
        params = list(inspect.signature(decide_post).parameters)
        self.assertEqual(params, ["video_ref", "allowed_videos", "dry_run"])

    def test_non_bool_dry_run_is_test_mode(self) -> None:
        for value in (None, 0, "", 0.0, "false", []):
            with self.subTest(dry_run=value):
                self.assert_decision(decide_post(VID, ALLOWED, value), False, "dry_run")


class VideoIdFromRefTest(unittest.TestCase):
    def test_table(self) -> None:
        table = (
            (VID, VID),
            (f"  {VID}\n", VID),
            (f"https://youtu.be/{VID}?si=abc123", VID),
            (f"https://www.youtube.com/watch?v={VID}&t=30s", VID),
            (f"https://m.youtube.com/watch?v={VID}", VID),
            (f"https://WWW.YouTube.com/watch?v={VID}", VID),
            (f"https://www.youtube.com/shorts/{VID}", VID),
            (f"http://youtube.com/shorts/{VID}?feature=share", VID),
            (f"https://evil.example/watch?v={VID}", None),
            (f"https://youtube.com.evil.example/watch?v={VID}", None),
            (f"ftp://youtube.com/watch?v={VID}", None),
            ("", None),
            ("https://www.youtube.com/watch", None),
            ("https://www.youtube.com/watch?v=short", None),
            ("https://youtu.be/", None),
            (PLACEHOLDER, None),
            ("http://[::1", None),
            ("AAAAAAAAAAAB", None),
            ("AAAAAAAAAAA&v=BBBBBBBBBBB", None),
            ("https://youtube-nocookie.com/watch?v=AAAAAAAAAAA", None),
        )
        for ref, expected in table:
            with self.subTest(ref=ref):
                self.assertEqual(video_id_from_ref(ref), expected)

    def test_allowed_ids_drop_unparseable_entries(self) -> None:
        entries = [PLACEHOLDER, f"https://youtu.be/{VID}", OTHER, "nonsense"]
        self.assertEqual(allowed_video_ids(entries), frozenset({VID, OTHER}))


class StrictAddressTest(unittest.TestCase):
    def test_rejected_addresses_are_invalid_even_when_allowlisted(self) -> None:
        for ref in REJECTED_REFS:
            with self.subTest(ref=ref):
                self.assertIsNone(video_id_from_ref(ref))
            for dry_run in (False, True):
                with self.subTest(ref=ref, dry_run=dry_run):
                    decision = decide_post(ref, [REPRO_A], dry_run)
                    self.assertIs(decision.live, False)
                    self.assertEqual(decision.reason, "invalid_video")
                    self.assertIsNone(decision.video_id)

    def test_rejected_addresses_never_become_allowlist_entries(self) -> None:
        self.assertEqual(allowed_video_ids(REJECTED_REFS), frozenset())
        for ref in REJECTED_REFS:
            with self.subTest(ref=ref):
                decision = decide_post(REPRO_A, [ref], False)
                self.assertIs(decision.live, False)
                self.assertEqual(decision.reason, "not_in_allowlist")

    def test_contract_forms_still_read(self) -> None:
        for ref in ACCEPTED_REFS:
            with self.subTest(ref=ref):
                self.assertEqual(video_id_from_ref(ref), REPRO_A)
                decision = decide_post(ref, [REPRO_A], False)
                self.assertIs(decision.live, True)
                self.assertEqual(decision.reason, "allowlisted")

    def test_canonical_watch_url_reads_back(self) -> None:
        for vid in (VID, OTHER, REPRO_A, "a-b_c-d_e-f"):
            url = f"https://www.youtube.com/watch?v={vid}"
            with self.subTest(url=url):
                self.assertEqual(video_id_from_ref(url), vid)
                self.assertIs(decide_post(url, [vid], False).live, True)


if __name__ == "__main__":
    unittest.main()
