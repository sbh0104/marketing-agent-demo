"""로그 형식 테스트 — 한 줄 형식, 되읽기, 쓰기, 줄 경계 글자."""
from __future__ import annotations

import io
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.logbook import KST, REQUIRED_FIELDS, Event, Logbook, format_line, parse_line
from agent.models import Verdict

AT = datetime(2026, 10, 12, 12, 30, tzinfo=timezone.utc)
DETECT = {"video": "abcdefghijk", "channel": "UC123", "keyword": "썸", "title": "연락 텀 때문에 불안한 썸"}
# 파이썬이 줄 경계로 세는 글자 전부 — 목록을 손으로 적지 않고 splitlines 에서 얻습니다
SPLITLINES_BREAKS = "".join(
    chr(cp) for cp in range(0x110000) if len(f"a{chr(cp)}b".splitlines()) != 1
)
# HC1 재현 — 제목에 숨겨 가짜 게시 줄을 만들려던 글
FORGED = (
    "2026-10-12T21:30:00+09:00 POST video=BBBBBBBBBBB mode=live result=posted reason=allowlisted"
)


def stop(value: object) -> str:
    """STOP reason 자리에 값을 넣고 그 토큰만 돌려줍니다."""
    return format_line(AT, Event.STOP, {"reason": value}).split(" ", 2)[2]


class FormatLineTest(unittest.TestCase):
    def test_exact_detect_line(self) -> None:
        self.assertEqual(
            format_line(AT, Event.DETECT, DETECT),
            '2026-10-12T21:30:00+09:00 DETECT video=abcdefghijk channel=UC123 keyword=썸 '
            'title="연락 텀 때문에 불안한 썸"',
        )

    def test_rendering_rules(self) -> None:
        table = (
            (None, "reason=-"),
            (True, "reason=true"),
            (False, "reason=false"),
            (Verdict.HOLD, "reason=hold"),
            (Event.POST, "reason=POST"),
            (0, "reason=0"),
            (-42, "reason=-42"),
            (1.5, "reason=1.50"),
            (2.0 / 3.0, "reason=0.67"),
            (datetime(2026, 10, 12, 15, 0, 7, 999, tzinfo=timezone.utc),
             "reason=2026-10-13T00:00:07+09:00"),
            ("bare_value", "reason=bare_value"),
            ("썸", "reason=썸"),
            ("-", 'reason="-"'),
            ("", 'reason=""'),
            ("두 단어", 'reason="두 단어"'),
            ('a"b', 'reason="a\\"b"'),
            ("a=b", 'reason="a=b"'),
            ("a\\b", 'reason="a\\\\b"'),
            ("tab\there", 'reason="tab\\there"'),
            ("x\ny", 'reason="x\\ny"'),
            ("x\ry", 'reason="x\\ry"'),
            ("x\x85y", 'reason="x\\u0085y"'),
            ("x\u2028y", 'reason="x\\u2028y"'),
            ("x\u2029y", 'reason="x\\u2029y"'),
        )
        for value, expected in table:
            with self.subTest(value=value):
                self.assertEqual(stop(value), expected)

    def test_multi_line_value_stays_on_one_line_and_round_trips(self) -> None:
        text = '첫 줄\n둘째 줄 "인용" = 끝\\'
        fields = {"video": "abcdefghijk", "concern": "연락", "text": text}
        line = format_line(AT, Event.COMMENT, fields)
        self.assertNotIn("\n", line)
        at, event, parsed = parse_line(line)
        self.assertEqual(at, AT)
        self.assertEqual(event, Event.COMMENT)
        self.assertEqual(parsed, fields)

    def test_bare_looking_line_breaks_round_trip(self) -> None:
        for value, token in (("x\ny", 'reason="x\\ny"'), ("x\ry", 'reason="x\\ry"')):
            with self.subTest(value=value):
                line = format_line(AT, Event.STOP, {"reason": value})
                self.assertNotIn("\n", line)
                self.assertNotIn("\r", line)
                self.assertEqual(line.split(" ", 2)[2], token)
                self.assertEqual(parse_line(line)[2], {"reason": value})

    def test_extras_sort_after_required(self) -> None:
        line = format_line(AT, Event.SKIP, {"zeta": 1, "reason": "dup", "alpha": 2, "video": "v"})
        self.assertEqual(line.split(" ", 2)[2], "video=v reason=dup alpha=2 zeta=1")

    def test_missing_required_field_names_it(self) -> None:
        fields = dict(DETECT)
        del fields["keyword"]
        with self.assertRaises(ValueError) as caught:
            format_line(AT, Event.DETECT, fields)
        self.assertIn("keyword", str(caught.exception))

    def test_bad_key_is_rejected(self) -> None:
        for key in ("Bad", "1x", "a-b", "", "공백"):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    format_line(AT, Event.STOP, {"reason": "x", key: 1})

    def test_unsupported_value_type(self) -> None:
        with self.assertRaises(TypeError):
            format_line(AT, Event.STOP, {"reason": ["a", "b"]})

    def test_naive_time_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            format_line(datetime(2026, 10, 12, 12, 30), Event.STOP, {"reason": "x"})

    def test_every_event_has_required_fields(self) -> None:
        for event in Event:
            with self.subTest(event=event.value):
                self.assertEqual(event.value, event.name)
                self.assertTrue(REQUIRED_FIELDS[event])
        self.assertEqual(set(REQUIRED_FIELDS), set(Event))
        self.assertEqual(REQUIRED_FIELDS[Event.POST], ("video", "mode", "result", "reason"))

    def test_kst_offset(self) -> None:
        self.assertEqual(KST.utcoffset(None), timedelta(hours=9))


class ParseLineTest(unittest.TestCase):
    def test_round_trip_of_every_value_kind(self) -> None:
        fields = {
            "video": "abcdefghijk",
            "mode": "live",
            "result": "posted",
            "reason": "-",
            "screenshot": None,
            "ok": True,
            "n": 3,
            "ratio": 0.25,
            "space": "a b",
            "empty": "",
        }
        line = format_line(AT, Event.POST, fields)
        at, event, parsed = parse_line(line)
        self.assertEqual((at, event), (AT, Event.POST))
        self.assertEqual(
            parsed,
            {
                "video": "abcdefghijk",
                "mode": "live",
                "result": "posted",
                "reason": "-",
                "screenshot": "-",
                "ok": "true",
                "n": "3",
                "ratio": "0.25",
                "space": "a b",
                "empty": "",
            },
        )
        self.assertEqual(at.utcoffset(), timedelta(hours=9))

    def test_trailing_newline_is_accepted(self) -> None:
        line = format_line(AT, Event.DETECT, DETECT)
        self.assertEqual(parse_line(line + "\n"), parse_line(line))

    def test_malformed_lines(self) -> None:
        good = format_line(AT, Event.STOP, {"reason": "끝"})
        bad = (
            "",
            "garbage",
            "2026-10-12T21:30:00+09:00",
            "2026-10-12T21:30:00 STOP reason=x",
            "2026-10-12T21:30:00+09:00 NOPE reason=x",
            "2026-10-12T21:30:00+09:00 STOP",
            "2026-10-12T21:30:00+09:00 STOP other=x",
            "2026-10-12T21:30:00+09:00 STOP reason=",
            "2026-10-12T21:30:00+09:00 STOP reason=x  extra=y",
            '2026-10-12T21:30:00+09:00 STOP reason="open',
            '2026-10-12T21:30:00+09:00 STOP reason="a"b',
            "2026-10-12T21:30:00+09:00 STOP reason=x reason=y",
            "2026-10-12T21:30:00+09:00 STOP Reason=x",
            good + " ",
            '2026-10-12T21:30:00+09:00 STOP reason="a"_x=y',
            good + "\n\n",
        )
        for line in bad:
            with self.subTest(line=line):
                with self.assertRaises(ValueError):
                    parse_line(line)


class LogbookTest(unittest.TestCase):
    def test_write_creates_dirs_appends_utf8_and_echoes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "logs" / "nested" / "agent.log"
            echo = io.StringIO()
            book = Logbook(path, clock=lambda: AT, echo=echo)
            first = book.write(Event.DETECT, **DETECT)
            second = book.write(Event.STOP, reason="사용자 중단")
            self.assertEqual(first, format_line(AT, Event.DETECT, DETECT))
            expected = first + "\n" + second + "\n"
            self.assertEqual(path.read_bytes(), expected.encode("utf-8"))
            self.assertEqual(echo.getvalue(), expected)

    def test_write_without_echo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agent.log"
            line = Logbook(path, clock=lambda: AT).write(Event.CYCLE, n=1)
            self.assertEqual(path.read_text(encoding="utf-8"), line + "\n")


class LineBreakTest(unittest.TestCase):
    """HC1 인터뷰(2026-10-13) — 줄 경계 글자를 숨긴 값도 한 사건 한 줄로 남고 그대로 되읽혀야 합니다."""

    def test_splitlines_boundaries_are_the_known_ten(self) -> None:
        self.assertEqual(SPLITLINES_BREAKS, "\n\v\f\r\x1c\x1d\x1e\x85\u2028\u2029")

    def test_every_boundary_in_a_title_stays_one_line_and_round_trips(self) -> None:
        for char in SPLITLINES_BREAKS:
            with self.subTest(char=f"U+{ord(char):04X}"):
                fields = {**DETECT, "title": f"제목{char}{FORGED}"}
                line = format_line(AT, Event.DETECT, fields)
                self.assertEqual(line.splitlines(), [line])
                self.assertNotIn(char, line)
                self.assertEqual(parse_line(line), (AT, Event.DETECT, fields))

    def test_log_file_keeps_one_line_per_event(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name)
        book = Logbook(directory / "agent.log", clock=lambda: AT)
        for char in SPLITLINES_BREAKS:
            book.write(Event.DETECT, **{**DETECT, "title": f"제목{char}{FORGED}"})
        lines = (directory / "agent.log").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), len(SPLITLINES_BREAKS))
        for line in lines:
            with self.subTest(line=line):
                self.assertIs(parse_line(line)[1], Event.DETECT)


if __name__ == "__main__":
    unittest.main()
