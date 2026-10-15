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
from agent.classifier import MATCH_ID, JevError
from agent.config import ConfigError, load_config
from agent.guard import decide_post
from agent.logbook import Event, Logbook, read_log
from agent.models import Judgement, Verdict, VideoRecord, ViewSample
from agent.scheduler import run_loop
from agent.store import Store
from agent.watcher import Watcher
from agent.writer import TOP_COMMENTS_MAX
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


class StrFails(Exception):
    """str() 이 터지는 예외 — 울타리의 이유는 종류 이름만 남아야 합니다."""

    def __str__(self) -> str:
        raise RuntimeError("str 이 터졌습니다")


def raise_for(video_id: str, error: BaseException | None, real: object) -> object:
    """단계 함수 자리 — 그 영상에서는 error 를(None 이면 R6 표본을) 내고, 나머지는 진짜를 부릅니다."""

    def stage(record: object, *args: object, **kwargs: object) -> object:
        if record.video_id == video_id:
            if error is None:
                raise_marked()
            raise error
        return real(record, *args, **kwargs)

    return stage


def watch(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


# 단계 함수 이름(agent.run 의 이름) → 울타리 줄의 where
STAGES = (
    ("classify", "run.classify"),
    ("judge_trigger", "run.trigger"),
    ("write_comment", "run.write"),
    ("post_video", "run.post"),
)


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

    def seed_quota(self, units: int) -> None:
        """한 시간 전에 units 만큼 쓴 쿼터 장부로 서비스를 다시 만듭니다."""
        path = self.root / "data" / "quota.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": (T0 - HOUR).isoformat(), "call": "videos.list", "units": units}
        path.write_text(json.dumps({"calls": [entry], "schema_version": 1}), encoding="utf-8")
        youtube = YouTubeClient("TESTKEY", QuotaLedger(path), self.api)
        self.services = dataclasses.replace(self.services, youtube=youtube)

    def patch_stage(self, name: str, error: BaseException | None, video_id: str = A) -> object:
        """agent.run 의 단계 함수 하나가 그 영상에서만 error 를 내게 합니다."""
        real = getattr(run, name)
        return mock.patch.object(run, name, side_effect=raise_for(video_id, error, real))

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

    def record(self, video_id: str) -> object:
        record = Store(self.root / "data" / "videos.json").get(video_id)
        self.assertIsNotNone(record, video_id)
        return record

    def posted_live(self) -> list[str]:
        return [f["video"] for f in self.lines(Event.POST, mode="live", result="posted")]


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


class TwoListedCase(RunCase):
    """명단 영상 둘(A · B, 다른 채널)이 첫 사이클에 나타나 모두 대상이 되는 자리."""

    def setUp(self) -> None:
        super().setUp()
        self.show(A, 2000, channel="UC1")
        self.show(B, 2000, channel="UC2")

    def fenced(self, video_id: str = A) -> list[dict[str, str]]:
        return [fields for fields in self.lines(Event.ERROR) if fields.get("video") == video_id]

    def cycle_errors(self) -> list[str]:
        return [fields["errors"] for fields in self.lines(Event.CYCLE)]


class TestFence(TwoListedCase):
    def test_exception_in_each_stage_moves_to_next_video(self) -> None:
        for name, where in STAGES:
            with self.subTest(stage=where):
                self.setUp()
                with self.patch_stage(name, ValueError("단계가 터졌습니다")):
                    self.cycle(self.pipeline())
                (line,) = self.fenced()
                self.assertEqual(line["where"], where)
                self.assertEqual(line["reason"], "ValueError: 단계가 터졌습니다")
                self.assertEqual(self.lines(Event.ERROR, where="classify"), [])
                self.assertEqual(self.posted_live(), [B])
                self.assertEqual(
                    self.lines(Event.CYCLE), [{"n": "1", "errors": "1", "mode": "live"}]
                )

    def test_keyboard_interrupt_propagates(self) -> None:
        pipeline = self.pipeline()
        with self.patch_stage("classify", KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                pipeline.cycle(self.load())
        self.assertEqual(self.lines(Event.ERROR), [])
        self.assertEqual(self.lines(Event.CLASSIFY), [])
        self.assertEqual(self.jev.asked(B), 0)
        self.assertEqual(self.lines(Event.CYCLE), [])

    def test_run_agent_interrupt_writes_stop_interrupted(self) -> None:
        with self.patch_stage("classify", KeyboardInterrupt()):
            code = self.run_agent("--once")
        self.assertEqual(code, 130)
        self.assertEqual(self.lines(Event.STOP), [{"reason": "interrupted"}])
        self.assertEqual(self.lines(Event.CYCLE), [])

    def test_r6_error_line_has_no_context_or_traceback(self) -> None:
        # 단계 쪽 — 판별에서 난 예외를 울타리가 받습니다
        pipeline = self.pipeline()
        with self.patch_stage("classify", None):
            self.cycle(pipeline)
        self.assertEqual(
            self.fenced(), [{"where": "run.classify", "reason": "RuntimeError: boom", "video": A}]
        )
        self.assertEqual(self.posted_live(), [B])
        # on_error 쪽 — 탐지가 낸 예외가 run_loop 의 on_error("cycle") 로 갑니다
        with mock.patch.object(Watcher, "cycle", side_effect=raise_marked):
            self.loop(pipeline, self.load(), 1, self.clock.sleep)
        self.assertEqual(
            self.lines(Event.ERROR, where="cycle"),
            [{"where": "cycle", "reason": "RuntimeError: boom"}],
        )
        self.assertNotIn(MARK, self.log_text())

    def test_unicode_encode_error_is_fenced(self) -> None:
        error = UnicodeEncodeError("utf-8", "\ud800", 0, 1, "surrogates not allowed")
        with self.patch_stage("classify", error):
            self.cycle(self.pipeline())
        read_log(self.log_path)  # 모든 줄이 UTF-8 로 풀리고 parse_line 을 지납니다
        self.assertEqual(
            self.fenced(),
            [
                {
                    "where": "run.classify",
                    "reason": "UnicodeEncodeError: 'utf-8' codec can't encode character"
                    " '\\ud800' in position 0: surrogates not allowed",
                    "video": A,
                }
            ],
        )
        self.assertEqual(self.posted_live(), [B])
        self.assertEqual(self.cycle_errors(), ["1"])

    def test_reason_survives_raising_str(self) -> None:
        with self.patch_stage("judge_trigger", StrFails()):
            self.cycle(self.pipeline())
        self.assertEqual(
            self.fenced(), [{"where": "run.trigger", "reason": "StrFails", "video": A}]
        )
        self.assertEqual(self.posted_live(), [B])
        self.assertEqual(self.cycle_errors(), ["1"])

    def test_fenced_video_retried_next_cycle(self) -> None:
        pipeline = self.pipeline()
        with self.patch_stage("write_comment", ValueError("작성기가 터졌습니다")):
            self.cycle(pipeline)
        self.assertIsNone(self.record(A).comment)
        self.assertEqual(self.claude.user_messages(A), [])
        self.cycle(pipeline)
        self.assertEqual(len(self.claude.user_messages(A)), 1)
        self.assertIsNotNone(self.record(A).comment)
        self.assertEqual(self.posted_live(), [B, A])
        self.assertEqual(self.cycle_errors(), ["1", "0"])

    def test_stage_reported_errors_not_counted(self) -> None:
        self.claude.error = RuntimeError("Claude 가 답하지 않습니다")
        self.cycle(self.pipeline())
        where = [fields["video"] for fields in self.lines(Event.ERROR, where="writer.claude")]
        self.assertEqual(where, [A, B])
        self.assertEqual(self.cycle_errors(), ["0"])


class TestChrome(TwoListedCase):
    def test_new_session_per_allowlisted_post_and_closed(self) -> None:
        config = self.load()
        self.cycle(self.pipeline(), config)
        self.assertEqual(self.posted_live(), [A, B])
        self.assertEqual(self.chrome.submits, [watch(A), watch(B)])
        first, second = self.chrome.sessions
        self.assertIsNot(first, second)
        self.assertEqual([first.debug_url, second.debug_url], [config.chrome_debug_url] * 2)
        self.assertEqual([len(first.pages), len(second.pages)], [1, 1])
        self.assertEqual([first.closes, second.closes], [1, 1])

    def test_session_closed_when_post_raises(self) -> None:
        with self.patch_stage("post_video", ValueError("게시가 터졌습니다")):
            self.cycle(self.pipeline())
        self.assertEqual([session.closes for session in self.chrome.sessions], [1, 1])
        self.assertEqual([fields["where"] for fields in self.fenced()], ["run.post"])
        self.assertEqual(self.posted_live(), [B])

    def test_chrome_unreachable_stops_only_that_post(self) -> None:
        self.chrome.unreachable = 1
        self.cycle(self.pipeline())
        (stopped,) = self.lines(Event.ERROR, where="poster")
        self.assertEqual((stopped["video"], stopped["reason"]), (A, "chrome_unreachable"))
        self.assertEqual(self.record(A).attempts, [])
        self.assertEqual(self.posted_live(), [B])
        self.assertEqual([session.closes for session in self.chrome.sessions], [1, 1])
        self.assertEqual(self.cycle_errors(), ["0"])

    def test_out_of_list_never_gets_chrome(self) -> None:
        for dry_run in (False, True):
            with self.subTest(dry_run=dry_run):
                self.setUp()
                self.write_config(allowed=(D,))
                self.show(C, 2000, channel="UC3")
                self.find(C)
                self.cycle(self.pipeline(dry_run=dry_run))
                self.assertEqual(self.chrome.sessions, [])
                saved = {"video": C, "mode": "test", "result": "saved"}
                self.assertEqual(self.lines(Event.POST), [{**saved, "reason": "not_in_allowlist"}])


class TestRunMode(RunCase):
    COMBINATIONS = ((False, False), (True, False), (False, True), (True, True))

    def test_four_combinations_either_turns_test_run_on(self) -> None:
        for dry_run, test_run in self.COMBINATIONS:
            with self.subTest(dry_run=dry_run, test_run=test_run):
                self.setUp()
                self.write_config(test_run=test_run)
                config = self.load()
                expected = dry_run or test_run
                self.assertIs(run.is_test_run(dry_run, config), expected)
                decision = decide_post(A, config.allowed_videos, run.is_test_run(dry_run, config))
                want = (False, "dry_run") if expected else (True, "allowlisted")
                self.assertEqual((decision.live, decision.reason), want)
                self.show(A, 2000)
                with mock.patch.object(run, "post_video") as post:
                    self.cycle(self.pipeline(dry_run=dry_run), config)
                (call,) = post.call_args_list
                self.assertIs(call.kwargs["dry_run"], expected)
                mode = "test" if expected else "live"
                self.assertEqual(
                    self.lines(Event.CYCLE), [{"n": "1", "errors": "0", "mode": mode}]
                )
        # 둘 다 꺼짐 — 진짜 게시 단계로 끝까지, 한 번 누릅니다(Phase 7F 가 손대지 않는 길)
        self.setUp()
        self.show(A, 2000)
        self.cycle(self.pipeline())
        self.assertEqual(self.chrome.submits, [watch(A)])
        self.assertEqual(
            self.lines(Event.POST, video=A, result="posted"),
            [{"video": A, "mode": "live", "result": "posted", "reason": "allowlisted"}],
        )

    def test_config_cannot_turn_dry_run_off(self) -> None:
        config = self.load()
        self.assertIs(config.test_run, False)
        self.assertIs(run.is_test_run(True, config), True)
        self.show(A, 2000)
        with mock.patch.object(run, "post_video") as post:
            code = self.run_agent("--dry-run", "--once")
        self.assertEqual(code, 0)
        (start,) = self.lines(Event.START)
        self.assertEqual(
            (start["mode"], start["dry_run"], start["test_run"]), ("test", "true", "false")
        )
        self.assertIs(post.call_args.kwargs["dry_run"], True)
        self.assertEqual(self.lines(Event.CYCLE), [{"n": "1", "errors": "0", "mode": "test"}])
        self.assertEqual(self.chrome.submits, [])

    def test_test_run_hands_listed_video_a_fresh_session_opener(self) -> None:
        self.write_config(test_run=True)
        config = self.load()
        self.show(A, 2000)
        seen: list[tuple[str, object, object, int]] = []

        def post(record: object, **kwargs: object) -> None:
            opener = kwargs["open_page"]
            seen.append((record.video_id, kwargs["dry_run"], opener, opener.__self__.closes))

        with mock.patch.object(run, "post_video", side_effect=post):
            self.cycle(self.pipeline(), config)
        (session,) = self.chrome.sessions
        ((video_id, dry_run, opener, closes_during_post),) = seen
        self.assertEqual(video_id, A)
        self.assertIs(dry_run, True)
        self.assertEqual(session.debug_url, config.chrome_debug_url)
        self.assertEqual(opener, session.new_page)
        self.assertEqual((closes_during_post, session.closes), (0, 1))

    def test_test_run_never_clicks(self) -> None:
        for dry_run, test_run in self.COMBINATIONS[1:]:
            with self.subTest(dry_run=dry_run, test_run=test_run):
                self.setUp()
                self.write_config(test_run=test_run)
                self.show(A, 2000, channel="UC1")
                self.show(B, 2000, channel="UC2")
                self.cycle(self.pipeline(dry_run=dry_run))
                self.assertEqual(self.chrome.submits, [])
                self.assertEqual(self.lines(Event.POST, mode="live"), [])


class TestOperatingRules(RunCase):
    def test_one_comment_per_video(self) -> None:
        config = self.load()
        self.show(A, 2000)
        pipeline = self.pipeline()
        self.cycle(pipeline, config)
        self.cycle(pipeline, config)
        self.assertEqual(self.chrome.submits, [watch(A)])
        self.assertEqual(len(self.claude.user_messages(A)), 1)
        expected = self.store.check_post(A, "UC1", self.clock.now, config.limits, live=True)
        self.assertEqual(
            self.lines(Event.SKIP, video=A), [{"video": A, "reason": expected.reason}]
        )

    def test_daily_cap(self) -> None:
        self.write_config(daily_max_comments=1)
        config = self.load()
        self.show(A, 2000, channel="UC1")
        self.show(B, 2000, channel="UC2")
        self.cycle(self.pipeline(), config)
        self.assertEqual(self.posted_live(), [A])
        expected = self.store.check_post(B, "UC2", self.clock.now, config.limits, live=True)
        self.assertEqual(expected.reason, "daily_cap")
        self.assertEqual(
            self.lines(Event.SKIP, video=B), [{"video": B, "reason": expected.reason}]
        )
        self.assertEqual(self.record(B).attempts, [])

    def test_channel_cooldown(self) -> None:
        config = self.load()
        self.show(A, 2000, channel="UC1")
        self.show(B, 2000, channel="UC1")
        self.cycle(self.pipeline(), config)
        self.assertEqual(self.posted_live(), [A])
        expected = self.store.check_post(B, "UC1", self.clock.now, config.limits, live=True)
        self.assertEqual(expected.reason, "channel_cooldown")
        self.assertEqual(
            self.lines(Event.SKIP, video=B), [{"video": B, "reason": expected.reason}]
        )
        self.assertEqual(self.record(B).attempts, [])

    def test_allowlist_enforced_in_log(self) -> None:
        self.write_config(allowed=(A,))
        self.show(A, 2000, channel="UC1")
        self.show(C, 2000, channel="UC3")
        self.show(D, 2000, channel="UC4")
        self.find(C, D)
        pipeline = self.pipeline()
        self.cycle(pipeline)
        self.cycle(pipeline)
        listed = run._allowed(self.load())
        posts = [fields for _, event, fields in read_log(self.log_path) if event is Event.POST]
        live = [fields["video"] for fields in posts if fields["mode"] == "live"]
        self.assertEqual(live, [A, A])  # reserved → posted
        self.assertLessEqual(set(live), listed)
        self.assertEqual(
            [(fields["video"], fields["reason"]) for fields in posts if fields["mode"] == "test"],
            [(C, "not_in_allowlist"), (D, "not_in_allowlist")],
        )


class TestStages(RunCase):
    def bump(self, video_id: str, views: int) -> None:
        """다음 videos.list 의 조회수만 바꿉니다 — 업로드 시각은 그대로."""
        self.api.videos[video_id]["statistics"]["viewCount"] = str(views)

    def test_classified_once(self) -> None:
        self.show(A, 2000)
        pipeline = self.pipeline()
        self.cycle(pipeline)
        self.cycle(pipeline)
        self.assertEqual(self.jev.asked(A), 1)
        self.assertEqual(len(self.lines(Event.CLASSIFY, video=A)), 1)
        self.assertIs(self.record(A).classification.verdict, Verdict.YES)

    def test_classify_hold_stored_not_asked_again(self) -> None:
        self.jev.classify[A] = response(noul=0.5)
        self.show(A, 2000)
        pipeline = self.pipeline()
        self.cycle(pipeline)
        self.cycle(pipeline)
        self.assertEqual(self.jev.asked(A), 1)
        classification = self.record(A).classification
        self.assertIs(classification.verdict, Verdict.HOLD)
        self.assertTrue(classification.reason.startswith("확신 낮음"), classification)
        self.assertEqual(self.lines(Event.ERROR, where="classify"), [])
        self.assertEqual(self.claude.user_messages(A), [])

    def test_error_hold_not_stored_and_asked_again_next_cycle(self) -> None:
        self.jev.classify[A] = JevError("TypeSafeError 503")
        self.show(A, 2000)
        pipeline = self.pipeline()
        self.cycle(pipeline)
        (line,) = self.lines(Event.CLASSIFY, video=A)
        self.assertEqual((line["verdict"], line["reason"]), ("hold", "API 오류: TypeSafeError 503"))
        self.assertEqual(
            self.lines(Event.ERROR, where="classify"),
            [{"where": "classify", "reason": "API 오류: TypeSafeError 503", "video": A}],
        )
        self.assertIsNone(self.record(A).classification)
        del self.jev.classify[A]
        self.cycle(pipeline)
        self.assertEqual(self.jev.asked(A), 2)
        self.assertIs(self.record(A).classification.verdict, Verdict.YES)
        self.assertEqual([fields["errors"] for fields in self.lines(Event.CYCLE)], ["0", "0"])

    def test_trigger_rejudged_each_new_sample_with_per_hour(self) -> None:
        self.show(C, 2000, channel="UC3")
        self.find(C)
        pipeline = self.pipeline()
        self.cycle(pipeline)
        self.bump(C, 2100)
        self.cycle(pipeline)
        record = self.record(C)
        first, second = record.view_history

        def rate(gained: int, start: datetime, end: datetime) -> str:
            return f"{gained * 3_600_000_000 / ((end - start) // timedelta(microseconds=1)):.2f}"

        lines = self.lines(Event.TRIGGER, video=C)
        self.assertEqual(
            [(fields["verdict"], fields["reason"], fields["per_hour"]) for fields in lines],
            [
                ("yes", "views_per_hour", rate(2000, record.published_at, first.at)),
                ("no", "too_slow", rate(100, first.at, second.at)),
            ],
        )
        self.assertNotIn("rule_verdict", lines[0])
        self.assertEqual((record.trigger.verdict, record.trigger.reason), (Verdict.NO, "too_slow"))

    def test_allowlisted_timing_exempt_with_rule_verdict(self) -> None:
        cases = (
            ("yes", "views_per_hour", 2000, 2 * HOUR),
            ("no", "views_below_min", 500, 2 * HOUR),
            ("hold", "too_few_samples", 2000, -HOUR),  # 미래 업로드 — 첫 표본을 잴 수 없음
        )
        for verdict, reason, views, age in cases:
            with self.subTest(rule=verdict):
                self.setUp()
                self.show(A, views, channel="UC1", age=age)
                self.show(C, views, channel="UC3", age=age)
                self.find(C)
                self.cycle(self.pipeline())
                (listed,) = self.lines(Event.TRIGGER, video=A)
                self.assertEqual(
                    listed,
                    {
                        "video": A,
                        "verdict": "yes",
                        "reason": "allowlisted",
                        "per_hour": listed["per_hour"],
                        "rule_verdict": verdict,
                        "rule_reason": reason,
                    },
                )
                (twin,) = self.lines(Event.TRIGGER, video=C)
                self.assertEqual(
                    twin,
                    {
                        "video": C,
                        "verdict": verdict,
                        "reason": reason,
                        "per_hour": listed["per_hour"],
                    },
                )
                self.assertEqual(
                    (self.record(A).trigger.verdict, self.record(A).trigger.reason),
                    (Verdict.YES, "allowlisted"),
                )
                self.assertEqual(len(self.claude.user_messages(A)), 1)
                self.assertEqual(len(self.claude.user_messages(C)), 1 if verdict == "yes" else 0)

    def test_top_comments_passed_to_writer_transcript_empty(self) -> None:
        self.api.comments[A] = ["답장 세 시간 장면 공감해요", "둘째 인기 댓글"]
        self.show(A, 2000)
        self.cycle(self.pipeline())
        (message,) = self.claude.user_messages(A)
        self.assertIn(
            "<top_comments>\n<comment>답장 세 시간 장면 공감해요</comment>\n"
            "<comment>둘째 인기 댓글</comment>\n</top_comments>",
            message,
        )
        self.assertNotIn("<transcript>", message)
        (query,) = [query for endpoint, query in self.api.calls if endpoint == "commentThreads"]
        self.assertEqual((query["videoId"], query["maxResults"]), (A, str(TOP_COMMENTS_MAX)))

    def test_comments_disabled_writes_with_empty_top_comments(self) -> None:
        self.api.comments[A] = 403
        self.show(A, 2000)
        self.cycle(self.pipeline())
        (message,) = self.claude.user_messages(A)
        self.assertNotIn("<top_comments>", message)
        self.assertIsNotNone(self.record(A).comment)
        self.assertEqual(self.lines(Event.ERROR), [])

    def test_top_comments_failure_skips_writing(self) -> None:
        for case in ("http", "quota"):
            with self.subTest(case=case):
                self.setUp()
                if case == "http":
                    self.api.comments[A] = 500
                else:
                    self.seed_quota(9999)  # 검색은 막히고 videos.list 한 번만 남음
                self.show(A, 2000)
                self.cycle(self.pipeline())
                self.assertEqual(self.claude.calls, [])
                self.assertIsNone(self.record(A).comment)
                if case == "http":
                    (failed,) = self.lines(Event.ERROR, video=A)
                    self.assertEqual(
                        (failed["where"], failed["reason"]),
                        ("commentThreads.list", "HTTP 500 backendError"),
                    )
                else:
                    (held,) = self.lines(Event.QUOTA, video=A)
                    self.assertEqual(
                        (held["call"], held["counter"]), ("commentThreads.list", "units")
                    )
                self.assertEqual([fields["errors"] for fields in self.lines(Event.CYCLE)], ["0"])

    def test_previous_comments_from_store(self) -> None:
        self.show(A, 2000)
        pipeline = self.pipeline()
        self.cycle(pipeline)
        first = self.record(A).comment.text
        self.show(B, 2000, channel="UC2")
        self.cycle(pipeline)
        (message,) = self.claude.user_messages(B)
        self.assertIn(
            f"<my_previous_comments>\n<comment>{first}</comment>\n</my_previous_comments>", message
        )

    def test_out_of_list_comment_kept_in_store_and_log(self) -> None:
        self.show(C, 2000, channel="UC3")
        self.find(C)
        self.cycle(self.pipeline())
        text = self.record(C).comment.text
        (line,) = self.lines(Event.COMMENT, video=C)
        self.assertEqual((line["concern"], line["text"]), (CONCERN, text))
        self.assertEqual(
            self.lines(Event.POST, video=C),
            [{"video": C, "mode": "test", "result": "saved", "reason": "not_in_allowlist"}],
        )

    def test_untracked_old_record_not_rejudged(self) -> None:
        pipeline = self.pipeline()
        judged = T0 - 12 * HOUR
        old = VideoRecord(
            video_id=D,
            channel_id="UC4",
            title=title_of(D),
            description="",
            published_at=T0 - 13 * HOUR,
            detected_at=judged,
            keyword=KEYWORD,
            view_history=[ViewSample(judged, 800)],
            classification=Judgement(Verdict.YES, "연애 고민 상담", judged),
            trigger=Judgement(Verdict.NO, "views_below_min", judged),
        )
        self.store.put(old)
        self.show(D, 3000, channel="UC4", age=13 * HOUR)
        self.cycle(pipeline)
        self.assertNotIn(D, self.api.sampled())
        self.assertEqual(self.lines(Event.TRIGGER, video=D), [])
        self.assertEqual(self.record(D), old)


if __name__ == "__main__":
    unittest.main()
