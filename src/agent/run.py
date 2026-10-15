"""실행 진입점 — 다섯 단계(탐지 → 판별 → 타이밍 → 작성 → 게시)를 주기 루프 하나 · 한 스레드에서 잇습니다.

    PYTHONPATH=src python3 -m agent.run [--dry-run] [--once]

켜기 차례는 단일 실행 잠금 → SDK 둘 → 비밀 값 셋 → config.yaml → 저장소 → START → run_loop 입니다.
저장소 · 쿼터 장부 · 로그는 데이터 폴더마다 한 벌만 만들어 모든 단계가 함께 씁니다. 테스트 실행은
--dry-run 또는 설정의 test_run 이고, 설정은 --dry-run 을 끄지 못합니다. 다시 읽기가 거절된 동안은
실제 게시만 멈추고(명단 영상까지 크롬 없이 테스트 저장), 받으면 다음 사이클부터 돌아옵니다.
한 영상에서 난 예외는 그 영상의 ERROR 한 줄로 남기고 다음 영상으로 갑니다 — 줄에는 예외 자신의
종류와 메시지만 쓰고 __context__ · __cause__ · traceback 은 따라가지 않습니다(R6).
계약 '실행 진입점 — `run.py` (Phase 7)' 절.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, TextIO

from agent.chrome import ChromeSession
from agent.classifier import Ask, classify, is_error_hold, sdk_ask
from agent.config import Config, ConfigError, load_config
from agent.env import EnvError, require_secret
from agent.guard import allowed_video_ids
from agent.logbook import Event, Logbook
from agent.models import Judgement, Verdict, VideoRecord
from agent.poster import CommentPage, PageError, post_video
from agent.scheduler import run_loop
from agent.store import Store, StoreError
from agent.trigger import judge_trigger, views_per_hour
from agent.watcher import Watcher
from agent.writer import (
    TOP_COMMENTS_MAX,
    ClaudeClient,
    SelfCheck,
    anthropic_client,
    jev_self_check,
    write_comment,
)
from agent.youtube import QuotaError, QuotaExhausted, QuotaLedger, YouTubeClient, YouTubeError

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path("config.yaml")
ENV_PATH = Path(".env")
STORE_PATH = Path("data/videos.json")
QUOTA_PATH = Path("data/quota.json")
LOCK_PATH = Path("data/agent.lock")
LOG_PATH = Path("logs/agent.log")
SECRET_NAMES = ("YOUTUBE_API_KEY", "TYPESAFE_API_KEY", "ANTHROPIC_API_KEY")
ALLOWLISTED = "allowlisted"          # TRIGGER reason of a listed video
CONFIG_REJECTED = "config_rejected"  # POST reason of a listed video while the config is rejected
CHROME_WITHHELD = "chrome_withheld"  # PageError reason of the opener handed to out-of-list videos
REASON_MAX = 200
STAGE_CLASSIFY, STAGE_TRIGGER = "run.classify", "run.trigger"
STAGE_WRITE, STAGE_POST = "run.write", "run.post"
# module, pip package — checked before secrets
SDK_MODULES = (("typesafe_sdk", "typesafe-sdk"), ("anthropic", "anthropic"))
EXIT_OK, EXIT_SETUP, EXIT_LOCKED, EXIT_INTERRUPTED = 0, 2, 3, 130


@dataclass(frozen=True)
class Options:
    dry_run: bool
    once: bool


def parse_args(argv: Sequence[str]) -> Options:
    """명령 줄 — --dry-run(테스트 실행) · --once(사이클 한 번)."""
    parser = argparse.ArgumentParser(
        prog="python3 -m agent.run",
        description="마케팅 에이전트 — 탐지 → 판별 → 타이밍 → 작성 → 게시를 주기마다 돌립니다.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="테스트 실행 — 게시 직전까지만 돌고 실제 게시는 하지 않습니다(저장만)",
    )
    parser.add_argument("--once", action="store_true", help="사이클 한 번만 돌고 끝냅니다")
    namespace = parser.parse_args(list(argv))
    return Options(dry_run=namespace.dry_run, once=namespace.once)


class ChromeConnection(Protocol):
    def new_page(self) -> CommentPage: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class Services:
    ask: Ask                                       # jev — classify and self check share it
    claude: ClaudeClient
    youtube: YouTubeClient
    chrome: Callable[[str], ChromeConnection]      # debug_url -> one connection (ChromeSession)


class MissingSdkError(ImportError):
    """SDK(typesafe-sdk · anthropic)가 설치되지 않음 — 운영은 켜지지 않습니다(종료 코드 2)."""


def connect_real(
    root: Path,
    environ: Mapping[str, str],
    find_spec: Callable[[str], object] = importlib.util.find_spec,
) -> Services:
    """진짜 서비스 — SDK 둘을 먼저 보고, 비밀 값 셋(환경 변수, 없으면 .env)을 읽어 잇습니다."""
    for module, package in SDK_MODULES:
        if find_spec(module) is None:
            raise MissingSdkError(f"{package} 가 설치되지 않았습니다 — pip install -r requirements.txt")
    youtube_key, jev_key, claude_key = (
        require_secret(name, root / ENV_PATH, environ) for name in SECRET_NAMES
    )
    os.environ["TYPESAFE_API_KEY"] = jev_key  # jev SDK 는 환경 변수만 읽습니다
    return Services(
        ask=sdk_ask,
        claude=anthropic_client(claude_key),
        youtube=YouTubeClient(youtube_key, QuotaLedger(root / QUOTA_PATH)),
        chrome=ChromeSession,
    )


def short_reason(exc: BaseException) -> str:
    """`<예외 종류>: <메시지, 공백을 모아 REASON_MAX 자까지>` — 메시지가 없으면 종류만.

    예외 자신만 읽고 __context__ · __cause__ · __traceback__ 은 보지 않습니다(R6).
    """
    try:
        text = str(exc)
    except Exception:  # __str__ 이 터져도 울타리는 줄을 남깁니다
        text = ""
    text = " ".join(text.split())[:REASON_MAX]
    name = type(exc).__name__
    return f"{name}: {text}" if text else name


def echo_stream(stream: TextIO) -> TextIO:
    """화면 출력 — 콘솔 인코딩이 못 쓰는 글자를 `\\` 이스케이프로 바꿔 쓰게 합니다(Phase 1 HC1-2 R4)."""
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(errors="backslashreplace")
    return stream


def is_test_run(dry_run: object, config: Config) -> bool:
    """--dry-run 또는 test_run 중 하나라도 정확히 False 가 아니면 테스트 실행입니다."""
    return dry_run is not False or config.test_run is not False


def _allowed(config: Config) -> frozenset[str]:
    """명단 영상 ID — 게시 거절 길 밖에서 허용 목록을 읽는 단 한 곳(live 는 정하지 않음)."""
    return allowed_video_ids(config.allowed_videos)


def _chrome_withheld() -> CommentPage:
    """명단 밖 영상에 넘기는 탭 여는 함수 — 크롬을 열지 않고 언제나 멈춥니다."""
    raise PageError(CHROME_WITHHELD, "명단 밖 영상에는 크롬을 열지 않습니다")


class LockedError(Exception):
    """단일 실행 잠금을 다른 에이전트가 쥐고 있음 — 종료 코드 3."""


class RunLock:
    """같은 데이터 폴더에 에이전트 하나 — 운영체제 잠금이라 프로세스가 죽으면 풀립니다."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._handle: TextIO | None = None

    def __enter__(self) -> RunLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self._path, "a+", encoding="utf-8")
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise LockedError(str(self._path)) from None
        self._handle = handle
        return self

    def __exit__(self, *exc: object) -> None:
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


class ConfigReloader:
    """run_loop 의 reload 자리 — 거절을 기억하고(rejected), 받으면 잊습니다."""

    rejected: bool

    def __init__(self, path: Path, load: Callable[[Path], Config] = load_config) -> None:
        self._path = Path(path)
        self._load = load
        self.rejected = False

    def __call__(self) -> Config:
        try:
            config = self._load(self._path)
        except ConfigError:
            self.rejected = True
            raise
        self.rejected = False
        return config


class Pipeline:
    """한 사이클 — 탐지 뒤 새 조회수 기록이 붙은 영상마다 판별 → 타이밍 → 작성 → 게시."""

    def __init__(
        self,
        *,
        store: Store,
        logbook: Logbook,
        watcher: Watcher,
        services: Services,
        clock: Callable[[], datetime],
        dry_run: bool,
        reloader: ConfigReloader,
        repo_root: Path,
    ) -> None:
        self._store = store
        self._logbook = logbook
        self._watcher = watcher
        self._services = services
        self._clock = clock
        self._dry_run = dry_run
        self._reloader = reloader
        self._repo_root = repo_root
        self._cycles = 0

    def cycle(self, config: Config) -> None:
        """run_loop 의 cycle 자리. 탐지의 예외는 run_loop 의 on_error("cycle") 로 갑니다(CYCLE 없음)."""
        self._cycles += 1
        before = {r.video_id: len(r.view_history) for r in self._store.records()}
        self._watcher.cycle(config)
        allowed = _allowed(config)
        test_run = is_test_run(self._dry_run, config)
        rejected = self._reloader.rejected
        check = jev_self_check(self._services.ask, config.classifier.model)
        errors = 0
        for record in self._store.records():
            if len(record.view_history) > before.get(record.video_id, 0):
                if not self._process(
                    record.video_id,
                    config,
                    allowed=allowed,
                    test_run=test_run,
                    rejected=rejected,
                    check=check,
                ):
                    errors += 1
        self._logbook.write(
            Event.CYCLE,
            n=self._cycles,
            errors=errors,
            mode="test" if test_run or rejected else "live",
        )

    def on_error(self, where: str, exc: Exception) -> None:
        """run_loop 의 on_error 자리 — 예외 자신의 종류와 메시지만 씁니다(R6)."""
        self._logbook.write(Event.ERROR, where=where, reason=short_reason(exc))

    def _process(
        self,
        video_id: str,
        config: Config,
        *,
        allowed: frozenset[str],
        test_run: bool,
        rejected: bool,
        check: SelfCheck,
    ) -> bool:
        """영상 하나의 판별 → 타이밍 → 작성 → 게시. 울타리가 예외를 받았으면 False."""
        stage = STAGE_CLASSIFY
        try:
            record = self._classify(video_id, config)
            stage = STAGE_TRIGGER
            record = self._time(record, config, allowed)
            stage = STAGE_WRITE
            record = self._write(record, config, check)
            stage = STAGE_POST
            self._post(record, config, allowed=allowed, test_run=test_run, rejected=rejected)
        except Exception as exc:  # 영상 하나의 울타리 — BaseException 은 그대로 올라갑니다
            self._logbook.write(Event.ERROR, where=stage, reason=short_reason(exc), video=video_id)
            return False
        return True

    def _classify(self, video_id: str, config: Config) -> VideoRecord:
        """판별은 영상마다 한 번 — 오류 보류는 저장하지 않아 다음 새 기록 때 다시 묻습니다."""
        record = self._store.get(video_id)
        if record is None:
            raise LookupError(video_id)
        if record.classification is None:
            judgement = classify(record, config, self._services.ask, self._clock())
            self._logbook.write(
                Event.CLASSIFY, video=video_id, verdict=judgement.verdict, reason=judgement.reason
            )
            if is_error_hold(judgement):
                self._logbook.write(
                    Event.ERROR, where="classify", reason=judgement.reason, video=video_id
                )
                return record
            record.classification = judgement
            self._store.put(record)
        return record

    def _time(self, record: VideoRecord, config: Config, allowed: frozenset[str]) -> VideoRecord:
        """새 기록마다 다시 판정합니다. 명단 영상은 규칙 판정을 함께 적고 통과합니다."""
        now = self._clock()
        rule = judge_trigger(record, config.trigger, now)
        per_hour = views_per_hour(record)
        exempt = record.video_id in allowed
        if exempt:
            record.trigger = Judgement(Verdict.YES, ALLOWLISTED, now)
            self._logbook.write(
                Event.TRIGGER,
                video=record.video_id,
                verdict=Verdict.YES,
                reason=ALLOWLISTED,
                per_hour=per_hour,
                rule_verdict=rule.verdict,
                rule_reason=rule.reason,
            )
        else:
            record.trigger = rule
            self._logbook.write(
                Event.TRIGGER,
                video=record.video_id,
                verdict=rule.verdict,
                reason=rule.reason,
                per_hour=per_hour,
            )
        self._store.put(record)
        return record

    def _write(self, record: VideoRecord, config: Config, check: SelfCheck) -> VideoRecord:
        """판별 · 타이밍이 모두 yes 이고 댓글이 없을 때만 씁니다. 인기 댓글을 못 받으면 이번엔 쉽니다."""
        if (
            record.classification is None
            or record.classification.verdict is not Verdict.YES
            or record.trigger is None
            or record.trigger.verdict is not Verdict.YES
            or record.comment is not None
        ):
            return record
        now = self._clock()
        try:
            comments = self._services.youtube.top_comments(
                record.video_id, now, config.limits, TOP_COMMENTS_MAX
            )
        except QuotaExhausted as exc:
            self._logbook.write(
                Event.QUOTA,
                used=exc.used,
                limit=exc.limit,
                call=exc.call,
                counter=exc.counter,
                video=record.video_id,
            )
            return record
        except YouTubeError as exc:
            self._logbook.write(
                Event.ERROR, where=exc.call, reason=exc.reason, video=record.video_id
            )
            return record
        result = write_comment(
            record,
            config=config.comment,
            claude=self._services.claude,
            check=check,
            previous=self._store.comments(),
            logbook=self._logbook,
            now=now,
            transcript="",
            top_comments=comments or (),
        )
        if result.draft is not None:
            record.comment = result.draft
            self._store.put(record)
        return record

    def _post(
        self,
        record: VideoRecord,
        config: Config,
        *,
        allowed: frozenset[str],
        test_run: bool,
        rejected: bool,
    ) -> None:
        """댓글이 있으면 게시 단계로 — 명단 영상에만 게시마다 새 크롬 연결을 넘기고 끝나면 놓습니다."""
        if record.comment is None:
            return
        if record.video_id not in allowed:
            post_video(
                record,
                config=config,
                dry_run=test_run,
                store=self._store,
                logbook=self._logbook,
                open_page=_chrome_withheld,
                clock=self._clock,
                repo_root=self._repo_root,
            )
            return
        session = self._services.chrome(config.chrome_debug_url)
        try:
            post_video(
                record,
                config=config,
                dry_run=test_run,
                store=self._store,
                logbook=self._logbook,
                open_page=session.new_page,
                clock=self._clock,
                repo_root=self._repo_root,
            )
        finally:
            session.close()


def run_agent(
    options: Options,
    *,
    root: Path,
    services: Services,
    clock: Callable[[], datetime],
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
    echo: TextIO | None = None,
) -> int:
    """설정 · 저장소를 열고 START 를 쓴 뒤 주기 루프를 돌립니다. 끝에는 언제나 STOP."""
    logbook = Logbook(root / LOG_PATH, clock, echo)
    reloader = ConfigReloader(root / CONFIG_PATH)
    try:
        config = load_config(root / CONFIG_PATH)
    except ConfigError as exc:
        logbook.write(Event.ERROR, where="config", reason=short_reason(exc))
        return EXIT_SETUP
    try:
        store = Store(root / STORE_PATH)
    except StoreError as exc:
        logbook.write(Event.ERROR, where="store", reason=short_reason(exc))
        return EXIT_SETUP
    watcher = Watcher(store, logbook, services.youtube, clock)
    pipeline = Pipeline(
        store=store,
        logbook=logbook,
        watcher=watcher,
        services=services,
        clock=clock,
        dry_run=options.dry_run,
        reloader=reloader,
        repo_root=root,
    )
    logbook.write(
        Event.START,
        mode="test" if is_test_run(options.dry_run, config) else "live",
        allowed=len(_allowed(config)),
        interval_min=config.poll_interval_min,
        dry_run=options.dry_run,
        once=options.once,
        test_run=config.test_run,
    )
    stop = "error"
    try:
        run_loop(
            pipeline.cycle,
            reloader,
            config,
            on_error=pipeline.on_error,
            sleep=sleep,
            monotonic=monotonic,
            max_cycles=1 if options.once else None,
        )
        stop = "once"
        return EXIT_OK
    except KeyboardInterrupt:
        stop = "interrupted"
        return EXIT_INTERRUPTED
    finally:
        logbook.write(Event.STOP, reason=stop)


def main(
    argv: Sequence[str] | None = None,
    *,
    root: Path = ROOT,
    environ: Mapping[str, str] | None = None,
) -> int:
    """잠금 → 서비스 → run_agent. 종료 코드 0 끝 · 2 켤 수 없음 · 3 이미 실행 중 · 130 Ctrl-C."""
    options = parse_args(sys.argv[1:] if argv is None else argv)
    env = os.environ if environ is None else environ
    lock_path = root / LOCK_PATH
    try:
        with RunLock(lock_path):
            try:
                services = connect_real(root, env)
            except (EnvError, QuotaError, ImportError, ValueError) as exc:
                print(f"에이전트를 시작할 수 없습니다 — {short_reason(exc)}", file=sys.stderr)
                return EXIT_SETUP
            return run_agent(
                options,
                root=root,
                services=services,
                clock=lambda: datetime.now(timezone.utc),
                echo=echo_stream(sys.stdout),
            )
    except LockedError:
        print(f"이미 실행 중입니다 — {lock_path} 을 다른 에이전트가 쥐고 있습니다", file=sys.stderr)
        return EXIT_LOCKED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
