"""주기 실행 테스트 — 가짜 시계와 가짜 sleep 으로 run_loop 의 순서를 확인합니다."""
from __future__ import annotations

import dataclasses
import unittest
from collections.abc import Iterable
from pathlib import Path

from agent.config import Config, ConfigError, load_config
from agent.scheduler import run_loop

BASE = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
FIVE = dataclasses.replace(BASE, poll_interval_min=5)


class Harness:
    def __init__(self, ticks: Iterable[float], reloads: Iterable[object] = ()) -> None:
        self._ticks = iter(ticks)
        self._reloads = iter(reloads)
        self.cycles: list[Config] = []
        self.sleeps: list[float] = []
        self.errors: list[tuple[str, Exception]] = []
        self.reload_calls = 0
        self.fail_cycles: dict[int, BaseException] = {}

    def cycle(self, config: Config) -> None:
        self.cycles.append(config)
        failure = self.fail_cycles.get(len(self.cycles))
        if failure is not None:
            raise failure

    def reload(self) -> Config:
        self.reload_calls += 1
        result = next(self._reloads, BASE)
        if isinstance(result, Exception):
            raise result
        return result

    def on_error(self, where: str, exc: Exception) -> None:
        self.errors.append((where, exc))

    def monotonic(self) -> float:
        return next(self._ticks)

    def run(self, max_cycles: int | None) -> int:
        return run_loop(
            self.cycle,
            self.reload,
            BASE,
            on_error=self.on_error,
            sleep=self.sleeps.append,
            monotonic=self.monotonic,
            max_cycles=max_cycles,
        )


class RunLoopTest(unittest.TestCase):
    def test_single_cycle_does_not_reload_or_sleep(self) -> None:
        harness = Harness(ticks=[0.0])
        self.assertEqual(harness.run(max_cycles=1), 1)
        self.assertEqual(harness.cycles, [BASE])
        self.assertEqual(harness.reload_calls, 0)
        self.assertEqual(harness.sleeps, [])

    def test_cadence_is_measured_from_cycle_start(self) -> None:
        harness = Harness(ticks=[0.0, 120.0, 1800.0])
        self.assertEqual(harness.run(max_cycles=2), 2)
        self.assertEqual(harness.sleeps, [1680.0])

    def test_reloaded_interval_changes_the_next_wait(self) -> None:
        harness = Harness(ticks=[0.0, 10.0, 1000.0, 1030.0, 2000.0], reloads=[FIVE, FIVE])
        self.assertEqual(harness.run(max_cycles=3), 3)
        self.assertEqual(harness.sleeps, [290.0, 270.0])
        self.assertEqual(harness.cycles, [BASE, FIVE, FIVE])

    def test_bad_reload_keeps_previous_config(self) -> None:
        error = ConfigError("필수 설정이 없습니다: topic")
        harness = Harness(ticks=[0.0, 60.0, 2000.0], reloads=[error])
        self.assertEqual(harness.run(max_cycles=2), 2)
        self.assertEqual(harness.errors, [("config", error)])
        self.assertEqual(harness.sleeps, [1740.0])
        self.assertEqual(harness.cycles, [BASE, BASE])

    def test_failing_cycle_is_reported_and_loop_continues(self) -> None:
        harness = Harness(ticks=[0.0, 0.0, 1800.0])
        failure = RuntimeError("탐지 실패")
        harness.fail_cycles[1] = failure
        self.assertEqual(harness.run(max_cycles=2), 2)
        self.assertEqual(harness.errors, [("cycle", failure)])
        self.assertEqual(len(harness.cycles), 2)
        self.assertEqual(harness.sleeps, [1800.0])

    def test_overrun_cycle_sleeps_zero(self) -> None:
        harness = Harness(ticks=[0.0, 5000.0, 5000.0])
        harness.run(max_cycles=2)
        self.assertEqual(harness.sleeps, [0.0])

    def test_keyboard_interrupt_propagates(self) -> None:
        harness = Harness(ticks=[0.0])
        harness.fail_cycles[1] = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            harness.run(max_cycles=None)
        self.assertEqual(harness.errors, [])


if __name__ == "__main__":
    unittest.main()
