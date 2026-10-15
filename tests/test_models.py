"""영상 기록 모양 테스트 — 검사, JSON 왕복, 시간대."""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone

from agent.models import (
    MODES,
    RESULTS,
    VIDEO_ID_RE,
    CommentDraft,
    Judgement,
    Memory,
    PostAttempt,
    Verdict,
    VideoRecord,
    ViewSample,
)

UTC = timezone.utc
KST = timezone(timedelta(hours=9))
T0 = datetime(2026, 10, 12, 3, 0, tzinfo=UTC)


def full_record() -> VideoRecord:
    return VideoRecord(
        video_id="abcdefghijk",
        channel_id="UC123",
        title="연락 텀 때문에 불안한 썸",
        description="설명\n두 줄",
        published_at=T0,
        detected_at=T0 + timedelta(minutes=5),
        keyword="썸",
        view_history=[ViewSample(T0, 900), ViewSample(T0 + timedelta(hours=1), 1200)],
        classification=Judgement(Verdict.YES, "연애 고민", T0),
        trigger=Judgement(Verdict.HOLD, "조회수 부족", T0),
        comment=CommentDraft(
            concern="연락 빈도",
            text="연락 텀이 길면 불안할 수 있어요.",
            at=T0,
            self_check=Judgement(Verdict.YES, "자연스러움", T0),
        ),
        attempts=[
            PostAttempt(T0, "test", "saved", "dry_run"),
            PostAttempt(T0 + timedelta(hours=2), "live", "reserved"),
        ],
    )


def minimal_record(**changes: object) -> VideoRecord:
    fields: dict[str, object] = {
        "video_id": "abcdefghijk",
        "channel_id": "UC123",
        "title": "제목",
        "description": "",
        "published_at": T0,
        "detected_at": T0,
        "keyword": "썸",
    }
    fields.update(changes)
    return VideoRecord(**fields)


class RoundTripTest(unittest.TestCase):
    def test_full_record_survives_json_round_trip(self) -> None:
        record = full_record()
        text = json.dumps(record.to_dict(), ensure_ascii=False)
        self.assertEqual(VideoRecord.from_dict(json.loads(text)), record)
        self.assertEqual(record.attempts[-1].result, "reserved")

    def test_minimal_record_defaults(self) -> None:
        record = minimal_record()
        self.assertEqual(record.view_history, [])
        self.assertEqual(record.attempts, [])
        self.assertIsNone(record.classification)
        self.assertIsNone(record.trigger)
        self.assertIsNone(record.comment)
        self.assertEqual(VideoRecord.from_dict(record.to_dict()), record)

    def test_default_lists_are_not_shared(self) -> None:
        first, second = minimal_record(), minimal_record()
        first.attempts.append(PostAttempt(T0, "test", "saved"))
        self.assertEqual(second.attempts, [])

    def test_kst_input_serialises_as_utc(self) -> None:
        at = datetime(2026, 10, 12, 21, 30, tzinfo=KST)
        data = ViewSample(at, 10).to_dict()
        self.assertEqual(data["at"], "2026-10-12T12:30:00+00:00")
        self.assertEqual(ViewSample.from_dict(data).at, at)

    def test_enum_serialises_as_value(self) -> None:
        self.assertEqual(Judgement(Verdict.NO, "x", T0).to_dict()["verdict"], "no")

    def test_attempt_defaults(self) -> None:
        attempt = PostAttempt.from_dict({"at": T0.isoformat(), "mode": "live", "result": "posted"})
        self.assertEqual(attempt, PostAttempt(T0, "live", "posted", "", None))


class ValidationTest(unittest.TestCase):
    def test_naive_datetime_is_rejected(self) -> None:
        naive = datetime(2026, 10, 12, 3, 0)
        with self.assertRaises(ValueError):
            ViewSample(naive, 1)
        with self.assertRaises(ValueError):
            minimal_record(detected_at=naive)
        with self.assertRaises(ValueError):
            PostAttempt(naive, "live", "posted")
        with self.assertRaises(ValueError):
            ViewSample.from_dict({"at": "2026-10-12T03:00:00", "count": 1})

    def test_short_video_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            minimal_record(video_id="abcdefghij")

    def test_non_ascii_video_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            minimal_record(video_id="내-테스트-영상-ID")
        with self.assertRaises(ValueError):
            minimal_record(video_id="abcdefghij가")

    def test_empty_channel_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            minimal_record(channel_id="")

    def test_attempt_mode_and_result_must_pair(self) -> None:
        for mode, result in (("live", "saved"), ("test", "posted"), ("test", "reserved")):
            with self.subTest(mode=mode, result=result):
                with self.assertRaises(ValueError):
                    PostAttempt(T0, mode, result)
        with self.assertRaises(ValueError):
            PostAttempt(T0, "dry", "saved")

    def test_every_listed_pair_is_accepted(self) -> None:
        for mode in MODES:
            for result in RESULTS[mode]:
                with self.subTest(mode=mode, result=result):
                    self.assertEqual(PostAttempt(T0, mode, result).result, result)
        self.assertEqual(RESULTS["live"], ("reserved", "posted", "failed"))

    def test_view_count_must_be_non_negative_int(self) -> None:
        with self.assertRaises(ValueError):
            ViewSample(T0, -1)
        with self.assertRaises(ValueError):
            ViewSample(T0, True)

    def test_verdict_must_be_enum(self) -> None:
        with self.assertRaises(ValueError):
            Judgement.from_dict({"verdict": "maybe", "reason": "", "at": T0.isoformat()})

    def test_from_dict_rejects_unknown_key(self) -> None:
        data = minimal_record().to_dict()
        data["extra"] = 1
        with self.assertRaises(ValueError):
            VideoRecord.from_dict(data)
        with self.assertRaises(ValueError):
            ViewSample.from_dict({"at": T0.isoformat(), "count": 1, "views": 1})

    def test_from_dict_rejects_missing_key(self) -> None:
        data = minimal_record().to_dict()
        del data["channel_id"]
        with self.assertRaises(ValueError):
            VideoRecord.from_dict(data)
        with self.assertRaises(ValueError):
            PostAttempt.from_dict({"at": T0.isoformat(), "mode": "live"})

    def test_video_id_pattern(self) -> None:
        self.assertIsNotNone(VIDEO_ID_RE.fullmatch("abc_DEF-123"))
        self.assertIsNone(VIDEO_ID_RE.fullmatch("abc_DEF-1234"))


class MemoryTest(unittest.TestCase):
    """기억 칸 — 작성 · 게시가 멈춘 까닭(계약 3절, Phase 7C)."""

    FIELDS = {"reason", "stage", "at", "tries", "top_comments"}

    def good(self) -> dict[str, object]:
        return {
            "reason": "재료에 장면 없음",
            "stage": "run.write",
            "at": T0,
            "tries": 1,
            "top_comments": 2,
        }

    def test_memory_round_trips(self) -> None:
        memory = Memory("재료에 장면 없음", "run.write", T0, 1, 2)
        record = minimal_record(memory=memory)
        data = record.to_dict()
        self.assertEqual(set(data["memory"]), self.FIELDS)
        loaded = VideoRecord.from_dict(json.loads(json.dumps(data, ensure_ascii=False)))
        self.assertEqual(loaded, record)
        self.assertEqual(loaded.memory, memory)
        self.assertEqual(
            data["memory"],
            {
                "reason": "재료에 장면 없음",
                "stage": "run.write",
                "at": "2026-10-12T03:00:00+00:00",
                "tries": 1,
                "top_comments": 2,
            },
        )

    def test_record_without_memory_key_still_loads(self) -> None:
        data = minimal_record().to_dict()
        self.assertIn("memory", data)
        self.assertIsNone(data["memory"])
        del data["memory"]
        self.assertIsNone(VideoRecord.from_dict(data).memory)
        self.assertEqual(VideoRecord.from_dict(data), minimal_record())

    def test_memory_is_the_only_added_record_key(self) -> None:
        # 되돌리기 고정 — memory 를 떼면 옛 from_dict 가 받는 키만 남습니다(옛 키 목록은 base 에서 잰 값)
        base = {
            "attempts",
            "channel_id",
            "classification",
            "comment",
            "description",
            "detected_at",
            "keyword",
            "published_at",
            "title",
            "trigger",
            "video_id",
            "view_history",
        }
        self.assertEqual(set(minimal_record().to_dict()) - {"memory"}, base)

    def test_memory_rejects_bad_values(self) -> None:
        naive = datetime(2026, 10, 12, 3, 0)
        bad = {
            "empty reason": ({"reason": ""}, {"reason": ""}),
            "empty stage": ({"stage": ""}, {"stage": ""}),
            "naive at": ({"at": naive}, {"at": naive.isoformat()}),
            "tries -1": ({"tries": -1}, {"tries": -1}),
            "tries bool": ({"tries": True}, {"tries": True}),
            "top_comments text": ({"top_comments": "1"}, {"top_comments": "1"}),
        }
        for label, (direct, stored) in bad.items():
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    Memory(**{**self.good(), **direct})
                data = minimal_record(memory=Memory(**self.good())).to_dict()
                data["memory"].update(stored)
                with self.assertRaises(ValueError):
                    VideoRecord.from_dict(data)
        keys = {
            "unknown key": lambda memory: memory.update(extra=1),
            "missing key": lambda memory: memory.pop("tries"),
        }
        for label, edit in keys.items():
            with self.subTest(label):
                data = minimal_record(memory=Memory(**self.good())).to_dict()
                edit(data["memory"])
                with self.assertRaises(ValueError):
                    Memory.from_dict(data["memory"])
                with self.assertRaises(ValueError):
                    VideoRecord.from_dict(data)


class VerdictTest(unittest.TestCase):
    def test_values(self) -> None:
        self.assertEqual([v.value for v in Verdict], ["yes", "no", "hold"])


if __name__ == "__main__":
    unittest.main()
