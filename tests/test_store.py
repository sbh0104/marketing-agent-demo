"""저장소 테스트 — 행 S1–S17, 이유 우선순위, 파일 보존."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.config import LimitsConfig
from agent.models import CommentDraft, PostAttempt, VideoRecord
from agent.store import PostCheck, Store, StoreError

NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
LIMITS = LimitsConfig(10, 24.0, 100)
HOUR = timedelta(hours=1)
OK = PostCheck(True, "ok")
DUPLICATE = PostCheck(False, "duplicate_video")
CAP = PostCheck(False, "daily_cap")
COOLDOWN = PostCheck(False, "channel_cooldown")


def vid(n: int) -> str:
    return f"vid{n:08d}"


def record(
    video_id: str,
    channel_id: str = "UCfresh",
    detected_at: datetime = NOW - 3 * HOUR,
    comment: CommentDraft | None = None,
) -> VideoRecord:
    return VideoRecord(
        video_id=video_id,
        channel_id=channel_id,
        title="연락 텀 때문에 불안한 썸",
        description="",
        published_at=NOW - 5 * HOUR,
        detected_at=detected_at,
        keyword="썸",
        comment=comment,
    )


class StoreCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.path = self.dir / "data" / "videos.json"
        self.store = Store(self.path)

    def add(self, n: int, channel: str) -> str:
        video_id = vid(n)
        self.store.put(record(video_id, channel))
        return video_id

    def posted(self, n: int, channel: str, at: datetime) -> str:
        video_id = self.add(n, channel)
        self.store.reserve_live(video_id, at)
        self.store.resolve_live(video_id, "posted", at)
        return video_id

    def failed(self, n: int, channel: str, at: datetime) -> str:
        video_id = self.add(n, channel)
        self.store.reserve_live(video_id, at)
        self.store.resolve_live(video_id, "failed", at, "버튼 없음", "logs/screenshots/x.png")
        return video_id

    def reserved(self, n: int, channel: str, at: datetime) -> str:
        video_id = self.add(n, channel)
        self.store.reserve_live(video_id, at)
        return video_id

    def saved(self, n: int, channel: str, at: datetime) -> str:
        video_id = self.add(n, channel)
        self.store.save_test(video_id, at, "dry_run")
        return video_id

    def check(
        self, video_id: str, channel: str, live: bool, store: Store | None = None
    ) -> PostCheck:
        return (store or self.store).check_post(video_id, channel, NOW, LIMITS, live)


class CheckPostRowsTest(StoreCase):
    def test_s1_fresh_video_fresh_channel_under_cap_is_ok(self) -> None:
        for live in (True, False):
            with self.subTest(live=live, stored=False):
                self.assertEqual(self.check(vid(99), "UCnew", live), OK)
        for n in range(1, 10):
            self.posted(n, f"UC{n}", NOW - HOUR)
        self.add(50, "UCnew")
        for live in (True, False):
            with self.subTest(live=live, stored=True):
                self.assertEqual(self.check(vid(50), "UCnew", live), OK)

    def test_s2_live_check_with_posted_live_attempt_is_duplicate(self) -> None:
        video_id = self.posted(1, "UC1", NOW - 30 * HOUR)
        self.assertEqual(self.check(video_id, "UC1", live=True), DUPLICATE)
        self.assertEqual(self.check(video_id, "UC1", live=False), DUPLICATE)

    def test_s3_live_check_with_only_failed_live_attempt_is_duplicate(self) -> None:
        video_id = self.failed(1, "UC1", NOW - HOUR)
        self.assertEqual(self.check(video_id, "UC1", live=True), DUPLICATE)

    def test_s4_test_check_with_saved_test_attempt_is_duplicate(self) -> None:
        video_id = self.saved(1, "UC1", NOW - HOUR)
        self.assertEqual(self.check(video_id, "UC1", live=False), DUPLICATE)

    def test_s5_live_check_with_only_saved_test_attempt_is_ok(self) -> None:
        video_id = self.saved(1, "UC1", NOW - HOUR)
        self.assertEqual(self.check(video_id, "UC1", live=True), OK)

    def test_s6_cap_reached_by_posts_on_other_channels(self) -> None:
        for n in range(1, 11):
            self.posted(n, f"UC{n}", NOW - n * HOUR)
        self.assertEqual(self.check(vid(50), "UCnew", live=True), CAP)
        self.assertEqual(self.check(vid(50), "UCnew", live=False), CAP)

    def test_s7_post_exactly_24h_old_no_longer_counts(self) -> None:
        for n in range(1, 10):
            self.posted(n, f"UC{n}", NOW - n * HOUR)
        self.posted(10, "UC10", NOW - 24 * HOUR)
        self.assertEqual(self.check(vid(50), "UCnew", live=True), OK)

    def test_s8_failed_attempts_do_not_count_toward_cap(self) -> None:
        for n in range(1, 11):
            self.failed(n, f"UC{n}", NOW - HOUR)
        self.assertEqual(self.check(vid(50), "UCnew", live=True), OK)

    def test_s9_same_channel_within_cooldown(self) -> None:
        self.posted(1, "UCsame", NOW - 23 * HOUR)
        self.assertEqual(self.check(vid(50), "UCsame", live=True), COOLDOWN)
        self.assertEqual(self.check(vid(50), "UCsame", live=False), COOLDOWN)

    def test_s10_same_channel_exactly_cooldown_hours_ago_is_ok(self) -> None:
        self.posted(1, "UCsame", NOW - 24 * HOUR)
        self.assertEqual(self.check(vid(50), "UCsame", live=True), OK)

    def test_s11_different_channel_within_cooldown_is_ok(self) -> None:
        self.posted(1, "UCother", NOW - HOUR)
        self.assertEqual(self.check(vid(50), "UCsame", live=True), OK)

    def test_s12_reservation_survives_reload_without_resolve(self) -> None:
        video_id = self.reserved(1, "UC1", NOW - HOUR)
        reloaded = Store(self.path)
        self.assertEqual(self.check(video_id, "UC1", live=True, store=reloaded), DUPLICATE)
        self.assertEqual(reloaded.get(video_id).attempts[-1].result, "reserved")

    def test_s13_unresolved_reservations_count_toward_cap_and_cooldown(self) -> None:
        self.reserved(1, "UCsame", NOW - HOUR)
        self.assertEqual(self.check(vid(50), "UCsame", live=True), COOLDOWN)
        for n in range(2, 11):
            self.reserved(n, f"UC{n}", NOW - HOUR)
        self.assertEqual(self.check(vid(50), "UCnew", live=True), CAP)

    def test_s14_failed_resolution_stops_counting_posted_keeps_counting(self) -> None:
        for n in range(1, 11):
            self.reserved(n, f"UC{n}", NOW - HOUR)
        for n in range(1, 11):
            self.store.resolve_live(vid(n), "failed", NOW - HOUR, "실패")
        self.assertEqual(self.check(vid(50), "UCnew", live=True), OK)
        self.assertEqual(self.check(vid(50), "UC1", live=True), OK)
        for n in range(11, 21):
            self.reserved(n, f"UC{n}", NOW - HOUR)
            self.store.resolve_live(vid(n), "posted", NOW - HOUR)
        self.assertEqual(self.check(vid(50), "UCnew", live=True), CAP)
        self.assertEqual(self.check(vid(50), "UC11", live=False), CAP)

    def test_s14_posted_resolution_keeps_channel_wait(self) -> None:
        self.reserved(1, "UCsame", NOW - HOUR)
        self.store.resolve_live(vid(1), "posted", NOW - HOUR)
        self.assertEqual(self.check(vid(50), "UCsame", live=True), COOLDOWN)

    def test_s15_put_refuses_changed_attempts(self) -> None:
        video_id = self.posted(1, "UC1", NOW - HOUR)
        before = self.path.read_bytes()

        wiped = self.store.get(video_id)
        wiped.attempts.clear()
        with self.assertRaises(ValueError):
            self.store.put(wiped)

        edited = self.store.get(video_id)
        edited.attempts[0] = PostAttempt(NOW - HOUR, "live", "failed")
        with self.assertRaises(ValueError):
            self.store.put(edited)

        carrying = record(vid(2), "UC2")
        carrying.attempts.append(PostAttempt(NOW - HOUR, "test", "saved"))
        with self.assertRaises(ValueError):
            self.store.put(carrying)

        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(self.store.get(vid(2)))
        self.assertEqual(self.store.get(video_id).attempts[0].result, "posted")

    def test_s15_put_with_unchanged_attempts_updates_other_fields(self) -> None:
        video_id = self.posted(1, "UC1", NOW - HOUR)
        updated = self.store.get(video_id)
        updated.title = "새 제목"
        self.store.put(updated)
        self.assertEqual(Store(self.path).get(video_id), updated)

    def test_s16_reserve_live_refuses_second_live_attempt(self) -> None:
        reserved = self.reserved(1, "UC1", NOW - HOUR)
        posted = self.posted(2, "UC2", NOW - HOUR)
        failed = self.failed(3, "UC3", NOW - HOUR)
        for video_id in (reserved, posted, failed):
            with self.subTest(video_id=video_id):
                with self.assertRaises(ValueError):
                    self.store.reserve_live(video_id, NOW)
                self.assertEqual(len(self.store.get(video_id).attempts), 1)

    def test_s16_reserve_live_after_test_save_is_allowed(self) -> None:
        video_id = self.saved(1, "UC1", NOW - HOUR)
        self.store.reserve_live(video_id, NOW)
        results = [att.result for att in self.store.get(video_id).attempts]
        self.assertEqual(results, ["saved", "reserved"])

    def test_s17_resolve_live_without_open_reservation(self) -> None:
        fresh = self.add(1, "UC1")
        posted = self.posted(2, "UC2", NOW - HOUR)
        saved = self.saved(3, "UC3", NOW - HOUR)
        for video_id in (fresh, posted, saved):
            with self.subTest(video_id=video_id):
                with self.assertRaises(ValueError):
                    self.store.resolve_live(video_id, "posted", NOW)

    def test_s17_resolve_live_with_bad_result(self) -> None:
        video_id = self.reserved(1, "UC1", NOW - HOUR)
        for result in ("saved", "reserved", "ok"):
            with self.subTest(result=result):
                with self.assertRaises(ValueError):
                    self.store.resolve_live(video_id, result, NOW)
        self.assertEqual(self.store.get(video_id).attempts[-1].result, "reserved")

    def test_resolve_live_replaces_reservation(self) -> None:
        video_id = self.reserved(1, "UC1", NOW - HOUR)
        self.store.resolve_live(video_id, "failed", NOW, "버튼 없음", "logs/screenshots/a.png")
        attempts = Store(self.path).get(video_id).attempts
        self.assertEqual(
            attempts, [PostAttempt(NOW, "live", "failed", "버튼 없음", "logs/screenshots/a.png")]
        )

    def test_duplicate_outranks_daily_cap(self) -> None:
        for n in range(1, 11):
            self.posted(n, f"UC{n}", NOW - HOUR)
        self.assertEqual(self.check(vid(1), "UC1", live=True), DUPLICATE)

    def test_naive_now_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.store.check_post(vid(1), "UC1", datetime(2026, 10, 12, 12, 0), LIMITS, True)


class PersistenceTest(StoreCase):
    def test_fresh_store_reads_equal_record(self) -> None:
        video_id = self.saved(1, "UC1", NOW - HOUR)
        self.assertEqual(Store(self.path).get(video_id), self.store.get(video_id))

    def test_put_order_does_not_change_bytes(self) -> None:
        first = Store(self.dir / "a" / "videos.json")
        second = Store(self.dir / "b" / "videos.json")
        records = [record(vid(n), f"UC{n}") for n in (3, 1, 2)]
        for item in records:
            first.put(item)
        for item in reversed(records):
            second.put(item)
        self.assertEqual(first.path.read_bytes(), second.path.read_bytes())

    def test_file_is_utf8_with_trailing_newline(self) -> None:
        self.add(1, "UC1")
        text = self.path.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("}\n"))
        self.assertIn("연락 텀 때문에 불안한 썸", text)
        self.assertNotIn("\\u", text)
        self.assertEqual(json.loads(text)["schema_version"], 1)

    def test_no_tmp_file_is_left(self) -> None:
        self.reserved(1, "UC1", NOW - HOUR)
        self.store.resolve_live(vid(1), "posted", NOW)
        self.assertEqual(sorted(p.name for p in self.path.parent.iterdir()), ["videos.json"])

    def test_missing_file_stays_absent_until_first_mutation(self) -> None:
        self.assertFalse(self.path.exists())
        self.check(vid(1), "UC1", live=True)
        self.store.get(vid(1))
        self.store.records()
        self.store.comments()
        self.assertFalse(self.path.exists())
        self.add(1, "UC1")
        self.assertTrue(self.path.exists())

    def test_get_returns_a_copy(self) -> None:
        video_id = self.add(1, "UC1")
        copy = self.store.get(video_id)
        copy.title = "바뀐 제목"
        copy.attempts.append(PostAttempt(NOW, "test", "saved"))
        stored = self.store.get(video_id)
        self.assertEqual(stored.title, "연락 텀 때문에 불안한 썸")
        self.assertEqual(stored.attempts, [])

    def test_put_keeps_its_own_copy(self) -> None:
        item = record(vid(1), "UC1")
        self.store.put(item)
        item.title = "밖에서 바꿈"
        self.assertEqual(self.store.get(vid(1)).title, "연락 텀 때문에 불안한 썸")

    def test_records_sorted_by_detected_at_then_id(self) -> None:
        self.store.put(record(vid(3), "UC3", detected_at=NOW - 2 * HOUR))
        self.store.put(record(vid(2), "UC2", detected_at=NOW - 1 * HOUR))
        self.store.put(record(vid(1), "UC1", detected_at=NOW - 2 * HOUR))
        self.assertEqual([r.video_id for r in self.store.records()], [vid(1), vid(3), vid(2)])

    def test_comments_sorted_by_comment_time_then_id(self) -> None:
        self.store.put(record(vid(3), "UC3", comment=CommentDraft("c", "셋", NOW - HOUR)))
        self.store.put(record(vid(1), "UC1", comment=CommentDraft("c", "하나", NOW - HOUR)))
        self.store.put(record(vid(2), "UC2", comment=CommentDraft("c", "둘", NOW - 2 * HOUR)))
        self.store.put(record(vid(4), "UC4"))
        self.assertEqual(self.store.comments(), ["둘", "하나", "셋"])

    def test_unknown_video_mutations_raise(self) -> None:
        with self.assertRaises(ValueError):
            self.store.save_test(vid(1), NOW, "dry_run")
        with self.assertRaises(ValueError):
            self.store.resolve_live(vid(1), "posted", NOW)
        with self.assertRaises(ValueError):
            self.store.reserve_live(vid(1), NOW)
        self.assertFalse(self.path.exists())

    def write(self, text: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text, encoding="utf-8", newline="\n")

    def test_corrupt_json_raises_store_error(self) -> None:
        self.write("{")
        with self.assertRaises(StoreError):
            Store(self.path)

    def test_other_schema_version_raises_store_error(self) -> None:
        self.write(json.dumps({"schema_version": 2, "videos": {}}))
        with self.assertRaises(StoreError):
            Store(self.path)

    def test_non_dict_raises_store_error(self) -> None:
        self.write("[]")
        with self.assertRaises(StoreError):
            Store(self.path)

    def test_key_mismatch_raises_store_error(self) -> None:
        data = {"schema_version": 1, "videos": {vid(2): record(vid(1)).to_dict()}}
        self.write(json.dumps(data))
        with self.assertRaises(StoreError):
            Store(self.path)

    def test_invalid_record_raises_store_error(self) -> None:
        bad = record(vid(1)).to_dict()
        bad["channel_id"] = ""
        self.write(json.dumps({"schema_version": 1, "videos": {vid(1): bad}}))
        with self.assertRaises(StoreError):
            Store(self.path)

    def test_corrupt_file_is_not_reset(self) -> None:
        self.write("{")
        with self.assertRaises(StoreError):
            Store(self.path)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{")


if __name__ == "__main__":
    unittest.main()
