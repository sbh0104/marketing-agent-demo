"""허용 목록 가드 테스트 — 행 G1–G7 과 영상 주소 읽기."""
from __future__ import annotations

import inspect
import unittest

from agent.guard import PostDecision, allowed_video_ids, decide_post, video_id_from_ref

VID = "abcdefghijk"
OTHER = "zyxwvutsrqp"
PLACEHOLDER = "https://youtu.be/내-테스트-영상-ID"
ALLOWED = [f"https://youtu.be/{VID}"]


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
        )
        for ref, expected in table:
            with self.subTest(ref=ref):
                self.assertEqual(video_id_from_ref(ref), expected)

    def test_allowed_ids_drop_unparseable_entries(self) -> None:
        entries = [PLACEHOLDER, f"https://youtu.be/{VID}", OTHER, "nonsense"]
        self.assertEqual(allowed_video_ids(entries), frozenset({VID, OTHER}))


if __name__ == "__main__":
    unittest.main()
