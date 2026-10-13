"""jev 정확도 실행기 — 한국어 예시 묶음을 실제 jev 로 판정해 질문 언어별로 셉니다.

    python3 -m tests.jev_accuracy

환경 변수 TYPESAFE_API_KEY 가 있어야 합니다 — 이 러너는 .env 를 읽지 않으므로 사람이 셸에서
export 합니다(.env 를 읽고 결과 파일을 남기는 실행기는 tests/live_check.py). 언어마다 맞음 · 잘못된
일치 · 잘못된 불일치 · 보류 · 오류를 따로 찍고, 잘못된 일치가 없고 22개 중 20개 이상 맞으면
통과입니다. 종료 코드는 0 ko 통과 · 1 ko 미달(권고를 찍음) · 2 재지 않음(키 없음 · 잘못된 인자) ·
3 측정 실패(API 오류 · 응답 모양 오류 — 모델 문제가 아님)입니다. 네트워크를 쓰는 실행기는 이것과
tests/live_check.py 이고, 둘 다 키가 없으면 아무것도 부르지 않습니다. 예시를 판정하는
차례(judge_examples)와 세기(tally)는 두 실행기가 함께 씁니다. 이 파일은 test*.py 가 아니라서
discover 가 줍지 않습니다.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

import tests  # noqa: F401 — src/ 를 sys.path 에 넣는 준비
from agent.classifier import LANGUAGES, Ask, classify, is_error_hold, sdk_ask
from agent.config import Config, load_config
from agent.models import Judgement, Verdict, VideoRecord
from tests.classifier_examples import EXAMPLES, Example

REPO_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"
PASS_CORRECT = 20
USAGE = "사용법: python3 -m tests.jev_accuracy"


class Tally(NamedTuple):
    correct: int
    false_yes: int
    false_no: int
    hold: int
    error: int
    misses: tuple[str, ...]


def example_record(index: int, example: Example, now: datetime) -> VideoRecord:
    return VideoRecord(
        video_id=f"example{index:04d}",
        channel_id="UCexample",
        title=example.title,
        description=example.description,
        published_at=now,
        detected_at=now,
        keyword="연애",
    )


def judge_examples(
    examples: Iterable[Example], config: Config, ask: Ask, now: datetime, language: str
) -> Iterator[tuple[int, Example, Judgement]]:
    """예시마다 한 번 판정해 (번호, 예시, 판정)을 차례로 내놓습니다 — measure 와 실제 호출 실행기가 함께 씁니다."""
    for index, example in enumerate(examples, 1):
        yield index, example, classify(
            example_record(index, example, now), config, ask, now, language=language
        )


def tally(judged: Iterable[tuple[int, Example, Judgement]]) -> Tally:
    """판정을 정확히 한 칸에 셉니다. 맞지 않은 판정은 한 줄씩 남깁니다."""
    correct = false_yes = false_no = hold = error = 0
    misses: list[str] = []
    for _, example, judgement in judged:
        verdict = judgement.verdict
        if is_error_hold(judgement):
            error += 1
        elif verdict is Verdict.HOLD:
            hold += 1
        elif verdict is example.label:
            correct += 1
            continue
        elif verdict is Verdict.YES:
            false_yes += 1
        else:
            false_no += 1
        misses.append(
            f"{example.kind} · {example.label.value} → {verdict.value}: "
            f"{example.title} — {judgement.reason}"
        )
    return Tally(correct, false_yes, false_no, hold, error, tuple(misses))


def measure(
    examples: Iterable[Example], config: Config, ask: Ask, now: datetime, language: str
) -> Tally:
    """예시마다 한 번 판정해 결과를 정확히 한 칸에 셉니다. 맞지 않은 판정은 한 줄씩 남깁니다."""
    return tally(judge_examples(examples, config, ask, now, language))


def passes(t: Tally) -> bool:
    return t.false_yes == 0 and t.correct >= PASS_CORRECT


def main(
    argv: list[str], env: Mapping[str, str] | None = None, ask: Ask | None = None
) -> int:
    if argv:
        print(USAGE, file=sys.stderr)
        return 2
    env = os.environ if env is None else env
    if not env.get("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY 가 없어 정확도를 재지 않습니다", file=sys.stderr)
        return 2
    ask = sdk_ask if ask is None else ask
    config = load_config(REPO_CONFIG)
    now = datetime.now(timezone.utc)
    tallies: dict[str, Tally] = {}
    for language in LANGUAGES:
        t = measure(EXAMPLES, config, ask, now, language)
        tallies[language] = t
        print(
            f"{language}: 맞음 {t.correct}/{len(EXAMPLES)} · 잘못된 일치 {t.false_yes} · "
            f"잘못된 불일치 {t.false_no} · 보류 {t.hold} · 오류 {t.error}"
        )
        for miss in t.misses:
            print(f"  {miss}")
    if any(t.error > 0 for t in tallies.values()):
        print(
            "측정 실패 — API 오류 · 응답 모양 오류가 있어 정확도가 아닙니다: "
            "키 · SDK · 연결을 확인하세요"
        )
        return 3
    if passes(tallies["ko"]):
        print("권고: ko 그대로")
        return 0
    if passes(tallies["en"]):
        print('권고: QUESTION_LANGUAGE 를 "en" 으로 (코드 한 줄, 새 사이클)')
        return 1
    print("권고: 두 언어 모두 미달 — 모델 · 기준값 문제, 사람이 정합니다 (트래커 cross-cutting)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
