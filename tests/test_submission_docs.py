"""제출 문서 테스트 — README · PROCESS.md 가 코드의 프롬프트와 진입점을 그대로 옮겼는지, 실제 실행 기록(logs/sample.log)과 문서가 맞는지 확인합니다."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import agent.run
from agent.classifier import build_questions
from agent.config import ConfigError, load_config
from agent.guard import decide_post
from agent.logbook import read_log
from agent.writer import (
    CHECK_QUESTIONS,
    REWRITE_PROMPT,
    SELF_CHECK_CRITERIA,
    SYSTEM_PROMPT,
    USER_INSTRUCTION,
    WRITE_TOOL,
)
from tests.live_check import count_contacts

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
PROCESS = REPO / "PROCESS.md"
CONFIG = REPO / "config.yaml"
TRACKER = REPO / "plans" / "interview-marketing-agent.md"
CONTRACT = REPO / "docs" / "contracts.md"
SAMPLE_LOG = REPO / "logs" / "sample.log"
ATTRIBUTES = REPO / ".gitattributes"

RUN_COMMAND = "PYTHONPATH=src python3 -m agent.run"
SUITE_COMMAND = (
    "python3 -X warn_default_encoding -W error::EncodingWarning -m unittest discover -s tests -t ."
)

DEMO_URL = "https://www.youtube.com/watch?v=vwogTb6XHGk"
COMMIT_X = "7dd5450"
SAMPLE_SHA256 = "2c99255324a9f537728f25e00e3684765cd1191220c643933e92ae0031bb88e7"
SAMPLE_LINES = 1738
PLACEHOLDER = "https://youtu.be/내-테스트-영상-ID"
BLOCKED_POST = "POST video=C_Ylul6a6y0 mode=test result=saved reason=not_in_allowlist"
BLOCKED_VIDEO = "C_Ylul6a6y0"
CYCLE_LINE = "CYCLE n=1 errors=0 mode=test"
REHEARSED = ("3K82-PjUeP0", "WxXINTXQSd4")
SHAPES = ("scene_first", "question_first", "story_first")
SKIP_REASONS = {
    "comments_disabled": 3,
    "unavailable": 3,
    "검사 두 번 탈락": 3,
    "재료에 장면 없음": 2,
    "재료에 연애 고민 없음": 1,
    "duplicate_video": 1,
}
TABLE_LABELS = (
    ("DETECT", "① 탐지"),
    ("VIEWS", "조회수 표본"),
    ("CLASSIFY", "② 판별 — yes · no · hold"),
    ("TRIGGER", "③ 타이밍 — yes · no · hold"),
    ("COMMENT", "④ 작성"),
    ("SKIP", "건너뜀"),
    ("POST", "⑤ 게시 — saved · rehearsed · posted"),
)
SPLITS = {
    "CLASSIFY": ("verdict", ("yes", "no", "hold")),
    "TRIGGER": ("verdict", ("yes", "no", "hold")),
    "POST": ("result", ("saved", "rehearsed", "posted")),
}
REMAINING_8A = ["7B jev 키가 없을 때 Claude 판단"]
REMAINING_HEADER = "남은 일(트래커의 페이즈 제목):"
LIST_WORDS = ("allowed_videos", "명단", "목록", "allowlist")
APPLICANT_WORD = "지원자"
RECORDING_WORDS = ("녹화", "시연")
POSTED_SHAPES = (
    "게시했",
    "게시를했",
    "게시됐",
    "게시되었",
    "게시하였",
    "게시를하였",
    "올라갔",
    "올렸",
    "달렸",
    "달았",
    "등록했",
    "등록됐",
    "등록되었",
    "result=posted",
    "mode=live",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def squeeze(line: str) -> str:
    """공백을 모두 지우고 소문자로 — 띄어쓰기 · 대소문자만 바꾼 문장도 같은 꼴로 봅니다."""
    return "".join(line.split()).lower()


def committed_list_claims(text: str) -> list[str]:
    """'커밋된 명단에 지원자 영상이 있다' 로 읽힐 줄 — 지원자와 명단 낱말이 한 줄에 함께 있는 줄입니다."""
    return [
        line
        for line in text.splitlines()
        if APPLICANT_WORD in squeeze(line) and any(word in squeeze(line) for word in LIST_WORDS)
    ]


def recording_post_claims(text: str) -> list[str]:
    """'녹화에서 실제 게시를 했다' 로 읽힐 줄 — 녹화 낱말과 게시한 꼴이 한 줄에 함께 있는 줄입니다."""
    return [
        line
        for line in text.splitlines()
        if any(word in squeeze(line) for word in RECORDING_WORDS)
        and any(shape in squeeze(line) for shape in POSTED_SHAPES)
    ]


def remaining_bullets(process: str) -> list[str]:
    """PROCESS '남은 일' 머리줄 뒤, 다음 `## ` 줄까지의 `- ` 줄들 — 머리줄은 꼭 한 번 있어야 합니다."""
    lines = process.splitlines()
    if lines.count(REMAINING_HEADER) != 1:
        raise AssertionError(f"머리줄이 한 번이 아닙니다: {REMAINING_HEADER}")
    bullets: list[str] = []
    for line in lines[lines.index(REMAINING_HEADER) + 1:]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            bullets.append(line[2:])
    return bullets


def sample_log_failures(path: Path) -> list[str]:
    """트래커 Phase 8A 첫 단계의 조건(질문 4 C 로 고친 것)에서 어긋난 것 — 비어 있으면 모두 지킵니다.

    받은 파일 그대로(sha256) · 모든 줄 read_log · 줄 수 · 실제 게시 줄 없음 · 막은 줄 하나 이상 · 연락처 모양 없음.
    read_log 가 거절하면 그 뒤 조건은 보지 않습니다.
    """
    data = path.read_bytes()
    failures: list[str] = []
    if hashlib.sha256(data).hexdigest() != SAMPLE_SHA256:
        failures.append("sha256")
    try:
        rows = read_log(path)
    except ValueError as exc:
        failures.append("read_log: " + str(exc))
        return failures
    if len(rows) != SAMPLE_LINES:
        failures.append("lines")
    if any(fields.get("mode") == "live" for _, _, fields in rows):
        failures.append("mode=live")
    if not any(
        event == "POST"
        and fields.get("mode") == "test"
        and fields.get("result") == "saved"
        and fields.get("reason") == "not_in_allowlist"
        for _, event, fields in rows
    ):
        failures.append("blocked")
    if count_contacts(data.decode("utf-8")) != 0:
        failures.append("contacts")
    return failures


def sample_rows() -> list[tuple]:
    """커밋된 파일 그대로를 read_log 로 읽은 줄들."""
    return read_log(SAMPLE_LOG)


def runs(rows: list[tuple]) -> list[list[tuple]]:
    """줄들을 `START` 줄마다 나눈 실행들."""
    split: list[list[tuple]] = []
    for row in rows:
        if row[1] == "START" or not split:
            split.append([])
        split[-1].append(row)
    return split


def videos(run: list[tuple], event: str, **match: str) -> set[str]:
    """실행 안 그 사건 줄 가운데 `match` 의 칸이 모두 같은 줄들의 영상 ID."""
    return {
        fields["video"]
        for _, name, fields in run
        if name == event and all(fields.get(key) == value for key, value in match.items())
    }


def table_rows(rows: list[tuple]) -> list[str]:
    """PROCESS '실제 실행' 표의 머리줄과 사건별 줄 — 실행마다 그 사건의 줄 수를 셉니다."""
    split = runs(rows)
    if len(split) != 2:
        raise AssertionError(f"실행이 둘이 아닙니다: {len(split)}")
    t1, t2 = (
        next(at for at, name, _ in run if name == "START").strftime("%H:%M:%S") for run in split
    )
    lines = [f"| 줄 | 사전 점검 ({t1}) | 녹화 실행 ({t2}) |"]
    for event, label in TABLE_LABELS:
        cells: list[str] = []
        for run in split:
            fields = [found for _, name, found in run if name == event]
            n = len(fields)
            if event in SPLITS:
                key, values = SPLITS[event]
                a, b, c = (sum(found.get(key) == value for found in fields) for value in values)
                if a + b + c != n:
                    raise AssertionError(f"{event} 의 {key} 세 값의 합이 {n} 이 아닙니다")
                cells.append(f"{n} — {a} · {b} · {c}")
            else:
                cells.append(str(n))
        c1, c2 = cells
        lines.append(f"| `{event}` {label} | {c1} | {c2} |")
    return lines


class ProcessPromptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.process = read(PROCESS)

    def test_writer_prompts_are_quoted_verbatim(self) -> None:
        for name, text in (
            ("SYSTEM_PROMPT", SYSTEM_PROMPT),
            ("USER_INSTRUCTION", USER_INSTRUCTION),
            ("REWRITE_PROMPT", REWRITE_PROMPT),
            ("WRITE_TOOL", json.dumps(WRITE_TOOL, ensure_ascii=False, indent=2)),
        ):
            with self.subTest(name=name):
                self.assertIn(text, self.process)

    def test_jev_questions_are_quoted_verbatim(self) -> None:
        questions = build_questions(load_config(CONFIG))
        self.assertIn(json.dumps(questions, ensure_ascii=False, indent=2), self.process)
        for name, text in {**CHECK_QUESTIONS, **SELF_CHECK_CRITERIA}.items():
            with self.subTest(name=name):
                self.assertIn(text, self.process)


class ReadmeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = read(README)

    def test_run_command_is_the_entry_point(self) -> None:
        self.assertIn(f"{RUN_COMMAND} --once --dry-run", self.readme)
        self.assertIn(RUN_COMMAND, agent.run.__doc__ or "")

    def test_run_lines_are_locked_line_by_line(self) -> None:
        """맥 첫 실행 줄과 녹화 3단계 줄이 둘 다, 윈도우 줄은 두 조각이 한 줄에 함께 있어야 합니다."""
        self.assertGreaterEqual(self.readme.count(f"{RUN_COMMAND} --once --dry-run"), 2)
        windows = [
            line
            for line in self.readme.splitlines()
            if '$env:PYTHONPATH = "src"' in line and "python -m agent.run --once --dry-run" in line
        ]
        self.assertTrue(windows)

    def test_suite_command_is_the_contract_one(self) -> None:
        self.assertIn(SUITE_COMMAND, self.readme)

    def test_mode_lines_are_test_mode(self) -> None:
        lines = [line for line in self.readme.splitlines() if "mode=" in line]
        self.assertGreaterEqual(len(lines), 2)
        for line in lines:
            with self.subTest(line=line):
                self.assertIn("mode=test", line)

    def test_zwj_keyword_is_refused(self) -> None:
        emoji = "👩‍💻"
        lines = read(CONFIG).split("\n")
        changed = [
            f"keywords: [연애, {emoji}]" if line.startswith("keywords:") else line for line in lines
        ]
        self.assertNotEqual(changed, lines)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.yaml"
            path.write_text("\n".join(changed), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)
        self.assertIn("ZWJ", self.readme)


class SampleLogTest(unittest.TestCase):
    """커밋된 logs/sample.log 가 받은 파일 그대로이고 트래커 Phase 8A 의 조건을 지키는지 봅니다."""

    def test_sample_log_is_the_received_file(self) -> None:
        self.assertEqual(hashlib.sha256(SAMPLE_LOG.read_bytes()).hexdigest(), SAMPLE_SHA256)
        self.assertIn(SAMPLE_SHA256, read(TRACKER))

    def test_sample_log_meets_the_tracker_conditions(self) -> None:
        self.assertEqual(sample_log_failures(SAMPLE_LOG), [])

    def test_rehearsed_rows_carry_no_detail(self) -> None:
        rehearsed = [
            fields
            for _, event, fields in sample_rows()
            if event == "POST" and fields["result"] == "rehearsed"
        ]
        self.assertTrue(rehearsed)
        for fields in rehearsed:
            with self.subTest(video=fields["video"]):
                self.assertEqual(fields["reason"], "dry_run")
                self.assertNotIn("detail", fields)

    def test_sample_log_is_not_text_converted(self) -> None:
        self.assertIn("logs/sample.log -text", read(ATTRIBUTES).splitlines())


class SampleLogBrokenCopyTest(unittest.TestCase):
    """이름 붙인 망가진 사본마다 sample_log_failures 가 제 실패를 그대로 내는지 봅니다."""

    def setUp(self) -> None:
        self.data = SAMPLE_LOG.read_bytes()

    def failures_of(self, name: str, data: bytes) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_bytes(data)
            return sample_log_failures(path)

    def test_crlf_copy_is_refused(self) -> None:
        failures = self.failures_of("crlf.log", self.data.replace(b"\n", b"\r\n"))
        self.assertEqual(len(failures), 2, failures)
        self.assertEqual(failures[0], "sha256")
        self.assertTrue(failures[1].startswith("read_log: 1번째 줄:"), failures)

    def test_live_row_copy_is_refused(self) -> None:
        row = (
            "2026-10-16T14:14:08+09:00 POST video=AAAAAAAAAAA mode=live result=posted"
            " reason=allowlisted\n"
        )
        failures = self.failures_of("live.log", self.data + row.encode("utf-8"))
        self.assertEqual(failures, ["sha256", "lines", "mode=live"])

    def test_blocked_line_removed_copy_is_refused(self) -> None:
        blocked = BLOCKED_POST.encode("utf-8")
        kept = [line for line in self.data.split(b"\n") if blocked not in line]
        failures = self.failures_of("noblock.log", b"\n".join(kept))
        self.assertEqual(failures, ["sha256", "lines", "blocked"])

    def test_cut_last_line_copy_is_refused(self) -> None:
        failures = self.failures_of("cut.log", self.data[:-1])
        self.assertEqual(len(failures), 2, failures)
        self.assertEqual(failures[0], "sha256")
        self.assertTrue(failures[1].startswith("read_log: 1738번째 줄:"), failures)

    def test_contact_copy_is_refused(self) -> None:
        phone = "010-" + "0000-1234"  # 실행할 때 이어 붙여, 커밋된 글에는 연락처 모양이 없습니다
        row = (
            "2026-10-16T14:14:08+09:00 DETECT video=BBBBBBBBBBB channel=UC1 keyword=연애"
            f' title="문의 {phone}"\n'
        )
        failures = self.failures_of("contact.log", self.data + row.encode("utf-8"))
        self.assertEqual(failures, ["sha256", "lines", "contacts"])


class ReadmeCodeMatchTest(unittest.TestCase):
    """README · PROCESS 가 안내하는 기능이 8A 때 main 의 코드와 맞는지 봅니다(트래커 Phase 8 질문 3 A)."""

    def setUp(self) -> None:
        self.readme = read(README)
        self.process = read(PROCESS)

    def test_jev_key_line_matches_start_step(self) -> None:
        self.assertIn("TYPESAFE_API_KEY", agent.run.SECRET_NAMES)
        self.assertIn("이 판에서는 jev 키 없이 테스트 모드도 시작하지 않습니다", self.readme)

    def test_report_line_matches_report_path(self) -> None:
        self.assertEqual(agent.run.REPORT_PATH, Path("data/report.html"))
        self.assertIn("`data/report.html`", self.readme)
        self.assertIn("open data/report.html", self.readme)

    def test_chrome_address_line_matches_config(self) -> None:
        self.assertIn("`localhost` · `127.0.0.1` · `[::1]`", self.readme)
        text = read(CONFIG)
        line = "chrome_debug_url: http://localhost:9222"
        self.assertEqual(text.count(line), 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.yaml"
            foreign = text.replace(line, "chrome_debug_url: http://evil.example:9222")
            path.write_text(foreign, encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_config(path)
            path.write_text(
                text.replace(line, 'chrome_debug_url: "http://[::1]:9222"'), encoding="utf-8"
            )
            load_config(path)

    def test_proxy_and_mirrored_lines(self) -> None:
        self.assertIn("`no_proxy` 에 `localhost,127.0.0.1,[::1]`", self.readme)
        self.assertIn("`networkingMode=mirrored`", self.readme)

    def test_remaining_work_is_the_8a_time_list(self) -> None:
        self.assertEqual(remaining_bullets(self.process), REMAINING_8A)


class LiveRunDocsTest(unittest.TestCase):
    """README 의 시연 링크와 PROCESS 의 실제 숫자가 트래커 Phase 8A 와 logs/sample.log 그대로인지 봅니다."""

    def setUp(self) -> None:
        self.readme = read(README)
        self.process = read(PROCESS)

    def test_demo_link_is_the_tracker_link(self) -> None:
        self.assertIn(DEMO_URL, self.readme)
        self.assertIn(DEMO_URL, read(TRACKER))
        self.assertNotIn("준비 중", self.readme)
        self.assertIn("실제 게시는 없습니다", self.readme)

    def test_readme_points_at_sample_log(self) -> None:
        self.assertIn("실제 실행의 기록은 `logs/sample.log` 입니다", self.readme)
        self.assertNotIn("둘 예정", self.readme)

    def test_readme_has_no_committed_list_claim(self) -> None:
        self.assertEqual(committed_list_claims(self.readme), [])
        self.assertIn(
            "자리 표시(`https://youtu.be/내-테스트-영상-ID`)라, 그대로 돌리면 어떤 영상에도 실제 게시하지 않습니다",
            self.readme,
        )
        self.assertIn(f"  - {PLACEHOLDER}\n", read(CONFIG))
        self.assertEqual(load_config(CONFIG).allowed_videos, (PLACEHOLDER,))

    def test_demo_videos_do_not_read_as_applicant_videos(self) -> None:
        lines = [
            line
            for line in self.readme.splitlines()
            if "시연에 쓴 영상은 `logs/sample.log` 에 보입니다" in line
        ]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("남의 채널", lines[0])

    def test_demo_section_says_how_far_the_video_went(self) -> None:
        self.assertIn("제출한 시연 영상(맨 위 링크)은 이 순서의 3단계까지만 찍었습니다", self.readme)
        self.assertIn("4단계(실제 게시)는 하지 않아 실제 게시는 없습니다", self.readme)

    def test_no_doc_says_the_recording_posted(self) -> None:
        self.assertEqual(recording_post_claims(self.readme), [])
        self.assertEqual(recording_post_claims(self.process), [])

    def test_process_states_no_post_and_the_setup(self) -> None:
        self.assertIn("녹화에는 실제 게시가 없습니다", self.process)
        self.assertIn("남의 채널 다섯의 인기 영상", self.process)
        self.assertIn("`test_run: true`", self.process)

    def test_process_setup_matches_sample_log(self) -> None:
        rows = sample_rows()
        starts = [fields for _, event, fields in rows if event == "START"]
        self.assertEqual(len(starts), 2)
        self.assertEqual((starts[0]["allowed"], starts[0]["dry_run"]), ("0", "true"))
        self.assertEqual(
            (starts[1]["allowed"], starts[1]["dry_run"], starts[1]["test_run"]),
            ("5", "true", "true"),
        )
        stops = [fields["reason"] for _, event, fields in rows if event == "STOP"]
        self.assertEqual(stops, ["interrupted", "once"])
        self.assertIn(CYCLE_LINE, read(SAMPLE_LOG))
        cycles = [[row for row in run if row[1] == "CYCLE"] for run in runs(rows)]
        self.assertEqual([len(found) for found in cycles], [0, 1])
        allowlisted = [
            fields
            for _, event, fields in rows
            if event == "TRIGGER" and fields["reason"] == "allowlisted"
        ]
        self.assertEqual(len(allowlisted), 5)
        for fields in allowlisted:
            with self.subTest(video=fields["video"]):
                self.assertEqual(fields.get("rule_reason"), "views_above_max")
        rehearsed = [
            fields["video"]
            for _, event, fields in rows
            if event == "POST" and fields["result"] == "rehearsed"
        ]
        self.assertEqual(tuple(rehearsed), REHEARSED)
        for text in (
            "`START … allowed=0 dry_run=true`",
            "`START … allowed=5 test_run=true`",
            "`STOP reason=interrupted`",
            "`STOP reason=once`",
            f"`{CYCLE_LINE}`",
            "`3K82-PjUeP0` · `WxXINTXQSd4`",
            "1,738줄, 2026-10-16 13:47:11–14:14:07(+09:00)",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.process)

    def test_process_commit_line_is_the_tracker_commit(self) -> None:
        self.assertIn(f"`sample.log` 는 커밋 `{COMMIT_X}` 의 코드로 돌았습니다", self.process)
        self.assertIn(f"X = `{COMMIT_X}`", read(TRACKER))

    def test_process_table_is_counted_from_sample_log(self) -> None:
        for line in table_rows(sample_rows()):
            with self.subTest(line=line):
                self.assertIn(line, self.process)

    def test_process_table_note_is_counted_from_sample_log(self) -> None:
        rows = sample_rows()
        r1, r2 = runs(rows)
        d1 = videos(r1, "DETECT")
        d2 = videos(r2, "DETECT")
        allowed2 = videos(r2, "DETECT", keyword="allowed_videos")
        v2 = videos(r2, "VIEWS")
        c1 = videos(r1, "CLASSIFY")
        c2 = videos(r2, "CLASSIFY")
        t2 = videos(r2, "TRIGGER")
        both = videos(r2, "TRIGGER", verdict="yes") & (
            videos(r1, "CLASSIFY", verdict="yes") | videos(r2, "CLASSIFY", verdict="yes")
        )
        self.assertEqual(c1 & c2, set())
        self.assertEqual(t2, v2)
        self.assertEqual(len(c2 & d1) + len(c2 & d2), len(c2))
        self.assertEqual([row for row in rows if row[1] == "ERROR"], [])
        for text in (
            f"녹화 실행이 추적한 영상 {len(v2)}개 가운데 {len(v2 & d1)}개는 사전 점검이 먼저 찾아"
            f" `DETECT` 줄이 없고, 녹화 실행의 `DETECT` {len(d2)} 은 새 검색 결과"
            f" {len(d2 - allowed2)} 과 명단 영상(`keyword=allowed_videos`) {len(allowed2)} 입니다",
            f"녹화 실행의 {len(c2)} 가운데 {len(c2 & d1)} 은 사전 점검이 찾고 `Ctrl+C` 전에"
            f" 판별하지 못한 영상이고, {len(c2 & d2)} 은 녹화 실행이 새로 찾은 영상입니다",
            f"녹화 실행에서는 추적한 영상 수와 같은 {len(t2)} 입니다",
            f"녹화 실행에서 그런 영상은 {len(both)} 개입니다",
            "이 로그에는 `ERROR` 줄이 없어 오류로 보류한 영상은 없습니다",
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.process)

    def test_process_cites_blocked_line_and_shapes(self) -> None:
        self.assertIn(BLOCKED_POST, read(SAMPLE_LOG))
        self.assertIn(BLOCKED_POST, self.process)
        shapes = [fields["shape"] for _, event, fields in sample_rows() if event == "COMMENT"]
        self.assertEqual(tuple(shapes), SHAPES)
        self.assertIn("`scene_first` · `question_first` · `story_first`", self.process)
        self.assertEqual(
            decide_post(BLOCKED_VIDEO, (PLACEHOLDER,), True).reason, "not_in_allowlist"
        )
        self.assertEqual(
            decide_post(BLOCKED_VIDEO, (PLACEHOLDER,), False).reason, "not_in_allowlist"
        )
        self.assertIn(
            "이유가 `dry_run` 이 아니라 `not_in_allowlist` 인 것은"
            " 가드가 테스트 실행인지보다 허용 목록을 먼저 보기 때문입니다",
            self.process,
        )

    def test_process_skip_reasons_are_counted_from_sample_log(self) -> None:
        reasons = Counter(
            fields["reason"].split(" — ", 1)[0]
            for _, event, fields in sample_rows()
            if event == "SKIP"
        )
        self.assertEqual(dict(reasons), SKIP_REASONS)
        self.assertIn(" · ".join(f"`{k}` {v}" for k, v in SKIP_REASONS.items()), self.process)

    def test_process_quotes_6f_after_numbers(self) -> None:
        contract = read(CONTRACT).splitlines()
        for label, prefix in (
            ("운영 창", "- 과제 품질 전후 운영 창: "),
            ("넓힌 창", "- 과제 품질 전후 넓힌 창: "),
        ):
            with self.subTest(label=label):
                found = [line.strip() for line in contract if line.strip().startswith(prefix)]
                self.assertEqual(len(found), 1, found)
                self.assertIn(f"{label}: {found[0][len(prefix):]}", self.process)
        self.assertNotIn("아직 재지 않았습니다", self.process)

    def test_docs_have_no_contact_shapes(self) -> None:
        self.assertEqual(count_contacts(self.readme), 0)
        self.assertEqual(count_contacts(self.process), 0)


class JudgeSampleTest(unittest.TestCase):
    """줄 판정기 둘의 가까운 표본(헌법 12조) — 빨강은 잡고 초록은 지나야 합니다."""

    def test_committed_list_red_samples(self) -> None:
        for sample in (
            "- **커밋된 명단.** 제출본의 `allowed_videos` 에는 지원자의 테스트 영상이 들어 있습니다.",
            "제출본의 allowed_videos에는 지원자의 테스트 영상이 들어 있습니다",
            "커밋된 명단에는 지 원 자 영상이 있습니다",
            "ALLOWED_VIDEOS 에는 지원자 영상이 있습니다",
            "커밋된 목록에는 지원자의 영상이 들어 있습니다",
            "  - 커밋된 명단: 지원자 영상",
        ):
            with self.subTest(sample=sample):
                self.assertEqual(committed_list_claims(sample), [sample])

    def test_committed_list_green_samples(self) -> None:
        for sample in (
            "- **커밋된 명단.** 제출본의 `allowed_videos` 는 자리 표시(`https://youtu.be/내-테스트-영상-ID`)라,"
            " 그대로 돌리면 어떤 영상에도 실제 게시하지 않습니다. 실제 게시를 보려면 제 테스트 영상 ID 를"
            " 넣으세요. 시연에 쓴 영상은 `logs/sample.log` 에 보입니다 — 본인 테스트 영상이 아니라 남의 채널"
            " 다섯의 인기 영상이고, 테스트 실행이라 게시하지 않았습니다.",
            "- **명단 영상은 타이밍 규칙을 면제받습니다.** 키워드 검색과 타이밍 조건"
            "(조회수 1,000–5,000 · 시간당 150)은 새로 올린 본인 영상을 통과시키지 않아",
        ):
            with self.subTest(sample=sample):
                self.assertEqual(committed_list_claims(sample), [])

    def test_recording_post_reach(self) -> None:
        for word in RECORDING_WORDS:
            for shape in POSTED_SHAPES:
                sample = f"{word}에서 {shape}"
                with self.subTest(sample=sample):
                    self.assertEqual(recording_post_claims(sample), [sample])
        for shape in POSTED_SHAPES:
            sample = f"테스트 실행에서 {shape}"
            with self.subTest(sample=sample):
                self.assertEqual(recording_post_claims(sample), [])
        for word in RECORDING_WORDS:
            sample = f"{word}에는 실제 게시가 없습니다"
            with self.subTest(sample=sample):
                self.assertEqual(recording_post_claims(sample), [])

    def test_recording_post_near_misses(self) -> None:
        for sample in (
            "녹 화 에서 실제로 게시 했습니다",
            "  녹화에서 게시했습니다",
            "녹화 로그: RESULT=POSTED",
            "녹화: 게시됐음",
        ):
            with self.subTest(red=sample):
                self.assertEqual(recording_post_claims(sample), [sample])
        for sample in (
            "녹화에는 실제 게시가 없습니다",
            "시연에 쓴 영상은 `logs/sample.log` 에 보입니다 — 본인 테스트 영상이 아니라"
            " 남의 채널 다섯의 인기 영상이고, 테스트 실행이라 게시하지 않았습니다.",
            "4. `PYTHONPATH=src python3 -m agent.run --once` — V 에 같은 댓글이 실제로 게시됩니다.",
        ):
            with self.subTest(green=sample):
                self.assertEqual(recording_post_claims(sample), [])


if __name__ == "__main__":
    unittest.main()
