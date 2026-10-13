"""주제 판별 — 영상의 제목 · 설명 · 자막을 jev 에 보내 주제 일치 여부와 이유를 판정합니다.

한 요청에 주제 일치 확률(noul) 질문 하나와 이유 보기(choice) 질문 하나를 묶어 보내고, 일치(yes)와
불일치(no)는 두 답이 함께 확신 있게 맞을 때만 냅니다. SDK 가 알린 실패와 모양을 알 수 없는 응답은
보류(hold)가 되며, 오류 보류는 이 두 가지뿐이고 기준값 아래나 두 답이 엇갈린 보류는 판단 보류입니다.
영상 글은 state 에만 들어가고 질문 문구에는 들어가지 않습니다. 이 모듈은 저장도 로그도 하지 않으며,
판정을 저장하고 CLASSIFY · ERROR 줄을 남기는 일은 부르는 쪽이 합니다(계약 '주제 판별' 절).
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import NamedTuple

from agent.config import ClassifierConfig, Config
from agent.models import Judgement, Verdict, VideoRecord

MATCH_ID = "matches_topic"   # noul — 주제 일치 확률
REASON_ID = "reason"         # choice — 이유 보기
LANGUAGES = ("ko", "en")
QUESTION_LANGUAGE = "ko"     # 질문 문구 언어 — 정확도 실행기 결과로만 바꿉니다(계약 '주제 판별' 절)
ERROR_PREFIXES = ("API 오류: ", "응답 모양 오류: ")
# state 와 가장 긴 질문의 합 상한. jev 한도는 32k 토큰이고 토큰 수는 UTF-8 바이트 수를 넘지 않으므로
# 바이트로 묶습니다.
_MAX_INPUT_BYTES = 32_000

Ask = Callable[[str, str, Mapping[str, Mapping[str, object]]], object]


class JevError(Exception):
    """jev 가 답하지 못함 — SDK 가 알린 실패(401 · 422 · 429 · 529 · 연결 · 응답 검증)만 이것으로 바뀝니다."""


class _Wording(NamedTuple):
    match: str
    match_true: str
    match_false: str
    reason: str


_WORDING = {
    "ko": _Wording(
        match="이 영상은 '{topic}' 자체를 중심 주제로 다룬다",
        match_true="영상이 '{topic}' 에 관한 고민 · 경험 · 조언을 중심으로 이야기한다",
        match_false="'{topic}' 라는 낱말이 나오더라도 영상의 중심은 게임 · 음악 · 예능 같은 다른 내용이다",
        reason="이 영상의 중심 내용에 가장 가까운 것",
    ),
    "en": _Wording(
        match="This video's main subject is {topic} itself",
        match_true="The video mainly talks about {topic} worries, experiences or advice",
        match_false=(
            "The word {topic} may appear, but the video is mainly about something else, "
            "such as a game, music or a TV show"
        ),
        reason="Which option is closest to the main content of this video",
    ),
}


def build_questions(
    config: Config, language: str = QUESTION_LANGUAGE
) -> dict[str, dict[str, object]]:
    """jev 에 보낼 질문 두 개 — 문구는 언어별로 고정이고 영상 글은 넣지 않습니다.

    모르는 언어는 KeyError — 코드 잘못이므로 그대로 올라갑니다.
    """
    wording = _WORDING[language]
    topic = config.topic
    # choice 는 첫 보기 쪽으로 기우는 경향이 있어 불일치 보기를 먼저 보입니다 — 기울어도 댓글이 남지 않는 쪽
    options = config.classifier.off_topic_reasons + config.classifier.on_topic_reasons
    return {
        MATCH_ID: {
            "type": "noul",
            "instructions": wording.match.format(topic=topic),
            "criteria": {
                "true": wording.match_true.format(topic=topic),
                "false": wording.match_false.format(topic=topic),
            },
        },
        REASON_ID: {
            "type": "choice",
            "instructions": wording.reason,
            "criteria": {name: None for name in options},
        },
    }


def state_budget(questions: Mapping[str, Mapping[str, object]]) -> int:
    """state 에 쓸 수 있는 바이트 수 — 상한에서 가장 긴 질문(JSON, UTF-8 바이트)을 뺀 값."""
    longest = max(
        len(json.dumps(question, ensure_ascii=False).encode("utf-8"))
        for question in questions.values()
    )
    return _MAX_INPUT_BYTES - longest


def build_state(title: str, description: str, transcript: str | None, budget: int) -> str:
    """제목 → 설명 → 자막 순의 글을 budget 바이트 안으로 끝에서부터 자릅니다. 글자는 쪼개지 않습니다."""
    text = f"Title: {title}\n\nDescription: {description}"
    if transcript:
        text += f"\n\nTranscript: {transcript}"
    data = text.encode("utf-8", "replace")  # 짝 없는 서로게이트는 "?" — 예외 없음
    return data[: max(budget, 0)].decode("utf-8", "ignore")  # 끝의 잘린 글자만 버림


def _probability(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: 숫자가 아닙니다: {value!r}")
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{name}: 0~1 밖입니다: {number!r}")
    return number


def read_answers(response: object, config: ClassifierConfig) -> tuple[float, str, float, float]:
    """응답에서 (noul, 고른 보기, 그 보기의 확률, 확신) 을 읽습니다. 모양이 다르면 예외를 냅니다."""
    answers = getattr(response, "answers")
    noul = _probability(answers[MATCH_ID].noul, "noul")
    reason = answers[REASON_ID]
    choice = reason.choice
    if not isinstance(choice, str) or choice not in (
        config.on_topic_reasons + config.off_topic_reasons
    ):
        raise ValueError(f"보기에 없는 답입니다: {choice!r}")
    probability = _probability(reason.probabilities[choice], "probabilities")
    confidence = _probability(reason.confidence, "confidence")
    return noul, choice, probability, confidence


def _decide(
    noul: float, choice: str, probability: float, confidence: float, config: ClassifierConfig
) -> tuple[Verdict, str]:
    body = f"{choice} ({probability:.2f}) · 일치 {noul:.2f} · 확신 {confidence:.2f}"
    if confidence < config.choice_min_confidence:
        return Verdict.HOLD, f"확신 낮음: {body}"
    if config.noul_no_max < noul < config.noul_yes_min:
        return Verdict.HOLD, f"확신 낮음: {body}"
    on_topic = choice in config.on_topic_reasons
    if noul >= config.noul_yes_min and on_topic:
        return Verdict.YES, body
    if noul <= config.noul_no_max and not on_topic:
        return Verdict.NO, body
    return Verdict.HOLD, f"판단 엇갈림: {body}"


def classify(
    record: VideoRecord,
    config: Config,
    ask: Ask,
    now: datetime,
    *,
    transcript: str | None = None,
    language: str = QUESTION_LANGUAGE,
) -> Judgement:
    """영상 한 개를 판정합니다. 저장 · 로그는 하지 않습니다(계약 '주제 판별' 절)."""
    questions = build_questions(config, language)
    state = build_state(record.title, record.description, transcript, state_budget(questions))
    try:
        response = ask(config.classifier.model, state, questions)
    except JevError as exc:  # SDK 가 알린 실패만 보류 — 그 밖의 예외(SDK 없음 · 코드 잘못)는 그대로 올라가 크게 실패합니다
        return Judgement(Verdict.HOLD, f"API 오류: {exc}", now)
    try:
        noul, choice, probability, confidence = read_answers(response, config.classifier)
    except Exception as exc:
        return Judgement(Verdict.HOLD, f"응답 모양 오류: {type(exc).__name__}: {exc}", now)
    verdict, reason = _decide(noul, choice, probability, confidence, config.classifier)
    return Judgement(verdict, reason, now)


def is_error_hold(judgement: Judgement) -> bool:
    """판정이 아니라 jev 가 답하지 못한 보류인지 — 부르는 쪽이 ERROR 로도 남깁니다."""
    return judgement.verdict is Verdict.HOLD and judgement.reason.startswith(ERROR_PREFIXES)


def sdk_ask(model: str, state: str, questions: Mapping[str, Mapping[str, object]]) -> object:
    """typesafe-sdk 로 jev 에 한 번 묻습니다. SDK 가 알린 실패(TypeSafeError)만 JevError 로 바꿉니다."""
    import typesafe_sdk  # 함수 안에서 — SDK 가 없으면 ModuleNotFoundError 가 그대로 올라갑니다

    sdk_questions: dict[str, object] = {}
    for question_id, spec in questions.items():
        criteria = spec["criteria"]
        if spec["type"] == "noul":
            sdk_questions[question_id] = typesafe_sdk.Noul(
                instructions=spec["instructions"],
                criteria=typesafe_sdk.NoulCriteria(true=criteria["true"], false=criteria["false"]),
            )
        elif spec["type"] == "choice":
            sdk_questions[question_id] = typesafe_sdk.Choice(
                instructions=spec["instructions"], criteria=dict(criteria)
            )
        else:
            raise ValueError(f"모르는 질문 종류입니다: {spec['type']!r}")
    try:
        # 키는 환경 변수 TYPESAFE_API_KEY, 다시 시도는 SDK 기본 정책
        with typesafe_sdk.TypeSafeClient() as client:
            return client.system_one(model=model, state=state, questions=sdk_questions)
    except typesafe_sdk.TypeSafeError as exc:
        status = getattr(exc, "status", None)
        name = type(exc).__name__
        raise JevError(f"{name} {status}" if status is not None else name) from exc
