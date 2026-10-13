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
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-008 — 트리거 판정에서 나이 창 검사가 줄어든 조회수 · 속도 검사보다 먼저인 차례를 테스트로 고정
- source: cycle 20261013-161358-adw/phase-4-trigger-timing · tracker plans/interview-marketing-agent.md#phase-4 · deferred by ship-check
- evidence: src/agent/trigger.py:56-62 — `too_old` 검사를 `views_decreased` 검사 뒤로 옮긴 변이와 `too_slow` 검사 뒤로 옮긴 변이가 둘 다 스위트에서 초록(`Ran 35 tests` · `OK`). 지금 코드는 20시간 된 1450→1300 영상을 `no too_old` 로 판정하지만 앞 변이는 `hold views_decreased` 로 영원히 미룸(.adw/ship-report.md § Test integrity)
- direction: tests/test_trigger.py 의 NoTests 에 ① `video((19*H+30*M, 1450), (20*H, 1300))` 를 `20*H` 에 → `("no", "too_old")` ② `video((19*H+30*M, 1200), (20*H, 1274))` 를 `20*H` 에 → `("no", "too_old")` 행을 더한다 — 코드 변경 없음, 지금 코드는 둘 다 too_old(ship-check 에서 확인)
- touches: tests/test_trigger.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-009 — 계약 11절이 약속하지만 테스트가 잡지 않는 네 가지(at=now · 기록 안 바꿈 · 직전 시각의 큰 조회수 · 소수 기준값)를 테스트로 고정
- source: cycle 20261013-161358-adw/phase-4-trigger-timing · tracker plans/interview-marketing-agent.md#phase-4 · deferred by ship-check
- evidence: src/agent/trigger.py:23-63 — 일곱 갈래의 `Judgement(..., now)` 를 `latest.at` 으로 바꾼 변이 7개, `history.sort(...)` 로 받은 목록을 제자리 정렬하는 변이, 직전 시각에서 작은 조회수를 고르는 변이, `_rate` 의 `/` → `//` 변이가 모두 스위트에서 초록. tests/test_trigger.py:229 는 최신 기록 시각에 판정해 `at=now` 와 `at=latest.at` 을 가르지 못하고, :240 은 이미 정렬된 기록을 씀(.adw/ship-report.md § Test integrity)
- direction: tests/test_trigger.py 에 ① test_every_reason_logs_unquoted 의 여덟 장면마다 `j.at == now` 를 확인하고, 판정 시각이 최신 기록보다 늦은 장면(`video(*GOOD)` 을 `3*H` 에 → yes)을 하나 더함 ② test_record_is_not_changed 에 순서가 뒤섞인 기록을 씀 ③ `video((2*H, 1200), (2*H, 1300), (2*H+30*M, 1450))` 이 `min_views_per_hour=300.0` 에서 yes · `301.0` 에서 `too_slow` ④ `video((1*H, 1000), (11*H, 2505))` 를 `11*H` 에(시간당 150.5) `150.5` 에서 yes · `150.6` 에서 `too_slow` 행을 더한다 — 코드 변경 없음, 지금 코드는 넷 다 이렇게 동작(ship-check 에서 확인)
- touches: tests/test_trigger.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-010 — 트리거 판정이 같은 시간대 객체의 일광 절약 시각을 벽시계로 비교하는 것을 UTC 비교로 고침
- source: cycle 20261013-161358-adw/phase-4-trigger-timing · tracker plans/interview-marketing-agent.md#phase-4 · deferred by ship-check
- evidence: src/agent/trigger.py:23, :27, :39, :54, :56 — 파이썬은 tzinfo 가 같은 두 시각을 벽시계로 비교 · 뺄셈함. `ZoneInfo("America/New_York")` 의 2026-11-01 01:30 fold 0 · fold 1(실제 1시간 차) 두 기록이 `hold too_few_samples`, 같은 두 순간을 UTC 로 주면 `yes views_per_hour`(ship-check 에서 재현). 계약 11절 "같은 순간이면 같은 시각" · "목록 순서는 보지 않고" 와 어긋남
- direction: `_latest_pair` · `_rate` · 미래 업로드 검사 · 나이 검사가 `.astimezone(timezone.utc)` 로 바꾼 순간끼리 비교 · 뺄셈하게 한다(`Judgement.at` 은 받은 `now` 그대로). tests/mutants.py 의 `trigger-*` 고정 문자열이 trigger.py 에 한 번씩 남는지 확인하고 바뀐 줄이면 고정 문자열도 맞춘다. 테스트는 zoneinfo 대신 손으로 쓴 일광 절약 tzinfo 로(Windows 에 tzdata 가 없어도 돌게) 가을 겹침(fold) · 봄 당김 두 행을 더한다
- touches: src/agent/trigger.py, tests/test_trigger.py, tests/mutants.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-1 — sdk_ask 의 좁은 catch 를 테스트로 고정 — try 안에서 난 TypeError 가 그대로 올라가는지
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: src/agent/classifier.py:198 — `except typesafe_sdk.TypeSafeError as exc:` → `except Exception as exc:` 변이가 tests.test_classifier 39개 모두 초록. test_non_sdk_error_inside_sdk_ask_propagates(tests/test_classifier.py:524)는 try 바깥의 `Noul(...)`(classifier.py:184)에서 오류를 내 이 자리에 닿지 않음(.adw/ship-report.md § Test integrity, R1)
- direction: tests/test_classifier.py SdkAskTest 에 가짜 TypeSafeClient.system_one 이 TypeError 를 내면 classify(…, sdk_ask, …) 가 같은 TypeError 를 올리는지(보류가 아님) 보는 테스트를 더한다 — 코드 변경 없음, 지금 코드는 이렇게 동작
- touches: tests/test_classifier.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-2 — 설정의 classifier.model 이 ask · system_one 까지 가는지 테스트로 고정
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: src/agent/classifier.py:160, src/agent/classifier.py:197 — `ask(config.classifier.model, …)` → `ask("jev-latest", …)` 와 `system_one(model=model, …)` → `system_one(model="jev-latest", …)` 변이가 초록. tests/test_classifier.py:199, :493 이 고정 설정의 유일한 값 `"jev-latest"` 만 확인(.adw/ship-report.md § Test integrity, R2)
- direction: tests/test_classifier.py 에 classifier.model 을 `jev-test-x` 로 바꾼 설정으로 classify 를 불러 FakeJev 의 model 인자와 가짜 system_one 의 `model=` 이 `jev-test-x` 인지 보는 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_classifier.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-3 — 정확도 러너의 경계(오류가 일부만 · 정확히 20/22)를 테스트로 고정
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: tests/jev_accuracy.py:28, tests/jev_accuracy.py:81-82, tests/jev_accuracy.py:108 — `any(t.error > 0 …)` → `all(…)` · ko 만 보기, `t.correct >= PASS_CORRECT` → `>`, `PASS_CORRECT = 21` 변이가 모두 초록. test_runner_error_holds_exit_3(tests/test_classifier.py:672)는 22개 × 두 언어 모두 오류인 경우만 돌림(.adw/ship-report.md § Test integrity, R3)
- direction: tests/test_classifier.py ExamplesTest 에 ① en 의 예시 하나만 JevError 를 내는 가짜로 main 이 3 과 `측정 실패` 줄을 내는지 ② 잘못된 일치 0 · 정확히 20/22(YES 라벨 둘을 NO 로 답하는 가짜)로 main 이 0 과 `권고: ko 그대로` 를 내는지 보는 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_classifier.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-4 — 가짜 SDK 의 응답 검증 오류를 진짜 typesafe-sdk 0.7.4 계보로 맞추기
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: tests/test_classifier.py:147 `class TypeSafeAPIResponseValidationError(TypeSafeError)` — 진짜 0.7.4 휠 `_core/errors.py:176` 은 `class TypeSafeAPIResponseValidationError(TypeSafeAPIError)` 라 `.status` 가 있어 실제 이유는 `API 오류: TypeSafeAPIResponseValidationError 200` 꼴. docs/research/jev.md 오류 항목에 이 계보가 없음(.adw/ship-report.md § Risks R4)
- direction: 가짜 TypeSafeAPIResponseValidationError 를 TypeSafeAPIError 의 자식(.status 있음)으로 바꾸고 그 행의 기대 이유에 상태 코드를 넣으며, docs/research/jev.md 'SDK 확인' 절 오류 항목에 "응답 검증 오류도 TypeSafeAPIError 의 자식이라 .status 를 가진다" 한 줄을 더한다 — 코드 변경 없음, 계약의 `[<상태 코드>]` 모양 안
- touches: tests/test_classifier.py, docs/research/jev.md
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-5 — 계약 문서 머리 문단 · 10절 머리 문장에 판별 모듈 반영
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: docs/contracts.md:5-6 — `src/agent/` 목록에 `classifier.py` 없음; docs/contracts.md:430 — 음성 대조 대상 "가드 · 저장소 · 설정 읽기 · 로그 한 줄 규칙"에 판별 없음(verify-plan § Out of scope 의 RISK 메모, .adw/ship-report.md § Risks R5)
- direction: 머리 문단 `src/agent/` 목록에 `classifier.py` 를, 10절 머리 문장 대상 목록에 `판별` 을 더한다 — 계약 내용(키 · 판정 토큰 · 형식 · CLI 인자) 변경 없음
- touches: docs/contracts.md
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13
