"""음성 대조 실행기 — 가드 한 줄을 일부러 망가뜨린 채 그 모듈의 테스트를 돌립니다.

    python3 -m tests.mutants <이름>

agent.guard / agent.store / agent.config / agent.scheduler / agent.logbook / agent.poster /
agent.chrome / agent.classifier / agent.writer / agent.youtube / agent.watcher /
tests.live_check 의 소스에서 정확한 글자 하나를 바꿔 메모리에서만 모듈을 다시
만들고(파일은 건드리지 않음), 해당 테스트 모듈을 돌립니다. agent.* 모듈은 src/ 에서,
tests.* 모듈은 저장소 뿌리에서 읽습니다. 종료 코드 1 은 테스트가
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

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"

MUTANTS: dict[str, tuple[str, str, str, str]] = {
    "poster-open-received-ref": (
        "agent.poster",
        "tests.test_poster",
        "page.open(WATCH_URL.format(video_id=decision.video_id))",
        "page.open(decision.video_id)",
    ),
    "poster-recheck-before-prepare": (
        "agent.poster",
        "tests.test_poster",
        "page.prepare_comment(text)\n            page_url = page.url",
        "page_url = page.url\n            page.prepare_comment(text)",
    ),
    "poster-no-recheck": (
        "agent.poster",
        "tests.test_poster",
        "recheck = decide_post(page_url, config.allowed_videos, dry_run)",
        "recheck = decision",
    ),
    "poster-no-page-mismatch": (
        "agent.poster",
        "tests.test_poster",
        "if recheck.video_id != decision.video_id:",
        "if False:",
    ),
    "poster-skip-reserve": (
        "agent.poster",
        "tests.test_poster",
        "store.reserve_live(video_id, clock())",
        "None",
    ),
    "poster-click-error-as-failed": (
        "agent.poster",
        "tests.test_poster",
        "except PageError as exc:",
        "except Exception as exc:",
    ),
    "poster-unconfirmed-as-posted": (
        "agent.poster",
        "tests.test_poster",
        "if confirmed is True:",
        "if True:",
    ),
    "poster-ignore-check": (
        "agent.poster",
        "tests.test_poster",
        "if not check.allowed:",
        "if False:",
    ),
    "poster-test-mode-opens-chrome": (
        "agent.poster",
        "tests.test_poster",
        "if not decision.live:",
        "if False:",
    ),
    "chrome-allow-default-profile": (
        "agent.chrome",
        "tests.test_chrome",
        "if _same_or_inside(path, Path(default).expanduser().resolve()):",
        "if False:",
    ),
    "chrome-allow-repo-folder": (
        "agent.chrome",
        "tests.test_chrome",
        "if _same_or_inside(path, repo) and not _same_or_inside(path, repo / PROFILE_DIR_NAME):",
        "if False:",
    ),
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
        'if host == "youtu.be" and share_query:',
        'if host == "youtu.be":',
    ),
    "guard-shorts-ignores-query-v": (
        "agent.guard",
        "tests.test_guard",
        "parts.path.startswith(_SHORTS_PREFIX) and share_query:",
        "parts.path.startswith(_SHORTS_PREFIX):",
    ),
    "guard-query-ampersand-only": (
        "agent.guard",
        "tests.test_guard",
        'parse_qsl(parts.query.replace(";", "&"), keep_blank_values=True)',
        "parse_qsl(parts.query, keep_blank_values=True)",
    ),
    "guard-share-names-blocklist": (
        "agent.guard",
        "tests.test_guard",
        "share_query = all(key in _SHARE_QUERY_NAMES for key, _ in pairs)",
        'share_query = not any(key == "v" for key, _ in pairs)',
    ),
    "guard-share-names-ignore-case": (
        "agent.guard",
        "tests.test_guard",
        "key in _SHARE_QUERY_NAMES",
        "key.lower() in _SHARE_QUERY_NAMES",
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
    "config-no-int-ceiling": (
        "agent.config",
        "tests.test_config",
        "if value > maximum:",
        "if False:",
    ),
    "config-text-any-char": (
        "agent.config",
        "tests.test_config",
        "if not all(map(_is_raw, value)):",
        "if False:",
    ),
    "config-text-edge-spaces": (
        "agent.config",
        "tests.test_config",
        'if value[0] == " " or value[-1] == " ":',
        "if False:",
    ),
    "config-debug-url-skips-text": (
        "agent.config",
        "tests.test_config",
        'url = _text(data["chrome_debug_url"], "chrome_debug_url")',
        'url = data["chrome_debug_url"]',
    ),
    "config-no-topic-ceiling": (
        "agent.config",
        "tests.test_config",
        "if len(topic) > _MAX_TOPIC_CHARS:",
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
        'return "".join(char if _is_raw(char) else json.dumps(char)[1:-1] for char in quoted)',
        "return quoted",
    ),
    "logbook-bare-control-chars": (
        "agent.logbook",
        "tests.test_logbook",
        "_BARE_RE.fullmatch(value) and all(map(_is_raw, value))",
        "_BARE_RE.fullmatch(value)",
    ),
    "logbook-read-latin1": (
        "agent.logbook",
        "tests.test_logbook",
        'text = data.decode("utf-8")',
        'text = data.decode("latin-1")',
    ),
    "logbook-read-splitlines": (
        "agent.logbook",
        "tests.test_logbook",
        r'*lines, tail = text.split("\n")',
        r'*lines, tail = [*text.splitlines(), ""]',
    ),
    "logbook-read-skips-bad-lines": (
        "agent.logbook",
        "tests.test_logbook",
        'raise ValueError(f"{number}번째 줄: {exc}") from exc',
        "continue",
    ),
    "logbook-read-keeps-cut-line": (
        "agent.logbook",
        "tests.test_logbook",
        "if tail:",
        "if False:",
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
    "writer-hardcoded-model": (
        "agent.writer",
        "tests.test_writer",
        'model=config.writer_model,',
        'model="claude-sonnet-5-5",',
    ),
    "writer-no-rewrite": (
        "agent.writer",
        "tests.test_writer",
        "for attempt in (1, 2):",
        "for attempt in (1,):",
    ),
    "writer-third-try": (
        "agent.writer",
        "tests.test_writer",
        "for attempt in (1, 2):",
        "for attempt in (1, 2, 3):",
    ),
    "writer-ignore-self-check": (
        "agent.writer",
        "tests.test_writer",
        "if score + _TOLERANCE < threshold:",
        "if False:",
    ),
    "writer-threshold-strict": (
        "agent.writer",
        "tests.test_writer",
        "if score + _TOLERANCE < threshold:",
        "if score <= threshold:",
    ),
    "writer-no-float-tolerance": (
        "agent.writer",
        "tests.test_writer",
        "if score + _TOLERANCE < threshold:",
        "if score < threshold:",
    ),
    "writer-ad-not-inverted": (
        "agent.writer",
        "tests.test_writer",
        "score = 1.0 - probability if name in INVERTED_QUESTIONS else probability",
        "score = probability",
    ),
    "writer-trusts-jev-answer": (
        "agent.writer",
        "tests.test_writer",
        "if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:",
        "if False:",
    ),
    "writer-no-length": (
        "agent.writer",
        "tests.test_writer",
        "if not config.min_chars <= length <= config.max_chars:",
        "if False:",
    ),
    "writer-length-in-bytes": (
        "agent.writer",
        "tests.test_writer",
        "length = len(text)",
        'length = len(text.encode("utf-8"))',
    ),
    "writer-no-link": (
        "agent.writer",
        "tests.test_writer",
        "if link is not None:",
        "if False:",
    ),
    "writer-link-no-nfkc": (
        "agent.writer",
        "tests.test_writer",
        'folded = unicodedata.normalize("NFKC", text).casefold()',
        "folded = text.casefold()",
    ),
    "writer-link-view-keeps-all": (
        "agent.writer",
        "tests.test_writer",
        'if ch.isalnum() or ch == "@":',
        "if True:",
    ),
    "writer-link-ascii-separators-only": (
        "agent.writer",
        "tests.test_writer",
        "if any(part in name for part in _SEPARATOR_NAMES):",
        'if ch in ".:/":',
    ),
    "writer-link-latin-left-only": (
        "agent.writer",
        "tests.test_writer",
        r"[^\W_]\.+[a-z]{2,}",
        r"[a-z0-9]\.+[a-z]{2,}",
    ),
    "writer-link-no-handle": (
        "agent.writer",
        "tests.test_writer",
        r"|@[^\W_]",
        "",
    ),
    "writer-no-repeat": (
        "agent.writer",
        "tests.test_writer",
        "if match.size >= min_run:",
        "if False:",
    ),
    "writer-repeat-keeps-punctuation": (
        "agent.writer",
        "tests.test_writer",
        ".casefold() if ch.isalnum())",
        ".casefold())",
    ),
    "writer-repeat-all-history": (
        "agent.writer",
        "tests.test_writer",
        "recent = list(previous)[-RECENT_WINDOW:]",
        "recent = list(previous)",
    ),
    "writer-unescaped-material": (
        "agent.writer",
        "tests.test_writer",
        'text.replace("<", "＜").replace(">", "＞")',
        "text",
    ),
    "writer-api-error-unlogged": (
        "agent.writer",
        "tests.test_writer",
        "logbook.write(Event.ERROR, where=where, reason=reason, video=record.video_id)",
        "None",
    ),
    "writer-self-skip-checked": (
        "agent.writer",
        "tests.test_writer",
        "if isinstance(reply, str):",
        "if False:",
    ),
    "writer-no-concern-ignored": (
        "agent.writer",
        "tests.test_writer",
        "if not has_concern:",
        "if False:",
    ),
    "writer-no-frame": (
        "agent.writer",
        "tests.test_writer",
        "if piece in others:",
        "if False:",
    ),
    "writer-frame-counts-required-word": (
        "agent.writer",
        "tests.test_writer",
        "if not covered.intersection(range(start, start + FRAME_MIN_CHARS))",
        "if True",
    ),
    "task-table-missing-sentence-ignored": (
        "tests.test_task_table",
        "tests.test_task_table",
        'problems.append(f"없는 문장: {sentence}")',
        "None",
    ),
    "classifier-error-yes": (
        "agent.classifier",
        "tests.test_classifier",
        'return Judgement(Verdict.HOLD, f"API 오류: {exc}", now)',
        'return Judgement(Verdict.YES, f"API 오류: {exc}", now)',
    ),
    "classifier-malformed-yes": (
        "agent.classifier",
        "tests.test_classifier",
        'return Judgement(Verdict.HOLD, f"응답 모양 오류: {type(exc).__name__}: {exc}", now)',
        'return Judgement(Verdict.YES, f"응답 모양 오류: {type(exc).__name__}: {exc}", now)',
    ),
    "classifier-unchecked-probability": (
        "agent.classifier",
        "tests.test_classifier",
        "if not 0.0 <= number <= 1.0:",
        "if False:",
    ),
    "classifier-no-confidence-floor": (
        "agent.classifier",
        "tests.test_classifier",
        "if confidence < config.choice_min_confidence:",
        "if False:",
    ),
    "classifier-keyword-only-passes": (
        "agent.classifier",
        "tests.test_classifier",
        "if noul >= config.noul_yes_min and on_topic:",
        "if noul >= config.noul_yes_min:",
    ),
    "classifier-no-truncation": (
        "agent.classifier",
        "tests.test_classifier",
        "_MAX_INPUT_BYTES = 32_000",
        "_MAX_INPUT_BYTES = 10**9",
    ),
    "classifier-error-hold-unmarked": (
        "agent.classifier",
        "tests.test_classifier",
        "return judgement.verdict is Verdict.HOLD and judgement.reason.startswith(ERROR_PREFIXES)",
        "return False",
    ),
    "classifier-swallows-faults": (
        "agent.classifier",
        "tests.test_classifier",
        "except JevError as exc:",
        "except Exception as exc:",
    ),
    "trigger-negative-speed": (
        "agent.trigger",
        "tests.test_trigger",
        "if gained < 0:",
        "if False:",
    ),
    "trigger-flat-is-decrease": (
        "agent.trigger",
        "tests.test_trigger",
        "if gained < 0:",
        "if gained <= 0:",
    ),
    "trigger-list-order": (
        "agent.trigger",
        "tests.test_trigger",
        "ordered = sorted(history, key=lambda sample: (_utc(sample.at), sample.count))",
        "ordered = list(history)",
    ),
    "trigger-same-instant": (
        "agent.trigger",
        "tests.test_trigger",
        "earlier = [sample for sample in ordered if _utc(sample.at) < _utc(latest.at)]",
        "earlier = ordered[:-1]",
    ),
    "trigger-min-views-exclusive": (
        "agent.trigger",
        "tests.test_trigger",
        "if latest.count < config.min_views:",
        "if latest.count <= config.min_views:",
    ),
    "trigger-max-views-exclusive": (
        "agent.trigger",
        "tests.test_trigger",
        "if latest.count > config.max_views:",
        "if latest.count >= config.max_views:",
    ),
    "trigger-future-publish-passes": (
        "agent.trigger",
        "tests.test_trigger",
        "if _utc(record.published_at) > _utc(now):",
        "if False:",
    ),
    "trigger-future-publish-inclusive": (
        "agent.trigger",
        "tests.test_trigger",
        "if _utc(record.published_at) > _utc(now):",
        "if _utc(record.published_at) >= _utc(now):",
    ),
    "trigger-age-exclusive": (
        "agent.trigger",
        "tests.test_trigger",
        "if _utc(now) - _utc(record.published_at) > timedelta(hours=config.max_age_hours):",
        "if _utc(now) - _utc(record.published_at) >= timedelta(hours=config.max_age_hours):",
    ),
    "trigger-rate-exclusive": (
        "agent.trigger",
        "tests.test_trigger",
        "if rate < config.min_views_per_hour:",
        "if rate <= config.min_views_per_hour:",
    ),
    "youtube-comments-free": (
        "agent.youtube",
        "tests.test_youtube",
        '"commentThreads.list": 1}',
        '"commentThreads.list": 0}',
    ),
    "youtube-comments-any-403-disabled": (
        "agent.youtube",
        "tests.test_youtube",
        "if exc.reason == COMMENTS_DISABLED:",
        'if exc.reason.startswith("HTTP 403"):',
    ),
    "live-check-ceiling-plus-one": (
        "tests.live_check",
        "tests.test_live_check",
        "if self.counts[service] >= self.ceilings[service]:",
        "if self.counts[service] > self.ceilings[service]:",
    ),
    "live-check-ceiling-swallowed": (
        "tests.live_check",
        "tests.test_live_check",
        "class CeilingReached(BaseException):",
        "class CeilingReached(Exception):",
    ),
    "live-check-key-unredacted": (
        "tests.live_check",
        "tests.test_live_check",
        "return self._pattern.sub(self._mask, text)",
        "return text",
    ),
    "live-check-views-exclusive": (
        "tests.live_check",
        "tests.test_live_check",
        "if trigger.min_views <= views <= trigger.max_views:",
        "if trigger.min_views < views < trigger.max_views:",
    ),
    "live-check-calls-without-key": (
        "tests.live_check",
        "tests.test_live_check",
        "if problems:",
        "if False:",
    ),
    "live-check-unmeasured-ignored": (
        "tests.live_check",
        "tests.test_live_check",
        "if example_errors:",
        "if False:",
    ),
    "live-check-call-errors-ignored": (
        "tests.live_check",
        "tests.test_live_check",
        "if call_errors:",
        "if False:",
    ),
    "live-check-video-errors-ignored": (
        "tests.live_check",
        "tests.test_live_check",
        "if video_errors:",
        "if False:",
    ),
    "live-check-api-failure-as-skip": (
        "tests.live_check",
        "tests.test_live_check",
        'video["result"] = "error" if error_cause is not None else "skip"',
        'video["result"] = "skip"',
    ),
    "live-check-no-margin": (
        "tests.live_check",
        "tests.test_live_check",
        "MARGIN = 0.05",
        "MARGIN = 0.0",
    ),
    "live-check-floor-above-one": (
        "tests.live_check",
        "tests.test_live_check",
        "if current < x <= 1.0",
        "if current < x",
    ),
    "live-check-skip-half-stops": (
        "tests.live_check",
        "tests.test_live_check",
        "if 2 * skipped > written:",
        "if 2 * skipped >= written:",
    ),
    "live-check-one-model-stops": (
        "tests.live_check",
        "tests.test_live_check",
        'if all(_model_status(result, name) == "rejected" for name in MODEL_NAMES):',
        'if any(_model_status(result, name) == "rejected" for name in MODEL_NAMES):',
    ),
    "live-check-grader-in-agent": (
        "agent.writer",
        "tests.test_live_check",
        "MAX_TOKENS = 1024",
        'MAX_TOKENS = 1024\nGRADE_SYSTEM = "채점"',
    ),
    "live-check-cli-exception-only": (
        "tests.live_check",
        "tests.test_live_check",
        "except BaseException as exc:",
        "except Exception as exc:",
    ),
    "live-check-entry-skips-cli": (
        "tests.live_check",
        "tests.test_live_check",
        "raise SystemExit(cli(sys.argv[1:]))",
        "raise SystemExit(main(sys.argv[1:]))",
    ),
    "live-check-grade-block-half-stops": (
        "tests.live_check",
        "tests.test_live_check",
        "if 2 * grade_errors > graded:",
        "if 2 * grade_errors >= graded:",
    ),
    "live-check-grade-block-schema-ignored": (
        "tests.live_check",
        "tests.test_live_check",
        'if result["schema_version"] >= GRADE_BLOCK_SCHEMA:',
        "if True:",
    ),
    "live-check-popular-shortfall-ignored": (
        "tests.live_check",
        "tests.test_live_check",
        "self.drafts < self.limits.target_drafts or self.popular < self.limits.popular_drafts_min",
        "self.drafts < self.limits.target_drafts",
    ),
    "live-check-best-setting-tie-raised": (
        "tests.live_check",
        "tests.test_live_check",
        "if false_yes == 0 and (best is None or correct > best[1]):",
        "if false_yes == 0 and (best is None or correct >= best[1]):",
    ),
    "live-check-contacts-unmasked": (
        "tests.live_check",
        "tests.test_live_check",
        "for start, end in _contact_spans(text):",
        "for start, end in ():",
    ),
    "live-check-contact-line-blind": (
        "tests.live_check",
        "tests.test_live_check",
        "places = contact_places(paths)",
        "places = 0",
    ),
    "live-check-clip-before-mask": (
        "tests.live_check",
        "tests.test_live_check",
        "return mask_contacts(mask_contacts(redactor(_clean(text, len(text))))[:limit])",
        "return mask_contacts(redactor(_clean(text, limit)))",
    ),
    "live-check-untrusted-unmasked-at-write": (
        "tests.live_check",
        "tests.test_live_check",
        '_scrub(item, redactor, outside or key == "untrusted")',
        "_scrub(item, redactor, outside)",
    ),
    "live-check-published-scan-blind": (
        "tests.live_check",
        "tests.test_live_check_published",
        "return sum(count_contacts(text) for path in paths for text in file_texts(path))",
        "return 0",
    ),
    "live-check-draft-masked-at-write-only": (
        "tests.live_check",
        "tests.test_live_check",
        '"comment": mask_contacts(self.redactor(text)),',
        '"comment": self.redactor(text),',
    ),
    "live-check-kept-contacts-before-keys": (
        "tests.live_check",
        "tests.test_live_check",
        "mask_contacts(redactor(_clean(text, len(text))))",
        "redactor(mask_contacts(_clean(text, len(text))))",
    ),
    "live-check-draft-contacts-before-keys": (
        "tests.live_check",
        "tests.test_live_check",
        '"comment": mask_contacts(self.redactor(text)),',
        '"comment": self.redactor(mask_contacts(text)),',
    ),
    "live-check-gap-ambiguous": (
        "tests.live_check",
        "tests.test_live_check",
        r'_GAP = rf"[ \t]*(?:[.{_DASH}][ \t]*)?"',
        r'_GAP = rf"[ \t]*[.{_DASH}]?[ \t]*"',
    ),
    "live-check-dash-like-unbounded": (
        "tests.live_check",
        "tests.test_live_check",
        r'_DASH_BETWEEN_DIGITS.sub(r"\1-", text.translate(MATCH_VIEW))',
        r'text.translate({**MATCH_VIEW, **dict.fromkeys(map(ord, _DASH_LIKE), ord("-"))})',
    ),
    "live-check-code-failures-raw": (
        "tests.live_check",
        "tests.test_live_check",
        '"code_failures": _stored_failures(failures),',
        '"code_failures": failures,',
    ),
    "live-check-code-failures-dropped": (
        "tests.live_check",
        "tests.test_live_check",
        '"code_failures": _stored_failures(failures),',
        '"code_failures": [],',
    ),
    "live-check-repeat-count-shifted": (
        "tests.live_check",
        "tests.test_live_check",
        "len(reason) - len(REPEAT_REASON)",
        "len(reason) - len(REPEAT_REASON) + 1",
    ),
    "live-check-contact-keys-unread": (
        "tests.live_check",
        "tests.test_live_check",
        "found.append(key)",
        'found.append("")',
    ),
    "live-check-contact-line-summary-blind": (
        "tests.live_check",
        "tests.test_live_check",
        "places = contact_places(paths)",
        "places = contact_places(paths[:1])",
    ),
    "live-check-contact-line-one-place-passes": (
        "tests.live_check",
        "tests.test_live_check",
        "if places:",
        "if places > 1:",
    ),
    "live-check-code-check-reads-masked": (
        "tests.live_check",
        "tests.test_live_check",
        "failures = code_failures(text, recent, self.comment_config)",
        "failures = code_failures(mask_contacts(text), recent, self.comment_config)",
    ),
    "live-check-grade-reads-masked": (
        "tests.live_check",
        "tests.test_live_check",
        'self.claude, self.result["grader_model"], record, comments, concern, text',
        'self.claude, self.result["grader_model"], record, comments, concern, mask_contacts(text)',
    ),
    "live-check-passed-ignores-code-check": (
        "tests.live_check",
        "tests.test_live_check",
        '"passed": self_check_pass is True and not failures,',
        '"passed": self_check_pass is True,',
    ),
    "live-check-applied-yes-floor-lowered": (
        "agent.config",
        "tests.test_live_check_applied",
        'section["noul_yes_min"], "classifier.noul_yes_min", 0.5, 1.0, inclusive=False',
        'section["noul_yes_min"] - 0.05, "classifier.noul_yes_min", 0.5, 1.0, inclusive=False',
    ),
    "live-check-applied-floor-lowered": (
        "agent.config",
        "tests.test_live_check_applied",
        'comment["check_min_probability"], "comment.check_min_probability", 0, 1',
        'comment["check_min_probability"] - 0.05, "comment.check_min_probability", 0, 1',
    ),
    "live-check-applied-reads-jev-models": (
        "tests.test_live_check_applied",
        "tests.test_live_check_applied",
        '"classifier.off_topic_reasons", "margin", "pass_correct")',
        '"classifier.off_topic_reasons", "margin", "pass_correct", "jev_models")',
    ),
    "live-check-applied-recount-ignored": (
        "tests.test_live_check_applied",
        "tests.test_live_check_applied",
        "return drift + [key for key in RECOUNTED if cell(current, key) != recounted.get(key)]",
        "return drift",
    ),
    "live-check-applied-exception-any-run": (
        "tests.test_live_check_applied",
        "tests.test_live_check_applied",
        "(run_at == BEFORE_FIX_RUN_AT and line == BEFORE_FIX_LINE)",
        "(line == BEFORE_FIX_LINE)",
    ),
    "live-check-applied-stored-verdicts-unchecked": (
        "tests.test_live_check_applied",
        "tests.test_live_check_applied",
        "return mismatches",
        "return []",
    ),
    "live-check-applied-unknown-question-ignored": (
        "tests.test_live_check_applied",
        "tests.test_live_check_applied",
        "if unknown or not scores:",
        "if not scores:",
    ),
    "live-check-applied-recheck-no-tolerance": (
        "tests.test_live_check_applied",
        "tests.test_live_check_applied",
        "return lowest_score(scores) + _TOLERANCE >= threshold",
        "return lowest_score(scores) >= threshold",
    ),
    "live-check-skip-grade-every-skip": (
        "tests.live_check",
        "tests.test_live_check",
        'if video["skip_kind"] in SELF_SKIP_KINDS:',
        'if video["result"] == "skip":',
    ),
}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in MUTANTS:
        names = " | ".join(MUTANTS)
        print(f"사용법: python3 -m tests.mutants <{names}>", file=sys.stderr)
        return 2
    name = argv[0]
    module_name, test_module, old, new = MUTANTS[name]

    root = _SRC if module_name.split(".")[0] == "agent" else _ROOT
    path = root.joinpath(*module_name.split(".")).with_suffix(".py")
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        print(f"anchor not found exactly once: {name}: {old}", file=sys.stderr)
        return 2
    mutated = source.replace(old, new)

    module = types.ModuleType(module_name)
    module.__file__ = str(path)
    sys.modules[module_name] = module
    package_name, _, attribute = module_name.rpartition(".")
    setattr(sys.modules[package_name], attribute, module)
    exec(compile(mutated, str(path), "exec"), module.__dict__)

    print(f"mutant {name}: {old} -> {new}", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromName(test_module)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
