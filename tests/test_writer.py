"""댓글 작성 테스트 — 코드 검사(글자 수 · 링크 · 반복), 자체 검사 기준, 답 읽기."""
from __future__ import annotations

import json
import unicodedata
import unittest

from agent.config import CommentConfig
from agent.writer import (
    CHECK_QUESTIONS,
    REPEAT_MIN_CHARS,
    code_failures,
    link_fragment,
    parse_output,
    repeated_run,
    self_check_failure,
)

CONFIG = CommentConfig(40, 120, "test-writer-model", 0.5)
# 이전에 쓴 댓글 — 40–120자, 링크 없음, 아래 다른 고정 댓글과 겹치지 않음을 테스트 안에서 확인합니다
PREV = (
    "저도 연락 텀 때문에 불안했던 적이 있어요. 연애사주에서 서로 표현 방식이 다르다는 얘기를 듣고"
    " 마음이 놓였어요."
)
PASSING = {"mentions_scene": 0.9, "reads_like_ad": 0.1, "follows_concern": 0.8}


def reply(concern: str, comment: str) -> str:
    return json.dumps({"concern": concern, "comment": comment}, ensure_ascii=False)


class CheckTest(unittest.TestCase):
    def test_length_is_counted_in_characters_not_bytes(self) -> None:
        text = "가" * 100
        self.assertEqual(len(text.encode("utf-8")), 300)
        self.assertEqual(code_failures(text, [], CONFIG), [])
        # 받침 있는 음절은 NFD 로 세 글자 — 읽을 때 NFC 로 합쳐 음절 수로 셉니다
        decomposed = unicodedata.normalize("NFD", "한" * 41)
        self.assertEqual(len(decomposed), 123)
        parsed = parse_output(reply("연락 텀", decomposed))
        self.assertIsNotNone(parsed)
        _, comment = parsed
        self.assertEqual(len(comment), 41)
        self.assertEqual(code_failures(comment, [], CONFIG), [])

    def test_length_bounds_come_from_config(self) -> None:
        self.assertEqual(
            code_failures("가" * 39, [], CONFIG), ["글자 수 39자 — 40–120자여야 합니다"]
        )
        for length in (40, 120):
            with self.subTest(length=length):
                self.assertEqual(code_failures("가" * length, [], CONFIG), [])
        self.assertEqual(
            code_failures("가" * 121, [], CONFIG), ["글자 수 121자 — 40–120자여야 합니다"]
        )
        narrow = CommentConfig(50, 60, "test-writer-model", 0.5)
        self.assertEqual(
            code_failures("가" * 49, [], narrow), ["글자 수 49자 — 50–60자여야 합니다"]
        )
        self.assertEqual(code_failures("가" * 50, [], narrow), [])
        self.assertEqual(code_failures("가" * 60, [], narrow), [])
        self.assertEqual(
            code_failures("가" * 61, [], narrow), ["글자 수 61자 — 50–60자여야 합니다"]
        )

    def test_link_shapes_are_rejected(self) -> None:
        probes = (
            "https://example.com",
            "HTTPS://EXAMPLE.COM",
            "www.example.com",
            "youtu.be/abcdefghijk",
            "bit.ly/3abc",
            "naver.me",
            "naver . me",
            "ｎａｖｅｒ．ｍｅ",
            "youtu​.be",
            "example。com",
            "연애사주.com",
            "연애사주.kr에서 봤어요",
            "사주앱.com",
            "연애사주．ｃｏｍ",
            "연애사주 . com",
            "연애사주。com",
            "naver(.)me",
            "naver[.]com",
            "youtu·be",
            "kakao·com",
            "naver͏.me",
            "naver️.me",
            "연애사주ㅤ.com",
            "naver⠀.me",
            "@연애사주공식",
            "192.168.0.1",
        )
        for probe in probes:
            with self.subTest(probe=probe):
                self.assertIsNotNone(link_fragment(probe))

    def test_link_free_text_passes(self) -> None:
        probes = (
            "1.5배 더",
            "10:30에",
            "ENFP. 그래서 저도",
            "MBTI 얘기",
            "연애사주 봤어요!",
            "P.S. 저도",
            "A/S 받듯이",
            "장면·말이 와닿았어요",
            "3.5km 걸어서",
            "연애사주 봤는데, MBTI랑 비슷했어요",
        )
        for probe in probes:
            with self.subTest(probe=probe):
                self.assertIsNone(link_fragment(probe))

    def test_code_checks_report_every_failure_in_order(self) -> None:
        self.assertEqual(code_failures(PREV, [], CONFIG), [])
        text = PREV + " 자세한 건 naver.me 에서 보시면 돼요. " + "정말 그랬어요. " * 6
        length = len(text)
        self.assertGreater(length, 120)
        self.assertEqual(
            code_failures(text, [PREV], CONFIG),
            [
                f"글자 수 {length}자 — 40–120자여야 합니다",
                "링크·주소 모양이 들어 있습니다: r.me",
                "이전 댓글과 겹칩니다: "
                "저도연락텀때문에불안했던적이있어요연애사주에서서로표현방식이다르다는얘기를듣고"
                "마음이놓였어요",
            ],
        )

    def test_repeated_sentence_inside_new_comment_is_found(self) -> None:
        previous = ["완전 공감해요.", "저도 연락 텀 때문에 불안했던 적 있어요."]
        text = "영상 보면서 생각났는데 저도 연락 텀 때문에 불안했던 적 있어요. 연애사주가 도움이 됐어요."
        self.assertEqual(
            repeated_run(text, previous, REPEAT_MIN_CHARS), "저도연락텀때문에불안했던적있어요"
        )

    def test_repeat_ignores_spacing_punctuation_and_width(self) -> None:
        self.assertEqual(
            repeated_run(
                "저도·연락·텀·때문에·불안했던·적·있어요",
                ["저도 연락 텀 때문에 불안했던 적 있어요"],
                REPEAT_MIN_CHARS,
            ),
            "저도연락텀때문에불안했던적있어요",
        )
        self.assertEqual(
            repeated_run(
                "ＥＮＦＰ라서 연락이 늦으면 서운했어요",
                ["enfp라서 연락이 늦으면 서운했어요!!"],
                REPEAT_MIN_CHARS,
            ),
            "enfp라서연락이늦으면서운했어요",
        )

    def test_shared_stock_phrase_is_not_a_repeat(self) -> None:
        self.assertIsNone(
            repeated_run(
                "연애사주 봤는데 썸 타는 시기엔 기다림이 필요하대요",
                ["연애사주 봤는데 이별 뒤에는 혼자만의 시간이 약이래요"],
                REPEAT_MIN_CHARS,
            )
        )

    def test_equal_short_comment_is_a_repeat(self) -> None:
        self.assertEqual(repeated_run("공감돼요!!", ["공감 돼요"], REPEAT_MIN_CHARS), "공감돼요")

    def test_repeat_run_length_comes_from_argument(self) -> None:
        text = "저는 연락 텀 때문에 불안했던 적이 많아요"
        previous = ["친구도 연락 텀 때문에 불안했던 적이 있대요"]
        self.assertIsNone(repeated_run(text, previous, 13))
        self.assertEqual(repeated_run(text, previous, 12), "연락텀때문에불안했던적이")

    def test_self_check_passes_at_threshold(self) -> None:
        answer = {"mentions_scene": 0.5, "reads_like_ad": 0.5, "follows_concern": 0.5}
        self.assertIsNone(self_check_failure(answer, 0.5))

    def test_each_question_can_fail_alone(self) -> None:
        cases = {
            "mentions_scene": (0.25, "자체 검사 미달 — 영상 속 장면·말 언급 0.25"),
            "reads_like_ad": (0.75, "자체 검사 미달 — 광고처럼 읽힘 0.75"),
            "follows_concern": (0.25, "자체 검사 미달 — 영상 고민과 이어짐 0.25"),
        }
        self.assertEqual(set(cases), set(CHECK_QUESTIONS))
        self.assertIsNone(self_check_failure(PASSING, 0.5))
        for name, (probability, reason) in cases.items():
            with self.subTest(name):
                self.assertEqual(self_check_failure({**PASSING, name: probability}, 0.5), reason)

    def test_ad_question_is_inverted(self) -> None:
        self.assertEqual(
            self_check_failure({**PASSING, "reads_like_ad": 0.75}, 0.5),
            "자체 검사 미달 — 광고처럼 읽힘 0.75",
        )
        self.assertIsNone(self_check_failure({**PASSING, "reads_like_ad": 0.0}, 0.5))

    def test_ad_question_boundary_holds_at_every_two_decimal_floor(self) -> None:
        # 그냥 < 로 비교하면 1 − P 의 부동소수 오차로 20개 하한에서 경계가 떨어집니다
        for i in range(1, 100):
            floor = float(f"0.{i:02d}")
            probability = round(1 - floor, 2)
            with self.subTest(floor=floor):
                answer = {
                    "mentions_scene": 1.0,
                    "reads_like_ad": probability,
                    "follows_concern": 1.0,
                }
                self.assertIsNone(self_check_failure(answer, floor))
                if i <= 98:
                    above = probability + 0.01
                    self.assertEqual(
                        self_check_failure({**answer, "reads_like_ad": above}, floor),
                        f"자체 검사 미달 — 광고처럼 읽힘 {above:.2f}",
                    )

    def test_parse_output_reads_fenced_json(self) -> None:
        raw = "```json\n" + reply("연락 텀", PREV) + "\n```"
        self.assertEqual(parse_output(raw), ("연락 텀", PREV))

    def test_parse_output_rejects_bad_shapes(self) -> None:
        cases = (
            ("prose", "죄송하지만 이 영상에는 댓글을 쓸 수 없습니다."),
            ("brace_less_array", "[1, 2]"),
            ("missing_key", '{"concern": "연락 텀"}'),
            ("non_str_value", '{"concern": "연락 텀", "comment": 5}'),
            ("empty_comment", '{"concern": "연락 텀", "comment": "  "}'),
            ("deep_nesting", '{"concern": ' + "[" * 100_000 + "]" * 100_000 + "}"),
        )
        for label, raw in cases:
            with self.subTest(label):
                self.assertIsNone(parse_output(raw))

    def test_parse_output_makes_concern_one_line_and_comment_nfc(self) -> None:
        decomposed = unicodedata.normalize("NFD", PREV)
        self.assertNotEqual(decomposed, PREV)
        parsed = parse_output(reply(" 연락 텀이\n길어지는  썸 ", decomposed + "\n"))
        self.assertEqual(parsed, ("연락 텀이 길어지는 썸", PREV))


if __name__ == "__main__":
    unittest.main()
