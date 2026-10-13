"""게시 단계 테스트 — 가짜 페이지로 계약 6절의 모든 갈래(테스트 모드 · 다시 확인 · 예약 · 클릭 · 확인)."""
from __future__ import annotations

import dataclasses
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from agent.config import LimitsConfig, load_config
from agent.logbook import KST, Event, Logbook, parse_line
from agent.models import CommentDraft, VideoRecord
from agent.poster import (
    CHROME_UNREACHABLE,
    LOGIN_REQUIRED,
    POST_BUTTON_MISSING,
    PageError,
    PostOutcome,
    post_video,
    screenshot_path,
)
from agent.store import Store

ROOT = Path(__file__).resolve().parent.parent
VID = "AAAAAAAAAAA"
OTHER_ALLOWED = "BBBBBBBBBBB"
NOT_ALLOWED = "CCCCCCCCCCC"
NOW = datetime(2026, 10, 13, 12, 0, tzinfo=KST)
TEXT = "연락 텀이 길어질 때 불안한 마음, 저도 겪어 봐서 알아요. 먼저 내 기준을 정해 두면 훨씬 편해져요."
WATCH = "https://www.youtube.com/watch?v={}"
SIGN_IN = (
    "https://accounts.google.com/ServiceLogin?service=youtube"
    "&continue=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DAAAAAAAAAAA"
)


class StepClock:
    """n 번째 부름에 NOW + n 초를 돌려주는 시계."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> datetime:
        self.calls += 1
        return NOW + timedelta(seconds=self.calls)


class FakePage:
    """CommentPage 가짜. 무엇을 열고 불렀는지, 클릭 순간의 저장소 · 로그 상태를 적어 둡니다."""

    def __init__(self, store: Store, log_path: Path, video_id: str = VID) -> None:
        self._store = store
        self._log_path = log_path
        self._video_id = video_id
        self._url = "about:blank"
        self.opened: list[str] = []
        self.calls: list[str] = []
        self.closed = False
        self.attempt_at_submit: str | None = None
        self.log_lines_at_submit: int | None = None
        self.url_after_open: str | None = None
        self.url_after_prepare: str | None = None
        self.prepare_error: BaseException | None = None
        self.submit_error: BaseException | None = None
        self.confirm = True
        self.confirm_error: BaseException | None = None
        self.screenshot_error: BaseException | None = None
        self.close_error: BaseException | None = None
        self.typed: list[str] = []

    @property
    def url(self) -> str:
        return self._url

    def open(self, url: str) -> None:
        self.calls.append("open")
        self.opened.append(url)
        self._url = self.url_after_open if self.url_after_open is not None else url

    def prepare_comment(self, text: str) -> None:
        self.calls.append("prepare_comment")
        if self.prepare_error is not None:
            raise self.prepare_error
        self.typed.append(text)
        if self.url_after_prepare is not None:
            self._url = self.url_after_prepare

    def submit(self) -> None:
        self.calls.append("submit")
        record = self._store.get(self._video_id)
        self.attempt_at_submit = record.attempts[-1].result if record.attempts else None
        if self._log_path.exists():
            lines = self._log_path.read_text(encoding="utf-8").splitlines()
            self.log_lines_at_submit = len(lines)
        else:
            self.log_lines_at_submit = 0
        if self.submit_error is not None:
            raise self.submit_error

    def confirm_posted(self, text: str) -> bool:
        self.calls.append("confirm_posted")
        if self.confirm_error is not None:
            raise self.confirm_error
        return self.confirm

    def screenshot(self, path: Path) -> None:
        self.calls.append("screenshot")
        if self.screenshot_error is not None:
            raise self.screenshot_error
        Path(path).write_bytes(b"\x89PNG fake")

    def close(self) -> None:
        self.calls.append("close")
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FailingReserveStore(Store):
    """예약 쓰기가 실패하는 저장소 — 예약 없이 클릭하지 않는지 봅니다."""

    def reserve_live(self, video_id: str, now: datetime) -> None:
        raise OSError("disk full")


def make_record(video_id: str = VID, *, comment: bool = True) -> VideoRecord:
    draft = CommentDraft("연락 텀 불안", TEXT, NOW - timedelta(minutes=5)) if comment else None
    return VideoRecord(
        video_id=video_id,
        channel_id="UCchannel",
        title="연락 텀 때문에 불안한 썸",
        description="",
        published_at=NOW - timedelta(hours=5),
        detected_at=NOW - timedelta(hours=1),
        keyword="썸",
        comment=draft,
    )


class PosterCase(unittest.TestCase):
    store_class: type[Store] = Store

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.config = dataclasses.replace(
            load_config(ROOT / "config.yaml"),
            allowed_videos=(f"https://youtu.be/{VID}?si=x", OTHER_ALLOWED),
            limits=LimitsConfig(10, 24.0, 100),
        )
        self.store = self.store_class(self.root / "data" / "videos.json")
        self.log_path = self.root / "logs" / "agent.log"
        self.logbook = Logbook(self.log_path, clock=lambda: NOW)
        self.opens = 0
        self.page = FakePage(self.store, self.log_path)

    def open_page(self) -> FakePage:
        self.opens += 1
        return self.page

    def put(self, video_id: str = VID, *, comment: bool = True) -> VideoRecord:
        record = make_record(video_id, comment=comment)
        self.store.put(record)
        return record

    def post(self, record: VideoRecord, *, dry_run: object = False, clock=None, open_page=None):
        return post_video(
            record,
            config=self.config,
            dry_run=dry_run,
            store=self.store,
            logbook=self.logbook,
            open_page=open_page if open_page is not None else self.open_page,
            clock=clock if clock is not None else (lambda: NOW),
            repo_root=self.root,
        )

    def log(self) -> list[tuple[Event, dict[str, str]]]:
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        return [parse_line(line)[1:] for line in lines]

    def attempts(self, video_id: str = VID) -> list[tuple[str, str, str, str | None]]:
        record = self.store.get(video_id)
        return [(a.mode, a.result, a.reason, a.screenshot) for a in record.attempts]

    def reloaded_attempts(self, video_id: str = VID) -> list[tuple[str, str, str, str | None]]:
        record = Store(self.root / "data" / "videos.json").get(video_id)
        return [(a.mode, a.result, a.reason, a.screenshot) for a in record.attempts]


class PosterTestModeTest(PosterCase):
    def test_not_allowlisted_saves_without_opening_chrome(self) -> None:
        record = self.put(NOT_ALLOWED)
        outcome = self.post(record, dry_run=False)
        self.assertEqual(self.opens, 0)
        self.assertEqual(outcome, PostOutcome(NOT_ALLOWED, "test", "saved", "not_in_allowlist"))
        self.assertEqual(
            self.reloaded_attempts(NOT_ALLOWED), [("test", "saved", "not_in_allowlist", None)]
        )
        self.assertEqual(
            self.log(),
            [
                (
                    Event.POST,
                    {
                        "video": NOT_ALLOWED,
                        "mode": "test",
                        "result": "saved",
                        "reason": "not_in_allowlist",
                    },
                )
            ],
        )

    def test_allowlisted_dry_run_saves_without_opening_chrome(self) -> None:
        record = self.put()
        outcome = self.post(record, dry_run=True)
        self.assertEqual(self.opens, 0)
        self.assertEqual(outcome, PostOutcome(VID, "test", "saved", "dry_run"))
        self.assertEqual(self.attempts(), [("test", "saved", "dry_run", None)])

    def test_dry_run_none_is_still_test_mode(self) -> None:
        record = self.put()
        outcome = self.post(record, dry_run=None)
        self.assertEqual(self.opens, 0)
        self.assertEqual(outcome.mode, "test")
        self.assertEqual(outcome.result, "saved")
        self.assertEqual(self.attempts(), [("test", "saved", "dry_run", None)])


class PosterSkipTest(PosterCase):
    def test_no_comment_skips(self) -> None:
        record = self.put(comment=False)
        outcome = self.post(record)
        self.assertEqual(self.opens, 0)
        self.assertEqual(outcome, PostOutcome(VID, "test", "skipped", "no_comment"))
        self.assertEqual(self.attempts(), [])
        self.assertEqual(self.log(), [(Event.SKIP, {"video": VID, "reason": "no_comment"})])

    def test_check_post_blocks_duplicate(self) -> None:
        record = self.put()
        earlier = NOW - timedelta(hours=30)
        self.store.reserve_live(VID, earlier)
        self.store.resolve_live(VID, "posted", earlier, "allowlisted")
        outcome = self.post(record)
        self.assertEqual(self.opens, 0)
        self.assertEqual(outcome, PostOutcome(VID, "live", "skipped", "duplicate_video"))
        self.assertEqual(self.attempts(), [("live", "posted", "allowlisted", None)])
        self.assertEqual(self.log(), [(Event.SKIP, {"video": VID, "reason": "duplicate_video"})])


class PosterLiveTest(PosterCase):
    # 여는 주소와 정상 게시

    def test_opens_watch_url_built_from_video_id(self) -> None:
        self.post(self.put())
        self.assertEqual(self.page.opened, ["https://www.youtube.com/watch?v=AAAAAAAAAAA"])

    def test_happy_path_reserves_before_click_then_posts(self) -> None:
        outcome = self.post(self.put())
        self.assertEqual(self.page.attempt_at_submit, "reserved")
        self.assertEqual(self.page.log_lines_at_submit, 1)
        self.assertEqual(self.page.typed, [TEXT])
        self.assertEqual(self.reloaded_attempts(), [("live", "posted", "allowlisted", None)])
        self.assertEqual(
            self.log(),
            [
                (
                    Event.POST,
                    {"video": VID, "mode": "live", "result": "reserved", "reason": "allowlisted"},
                ),
                (
                    Event.POST,
                    {"video": VID, "mode": "live", "result": "posted", "reason": "allowlisted"},
                ),
            ],
        )
        self.assertEqual(outcome, PostOutcome(VID, "live", "posted", "allowlisted"))
        self.assertTrue(self.page.closed)

    # 클릭 직전 다시 확인 (계약 6절 3.2)

    def assert_recheck_fallback(self, outcome: PostOutcome, reason: str, page_url: str) -> None:
        self.assertNotIn("submit", self.page.calls)
        shot = screenshot_path(VID, NOW)
        self.assertEqual(outcome, PostOutcome(VID, "test", "saved", reason, shot))
        self.assertEqual(self.reloaded_attempts(), [("test", "saved", reason, None)])
        self.assertEqual(
            self.log(),
            [
                (
                    Event.POST,
                    {
                        "video": VID,
                        "mode": "test",
                        "result": "saved",
                        "reason": reason,
                        "screenshot": shot,
                        "page_url": page_url,
                    },
                )
            ],
        )
        self.assertTrue((self.root / shot).is_file())
        self.assertTrue(self.page.closed)

    def test_recheck_other_video_not_allowlisted(self) -> None:
        self.page.url_after_open = WATCH.format(NOT_ALLOWED)
        outcome = self.post(self.put())
        self.assert_recheck_fallback(
            outcome, "not_in_allowlist", "https://www.youtube.com/watch?v=CCCCCCCCCCC"
        )

    def test_recheck_sign_in_interstitial(self) -> None:
        self.page.url_after_open = SIGN_IN
        outcome = self.post(self.put())
        self.assert_recheck_fallback(outcome, "invalid_video", SIGN_IN)

    def test_recheck_other_allowlisted_video_is_page_mismatch(self) -> None:
        self.page.url_after_open = WATCH.format(OTHER_ALLOWED)
        outcome = self.post(self.put())
        self.assert_recheck_fallback(outcome, "page_mismatch", WATCH.format(OTHER_ALLOWED))

    def test_recheck_reads_url_after_prepare(self) -> None:
        self.page.url_after_prepare = WATCH.format(OTHER_ALLOWED)
        outcome = self.post(self.put())
        self.assertEqual(self.page.calls[:2], ["open", "prepare_comment"])
        self.assert_recheck_fallback(outcome, "page_mismatch", WATCH.format(OTHER_ALLOWED))

    # 클릭 전 멈춤 — 저장소 그대로

    def test_prepare_page_error_stops_with_store_unchanged(self) -> None:
        self.page.prepare_error = PageError(LOGIN_REQUIRED)
        outcome = self.post(self.put())
        shot = "logs/screenshots/AAAAAAAAAAA-20261013T030000Z.png"
        self.assertNotIn("submit", self.page.calls)
        self.assertEqual(self.reloaded_attempts(), [])
        self.assertEqual(outcome, PostOutcome(VID, "live", "stopped", "login_required", shot))
        self.assertEqual(
            self.log(),
            [
                (
                    Event.ERROR,
                    {
                        "where": "poster",
                        "reason": "login_required",
                        "stage": "before_click",
                        "video": VID,
                        "screenshot": shot,
                    },
                )
            ],
        )
        self.assertTrue((self.root / shot).is_file())
        self.assertTrue(self.page.closed)

    def test_pre_click_stop_does_not_block_next_try(self) -> None:
        record = self.put()
        self.page.prepare_error = PageError(LOGIN_REQUIRED)
        self.assertEqual(self.post(record).result, "stopped")
        self.page = FakePage(self.store, self.log_path)
        later = NOW + timedelta(minutes=30)
        outcome = self.post(record, clock=lambda: later)
        self.assertEqual(outcome.result, "posted")
        self.assertEqual(self.attempts(), [("live", "posted", "allowlisted", None)])

    def test_open_page_failure_logs_without_screenshot(self) -> None:
        def unreachable() -> FakePage:
            raise PageError(CHROME_UNREACHABLE, "ConnectionRefusedError: 9222")

        outcome = self.post(self.put(), open_page=unreachable)
        self.assertEqual(outcome, PostOutcome(VID, "live", "stopped", "chrome_unreachable"))
        self.assertEqual(self.reloaded_attempts(), [])
        self.assertEqual(
            self.log(),
            [
                (
                    Event.ERROR,
                    {
                        "where": "poster",
                        "reason": "chrome_unreachable",
                        "stage": "before_click",
                        "video": VID,
                        "detail": "ConnectionRefusedError: 9222",
                    },
                )
            ],
        )

    def test_other_prepare_exception_is_page_error_one_line_per_event(self) -> None:
        self.page.prepare_error = RuntimeError("boom\nsecond")
        outcome = self.post(self.put())
        self.assertEqual(outcome.result, "stopped")
        self.assertEqual(outcome.reason, "page_error")
        self.assertEqual(self.reloaded_attempts(), [])
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        _, event, fields = parse_line(lines[0])
        self.assertEqual(event, Event.ERROR)
        self.assertEqual(fields["reason"], "page_error")
        self.assertEqual(fields["stage"], "before_click")
        self.assertEqual(fields["detail"], "RuntimeError: boom\nsecond")

    # 예약 · 클릭 · 확인

    def test_reserve_failure_propagates_without_click(self) -> None:
        self.store = FailingReserveStore(self.root / "data" / "videos.json")
        self.page = FakePage(self.store, self.log_path)
        record = self.put()
        with self.assertRaises(OSError):
            self.post(record)
        self.assertNotIn("submit", self.page.calls)
        self.assertEqual(self.attempts(), [])
        self.assertNotIn(
            "reserved",
            [fields.get("result") for event, fields in self.log() if event is Event.POST],
        )
        self.assertTrue(self.page.closed)

    def test_submit_page_error_resolves_failed(self) -> None:
        self.page.submit_error = PageError(POST_BUTTON_MISSING, "ytd-commentbox #submit-button")
        outcome = self.post(self.put())
        shot = screenshot_path(VID, NOW)
        self.assertEqual(outcome, PostOutcome(VID, "live", "failed", "post_button_missing", shot))
        self.assertEqual(
            self.reloaded_attempts(), [("live", "failed", "post_button_missing", shot)]
        )
        self.assertTrue((self.root / shot).is_file())
        self.assertEqual(
            self.log()[-1],
            (
                Event.POST,
                {
                    "video": VID,
                    "mode": "live",
                    "result": "failed",
                    "reason": "post_button_missing",
                    "screenshot": shot,
                    "detail": "ytd-commentbox #submit-button",
                },
            ),
        )

    def test_submit_other_exception_stays_reserved(self) -> None:
        self.page.submit_error = RuntimeError("Target closed")
        outcome = self.post(self.put())
        shot = screenshot_path(VID, NOW)
        self.assertEqual(outcome, PostOutcome(VID, "live", "reserved", "click_unknown", shot))
        self.assertEqual(self.reloaded_attempts(), [("live", "reserved", "", None)])
        self.assertEqual(
            self.log()[-1],
            (
                Event.ERROR,
                {
                    "where": "poster",
                    "reason": "click_unknown",
                    "stage": "after_click",
                    "video": VID,
                    "screenshot": shot,
                    "detail": "RuntimeError: Target closed",
                },
            ),
        )

    def test_not_confirmed_stays_reserved(self) -> None:
        self.page.confirm = False
        outcome = self.post(self.put())
        shot = screenshot_path(VID, NOW)
        self.assertEqual(outcome, PostOutcome(VID, "live", "reserved", "not_confirmed", shot))
        self.assertEqual(self.reloaded_attempts(), [("live", "reserved", "", None)])
        self.assertEqual(
            self.log()[-1],
            (
                Event.ERROR,
                {
                    "where": "poster",
                    "reason": "not_confirmed",
                    "stage": "after_click",
                    "video": VID,
                    "screenshot": shot,
                },
            ),
        )
        self.assertTrue((self.root / shot).is_file())

    def test_confirm_exception_stays_reserved(self) -> None:
        self.page.confirm_error = RuntimeError("detached")
        outcome = self.post(self.put())
        self.assertEqual(outcome.result, "reserved")
        self.assertEqual(outcome.reason, "confirm_error")
        self.assertEqual(self.reloaded_attempts(), [("live", "reserved", "", None)])
        _, fields = self.log()[-1]
        self.assertEqual(fields["reason"], "confirm_error")
        self.assertEqual(fields["stage"], "after_click")

    def test_keyboard_interrupt_after_reserve_stays_reserved(self) -> None:
        self.page.confirm_error = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.post(self.put())
        self.assertEqual(self.reloaded_attempts(), [("live", "reserved", "", None)])
        self.assertTrue(self.page.closed)

    # 시계가 흐를 때 — 실패 갈래마다 시계를 한 번만 읽음

    def test_failed_branch_screenshot_matches_attempt_time(self) -> None:
        self.page.submit_error = PageError(POST_BUTTON_MISSING)
        self.post(self.put(), clock=StepClock())
        attempt = self.store.get(VID).attempts[-1]
        self.assertEqual(attempt.result, "failed")
        self.assertEqual(attempt.screenshot, screenshot_path(VID, attempt.at))

    def test_page_mismatch_screenshot_matches_attempt_time(self) -> None:
        self.page.url_after_open = WATCH.format(OTHER_ALLOWED)
        self.post(self.put(), clock=StepClock())
        attempt = self.store.get(VID).attempts[-1]
        self.assertEqual(attempt.reason, "page_mismatch")
        _, fields = self.log()[-1]
        self.assertEqual(fields["screenshot"], screenshot_path(VID, attempt.at))

    # 캡처 · 닫기 실패

    def test_screenshot_failure_still_writes_store_and_log(self) -> None:
        self.page.submit_error = PageError(POST_BUTTON_MISSING)
        self.page.screenshot_error = OSError("capture failed")
        outcome = self.post(self.put())
        self.assertEqual(outcome, PostOutcome(VID, "live", "failed", "post_button_missing"))
        self.assertEqual(
            self.reloaded_attempts(), [("live", "failed", "post_button_missing", None)]
        )
        event, fields = self.log()[-1]
        self.assertEqual(event, Event.POST)
        self.assertEqual(fields["result"], "failed")
        self.assertNotIn("screenshot", fields)

    def test_close_failure_does_not_propagate(self) -> None:
        self.page.close_error = RuntimeError("already closed")
        outcome = self.post(self.put())
        self.assertEqual(outcome.result, "posted")
        self.assertTrue(self.page.closed)


if __name__ == "__main__":
    unittest.main()
