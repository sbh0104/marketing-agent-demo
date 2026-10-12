"""설정 계약 테스트 — config.yaml 읽기와 엄격한 검사."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from agent.config import (
    CommentConfig,
    Config,
    ConfigError,
    LimitsConfig,
    TriggerConfig,
    config_from_mapping,
    load_config,
    parse_yaml,
)

REPO_CONFIG = Path(__file__).resolve().parent.parent / "config.yaml"

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
    "comment": {"min_chars": 40, "max_chars": 120},
    "chrome_debug_url": "http://localhost:9222",
    "allowed_videos": ["https://youtu.be/abcdefghijk"],
}


def valid() -> dict[str, object]:
    return copy.deepcopy(VALID)


class CommittedConfigTest(unittest.TestCase):
    def test_committed_config_holds_pdf_values_plus_search_ceiling(self) -> None:
        self.assertEqual(
            load_config(REPO_CONFIG),
            Config(
                topic="연애",
                keywords=("연애", "썸", "연애 상담", "이별", "소개팅"),
                poll_interval_min=30,
                trigger=TriggerConfig(1000, 5000, 12.0, 150.0),
                limits=LimitsConfig(10, 24.0, 100),
                comment=CommentConfig(40, 120),
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
    """YAML 1.1 이 몰래 bool · 날짜 · 정수로 바꾸는 값은 크게 실패해야 합니다."""

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


if __name__ == "__main__":
    unittest.main()
