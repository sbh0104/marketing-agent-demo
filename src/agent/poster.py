"""게시 단계 — 허용된 영상 하나에 댓글을 달고, 보이는지 확인합니다 (계약 6절).

실제 게시 여부는 오직 decide_post 가 정합니다. 크롬에는 받은 주소 글자가 아니라
decision.video_id 로 만든 watch 주소만 열고, 댓글을 입력한 뒤 클릭 바로 직전에 그 페이지의
주소(page.url)로 decide_post 를 한 번 더 부릅니다. live 가 아니거나 다른 영상이면 누르지 않고
테스트 모드로 저장합니다.

테스트 실행의 허용 목록 영상(decide_post 의 이유 dry_run)은 리허설합니다 — 같은 watch 주소를 열고
입력해 게시 버튼까지 본 뒤, 누르지 않고 화면을 남기고 입력한 글을 지웁니다. 다시 확인이 실제 게시라면
누르지 않았을 화면이면 ERROR 한 줄과 함께 멈춥니다. 리허설은 저장소를 받지 않으므로 시도를 남기지
않습니다. 허용 목록 밖 영상은 언제나 크롬 없이 테스트 모드로 저장합니다.

예약 전에 멈추면(크롬 연결 · 영상 열기 · 댓글 칸 준비 · 입력 · 버튼 확인) 아무것도 누르지 않았으므로
저장소는 그대로 두고 ERROR 줄 하나와 화면 캡처만 남깁니다 — 다음 주기에 다시 시도합니다.
예약 뒤 결과를 모르면(클릭 중 오류 · 확인 오류 · 댓글이 안 보임 · Ctrl-C) 예약을 그대로
reserved 로 둡니다. 확정되지 않은 예약은 게시로 셉니다.

브라우저는 CommentPage 뒤에 있어 가짜로 시험할 수 있습니다. 실제 구현은 agent.chrome 입니다.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from agent.config import Config
from agent.guard import PostDecision, decide_post
from agent.logbook import Event, Logbook
from agent.models import VideoRecord
from agent.store import Store

WATCH_URL = "https://www.youtube.com/watch?v={video_id}"
SCREENSHOT_DIR = "logs/screenshots"
DETAIL_MAX = 200

# 멈춘 자리
BEFORE_CLICK = "before_click"
AFTER_CLICK = "after_click"

# 리허설 갈래의 신호 — src/agent/guard.py (decide_post) 가 테스트 실행의 허용 목록 영상에만 주는 이유
DRY_RUN = "dry_run"

# 원인 이름 — 로그에 따옴표 없이 쓰이도록 소문자 ASCII
NO_COMMENT = "no_comment"
PAGE_MISMATCH = "page_mismatch"
PLAYWRIGHT_MISSING = "playwright_missing"
CHROME_UNREACHABLE = "chrome_unreachable"
LOGIN_REQUIRED = "login_required"
COMMENTS_DISABLED = "comments_disabled"
COMMENT_BOX_MISSING = "comment_box_missing"
POST_BUTTON_MISSING = "post_button_missing"
PAGE_ERROR = "page_error"
CLICK_UNKNOWN = "click_unknown"
CONFIRM_ERROR = "confirm_error"
NOT_CONFIRMED = "not_confirmed"
CLEAR_FAILED = "clear_failed"  # 리허설의 글 지우기 실패 — 원인이 아니라 rehearsed 줄 detail 의 머리


class PageError(Exception):
    """화면 단계가 *누르지 않고* 멈췄을 때 — reason 은 원인 이름, detail 은 덧붙일 설명."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


class CommentPage(Protocol):
    """댓글을 다는 브라우저 탭 하나 — 실제 구현은 agent.chrome.YouTubePage 입니다."""

    @property
    def url(self) -> str:
        """지금 탭의 주소."""
        ...

    def open(self, url: str) -> None:
        """주소를 엽니다."""
        ...

    def prepare_comment(self, text: str) -> None:
        """댓글 칸까지 내려가 열고 text 를 입력한 뒤, 게시 버튼이 켜졌는지 봅니다.

        어느 단계에서든 멈추면 PageError 를 냅니다.
        """
        ...

    def clear_comment(self) -> None:
        """prepare_comment 가 입력한 글을 지웁니다 — 아무것도 누르지 않습니다.

        입력 칸을 찾지 못하는 등 멈추면 PageError 를 냅니다.
        """
        ...

    def submit(self) -> None:
        """게시 버튼을 누릅니다 — 이동도 기다림도 없이.

        누르기 전에 멈췄을 때만 PageError 를 냅니다. 그 밖의 예외는 결과를 모른다는 뜻입니다.
        """
        ...

    def confirm_posted(self, text: str) -> bool:
        """방금 단 댓글이 보이면 True."""
        ...

    def screenshot(self, path: Path) -> None:
        """화면을 path 에 PNG 로 저장합니다."""
        ...

    def close(self) -> None:
        """탭을 닫습니다."""
        ...


@dataclass(frozen=True)
class PostOutcome:
    """게시 단계 결과. result 는 skipped · saved · rehearsed · stopped · reserved · posted · failed
    중 하나.

    rehearsed 는 테스트 실행의 리허설이 게시 버튼 앞에서 멈췄다는 뜻입니다(글 지우기 실패는 줄의 detail).
    stopped 는 크롬 길이 예약 전에(리허설이면 끝나기 전에, 또는 다시 확인이 맞지 않아) 멈춰 저장소가
    그대로라는 뜻입니다.
    """

    video_id: str
    mode: str
    result: str
    reason: str
    screenshot: str | None = None


def screenshot_path(video_id: str, at: datetime) -> str:
    """화면 캡처의 저장소 기준 상대 경로(POSIX) — 시각은 UTC."""
    return f"{SCREENSHOT_DIR}/{video_id}-{at.astimezone(timezone.utc):%Y%m%dT%H%M%SZ}.png"


def post_video(
    record: VideoRecord,
    *,
    config: Config,
    dry_run: bool,
    store: Store,
    logbook: Logbook,
    open_page: Callable[[], CommentPage],
    clock: Callable[[], datetime],
    repo_root: Path,
) -> PostOutcome:
    """영상 하나를 계약 6절 순서대로 게시합니다 — 판단 · 한도 · 테스트 모드(허용 목록 영상은 리허설) · 실제 게시."""
    if record.comment is None:
        logbook.write(Event.SKIP, video=record.video_id, reason=NO_COMMENT)
        return PostOutcome(record.video_id, "test", "skipped", NO_COMMENT)
    decision = decide_post(record.video_id, config.allowed_videos, dry_run)
    if decision.video_id is None:
        logbook.write(Event.SKIP, video=record.video_id, reason=decision.reason)
        return PostOutcome(record.video_id, "test", "skipped", decision.reason)
    check = store.check_post(
        decision.video_id, record.channel_id, clock(), config.limits, live=decision.live
    )
    if not check.allowed:
        logbook.write(Event.SKIP, video=decision.video_id, reason=check.reason)
        return PostOutcome(decision.video_id, decision.mode, "skipped", check.reason)
    if not decision.live:
        if decision.reason == DRY_RUN:
            return _rehearse(
                record.comment.text,
                decision,
                config=config,
                dry_run=dry_run,
                logbook=logbook,
                open_page=open_page,
                clock=clock,
                repo_root=repo_root,
            )
        return _save_test(
            decision.video_id, decision.reason, now=clock(), store=store, logbook=logbook
        )
    return _post_live(
        record.comment.text,
        decision,
        config=config,
        dry_run=dry_run,
        store=store,
        logbook=logbook,
        open_page=open_page,
        clock=clock,
        repo_root=repo_root,
    )


def _post_live(
    text: str,
    decision: PostDecision,
    *,
    config: Config,
    dry_run: bool,
    store: Store,
    logbook: Logbook,
    open_page: Callable[[], CommentPage],
    clock: Callable[[], datetime],
    repo_root: Path,
) -> PostOutcome:
    """실제 게시 — 열기 · 입력 → 다시 확인 → 예약 → 클릭 → 확인. 실패 갈래마다 시계는 한 번."""
    video_id = decision.video_id
    page = None
    try:
        try:
            page = open_page()
            page.open(WATCH_URL.format(video_id=decision.video_id))
            page.prepare_comment(text)
            page_url = page.url
        except Exception as exc:  # 클릭 전 — 아무것도 누르지 않았고 저장소도 그대로입니다
            shot = _log_error(
                page, video_id, BEFORE_CLICK, _cause(exc), _detail(exc),
                now=clock(), logbook=logbook, repo_root=repo_root,
            )
            return PostOutcome(video_id, "live", "stopped", _cause(exc), shot)
        recheck = decide_post(page_url, config.allowed_videos, dry_run)
        if not recheck.live:
            return _save_test(
                video_id, recheck.reason, now=clock(), store=store, logbook=logbook,
                page=page, page_url=page_url, repo_root=repo_root,
            )
        if recheck.video_id != decision.video_id:
            return _save_test(
                video_id, PAGE_MISMATCH, now=clock(), store=store, logbook=logbook,
                page=page, page_url=page_url, repo_root=repo_root,
            )
        store.reserve_live(video_id, clock())
        logbook.write(
            Event.POST, video=video_id, mode="live", result="reserved", reason=decision.reason
        )
        try:
            page.submit()
        except PageError as exc:  # 누르기 전에 멈춤 — 게시되지 않았음을 압니다
            now = clock()
            shot = _capture(page, video_id, now, repo_root)
            store.resolve_live(video_id, "failed", now, _cause(exc), shot)
            _write_post(
                logbook, video_id, "live", "failed", _cause(exc),
                screenshot=shot, detail=_detail(exc),
            )
            return PostOutcome(video_id, "live", "failed", _cause(exc), shot)
        except Exception as exc:  # 누르는 중 — 결과를 모릅니다
            shot = _log_error(
                page, video_id, AFTER_CLICK, CLICK_UNKNOWN, _detail(exc),
                now=clock(), logbook=logbook, repo_root=repo_root,
            )
            return PostOutcome(video_id, "live", "reserved", CLICK_UNKNOWN, shot)
        try:
            confirmed = page.confirm_posted(text)
        except Exception as exc:
            shot = _log_error(
                page, video_id, AFTER_CLICK, CONFIRM_ERROR, _detail(exc),
                now=clock(), logbook=logbook, repo_root=repo_root,
            )
            return PostOutcome(video_id, "live", "reserved", CONFIRM_ERROR, shot)
        if confirmed is True:
            store.resolve_live(video_id, "posted", clock(), decision.reason)
            _write_post(logbook, video_id, "live", "posted", decision.reason)
            return PostOutcome(video_id, "live", "posted", decision.reason)
        shot = _log_error(
            page, video_id, AFTER_CLICK, NOT_CONFIRMED, "",
            now=clock(), logbook=logbook, repo_root=repo_root,
        )
        return PostOutcome(video_id, "live", "reserved", NOT_CONFIRMED, shot)
    finally:
        _close_quietly(page)


def _rehearse(
    text: str,
    decision: PostDecision,
    *,
    config: Config,
    dry_run: bool,
    logbook: Logbook,
    open_page: Callable[[], CommentPage],
    clock: Callable[[], datetime],
    repo_root: Path,
) -> PostOutcome:
    """리허설 — 열기 · 입력 · 버튼 확인 → 다시 확인 → 캡처 → 글 지우기. 갈래마다 시계는 한 번.

    게시 버튼은 누르지 않습니다. 저장소를 받지 않으므로 시도도 남기지 않습니다 — 같은 영상을 몇 번이고
    다시 리허설하고, 그 뒤 실제 게시는 그대로 할 수 있습니다. 이름(shown_url 등)이 _post_live 와 다른
    것은 음성 대조 표 tests/mutants.py (MUTANTS) 의 글자가 이 파일에 한 번씩만 나오게 하려는 것입니다.
    """
    video_id = decision.video_id
    page = None
    try:
        try:
            page = open_page()
            page.open(WATCH_URL.format(video_id=video_id))
            page.prepare_comment(text)
            shown_url = page.url
        except Exception as exc:  # 클릭 전 — 누른 것도 저장한 것도 없습니다
            shot = _log_error(
                page, video_id, BEFORE_CLICK, _cause(exc), _detail(exc),
                now=clock(), logbook=logbook, repo_root=repo_root,
            )
            return PostOutcome(video_id, "test", "stopped", _cause(exc), shot)
        recheck = decide_post(shown_url, config.allowed_videos, dry_run)
        if recheck.reason != DRY_RUN:  # 실제 게시였다면 3.2 에서 테스트 저장으로 빠졌을 화면
            missed = recheck.reason
        elif recheck.video_id != video_id:
            missed = PAGE_MISMATCH
        else:
            missed = None
        if missed is not None:  # 리허설 실패 — 저장 없이 ERROR 한 줄, 입력한 글은 지웁니다
            shot = _log_error(
                page, video_id, BEFORE_CLICK, missed, shown_url[:DETAIL_MAX],
                now=clock(), logbook=logbook, repo_root=repo_root,
            )
            _clear(page)
            return PostOutcome(video_id, "test", "stopped", missed, shot)
        shot = _capture(page, video_id, clock(), repo_root)
        failed = _clear(page)
        detail = (
            "" if failed is None
            else f"{CLEAR_FAILED} {_cause(failed)}: {_detail(failed)}"[:DETAIL_MAX]
        )
        _write_post(
            logbook, video_id, "test", "rehearsed", DRY_RUN,
            screenshot=shot, detail=detail, page_url=shown_url,
        )
        return PostOutcome(video_id, "test", "rehearsed", DRY_RUN, shot)
    finally:
        _close_quietly(page)


def _clear(page: CommentPage) -> BaseException | None:
    """입력한 글을 지웁니다 — 못 지우면 그 예외를 돌려줍니다(누른 것은 없으므로 멈추지 않음)."""
    try:
        page.clear_comment()
    except Exception as exc:
        return exc
    return None


def _save_test(
    video_id: str,
    reason: str,
    *,
    now: datetime,
    store: Store,
    logbook: Logbook,
    page: CommentPage | None = None,
    page_url: str | None = None,
    repo_root: Path | None = None,
) -> PostOutcome:
    """테스트 모드 저장(계약 6절 4) — 페이지가 있으면(다시 확인에서 왔으면) 화면도 남깁니다."""
    shot = _capture(page, video_id, now, repo_root)
    store.save_test(video_id, now, reason)
    _write_post(logbook, video_id, "test", "saved", reason, screenshot=shot, page_url=page_url)
    return PostOutcome(video_id, "test", "saved", reason, shot)


def _write_post(
    logbook: Logbook,
    video_id: str,
    mode: str,
    result: str,
    reason: str,
    *,
    screenshot: str | None = None,
    detail: str = "",
    page_url: str | None = None,
) -> None:
    """POST 줄 하나 — 있는 덧붙임만 씁니다. 제어 글자는 로그 형식이 이스케이프합니다."""
    extra: dict[str, object] = {}
    if screenshot is not None:
        extra["screenshot"] = screenshot
    if detail:
        extra["detail"] = detail
    if page_url is not None:
        extra["page_url"] = page_url
    logbook.write(Event.POST, video=video_id, mode=mode, result=result, reason=reason, **extra)


def _log_error(
    page: CommentPage | None,
    video_id: str,
    stage: str,
    reason: str,
    detail: str,
    *,
    now: datetime,
    logbook: Logbook,
    repo_root: Path,
) -> str | None:
    """화면을 남기고 ERROR 줄 하나를 씁니다. 저장소는 건드리지 않습니다."""
    shot = _capture(page, video_id, now, repo_root)
    extra: dict[str, object] = {}
    if shot is not None:
        extra["screenshot"] = shot
    if detail:
        extra["detail"] = detail
    logbook.write(Event.ERROR, where="poster", reason=reason, stage=stage, video=video_id, **extra)
    return shot


def _capture(
    page: CommentPage | None, video_id: str, at: datetime, repo_root: Path | None
) -> str | None:
    """화면 캡처 — 저장소 기준 상대 경로를 돌려줍니다. 페이지가 없거나 실패하면 None."""
    if page is None:
        return None
    rel = screenshot_path(video_id, at)
    try:
        target = Path(repo_root) / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(target)
    except Exception:
        return None
    return rel


def _cause(exc: BaseException) -> str:
    return exc.reason if isinstance(exc, PageError) else PAGE_ERROR


def _detail(exc: BaseException) -> str:
    return (
        exc.detail if isinstance(exc, PageError) else f"{type(exc).__name__}: {exc}"
    )[:DETAIL_MAX]


def _close_quietly(page: CommentPage | None) -> None:
    if page is None:
        return
    try:
        page.close()
    except Exception:
        pass
