"""실행 진입점 테스트 — run.py 가 다섯 단계를 한 스레드 · 한 저장소로 잇는지(계약 '실행 진입점 — run.py' 절).

가짜 YouTube(fetch) · jev(ask) · Claude · 크롬 · 시계로 돕니다 — 네트워크 · SDK · 브라우저가 필요 없습니다.
"""
from __future__ import annotations

import ast
import contextlib
import dataclasses
import io
import json
import os
import tempfile
import unittest
import urllib.parse
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import agent.run as run
from agent.classifier import MATCH_ID
from agent.config import ConfigError, load_config
from agent.logbook import Event, Logbook, read_log
from agent.scheduler import run_loop
from agent.store import Store
from agent.watcher import Watcher
from agent.youtube import QuotaLedger, YouTubeClient
from tests.test_classifier import response
from tests.test_watcher import FakeApi, google_error, search_page, video_item
from tests.test_writer import reply, tool_reply

REPO_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"
T0 = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)
WAIT_S = 7200.0  # poll_interval_min 120 — 가짜 monotonic 이 멈춰 있어 대기는 언제나 두 시간
A = "AAAAAAAAAAA"
B = "BBBBBBBBBBB"
C = "CCCCCCCCCCC"
D = "DDDDDDDDDDD"
KEYWORD = "연애"
CONCERN = "썸 상대의 답장이 늦어 불안한 마음"
MARK = "MRK"  # R6 표본 — 로그 어디에도 나오면 안 되는 표시
KEYS = {
    "YOUTUBE_API_KEY": "yt-key-0001",
    "TYPESAFE_API_KEY": "jev-key-0002",
    "ANTHROPIC_API_KEY": "claude-key-0003",
}


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise AssertionError(f"config.yaml 에 정확히 한 번 나오지 않습니다: {old!r}")
    return text.replace(old, new)


def config_text(
    allowed: tuple[str, ...] = (A, B), *, test_run: bool = False, daily_max_comments: int = 10
) -> str:
    """저장소의 config.yaml 에서 검색어 · 허용 목록 · test_run · 하루 상한만 바꾼 글(E-027: 맨 ID)."""
    text = REPO_CONFIG.read_text(encoding="utf-8")
    text = replace_once(text, "keywords: [연애, 썸, 연애 상담, 이별, 소개팅]", f"keywords: [{KEYWORD}]")
    entries = "".join(f"  - {video_id}\n" for video_id in allowed)
    text = replace_once(text, "  - https://youtu.be/내-테스트-영상-ID\n", entries)
    text = replace_once(text, "test_run: false ", f"test_run: {'true' if test_run else 'false'} ")
    return replace_once(
        text, "daily_max_comments: 10 ", f"daily_max_comments: {daily_max_comments} "
    )


def title_of(video_id: str) -> str:
    return f"연애 고민 {video_id}"


def draft(n: int) -> str:
    """n 번째 초안 — 부를 때마다 다른 한글 50자라 반복 · 문장 틀 검사에 걸리지 않습니다."""
    return "".join(chr(0xAC00 + 100 * n + k) for k in range(50))


class FakeClock:
    """부를 때마다 1초씩 가는 UTC 시계. sleep 은 그만큼 시계를 앞으로 돌립니다."""

    def __init__(self, start: datetime = T0) -> None:
        self.now = start

    def __call__(self) -> datetime:
        self.now += timedelta(seconds=1)
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class FakeYouTube(FakeApi):
    """test_watcher 의 가짜 API 에 인기 댓글(commentThreads)을 더합니다.

    comments[id] 는 댓글 글 목록이거나 오류 상태(정수), 상태 403 은 댓글이 막힌 영상입니다.
    """

    def __init__(self) -> None:
        super().__init__()
        self.comments: dict[str, object] = {}

    def __call__(self, url: str, timeout: float) -> tuple[int, bytes]:
        parts = urllib.parse.urlsplit(url)
        if parts.path.rsplit("/", 1)[-1] != "commentThreads":
            return super().__call__(url, timeout)
        query = dict(urllib.parse.parse_qsl(parts.query))
        self.calls.append(("commentThreads", query))
        entry = self.comments.get(query["videoId"], [])
        if isinstance(entry, int):
            body = google_error(entry)
            if entry == 403:
                body = {"error": {"code": 403, "errors": [{"reason": "commentsDisabled"}]}}
            return entry, json.dumps(body).encode("ascii")
        items = [
            {"snippet": {"topLevelComment": {"snippet": {"textDisplay": text}}}} for text in entry
        ]
        return 200, json.dumps({"items": items}).encode("ascii")

    def sampled(self) -> list[str]:
        return [video_id for batch in self.video_batches() for video_id in batch]


class FakeJevAsk:
    """classifier.Ask 모양 — 판별 질문(matches_topic)과 자체 검사 질문을 가려 답합니다.

    classify[id] 는 그 영상의 판별 답(응답 또는 예외), 없으면 확신 있는 일치입니다. 자체 검사는
    광고처럼 읽힘만 낮고 나머지는 높게 답합니다. 영상은 상태 글의 제목(ID 가 든)으로 알아봅니다.
    """

    def __init__(self) -> None:
        self.classify: dict[str, object] = {}
        self.calls: list[tuple[str, str | None]] = []

    def __call__(self, model: str, state: str, questions: Mapping[str, object]) -> object:
        video_id = next((v for v in (A, B, C, D) if title_of(v) in state), None)
        if MATCH_ID in questions:
            self.calls.append(("classify", video_id))
            answer = self.classify.get(video_id, response())
            if isinstance(answer, BaseException):
                raise answer
            return answer
        self.calls.append(("check", video_id))
        nouls = {
            name: SimpleNamespace(noul=0.1 if name == "reads_like_ad" else 0.9)
            for name in questions
        }
        return SimpleNamespace(answers=nouls)

    def asked(self, video_id: str) -> int:
        return self.calls.count(("classify", video_id))


class WriterClaude:
    """anthropic.Anthropic 모양 — 부를 때마다 겹치지 않는 초안을 submit_comment 로 답합니다."""

    def __init__(self) -> None:
        self.messages = self
        self.calls: list[dict[str, object]] = []
        self.error: Exception | None = None

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return tool_reply(reply(CONCERN, draft(len(self.calls))))

    def user_messages(self, video_id: str) -> list[str]:
        """그 영상에 보낸 첫 user 차례 글들."""
        texts = [str(call["messages"][0]["content"]) for call in self.calls]
        return [text for text in texts if title_of(video_id) in text]


class FakeTab:
    """CommentPage 가짜 — 연 주소를 url 로 돌려주고 submit 을 셉니다."""

    def __init__(self, chrome: FakeChrome) -> None:
        self._chrome = chrome
        self.url = "about:blank"
        self.closed = False

    def open(self, url: str) -> None:
        self.url = url

    def prepare_comment(self, text: str) -> None:
        self._chrome.typed.append(text)

    def submit(self) -> None:
        self._chrome.submits.append(self.url)

    def confirm_posted(self, text: str) -> bool:
        return True

    def screenshot(self, path: Path) -> None:
        Path(path).write_bytes(b"\x89PNG fake")

    def close(self) -> None:
        self.closed = True


class FakeSession:
    """ChromeSession 가짜 — new_page 와 close 를 셉니다."""

    def __init__(self, chrome: FakeChrome, debug_url: str) -> None:
        self._chrome = chrome
        self.debug_url = debug_url
        self.pages: list[FakeTab] = []
        self.closes = 0

    def new_page(self) -> FakeTab:
        if self._chrome.unreachable:
            self._chrome.unreachable -= 1
            raise run.PageError("chrome_unreachable", "가짜 크롬이 꺼져 있습니다")
        page = FakeTab(self._chrome)
        self.pages.append(page)
        return page

    def close(self) -> None:
        self.closes += 1


class FakeChrome:
    """Services.chrome 자리 — 받은 debug_url 과 만든 세션, 눌린 submit 을 적습니다.

    unreachable 이 n 이면 처음 n 번의 new_page 가 chrome_unreachable 로 멈춥니다.
    """

    def __init__(self) -> None:
        self.sessions: list[FakeSession] = []
        self.submits: list[str] = []
        self.typed: list[str] = []
        self.unreachable = 0

    def __call__(self, debug_url: str) -> FakeSession:
        session = FakeSession(self, debug_url)
        self.sessions.append(session)
        return session


def raise_marked(*_args: object, **_kwargs: object) -> None:
    """R6 표본 — 자기 메시지(boom)에는 표시가 없고, __context__ 메시지 · 유튜브 주소의 key= ·
    __cause__ 의 .env 바이트 · traceback 지역 변수에 표시가 있습니다."""
    frame_local = f"{MARK}-frame-local"  # noqa: F841 — traceback 지역 변수의 표시
    try:
        raise OSError(
            f"{MARK}-context https://www.googleapis.com/youtube/v3/search?q=x&key={MARK}key0001"
        )
    except OSError:
        cause = UnicodeDecodeError(
            "utf-8", f"YOUTUBE_API_KEY={MARK}-env-bytes\n".encode("utf-8") + b"\xff", 30, 31,
            "invalid start byte",
        )
        raise RuntimeError("boom") from cause


class RunCase(unittest.TestCase):
    """임시 저장소 뿌리 하나 — config.yaml · data/ · logs/ 와 가짜 서비스."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.clock = FakeClock()
        self.api = FakeYouTube()
        self.jev = FakeJevAsk()
        self.claude = WriterClaude()
        self.chrome = FakeChrome()
        ledger = QuotaLedger(self.root / "data" / "quota.json")
        self.services = run.Services(
            ask=self.jev,
            claude=self.claude,
            youtube=YouTubeClient("TESTKEY", ledger, self.api),
            chrome=self.chrome,
        )
        self.log_path = self.root / "logs" / "agent.log"
        self.write_config()

    def write_config(self, text: str | None = None, **kwargs: object) -> None:
        body = text if text is not None else config_text(**kwargs)
        (self.root / "config.yaml").write_text(body, encoding="utf-8", newline="\n")

    def load(self) -> object:
        return load_config(self.root / "config.yaml")

    def show(
        self, video_id: str, views: int, *, channel: str = "UC1", age: timedelta = 2 * HOUR
    ) -> None:
        """다음 videos.list 가 이 영상을 이 조회수로 답합니다. age 는 시계의 지금에서 잰 업로드 나이."""
        published = (self.clock.now - age).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.api.videos[video_id] = video_item(
            video_id, views, title=title_of(video_id), published=published, channel=channel
        )

    def find(self, *video_ids: str) -> None:
        """다음 검색이 이 영상들을 찾습니다."""
        self.api.pages[(KEYWORD, None)] = search_page(list(video_ids))

    def pipeline(self, *, dry_run: bool = False, reloader: object = None) -> run.Pipeline:
        self.store = Store(self.root / "data" / "videos.json")
        self.logbook = Logbook(self.log_path, self.clock)
        watcher = Watcher(self.store, self.logbook, self.services.youtube, self.clock)
        return run.Pipeline(
            store=self.store,
            logbook=self.logbook,
            watcher=watcher,
            services=self.services,
            clock=self.clock,
            dry_run=dry_run,
            reloader=reloader or run.ConfigReloader(self.root / "config.yaml"),
            repo_root=self.root,
        )

    def cycle(self, pipeline: run.Pipeline, config: object = None) -> None:
        """사이클 하나를 돌리고 시계를 주기만큼 돌립니다."""
        pipeline.cycle(config if config is not None else self.load())
        self.clock.sleep(WAIT_S)

    def loop(self, pipeline: run.Pipeline, initial: object, cycles: int, sleep: object) -> None:
        run_loop(
            pipeline.cycle,
            pipeline._reloader,
            initial,
            on_error=pipeline.on_error,
            sleep=sleep,
            monotonic=lambda: 0.0,
            max_cycles=cycles,
        )

    def run_agent(self, *flags: str) -> int:
        options = run.parse_args(flags)
        return run.run_agent(
            options,
            root=self.root,
            services=self.services,
            clock=self.clock,
            sleep=self.clock.sleep,
            monotonic=lambda: 0.0,
        )

    def events(self) -> list[tuple[Event, dict[str, str]]]:
        if not self.log_path.exists():
            return []
        return [(event, fields) for _, event, fields in read_log(self.log_path)]

    def lines(self, event: Event, **match: str) -> list[dict[str, str]]:
        return [
            fields
            for name, fields in self.events()
            if name is event and all(fields.get(k) == v for k, v in match.items())
        ]

    def log_text(self) -> str:
        return self.log_path.read_text(encoding="utf-8") if self.log_path.exists() else ""


class TestLock(RunCase):
    def test_second_lock_refused_until_release(self) -> None:
        path = self.root / "data" / "agent.lock"
        with run.RunLock(path):
            with self.assertRaises(run.LockedError):
                with run.RunLock(path):
                    self.fail("두 번째 잠금이 잡혔습니다")
        with run.RunLock(path):
            pass

    def test_second_run_exits_3_without_log(self) -> None:
        stderr = io.StringIO()
        with run.RunLock(self.root / "data" / "agent.lock"):
            with contextlib.redirect_stderr(stderr):
                code = run.main(["--once"], root=self.root, environ=KEYS)
        self.assertEqual(code, 3)
        self.assertFalse(self.log_path.exists())
        self.assertIn("이미 실행 중입니다", stderr.getvalue())
        self.assertIn("agent.lock", stderr.getvalue())


class TestReloader(RunCase):
    def test_reloader_remembers_rejection_and_forgets_on_accept(self) -> None:
        reloader = run.ConfigReloader(self.root / "config.yaml")
        self.assertFalse(reloader.rejected)
        self.assertEqual(reloader().allowed_videos, (A, B))
        self.assertFalse(reloader.rejected)
        self.write_config(config_text(daily_max_comments=999999))
        for _ in range(2):
            with self.assertRaises(ConfigError):
                reloader()
            self.assertTrue(reloader.rejected)
        self.write_config(allowed=(A,))
        self.assertEqual(reloader().allowed_videos, (A,))
        self.assertFalse(reloader.rejected)


class TestEntry(RunCase):
    def test_start_cycle_stop_lines(self) -> None:
        code = self.run_agent("--once")
        self.assertEqual(code, 0)
        names = [event for event, _ in self.events()]
        self.assertEqual(names[0], Event.START)
        self.assertEqual(names[-2:], [Event.CYCLE, Event.STOP])
        self.assertEqual(
            self.lines(Event.START),
            [
                {
                    "mode": "live",
                    "allowed": "2",
                    "interval_min": "120",
                    "dry_run": "false",
                    "once": "true",
                    "test_run": "false",
                }
            ],
        )
        self.assertEqual(self.lines(Event.CYCLE), [{"n": "1", "errors": "0", "mode": "live"}])
        self.assertEqual(self.lines(Event.STOP), [{"reason": "once"}])

    def test_single_store_and_ledger(self) -> None:
        self.show(A, 2000)
        with (
            mock.patch.object(run, "Store", side_effect=Store) as store_cls,
            mock.patch.object(run, "QuotaLedger", side_effect=QuotaLedger) as ledger_cls,
            mock.patch.object(
                run,
                "YouTubeClient",
                side_effect=lambda key, ledger: YouTubeClient(key, ledger, self.api),
            ),
            mock.patch.object(run, "anthropic_client", return_value=self.claude),
            mock.patch.dict(os.environ),
        ):
            services = run.connect_real(self.root, KEYS, find_spec=lambda name: object())
            services = dataclasses.replace(services, ask=self.jev, chrome=self.chrome)
            code = run.run_agent(
                run.Options(dry_run=False, once=True),
                root=self.root,
                services=services,
                clock=self.clock,
                sleep=self.clock.sleep,
                monotonic=lambda: 0.0,
            )
        self.assertEqual(code, 0)
        self.assertEqual(store_cls.call_count, 1)
        self.assertEqual(ledger_cls.call_count, 1)
        self.assertEqual(
            [call.args for call in store_cls.call_args_list],
            [(self.root / "data" / "videos.json",)],
        )
        self.assertEqual(
            [call.args for call in ledger_cls.call_args_list],
            [(self.root / "data" / "quota.json",)],
        )

    def test_connect_real_reads_three_secrets_and_sets_jev_env(self) -> None:
        (self.root / ".env").write_text(
            f"ANTHROPIC_API_KEY={KEYS['ANTHROPIC_API_KEY']}\n", encoding="utf-8"
        )
        environ = {k: v for k, v in KEYS.items() if k != "ANTHROPIC_API_KEY"}
        sentinel = object()
        with (
            mock.patch.object(run, "anthropic_client", return_value=sentinel) as claude,
            mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}),
        ):
            services = run.connect_real(self.root, environ, find_spec=lambda name: object())
            self.assertEqual(os.environ["TYPESAFE_API_KEY"], KEYS["TYPESAFE_API_KEY"])
        claude.assert_called_once_with(KEYS["ANTHROPIC_API_KEY"])
        self.assertIs(services.claude, sentinel)
        self.assertIs(services.ask, run.sdk_ask)
        self.assertIs(services.chrome, run.ChromeSession)
        self.assertIsInstance(services.youtube, YouTubeClient)
        self.assertEqual(services.youtube._api_key, KEYS["YOUTUBE_API_KEY"])

    def test_missing_secret_exits_2(self) -> None:
        environ = {k: v for k, v in KEYS.items() if k != "ANTHROPIC_API_KEY"}
        real = run.connect_real
        stderr = io.StringIO()
        with (
            mock.patch.object(
                run,
                "connect_real",
                side_effect=lambda root, env: real(root, env, lambda name: object()),
            ),
            contextlib.redirect_stderr(stderr),
        ):
            code = run.main(["--once"], root=self.root, environ=environ)
        self.assertEqual(code, 2)
        self.assertIn(
            "에이전트를 시작할 수 없습니다 — EnvError: ANTHROPIC_API_KEY 가 비어 있습니다",
            stderr.getvalue(),
        )
        self.assertFalse(self.log_path.exists())

    def test_missing_sdk_exits_2(self) -> None:
        for missing, package in (("typesafe_sdk", "typesafe-sdk"), ("anthropic", "anthropic")):
            with self.subTest(missing=missing):
                def find_spec(name: str, missing: str = missing) -> object:
                    return None if name == missing else object()

                read_secret = AssertionError("SDK 를 보기 전에 비밀 값을 읽었습니다")
                with mock.patch.object(run, "require_secret", side_effect=read_secret):
                    with self.assertRaises(run.MissingSdkError) as caught:
                        run.connect_real(self.root, KEYS, find_spec=find_spec)
                self.assertIn(package, str(caught.exception))
                self.assertIsInstance(caught.exception, ImportError)
                stderr = io.StringIO()
                with (
                    mock.patch.object(run, "connect_real", side_effect=caught.exception),
                    contextlib.redirect_stderr(stderr),
                ):
                    code = run.main(["--once"], root=self.root, environ=KEYS)
                self.assertEqual(code, 2)
                self.assertIn(f"MissingSdkError: {package} 가 설치되지 않았습니다", stderr.getvalue())
                self.assertFalse(self.log_path.exists())

    def test_echo_never_raises_on_unencodable_text(self) -> None:
        console = io.TextIOWrapper(io.BytesIO(), encoding="cp949")
        logbook = Logbook(self.log_path, self.clock, run.echo_stream(console))
        line = logbook.write(Event.DETECT, video=A, channel="UC1", keyword=KEYWORD, title="연애 😀")
        self.assertIn("😀", line)
        self.assertIn("title=\"연애 😀\"", self.log_text())
        echoed = console.buffer.getvalue()
        self.assertIn(b"\\U0001f600", echoed)
        self.assertIn("연애".encode("cp949"), echoed)

    def test_bad_initial_config_exits_2_with_config_error_line(self) -> None:
        self.write_config(config_text(daily_max_comments=999999))
        code = self.run_agent("--once")
        self.assertEqual(code, 2)
        self.assertEqual([event for event, _ in self.events()], [Event.ERROR])
        (fields,) = self.lines(Event.ERROR)
        self.assertEqual(fields["where"], "config")
        self.assertTrue(fields["reason"].startswith("ConfigError: "), fields)
        self.assertIn("86400 이하여야 합니다: limits.daily_max_comments", fields["reason"])


class TestOneWorker(unittest.TestCase):
    def test_run_module_imports_no_concurrency(self) -> None:
        tree = ast.parse(Path(run.__file__).read_text(encoding="utf-8"))
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.append(node.module)
        self.assertIn("agent.scheduler", names)  # import 를 정말 읽었는지
        banned = {"threading", "asyncio", "concurrent", "multiprocessing", "subprocess"}
        self.assertEqual([name for name in names if name.split(".")[0] in banned], [])


class TestFence(RunCase):
    def test_r6_error_line_has_no_context_or_traceback(self) -> None:
        # on_error 쪽 — 탐지가 낸 예외가 run_loop 의 on_error("cycle") 로 갑니다
        pipeline = self.pipeline()
        with mock.patch.object(Watcher, "cycle", side_effect=raise_marked):
            self.loop(pipeline, self.load(), 1, self.clock.sleep)
        self.assertEqual(
            self.lines(Event.ERROR, where="cycle"),
            [{"where": "cycle", "reason": "RuntimeError: boom"}],
        )
        self.assertNotIn(MARK, self.log_text())


if __name__ == "__main__":
    unittest.main()
