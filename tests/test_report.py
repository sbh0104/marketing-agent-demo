"""결과 화면 테스트 — report.py 가 저장소와 로그만 읽고, 로그의 이유는 이름표로만 옮기는지.

계약 '결과 화면 — `report.py` (Phase 7D)' 절. 표시 글 mark() 는 `<script>` · `"` · `&` 를 담아 화면에
날 글자로 나오면 바로 보이고, `~` 로 끝나 어느 표시도 다른 표시의 일부가 되지 않습니다.
"""
from __future__ import annotations

import unittest

import agent.run as run
from agent.guard import decide_post
from agent.poster import DRY_RUN, NO_COMMENT
from agent.report import (
    OTHER,
    REASON_LABELS,
    REASON_PREFIXES,
    WHERE_LABELS,
    reason_label,
    where_label,
)
from agent.writer import NO_CONCERN, NO_SCENE


def mark(field: str) -> str:
    """표시 글 — 화면에 나오면 이스케이프된 꼴로만 나와야 합니다."""
    return f'<script>"&MRK-{field}~'


class TestLabels(unittest.TestCase):
    """이름표 목록 — 정해 둔 코드 · 머리말만 이름표, 나머지는 OTHER (헌법 12조 근접 표본)."""

    def test_listed_codes_get_labels(self) -> None:
        expected = {
            "channel_cooldown": "같은 채널 대기 중",
            "daily_cap": "하루 상한에 닿음",
            "duplicate_video": "이미 처리한 영상",
            "not_in_allowlist": "허용 목록 밖이라 게시하지 않음",
            "invalid_video": "영상 주소를 읽을 수 없음",
            "dry_run": "테스트 실행 — 저장만",
            "no_comment": "댓글 없음",
            "config_rejected": "설정 거절로 저장만",
            "unavailable": "영상을 볼 수 없음",
        }
        self.assertEqual(REASON_LABELS, expected)
        for code, label in expected.items():
            with self.subTest(code=code):
                self.assertEqual(reason_label(code), label)
        # 트래커 결정 1 의 문장 그대로
        self.assertEqual(reason_label("not_in_allowlist"), "허용 목록 밖이라 게시하지 않음")

    def test_producer_constants_are_listed(self) -> None:
        prefixes = [prefix for prefix, _ in REASON_PREFIXES]
        self.assertIn(NO_SCENE, prefixes)
        self.assertIn(NO_CONCERN, prefixes)
        codes = (
            NO_COMMENT,
            DRY_RUN,
            run.CONFIG_REJECTED,
            decide_post("not a url", (), True).reason,
            decide_post("abcdefghijk", (), True).reason,
        )
        for code in codes:
            with self.subTest(code=code):
                self.assertIn(code, REASON_LABELS)
        stages = (run.STAGE_CLASSIFY, run.STAGE_TRIGGER, run.STAGE_WRITE, run.STAGE_POST)
        for stage in stages:
            with self.subTest(stage=stage):
                self.assertIn(stage, WHERE_LABELS)

    def test_writer_reason_shapes_get_labels(self) -> None:
        cases = (
            (f"{NO_SCENE} — 1차: 답을 읽을 수 없습니다", "작성 건너뜀 — 짚을 장면 없음"),
            (
                "검사 두 번 탈락 — 1차: 글자 수 30자 — 40–120자여야 합니다 / 2차: …",
                "검사 두 번 탈락",
            ),
            ("claude 호출 실패: " + mark("server"), "AI 호출 오류 (Claude)"),
            ("jev 검사 호출 실패: " + mark("server"), "AI 호출 오류 (jev 검사)"),
            ("jev 검사 응답 이상: " + mark("q"), "AI 응답 이상 (jev 검사)"),
        )
        for reason, label in cases:
            with self.subTest(reason=reason):
                self.assertEqual(reason_label(reason), label)
                self.assertNotIn("MRK", reason_label(reason))

    def test_near_miss_reasons_fall_to_other(self) -> None:
        samples = (
            "channel_cooldown2",
            " channel_cooldown",
            "channel_cooldown ",
            "Channel_cooldown",
            "channel-cooldown",
            "ｃhannel_cooldown",  # 전각 c (U+FF43)
            " 재료에 장면 없음",
            "재료에장면 없음",
            "재료에 장면",
            "검사 두 번 통과 못함",
            "jev 검사 실패",
            "Claude 호출 실패: X",
        )
        for reason in samples:
            with self.subTest(reason=reason):
                self.assertEqual(reason_label(reason), OTHER)

    def test_near_miss_green_reasons(self) -> None:
        samples = (
            ("channel_cooldown", "같은 채널 대기 중"),
            ("daily_cap", "하루 상한에 닿음"),
            ("unavailable", "영상을 볼 수 없음"),
            ("재료에 장면 없음 — 1차: 답을 읽을 수 없습니다", "작성 건너뜀 — 짚을 장면 없음"),
            ("claude 호출 실패: RuntimeError: " + mark("server"), "AI 호출 오류 (Claude)"),
            ("재료에 장면 없음표", "작성 건너뜀 — 짚을 장면 없음"),
        )
        for reason, label in samples:
            with self.subTest(reason=reason):
                self.assertEqual(reason_label(reason), label)
                self.assertNotIn("MRK", reason_label(reason))

    def test_where_labels_and_near_misses(self) -> None:
        self.assertEqual(
            WHERE_LABELS,
            {
                "classify": "판별 단계 오류",
                "run.classify": "판별 단계 오류",
                "run.trigger": "타이밍 단계 오류",
                "commentThreads.list": "인기 댓글을 받지 못함",
                "writer.claude": "AI 호출 오류 (Claude)",
                "writer.jev": "AI 호출 오류 (jev 검사)",
                "run.write": "작성 단계 오류",
                "poster": "게시 단계 오류",
                "run.post": "게시 단계 오류",
            },
        )
        self.assertEqual(where_label("writer.claude"), "AI 호출 오류 (Claude)")
        self.assertEqual(where_label("run.post"), "게시 단계 오류")
        samples = (
            "writer.claude2",
            " run.post",
            "Run.post",
            "run_post",
            "ｒun.post",  # 전각 r (U+FF52)
            mark("where"),
            "videos.list",  # 감시기 _fail 의 ERROR 에는 video= 가 없습니다
        )
        for where in samples:
            with self.subTest(where=where):
                self.assertEqual(where_label(where), OTHER)
                self.assertNotIn("MRK", where_label(where))


if __name__ == "__main__":
    unittest.main()
