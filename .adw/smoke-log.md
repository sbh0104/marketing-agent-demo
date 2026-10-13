# Smoke log

_The bucket for fixes that need no judgment. Made by
`plans/interview-cycle-friction.md#phase-f8`; emptied by the short route
(`.adw/workflow-smoke.yml`, Phase F9). Nothing else empties it._

## Rules — read this block before writing an entry

- rules version: F9 2026-09-05 · S2 2026-09-21 · T9 2026-09-22 · F8′ 2026-09-26 · F26-D 2026-10-04 — everything **above** `## Entries` is the template's:
  `install.sh --force` refreshes this block on every install, so the rules can never drift
  behind the skills that point at them. Everything **below** `## Entries` is the project's
  and no installer ever touches it. One file, two owners, and the line between them is that
  heading.
- **Append only.** A new item is one `### S-###` section added at the **end of this file**.
  Nothing above the last section is ever rewritten, except an existing item's own
  `- status:` and `- attempts:` lines, and a header the numbering hand settles (next rule).
- **Ids are `S-###`, three digits, monotonic, never reused.** The next id is one greater
  than the highest `S-###` that has ever appeared below `## Entries`, closed items included.
  The shape below is `S-000`, so the first real item is `S-001`.
  **Numbers are issued under the registry lock, from the home tree** — several lanes write
  this file at once (S4), so a lane's own copy never decides a number. A step inside a cycle
  (ship-check) writes a placeholder header `### S-NEW-<n>`, n one above the
  highest `S-NEW-` already here; the hand that carries the lane's copy home (`lane.py`, at
  the red verdict's immediate send, at landing, and `smoke-file` inside its own lock hold)
  gives **each placeholder header** the home tree's highest plus one and writes the number
  back into the lane's copy, so a second send appends nothing. A number that turns out to be
  taken by a different item (a different `- source:` line — in the home tree or twice in one
  copy) is never dropped: the newcomer is renumbered, and the step's result line opens with
  a `⚠` line saying so.
- **The entry criterion is judgment, not size.** An item belongs here only if its fix
  touches **none** of: a tracker decision · a public contract (verdict token · gate
  protocol · file format · CLI argument) · a sensitive area · a rule file
  (`constitution.md` · `CLAUDE.md` · `workflow*.yml` · `.claude/skills/**` ·
  `.claude/agents/**`). A mechanical 200-line rename belongs here; a one-line change to a
  gate protocol does not. **This list is defined here and nowhere else** — the skills that
  write into this file point at this block instead of restating it, because a second copy
  is a copy that drifts.
- **`- touches:` is the criterion's evidence, and it is what makes the criterion
  falsifiable.** It names every path the fix changes, so any later reader — the sweep, the
  next ship-check, a human — can re-run the criterion against the real diff instead of
  taking the writer's word for it. An item whose `- touches:` names a rule file or a
  sensitive area was never eligible: it is a finding to route, not a fix to sweep.
- **Status is one of `open` · `in-sweep` · `resolved` · `reverted` · `escalated`.** It is
  the **first token** after `- status: `; anything after a `→` is provenance, not status.
  `escalated` is an item that broke twice: it is
  **excluded from every blocking calculation** and leaves through `smoke-triage` as a
  phase-sized backlog item, so one stubborn item can never hold the whole roadmap.
  `resolved` is excluded too.
- **The blocking calculation is the driver's, not this file's.** `smoke_block` in
  `cycle_driver.py` reads the statuses written here. With lanes off, `open` and `reverted`
  **block** — the short route runs ahead of every tracker phase until the bucket clears. With
  lanes on (the default since S4) the bucket blocks nothing: a sweep runs in its own lane,
  started by the hub automatically only when `lane.max` is 2 or more, otherwise from the hub's
  🧪 button. `escalated` and `resolved` never count. This file says what a status *means*; the
  driver says what it *costs*. Nothing else gates work on these statuses.
- **`in-sweep` is written by no automated hand.** The short route leaves a swept item `open`
  until `smoke-close` gives it a final status, so a round that dies mid-sweep re-blocks on the
  next pick instead of leaking its items past the block. The status is here for a human
  marking a sweep they are running by hand; after an automated round it is a sign that
  something wrote what it shouldn't have.
- **`- attempts:` is incremented by `smoke-close` and by the short route's red end, nothing
  else.** It counts breaks, not tries: `smoke-close` raises it when it reverts the item's own
  commit, and the driver raises it when a sweep ends red with the item's commits kept on its
  sweep branch (ship `BLOCKED`, F8′). Each writes the reason on the same line
  (`last failure:`), and the next sweep reads it before writing its checks.
  **Two breaks and the item becomes `escalated`** — it leaves the
  blocking calculation and goes to a human, because an item that broke twice was never the
  small thing it claimed to be.
- **A sweep files side findings one generation deep (F8′).** An item a sweep's own
  ship-check filed carries a `- source:` line starting `sweep <cycle id>` — the driver stamps
  it right after that step. A sweep whose batch holds such an item files nothing more; its
  findings stay in its report. So a sweep can add one more sweep, never a chain of them.
- **One item never lives in two files.** An item that came from the debt ledger carries a
  `- cross-ref: S-### ← D-###` line here, and its ledger entry carries
  `- status: routed → S-###` there. While the item is here, **this file owns its status**
  and the ledger keeps only the pointer.
- **A red cycle files here instead of rewinding (S2, 2026-09-21).** `smoke-file` turns a
  verify-run `FAIL` or a ship-check `BLOCKED` into items carrying `- base: <that phase
  branch>` and `- phase: <tracker ref>`. The sweep starts its branch from `base:` (not from
  main), and when it ships, the phase ships with it and the `phase:` backlog line closes.
  Items without `base:` sweep from main as before. A batch never mixes bases.
- **A red verdict the bucket cannot carry is held, not filed (F26-D, 2026-10-04).** A BLOCKED
  or FAIL whose touches are unknown, or that the ship-report's `## Smoke candidates` section did
  not offer as a candidate (the section is there and lists none), is never written here:
  `smoke-file` names it in `.adw/smoke-filed.json` `held` with a `why` (`unknown-touches` ·
  `report-declined` · `rule-path` for a rule file) and the red end goes to a 🎤 interview.
- **A stale `- direction:` is revised, never erased (F14).** When the prescription turned out
  wrong (a later phase changed the shape of the fix), strike the old sentence and append the
  new one on the same line: `- direction: ~~old~~ (revised YYYY-MM-DD: new)`. The history
  stays readable and the sweep reads the last clause.

Entry shape — copy every line, in this order:

```text
### S-000 — <one-line title>
- source: cycle <cycle id> · tracker <tracker path>#phase-<n> · deferred by <step>
- evidence: <file:line>
- direction: <the shape of the fix, one line>
- touches: <every path the fix changes, comma-separated>
- base: <phase branch the fix must start from — omit for main>
- phase: <tracker path>#phase-<n> — the backlog line that closes when this ships; omit if none
- status: open
- attempts: 0 · last failure: —
- first seen: YYYY-MM-DD · last seen: YYYY-MM-DD
- cross-ref: S-000 ← D-000
```

The `- cross-ref:` line is written **only** when the item came from `.adw/debt.md`; every
other line is required on every item.

## Entries

<!-- New items are appended below, one `### S-###` section each, newest last. The bucket
     ships empty on purpose: the short route's invariant is "empty bucket → next phase". -->

### S-001 — 설정 숫자 하한 규칙(음수 대기·max_age_hours 0·음수 상한)을 테스트로 고정
- source: cycle 20261013-062542-adw/phase-1-foundation-contracts · tracker plans/interview-marketing-agent.md#phase-1 · deferred by ship-check
- evidence: src/agent/config.py:143, src/agent/config.py:171, src/agent/config.py:180 — 각 하한을 없애는 변이가 스위트에서 초록(.adw/ship-report.md § Test integrity)
- direction: tests/test_config.py 의 ConfigFromMappingTest 에 channel_cooldown_hours -1·.nan, max_age_hours 0, daily_max_comments -1 이 각각 ConfigError 인지 보는 행을 더한다 — 코드 변경 없음
- touches: tests/test_config.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-002 — 로그 값 속 줄바꿈 이스케이프를 공백 없는 값으로 테스트에 고정
- source: cycle 20261013-062542-adw/phase-1-foundation-contracts · tracker plans/interview-marketing-agent.md#phase-1 · deferred by ship-check
- evidence: src/agent/logbook.py:51 — `[^\s"=\\]+` 를 `[^ \t"=\\]+` 로 바꾼 변이가 스위트에서 초록(.adw/ship-report.md § Test integrity)
- direction: tests/test_logbook.py 의 test_rendering_rules 에 "x\ny"·"x\ry" 같은 공백·따옴표 없는 값을 더해 이스케이프된 따옴표 값으로 쓰이고 parse_line 으로 되돌아오는지 본다 — 코드 변경 없음
- touches: tests/test_logbook.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-003 — 가드 거부 표에 두 번째 `;` 뒤에 숨은 `v` 행을 더해 쿼리 나누기를 테스트에 고정
- source: cycle 20261013-062542-adw/phase-1-foundation-contracts · tracker plans/interview-marketing-agent.md#phase-1 · deferred by ship-check
- evidence: src/agent/guard.py:60 — `parts.query.replace(";", "&")` 를 `replace(";", "&", 1)`(첫 `;` 만 나눔)로 바꾼 변이가 스위트에서 초록(141개 OK). 이때 `https://youtu.be/AAAAAAAAAAA?x=1;y=2;v=BBBBBBBBBBB` 가 A 로 읽힘. tests/test_guard.py:43-46, 72 의 `;` 행은 모두 `;` 가 하나뿐(.adw/ship-report.md § Test integrity)
- direction: tests/test_guard.py 의 REJECTED_REFS `;` 묶음에 `f"https://youtu.be/{REPRO_A}?x=1;y=2;v={REPRO_B}"` 와 `f"https://www.youtube.com/shorts/{REPRO_A}?a=1;b=2;v={REPRO_B}"` 행을 더한다 — 코드 변경 없음, 지금 코드는 둘 다 None
- touches: tests/test_guard.py
- base: adw/phase-1-foundation-contracts
- phase: plans/interview-marketing-agent.md#phase-1
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-004 — 가드 ID 표에 12자 맨 ID 와 닮은 호스트 행을 더해 11자 규칙과 호스트 목록을 테스트에 고정
- source: cycle 20261013-062542-adw/phase-1-foundation-contracts · tracker plans/interview-marketing-agent.md#phase-1 · deferred by ship-check
- evidence: src/agent/guard.py:49, src/agent/guard.py:19 — `VIDEO_ID_RE.fullmatch(text)` → `.match(text)` 변이와 `_YOUTUBE_HOSTS` 에 `youtube-nocookie.com` 을 더한 변이가 스위트에서 초록(141개 OK). 앞 변이에서는 `decide_post("AAAAAAAAAAA&v=BBBBBBBBBBB", ["AAAAAAAAAAA&v=BBBBBBBBBBB"], False)` 가 live=True(.adw/ship-report.md § Test integrity)
- direction: tests/test_guard.py 의 VideoIdFromRefTest 표(158-177행)에 `"AAAAAAAAAAAB"` · `"AAAAAAAAAAA&v=BBBBBBBBBBB"` → None, test_g7 곁에 `https://youtube-nocookie.com/watch?v=AAAAAAAAAAA` → None 행을 더한다 — 코드 변경 없음, 지금 코드는 셋 다 None(ship-check 에서 확인)
- touches: tests/test_guard.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-005 — 저장소 테스트에 23.5시간 전 게시와 24시간이 아닌 채널 대기를 더해 하루 창과 대기 계산을 고정
- source: cycle 20261013-062542-adw/phase-1-foundation-contracts · tracker plans/interview-marketing-agent.md#phase-1 · deferred by ship-check
- evidence: src/agent/store.py:170, src/agent/store.py:174 — 하루 창 `timedelta(hours=24)` → `hours=23` 변이와 채널 대기 `hours=limits.channel_cooldown_hours` → `hours=24` 변이가 둘 다 초록(141개 OK). 저장소 테스트는 모두 `LimitsConfig(10, 24.0, 100)`(tests/test_store.py:15)을 쓰고, 하루 창은 정확히 24시간 경계 하나만 본다(tests/test_store.py:121)
- direction: tests/test_store.py 에 ① 하루 상한 10, 다른 채널 9건을 1시간 전 · 1건을 23.5시간 전에 게시한 뒤 새 채널 → `daily_cap` ② 채널 대기 48시간, 같은 채널 30시간 전 게시 → `channel_cooldown` ③ 채널 대기 1시간, 같은 채널 2시간 전 게시 → `ok` 행을 더한다 — 코드 변경 없음
- touches: tests/test_store.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-006 — 설정 테스트에 하한 경계값 · 숫자 키의 bool · 빠진 하한 넷을 더해 계약 2절 표를 고정
- source: cycle 20261013-062542-adw/phase-1-foundation-contracts · tracker plans/interview-marketing-agent.md#phase-1 · deferred by ship-check
- evidence: src/agent/config.py:139-160, src/agent/config.py:179-201 — 하한 비교를 `>=`→`>` · `<`→`<=` 로 바꾼 변이, `_number` 의 bool 검사를 뺀 변이, `min_views_per_hour` · `min_views` · `daily_max_searches` · `comment.min_chars` 의 하한을 넓힌 변이 7개가 모두 초록(.adw/ship-report.md § Test integrity)
- direction: tests/test_config.py 에 ① 하한값 그대로 읽힘: `limits.channel_cooldown_hours: 0` · `trigger.min_views_per_hour: 0` · `limits.daily_max_comments: 0` · `poll_interval_min: 1` · `trigger.max_views` = `min_views` ② 숫자 키의 bool 거부: `trigger.max_age_hours: true` · `limits.channel_cooldown_hours: false` → `숫자여야 합니다` ③ 하한 넷: `trigger.min_views_per_hour: -1` · `trigger.min_views: -1` · `limits.daily_max_searches: -1` → `0 이상이어야 합니다`, `comment.min_chars: 0` → `1 이상이어야 합니다` 행을 더한다 — 코드 변경 없음, 지금 코드는 모두 이렇게 동작(ship-check 에서 확인)
- touches: tests/test_config.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-007 — parse_line 거부 표에 따옴표 값 뒤에 붙은 글자와 끝의 빈 줄 행을 더함
- source: cycle 20261013-062542-adw/phase-1-foundation-contracts · tracker plans/interview-marketing-agent.md#phase-1 · deferred by ship-check
- evidence: src/agent/logbook.py:143, src/agent/logbook.py:109 — `if rest[end] != " ":` → `if False:` 변이와 줄 끝 `\n` 하나 대신 모두 떼는 변이가 초록. 앞 변이에서 `parse_line('2026-10-12T21:30:00+09:00 STOP reason="a"_extra=y')` 가 `_` 를 버리고 `{'reason': 'a', 'extra': 'y'}` 를 돌려줌(.adw/ship-report.md § Test integrity)
- direction: tests/test_logbook.py 의 test_malformed_lines 나쁜 줄 목록(157-172행)에 `2026-10-12T21:30:00+09:00 STOP reason="a"_x=y` 와 정상 STOP 줄 + `"\n\n"` 을 더한다 — 코드 변경 없음, 지금 코드는 둘 다 ValueError(ship-check 에서 확인)
- touches: tests/test_logbook.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13
