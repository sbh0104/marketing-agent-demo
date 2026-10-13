"""댓글 작성 — Claude 가 쓰고, jev 가 자체 검사하고, 코드가 마지막에 검사합니다.

흐름: Claude 가 영상의 고민 한 줄과 '연애사주 경험' 댓글을 JSON 하나로 답합니다 → jev 가 초안
한 개에 `noul` 질문 세 개(영상 속 장면·말 언급 · 광고처럼 읽힘 · 영상 고민과 이어짐)를 한 요청으로
답합니다 → 코드가 글자 수 · 링크 · 최근 내 댓글과의 반복을 셉니다. 떨어지면 모든 이유를 붙여 같은
대화에서 한 번 다시 쓰고, 두 번째도 떨어지면 그 영상을 건너뛰고 이유를 `SKIP` 으로 남깁니다.
Claude · jev 호출 오류는 다시 써도 고쳐지지 않으므로 다시 쓰지 않고 `ERROR` 와 `SKIP` 을 남깁니다.

프롬프트 원문은 이 모듈 맨 위에만 둡니다 — Phase 8 PROCESS.md 가 옮겨 적습니다. 계약 11절.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Protocol

from agent.config import CommentConfig
from agent.logbook import Event, Logbook
from agent.models import CommentDraft, Judgement, Verdict, VideoRecord

# 자체 검사 질문은 영어로 씁니다 — jev 의 주 언어가 영어이기 때문입니다(docs/research/jev.md).
# 질문이 읽는 자료(영상 제목 · 설명 · 자막 · 초안)는 한국어 그대로 둡니다.
CHECK_QUESTIONS: dict[str, str] = {
    "mentions_scene": (
        "Does the text inside <draft_comment> mention at least one specific scene, moment,"
        " or line from the video described in the material?"
    ),
    "reads_like_ad": (
        "Does the text inside <draft_comment> read like an advertisement or a promotion"
        " of a product or service?"
    ),
    "follows_concern": (
        "Does the text inside <draft_comment> respond to the concern written inside"
        " <video_concern>?"
    ),
}
INVERTED_QUESTIONS = frozenset({"reads_like_ad"})  # '예' 가 나쁜 질문 — 통과 확률은 1 − P(예)
CHECK_LABELS = {
    "mentions_scene": "영상 속 장면·말 언급",
    "reads_like_ad": "광고처럼 읽힘",
    "follows_concern": "영상 고민과 이어짐",
}
_TOLERANCE = 1e-9  # 1 − P 의 부동소수 오차(1 − 0.9 = 0.0999…98)가 하한 경계를 넘지 않게 덮습니다
REPEAT_MIN_CHARS = 12   # 공백·문장부호를 뺀 글자가 연속 이만큼 같으면 반복 — 한국어 한 마디 크기
_SEPARATOR_NAMES = ("FULL STOP", "DOT", "SOLIDUS", "SLASH", "COLON")
_LINK_RE = re.compile(r"[^\W_]\.+[a-z]{2,}|@[^\W_]|:/|[0-9]{1,3}(?:\.[0-9]{1,3}){3}")


def _link_char(ch: str) -> str:
    """링크 보기에 남길 글자 — 글자 · 숫자 · `@` 는 그대로, 점 · 빗금 · 쌍점 닮은꼴은 대표 글자로.

    그 밖(공백 · 괄호 · 보이지 않는 글자 · 다른 문장부호)은 모두 버립니다. 버릴 글자를 나열하지
    않고 남길 모양만 정합니다.
    """
    if ch.isalnum() or ch == "@":
        return ch
    name = unicodedata.name(ch, "")
    if any(part in name for part in _SEPARATOR_NAMES):
        if "SOLIDUS" in name or "SLASH" in name:
            return "/"
        if "COLON" in name:
            return ":"
        return "."
    return ""


def _link_view(text: str) -> str:
    """NFKC + casefold 한 뒤 링크 모양만 남긴 글 — 전각 · 띄어 쓴 · 괄호로 감싼 점도 붙습니다."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return "".join(_link_char(ch) for ch in folded)


def link_fragment(text: str) -> str | None:
    """링크 · 주소 모양(호스트+영문 끝, @이름, 스킴, IPv4)이 있으면 그 조각을, 없으면 None."""
    match = _LINK_RE.search(_link_view(text))
    return match.group() if match is not None else None


def _letters(text: str) -> str:
    """NFKC + casefold 한 뒤 글자와 숫자만 남깁니다 — 공백 · 문장부호 · 이모지는 버립니다."""
    return "".join(ch for ch in unicodedata.normalize("NFKC", text).casefold() if ch.isalnum())


def repeated_run(text: str, previous: Sequence[str], min_run: int) -> str | None:
    """이전 댓글과 같거나 `min_run` 글자 이상 연속으로 겹치면 겹친 글자를, 아니면 None."""
    new = _letters(text)
    for comment in previous:
        old = _letters(comment)
        if new == old:
            return new
        match = SequenceMatcher(None, new, old, autojunk=False).find_longest_match(
            0, len(new), 0, len(old)
        )
        if match.size >= min_run:
            return new[match.a : match.a + match.size]
    return None


def code_failures(text: str, recent: Sequence[str], config: CommentConfig) -> list[str]:
    """코드 검사 세 가지(글자 수 · 링크 · 반복)를 모두 돌리고 걸린 이유를 순서대로 돌려줍니다."""
    failures: list[str] = []
    length = len(text)
    if not config.min_chars <= length <= config.max_chars:
        failures.append(f"글자 수 {length}자 — {config.min_chars}–{config.max_chars}자여야 합니다")
    link = link_fragment(text)
    if link is not None:
        failures.append(f"링크·주소 모양이 들어 있습니다: {link}")
    run = repeated_run(text, recent, REPEAT_MIN_CHARS)
    if run is not None:
        failures.append(f"이전 댓글과 겹칩니다: {run}")
    return failures


def self_check_failure(probabilities: Mapping[str, float], threshold: float) -> str | None:
    """jev 답의 질문마다 점수가 하한 이상인지 봅니다. 떨어진 질문이 있으면 그 이유를, 없으면 None.

    점수는 P(예)이고, 광고 질문처럼 '예' 가 나쁜 질문은 1 − P(예)입니다.
    """
    failing: list[str] = []
    for name in CHECK_QUESTIONS:
        probability = probabilities[name]
        score = 1.0 - probability if name in INVERTED_QUESTIONS else probability
        if score + _TOLERANCE < threshold:
            failing.append(f"{CHECK_LABELS[name]} {probability:.2f}")
    if failing:
        return "자체 검사 미달 — " + ", ".join(failing)
    return None


def parse_output(raw: str) -> tuple[str, str] | None:
    """Claude 의 답에서 JSON `{"concern", "comment"}` 을 읽습니다. 읽을 수 없으면 None.

    고민은 한 줄로 모으고, 댓글은 NFC 로 맞춘 뒤 앞뒤 공백을 뗍니다.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except (ValueError, RecursionError):
        return None
    if not isinstance(data, dict):
        return None
    concern = data.get("concern")
    comment = data.get("comment")
    if not isinstance(concern, str) or not isinstance(comment, str):
        return None
    concern = " ".join(unicodedata.normalize("NFC", concern).split())
    comment = unicodedata.normalize("NFC", comment).strip()
    if not concern or not comment:
        return None
    return concern, comment
