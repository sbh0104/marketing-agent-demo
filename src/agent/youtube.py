"""YouTube Data API v3 클라이언트와 쿼터 가드 — 쿼터 단위를 아는 유일한 곳 (계약 '탐지 · 조회수 추적' 절).

- 호출마다 드는 단위는 `UNIT_COST` 한 곳에 있고, 모든 HTTP 호출은 `YouTubeClient._call` 에서
  `QuotaLedger.reserve` 를 거칩니다. 페이지 넘김도 search.list 한 번이라 가드를 비켜 가지 못합니다.
- 하루는 굴러가는 24시간이고 경계는 `>` 입니다 — 정확히 24시간 전의 호출은 더 이상 세지 않습니다.
- 허락된 호출은 요청을 보내기 *전에* 파일(`data/quota.json`)에 적습니다. 실패한 요청도 Google 이
  쿼터를 떼므로 그대로 셉니다.
- 막힌 호출은 보내지 않고 `QuotaExhausted` 를 냅니다. 부른 쪽이 `QUOTA` 줄을 남깁니다.
- 기록 파일을 믿을 수 없으면 `QuotaError` 를 내고 파일은 그대로 둡니다 — 지우면 오늘 쓴 쿼터를
  잊고 한도를 넘겨 부르게 되기 때문입니다.
- 전송은 표준 라이브러리 `urllib` 뿐입니다. API 키는 `[A-Za-z0-9_-]+` 만 받고, 오류 글에서는
  키를 `<YOUTUBE_API_KEY>` 로 가립니다.
- 인기 댓글(commentThreads.list)은 댓글 글만 돌려주고 작성자 이름 · 채널 ID 는 읽지 않습니다.
  댓글이 막힌 영상(403 commentsDisabled)은 None 입니다 — 계약 '탐지 · 조회수 추적' 절.
- Google 쿼터를 늘린 프로젝트는 `DAILY_QUOTA_UNITS` 하나만 바꿉니다.
"""
from __future__ import annotations

import http.client
import json
import os
import re
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.config import LimitsConfig

API_ROOT = "https://www.googleapis.com/youtube/v3/"
UNIT_COST: dict[str, int] = {"search.list": 100, "videos.list": 1, "commentThreads.list": 1}
DAILY_QUOTA_UNITS = 10_000
REGION_CODE = "KR"
RELEVANCE_LANGUAGE = "ko"
PAGE_SIZE = 50
MAX_IDS_PER_CALL = 50
MAX_COMMENTS_PER_CALL = 100
COMMENTS_DISABLED = "HTTP 403 commentsDisabled"
LEDGER_SCHEMA_VERSION = 1
_WINDOW = timedelta(hours=24)
# 장부는 48시간치를 보관하고 셈은 24시간 — 하루 안쪽으로 앞선 시계가 실제 호출 기록을 지우지 않게 (계약 '탐지 · 조회수 추적' 절)
_KEEP = 2 * _WINDOW
# https 확인용 SSL 문맥 하나 — opener 마다 새로 만들면 요청마다 CA 묶음을 다시 읽습니다
_TLS_CONTEXT = ssl.create_default_context()
# 요청 하나의 전체 상한(초) — http_get 이 연결부터 마지막 바이트까지 잽니다 (계약 '탐지 · 조회수 추적' 절)
_TIMEOUT_S = 30.0
_KEY_RE = re.compile(r"[A-Za-z0-9_-]+")
_KEY_MASK = "<YOUTUBE_API_KEY>"
_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")
_REPLACEMENT = chr(0xFFFD)
_TEXT_PATH = ("snippet", "topLevelComment", "snippet", "textDisplay")

# (주소, 요청 전체 상한 초) → (상태, 본문)
Fetch = Callable[[str, float], tuple[int, bytes]]


class QuotaError(Exception):
    """쿼터 기록 파일을 믿을 수 없을 때 — 파일은 그대로 두고 멈춥니다."""


class QuotaExhausted(Exception):
    """하루 한도에 닿아 호출을 보내지 않았을 때. counter 는 searches 또는 units."""

    def __init__(self, call: str, counter: str, used: int, limit: int) -> None:
        self.call = call
        self.counter = counter
        self.used = used
        self.limit = limit
        super().__init__(f"{call}: {counter} {used}/{limit} — 하루 한도에 닿아 호출하지 않았습니다")


class YouTubeError(Exception):
    """API 호출이 실패했을 때 — reason 에 키는 들지 않습니다."""

    def __init__(self, call: str, reason: str) -> None:
        self.call = call
        self.reason = reason
        super().__init__(f"{call}: {reason}")


@dataclass(frozen=True)
class Usage:
    searches: int
    units: int


@dataclass(frozen=True)
class _Entry:
    at: datetime
    call: str
    units: int


class QuotaLedger:
    """최근 24시간의 호출 기록 — data/quota.json 한 파일. 파일이 없으면 첫 호출 때 만듭니다."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._calls: list[_Entry] = []
        if self.path.exists():
            self._load()

    def usage(self, now: datetime) -> Usage:
        """now 기준 최근 24시간의 search.list 호출 수와 단위 합."""
        if now.utcoffset() is None:
            raise ValueError("now 에 시간대가 없습니다")
        recent = self._recent(now - _WINDOW)
        return Usage(
            sum(1 for e in recent if e.call == "search.list"), sum(e.units for e in recent)
        )

    def reserve(self, call: str, now: datetime, limits: LimitsConfig) -> None:
        """호출 하나를 허락하면 파일에 먼저 적고, 한도에 닿았으면 QuotaExhausted."""
        if call not in UNIT_COST:
            raise ValueError(f"모르는 호출입니다: {call!r}")
        cost = UNIT_COST[call]
        used = self.usage(now)
        if call == "search.list" and used.searches >= limits.daily_max_searches:
            raise QuotaExhausted(call, "searches", used.searches, limits.daily_max_searches)
        if used.units + cost > DAILY_QUOTA_UNITS:
            raise QuotaExhausted(call, "units", used.units, DAILY_QUOTA_UNITS)
        calls = [*self._recent(now - _KEEP), _Entry(now, call, cost)]
        self._save(calls)
        self._calls = calls

    def _recent(self, start: datetime) -> list[_Entry]:
        return [entry for entry in self._calls if entry.at > start]

    def _save(self, calls: list[_Entry]) -> None:
        """임시 파일에 쓴 뒤 바꿔 끼웁니다 (저장소와 같은 방식)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records = [
            {
                "at": entry.at.astimezone(timezone.utc).isoformat(),
                "call": entry.call,
                "units": entry.units,
            }
            for entry in calls
        ]
        text = json.dumps(
            {"calls": records, "schema_version": LEDGER_SCHEMA_VERSION},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, self.path)

    def _untrusted(self, cause: str) -> QuotaError:
        return QuotaError(
            f"쿼터 기록 파일을 믿을 수 없습니다 ({cause}): {self.path} — 고치거나, 오늘 쓴 쿼터를"
            " 확인한 뒤 지우세요"
        )

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise self._untrusted(f"UTF-8 JSON 이 아닙니다: {exc}") from exc
        if not isinstance(data, dict):
            raise self._untrusted("최상위가 객체가 아닙니다")
        if data.get("schema_version") != LEDGER_SCHEMA_VERSION:
            raise self._untrusted(
                f"버전이 다릅니다 (기대 {LEDGER_SCHEMA_VERSION}, 실제 {data.get('schema_version')!r})"
            )
        raw_calls = data.get("calls")
        if not isinstance(raw_calls, list):
            raise self._untrusted("calls 가 목록이 아닙니다")
        calls: list[_Entry] = []
        for n, raw in enumerate(raw_calls):
            if not isinstance(raw, dict) or set(raw) != {"at", "call", "units"}:
                raise self._untrusted(f"calls[{n}] 은 at · call · units 만 담은 객체여야 합니다")
            at, call, units = raw["at"], raw["call"], raw["units"]
            if not isinstance(at, str):
                raise self._untrusted(f"calls[{n}].at 이 글자가 아닙니다")
            try:
                parsed = datetime.fromisoformat(at)
            except ValueError as exc:
                raise self._untrusted(f"calls[{n}].at 이 ISO 시각이 아닙니다") from exc
            if parsed.utcoffset() is None:
                raise self._untrusted(f"calls[{n}].at 에 시간대가 없습니다")
            if call not in UNIT_COST:
                raise self._untrusted(f"calls[{n}].call 을 모릅니다: {call!r}")
            if isinstance(units, bool) or not isinstance(units, int) or units < 0:
                raise self._untrusted(f"calls[{n}].units 가 0 이상의 정수가 아닙니다")
            calls.append(_Entry(parsed, call, units))
        self._calls = calls


def http_get(url: str, timeout: float) -> tuple[int, bytes]:
    """GET 한 번 → (상태, 본문). 오류 상태 · 3xx 도 본문과 함께 돌려주고, 리다이렉트는 따라가지 않습니다.

    timeout 은 요청 전체의 상한입니다 — urllib 의 timeout 은 읽기 한 번마다라 조금씩 흘려 보내는 응답을
    막지 못하므로, 요청은 일꾼 스레드에서 돌고 상한에 닿으면 TimeoutError 입니다 (계약 '탐지 · 조회수 추적' 절).
    """
    outcome: list[tuple[int, bytes] | BaseException] = []
    done = threading.Event()

    def work() -> None:
        try:
            outcome.append(_get(url, timeout))
        except BaseException as exc:  # 일꾼의 예외는 무엇이든 부르는 쪽에서 다시 냅니다
            outcome.append(exc)
        finally:
            done.set()

    threading.Thread(target=work, name="http_get", daemon=True).start()
    if not done.wait(timeout):
        raise _overrun(timeout)
    result = outcome[0]
    if isinstance(result, BaseException):
        raise result
    return result


def _get(url: str, timeout: float) -> tuple[int, bytes]:
    """http_get 의 일꾼 — 리다이렉트 처리기 없는 opener 로 GET 한 번. 읽기마다의 timeout 은 urllib 그대로."""
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        response = _opener().open(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        # 오류 상태 — 본문을 읽다 실패해도 상태 코드는 남기고, 응답은 늘 닫습니다
        try:
            return exc.code, exc.read()
        except Exception:
            return exc.code, b""
        finally:
            exc.close()
    with response:
        return response.status, response.read()


def _overrun(timeout: float) -> TimeoutError:
    return TimeoutError(f"요청 전체가 {timeout:g}초 상한을 넘었습니다")


def _opener() -> urllib.request.OpenerDirector:
    """urlopen 의 http · https 처리기에서 리다이렉트 처리기만 뺀 opener — 3xx 는 HTTPError 로 옵니다.

    덮어쓰지 않고 빼는 까닭: http_error_302 만 고치면 301 · 303 · 307 · 308 은 따라가고, redirect_request 가
    None 을 돌려도 Location 은 그 전에 urlparse 를 거칩니다 (계약 '탐지 · 조회수 추적' 절).
    """
    opener = urllib.request.OpenerDirector()
    for handler in (
        urllib.request.ProxyHandler(),
        urllib.request.UnknownHandler(),
        urllib.request.HTTPHandler(),
        urllib.request.HTTPSHandler(context=_TLS_CONTEXT),
        urllib.request.HTTPDefaultErrorHandler(),
        urllib.request.HTTPErrorProcessor(),
    ):
        opener.add_handler(handler)
    return opener


class YouTubeClient:
    """search.list · videos.list · commentThreads.list 를 부르는 클라이언트. 모든 호출이 쿼터 가드를 거칩니다."""

    def __init__(self, api_key: str, ledger: QuotaLedger, fetch: Fetch = http_get) -> None:
        if not (isinstance(api_key, str) and _KEY_RE.fullmatch(api_key)):
            raise ValueError("API 키 형식이 아닙니다 — 영문자 · 숫자 · _ · - 만 씁니다")
        self._api_key = api_key
        self._ledger = ledger
        self._fetch = fetch

    def search(
        self,
        query: str,
        published_after: datetime,
        page_token: str | None,
        now: datetime,
        limits: LimitsConfig,
        published_before: datetime | None = None,
    ) -> dict[str, object]:
        """검색 한 페이지 — 최신순, 한국 · 한국어, published_after 이후 올라온 영상."""
        if published_after.utcoffset() is None:
            raise ValueError("published_after 에 시간대가 없습니다")
        if published_before is not None:
            if published_before.utcoffset() is None:
                raise ValueError("published_before 에 시간대가 없습니다")
            if published_before <= published_after:
                raise ValueError("published_before 는 published_after 보다 늦어야 합니다")
        params = {
            "part": "snippet",
            "type": "video",
            "order": "date",
            "q": query,
            "regionCode": REGION_CODE,
            "relevanceLanguage": RELEVANCE_LANGUAGE,
            "maxResults": str(PAGE_SIZE),
            "publishedAfter": published_after.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
        if published_before is not None:
            params["publishedBefore"] = published_before.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        if page_token is not None:
            params["pageToken"] = page_token
        return self._call("search.list", params, now, limits)

    def videos(
        self, video_ids: Sequence[str], now: datetime, limits: LimitsConfig
    ) -> dict[str, object]:
        """영상 정보와 조회수 — 한 번에 1–50개."""
        if not 1 <= len(video_ids) <= MAX_IDS_PER_CALL:
            raise ValueError(
                f"영상 ID 는 한 번에 1–{MAX_IDS_PER_CALL}개입니다: {len(video_ids)}개"
            )
        params = {"part": "snippet,statistics", "id": ",".join(video_ids)}
        return self._call("videos.list", params, now, limits)

    def top_comments(
        self, video_id: str, now: datetime, limits: LimitsConfig, max_results: int
    ) -> tuple[str, ...] | None:
        """인기 댓글 글 — 관련도순 앞 max_results 개. 댓글이 막힌 영상(403 commentsDisabled)은 None.

        작성자 이름 · 채널 ID 는 읽지 않습니다. 그 밖의 오류는 YouTubeError 그대로 올라갑니다.
        """
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not (
            1 <= max_results <= MAX_COMMENTS_PER_CALL
        ):
            raise ValueError(f"인기 댓글은 한 번에 1–{MAX_COMMENTS_PER_CALL}개입니다: {max_results!r}")
        params = {
            "part": "snippet",
            "videoId": video_id,
            "order": "relevance",
            "maxResults": str(max_results),
            "textFormat": "plainText",
        }
        try:
            data = self._call("commentThreads.list", params, now, limits)
        except YouTubeError as exc:
            if exc.reason == COMMENTS_DISABLED:
                return None
            raise
        return _comment_texts(data, max_results)

    def _call(
        self, call: str, params: dict[str, str], now: datetime, limits: LimitsConfig
    ) -> dict[str, object]:
        url = API_ROOT + call.partition(".")[0] + "?" + urllib.parse.urlencode({**params, "key": self._api_key})
        self._ledger.reserve(call, now, limits)
        try:
            status, body = self._fetch(url, _TIMEOUT_S)
        # _fetch 의 예외는 무엇이든 — 깨진 리다이렉트 · 덩어리 틀 · 시간 상한도 ERROR 한 줄입니다. Ctrl+C 는 BaseException 이라 빠집니다 (계약 '탐지 · 조회수 추적' 절)
        except Exception as exc:
            raise YouTubeError(call, self._redact(f"network {type(exc).__name__}: {exc}")) from None
        try:
            data = json.loads(body)
        except (ValueError, RecursionError):
            data = None
        if status != 200:
            raise YouTubeError(call, self._redact(f"HTTP {status} {_google_reason(data)}".rstrip()))
        if not isinstance(data, dict):
            raise YouTubeError(call, f"HTTP {status} invalid JSON")
        return data

    def _redact(self, text: str) -> str:
        return text.replace(self._api_key, _KEY_MASK)


def _google_reason(data: object) -> str:
    """Google 오류 본문의 error.errors[0].reason — 모양이 다르면 빈 글자."""
    if not isinstance(data, dict):
        return ""
    error = data.get("error")
    if not isinstance(error, dict):
        return ""
    errors = error.get("errors")
    if not isinstance(errors, list) or not errors or not isinstance(errors[0], dict):
        return ""
    reason = errors[0].get("reason")
    return reason if isinstance(reason, str) else ""


def _comment_texts(data: dict[str, object], max_results: int) -> tuple[str, ...]:
    """commentThreads.list 답에서 최상위 댓글 글만 — 모양이 다른 항목은 건너뜁니다."""
    items = data.get("items", [])
    if not isinstance(items, list):
        raise YouTubeError("commentThreads.list", "HTTP 200 items 가 목록이 아닙니다")
    texts: list[str] = []
    for item in items:
        node: object = item
        for key in _TEXT_PATH:
            if not isinstance(node, dict):
                break
            node = node.get(key)
        else:
            if isinstance(node, str):
                texts.append(_SURROGATE_RE.sub(_REPLACEMENT, node))
    return tuple(texts[:max_results])
