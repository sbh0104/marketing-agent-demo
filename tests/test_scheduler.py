"""주기 실행 테스트 — 가짜 시계와 가짜 sleep 으로 run_loop 의 순서를 확인합니다."""
from __future__ import annotations

import dataclasses
import tempfile
import unittest
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.config import Config, ConfigError, load_config
from agent.scheduler import run_loop
from agent.store import Store
from tests.test_config import (
    BAD_VALUES,
    OUT_OF_RANGE_VALUES,
    REPO_CONFIG,
    TEXT_VALUES,
    variant,
    write_config,
)

BASE = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
FIVE = dataclasses.replace(BASE, poll_interval_min=5)
NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)


def use_downstream(config: Config, directory: Path) -> None:
    """설정 값을 뒤 단계처럼 써 봅니다 — 저장소의 채널 대기 계산과 Phase 4 모양의 나이 창."""
    Store(directory / "videos.json").check_post(
        "abcdefghijk", "UC1", NOW, config.limits, live=True
    )
    _ = NOW - timedelta(hours=config.trigger.max_age_hours)


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
        self.assertEqual(harness.sleeps, [7080.0])

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
        self.assertEqual(harness.sleeps, [7140.0])
        self.assertEqual(harness.cycles, [BASE, BASE])

    def test_failing_cycle_is_reported_and_loop_continues(self) -> None:
        harness = Harness(ticks=[0.0, 0.0, 1800.0])
        failure = RuntimeError("탐지 실패")
        harness.fail_cycles[1] = failure
        self.assertEqual(harness.run(max_cycles=2), 2)
        self.assertEqual(harness.errors, [("cycle", failure)])
        self.assertEqual(len(harness.cycles), 2)
        self.assertEqual(harness.sleeps, [7200.0])

    def test_overrun_cycle_sleeps_zero(self) -> None:
        harness = Harness(ticks=[0.0, 8000.0, 8000.0])
        harness.run(max_cycles=2)
        self.assertEqual(harness.sleeps, [0.0])

    def test_keyboard_interrupt_propagates(self) -> None:
        harness = Harness(ticks=[0.0])
        harness.fail_cycles[1] = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            harness.run(max_cycles=None)
        self.assertEqual(harness.errors, [])

    def run_with_interval(self, minutes: int) -> tuple[list[float], list[tuple[str, Exception]]]:
        ticks = iter([0.0, 10.0, 20.0])
        sleeps: list[float] = []
        errors: list[tuple[str, Exception]] = []

        def reload() -> Config:
            return dataclasses.replace(BASE, poll_interval_min=minutes)

        def sleep(seconds: float) -> None:
            sleeps.append(seconds)
            if len(sleeps) > 40000:
                raise AssertionError("sleep 조각이 너무 많습니다 — 대기 전체에 상한이 없습니다")

        done = run_loop(
            lambda config: None,
            reload,
            BASE,
            on_error=lambda where, exc: errors.append((where, exc)),
            sleep=sleep,
            monotonic=lambda: next(ticks),
            max_cycles=2,
        )
        self.assertEqual(done, 2)
        return sleeps, errors

    def test_huge_interval_sleeps_in_day_chunks(self) -> None:
        sleeps, errors = self.run_with_interval(10**20)
        self.assertEqual(errors, [])
        self.assertLessEqual(max(sleeps), 86400.0)
        # 대기 전체 상한 약 100년 − 걸린 10초
        self.assertEqual(sum(sleeps), 100 * 365 * 86400 - 10.0)

    def test_astronomic_interval_does_not_overflow(self) -> None:
        sleeps, errors = self.run_with_interval(10**400)
        self.assertEqual(errors, [])
        self.assertLessEqual(max(sleeps), 86400.0)
        # 대기 전체 상한 약 100년 − 걸린 10초
        self.assertEqual(sum(sleeps), 100 * 365 * 86400 - 10.0)


class RealFileReloadTest(unittest.TestCase):
    """실제 config.yaml 을 실행 중에 고쳐 다시 읽기 — 잘못 고친 값은 이전 설정 유지로 끝나야 합니다."""

    def run_three_cycles(
        self, bad_text: str
    ) -> tuple[int, list[Config], list[tuple[str, Exception]], list[float], Config]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        directory = Path(tmp.name)
        path = write_config(directory, REPO_CONFIG.read_text(encoding="utf-8"))
        initial = load_config(path)
        cycles: list[Config] = []
        errors: list[tuple[str, Exception]] = []
        sleeps: list[float] = []
        ticks = iter([0.0, 10.0, 1800.0, 1830.0, 2100.0])

        def cycle(config: Config) -> None:
            cycles.append(config)
            if len(cycles) == 1:
                write_config(directory, bad_text)
            elif len(cycles) == 2:
                write_config(directory, variant("poll_interval_min: 120 ", "poll_interval_min: 5 "))
            use_downstream(config, directory)

        done = run_loop(
            cycle,
            lambda: load_config(path),
            initial,
            on_error=lambda where, exc: errors.append((where, exc)),
            sleep=sleeps.append,
            monotonic=lambda: next(ticks),
            max_cycles=3,
        )
        return done, cycles, errors, sleeps, initial

    def test_bad_edit_keeps_previous_config_and_fix_is_picked_up(self) -> None:
        for bad in (*BAD_VALUES, *OUT_OF_RANGE_VALUES, *TEXT_VALUES):
            with self.subTest(bad.label):
                done, cycles, errors, sleeps, initial = self.run_three_cycles(
                    variant(bad.old, bad.new)
                )
                self.assertEqual(done, 3)
                self.assertEqual([where for where, _ in errors], ["config"])
                self.assertIsInstance(errors[0][1], ConfigError)
                self.assertEqual(cycles[:2], [initial, initial])
                self.assertEqual(cycles[2], dataclasses.replace(initial, poll_interval_min=5))
                self.assertEqual(sleeps, [7190.0, 270.0])


if __name__ == "__main__":
    unittest.main()
