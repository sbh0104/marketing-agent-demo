"""음성 대조 실행기 — 가드 한 줄을 일부러 망가뜨린 채 그 모듈의 테스트를 돌립니다.

    python3 -m tests.mutants <이름>

agent.guard / agent.store / agent.config / agent.scheduler / agent.logbook / agent.youtube / agent.watcher 의 소스에서 정확한 글자 하나를 바꿔 메모리에서만 모듈을 다시
만들고(파일은 건드리지 않음), 해당 테스트 모듈을 돌립니다. 종료 코드 1 은 테스트가
망가짐을 잡았다는 뜻, 2 는 이름을 모르거나 바꿀 글자가 정확히 한 번 나오지 않았다는
뜻입니다. 이 파일은 test*.py 가 아니라서 discover 가 줍지 않습니다.
"""
from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

import tests  # noqa: F401 — src/ 를 sys.path 에 넣는 준비
import agent

_SRC = Path(__file__).resolve().parent.parent / "src"

MUTANTS: dict[str, tuple[str, str, str, str]] = {
    "guard-allow-all": (
        "agent.guard",
        "tests.test_guard",
        "if video_id not in allowed:",
        "if False:",
    ),
    "guard-ignore-dry-run": (
        "agent.guard",
        "tests.test_guard",
        "if dry_run is not False:",
        "if False:",
    ),
    "guard-dry-run-truthy": (
        "agent.guard",
        "tests.test_guard",
        "if dry_run is not False:",
        "if dry_run:",
    ),
    "guard-first-v": (
        "agent.guard",
        "tests.test_guard",
        'candidate = values[0] if len(values) == 1 else ""',
        'candidate = values[0] if values else ""',
    ),
    "guard-youtu-be-first-segment": (
        "agent.guard",
        "tests.test_guard",
        "candidate = parts.path[1:]",
        'candidate = parts.path[1:].split("/")[0]',
    ),
    "guard-shorts-first-segment": (
        "agent.guard",
        "tests.test_guard",
        'candidate = rest[:-1] if rest.endswith("/") else rest',
        'candidate = rest.split("/")[0]',
    ),
    "guard-host-ignores-userinfo": (
        "agent.guard",
        "tests.test_guard",
        "host = parts.netloc.lower()",
        'host = (parts.hostname or "").lower()',
    ),
    "guard-allow-backslash": (
        "agent.guard",
        "tests.test_guard",
        r'if "\\" in text:',
        "if False:",
    ),
    "guard-youtu-be-ignores-query-v": (
        "agent.guard",
        "tests.test_guard",
        'if host == "youtu.be" and not names_v:',
        'if host == "youtu.be":',
    ),
    "guard-shorts-ignores-query-v": (
        "agent.guard",
        "tests.test_guard",
        "parts.path.startswith(_SHORTS_PREFIX) and not names_v:",
        "parts.path.startswith(_SHORTS_PREFIX):",
    ),
    "guard-query-ampersand-only": (
        "agent.guard",
        "tests.test_guard",
        'parse_qsl(parts.query.replace(";", "&"), keep_blank_values=True)',
        "parse_qsl(parts.query, keep_blank_values=True)",
    ),
    "store-no-dedupe": (
        "agent.store",
        "tests.test_store",
        "if record is not None and _is_duplicate(record, live):",
        "if False:",
    ),
    "store-no-cap": (
        "agent.store",
        "tests.test_store",
        "if len(recent) >= limits.daily_max_comments:",
        "if False:",
    ),
    "store-no-cooldown": (
        "agent.store",
        "tests.test_store",
        "if any(channel == channel_id and at > cooldown_start for channel, at in counted):",
        "if False:",
    ),
    "store-reserved-not-counted": (
        "agent.store",
        "tests.test_store",
        'COUNTED_RESULTS = ("posted", "reserved")',
        'COUNTED_RESULTS = ("posted",)',
    ),
    "store-put-overwrites-attempts": (
        "agent.store",
        "tests.test_store",
        "if record.attempts != current_attempts:",
        "if False:",
    ),
    "store-double-reserve": (
        "agent.store",
        "tests.test_store",
        'if any(att.mode == "live" for att in record.attempts):',
        "if False:",
    ),
    "config-narrow-read-errors": (
        "agent.config",
        "tests.test_config",
        "except Exception as exc:",
        "except yaml.YAMLError as exc:",
    ),
    "config-no-ceiling": (
        "agent.config",
        "tests.test_config",
        "if not number <= maximum:",
        "if False:",
    ),
    "scheduler-one-sleep": (
        "agent.scheduler",
        "tests.test_scheduler",
        "chunk = min(remaining, _DAY_S)",
        "chunk = remaining",
    ),
    "scheduler-unclamped-wait": (
        "agent.scheduler",
        "tests.test_scheduler",
        "min(config.poll_interval_min * 60, _LONGEST_WAIT_S)",
        "config.poll_interval_min * 60",
    ),
    "logbook-raw-line-breaks": (
        "agent.logbook",
        "tests.test_logbook",
        "json.dumps(value, ensure_ascii=False).translate(_LINE_BREAK_ESCAPES)",
        "json.dumps(value, ensure_ascii=False)",
    ),
    "youtube-no-search-cap": (
        "agent.youtube",
        "tests.test_youtube",
        'if call == "search.list" and used.searches >= limits.daily_max_searches:',
        "if False:",
    ),
    "youtube-no-unit-cap": (
        "agent.youtube",
        "tests.test_youtube",
        "if used.units + cost > DAILY_QUOTA_UNITS:",
        "if False:",
    ),
    "youtube-unguarded-call": (
        "agent.youtube",
        "tests.test_youtube",
        "self._ledger.reserve(call, now, limits)",
        "pass",
    ),
    "youtube-window-never-expires": (
        "agent.youtube",
        "tests.test_youtube",
        "[entry for entry in self._calls if entry.at > start]",
        "list(self._calls)",
    ),
    "watcher-silent-hold": (
        "agent.watcher",
        "tests.test_watcher",
        "self._logbook.write(Event.QUOTA, used=exc.used, limit=exc.limit, call=exc.call,"
        " counter=exc.counter, **extra)",
        "pass",
    ),
    "watcher-no-page-cap": (
        "agent.watcher",
        "tests.test_watcher",
        "for _ in range(MAX_PAGES_PER_KEYWORD):",
        "while True:",
    ),
    "watcher-silent-page-cap": (
        "agent.watcher",
        "tests.test_watcher",
        "self._logbook.write(Event.QUOTA, used=MAX_PAGES_PER_KEYWORD,"
        ' limit=MAX_PAGES_PER_KEYWORD, call="search.list", counter="pages", keyword=query)',
        "pass",
    ),
    "watcher-keeps-surrogates": (
        "agent.watcher",
        "tests.test_watcher",
        "return _SURROGATE_RE.sub(_REPLACEMENT, text)",
        "return text",
    ),
    "watcher-unicode-digits": (
        "agent.watcher",
        "tests.test_watcher",
        r'_COUNT_RE = re.compile(r"[0-9]{1,19}")',
        r'_COUNT_RE = re.compile(r"\d+")',
    ),
    "watcher-published-any-shape": (
        "agent.watcher",
        "tests.test_watcher",
        "if not isinstance(value, str) or not _PUBLISHED_RE.fullmatch(value):",
        "if not isinstance(value, str):",
    ),
}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in MUTANTS:
        names = " | ".join(MUTANTS)
        print(f"사용법: python3 -m tests.mutants <{names}>", file=sys.stderr)
        return 2
    name = argv[0]
    module_name, test_module, old, new = MUTANTS[name]

    path = _SRC.joinpath(*module_name.split(".")).with_suffix(".py")
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        print(f"anchor not found exactly once: {name}: {old}", file=sys.stderr)
        return 2
    mutated = source.replace(old, new)

    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    sys.modules[module_name] = module
    setattr(agent, module_name.rpartition(".")[2], module)
    exec(compile(mutated, str(path), "exec"), module.__dict__)

    print(f"mutant {name}: {old} -> {new}", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
