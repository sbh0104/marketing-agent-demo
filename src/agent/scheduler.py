"""주기 실행 — 프로세스 안의 루프 하나.

주기는 각 사이클이 *시작한* 때부터 잽니다: `poll_interval_min*60 − 걸린 시간` 만큼
(0 아래로는 내려가지 않게) 잡니다. 사이클이 끝날 때마다 대기 전에 설정을 다시 읽으므로
poll_interval_min 만 고치면 재시작 없이 다음 대기부터 주기가 바뀝니다. 잘못 고친 설정은
on_error("config", …) 로 알리고 이전 설정을 계속 씁니다. 사이클이 실패해도 알리고
계속 돕니다. Ctrl-C(KeyboardInterrupt)는 그대로 위로 올라갑니다.

대기는 하루 이하 조각으로 나눠 잡고(운영체제마다 다른 sleep 한도에 닿지 않게), 전체는 약
100년까지로 묶습니다(아주 큰 정수를 실수로 바꾸다 나는 OverflowError 방지). 하루 이하 주기는
sleep 한 번입니다.
"""
from __future__ import annotations

import time
from collections.abc import Callable

from agent.config import Config, ConfigError

_DAY_S = 86400.0  # sleep 한 번의 상한 — 하루는 어느 운영체제에서나 됩니다
_LONGEST_WAIT_S = 100 * 365 * 86400  # 대기 전체의 상한(약 100년) — 이보다 긴 주기는 사실상 영원히 기다림과 같습니다


def _wait(sleep: Callable[[float], None], seconds: float) -> None:
    """seconds 만큼 하루 이하 조각으로 나눠 잡습니다. 0 이하면 sleep(0.0) 을 한 번 부릅니다."""
    remaining = max(0.0, seconds)
    while True:
        chunk = min(remaining, _DAY_S)
        sleep(chunk)
        remaining -= chunk
        if remaining <= 0.0:
            return


def run_loop(
    cycle: Callable[[Config], None],
    reload: Callable[[], Config],
    initial: Config,
    *,
    on_error: Callable[[str, Exception], None],
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
    max_cycles: int | None = None,
) -> int:
    """사이클을 주기마다 돌리고, max_cycles 에 닿으면 돈 횟수를 돌려줍니다."""
    config = initial
    done = 0
    while True:
        started = monotonic()
        try:
            cycle(config)
        except Exception as exc:
            on_error("cycle", exc)
        done += 1
        if max_cycles is not None and done >= max_cycles:
            return done
        try:
            config = reload()
        except ConfigError as exc:
            on_error("config", exc)
        wait = min(config.poll_interval_min * 60, _LONGEST_WAIT_S) - (monotonic() - started)
        _wait(sleep, wait)
