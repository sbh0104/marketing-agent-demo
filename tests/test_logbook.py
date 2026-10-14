"""로그 형식 테스트 — 한 줄 형식, 되읽기, 쓰기, 줄 경계 글자, 날 글자 범주, read_log."""
from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.logbook import KST, REQUIRED_FIELDS, Event, Logbook, format_line, parse_line, read_log
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


def raw(char: str) -> bool:
    """계약 7절의 날 글자 — 범주 L · M · N · P · S 와 U+0020. logbook 의 판정과 따로 셉니다."""
    return char == " " or unicodedata.category(char)[0] in "LMNPS"


# Phase 1 ship-report R1 · Phase 1A 인터뷰 재현 입력 — 로그를 가리거나 터미널에 가짜 줄을 그리거나 쓰기를 터뜨린 제목
REPRO_TITLES = ("x\x00y\x00z", "a\x1b[2Kb", "x" + chr(0xD800) + "y", "a" + chr(0x3000) + "b")
POSTED = {"video": "AAAAAAAAAAA", "mode": "live", "result": "posted", "reason": "allowlisted"}


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
            ("x\x00y\x00z", 'reason="x\\u0000y\\u0000z"'),
            ("a\x1b[2Kb", 'reason="a\\u001b[2Kb"'),
            ("x" + chr(0xD800) + "y", 'reason="x\\ud800y"'),
            ("a" + chr(0x3000) + "b", 'reason="a\\u3000b"'),
            ("a" + chr(0xA0) + "b", 'reason="a\\u00a0b"'),
            ("x\x7fy", 'reason="x\\u007fy"'),
            ("x\x01", 'reason="x\\u0001"'),
            ("x" + chr(0x202E) + "y", 'reason="x\\u202ey"'),
            ("x" + chr(0x200D) + "y", 'reason="x\\u200dy"'),
            ("x" + chr(0xE0001) + "y", 'reason="x\\udb40\\udc01y"'),
            ("x" + chr(0xF0000) + "y", 'reason="x\\udb80\\udc00y"'),
            (chr(0x1F600), "reason=" + chr(0x1F600)),
            ("e" + chr(0x301), "reason=e" + chr(0x301)),
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


class RawCharacterTest(unittest.TestCase):
    """Phase 1A 결정 3 — 값에 날 글자로 남는 것은 범주 L · M · N · P · S 와 U+0020 뿐."""

    def test_every_code_point_round_trips_and_only_the_raw_set_stays_raw(self) -> None:
        # | 가 서로게이트 반쪽끼리 짝을 이루지 못하게 가릅니다
        value = "|".join(map(chr, range(0x110000)))
        line = format_line(AT, Event.STOP, {"reason": value})
        self.assertEqual([c for c in set(line) if not raw(c)], [])
        self.assertEqual(parse_line(line)[2], {"reason": value})

    def test_separate_surrogate_halves_read_back_as_one_character(self) -> None:
        value = chr(0xD83D) + chr(0xDE00)
        self.assertEqual(len(value), 2)
        self.assertEqual(stop(value), 'reason="\\ud83d\\ude00"')
        line = format_line(AT, Event.STOP, {"reason": value})
        self.assertEqual(parse_line(line)[2], {"reason": chr(0x1F600)})

    def write_repro_log(self) -> tuple[Path, str, str]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "agent.log"
        echo = io.StringIO()
        book = Logbook(path, clock=lambda: AT, echo=echo)
        for title in REPRO_TITLES:
            book.write(Event.DETECT, **{**DETECT, "title": title})
        post = book.write(Event.POST, **POSTED)
        return path, post, echo.getvalue()

    def test_repro_titles_leave_no_raw_control_or_surrogate_and_read_back(self) -> None:
        path, _, echoed = self.write_repro_log()
        data = path.read_bytes()
        text = data.decode("utf-8")
        self.assertEqual([c for c in set(text) if c != "\n" and not raw(c)], [])
        self.assertNotIn(b"\x00", data)
        self.assertNotIn(b"\x1b", data)
        self.assertNotIn("\x1b", echoed)
        expected = [
            *((AT, Event.DETECT, {**DETECT, "title": title}) for title in REPRO_TITLES),
            (AT, Event.POST, POSTED),
        ]
        self.assertEqual(read_log(path), expected)

    @unittest.skipUnless(Path("/usr/bin/grep").exists(), "GNU grep 이 /usr/bin/grep 에 없습니다")
    def test_gnu_grep_shows_the_post_line_after_repro_titles(self) -> None:
        path, post, _ = self.write_repro_log()
        # 셸의 grep 은 이 기계에서 ugrep 이라(경험 장부 E-004) GNU grep 을 경로로 부릅니다
        result = subprocess.run(
            ["/usr/bin/grep", "posted", str(path)],
            capture_output=True,
            env={**os.environ, "LC_ALL": "C.UTF-8"},
            check=False,
        )
        # 종료 코드 0 만으로는 모릅니다 — 고치기 전에도 0 이었고 stderr 에 binary file matches 였습니다
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, (post + "\n").encode("utf-8"))
        self.assertNotIn(b"inary", result.stdout + result.stderr)

    def test_old_line_with_raw_control_char_still_parses(self) -> None:
        self.assertEqual(
            parse_line("2026-10-12T21:30:00+09:00 STOP reason=x\x00y"),
            (AT, Event.STOP, {"reason": "x\x00y"}),
        )


class ReadLogTest(unittest.TestCase):
    """Phase 1A 결정 3 — 로그를 읽는 단 하나의 방법 read_log."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "agent.log"
        self.good = format_line(AT, Event.STOP, {"reason": "끝"})

    def write(self, text: str) -> None:
        self.path.write_text(text, encoding="utf-8", newline="\n")

    def assert_error(self, text: str, prefix: str) -> str:
        self.write(text)
        with self.assertRaises(ValueError) as caught:
            read_log(self.path)
        message = str(caught.exception)
        self.assertTrue(message.startswith(prefix), message)
        return message

    def test_hidden_post_in_hangul_title_reads_as_one_detect(self) -> None:
        title = f"갅{FORGED}갅"
        Logbook(self.path, clock=lambda: AT).write(Event.DETECT, **{**DETECT, "title": title})
        # 함정은 살아 있습니다 — latin-1 로 풀고 splitlines 로 나누면 갅(ea b0 85)의 0x85 가 줄 경계
        segments = self.path.read_bytes().decode("latin-1").splitlines()
        _, event, fields = parse_line(segments[1])
        self.assertIs(event, Event.POST)
        self.assertEqual(fields["result"], "posted")
        self.assertEqual(read_log(self.path), [(AT, Event.DETECT, {**DETECT, "title": title})])

    def test_invalid_utf8_is_an_error_with_its_line_number(self) -> None:
        book = Logbook(self.path, clock=lambda: AT)
        book.write(Event.STOP, reason="첫 줄")
        book.write(Event.STOP, reason="갅 둘째")
        self.path.write_bytes(self.path.read_bytes().replace("갅".encode("utf-8"), b"\xea\xb0"))
        with self.assertRaises(ValueError) as caught:
            read_log(self.path)
        self.assertIn("2번째 줄", str(caught.exception))
        self.assertIn("UTF-8", str(caught.exception))

    def test_only_newline_splits_lines(self) -> None:
        # 옛 쓰기의 모양 — 따옴표 안에 splitlines 의 줄 경계가 날 글자로 있습니다
        value = "a" + chr(0x2028) + "b\x85c"
        self.write('2026-10-12T21:30:00+09:00 STOP reason="' + value + '"' + "\n")
        self.assertEqual(read_log(self.path), [(AT, Event.STOP, {"reason": value})])

    def test_bad_line_is_an_error_with_its_number_not_skipped(self) -> None:
        self.assert_error(f"{self.good}\ngarbage\n{self.good}\n", "2번째 줄: ")

    def test_empty_lines_are_skipped_and_still_counted(self) -> None:
        self.write(f"{self.good}\n\n{self.good}\n")
        self.assertEqual(len(read_log(self.path)), 2)
        self.assert_error(f"{self.good}\n\ngarbage\n", "3번째 줄: ")

    def test_whitespace_only_line_is_an_error_not_skipped(self) -> None:
        # 빈 줄만 건너뜁니다 — 공백 · 탭 · 폼 피드만 있는 줄은 빈 줄이 아닙니다(계약 7절)
        for blank in (chr(0x20), chr(0x09), chr(0x0C)):
            with self.subTest(line=f"U+{ord(blank):04X}"):
                self.assert_error(f"{self.good}\n{blank}\n", "2번째 줄: ")

    def test_line_break_titles_read_back_as_one_detect_each(self) -> None:
        # 여러 줄짜리 댓글도, 영상 제목에 숨긴 U+2028 도 read_log 의 읽기로 한 사건 한 줄
        titles = ("a\nb", "a" + chr(0x2028) + "b")
        book = Logbook(self.path, clock=lambda: AT)
        for title in titles:
            book.write(Event.DETECT, **{**DETECT, "title": title})
        expected = [(AT, Event.DETECT, {**DETECT, "title": title}) for title in titles]
        self.assertEqual(read_log(self.path), expected)

    def test_last_line_without_newline_is_an_error(self) -> None:
        message = self.assert_error(f"{self.good}\n{self.good}", "2번째 줄: ")
        self.assertIn("줄바꿈", message)
        cut = format_line(AT, Event.POST, POSTED)[:-3]
        self.assert_error(f"{self.good}\n{cut}", "2번째 줄: ")
        # 공백 · 탭 · 폼 피드만 남은 꼬리도 끊긴 줄입니다
        for tail in (chr(0x20), chr(0x09), chr(0x0C)):
            with self.subTest(tail=f"U+{ord(tail):04X}"):
                self.assert_error(f"{self.good}\n{tail}", "2번째 줄: ")

    def test_empty_file_reads_as_no_events(self) -> None:
        for text in ("", "\n"):
            with self.subTest(text=text):
                self.write(text)
                self.assertEqual(read_log(self.path), [])

    def test_missing_file_raises_os_error(self) -> None:
        with self.assertRaises(OSError):
            read_log(self.path.parent / "없는.log")


if __name__ == "__main__":
    unittest.main()
