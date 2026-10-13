"""설정 계약 테스트 — config.yaml 읽기와 엄격한 검사."""
from __future__ import annotations

import copy
import inspect
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple
from unittest import mock

from agent import config as config_module
from agent.config import (
    ClassifierConfig,
    CommentConfig,
    Config,
    ConfigError,
    LimitsConfig,
    TriggerConfig,
    config_from_mapping,
    load_config,
    parse_yaml,
)
from agent.logbook import Event, format_line, parse_line
from agent.models import VideoRecord, ViewSample
from agent.scheduler import run_loop
from agent.store import Store
from agent.trigger import judge_trigger
from agent.writer import SYSTEM_PROMPT, code_failures

REPO_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"
NOW = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)

VALID = {
    "topic": "연애",
    "keywords": ["연애", "썸"],
    "poll_interval_min": 30,
    "trigger": {
        "min_views": 1000,
        "max_views": 5000,
        "max_age_hours": 12,
        "min_views_per_hour": 150,
    },
    "limits": {
        "daily_max_comments": 10,
        "channel_cooldown_hours": 24,
        "daily_max_searches": 100,
    },
    "comment": {
        "min_chars": 40,
        "max_chars": 120,
        "writer_model": "claude-sonnet-5-5",
        "check_min_probability": 0.7,
    },
    "classifier": {
        "model": "jev-latest",
        "noul_yes_min": 0.8,
        "noul_no_max": 0.2,
        "choice_min_confidence": 0.5,
        "on_topic_reasons": ["연애 고민 상담", "연애 경험담"],
        "off_topic_reasons": ["키워드만 겹침: 게임", "연애와 관계없음"],
    },
    "chrome_debug_url": "http://localhost:9222",
    "allowed_videos": ["https://youtu.be/abcdefghijk"],
}


def valid() -> dict[str, object]:
    return copy.deepcopy(VALID)


class BadValue(NamedTuple):
    """실행 중에 잘못 고친 설정 한 줄 — 읽기 오류의 재현 입력."""

    label: str
    old: str
    new: str
    cause: type[Exception]
    needle: str


def variant(old: str, new: str) -> str:
    text = REPO_CONFIG.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"config.yaml 에 정확히 한 번 나오지 않습니다: {old!r}")
    return text.replace(old, new)


def write_config(directory: Path, text: str) -> Path:
    path = directory / "config.yaml"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


# ship-check BLOCKED(2026-10-13) 재현 입력 — 실제 파일에 그대로 씁니다
BAD_VALUES: tuple[BadValue, ...] = (
    BadValue(
        "date_shaped_topic",
        "topic: 연애\n",
        "topic: 2026-02-30\n",
        ValueError,
        "설정 값을 읽을 수 없습니다 (ValueError: ",
    ),
    BadValue(
        "int_over_4300_digits",
        "poll_interval_min: 120 ",
        "poll_interval_min: " + "1" * 5000 + " ",
        ValueError,
        "설정 값을 읽을 수 없습니다 (ValueError: ",
    ),
    BadValue(
        "int_too_large_for_float",
        "  max_age_hours: 12\n",
        "  max_age_hours: 1" + "0" * 400 + "\n",
        OverflowError,
        "설정 값을 읽을 수 없습니다 (OverflowError: ",
    ),
    BadValue(
        "nesting_3000_deep",
        "topic: 연애\n",
        "topic: " + "[" * 3000 + "]" * 3000 + "\n",
        RecursionError,
        "설정 값을 읽을 수 없습니다 (RecursionError: ",
    ),
)


class RangeValue(NamedTuple):
    """읽기는 되지만 규칙 밖인 설정 한 줄 — 검사가 ConfigError 로 거부해야 합니다."""

    label: str
    old: str
    new: str
    needle: str


# HC1 인터뷰(2026-10-13) 재현 입력과 ship-report R7 하한 행 — 실제 파일에 그대로 씁니다
OUT_OF_RANGE_VALUES: tuple[RangeValue, ...] = (
    RangeValue(
        "cooldown_inf",
        "channel_cooldown_hours: 24 ",
        "channel_cooldown_hours: .inf ",
        "유한한 숫자여야 합니다: limits.channel_cooldown_hours",
    ),
    RangeValue(
        "cooldown_minus_inf",
        "channel_cooldown_hours: 24 ",
        "channel_cooldown_hours: -.inf ",
        "유한한 숫자여야 합니다: limits.channel_cooldown_hours",
    ),
    RangeValue(
        "cooldown_nan",
        "channel_cooldown_hours: 24 ",
        "channel_cooldown_hours: .nan ",
        "유한한 숫자여야 합니다: limits.channel_cooldown_hours",
    ),
    RangeValue(
        "cooldown_20000000",
        "channel_cooldown_hours: 24 ",
        "channel_cooldown_hours: 20000000 ",
        "876000 이하여야 합니다: limits.channel_cooldown_hours",
    ),
    RangeValue(
        "cooldown_just_over_ceiling",
        "channel_cooldown_hours: 24 ",
        "channel_cooldown_hours: 876000.5 ",
        "876000 이하여야 합니다: limits.channel_cooldown_hours",
    ),
    RangeValue(
        "cooldown_negative",
        "channel_cooldown_hours: 24 ",
        "channel_cooldown_hours: -1 ",
        "0 이상이어야 합니다: limits.channel_cooldown_hours",
    ),
    RangeValue(
        "max_age_inf",
        "  max_age_hours: 12\n",
        "  max_age_hours: .inf\n",
        "유한한 숫자여야 합니다: trigger.max_age_hours",
    ),
    RangeValue(
        "max_age_20000000",
        "  max_age_hours: 12\n",
        "  max_age_hours: 20000000\n",
        "876000 이하여야 합니다: trigger.max_age_hours",
    ),
    RangeValue(
        "max_age_zero",
        "  max_age_hours: 12\n",
        "  max_age_hours: 0\n",
        "0 보다 커야 합니다: trigger.max_age_hours",
    ),
    RangeValue(
        "views_per_hour_inf",
        "  min_views_per_hour: 150\n",
        "  min_views_per_hour: .inf\n",
        "유한한 숫자여야 합니다: trigger.min_views_per_hour",
    ),
    RangeValue(
        "views_per_hour_over_ceiling",
        "  min_views_per_hour: 150\n",
        "  min_views_per_hour: 1000000001\n",
        "1000000000 이하여야 합니다: trigger.min_views_per_hour",
    ),
    RangeValue(
        "daily_max_comments_negative",
        "daily_max_comments: 10 ",
        "daily_max_comments: -1 ",
        "0 이상이어야 합니다: limits.daily_max_comments",
    ),
    RangeValue(
        "check_probability_above_one",
        "check_min_probability: 0.7 ",
        "check_min_probability: 1.5 ",
        "1 이하여야 합니다: comment.check_min_probability",
    ),
    RangeValue(
        "check_probability_negative",
        "check_min_probability: 0.7 ",
        "check_min_probability: -0.1 ",
        "0 이상이어야 합니다: comment.check_min_probability",
    ),
    RangeValue(
        "check_probability_nan",
        "check_min_probability: 0.7 ",
        "check_min_probability: .nan ",
        "유한한 숫자여야 합니다: comment.check_min_probability",
    ),
    # Phase 1 ship-report R4 · Phase 1A 인터뷰 재현 입력 — 16진수 표기는 4,300자리 한도를 거치지 않고 읽히므로 상한이 막습니다
    RangeValue(
        "interval_hex_3700_f",
        "poll_interval_min: 120 ",
        "poll_interval_min: 0x" + "F" * 3700 + " ",
        "52560000 이하여야 합니다: poll_interval_min",
    ),
    RangeValue(
        "max_chars_hex_3700_f",
        "  max_chars: 120\n",
        "  max_chars: 0x" + "F" * 3700 + "\n",
        "10000 이하여야 합니다: comment.max_chars",
    ),
    RangeValue(
        "interval_over_ceiling",
        "poll_interval_min: 120 ",
        "poll_interval_min: 52560001 ",
        "52560000 이하여야 합니다: poll_interval_min",
    ),
    RangeValue(
        "min_views_over_ceiling",
        "  min_views: 1000\n",
        "  min_views: 1000000000001\n",
        "1000000000000 이하여야 합니다: trigger.min_views",
    ),
    RangeValue(
        "max_views_over_ceiling",
        "  max_views: 5000\n",
        "  max_views: 1000000000001\n",
        "1000000000000 이하여야 합니다: trigger.max_views",
    ),
    RangeValue(
        "daily_max_comments_over_ceiling",
        "daily_max_comments: 10 ",
        "daily_max_comments: 86401 ",
        "86400 이하여야 합니다: limits.daily_max_comments",
    ),
    RangeValue(
        "daily_max_searches_over_ceiling",
        "daily_max_searches: 90 ",
        "daily_max_searches: 86401 ",
        "86400 이하여야 합니다: limits.daily_max_searches",
    ),
    RangeValue(
        "min_chars_over_ceiling",
        "  min_chars: 40\n",
        "  min_chars: 10001\n",
        "10000 이하여야 합니다: comment.min_chars",
    ),
    RangeValue(
        "max_chars_over_ceiling",
        "  max_chars: 120\n",
        "  max_chars: 10001\n",
        "10000 이하여야 합니다: comment.max_chars",
    ),
)


class CommittedConfigTest(unittest.TestCase):
    def test_committed_config_holds_pdf_values_plus_search_ceiling(self) -> None:
        self.assertEqual(
            load_config(REPO_CONFIG),
            Config(
                topic="연애",
                keywords=("연애", "썸", "연애 상담", "이별", "소개팅"),
                poll_interval_min=120,
                trigger=TriggerConfig(1000, 5000, 12.0, 150.0),
                limits=LimitsConfig(10, 24.0, 90),
                comment=CommentConfig(40, 120, "claude-sonnet-5-5", 0.7),
                classifier=ClassifierConfig(
                    "jev-latest",
                    0.8,
                    0.2,
                    0.5,
                    ("연애 고민 상담", "연애 경험담", "썸 · 소개팅 이야기", "이별 · 재회 고민"),
                    (
                        "키워드만 겹침: 게임",
                        "키워드만 겹침: 음악",
                        "키워드만 겹침: 예능 · 드라마",
                        "연애와 관계없음",
                    ),
                ),
                chrome_debug_url="http://localhost:9222",
                allowed_videos=("https://youtu.be/내-테스트-영상-ID",),
            ),
        )

    def test_two_loads_of_the_same_file_are_equal(self) -> None:
        self.assertEqual(load_config(REPO_CONFIG), load_config(REPO_CONFIG))

    def test_numbers_are_stored_as_float(self) -> None:
        config = load_config(REPO_CONFIG)
        self.assertIsInstance(config.trigger.max_age_hours, float)
        self.assertIsInstance(config.trigger.min_views_per_hour, float)
        self.assertIsInstance(config.limits.channel_cooldown_hours, float)
        self.assertIsInstance(config.comment.check_min_probability, float)


class ParseYamlTest(unittest.TestCase):
    def assert_line(self, text: str, line: int) -> None:
        with self.assertRaises(ConfigError) as caught:
            parse_yaml(text)
        self.assertEqual(caught.exception.line, line)
        self.assertTrue(str(caught.exception).startswith(f"{line}번째 줄: "))

    def test_duplicate_top_level_key_reports_second_line(self) -> None:
        self.assert_line("topic: 연애\npoll_interval_min: 30\ntopic: 썸\n", 3)

    def test_duplicate_nested_key_reports_second_line(self) -> None:
        text = (
            "topic: 연애\n"
            "limits:\n"
            "  daily_max_comments: 10\n"
            "  channel_cooldown_hours: 24\n"
            "  daily_max_comments: 5\n"
        )
        self.assert_line(text, 5)

    def test_unclosed_bracket_reports_line_where_parser_stopped(self) -> None:
        self.assert_line("topic: a\nkeywords: [a, b\npoll_interval_min: 30\n", 3)

    def test_empty_text_is_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            parse_yaml("")

    def test_top_level_list_is_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            parse_yaml("- topic\n- keywords\n")

    def test_plain_mapping_parses(self) -> None:
        self.assertEqual(parse_yaml("a: 1\nb: [x, y]\n"), {"a": 1, "b": ["x", "y"]})


class Yaml11TrapTest(unittest.TestCase):
    """글자 자리에서 YAML 1.1 이 몰래 bool · 날짜 · 정수로 바꾸는 값은 크게 실패해야 합니다.
    숫자 자리의 YAML 1.1 숫자 표기는 계약 2절대로 읽힙니다."""

    def assert_rejected(self, snippet: str) -> None:
        data = valid()
        data.update(parse_yaml(snippet))
        with self.assertRaises(ConfigError):
            config_from_mapping(data)

    def test_no_inside_keywords(self) -> None:
        self.assert_rejected("keywords: [연애, no]\n")

    def test_yes_as_topic(self) -> None:
        self.assert_rejected("topic: yes\n")

    def test_date_as_topic(self) -> None:
        self.assert_rejected("topic: 2026-10-12\n")

    def test_unquoted_numeric_allowed_video(self) -> None:
        self.assert_rejected("allowed_videos:\n  - 12345678901\n")

    def test_yaml11_number_spellings_are_read_in_number_keys(self) -> None:
        data = valid()
        data.update(parse_yaml("poll_interval_min: 017\n"))
        data["limits"].update(parse_yaml("channel_cooldown_hours: 1:30\n"))
        config = config_from_mapping(data)
        self.assertEqual(config.poll_interval_min, 15)
        self.assertEqual(config.limits.channel_cooldown_hours, 90.0)


class ConfigFromMappingTest(unittest.TestCase):
    def assert_rejected(self, data: dict[str, object], needle: str = "") -> None:
        with self.assertRaises(ConfigError) as caught:
            config_from_mapping(data)
        self.assertIn(needle, str(caught.exception))

    def test_valid_mapping_loads(self) -> None:
        config = config_from_mapping(valid())
        self.assertEqual(config.keywords, ("연애", "썸"))
        self.assertEqual(config.allowed_videos, ("https://youtu.be/abcdefghijk",))

    def test_missing_nested_key_names_dotted_path(self) -> None:
        data = valid()
        del data["limits"]["daily_max_searches"]
        self.assert_rejected(data, "필수 설정이 없습니다: limits.daily_max_searches")

    def test_missing_top_level_key(self) -> None:
        data = valid()
        del data["chrome_debug_url"]
        self.assert_rejected(data, "chrome_debug_url")

    def test_unknown_nested_key_names_dotted_path(self) -> None:
        data = valid()
        data["limits"]["daily_max_comment"] = 10
        self.assert_rejected(data, "알 수 없는 설정입니다: limits.daily_max_comment")

    def test_unknown_top_level_key(self) -> None:
        data = valid()
        data["dry_run"] = True
        self.assert_rejected(data, "dry_run")

    def test_bool_interval_is_rejected(self) -> None:
        data = valid()
        data["poll_interval_min"] = True
        self.assert_rejected(data, "poll_interval_min")

    def test_zero_interval_is_rejected(self) -> None:
        data = valid()
        data["poll_interval_min"] = 0
        self.assert_rejected(data, "poll_interval_min")

    def test_max_views_below_min_views(self) -> None:
        data = valid()
        data["trigger"]["max_views"] = 999
        self.assert_rejected(data, "trigger.max_views")

    def test_max_chars_below_min_chars(self) -> None:
        data = valid()
        data["comment"]["max_chars"] = 39
        self.assert_rejected(data, "comment.max_chars")

    def test_schemeless_debug_url(self) -> None:
        data = valid()
        data["chrome_debug_url"] = "localhost:9222"
        self.assert_rejected(data, "chrome_debug_url")

    def test_empty_keywords(self) -> None:
        data = valid()
        data["keywords"] = []
        self.assert_rejected(data, "keywords")

    def test_section_must_be_mapping(self) -> None:
        data = valid()
        data["trigger"] = None
        self.assert_rejected(data, "trigger")

    def test_empty_allowed_videos_is_empty_tuple(self) -> None:
        data = valid()
        data.update(parse_yaml("allowed_videos:\n"))
        self.assertEqual(config_from_mapping(data).allowed_videos, ())

    def test_lower_bounds_reject_negative_and_zero_values(self) -> None:
        rows = (
            ("limits", "channel_cooldown_hours", -1, "0 이상이어야 합니다"),
            ("limits", "channel_cooldown_hours", float("nan"), "유한한 숫자여야 합니다"),
            ("trigger", "max_age_hours", 0, "0 보다 커야 합니다"),
            ("limits", "daily_max_comments", -1, "0 이상이어야 합니다"),
        )
        for section, key, value, message in rows:
            with self.subTest(path=f"{section}.{key}", value=value):
                data = valid()
                data[section][key] = value
                self.assert_rejected(data, f"{message}: {section}.{key}")

    def test_lower_bound_values_are_accepted(self) -> None:
        rows = (
            ("limits", "channel_cooldown_hours", 0),
            ("trigger", "min_views_per_hour", 0),
            ("limits", "daily_max_comments", 0),
            ("limits", "daily_max_searches", 0),
            ("comment", "check_min_probability", 0),
        )
        for section, key, value in rows:
            with self.subTest(path=f"{section}.{key}", value=value):
                data = valid()
                data[section][key] = value
                config_from_mapping(data)
        with self.subTest(path="poll_interval_min", value=1):
            data = valid()
            data["poll_interval_min"] = 1
            config_from_mapping(data)
        with self.subTest(path="trigger.max_views", value="trigger.min_views"):
            data = valid()
            data["trigger"]["max_views"] = data["trigger"]["min_views"]
            config_from_mapping(data)

    def test_bool_in_number_keys_is_rejected(self) -> None:
        for section, key, value in (
            ("trigger", "max_age_hours", True),
            ("limits", "channel_cooldown_hours", False),
            ("comment", "check_min_probability", True),
        ):
            with self.subTest(path=f"{section}.{key}", value=value):
                data = valid()
                data[section][key] = value
                self.assert_rejected(data, f"숫자여야 합니다: {section}.{key}")

    def test_writer_model_must_be_non_empty_text(self) -> None:
        for value in ("", 5, False):
            with self.subTest(value=value):
                data = valid()
                data["comment"]["writer_model"] = value
                self.assert_rejected(data, "비어 있지 않은 글자여야 합니다: comment.writer_model")

    def test_probability_ceiling_is_accepted(self) -> None:
        data = valid()
        data["comment"]["check_min_probability"] = 1
        floor = config_from_mapping(data).comment.check_min_probability
        self.assertEqual(floor, 1.0)
        self.assertIsInstance(floor, float)

    def test_missing_lower_bounds_are_rejected(self) -> None:
        rows = (
            ("trigger", "min_views_per_hour", -1, "0 이상이어야 합니다"),
            ("trigger", "min_views", -1, "0 이상이어야 합니다"),
            ("limits", "daily_max_searches", -1, "0 이상이어야 합니다"),
            ("comment", "min_chars", 0, "1 이상이어야 합니다"),
        )
        for section, key, value, message in rows:
            with self.subTest(path=f"{section}.{key}", value=value):
                data = valid()
                data[section][key] = value
                self.assert_rejected(data, f"{message}: {section}.{key}")

    def test_int_takes_a_required_maximum(self) -> None:
        # 결정 2 — 상한에 기본값이 없어 정수 키를 더하는 단계가 빠뜨릴 수 없습니다
        maximum = inspect.signature(config_module._int).parameters["maximum"]
        self.assertIs(maximum.default, inspect.Parameter.empty)


class ClassifierConfigTest(unittest.TestCase):
    """classifier 절 — 판별 모델 이름 · 기준값 · 이유 보기 목록의 검사."""

    def assert_rejected(self, data: dict[str, object], needle: str) -> None:
        with self.assertRaises(ConfigError) as caught:
            config_from_mapping(data)
        self.assertIn(needle, str(caught.exception))

    def test_classifier_section_loads(self) -> None:
        classifier = config_from_mapping(valid()).classifier
        self.assertEqual(
            classifier,
            ClassifierConfig(
                "jev-latest",
                0.8,
                0.2,
                0.5,
                ("연애 고민 상담", "연애 경험담"),
                ("키워드만 겹침: 게임", "연애와 관계없음"),
            ),
        )
        for number in (
            classifier.noul_yes_min,
            classifier.noul_no_max,
            classifier.choice_min_confidence,
        ):
            self.assertIsInstance(number, float)
        self.assertIsInstance(classifier.on_topic_reasons, tuple)
        self.assertIsInstance(classifier.off_topic_reasons, tuple)

    def test_missing_classifier_key_names_dotted_path(self) -> None:
        data = valid()
        del data["classifier"]["noul_no_max"]
        self.assert_rejected(data, "필수 설정이 없습니다: classifier.noul_no_max")

    def test_unknown_classifier_key_names_dotted_path(self) -> None:
        data = valid()
        data["classifier"]["question_language"] = "en"
        self.assert_rejected(data, "알 수 없는 설정입니다: classifier.question_language")

    def test_probability_keys_out_of_range_are_rejected(self) -> None:
        rows = (
            ("noul_yes_min", 0.5, "0.5 보다 커야 합니다"),
            ("noul_yes_min", 1.01, "1 이하여야 합니다"),
            ("noul_yes_min", True, "숫자여야 합니다"),
            ("noul_no_max", -0.1, "0 이상이어야 합니다"),
            ("noul_no_max", 0.8, "noul_yes_min 보다 작아야 합니다"),
            ("choice_min_confidence", 1.5, "1 이하여야 합니다"),
            ("choice_min_confidence", -0.1, "0 이상이어야 합니다"),
            ("choice_min_confidence", float("nan"), "유한한 숫자여야 합니다"),
        )
        for key, value, message in rows:
            with self.subTest(key=key, value=value):
                data = valid()
                data["classifier"][key] = value
                self.assert_rejected(data, f"{message}: classifier.{key}")

    def test_probability_bounds_are_accepted(self) -> None:
        data = valid()
        data["classifier"]["noul_yes_min"] = 1
        classifier = config_from_mapping(data).classifier
        self.assertEqual(classifier.noul_yes_min, 1.0)
        self.assertIsInstance(classifier.noul_yes_min, float)
        for key, value in (
            ("noul_no_max", 0),
            ("choice_min_confidence", 0),
            ("choice_min_confidence", 1),
        ):
            with self.subTest(key=key, value=value):
                data = valid()
                data["classifier"][key] = value
                self.assertEqual(getattr(config_from_mapping(data).classifier, key), value)

    def test_reason_list_rules(self) -> None:
        on = "classifier.on_topic_reasons"
        off = "classifier.off_topic_reasons"
        rows = (
            ("on_topic_reasons", [], f"보기가 하나 이상 필요합니다: {on}"),
            ("on_topic_reasons", "연애", f"보기가 하나 이상 필요합니다: {on}"),
            ("on_topic_reasons", ["연애 고민 상담", ""], f"비어 있지 않은 글자여야 합니다: {on}[1]"),
            ("on_topic_reasons", ["가" * 41], f"40자 이하여야 합니다: {on}[0]"),
            (
                "on_topic_reasons",
                ["연애 고민 상담", "연애 고민 상담"],
                f"보기 이름이 겹칩니다: {on}[1]",
            ),
            (
                "off_topic_reasons",
                ["키워드만 겹침: 게임", "연애 고민 상담"],
                f"보기 이름이 겹칩니다: {off}[1]",
            ),
        )
        for key, value, needle in rows:
            with self.subTest(key=key, value=value):
                data = valid()
                data["classifier"][key] = value
                self.assert_rejected(data, needle)
        with self.subTest("26 + 25"):
            data = valid()
            data["classifier"]["on_topic_reasons"] = [f"일치 {i}" for i in range(26)]
            data["classifier"]["off_topic_reasons"] = [f"불일치 {i}" for i in range(25)]
            self.assert_rejected(data, "보기는 모두 50개 이하여야 합니다: classifier")

    def test_unquoted_colon_reason_is_rejected(self) -> None:
        data = valid()
        data["classifier"].update(parse_yaml("off_topic_reasons:\n  - 키워드만 겹침: 게임\n"))
        self.assertEqual(data["classifier"]["off_topic_reasons"], [{"키워드만 겹침": "게임"}])
        self.assert_rejected(
            data, "비어 있지 않은 글자여야 합니다: classifier.off_topic_reasons[0]"
        )

    def test_empty_model_is_rejected(self) -> None:
        for value in ("", None):
            with self.subTest(value=value):
                data = valid()
                data["classifier"]["model"] = value
                self.assert_rejected(data, "비어 있지 않은 글자여야 합니다: classifier.model")


class LoadConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_bom_is_accepted(self) -> None:
        text = REPO_CONFIG.read_text(encoding="utf-8")
        path = self.dir / "config.yaml"
        path.write_text("﻿" + text, encoding="utf-8", newline="\n")
        self.assertEqual(load_config(path), load_config(REPO_CONFIG))

    def test_missing_file_raises_config_error(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            load_config(self.dir / "없는-파일.yaml")
        self.assertIn("설정 파일을 읽을 수 없습니다", str(caught.exception))

    def test_non_utf8_save_raises_config_error(self) -> None:
        # 윈도우 메모장의 ANSI(CP949)·Unicode(UTF-16) 저장 — run_loop 는 ConfigError 만 잡습니다
        text = REPO_CONFIG.read_text(encoding="utf-8")
        path = self.dir / "config.yaml"
        for codec in ("cp949", "utf-16"):
            with self.subTest(codec=codec):
                path.write_bytes(text.encode(codec, errors="replace"))
                with self.assertRaises(ConfigError) as caught:
                    load_config(path)
                self.assertIn("UTF-8", str(caught.exception))


class ReadFailureTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_every_read_failure_is_config_error(self) -> None:
        for bad in BAD_VALUES:
            with self.subTest(bad.label):
                path = write_config(self.dir, variant(bad.old, bad.new))
                with self.assertRaises(ConfigError) as caught:
                    load_config(path)
                self.assertIn(bad.needle, str(caught.exception))
                self.assertIsInstance(caught.exception.__cause__, bad.cause)

    def test_fixed_file_loads_again(self) -> None:
        date_shaped = BAD_VALUES[0]
        path = write_config(self.dir, variant(date_shaped.old, date_shaped.new))
        with self.assertRaises(ConfigError):
            load_config(path)
        write_config(self.dir, REPO_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(load_config(path), load_config(REPO_CONFIG))

    def test_unexpected_exception_while_reading_is_config_error(self) -> None:
        path = write_config(self.dir, REPO_CONFIG.read_text(encoding="utf-8"))
        failure = TypeError("뜻밖의 오류")
        with mock.patch("agent.config.config_from_mapping", side_effect=failure):
            with self.assertRaises(ConfigError) as caught:
                load_config(path)
        self.assertIsInstance(caught.exception.__cause__, TypeError)
        self.assertIn("(TypeError: ", str(caught.exception))

    def test_keyboard_interrupt_is_not_converted(self) -> None:
        path = write_config(self.dir, REPO_CONFIG.read_text(encoding="utf-8"))
        with mock.patch("agent.config.parse_yaml", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                load_config(path)


class RangeFailureTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_every_out_of_range_value_is_config_error(self) -> None:
        for bad in OUT_OF_RANGE_VALUES:
            with self.subTest(bad.label):
                path = write_config(self.dir, variant(bad.old, bad.new))
                with self.assertRaises(ConfigError) as caught:
                    load_config(path)
                self.assertIn(bad.needle, str(caught.exception))
                # 변환 중 터진 것이 아니라 규칙이 거부한 값입니다
                self.assertIsNone(caught.exception.__cause__)

    def test_ceiling_values_load_and_stay_usable_downstream(self) -> None:
        text = variant("  max_age_hours: 12\n", "  max_age_hours: 876000\n")
        text = text.replace("channel_cooldown_hours: 24 ", "channel_cooldown_hours: 876000 ")
        text = text.replace("  min_views_per_hour: 150\n", "  min_views_per_hour: 1000000000\n")
        config = load_config(write_config(self.dir, text))
        self.assertEqual(
            (
                config.trigger.max_age_hours,
                config.trigger.min_views_per_hour,
                config.limits.channel_cooldown_hours,
            ),
            (876000.0, 1000000000.0, 876000.0),
        )
        check = Store(self.dir / "videos.json").check_post(
            "abcdefghijk", "UC1", NOW, config.limits, live=True
        )
        self.assertEqual((check.allowed, check.reason), (True, "ok"))
        self.assertLess(NOW - timedelta(hours=config.trigger.max_age_hours), NOW)

    def test_integer_ceilings_load_and_stay_usable_downstream(self) -> None:
        text = variant("poll_interval_min: 120 ", "poll_interval_min: 52560000 ")
        text = text.replace("  min_views: 1000\n", "  min_views: 1000000000000\n")
        text = text.replace("  max_views: 5000\n", "  max_views: 1000000000000\n")
        text = text.replace("daily_max_comments: 10 ", "daily_max_comments: 86400 ")
        text = text.replace("daily_max_searches: 90 ", "daily_max_searches: 86400 ")
        text = text.replace("  min_chars: 40\n", "  min_chars: 10000\n")
        text = text.replace("  max_chars: 120\n", "  max_chars: 10000\n")
        config = load_config(write_config(self.dir, text))
        ints = (
            config.poll_interval_min,
            config.trigger.min_views,
            config.trigger.max_views,
            config.limits.daily_max_comments,
            config.limits.daily_max_searches,
            config.comment.min_chars,
            config.comment.max_chars,
        )
        self.assertEqual(ints, (52560000, 10**12, 10**12, 86400, 86400, 10000, 10000))
        # 정수가 글자로 쓰이는 자리 — START · QUOTA 로그 줄
        start = format_line(
            NOW,
            Event.START,
            {"mode": "test", "allowed": 0, "interval_min": config.poll_interval_min},
        )
        self.assertEqual(parse_line(start)[2]["interval_min"], "52560000")
        for value in ints:
            with self.subTest(quota=value):
                parse_line(format_line(NOW, Event.QUOTA, {"used": value, "limit": value}))
        # 댓글 작성 지시문과 코드 검사의 글자 수
        prompt = SYSTEM_PROMPT.format(
            min_chars=config.comment.min_chars, max_chars=config.comment.max_chars
        )
        self.assertIn("10000자 이상 10000자 이하", prompt)
        self.assertEqual(code_failures("가" * 10000, [], config.comment), [])
        self.assertNotEqual(code_failures("가", [], config.comment), [])
        # 하루 상한 · 조회수 판정 · 주기 대기
        check = Store(self.dir / "videos.json").check_post(
            "abcdefghijk", "UC1", NOW, config.limits, live=True
        )
        self.assertEqual((check.allowed, check.reason), (True, "ok"))
        record = VideoRecord(
            video_id="abcdefghijk",
            channel_id="UC1",
            title="제목",
            description="",
            published_at=NOW - timedelta(hours=1),
            detected_at=NOW - timedelta(hours=1),
            keyword="썸",
            view_history=[
                ViewSample(NOW - timedelta(minutes=30), 10**12 - 10),
                ViewSample(NOW, 10**12),
            ],
        )
        verdict = judge_trigger(record, config.trigger, NOW)
        self.assertEqual((verdict.verdict.value, verdict.reason), ("no", "too_slow"))
        errors: list[tuple[str, Exception]] = []
        sleeps: list[float] = []
        ticks = iter([0.0, 10.0, 20.0])
        done = run_loop(
            lambda c: None,
            lambda: config,
            config,
            on_error=lambda where, exc: errors.append((where, exc)),
            sleep=sleeps.append,
            monotonic=lambda: next(ticks),
            max_cycles=2,
        )
        self.assertEqual(done, 2)
        self.assertEqual(errors, [])
        self.assertLessEqual(max(sleeps), 86400.0)
        self.assertEqual(sum(sleeps), 100 * 365 * 86400 - 10.0)


if __name__ == "__main__":
    unittest.main()
