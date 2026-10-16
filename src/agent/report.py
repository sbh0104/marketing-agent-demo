"""결과 화면 — 사이클마다 다시 쓰는 정적 HTML 한 장을 저장소 기록과 로그 줄로만 그립니다.

화면은 저장소와 로그(read_log 로 읽은 줄)를 읽기만 하고 판단 · 게시 · 저장소를 바꾸지 않습니다.
로그의 이유 칸과 단계 이름은 정해 둔 이름표로만 옮기고 원문은 한 글자도 옮기지 않습니다 — 정해 둔
코드와 같거나 정해 둔 머리말로 시작하지 않으면 "기타 — 로그 참고" 입니다. 제목 · 판별 이유 · 고민 ·
댓글 같은 바깥 글은 모두 HTML 이스케이프를 거친 글자로만 들어가고, 영상 링크는 코드가 영상 ID 로
새로 만듭니다. 외부 스크립트 · 글꼴 · 스타일 파일은 불러오지 않습니다.
계약 '결과 화면 — report.py (Phase 7D)' 절.
"""
from __future__ import annotations

import html
import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from agent.logbook import KST, Event
from agent.models import VideoRecord
from agent.poster import DRY_RUN, NO_COMMENT, PAGE_MISMATCH, WATCH_URL
from agent.trigger import views_per_hour
from agent.writer import NO_CONCERN, NO_SCENE

LogLine = tuple[datetime, Event, dict[str, str]]

OTHER = "기타 — 로그 참고"
LOG_UNREADABLE = "로그를 읽지 못함"
REHEARSED = "리허설 — 게시 버튼 앞에서 멈춤"
POSTED = "게시됨"
RESERVED = "게시 결과 모름 — 로그 참고"
FAILED = "게시 실패 — 로그 참고"
NO_POST = "게시 기록 없음"
NO_DRAFT = "댓글 안 씀"
NOT_JUDGED = "아직 판별 안 함"
NOT_TIMED = "아직 안 봄"

# 이유 코드 → 이름표 — 이유 글이 이 키와 정확히 같을 때만
REASON_LABELS: dict[str, str] = {
    "channel_cooldown": "같은 채널 대기 중",
    "daily_cap": "하루 상한에 닿음",
    "duplicate_video": "이미 처리한 영상",
    "not_in_allowlist": "허용 목록 밖이라 게시하지 않음",
    "invalid_video": "영상 주소를 읽을 수 없음",
    "invalid_item": "영상 정보를 읽을 수 없음",
    DRY_RUN: "테스트 실행 — 저장만",
    NO_COMMENT: "댓글 없음",
    "config_rejected": "설정 거절로 저장만",
    PAGE_MISMATCH: "열린 화면이 다른 영상이라 저장만",
    "unavailable": "영상을 볼 수 없음",
}
# 이유 머리말 → 이름표 — 이유 글이 이 머리말로 시작할 때, 앞에서부터 처음 맞는 것
REASON_PREFIXES: tuple[tuple[str, str], ...] = (
    (NO_SCENE, "작성 건너뜀 — 짚을 장면 없음"),
    (NO_CONCERN, "작성 건너뜀 — 연애 고민 없음"),
    ("검사 두 번 탈락", "검사 두 번 탈락"),
    ("claude 호출 실패", "AI 호출 오류 (Claude)"),
    ("jev 검사 호출 실패", "AI 호출 오류 (jev 검사)"),
    ("jev 검사 응답 이상", "AI 응답 이상 (jev 검사)"),
)
# ERROR 줄의 where= → 이름표 — video= 를 다는 단계만, 정확히 같을 때만
WHERE_LABELS: dict[str, str] = {
    "classify": "판별 단계 오류",
    "run.classify": "판별 단계 오류",
    "run.trigger": "타이밍 단계 오류",
    "commentThreads.list": "인기 댓글을 받지 못함",
    "writer.claude": "AI 호출 오류 (Claude)",
    "writer.jev": "AI 호출 오류 (jev 검사)",
    "run.write": "작성 단계 오류",
    "poster": "게시 단계 오류",
    "run.post": "게시 단계 오류",
}
# 실제 게시 시도의 (mode, result) → 결과 배지 — test/saved 는 그 시도 reason 의 이름표
OUTCOME_LABELS = {
    ("live", "posted"): POSTED,
    ("live", "reserved"): RESERVED,
    ("live", "failed"): FAILED,
}

_STYLE = (
    "<style>"
    "body{font-family:sans-serif;margin:1.5em}"
    "table{border-collapse:collapse;width:100%}"
    "th,td{border:1px solid #ccc;padding:4px 6px;text-align:left;vertical-align:top}"
    ".badge{display:inline-block;padding:1px 6px;border-radius:4px;background:#e8eefc}"
    ".reason{background:#fdecea}"
    ".warning{color:#a40000;font-weight:bold}"
    "</style>"
)
_HEADER = (
    "<thead><tr><th>영상</th><th>판별</th><th>판단한 쪽</th><th>타이밍</th>"
    "<th>고민 한 줄</th><th>댓글</th><th>게시 결과</th></tr></thead>"
)
_WARNING = (
    '<p class="warning">로그를 읽지 못해 이유 배지 · 리허설 · 판단한 쪽 칸을 채우지 못했습니다'
    " — logs/agent.log 의 ERROR where=report 줄을 보세요.</p>"
)
_EMPTY = '<tr><td colspan="7">아직 영상이 없습니다.</td></tr>'


def reason_label(reason: str) -> str:
    """이유 글의 이름표 — 정해 둔 코드와 같거나 정해 둔 머리말로 시작하면 그 이름표, 아니면 OTHER.

    받은 글은 돌려주지 않습니다 — 머리말 뒤의 세부 · 초안 인용 · 오류 원문은 화면에 가지 않습니다.
    """
    label = REASON_LABELS.get(reason)
    if label is not None:
        return label
    for prefix, label in REASON_PREFIXES:
        if reason.startswith(prefix):
            return label
    return OTHER


def where_label(where: str) -> str:
    """ERROR 줄 where= 의 이름표 — 정해 둔 단계와 정확히 같을 때만, 아니면 OTHER."""
    return WHERE_LABELS.get(where, OTHER)


def _store_floor(record: VideoRecord) -> datetime | None:
    """저장소의 마지막 결과 — 판별 · 타이밍 · 댓글 · 마지막 시도 시각 가운데 가장 늦은 것을 초로 내린 것, 없으면 None.

    로그 시각이 초 단위라 같은 초의 줄은 늦은 쪽으로 셉니다. 타이밍은 새 표본마다 다시 판정해 그 시각이
    그 영상을 마지막으로 다룬 때입니다. 판별 칸이 빈 영상(판별 보류)은 타이밍 시각을 세지 않습니다 — 보류
    때도 같은 주기에 타이밍이 판정되어 그 시각이 판별 오류 줄보다 몇 밀리초 늦기 때문입니다.
    """
    times = []
    if record.classification is not None:
        times.append(record.classification.at)
    # 판별 칸이 빈 영상(판별 보류)은 타이밍 시각을 세지 않습니다 — 같은 주기의 판별 오류 줄을 남깁니다
    if record.classification is not None and record.trigger is not None:
        times.append(record.trigger.at)
    if record.comment is not None:
        times.append(record.comment.at)
    if record.attempts:
        times.append(record.attempts[-1].at)
    if not times:
        return None
    return max(times).replace(microsecond=0)


def _is_reason_source(line: LogLine) -> bool:
    """이유 · 결과의 출처가 되는 줄 — SKIP · ERROR, 그리고 리허설 POST(mode=test result=rehearsed)."""
    _, event, fields = line
    if event is Event.SKIP or event is Event.ERROR:
        return True
    return (
        event is Event.POST
        and fields.get("mode") == "test"
        and fields.get("result") == "rehearsed"
    )


def late_lines(record: VideoRecord, events: Sequence[LogLine]) -> list[LogLine]:
    """그 영상의 이유 출처 줄 가운데 저장소의 마지막 결과와 같은 초이거나 늦은 줄 — 파일 순서대로."""
    floor = _store_floor(record)
    return [
        line
        for line in events
        if line[2].get("video") == record.video_id
        and _is_reason_source(line)
        and (floor is None or line[0] >= floor)
    ]


def badges(
    record: VideoRecord, events: Sequence[LogLine] | None
) -> tuple[str, datetime | None, str | None]:
    """게시 결과 칸 — (결과 배지, 그 결과의 시각, 이유 배지). events 가 None 이면 로그를 못 읽은 것.

    결과는 늦은 줄의 마지막이 리허설이면 리허설, 아니면 저장소의 마지막 시도입니다. 이유는 늦은 줄의
    마지막이 SKIP 이면 그 reason 의 이름표, ERROR 이면 그 where 의 이름표입니다.
    """
    lines = late_lines(record, events) if events is not None else []
    last = lines[-1] if lines else None
    outcome_at: datetime | None = None
    if last is not None and last[1] is Event.POST:
        outcome, outcome_at = REHEARSED, last[0]
    elif record.attempts:
        tried = record.attempts[-1]
        if tried.mode == "test":
            outcome = reason_label(tried.reason)
        else:
            outcome = OUTCOME_LABELS[(tried.mode, tried.result)]
        outcome_at = tried.at
    else:
        outcome = NO_POST if record.comment is not None else NO_DRAFT
    reason: str | None = None
    if events is None:
        reason = LOG_UNREADABLE
    elif last is not None and last[1] is Event.SKIP:
        reason = reason_label(last[2]["reason"])
    elif last is not None and last[1] is Event.ERROR:
        reason = where_label(last[2]["where"])
    return outcome, outcome_at, reason


def judge_of(video_id: str, events: Sequence[LogLine]) -> str:
    """판단한 쪽 — 그 영상의 마지막 CLASSIFY 줄의 judge=, 없으면 그 줄 앞 마지막 START 줄의 judge=."""
    start_judge = ""
    judge = ""
    for _, event, fields in events:
        if event is Event.START:
            start_judge = fields.get("judge", "")
        elif event is Event.CLASSIFY and fields.get("video") == video_id:
            judge = fields.get("judge", start_judge)
    return judge


def _text(value: str) -> str:
    """화면에 넣는 글 — 줄마다 HTML 이스케이프(따옴표 포함)하고 줄 경계는 <br>. 이스케이프는 여기뿐."""
    return "<br>".join(html.escape(part, quote=True) for part in value.splitlines())


def _stamp(at: datetime) -> str:
    return at.astimezone(KST).isoformat(timespec="seconds")


def _row(record: VideoRecord, events: Sequence[LogLine] | None) -> str:
    """영상 한 줄 — 칸 일곱, 한 물리 줄. 글 칸은 모두 _text 를 거칩니다."""
    video_id = record.video_id
    link = _text(WATCH_URL.format(video_id=video_id))
    title = _text(record.title) or _text(video_id)
    classification = record.classification
    if classification is None:
        judged = _text(NOT_JUDGED)
    else:
        judged = _text(f"{classification.verdict.value} · {classification.reason}")
    judge = ""
    if events is not None and classification is not None:
        judge = _text(judge_of(video_id, events))
    trigger = record.trigger
    if trigger is None:
        timing = _text(NOT_TIMED)
    else:
        rule = f"{trigger.verdict.value} · {trigger.reason}"
        per_hour = views_per_hour(record)
        if per_hour is not None:
            rule += f" · 시간당 {per_hour:.2f}회"
        timing = _text(rule)
    comment = record.comment
    concern = _text(comment.concern) if comment is not None else ""
    text = _text(comment.text) if comment is not None else ""
    outcome, outcome_at, reason = badges(record, events)
    result = f'<span class="badge">{_text(outcome)}</span>'
    if outcome_at is not None:
        result += f"<br><small>{_text(_stamp(outcome_at))}</small>"
    if reason is not None:
        result += f'<br><span class="badge reason">{_text(reason)}</span>'
    cells = (
        f'<a href="{link}">{title}</a><br><code>{_text(video_id)}</code>',
        judged,
        judge,
        timing,
        concern,
        text,
        result,
    )
    body = "".join(f"<td>{cell}</td>" for cell in cells)
    return f'<tr id="v-{_text(video_id)}">{body}</tr>'


def render_report(
    records: Sequence[VideoRecord],
    events: Sequence[LogLine] | None,
    *,
    generated_at: datetime,
) -> str:
    """화면 한 장의 글 — 저장소 기록과 로그 줄(None 이면 못 읽은 것)만으로 만듭니다. 같은 입력 → 같은 글.

    기록은 (detected_at, video_id) 가 늦은 차례로 한 줄씩입니다.
    """
    ordered = sorted(records, key=lambda rec: (rec.detected_at, rec.video_id), reverse=True)
    lines = [
        "<!doctype html>",
        '<html lang="ko">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>결과 화면 — 마케팅 에이전트</title>",
        _STYLE,
        "</head>",
        "<body>",
        "<h1>결과 화면</h1>",
        f'<p class="generated">만든 시각 {_text(_stamp(generated_at))}</p>',
        f'<p class="summary">영상 {len(ordered)}개 — data/videos.json 과 logs/agent.log 로 만듦</p>',
    ]
    if events is None:
        lines.append(_WARNING)
    lines += ["<table>", _HEADER, "<tbody>"]
    if ordered:
        lines += [_row(record, events) for record in ordered]
    else:
        lines.append(_EMPTY)
    lines += ["</tbody>", "</table>", "</body>", "</html>"]
    return "\n".join(lines) + "\n"


def write_report(path: Path, text: str) -> None:
    """화면을 원자적으로 씁니다 — 폴더를 만들고 `<이름>.tmp` 에 UTF-8 · LF 로 쓴 뒤 바꿔 끼웁니다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
