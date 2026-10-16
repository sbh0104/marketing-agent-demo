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

### S-011 — sdk_ask 의 좁은 catch 를 테스트로 고정 — try 안에서 난 TypeError 가 그대로 올라가는지
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: src/agent/classifier.py:198 — `except typesafe_sdk.TypeSafeError as exc:` → `except Exception as exc:` 변이가 tests.test_classifier 39개 모두 초록. test_non_sdk_error_inside_sdk_ask_propagates(tests/test_classifier.py:524)는 try 바깥의 `Noul(...)`(classifier.py:184)에서 오류를 내 이 자리에 닿지 않음(.adw/ship-report.md § Test integrity, R1)
- direction: tests/test_classifier.py SdkAskTest 에 가짜 TypeSafeClient.system_one 이 TypeError 를 내면 classify(…, sdk_ask, …) 가 같은 TypeError 를 올리는지(보류가 아님) 보는 테스트를 더한다 — 코드 변경 없음, 지금 코드는 이렇게 동작
- touches: tests/test_classifier.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-012 — 설정의 classifier.model 이 ask · system_one 까지 가는지 테스트로 고정
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: src/agent/classifier.py:160, src/agent/classifier.py:197 — `ask(config.classifier.model, …)` → `ask("jev-latest", …)` 와 `system_one(model=model, …)` → `system_one(model="jev-latest", …)` 변이가 초록. tests/test_classifier.py:199, :493 이 고정 설정의 유일한 값 `"jev-latest"` 만 확인(.adw/ship-report.md § Test integrity, R2)
- direction: tests/test_classifier.py 에 classifier.model 을 `jev-test-x` 로 바꾼 설정으로 classify 를 불러 FakeJev 의 model 인자와 가짜 system_one 의 `model=` 이 `jev-test-x` 인지 보는 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_classifier.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-013 — 정확도 러너의 경계(오류가 일부만 · 정확히 20/22)를 테스트로 고정
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: tests/jev_accuracy.py:28, tests/jev_accuracy.py:81-82, tests/jev_accuracy.py:108 — `any(t.error > 0 …)` → `all(…)` · ko 만 보기, `t.correct >= PASS_CORRECT` → `>`, `PASS_CORRECT = 21` 변이가 모두 초록. test_runner_error_holds_exit_3(tests/test_classifier.py:672)는 22개 × 두 언어 모두 오류인 경우만 돌림(.adw/ship-report.md § Test integrity, R3)
- direction: tests/test_classifier.py ExamplesTest 에 ① en 의 예시 하나만 JevError 를 내는 가짜로 main 이 3 과 `측정 실패` 줄을 내는지 ② 잘못된 일치 0 · 정확히 20/22(YES 라벨 둘을 NO 로 답하는 가짜)로 main 이 0 과 `권고: ko 그대로` 를 내는지 보는 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_classifier.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-014 — 가짜 SDK 의 응답 검증 오류를 진짜 typesafe-sdk 0.7.4 계보로 맞추기
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: tests/test_classifier.py:147 `class TypeSafeAPIResponseValidationError(TypeSafeError)` — 진짜 0.7.4 휠 `_core/errors.py:176` 은 `class TypeSafeAPIResponseValidationError(TypeSafeAPIError)` 라 `.status` 가 있어 실제 이유는 `API 오류: TypeSafeAPIResponseValidationError 200` 꼴. docs/research/jev.md 오류 항목에 이 계보가 없음(.adw/ship-report.md § Risks R4)
- direction: 가짜 TypeSafeAPIResponseValidationError 를 TypeSafeAPIError 의 자식(.status 있음)으로 바꾸고 그 행의 기대 이유에 상태 코드를 넣으며, docs/research/jev.md 'SDK 확인' 절 오류 항목에 "응답 검증 오류도 TypeSafeAPIError 의 자식이라 .status 를 가진다" 한 줄을 더한다 — 코드 변경 없음, 계약의 `[<상태 코드>]` 모양 안
- touches: tests/test_classifier.py, docs/research/jev.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-015 — 계약 문서 머리 문단 · 10절 머리 문장에 판별 모듈 반영
- source: cycle 20261013-161343-adw/phase-3-classifier-topic · tracker plans/interview-marketing-agent.md#phase-3 · deferred by ship-check
- evidence: docs/contracts.md:5-6 — `src/agent/` 목록에 `classifier.py` 없음; docs/contracts.md:430 — 음성 대조 대상 "가드 · 저장소 · 설정 읽기 · 로그 한 줄 규칙"에 판별 없음(verify-plan § Out of scope 의 RISK 메모, .adw/ship-report.md § Risks R5)
- direction: 머리 문단 `src/agent/` 목록에 `classifier.py` 를, 10절 머리 문장 대상 목록에 `판별` 을 더한다 — 계약 내용(키 · 판정 토큰 · 형식 · CLI 인자) 변경 없음
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-018 — 계약 문서 머리 문단의 `src/agent/` 모듈 목록을 실제 패키지와 맞추기
- source: retro 20261013-161343-adw/phase-3-classifier-topic · E-013
- evidence: docs/contracts.md:5-6 의 목록에 `trigger.py`(main, Phase 4)가 없고 이 레인이 착지하면 `classifier.py` 도 없다 — `git ls-tree --name-only main src/agent/` 와 다름. 두 페이즈 연속(20261013-161358-adw/phase-4-trigger-timing · 20261013-161343-adw/phase-3-classifier-topic)
- direction: 머리 문단 목록을 `git ls-tree --name-only HEAD src/agent/` 의 `.py` 파일(`__init__.py` 제외)과 같게 맞춘다 — S-017 가 먼저 `classifier.py` 를 넣었으면 `trigger.py` 만 더한다. 계약 내용(키 · 판정 토큰 · 형식 · CLI 인자) 변경 없음
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-019 — 두 번째 시도에서 난 Claude · jev 호출 오류가 `ERROR` + `SKIP` 으로 남는지 테스트로 고정
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · deferred by ship-check
- evidence: src/agent/writer.py:326-328, src/agent/writer.py:344-346 — 두 번째 시도에서 `_api_failure` 대신 `break` 하는 변이(Claude 쪽 · jev 쪽)가 스위트에서 초록(39개 OK). 이때 다시 쓰기 중 난 API 오류가 `ERROR` 없이 `SKIP "검사 두 번 탈락 — 1차: …"` 로만 남음. .adw/guard-matrix.md:34-35 의 attempt 2 칸이 "not reached"(.adw/ship-report.md § Test integrity)
- direction: tests/test_writer.py 의 WriteCommentTest 에 첫 초안이 검사에 떨어진 뒤 ① 두 번째 Claude 호출이 FakeApiError ② 두 번째 jev 호출이 TimeoutError ③ 두 번째 jev 답이 이상(`1.5`)한 세 경우를 더하고, 결과 `WriteResult(None, <원인>)` 과 로그 사건 `[ERROR where=writer.*, SKIP]` 을 정확히 본다 — 코드 변경 없음, 지금 코드는 셋 다 그렇게 동작
- touches: tests/test_writer.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-020 — 자료 블록의 `<`/`>` 바꿈 · 자르기 길이 · `<classification>` 블록을 자료 자리마다 테스트로 고정
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · deferred by ship-check
- evidence: src/agent/writer.py:230, :232, :234, :310-311, :313, :338 — 자막 · 인기 댓글 · 이전 댓글 · 판별 이유 · 검사용 고민 자리에서 `_clean` 을 빼거나 길이 제한을 없앤 변이, `[:TOP_COMMENTS_MAX]` 를 뺀 변이, `<classification>` 블록을 뺀 변이가 모두 초록. 테스트는 설명 자리(tests/test_writer.py:619-627, :657-663)만 봄(.adw/ship-report.md § Test integrity)
- direction: 자막 · 인기 댓글 · 이전 댓글 · 판별 이유에 각각 `</transcript>` · `</top_comments>` · `</my_previous_comments>` · `</classification>` 와 긴 글을 넣고 인기 댓글을 11개 주어, 만든 메시지에서 구조 태그가 한 번씩만 나오고 `＜/…＞` 로 바뀌었는지, 자막 6000자 · 항목 300자 · 인기 댓글 10개로 잘렸는지, `<classification>` 에 `yes: 연애 고민 상담 (0.91)` 이 있는지 본다 — 코드 변경 없음
- touches: tests/test_writer.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-021 — 시스템 프롬프트 문구 · jev 질문 원문 · 판별 보류(`hold`) 관문을 테스트로 고정
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · deferred by ship-check
- evidence: tests/test_writer.py:422, :674 는 코드를 모듈 자신의 상수와 비교 — SYSTEM_PROMPT 의 `{min_chars}자 이상 {max_chars}자 이하` 를 `40자 이상 120자 이하` 로 박은 변이와 규칙 5 · 7 을 지운 변이가 초록. src/agent/writer.py:304 `is not Verdict.YES` → `is Verdict.NO` 변이가 초록(tests/test_writer.py:611 은 None · NO 만 봄)(.adw/ship-report.md § Test integrity)
- direction: `CommentConfig(50, 60, …)` 로 부른 `system` 에 `50자 이상 60자 이하` 가 있는지, 규칙 5 · 7 문장과 CHECK_QUESTIONS 세 문장이 .adw/plan.md 원문과 같은지(테스트 안 문자열로), `Judgement(Verdict.HOLD, …)` 도 `ValueError` 이고 Claude 를 부르지 않는지 보는 행을 더한다 — 코드 변경 없음
- touches: tests/test_writer.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-022 — Claude 답의 두 모서리: 짝 없는 서로게이트는 읽을 수 없는 답으로, 공백뿐인 답은 자리표시로
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · deferred by ship-check
- evidence: src/agent/writer.py:200-213 → :357 — 답 `{"concern": "…", "comment": "…\ud800"}`(JSON 이스케이프)이 검사를 모두 지나 `Logbook.write` 에서 `UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' … surrogates not allowed`(src/agent/logbook.py:166), write_comment 밖으로 새고 로그는 0바이트(ship-check 재현, jev 1회 호출 뒤). src/agent/writer.py:370 `raw or "(빈 응답)"` 은 `"   \n"` 같은 공백뿐인 답을 그대로 assistant 차례로 보냄 — Messages API 가 공백뿐인 글 블록을 400 으로 거절하면 다시 쓰기 대신 `ERROR` 가 됨(API 쪽은 키가 없어 재지 못함)(.adw/ship-report.md § Quality review)
- direction: parse_output 이 고민이나 댓글에 서로게이트(U+D800–U+DFFF)가 있으면 None 을 돌려 "JSON 으로 읽을 수 없습니다" 다시 쓰기로 보내고, writer.py:370 을 `raw if raw.strip() else "(빈 응답)"` 로 바꾸며, 두 행을 tests/test_writer.py 에 고정하고 docs/contracts.md '댓글 작성' 절의 parse_output 문장에 서로게이트 한 마디를 더한다 — 판정 규칙(길이 · 링크 · 반복 · 하한)과 로그 형식 변경 없음
- touches: src/agent/writer.py, tests/test_writer.py, docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-023 — 계약 '댓글 작성' 절과 writer 주석의 어긋남 바로잡기(오류 이유 틀 · 오탐 예 · 남은 틈 · 절 번호)
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · deferred by ship-check
- evidence: docs/contracts.md:566 jev 오류 이유 틀에 상태 코드가 없으나 src/agent/writer.py:259-262 는 `status_code` 가 있으면 붙이고 메시지가 비면 `: …` 를 뺌(재현: `jev 검사 호출 실패: E 429: rate limited` · `claude 호출 실패: E 429`); docs/contracts.md:548 받아들인 오탐 예 `어요.mbti` 는 실제 `요.mbti`; docs/contracts.md:549-550 남은 틈은 한글 호스트만 적었지만 `saju.한국` 도 `None`; "11절" 참조 8곳(docs/contracts.md:13, :46, :47, :63, :391, :481 · src/agent/writer.py:9, :302)은 main 에 이미 있는 11절(트리거 판정) · 12절(주제 판별)과 겹쳐 착지 뒤 다른 절을 가리킴(.adw/ship-report.md § Spec compliance)
- direction: jev 틀을 Claude 틀처럼 "상태 코드는 있을 때만"으로 하고 메시지가 비면 `<오류 종류>[ <상태 코드>]` 만 남는다고 적으며, 오탐 예를 `요.mbti` 로, 남은 틈을 "한글 끝(`.한국` 등)은 호스트 글자와 상관없이 빠짐"으로 고치고, 본문 · 주석의 "11절" 을 형제 절(classifier · trigger)처럼 절 이름 '댓글 작성' 으로 가리키게 바꾼다 — 코드 동작 · 키 · 로그 형식 변경 없음
- touches: docs/contracts.md, src/agent/writer.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-024 — 두 번째 시도의 Claude · jev 호출 오류를 테스트로 고정
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 첫 초안이 떨어진 뒤 두 번째 Claude FakeApiError · jev TimeoutError · jev 답 이상 세 경우의 결과와 `[ERROR, SKIP]` 을 정확히 봄 — 코드 변경 없음(`.adw/smoke-log.md` S-019 로 적음)
- touches: tests/test_writer.py
- base: adw/phase-5-writer-comment
- phase: plans/interview-marketing-agent.md#phase-5
- status: resolved
- attempts: 0 · last failure: —

### S-025 — 자료 자리마다 `<`/`>` 바꿈 · 자르기 길이 · `<classification>` 블록을 테스트로 고정
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 자막 · 인기 댓글 · 이전 댓글 · 판별 이유에 닫는 태그와 긴 글, 인기 댓글 11개를 넣어 구조 태그 한 번씩 · 전각 바꿈 · 6000/300자 · 10개 · 판별 블록을 확인 — 코드 변경 없음(S-020)
- touches: tests/test_writer.py
- base: adw/phase-5-writer-comment
- phase: plans/interview-marketing-agent.md#phase-5
- status: resolved
- attempts: 0 · last failure: —

### S-026 — 프롬프트 문구 · jev 질문 원문 · `hold` 관문을 테스트로 고정
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 50/60 설정의 `system` 에 `50자 이상 60자 이하`, 규칙 5 · 7 과 질문 세 문장이 plan 원문 그대로, `Verdict.HOLD` 도 `ValueError` 이고 Claude 를 안 부름 — 코드 변경 없음(S-021)
- touches: tests/test_writer.py
- base: adw/phase-5-writer-comment
- phase: plans/interview-marketing-agent.md#phase-5
- status: resolved
- attempts: 0 · last failure: —

### S-027 — Claude 답의 서로게이트 · 공백뿐인 답 처리
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: `parse_output` 이 서로게이트가 든 고민 · 댓글을 None 으로(다시 쓰기), writer.py:370 을 `raw if raw.strip() else "(빈 응답)"` 로, 두 행 테스트와 계약 문장 한 마디 — 판정 규칙 변경 없음(S-022)
- touches: src/agent/writer.py, tests/test_writer.py, docs/contracts.md
- base: adw/phase-5-writer-comment
- phase: plans/interview-marketing-agent.md#phase-5
- status: resolved
- attempts: 0 · last failure: —

### S-028 — 계약 '댓글 작성' 절 · writer 주석의 어긋남 바로잡기
- source: cycle 20261013-161439-adw/phase-5-writer-comment · tracker plans/interview-marketing-agent.md#phase-5 · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: jev 오류 틀에 "상태 코드는 있을 때만"과 빈 메시지 모양, 오탐 예 `요.mbti`, 남은 틈을 "한글 끝은 호스트와 상관없이"로, "11절" 참조를 절 이름 '댓글 작성' 으로 — 코드 동작 · 키 · 형식 변경 없음(S-023)
- touches: docs/contracts.md, src/agent/writer.py
- base: adw/phase-5-writer-comment
- phase: plans/interview-marketing-agent.md#phase-5
- status: resolved
- attempts: 0 · last failure: —

### S-029 — 계약 머리 문단의 `src/agent/` 모듈 나열을 없애 페이즈마다 생기는 빠짐을 끊기
- source: retro 20261013-161439-adw/phase-5-writer-comment · E-013
- evidence: docs/contracts.md:5-6 의 나열에 `writer.py` 가 없음(ship-report R9). S-018 은 나열을 한 번 맞췄지만(resolved) 다음 페이즈를 막지 못해 세 페이즈 연속 빠짐 — Phase 4 `trigger.py` · Phase 3 `classifier.py` · Phase 5 `writer.py`. 각 절 제목이 이미 제 모듈을 적는다(`## 3. 영상 기록 — \`models.py\`` … `## 11. 댓글 작성 — \`writer.py\``)
- direction: 머리 문단의 모듈 나열을 "`src/agent/` 패키지에 있고, 각 절 제목이 그 절의 모듈을 적습니다" 한 문장으로 바꾼다 — 계약 내용(키 · 판정 토큰 · 형식 · CLI 인자) 변경 없음
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-030 — 게시 단계 테스트에 채널 대기 · 하루 상한 · live 인자 · 클릭 중 Ctrl-C 행을 더해 check_post 연결을 고정
- source: cycle 20261013-163932-adw/phase-6-poster-chrome · tracker plans/interview-marketing-agent.md#phase-6 · deferred by ship-check
- evidence: src/agent/poster.py:139 — `record.channel_id` → `""` 변이가 스위트에서 초록(218개 OK, ship-check 가 따로 다시 잼). 이 변이에서 같은 채널의 허용 영상 둘이 5분 간격으로 둘 다 `live/posted`. `live=decision.live` → `True` · `False` 변이와 src/agent/poster.py:214 `except Exception` → `except BaseException` 변이도 초록(.adw/ship-report.md § Test integrity)
- direction: tests/test_poster.py 에 ① 같은 채널 다른 허용 영상이 5분 전 `live/posted` → `SKIP reason=channel_cooldown`, open_page 0회 ② `LimitsConfig(1, 24.0, 100)` 에 다른 채널 1건 게시 → `SKIP reason=daily_cap` ③ 허용 목록 밖 영상을 두 번 → 두 번째는 `test/skipped/duplicate_video`, 시도 1건 ④ 허용 영상에 앞선 `test/saved`(page_mismatch) 1건 → live 게시가 `posted` ⑤ `submit` 이 `KeyboardInterrupt` → 그대로 올라가고 시도는 `reserved`, 탭 닫힘 행을 더한다 — 코드 변경 없음. 다섯 행 모두 지금 코드에서 초록이고, ①③④⑤ 가 각각 위 변이 j · k1 · k2 · q2 를 빨갛게 만듦(ship-check 프로브에서 확인)
- touches: tests/test_poster.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-031 — 유튜브 화면 어댑터 테스트에 클릭 순간 꺼진 버튼 · 댓글 확인의 비슷한 글 · 훑는 범위 행을 더함
- source: cycle 20261013-163932-adw/phase-6-poster-chrome · tracker plans/interview-marketing-agent.md#phase-6 · deferred by ship-check
- evidence: src/agent/chrome.py:231 `or not button.first.is_enabled()` 를 뺀 변이, src/agent/chrome.py:239 `==` → `in`(부분 일치) 변이와 `texts[:CONFIRM_SCAN]` → `texts` 변이가 스위트에서 초록(.adw/ship-report.md § Test integrity)
- direction: tests/test_chrome.py 의 YouTubePageTest 에 ① `full_page(submit={"enabled": False})` 에서 `submit()` → `PageError(post_button_missing)`, click 0회 ② `texts` 가 `(TEXT + " 그리고 덧붙인 말",)` → `confirm_posted` 가 False ③ `texts` 가 `("다른 사람 댓글",) * CONFIRM_SCAN + (TEXT,)` → False 행을 더한다 — 코드 변경 없음. 세 행 모두 지금 코드에서 초록이고, 각각 위 세 변이를 빨갛게 만듦(ship-check 프로브에서 확인)
- touches: tests/test_chrome.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-032 — 계약 '댓글 작성' 절의 Claude 오류 이유 틀에 빈 메시지 모양 적기
- source: sweep 20261013-180850-adw/smoke-sweep-s019-s023 · cycle 20261013-180850-adw/smoke-sweep-s019-s023 · tracker plans/interview-marketing-agent.md#phase-5 · deferred by ship-check
- evidence: docs/contracts.md:680 `claude 호출 실패: <오류 종류> <상태 코드>: <메시지 200자까지>` 는 콜론이 늘 붙는 것처럼 적었지만 src/agent/writer.py:260-265 `_error_detail` 은 메시지가 비면 `: …` 를 뺌(재현: `claude 호출 실패: E 429`). 바로 아래 :681-682 jev 틀은 `[ <상태 코드>][: …]` 로 적고 "Claude 틀과 같음"이라 해 두 줄이 서로 다르게 읽힘(.adw/ship-report.md § Risks R2)
- direction: docs/contracts.md:680 의 Claude 틀을 jev 틀과 같은 `claude 호출 실패: <오류 종류>[ <상태 코드>][: <메시지 200자까지>]` 표기로 바꾸고 괄호 설명에 "메시지가 비면 `: …` 도 뺍니다"를 더한다 — 코드 동작 · 로그 형식 변경 없음
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-033 — 추적 영상이 50개를 넘을 때 두 번째 videos.list 묶음까지 표본이 붙는지 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:222 — `range(0, len(queue), MAX_IDS_PER_CALL)` → `range(0, min(len(queue), MAX_IDS_PER_CALL), MAX_IDS_PER_CALL)`(처음 50개만 추적) 변이가 스위트에서 초록(201개 OK). 50개 넘는 테스트는 tests/test_watcher.py:421-433 하나뿐이고 첫 묶음이 500(.adw/ship-report.md § Test integrity). 지금 코드는 맞음 — 새 영상 120개 → `['videos:50', 'videos:50', 'videos:20']`, sampled 120(ship-check 에서 확인)
- direction: tests/test_watcher.py 에 창 안 영상 51개(새 ID 51개 또는 저장 영상 51개)와 두 묶음 모두 200 인 행을 더해 videos 호출 2번(50 · 1), `sampled == 51`, VIEWS 51줄을 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-034 — 검색어 둘 이상에서 오류·보류 뒤 남은 검색과 남은 묶음을 멈추는지 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:181, src/agent/watcher.py:177, src/agent/watcher.py:230 — 검색 오류 뒤 `return`→`break`, 검색 보류 뒤 `return`→`break`, videos 보류 뒤 `return`→`continue` 변이가 모두 초록. ApiErrorTest · QuotaTest 는 키워드 하나(tests/test_watcher.py:30 CONFIG)라 "남은 검색을 그만둠"(계약 11절)이 안 걸림(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 키워드 2개 Config 로 (a) 첫 검색 403 → search 호출 1번 · ERROR 1줄, (b) daily_max_searches 1 + 첫 키워드가 다음 페이지 토큰 → search 1번 · QUOTA 1줄, (c) 추적 51개 + 단위 한도로 첫 videos 묶음 보류 → QUOTA 1줄 · videos 호출 0번 을 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-035 — 제목·설명 밖 외부 글자 다섯 자리의 서로게이트 정리를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:72, src/agent/watcher.py:167, src/agent/watcher.py:207, src/agent/watcher.py:268, src/agent/watcher.py:296 — 각 자리의 `_clean` 을 뺀 변이가 tests.test_watcher 에서 초록. `Logbook.write(Event.ERROR, reason="HTTP 400 \ud800bad")` 는 UnicodeEncodeError 를 내므로 :296 이 깨지면 주기가 ERROR 줄 없이 끝남(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py IntakeTest/ApiErrorTest 에 channelId `"UC\ud800"`, 키워드 `"연애\ud800"`, search videoId `"x\ud800"`, 잘못된 viewCount 의 detail, 403 본문 reason `"bad\ud800"` 행을 더해 run 이 CycleReport 를 돌려주고 로그 값이 U+FFFD 로 parse_line 되는지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-036 — 경계값 넷(publishedAt 초 · 추적 창 경계와 설정값 · 단위 한도 경계 · 빈 nextPageToken)을 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:55 (`value[:16]` 변이 초록), src/agent/watcher.py:220 (`>`→`>=` 초록), src/agent/watcher.py:152 (`timedelta(hours=12)` 로 박은 변이 초록), src/agent/youtube.py:110 (`>`→`>=` 초록), src/agent/watcher.py:213 (빈 토큰을 따라가는 변이 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 `publishedAt "2026-10-12T10:00:37Z"` → `published_at` 초 37, `max_age_hours 6` 에서 정확히 NOW−6h 영상은 비추적 · NOW−5h 는 추적, `nextPageToken: ""` 이면 다음 페이지를 부르지 않음 을, tests/test_youtube.py 에 9,999 단위에서 videos.list 1회 허용 뒤 다음 호출 보류(units 10000/10000) 를 더한다 — 코드 변경 없음
- touches: tests/test_watcher.py, tests/test_youtube.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-037 — http_get 의 HTTPError → (code, body) 변환을 단위 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/youtube.py:181-188 — `grep -n -e http_get -e HTTPError -e urlopen tests/*.py` 결과 없음. 지금 증명은 verify 러너 V9(실제 루프백 403)뿐이라 스위트 밖(.adw/ship-report.md § Spec compliance)
- direction: tests/test_youtube.py 에 `urllib.request.urlopen` 을 patch 한 테스트를 더해 HTTPError(403, 본문) → `(403, 본문)`, 200 응답 → `(200, 본문)`, 요청의 `Accept: application/json` 헤더와 timeout 전달을 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-038 — 계약 첫 문단의 모듈 목록과 config.yaml 첫 주석을 지금 코드에 맞춤
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: docs/contracts.md:3-6 — 코드 위치로 Phase 1 파일 6개만 나열하고 11절의 env.py · youtube.py · watcher.py 를 빠뜨림. config.yaml:1 — "과제 안내의 예시 값입니다" 인데 poll_interval_min · daily_max_searches 는 과제와 다름(.adw/verify-plan.md § Out of scope (b), .adw/ship-report.md § Smoke candidates)
- direction: docs/contracts.md:3-6 의 모듈 목록에 `env.py` · `youtube.py` · `watcher.py`(11절)를 더하고, config.yaml:1 주석을 "과제 예시 값이 기본이고, 주기와 검색 상한은 계약 2절대로 바꿈" 으로 고친다 — 값과 계약 조항은 그대로
- touches: docs/contracts.md, config.yaml
- status: resolved
- attempts: 1 · last failure: reverted d7ca76f — own check red (스윕 20261014-031024-adw/smoke-sweep-s038-s042)
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-039 — 검색 쿼터 비용을 "구글의 계산"이 아니라 "우리 장부의 일부러 엄격한 계산"으로 바로 적음
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by deep-interview (ship-check R3 → HC1 질문 2 A)
- evidence: docs/contracts.md:58-67, docs/contracts.md:535-536, docs/contracts.md:553-554, config.yaml:14, docs/research/search-quota.md:8, docs/research/search-quota.md:17 — 검색 1회를 "Google 의 100 단위(하루 10,000 단위 한 통)"로 적음. 구글 공식 표는 2026-10-08 부터 `search.list` 를 하루 100회 별도 통(1회 1), `videos.list` 를 나머지 10,000 단위 통에서 1로 셈(https://developers.google.com/youtube/v3/determine_quota_cost "Last updated 2026-10-08 UTC", .adw/ship-report.md § Risks R3). 장부(src/agent/youtube.py:32-33, :107-111)는 트래커 Phase 2 결정(HC1 질문 2 A)대로 옛 계산을 일부러 유지 — 코드는 맞고 문서의 이유가 틀림
- direction: 계약 2절 · 11절과 config.yaml:14 주석을 "구글은 검색을 하루 100회 별도 통으로 센다 · 우리 장부는 더 엄격하게 검색 1회를 10,000 단위 통에서 100씩 깎는다(옛 규칙과 새 규칙 모두에서 넘치지 않게) · 그래서 기본 90회면 조회수 몫은 1,000 단위 이상이고, daily_max_searches 를 95–100 으로 올려 조회수가 막히는 것은 구글이 아니라 우리 장부 때문(그때는 장부를 두 통으로 나누는 결정이 따로 필요)"으로 고친다(출처 URL · 갱신일 포함). docs/research/search-quota.md 는 조사 기록이라 :8 · :17 을 지우지 않고 `## Decision` 아래에 날짜 붙은 정정 줄을 더한다 — 값 · 코드 · 장부 파일 모양 · 계약 조항의 동작은 그대로
- touches: docs/contracts.md, config.yaml, docs/research/search-quota.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-040 — 표본 2개 이상인 기록의 VIEWS prev/delta 와, 조회수 호출만 막혔을 때의 held 를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:274 (`view_history[-2]`→`[0]` 변이 초록), src/agent/watcher.py:220 (표본 2개 이상인 기록을 추적에서 빼는 변이 초록), src/agent/watcher.py:229 (`_track` 의 `tally.held = True` 를 지운 변이 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 창 안 저장 영상의 view_history 가 [1000, 1300] 일 때 새 조회수 1450 이면 `VIEWS prev=1300 delta=150` 인지, 장부를 검색 99회(9,900단위)로 채우고 daily_max_searches 200 에서 검색 1회는 통과 · videos.list 는 막히면 `CycleReport.held is True` 와 `QUOTA … call=videos.list counter=units` 한 줄인지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-041 — 실패할 수 없는 단언 둘을 고침
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: tests/test_youtube.py:276 (`QuotaLedger(...)` 가 먼저 QuotaError 를 내서 `fetch.urls == []` 는 늘 참), tests/test_watcher.py:613-617 (src/agent/watcher.py:150-151 을 지워도 src/agent/youtube.py:211 의 다른 ValueError 로 통과)(.adw/ship-report.md § Test integrity)
- direction: tests/test_youtube.py:276 의 단언을 지우거나 장부 거부를 직접 단언하는 것으로 바꾸고, tests/test_watcher.py ClockTest.test_naive_now_is_rejected 는 `assertRaisesRegex(ValueError, "now 에 시간대가 없습니다")` 로 문구까지 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py, tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-042 — 탐지 입력 가장자리 여섯 가지를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:213 (`isinstance(token, str)` 제거 초록), src/agent/watcher.py:207 (SKIP 의 `raw[:40]`→`raw` 초록), src/agent/watcher.py:74 (description 기본값 `""` 제거 초록), src/agent/watcher.py:202 (검색 ID `fullmatch`→`match` 초록), src/agent/watcher.py:53 (publishedAt `fullmatch`→`match` 초록), src/agent/watcher.py:55 (`.replace(tzinfo=utc)`→`.astimezone(utc)` 는 TZ=UTC 호스트에서 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 nextPageToken 이 str 이 아니면(예: 5) 다음 페이지를 부르지 않음 · 40자보다 긴 잘못된 검색 ID 의 SKIP video 값이 40자 · description 이 없는 영상은 description "" 로 저장 · 12자 검색 ID 는 search.list 단계에서 SKIP 되고 videos.list 로 가지 않음 · INVALID_ITEMS 에 publishedAt "2026-10-12T10:00:00Zjunk" 행 · publishedAt 고정 테스트를 로컬 시간대가 UTC 가 아닐 때(TZ=Asia/Seoul + time.tzset, 끝나면 되돌림, tzset 이 없는 곳은 skip)도 돌림 을 더한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-043 — 쿼터 장부 · 클라이언트 가장자리 일곱 가지를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/youtube.py:148 (`utf-8-sig`→`utf-8` 초록), src/agent/youtube.py:130-135 (장부 `indent=None` · `sort_keys=False` 초록), src/agent/youtube.py:124 (`astimezone(utc)` 없는 `isoformat()` 초록), src/agent/youtube.py:242-243 (URL 만들기와 reserve 순서 바꾸기 초록), src/agent/youtube.py:104-105 (모르는 호출 ValueError 제거 초록), src/agent/youtube.py:259 (`replace(key, mask, 1)` 초록), src/agent/youtube.py:252 (`status != 200`→`status >= 400` 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_youtube.py 에 BOM 붙은 유효한 quota.json 을 읽음 · 쓴 장부 파일이 키 정렬 · 2칸 들여쓰기 · KST 인 now 로 reserve 해도 저장된 at 이 `+00:00` · page_token="\ud800" 처럼 URL 을 못 만드는 호출은 장부에 안 적히고 fetch 0회 · `reserve("comments.list", …)` 는 ValueError · URL 을 두 번 담은 OSError 문구에서 키가 둘 다 가려짐 · `(302, b'{"items": []}')` 은 `YouTubeError` 의 reason `"HTTP 302"` 를 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-044 — .env 읽기 가장자리 셋을 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/env.py:34 (`raw.strip()`→`raw` 초록), src/agent/env.py:39 (`not sep` 제거 초록), src/agent/env.py:28-29 (`except OSError` 제거 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_env.py 에 공백만 있는 줄과 들여 쓴 `# 주석` 줄은 건너뜀 · `=` 없는 `JUSTNAME` 줄은 줄 번호를 대고 값은 말하지 않는 `EnvError` · `.env` 자리가 폴더면 `EnvError` 를 단언한다 — 코드 변경 없음
- touches: tests/test_env.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-045 — 쿼터 장부의 임시 파일 쓰기와 구글 reason 이 글자가 아닐 때를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/youtube.py:136 (`tmp = self.path` 로 바꿔 임시 파일 없이 바로 쓰는 변이 초록), src/agent/youtube.py:273 (`return str(reason)` 변이 초록 — 오류 줄이 `HTTP 404 None` 이 됨)(.adw/ship-report.md § Test integrity)
- direction: tests/test_youtube.py 에 reserve 하는 동안 `os.replace` 를 가로채 첫 인자가 `quota.json.tmp` 이고 둘째가 `quota.json` 인지 · 404 본문의 `error.errors[0].reason` 이 `5` 나 `null` 이면 `YouTubeError` reason 이 정확히 `"HTTP 404"` 인지 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-046 — 저장소 쓰기 오류 전파 · publishedAt 소수 자릿수 · 글자 아닌 id · 다음 페이지의 publishedAfter 를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:271 (`self._store.put(record)` 를 `try/except: return` 으로 감싼 변이 초록 — 계약 11절 "저장소 쓰기 오류는 run_loop 로 올라감"), src/agent/watcher.py:32 (소수 `{1,9}`→`{1,3}` 변이 초록), src/agent/watcher.py:89 (`isinstance(item.get("id"), str)` 제거 변이 초록), src/agent/youtube.py:220-225 (pageToken 이 있을 때 publishedAfter 를 빼는 변이 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 `put` 이 `OSError` 를 내는 Store 하위 클래스를 넣으면 `Watcher.run` 이 그 `OSError` 를 그대로 내는지 · publishedAt `"2026-10-12T10:00:00.123456789Z"` 가 저장되고 10자리 소수는 SKIP 인지 · videos.list 응답에 `{"id": {"x": 1}}` 항목이 섞여도 주기가 끝나고 그 항목이 무시되는지 · 다음 페이지 요청에도 첫 페이지와 같은 publishedAfter 가 실리는지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-047 — SKIP 줄의 detail 내용과 200 이 아닌 2xx 상태를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:268 (`detail=_clean(str(exc))` 를 `detail=None` · `detail="x"` 로 바꾼 변이 둘 다 초록 — tests/test_watcher.py:518 이 `assertTrue(fields.pop("detail"))` 로 참/거짓만 봄), src/agent/youtube.py:186 (`response.status` 를 `200` 으로 박은 변이 초록 — S-037 가 요구한 403 · 200 행으로는 잡히지 않음)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py IntakeTest 의 INVALID_ITEMS 행마다 SKIP 줄 detail 의 앞부분을 지금 코드가 내는 글 그대로 단언하고(예: viewCount `-5` 행은 `statistics.viewCount:` 로 시작), tests/test_youtube.py 에 `urllib.request.urlopen` 을 patch 해 204 응답이 `http_get` 에서 `(204, b"")` 로 돌아오는지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py, tests/test_youtube.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-048 — 달력에 없는 publishedAt 의 SKIP detail 이 칸 이름 없이 파이썬 판마다 다른 strptime 글을 냄
- source: sweep 20261014-035745-adw/smoke-sweep-s043-s047 · cycle 20261014-035745-adw/smoke-sweep-s043-s047 · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:55 — 모양 검사(`_PUBLISHED_RE`, watcher.py:32)를 통과한 `"2026-02-30T00:00:00Z"` 가 `strptime` 에서 떨어져 detail 이 3.14 에서 `day 30 must be in range 1..28 for month 2 in year 2026`, 3.10 에서 `day is out of range for month`(값도 칸 이름도 없음); 13월은 두 판 모두 `time data '2026-13-01T00:00:00' does not match format …` — 다른 invalid_item detail 은 모두 칸 이름으로 시작(watcher.py:54, :62)(.adw/ship-report.md § Risks R1)
- direction: `_published` 에서 `strptime` 이 낸 `ValueError` 를 `snippet.publishedAt:` 로 시작하고 값(`{value!r:.40}`)을 담은 고정 문구로 바꿔 다시 내고, tests/test_watcher.py 의 `INVALID_DETAIL_PREFIX` 13월 행을 `snippet.publishedAt:` 로 바꾸고 2월 30일 행(INVALID_ITEMS 와 함께)을 더한다
- touches: src/agent/watcher.py, tests/test_watcher.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-049 — 판별 미달 셈의 확신 하한(choice_min_confidence) 올리기를 테스트로 고정
- source: cycle 20261014-035728-adw/phase-6a-live-check-prepare · tracker plans/interview-marketing-agent.md#phase-6a · deferred by ship-check
- evidence: tests/live_check.py:216-218 (`[row["confidence"] for row in negatives]` 를 `[row["noul"] for row in negatives]` 로 바꾼 변이에도 스위트 539개 초록 `OK (skipped=3)` — 그런데 정답 no 예시 하나가 noul 0.97 · 확신 0.6 이면 best_correct 가 21 → None 으로 바뀌어 `6B: go` 가 `6B: stop — 판별 미달(… 잘못된 일치 못 막음)` 이 됨; 모든 테스트 표본의 확신이 0.9 또는 noul 이 이미 1 을 넘는 0.98 이라 확신 쪽 후보가 한 번도 판정을 가르지 않음 · .adw/guard-matrix.md G1 의 ② 행에도 확신 하한 행이 없음)(.adw/ship-report.md § Test integrity)
- direction: tests/test_live_check.py VerdictTest(또는 AccuracyTest)에 잘못된 일치를 확신 하한으로만 막을 수 있는 표본(예: 정답 yes 21개 noul 0.95 · 확신 0.9, 정답 no 1개 noul 0.97 · 확신 0.6)을 넣어 best_correct 21 · `6B: go` 를 단언하고, 같은 표본의 결과 파일을 `--verdict` 로 다시 세어도 같은 줄인지 단언한다 — 코드 변경 없음
- touches: tests/test_live_check.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-050 — Claude 채점의 광고 · 고민 질문이 claude_grade 를 bad 로 만드는지 테스트로 고정
- source: cycle 20261014-035728-adw/phase-6a-live-check-prepare · tracker plans/interview-marketing-agent.md#phase-6a · deferred by ship-check
- evidence: tests/live_check.py:1157-1158 (`and not grade["reads_like_ad"]` 와 `and grade["follows_concern"]` 를 각각 `and True` 로 바꾼 두 변이 모두 스위트 539개 초록 — 테스트의 나쁜 채점 표본(GRADE_BAD)은 `scene_in_material` 하나만 다름; `claude_grade` 는 6B 가 사람 칸이 비었을 때 초안의 정답으로 쓰는 칸)(.adw/ship-report.md § Test integrity)
- direction: tests/test_live_check.py GradeTest 에 `reads_like_ad=true` 인 답과 `follows_concern=false` 인 답을 하나씩 더해 각각 `claude_grade == "bad"` 를 단언한다 — 코드 변경 없음
- touches: tests/test_live_check.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-051 — youtu.be · shorts 쿼리 이름의 "셋뿐 · 정확히 같을 때" 를 테스트로 고정
- source: cycle 20261014-035715-adw/phase-1a-parser-allow-rules · tracker plans/interview-marketing-agent.md#phase-1a · deferred by ship-check
- evidence: src/agent/guard.py:23 (`_SHARE_QUERY_NAMES` 에 `"index"` 를 더한 변이 초록 — `?index=2` 가 A 로 읽힘), src/agent/guard.py:66 (`key in` 을 `key.strip() in` 으로 바꾼 변이 초록 — `?+si=x` · `?si%20=x` · `?%20t=1` 이 A 로 읽힘); 계약 docs/contracts.md:299-300 "셋뿐 … 대소문자까지 같을 때"(.adw/ship-report.md § Test integrity)
- direction: tests/test_guard.py 의 REJECTED_SHARE_QUERIES 에 `?index=2` · `?t=1&index=2` · `?start=5` · `?+si=x` · `?si%20=x` · `?%20t=1` 을 더해 두 형식 모두 `invalid_video` 인지 단언한다 — 코드 변경 없음
- touches: tests/test_guard.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-052 — read_log 의 공백만 있는 줄과 줄 바꿈 · U+2028 제목의 한 사건 읽기를 테스트로 고정
- source: cycle 20261014-035715-adw/phase-1a-parser-allow-rules · tracker plans/interview-marketing-agent.md#phase-1a · deferred by ship-check
- evidence: src/agent/logbook.py:180 (`if not line:` 을 `if not line.strip():` 으로 바꾼 변이 초록 — `good\n   \ngood\n` 이 오류 없이 사건 2개; 계약 docs/contracts.md:453 "빈 줄을 뺀 모든 줄 … 건너뛰지 않고"), tests/test_logbook.py RawCharacterTest::test_repro_titles_leave_no_raw_control_or_surrogate_and_read_back 의 제목에 `\n` · U+2028 이 없음(계약 L446 "여러 줄짜리 댓글도, 영상 제목에 숨긴 U+2028 도 read_log 의 읽기로 한 사건 한 줄")(.adw/ship-report.md § Test integrity)
- direction: tests/test_logbook.py ReadLogTest 에 공백 · 탭 · `\x0c` 만 있는 둘째 줄이 각각 `2번째 줄: ` 로 시작하는 ValueError 인지, `Logbook` 으로 제목 `"a\nb"` · `"a" + chr(0x2028) + "b"` 를 쓴 파일을 read_log 가 DETECT 하나씩 원래 값으로 돌려주는지 단언한다(글자는 chr() 로 씀) — 코드 변경 없음
- touches: tests/test_logbook.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-053 — 가드의 `;` 나누기를 받는 이름만 든 쿼리로 다시 테스트에 고정 (S-003 의 잠금이 1A 뒤 풀림)
- source: cycle 20261014-035715-adw/phase-1a-parser-allow-rules · tracker plans/interview-marketing-agent.md#phase-1a · deferred by ship-check
- evidence: src/agent/guard.py:65 (`parts.query.replace(";", "&")` 를 `replace(";", "&", 1)` 로 바꾼 변이가 스위트 461개 초록 — `https://youtu.be/AAAAAAAAAAA?si=x;t=1;v=BBBBBBBBBBB` · `https://www.youtube.com/shorts/AAAAAAAAAAA?feature=share;si=x;v=BBBBBBBBBBB` · `https://www.youtube.com/watch?si=x;t=1;v=BBBBBBBBBBB&v=AAAAAAAAAAA` 가 A 로 읽힘, HEAD 는 셋 다 None), tests/test_guard.py:47-48 (S-003 가 이 변이를 잡으려 더한 `?x=1;y=2;v=B` · `?a=1;b=2;v=B` 행은 1A 뒤 `x` · `a` 가 받는 이름 밖이라 `;` 나누기와 상관없이 막혀 더는 가리지 못함 — 같은 변이가 base `d9a3d0f` 에서는 빨강); 계약 docs/contracts.md:309-310 "숨는 이름을 놓치지 않으려는 것"(.adw/ship-report.md § Test integrity)
- direction: tests/test_guard.py 의 REJECTED_REFS `;` 묶음에 `f"https://youtu.be/{REPRO_A}?si=x;t=1;v={REPRO_B}"` · `f"https://www.youtube.com/shorts/{REPRO_A}?feature=share;si=x;v={REPRO_B}"` · `f"https://www.youtube.com/watch?si=x;t=1;v={REPRO_B}&v={REPRO_A}"` 행을 더한다 — 코드 변경 없음, 지금 코드는 셋 다 None
- touches: tests/test_guard.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-054 — read_log 의 끝 `\n` 없는 공백만 있는 마지막 줄을 테스트로 고정
- source: cycle 20261014-035715-adw/phase-1a-parser-allow-rules · tracker plans/interview-marketing-agent.md#phase-1a · deferred by ship-check
- evidence: src/agent/logbook.py:176 (`if tail:` 을 `if tail.strip():` 으로 바꾼 변이가 스위트 461개 초록 — `<정상 줄>\n` 뒤에 줄바꿈 없는 ` ` · `\t` · `\r` 만 남은 파일이 HEAD 에서는 `2번째 줄: 끝에 줄바꿈이 없습니다 (쓰기 중 끊긴 줄)` ValueError 인데 변이에서는 오류 없이 사건 1개); 계약 docs/contracts.md:456-457 "끝 `\n` 이 없는 마지막 줄 … 건너뛰지 않고"(.adw/ship-report.md § Test integrity). S-052 의 둘째 줄 행은 줄바꿈으로 끝나는 꼴이라 이 변이를 잡지 못함
- direction: tests/test_logbook.py ReadLogTest::test_last_line_without_newline_is_an_error 에 정상 줄 하나 뒤 줄바꿈 없는 `" "` · `"\t"` · `"\x0c"` 꼬리를 쓴 파일이 각각 `2번째 줄: ` 로 시작하는 ValueError 인지 보는 행을 더한다(글자는 chr() 로 써도 됨) — 코드 변경 없음
- touches: tests/test_logbook.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-055 — 정수 상한 오류 문구 "값은 메시지에 쓰지 않음" 을 10진수 행에서도 정확한 문자열로 고정
- source: cycle 20261014-035715-adw/phase-1a-parser-allow-rules · tracker plans/interview-marketing-agent.md#phase-1a · deferred by ship-check
- evidence: src/agent/config.py:180 (값이 `10**100` 보다 작을 때만 메시지에 `(값 {value})` 를 붙인 변이가 스위트 461개 초록 — `poll_interval_min: 52560001` 이 `52560000 이하여야 합니다: poll_interval_min (값 52560001)`); tests/test_config.py:743 이 `assertIn`(부분 문자열)으로만 보고, 값 빼기는 16진수 두 행에서만 잼; 계약 docs/contracts.md:73 "(값은 메시지에 쓰지 않음)"(.adw/ship-report.md § Test integrity)
- direction: tests/test_config.py RangeFailureTest::test_every_out_of_range_value_is_config_error 에서 상한+1 행마다 `str(exc)` 가 `<상한> 이하여야 합니다: <키>` 와 정확히 같은지(assertEqual) 단언한다 — 코드 변경 없음
- touches: tests/test_config.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-056 — 계약 10절 뒤 번호 제목 검사를 마침표 없음 · 괄호 · 공백 둘 · 앞 공백 꼴까지 넓히기 (헌법 12조 첫 본보기)
- source: cycle 20261014-035724-adw/phase-1b-contract-section-names · tracker plans/interview-marketing-agent.md#phase-1b · deferred by ship-check (Risks 2) → 색은 E-022 인터뷰가 정함(2026-10-14 · 슬롯 0bd7add3 질문 5 A, 트래커 Phase 1B "출하 뒤 고침" 줄)
- evidence: tests/test_contract_sections.py:20 (`HEADING_RE = ^## ([0-9]+)\.` — `## 11 제목` · `## 11) 제목` · `##  11.` · `   ## 11.` 이 `[]` 로 읽혀 초록, journal 20261014-035724-adw-phase-1b-contract-section-names/ship-report.md:177-181 Risks 2); 계약 docs/contracts.md:564 "그 뒤에 더하는 절은 번호 없이 제목만" 이 이미 넷을 금지
- direction: `HEADING_RE` 를 `^ {0,3}##[ \t]+(\d+)` (re.MULTILINE) 꼴로 넓히고 `numbered_headings` docstring 을 맞춘다(오늘 계약서에서 그대로 1–10 — 인터뷰가 잼). 헌법 12조 꼴로 표본을 스위트에 남긴다 — `FIRST_TEN` 뒤에 붙인 `## 11 제목` · `## 11) 제목` · `##  11.` · `   ## 11.` 은 각각 `numbered_headings(...) != NUMBERED` (red — 트래커 Phase 1B 출하 뒤 고침 줄), `TITLED` 뒤에 붙인 `### 1. 입력 확인` · `### 11.` 은 `== NUMBERED` (green — 같은 줄 · 1B Trade-offs accepted `### 11.` 줄); 표본 줄마다 주석으로 그 인용을 단다. 계약서 · src 변경 없음
- touches: tests/test_contract_sections.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-057 — 설정 글자 규칙 오류 메시지 괄호에 "이 파이썬이 모르는 새 글자(최근 이모지 등)" 를 더하기
- source: cycle 20261014-112313-adw/phase-1c-text-config-allow · tracker plans/interview-marketing-agent.md#phase-1c · deferred by deep-interview (HC1 질문 1 B, 슬롯 1c)
- evidence: src/agent/config.py:216-217 — 괄호가 "줄바꿈 · 탭 · 전각 공백 · 폭 없는 공백" 만 예로 듦; tests/test_config.py:289-292 (TEXT_CHARS) 가 정확한 문구를 고정; `topic: "연애 고민 🫩"` 이 파이썬 3.14.4 에서 `load OK`, 3.12.13 에서 이 메시지(인터뷰가 같은 파일로 잼) — 판정이 실행 중인 파이썬의 unicodedata 를 따르므로 낡은 판은 새 이모지를 Cn 으로 거절
- direction: `_text` 의 글자 규칙 ConfigError 괄호를 "(줄바꿈 · 탭 · 전각 공백 · 폭 없는 공백, 이 파이썬이 모르는 새 글자(최근 이모지 등) 등은 안 됩니다)" 꼴로 넓히고 TEXT_CHARS 를 같은 문구로 맞춘다 — 규칙 · 거절 범위 · 키 이름 꼬리 `: <키>` 는 그대로, 값은 여전히 메시지에 쓰지 않음; 계약 2절은 괄호를 `(…)` 로 비워 두어(docs/contracts.md:116) 고치지 않는다
- touches: src/agent/config.py, tests/test_config.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-058 — 두 키가 함께 틀린 설정에서 chrome_debug_url 오류가 topic 오류보다 먼저 나는 순서를 스위트로 고정
- source: cycle 20261014-112313-adw/phase-1c-text-config-allow · tracker plans/interview-marketing-agent.md#phase-1c · deferred by ship-check
- evidence: src/agent/config.py:319 (`chrome_debug_url` 읽기)가 :334 (`topic` 읽기)보다 앞 — topic 읽기를 크롬 주소 읽기 앞으로 옮긴 변이가 전체 스위트에서 `OK (skipped=3)`(.adw/ship-report.md § Test integrity, 시드 S15); 이 순서는 계획의 "error precedence is unchanged" 이고 지금은 일회성 점검 .adw/verify.sh V2 의 `order_url_before_topic` 행만 잼
- direction: tests/test_config.py 의 TextKeyTest 에 `config_from_mapping(valid())` 로 topic 을 `"연애\t"`, chrome_debug_url 을 `"http://localhost:9222 "` 로 함께 바꾼 행 하나를 더해 `str(exc) == f"{EDGE_SPACE}: chrome_debug_url"` 를 단언한다 — 코드 · 계약 변경 없음, 같은 행이 base 4ef1455 의 순서(주소 먼저)와도 같음
- touches: tests/test_config.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-059 — 계약 '결과 반영' · README 의 "사람 칸을 고친 결과를 커밋하면 빨강" 을 `ok` · `bad` 를 적은 경우로 좁힘
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by ship-check
- evidence: tests/test_live_check_applied.py:165 (사람 칸이 정확히 `ok` · `bad` 가 아니면 답 없음으로 셈) — 첫 parsed 초안의 `human` 을 `Bad` · `OK` · `ok ` · `good` 로 바꾸면 `draft_counts` 의 answered=0 · 기록 줄 그대로라 모듈 16개 초록(`bad` 만 failures=2); 문장 docs/contracts.md:1234 "새 결과나 사람 칸을 고친 결과를 커밋하거나 … 이 모듈이 빨강입니다" · docs/live-check/README.md:19 "사람 칸을 고친 `result.json` 을 커밋하면 … 빨강이 됩니다"; 계약 :1192-1193 은 사람 칸 값을 `ok` · `bad` 로 정함(.adw/ship-report.md § Risks R2)
- direction: 두 문장을 코드가 하는 만큼으로 좁힌다 — "사람 칸에 `ok` · `bad` 를 적은 결과" 로 쓰고, 그 밖의 값은 답 없음으로 세어 빨강이 되지 않는다고 덧붙인다(헌법 9 의 좁히기) — 코드 · 테스트 변경 없음
- touches: docs/contracts.md, docs/live-check/README.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-060 — 지문 맞대기가 지키는 칸 목록(GUARDED · WRITE_SIDE)을 계약의 두 목록과 맞대 테스트로 고정
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by ship-check
- evidence: tests/test_live_check_applied.py:28-30 — `margin` 을 GUARDED 에서 WRITE_SIDE 로 옮겨도 16개 초록(ship-check 메모리 재현 `(16, 0, 0)`); test_guarded_field_change_is_drift(:265)는 모듈의 GUARDED 를 그대로 돌고 test_every_fingerprint_key_is_sorted(:296)는 합집합만 봄; 계약 docs/contracts.md:1226-1229 의 두 칸 목록은 어느 테스트도 읽지 않음(.adw/ship-report.md § Risks R3)
- direction: MeasuredDriftTest 에 GUARDED · WRITE_SIDE 로 계약의 두 칸 목록 글(`` " · ".join(f"`{k}`" for k in GUARDED) `` 꼴)을 만들어 assert_in_contract 로 맞대는 테스트를 더한다 — 코드 · 계약 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-061 — 초안 정답의 사람 칸 우선과 기준값 사이 경계(noul 이 정확히 0.2 · 0.8)를 심은 데이터로 테스트에 고정
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by ship-check
- evidence: tests/test_live_check_applied.py:167 — 우선순위를 뒤집은 변이(`answer = claude if claude is not None else human`)가 16개 초록(ship-check 감사의 사본 실행); 심은 초안(human ok · claude_grade bad · self_check_pass True)에서 지금 코드는 bad_passed 0, 변이는 1. :112 · :126 의 `lo < noul < hi` 를 `lo <= noul <= hi` 로 바꾼 변이도 초록 — 커밋된 결과에 답 있는 초안이 없고 noul 이 정확히 0.2 · 0.8 인 예시 · 영상이 없음; 계약 docs/contracts.md:922 "정답은 사람 칸 … 있으면 그것" · :1091-1094 "0.2 초과 0.8 미만"(.adw/ship-report.md § Risks R4)
- direction: load_result() 의 deepcopy 에 초안 둘(human ok · claude_grade bad · self_check_pass True 와 그 반대)과 noul 0.2 · 0.8 인 예시 행 · 영상을 심어 draft_counts 와 gap_lines 의 셈을 정확한 값으로 단언하는 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-062 — 계약 기록 맞대기(assert_in_contract)가 숫자 뒤에 더 붙은 숫자를 놓침
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by ship-check
- evidence: tests/test_live_check_applied.py:210-214 (정규화한 계약 전체에서 부분 문자열로 찾음) — 계약의 `기준값 사이 영상 운영 창: 9/18` 을 `9/180` 으로 바꾼 사본으로도 16개 초록(ship-check 메모리 재현 `(16, 0, 0)`), `탈락 0` → `탈락 05` 도 초록(감사 사본); 트래커 Phase 6B Responsibilities 첫 줄 "계약에 적은 숫자와 결과 파일의 숫자가 같아야 한다"(.adw/ship-report.md § Risks R5)
- direction: assert_in_contract 가 phrase 가 숫자로 끝날 때 바로 뒤에 숫자나 `.숫자` 가 오지 않는지까지 보게 고친다(정규식 경계) — 기록 줄 · 계약 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-063 — '주제 판별' 기록의 다섯 셈을 accuracy 행에서 다시 세어 accuracy_tally 와 맞댐
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by ship-check
- evidence: tests/test_live_check_applied.py:94-99 — 맞음 · 잘못된 일치 · 잘못된 불일치 · 보류 · 오류를 `accuracy_tally` 에서 그대로 옮김(행에서 다시 세지 않음; `correct` 만 :335 의 reach == correct 로 간접 확인); 계약 docs/contracts.md:1099 "기록의 숫자를 결과 파일에서 다시 세어 맞댑니다". ship-check 의 독립 재셈은 ko · en 모두 20/0/0/2/0 으로 지금 값과 같음(.adw/ship-report.md § Risks R6)
- direction: AccuracyRecordTest 에 언어마다 accuracy 행(label · verdict · error, 또는 tests/jev_accuracy.py 의 tally)으로 다섯 칸을 다시 세어 accuracy_tally 와 같은지 단언하는 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-064 — 계약 '댓글 작성' 잰 값의 "세 점수 가운데 가장 낮은 것" 을 비교 점수로 · 여럿 · 1 넘음까지 적음
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by deep-interview (HC1 질문 1 A)
- evidence: docs/contracts.md:924-926 "그 초안의 세 점수 가운데 가장 낮은 것 + 0.05 로 올리고" — 결과 파일 `scores` 칸은 날 점수(P(예))라 광고 0.06 이 가장 낮게 읽혀 통과선이 0.11 로 내려갈 수 있음(.adw/ship-report.md § Risks R7); 하한 비교는 docs/contracts.md:893-894 · src/agent/writer.py:182 에서 광고를 1 − P(예) 로 뒤집음; 트래커 Phase 6B 결정 "(2026-10-14 6B HC1 인터뷰 질문 1 A …)" 이 뜻을 정함
- direction: 그 문장을 트래커 줄과 같은 뜻으로 고친다 — "세 비교 점수(장면 · 고민은 P(예), 광고는 1 − P(예)) 가운데 가장 낮은 것 + 0.05; 그런 초안이 여럿이면 초안마다 가장 낮은 비교 점수 중 가장 높은 값 + 0.05; 그 값이 1 을 넘으면 고치지 않고 사람에게" — 코드 · 테스트 변경 없음
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-065 — 계약 '결과 반영' 의 "그 사이클을 맡을 페이즈는 트래커가 정합니다" 를 Phase 6D · 레인에만 커밋으로 좁힘
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by deep-interview (HC1 질문 2 A)
- evidence: docs/contracts.md:1236 "그 사이클을 맡을 페이즈는 트래커가 정합니다" — 트래커에 그런 페이즈가 없었음(.adw/ship-report.md § Risks R8); 트래커 Phase 6B 결정 "(2026-10-14 6B HC1 인터뷰 질문 2 A …)" 과 Phase 6C · 6D 절이 주인과 길을 정함
- direction: 그 문장을 "그 사이클은 Phase 6D(트래커)가 맡고, 새 결과는 main 이 아니라 그 페이즈의 레인 브랜치에만 커밋합니다 — 그 뒤의 재실행도 트래커에 다시 반영 페이즈를 열고 같은 길로" 로 고친다 — 코드 · 테스트 변경 없음(README 커밋 단계는 Phase 6C 가 고침)
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-066 — 계약 기록 맞대기가 같은 머리에 다른 숫자를 단 모순된 중복 줄을 놓침
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by ship-check
- evidence: tests/test_live_check_applied.py:210-214 (`assert_in_contract` 는 맞는 줄이 계약 어딘가에 있는지만 봄) — 계약 사본의 `- en: 지금 기준값 맞음 20/22 …` 줄 아래에 `- en: 지금 기준값 맞음 12/22 · 잘못된 일치 3 · … — 미달` 을 더해도 AccuracyRecordTest 3개 초록(ship-check 재현 ran 3 · failures 0 · errors 0); S-062 의 숫자 경계 고침으로는 닫히지 않음; 트래커 Phase 6B Responsibilities 첫 줄 "계약에 적은 숫자와 결과 파일의 숫자가 같아야 한다"(.adw/ship-report.md § Risks R5)
- direction: 기록 줄마다 머리(`ko: 지금 기준값 맞음` · `en: 지금 기준값 맞음` · `영상 판별 운영 창:` · `기준값 사이 영상 운영 창:` · `초안 운영 창:` · `모델 이름:` 등, 정규화한 글)가 계약 전체에 정확히 한 번 나오는지 단언하는 테스트를 더한다 — 코드 · 계약 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-067 — '주제 판별' 기록 줄의 다섯 칸 자리를 서로 다른 값을 심은 tally 로 고정
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · deferred by ship-check
- evidence: tests/test_live_check_applied.py:94-99 (`accuracy_lines` 가 tally 다섯 칸을 줄에 넣음) — 커밋된 tally 는 잘못된 일치 · 잘못된 불일치가 모두 0 이라 두 칸을 바꿔 넣는 변이도 16개 초록(ship-check 감사의 사본 실행 `(16,0,0)`); 계약의 기록은 이 도우미의 출력을 붙여 쓴 것이라 도우미가 틀리면 계약과 테스트가 함께 틀려 초록으로 남음(.adw/ship-report.md § Risks R6)
- direction: load_result() deepcopy 의 accuracy_tally 에 서로 다른 다섯 값(예: 맞음 15 · 잘못된 일치 1 · 잘못된 불일치 2 · 보류 3 · 오류 1)을 심고 accuracy_lines 의 결과를 글자 그대로 단언하는 테스트를 더한다 — 코드 · 계약 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-068 — 계약 '결과 반영' · README 의 "사람 칸을 고친 결과를 커밋하면 빨강" 을 `ok` · `bad` 를 적은 경우로 좁힘 (S-059)
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 두 문장을 "사람 칸에 `ok` · `bad` 를 적은 결과" 로 좁히고 그 밖의 값은 답 없음으로 센다고 덧붙임 — 코드 변경 없음
- touches: docs/contracts.md, docs/live-check/README.md
- base: adw/phase-6b-live-check-apply
- phase: plans/interview-marketing-agent.md#phase-6b
- status: resolved
- attempts: 0 · last failure: —

### S-069 — 지문 맞대기가 지키는 칸 목록(GUARDED · WRITE_SIDE)을 계약의 두 목록과 맞대 고정 (S-060)
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 두 상수로 계약의 칸 목록 글을 만들어 assert_in_contract 로 맞대는 테스트 추가
- touches: tests/test_live_check_applied.py
- base: adw/phase-6b-live-check-apply
- phase: plans/interview-marketing-agent.md#phase-6b
- status: resolved
- attempts: 0 · last failure: —

### S-070 — 초안 정답의 사람 칸 우선 · 정답 목록 · 기준값 사이 경계를 심은 데이터로 고정 (S-061)
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: load_result() deepcopy 에 초안 둘과 경계값 행 · 영상을 심어 draft_counts · gap_lines 셈을 정확한 값으로 단언
- touches: tests/test_live_check_applied.py
- base: adw/phase-6b-live-check-apply
- phase: plans/interview-marketing-agent.md#phase-6b
- status: resolved
- attempts: 0 · last failure: —

### S-071 — 계약 기록 맞대기가 숫자 뒤에 더 붙은 숫자를 놓침 (S-062)
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: phrase 가 숫자로 끝날 때 바로 뒤에 숫자나 `.숫자` 가 오지 않는지까지 봄
- touches: tests/test_live_check_applied.py
- base: adw/phase-6b-live-check-apply
- phase: plans/interview-marketing-agent.md#phase-6b
- status: resolved
- attempts: 0 · last failure: —

### S-072 — '주제 판별' 기록의 다섯 셈을 accuracy 행에서 다시 세어 accuracy_tally 와 맞댐 (S-063)
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 언어마다 행에서 다섯 칸을 다시 세어 accuracy_tally 와 같은지 단언하는 테스트 추가
- touches: tests/test_live_check_applied.py
- base: adw/phase-6b-live-check-apply
- phase: plans/interview-marketing-agent.md#phase-6b
- status: resolved
- attempts: 0 · last failure: —

### S-073 — 계약 기록 맞대기가 같은 머리의 모순된 중복 줄을 놓침 (S-066)
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 기록 줄 머리마다 계약 전체에 정확히 한 번 나오는지 단언하는 테스트 추가
- touches: tests/test_live_check_applied.py
- base: adw/phase-6b-live-check-apply
- phase: plans/interview-marketing-agent.md#phase-6b
- status: resolved
- attempts: 0 · last failure: —

### S-074 — '주제 판별' 기록 줄의 다섯 칸 자리를 서로 다른 값을 심은 tally 로 고정 (S-067)
- source: cycle 20261014-112322-adw/phase-6b-live-check-apply · tracker plans/interview-marketing-agent.md#phase-6b · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: deepcopy 의 accuracy_tally 에 서로 다른 다섯 값을 심고 accuracy_lines 결과를 글자 그대로 단언
- touches: tests/test_live_check_applied.py
- base: adw/phase-6b-live-check-apply
- phase: plans/interview-marketing-agent.md#phase-6b
- status: resolved
- attempts: 0 · last failure: —

### S-075 — README 9단계의 `cp` 와 `git restore` 를 `&&` 로 묶어, 복사가 실패하면 새 결과를 지우지 않게 함
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · deferred by ship-check
- evidence: docs/live-check/README.md:28-29 — 두 명령이 따로 된 두 줄이라 붙여 넣으면 `cp` 가 실패해도 `git restore` 가 돈다. ship-check 보안 감사의 임시 저장소 재현: 없는 레인 경로로 `cp exit=1` → `restore exit=0` → result.json 이 "NEW-RUN" 에서 "old" 로 돌아감. 돈 들인 실제 실행 결과와 사람이 적은 `human` · `topic_human` 칸이 사라짐(.adw/ship-report.md § Risks R1)
- direction: 두 줄을 `cp … && git restore …` 한 줄로 묶고, "복사가 실패하면(레인 경로가 없거나 6F 등 다른 이름) `git restore` 를 돌리지 않습니다" 한 문장을 35행 설명에 더한다 — 코드 · 계약 · 테스트 변경 없음
- touches: docs/live-check/README.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-076 — README 5단계의 "재지 못함과 채점 막힘이 함께 나오면 채점 호출 자체가 실패한 것" 을 코드가 하는 만큼으로 좁힘
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · deferred by ship-check
- evidence: docs/live-check/README.md:20 — `ten_drafts(10)` 에 채점과 무관한 YouTube search 500 오류 한 줄을 더하면 `verdict_line` 이 `6B: stop — 재지 못함(호출 오류 1); 채점 막힘(오류 10/10)` 을 내고, 모든 `grade_error` 는 `응답 모양` 이며 claude/grade 오류 줄은 0 이다(ship-check 품질 감사 실행). 계약 docs/contracts.md:1275-1276 의 문장("채점 호출이 API 오류로 실패한 초안은 … 함께 셉니다")은 맞고 README 의 인과 문장만 넓다(.adw/ship-report.md § Risks R2)
- direction: "함께 나오면 `재지 못함` 의 오류 줄부터 봅니다 — 그 줄에 `claude` · `grade` 가 있으면 채점 호출이 실패한 것이고, 없으면 채점 막힘의 원인은 `채점 답 모양:` 줄입니다" 로 고친다 — 코드 · 계약 · 테스트 변경 없음
- touches: docs/live-check/README.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-077 — 넓힌 창 여는 조건의 경계(인기 댓글 초안 = 최소 3)와 채점 막힘의 홀수 초안 경계 · 채점 질문 글을 테스트로 고정
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · deferred by ship-check
- evidence: tests/live_check.py:1272 — `self.popular < self.limits.popular_drafts_min` 을 `<=` 로 바꾼 변이가 초록(ship-check 감사의 사본 실행: 전체 스위트 660개 OK · ship-check 본인의 사본 실행: live-check 두 모듈 147개 OK, rc=0). 넓힌 창이 닫혀 있어야 하는 유일한 테스트 tests/test_live_check.py:2135 가 `popular_drafts_min=0` 으로 돌아 "최소 3 에 정확히 닿음" 을 아무 테스트도 재지 않음(.adw/guard-matrix.md Guard B 첫 줄도 `min 0`). tests/live_check.py:380 `if 2 * grade_errors > graded:` 를 `> graded + 1` 로 바꾼 변이도 147개 초록 — 경계 표본이 4/10 · 5/10 · 6/10 짝수뿐. tests/live_check.py:136-139 의 GRADE_SYSTEM 질문 4 · 5 글은 테스트가 기호로만 비교해 바꿔 써도 초록(.adw/ship-report.md § Test integrity)
- direction: tests/test_live_check.py 에 ① 기본 `popular_drafts_min`(3)에서 운영 창이 `target_drafts` 와 인기 댓글 초안 정확히 3 에 닿으면 `list(result["windows"]) == ["operation"]` 인 실행 테스트 ② `ten_drafts` 꼴의 홀수 초안 결과(오류 6/11 → `채점 막힘(오류 6/11)`, 오류 5/11 → `go`)를 VerdictTest 와 G1_CASES 에 ③ GRADE_SYSTEM 의 질문 4 · 5 줄과 닫는 줄을 글자 그대로 단언하는 행을 더한다 ④ (2026-10-14 6C HC1 인터뷰 질문 1 A 가 더함) `test_near_miss_tool_block` 의 "정하지 않은 표본 — … 트래커 줄이 없어" 주석을 "빨강(거절) — 트래커 6C 결정 '도구 답은 … 글자 그대로 같을 때만'" 으로 고친다(단언은 그대로) — 코드 변경 없음, 지금 코드는 넷 다 기대대로
- touches: tests/test_live_check.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-078 — 채점 막힘 분모(파싱된 초안만) · 올바른 깊은 중첩 JSON · dict 아닌 도구 입력 · 이름이 다른 도구 블록 + 글 JSON 을 테스트로 고정
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · deferred by ship-check (2nd run, HEAD 5f9392d)
- evidence: tests/live_check.py:379 `graded = len(graded_drafts)` 를 파싱 안 된 초안까지 센 수로 바꾼 변이가 live-check 두 모듈 147개 초록(ship-check 본인의 사본 실행 rc=0, 감사 5 의 전체 스위트 660개 OK) — 계약 docs/contracts.md:1269 의 "초안(`parsed` 인 초안)" 을 잠그는 테스트가 없고 .adw/guard-matrix.md Guard A 에도 파싱 안 된 초안이 섞인 행이 없음. tests/live_check.py:860 의 `RecursionError` 를 잡지 않게 한 변이와 :899 `json_read` 를 `data is not None` 으로 바꾼 변이도 전체 스위트 초록(감사 5) — tests/test_live_check.py:2790 "깊은 중첩" 표본 `"{"*5000+"}"*5000` 은 올바르지 않은 JSON 이라 `JSONDecodeError` 길만 타고, dict 아닌 도구 `input` 을 보내는 테스트가 없음. 트래커 :501(HC1 결정)의 "그 블록을 지나쳐 글 블록의 JSON 을 읽는다" 갈래는 코드가 하지만(감사 1 탐침 `near-miss block + text JSON -> 받음 · tool_used False · json_read True`) 테스트 표본이 없음(.adw/ship-report.md § Test integrity)
- direction: tests/test_live_check.py 에 ① 판 2 결과에 파싱된 초안 10개(오류 6) + 파싱 안 된 초안 4개 → `채점 막힘(오류 6/10)` 인 VerdictTest 행 ② `'{"a":' * 100000 + '1' + '}' * 100000` 처럼 올바른 깊은 중첩 글 → `json_read` false · `응답 모양` 행 ③ `input` 이 목록 · 글자 · None 인 `record_grade` 도구 블록 → `tool_used` true · `json_read` false · 두 몫 `응답 모양` 행 ④ `Record_grade` · `TOOL_USE` 블록 + 맞는 다섯 키 JSON 글 블록 → 두 몫 받음 · `tool_used` false · `json_read` true 행을 더한다 — 코드 변경 없음, 지금 코드는 넷 다 기대대로(S-077 과 같은 파일이라 한 스윕에서 함께 고쳐도 됨)
- touches: tests/test_live_check.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-079 — README 9단계의 cp 와 git restore 를 && 로 묶어 복사 실패 때 새 결과를 지키기
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 두 줄을 `cp … && git restore …` 한 줄로 묶고 실패하면 restore 하지 않는다는 문장 하나를 더한다
- touches: docs/live-check/README.md
- base: adw/phase-6c-live-check-grader-fix
- phase: plans/interview-marketing-agent.md#phase-6c
- status: escalated
- attempts: 0 · last failure: entry criterion fails on inspection (스윕 20261014-224055-adw/smoke-sweep-s079-s082)

### S-080 — README 5단계의 "함께 나오면 채점 호출 자체가 실패" 를 오류 줄에 claude/grade 가 있을 때로 좁히기
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 함께 나오면 재지 못함 오류 줄부터 보되 claude·grade 줄이 없으면 원인은 채점 답 모양 줄이라고 고쳐 쓴다
- touches: docs/live-check/README.md
- base: adw/phase-6c-live-check-grader-fix
- phase: plans/interview-marketing-agent.md#phase-6c
- status: escalated
- attempts: 0 · last failure: entry criterion fails on inspection (스윕 20261014-224055-adw/smoke-sweep-s079-s082)

### S-081 — 넓힌 창 조건의 popular == 최소 경계 · 채점 막힘 홀수 초안 경계 · GRADE_SYSTEM 질문 4·5 글을 테스트로 고정
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 기본 최소 3 에 정확히 닿는 운영 창 실행(windows == ["operation"]) · 6/11 stop 과 5/11 go 픽스처 · GRADE_SYSTEM 글자 단언을 더하고 near-miss 주석을 HC1 결정으로 고친다, 코드 변경 없음
- touches: tests/test_live_check.py
- base: adw/phase-6c-live-check-grader-fix
- phase: plans/interview-marketing-agent.md#phase-6c
- status: escalated
- attempts: 0 · last failure: entry criterion fails on inspection (스윕 20261014-224055-adw/smoke-sweep-s079-s082)

### S-082 — 채점 막힘 분모(파싱된 초안만) · 올바른 깊은 중첩 JSON · dict 아닌 도구 입력 · 이름이 다른 도구 블록 + 글 JSON 을 테스트로 고정
- source: cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · tracker plans/interview-marketing-agent.md#phase-6c · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 파싱 안 된 초안이 섞인 판 2 VerdictTest 행 · RecursionError 를 타는 올바른 깊은 중첩 표본 · 목록/글자/None 도구 input 행 · near-miss 블록 + 맞는 JSON 글 블록 행을 더한다, 코드 변경 없음
- touches: tests/test_live_check.py
- base: adw/phase-6c-live-check-grader-fix
- phase: plans/interview-marketing-agent.md#phase-6c
- status: escalated
- attempts: 0 · last failure: entry criterion fails on inspection (스윕 20261014-224055-adw/smoke-sweep-s079-s082)

### S-083 — 계약 '결과 반영' 절과 README 4단계의 "사람 칸의 다른 값은 빨강을 만들지 않음" 을 topic_human 까지 좁히기
- source: cycle 20261014-225050-adw/phase-6d-live-check-reapply · tracker plans/interview-marketing-agent.md#phase-6d · deferred by ship-check
- evidence: docs/contracts.md:1349-1350 · docs/live-check/README.md:19 — 6D 가 topic_human 을 기록 줄에서 읽기 시작해(tests/test_live_check_applied.py:425-458) 거짓이 됨; 커밋 결과의 일치 영상 하나에 topic_human "아님" → AccuracyRecordTest.test_accuracy_record_is_in_contract 빨강(`… 일치 7 중 정답 아님 1 · … · 사람 칸 1/18`)
- direction: 두 문장에 topic_human 의 연애 · 아님 도 기록을 바꿔 이 모듈을 빨강으로 만든다고 적고("다른 값" 은 human 의 ok · bad 밖, topic_human 의 연애 · 아님 밖 글), 커밋 결과에 topic_human 하나를 심으면 빨강 · 엉뚱한 글이면 그대로인 짝 테스트를 더한다 — 코드 변경 없음
- touches: docs/contracts.md, docs/live-check/README.md, tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-084 — best_setting 동점 규칙: 지금 noul_no_max 를 명시적으로 먼저 두고 같은 거리 · 5e-7 근접 후보를 테스트로 고정
- source: cycle 20261014-225050-adw/phase-6d-live-check-reapply · tracker plans/interview-marketing-agent.md#phase-6d · deferred by ship-check
- evidence: tests/live_check.py:284-287 — round(abs(value - base.noul_no_max), 6) 이 지금 값보다 5e-7 안쪽으로 작은 noul 을 거리 0 으로 묶어 앞세움(setting_rows({"noul": 0.1999996}) → noul_no_max 0.1999996 · 맞음 22 = 지금 값 0.2 의 22); docs/contracts.md:1308 "거리가 같으면 작은 쪽" 은 표본 없음(정렬 키 value → -value 로 바꿔도 BestSettingTest · RecountTest · CommittedResultTest 초록)
- direction: no_ceilings 정렬 키 앞에 value != base.noul_no_max 를 두고, BestSettingTest 에 지금 값에서 같은 거리의 두 후보(맞음이 같으면 작은 쪽)와 0.1999996 표본을 더한다 — best_correct 의 개수는 바뀌지 않음, 계약 10절대로 live-check 실행기 변이를 다시 돌림
- touches: tests/live_check.py, tests/test_live_check.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-085 — check_floor 의 "내리지 않음" 다리(max(value, raised))를 테스트로 고정
- source: cycle 20261014-225050-adw/phase-6d-live-check-reapply · tracker plans/interview-marketing-agent.md#phase-6d · deferred by ship-check
- evidence: tests/test_live_check_applied.py:361 — return max(value, raised) → return raised 로 바꿔도 전체 698 초록(ship-check 변이 점검 (d)); docs/contracts.md:951 "통과선은 올리기만 하고 내리지 않습니다" 를 따로 재는 표본 없음
- direction: RecountTest 에 정답 bad · self_check_pass True 인데 가장 낮은 비교 점수 + MARGIN 이 지금 통과선보다 낮은 가짜 초안을 더해 check_floor 가 지금 값 그대로임을 단언한다 — 코드 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-086 — stored_verdict_mismatches 의 예시 행 다리를 테스트로 고정
- source: cycle 20261014-225050-adw/phase-6d-live-check-reapply · tracker plans/interview-marketing-agent.md#phase-6d · deferred by ship-check
- evidence: tests/test_live_check_applied.py:128 — 예시 행을 다시 판정하는 고리를 통째로 지워도 전체 698 초록(ship-check 3차 변이 점검 b3); RecountTest.test_lowered_recorded_floors_are_caught 의 가짜는 영상 · 초안 다리만 빨강으로 만들고, CommittedResultTest.test_stored_verdicts_follow_recorded_floors 는 `[]` 만 단언함; docs/contracts.md:1336-1338 "결과의 판정 · `self_check_pass` 칸을 다시 판정한 값과 같아야 합니다" 의 예시 행 몫을 재는 표본 없음 · guard-matrix G5 에 예시 행 편집 줄 없음
- direction: RecountTest 에 기록 하한을 내렸을 때 예시 행 하나만 판정이 바뀌는 가짜(영상 · 초안은 그대로)를 더해 `["accuracy.ko[i] hold -> yes"]` 꼴을 단언한다 — 코드 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 1 · last failure: reverted f01e433 — own check red (스윕 20261015-081303-adw/smoke-sweep-s083-s087)
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-087 — check_floor 의 정확히 1.0 경계와 todo_line 의 모든 창 셈을 테스트로 고정
- source: cycle 20261014-225050-adw/phase-6d-live-check-reapply · tracker plans/interview-marketing-agent.md#phase-6d · deferred by ship-check
- evidence: tests/test_live_check_applied.py:359 — `raised > 1` → `raised >= 1` 로 바꿔도 모듈 52 · 185 초록(ship-check 3차 변이 점검 a2 · 감사 N3); docs/contracts.md:953 "그 값이 1 을 넘으면" 은 1.0 을 막지 않고 config 도 1.0 을 받음(src/agent/config.py:313); tests/test_live_check_applied.py:561 — `task_counts(result, None)` → `task_counts(result, "operation")` 도 초록(변이 x1, 커밋 결과에 넓힌 창 없음)
- direction: RecountTest 에 가장 낮은 비교 점수 0.95 인 막을 초안 하나로 check_floor == 1.0(None 아님)을 단언하고, 넓힌 창 초안이 있는 가짜로 todo_line 의 ⓐ · ⓑ · ⓒ 분모가 두 창의 합임을 단언한다 — 코드 변경 없음
- touches: tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-088 — 문장 틀 검사의 '연애사주' 빼기 경계(앞 끝 · 뒤 끝)를 테스트로 고정
- source: cycle 20261015-091934-adw/phase-6e-comment-quality-fix · tracker plans/interview-marketing-agent.md#phase-6e · deferred by ship-check
- evidence: src/agent/writer.py:212 — `covered.update(range(found, found + len(word)))` 의 뒤 끝을 한 글자 당긴 변이(`found + len(word) - 1`)와 앞 끝을 한 글자 미룬 변이(`found + 1`)가 둘 다 스위트 744 개 초록(ship-check 변이 점검, git archive 스크래치 사본 · 감사 5 F1). 뒤 끝 변이에서 "저도 예전에 연애사주를 봤을 때 서로 맞는다고 했어요" / "그때 친구랑 연애사주를 봤을 때 서운했던 마음이 풀렸어요" 가 `주를봤을때서` 로 걸리고, 앞 끝 변이에서 "오늘 정말 설레는연애사주 이야기" / "어제 정말 설레는연애사주 덕분" 이 `정말설레는연` 으로 걸림 — 지금 코드는 두 쌍 모두 None. 계약 L964 "'연애사주'에 걸친 조각은 문장 틀로 세지 않습니다" 의 짝 test_required_word_pieces_are_not_frames 가 두 끝을 재지 않음
- direction: tests/test_writer.py 의 CheckTest.test_required_word_pieces_are_not_frames 에 위 두 쌍(낱말 + 뒤 다섯 글자 공유 · 앞 다섯 글자 + 낱말 공유)이 양쪽 방향 모두 shared_frame None 인 행을 더한다 — 코드 변경 없음
- touches: tests/test_writer.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-089 — 실행기 결과의 빈 사람 칸 `skip_human` 을 테스트로 고정
- source: cycle 20261015-091934-adw/phase-6e-comment-quality-fix · tracker plans/interview-marketing-agent.md#phase-6e · deferred by ship-check
- evidence: tests/live_check.py:1426 — `"skip_human": ""` 를 `"skip_human": "정당"` 으로 바꾼 변이가 스위트 744 개 초록(ship-check 변이 점검 · 감사 1 B1). 형제 칸 `topic_human` 의 같은 변이는 test_every_classified_video_is_topic_graded_once 가 잡음. test_new_video_cells_hold_no_outside_text 는 SKIP_CELLS[:4] 만 봄. 트래커 6E 질문 3 A "빈 사람 칸을 함께 둔다(사람 칸이 있으면 그것이 정답)"
- direction: tests/test_live_check.py 의 SelfSkipRecordTest(예: test_skip_grade_records_true_false_error)에서 결과 파일의 모든 영상이 `skip_human == ""` 인지 단언한다 — 코드 변경 없음
- touches: tests/test_live_check.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-090 — 대조표 짝 테스트 칸이 `tests/test_*.py::test_*` 모양만 받게
- source: cycle 20261015-091934-adw/phase-6e-comment-quality-fix · tracker plans/interview-marketing-agent.md#phase-6e · deferred by ship-check
- evidence: tests/test_task_table.py:102-117 `_test_exists` — 그 파일 안의 아무 함수면 받음: ④-4 짝 테스트를 `src/agent/writer.py::write_comment` · `tests/test_writer.py::reply`(도우미) · `tests/test_task_table.py::table_problems` 로 바꿔도 table_problems 가 [](ship-check 재현 · 감사 3 B2). 트래커 6E 질문 1 A "짝 테스트가 테스트 파일에 실제로 있는지 본다" → 빨강 표본(헌법 12조), 계획 결정 7 "pair tests `tests/<file>.py::<test>`", 계약 docs/contracts.md:1025-1026. 지금 표의 짝 테스트 이름 19 개는 모두 `tests/test_[a-z0-9_]+\.py::test_[A-Za-z0-9_]+` 모양(ship-check 확인)
- direction: `_test_exists` 가 경로 `tests/test_*.py` 와 `test_` 로 시작하는 함수 이름을 요구하게 하고, TaskTableTest 에 위 세 모양이 빨강인 표본을 더한다 — 지금 표는 그대로 초록
- touches: tests/test_task_table.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-091 — 계약 L1021(프롬프트 원문은 writer.py 맨 위에만)의 짝을 스위트 테스트로 옮기기
- source: cycle 20261015-091934-adw/phase-6e-comment-quality-fix · tracker plans/interview-marketing-agent.md#phase-6e · deferred by ship-check
- evidence: docs/contracts.md:1021 — 이 diff 가 고친 '에만' 약속 줄인데 계획 `## Test plan` 에 짝이 없고(.adw/plan.md:796-813), verify-plan 이 `.adw/verify.sh` V16 으로만 잼(.adw/verify-plan.md:214 `Promise: L1021 — V16`). 헌법 9조 plan 줄 "The test lives in the suite, never only in `.adw/verify.sh`" (감사 1 B2). V16 은 지금 초록: `prompt originals: 6 names before the first def/class (line 124) · … copies elsewhere 0 · copies inside writer bodies 0 · problems 0`
- direction: tests/test_writer.py 에 V16 과 같은 판정 — `SYSTEM_PROMPT` · `USER_INSTRUCTION` · `REWRITE_PROMPT` · `WRITE_TOOL` · `CHECK_QUESTIONS` · `CHECK_LABELS` 가 첫 def/class 앞에서 한 번씩 정해지고, 다른 `src/` 모듈과 writer 함수 본문에 그 15글자 이상 줄 · 질문의 복사본이 없음 — 을 하는 스위트 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_writer.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-092 — 낡은 docstring 두 곳: 작성 테스트 머리말의 코드 검사 목록 · `_VideoRound` 의 영상 한 바퀴 단계
- source: cycle 20261015-091934-adw/phase-6e-comment-quality-fix · tracker plans/interview-marketing-agent.md#phase-6e · deferred by ship-check
- evidence: tests/test_writer.py:1 "코드 검사(글자 수 · 링크 · 반복)" — 6E 가 넷째 검사 문장 틀(`shared_frame`)을 더함(.adw/verify-plan.md § Out of scope RISK · 감사 3 N9); tests/live_check.py:1288 `_VideoRound` docstring 의 단계 목록("… 댓글 작성 → 초안마다 채점")에 스스로 건너뛴 영상의 재료 채점(`_grade_skip`) 이 없음(감사 3 N12)
- direction: 두 docstring 에 '문장 틀' 과 '스스로 건너뛴 영상은 재료 채점 한 번' 을 더한다 — 동작 변경 없음
- touches: tests/test_writer.py, tests/live_check.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-093 — 작성기가 Claude Sonnet 5.5 에 도구를 강제해 작성 호출이 모두 400
- source: human run tests.live_check 2026-10-15T08:20:33Z (Phase 6F 사람 실행) · tracker plans/interview-marketing-agent.md#phase-6e · deferred by smoke-triage
- evidence: src/agent/writer.py:449 `tool_choice={"type": "tool", "name": WRITE_TOOL["name"]}` — 그 실행의 summary.md "오류: claude/write BadRequestError 400 ×15", 초안 0 (main 에 커밋 안 함); Claude API 는 Sonnet 5.5 · Opus 5.5 · Fable 5.1 에서 `tool_choice` 의 `tool` · `any` 를 400 으로 거절(`tool_choice: type "tool" and "any" are not supported for this model.`) — 같은 실행의 채점(tests/live_check.py:1146, claude-haiku-5-5)은 Haiku 5.5 가 강제를 받아 오류 0, 모델 확인(도구 없는 1토큰 호출)은 accepted 라 못 잡음; 운영 흐름(Phase 7)도 같은 작성기라 녹화에서 댓글 0개
- direction: 작성 호출을 `tool_choice={"type": "auto"}` 로, `WRITE_TOOL` 에 `"strict": True`(스키마는 이미 `additionalProperties: false`); 도구 없이 글로 답하면 지금처럼 '답을 읽을 수 없습니다' → 한 번 다시 쓰기; 다시 쓰기 차례(`_rewrite_turns`)는 첫 답의 content 블록을 고치지 않고 그대로 되돌려 붙임(Sonnet 5.5 는 생각 블록이 늘 켜져 있고 같은 대화에 그대로 돌려받아야 함 — 지금은 tool_use 블록 하나만 붙임); 계약 '댓글 작성' 절의 `tool_choice` 문장(docs/contracts.md:911-916)을 맞추고, 가짜 Claude 가 받은 요청의 `tool_choice` 가 `auto` · `strict` 가 참임과 생각 블록이 든 첫 답의 다시 쓰기 차례가 그 블록을 그대로 담음을 테스트로 잠금; 채점기(Haiku)의 강제는 범위 밖(채점 모델을 Sonnet · Opus 5.5 로 바꾸면 같은 400)
- touches: src/agent/writer.py, tests/test_writer.py, docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-094 — 게시 단계의 크롬 연결 끊기(`session.close()`)가 터져도 게시 자신의 결과 · Ctrl-C 가 이기게
- source: cycle 20261015-154340-adw/phase-7-pipeline-rules · tracker plans/interview-marketing-agent.md#phase-7 · deferred by ship-check
- evidence: src/agent/run.py:436-449 (Pipeline › _post) — `finally: session.close()` 를 감싸지 않음, 실제 `ChromeSession.close()` 는 `playwright.stop()` 을 그대로 부름(src/agent/chrome.py:290-296). ship-check 재현: post_video 가 KeyboardInterrupt 를 내고 close() 가 RuntimeError 를 내면 `C2 KeyboardInterrupt REPLACED by RuntimeError` — 울타리(`except Exception`)가 받아 `ERROR where=run.post` 로 남기고 에이전트가 계속 돎(계약 docs/contracts.md:1501 "BaseException 은 그대로 올라가 STOP reason=interrupted(종료 코드 130)" 와 어긋남). 성공한 게시도 close() 가 터지면 ERROR 한 줄 · CYCLE errors 1. poster.py 의 `_close_quietly`(poster.py:329-335)는 같은 경우를 이미 삼킴. 진입 기준: 정리 호출만 감쌈 — 가드 · `decide_post` · `live` · 탭 함수 고르기(`if record.video_id not in allowed:`)는 건드리지 않음
- direction: `finally:` 안의 `session.close()` 를 poster `_close_quietly` 와 같은 꼴(`try: … except Exception: pass`)로 감싸고, tests/test_run.py 에 두 테스트 — close() 가 터져도 성공한 게시는 ERROR 없이 posted · `CYCLE errors=0`, post_video 의 KeyboardInterrupt 는 close() 가 터져도 그대로 올라감 — 를 더한다
- touches: src/agent/run.py, tests/test_run.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-095 — 시작 때 저장소 · 쿼터 장부 파일을 못 읽으면(OSError) 계약대로 종료 코드 2 와 `ERROR where=store`
- source: cycle 20261015-154340-adw/phase-7-pipeline-rules · tracker plans/interview-marketing-agent.md#phase-7 · deferred by ship-check
- evidence: src/agent/run.py:492-496 `except StoreError` · :551 `except (EnvError, QuotaError, ImportError, ValueError)` — `Store._load`(store.py:57)와 `QuotaLedger._load`(youtube.py:153)는 디코드 오류만 감싸, 권한 거부 · 폴더 같은 OSError 가 빠져나감. ship-check 재현(`data/videos.json` 이 폴더): `C1 run_agent ESCAPED IsADirectoryError | log exists: False` — traceback · 종료 코드 1 · 로그 없음. 계약 docs/contracts.md:1464 "SDK · 비밀 값 · 쿼터 장부 · 설정 · 저장소를 쓸 수 없으면 종료 코드 2 … 저장소는 ERROR where=store 도 남김". 짝 테스트가 test_missing_sdk_exits_2 하나뿐이라 감사 변이(`except StoreError` → `except ZeroDivisionError`, main 튜플에서 QuotaError · ValueError 빼기)가 모두 스위트를 통과함
- direction: run_agent 의 저장소 열기를 `except (StoreError, OSError)` 로, main 의 connect_real 감싸기 튜플에 `OSError` 를 더하고, tests/test_run.py 에 깨진 저장소(StoreError) · 못 읽는 저장소(OSError) · 믿을 수 없는 쿼터 장부(QuotaError) · 못 읽는 쿼터 장부(OSError) → 종료 코드 2, traceback 없음(저장소는 `ERROR where=store` 한 줄) 테스트를 더한다
- touches: src/agent/run.py, tests/test_run.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-096 — 표본 하나 · 보류가 `too_old` 보다 먼저라는 차례를 다시 지키기(test_single_sample_holds_even_when_other_conditions_fail)
- source: cycle 20261015-154340-adw/phase-7-pipeline-rules · tracker plans/interview-marketing-agent.md#phase-7 · deferred by ship-check
- evidence: tests/test_trigger.py:58-60 — 2단계가 `published_at=T0 + 20 * H` 로 고쳐, 판정 시각 `20 * H` 에서 나이 0 이 되어 too_old 가 더는 함께 걸리지 않음. ship-check 재현: judge_trigger 의 `if pair is None:` 앞에 `if pair is None and <나이> > max_age_hours: return too_old` 를 심으면 HEAD 스위트 `Ran 821 tests … OK (skipped=3)`, 기준 eb65fc2 의 같은 테스트는 FAILED. 트래커 Phase 7 질문 5 A "판정 차례는 그대로"
- direction: 나이 0 표본은 두고 판정 시각만 12시간 넘게 뒤로 — 예: `video((2 * H, 6000), published_at=T0 + 2 * H)` 를 `20 * H` 에 판정해 `("hold", "too_few_samples")`(감사가 HEAD 초록 · 위 변이 빨강을 확인) — 코드 변경 없음
- touches: tests/test_trigger.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-097 — 운영의 자체 검사 연결(`jev_self_check(services.ask, …)`)을 스위트 테스트로 잠그기
- source: cycle 20261015-154340-adw/phase-7-pipeline-rules · tracker plans/interview-marketing-agent.md#phase-7 · deferred by ship-check
- evidence: src/agent/run.py:266 `check = jev_self_check(self._services.ask, config.classifier.model)` — 트래커 Phase 7 진입점 ⑤ "자체 검사 jev 어댑터를 src/ 로 옮겨 운영이 부름". ship-check 재현: 이 줄을 늘 통과하는 람다(`{n: 0.1 if n == "reads_like_ad" else 0.9}`)로 바꿔도 `Ran 821 tests … OK (skipped=3)` — 게시 전 품질 검사가 운영에서 빠져도 스위트가 모름. tests/test_run.py 의 FakeJevAsk 는 `("check", id)` 호출을 적지만 어떤 테스트도 보지 않음
- direction: tests/test_run.py 에 — 가짜 jev 가 자체 검사에서 reads_like_ad 를 높게 답하면 그 영상은 작성기의 `SKIP` 으로 끝나 `record.comment` 가 생기지 않고 게시가 없음 · 쓴 영상마다 jev 에 `("check", <ID>)` 호출이 감 — 을 보는 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_run.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-098 — run.py 의 덜 잠긴 줄 셋을 테스트로: 울타리 뒤 판별 저장 · 이유 200자와 공백 접기 · main 의 echo 연결
- source: cycle 20261015-154340-adw/phase-7-pipeline-rules · tracker plans/interview-marketing-agent.md#phase-7 · deferred by ship-check
- evidence: (a) src/agent/run.py:331 `_classify` 의 `self._store.put(record)` 를 지워도 스위트 OK — 타이밍 단계가 터지면 판별이 저장되지 않아 다음 주기에 jev 를 다시 부름(계약 "yes · no · 판정 보류는 저장하고 다시 묻지 않습니다"); (b) :137 `[:REASON_MAX]` 와 공백 접기를 지워도 스위트 OK(계약 docs/contracts.md:1500 "메시지 200자까지"); (c) :559 `echo=echo_stream(sys.stdout)` 을 `sys.stdout` 이나 `None` 으로 바꿔도 스위트 OK — 실제 프로세스 검사 `.adw/verify.sh` V9 (d) 만 잡음(헌법 9: 시험은 스위트에)
- direction: tests/test_run.py 에 — 타이밍 단계가 영상 A 에서 터진 뒤 다음 주기에 A 의 판별을 다시 묻지 않음(jev 분류 호출 1번, 저장된 classification 있음) · 250자 · 줄바꿈 섞인 메시지의 울타리 이유가 `<종류>: ` + 200자 한 줄 · main 이 run_agent 에 넘기는 echo 가 `errors="backslashreplace"` 스트림 — 세 테스트를 더한다 — 코드 변경 없음
- touches: tests/test_run.py
- status: resolved
- attempts: 1 · last failure: reverted f569184 — own check red (스윕 20261015-185700-adw/smoke-sweep-s094-s098)
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-099 — 계약 2절의 설정 거절 문장을 코드대로 좁히기(명단 밖 영상은 가드의 이유 그대로)
- source: cycle 20261015-154340-adw/phase-7-pipeline-rules · tracker plans/interview-marketing-agent.md#phase-7 · deferred by ship-check
- evidence: docs/contracts.md:140 "그동안 게시는 명단 영상까지 모두 크롬 없이 테스트 저장(`reason=config_rejected`)" — 명단 밖 영상은 `not_in_allowlist` 로 저장됨(src/agent/run.py:461, tests/test_run.py::TestConfigRejected::test_rejected_out_of_list_keeps_guard_reason). 같은 계약 '실행 진입점 — run.py (Phase 7)' 절의 '설정 거절' 줄은 정확함
- direction: 괄호를 "(명단 영상은 `reason=config_rejected`, 명단 밖 영상은 가드의 이유)" 처럼 좁힌다 — Promise 짝 줄의 머리 "하지 않습니다 — 그동안 게시는 명단 영상까지" 와 짝 테스트는 그대로, 코드 변경 없음
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-100 — 리허설 테스트 빈칸: `detail` 200자 자르기 두 곳 · 리허설 뒤 게시 테스트의 첫 결과
- source: cycle 20261015-182947-adw/phase-7f-chrome-rehearsal · tracker plans/interview-marketing-agent.md#phase-7f · deferred by ship-check
- evidence: src/agent/poster.py:311 `shown_url[:DETAIL_MAX]` 와 src/agent/poster.py:320 `…[:DETAIL_MAX]` 를 지워도 `tests.test_poster tests.test_chrome` 93개가 초록(ship-check 감사 5 손 변이 g · h, 각각 rc=0 `OK`) — 테스트 어디에도 `DETAIL_MAX` 가 없음; tests/test_poster.py:299 `test_live_post_follows_rehearsal` 은 첫 실행(리허설)의 결과를 단언하지 않음(감사 1 메모 3)
- direction: 테스트만 더함 — 다시 확인이 어긋난 화면의 주소가 200자를 넘을 때 `ERROR` 줄 `detail` 이 200자인지, 긴 원인의 글 지우기 실패에서 `rehearsed` 줄 `detail` 이 200자인지, `test_live_post_follows_rehearsal` 의 첫 결과가 `PostOutcome(VID, "test", "rehearsed", "dry_run", shot)` 인지 단언; 코드 · 계약 변경 없음
- touches: tests/test_poster.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-101 — README 7단계 사람 칸 안내가 세 칸(`claude_grade`)만 보라고 함 — 통과선 셈의 정답은 이제 다섯 칸
- source: cycle 20261015-175919-adw/phase-6f-live-check-reapply-after-fix · tracker plans/interview-marketing-agent.md#phase-6f · deferred by ship-check
- evidence: docs/live-check/README.md:24 "`claude_grade`(`ok` / `bad`)를 보고, 동의하지 않으면 그 초안의 `"human": ""` 을 … 고칩니다" — `100b615` 뒤 사람 칸이 빈 초안의 정답은 다섯 칸(tests/test_live_check_applied.py:282-295 `claude_answer`: `claude_grade` + `task_quality` ⓐ · ⓑ, 트래커 6F 결정 줄 716). 커밋된 결과에서 `claude_grade` ok 인데 다섯 칸 정답 bad 인 초안 3(om-TAoBO0Rc 시도 1 · dM2hFpUH6qg 시도 2 · qAgY7WxXWs4 시도 1); README 대로 om-TAoBO0Rc 시도 1 에 동의해 사람 칸을 비우면 `check_floor` 0.79(지금 0.7) — ship-check 감사 3, 탐침으로 확인
- direction: README 7단계 초안 줄을 "Claude 채점 다섯 칸(`claude_grade` 와 `task_quality` 의 ⓐ `concern_is_love_worry` · ⓑ `saju_story_fits`)을 보고, 그 정답에 동의하지 않으면 …" 으로 고친다 — 코드 · 결과 파일 · 계약 변경 없음
- touches: docs/live-check/README.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-102 — 테스트 두 곳 다지기: 늘 참인 단언 하나 · 동점 표본이 사전 차례와 `CHECK_QUESTIONS` 차례를 못 가름
- source: cycle 20261015-175919-adw/phase-6f-live-check-reapply-after-fix · tracker plans/interview-marketing-agent.md#phase-6f · deferred by ship-check
- evidence: tests/test_live_check.py:4272 `assertFalse(any(key in video …))` 는 바로 위 루프가 그 키를 지운 뒤라 늘 참(ship-check 감사 5 F1); tests/test_live_check_applied.py:1706 `test_lowest_question_samples` 의 동점 표본(`mentions_scene` · `saju_story_fits` 0.7)은 `five()` 가 키를 `CHECK_QUESTIONS` 차례로 넣어, `scores` 를 도는 구현도 통과(감사 3 N3 탐침 `naive on test tie: mentions_scene`)
- direction: 늘 참인 단언을 지우거나 `stored` 에 스스로 건너뜀 칸이 있음을 단언으로 바꾸고, `test_lowest_question_samples` 에 키 차례가 `CHECK_QUESTIONS` 와 다른 동점 표본 하나(예: `saju_story_fits` 를 먼저 넣은 사전)를 더한다 — 동작 변경 없음
- touches: tests/test_live_check.py, tests/test_live_check_applied.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-103 — 크롬 주소 판정의 `127.0.0.1` 점을 잠그는 빨강 표본 하나
- source: cycle 20261015-211343-adw/phase-7g-chrome-url-sample-gap · tracker plans/interview-marketing-agent.md#phase-7g · deferred by ship-check
- evidence: src/agent/config.py:124 `_LOOPBACK_URL` 의 `127\.0\.0\.1` 을 `127.0.0.1`(점 이스케이프 없음)로 바꿔도 전체 스위트 887개 `OK`(ship-check 감사 5 손 변이 M13, 임시 복사본) — 그 판본은 `http://127-0-0-1:9222` · `http://127x0y0z1:9222`(DNS 로 찾는 다른 호스트 이름)를 받음(HEAD 는 둘 다 거절, 메모리 확인); tests/test_config.py:908 `LoopbackUrlTest.RED` 에 점을 다른 글자로 바꾼 표본이 없음
- direction: `LoopbackUrlTest.RED` 에 `"http://127-0-0-1:9222"` 를 더하고 한 줄 주석으로 닮은 꼴 종류(점 바꿈 → 다른 호스트 이름)와 색의 근거(트래커 Phase 7G 질문 2 A "다른 호스트 이름")를 적는다 — 코드 · 계약 변경 없음. (2026-10-16 7G 출하 전 사람 확인 인터뷰 · 슬롯 7g HC1 질문 1 A 로 보탬) 같은 `RED` 묶음에 사람이 빨강으로 정한 일곱도 더한다 — `"https://localhost:9222"` · `"http://LOCALHOST:9222"` · `"http://127.0.0.2:9222"` · `"http://localhost"` · `"http://ｌｏｃａｌｈｏｓｔ:9222"`(전각) · `"http://localhost:123456"` · `"http://localhost:9222//"`, 줄마다 주석에 꼴 종류와 근거(트래커 Phase 7G Decisions 의 "HC1 질문 1 A" 줄 — 꼴마다 이유가 적혀 있음). 이 일곱은 ship-check 손 변이 `http://` → `https?://` · `[0-9]{1,5}` → `[0-9]+` · `/?` → `/*`(셋 다 887 `OK` 로 살아남음, `.adw/ship-report.md` Test integrity 표)를 잡는다 — 더한 뒤 각 변이가 빨강인지 임시 복사본에서 확인한다
- touches: tests/test_config.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-104 — 최소 간격 폴백 길에서 건너뛴 더 큰 기록을 쓰지 않음을 잠그는 테스트
- source: cycle 20261015-211343-adw/phase-7g-chrome-url-sample-gap · tracker plans/interview-marketing-agent.md#phase-7g · deferred by ship-check
- evidence: src/agent/trigger.py:52 `_first_pair` 의 `newest` 고르는 열쇠를 `(sample.count, _utc(sample.at))` 로 바꿔도 전체 스위트 887개 `OK`(ship-check 직접 변이, 임시 복사본) — 7G 전에는 이 줄이 같은 시각 기록끼리만 닿았지만 이제 10분 안 기록끼리도 닿는다. 기록 `(1h, 1500), (1h05m, 1450)` 에서 HEAD 는 views_per_hour 1338.46(업로드 0 ↔ 최신 1450), 변이는 1500.0(건너뛴 기록을 최신으로 씀). docs/contracts.md:1148 "건너뛴 기록(최신보다 10분 안)은 판정 어디에도 쓰지 않습니다" 의 짝 테스트(`test_decrease_is_seen_on_the_measured_pair_only` · `test_skips_near_sample_and_uses_latest_far_enough`)는 10분 넘게 앞선 기록이 있는 길만 봄
- direction: tests/test_trigger.py `TestMinimumGap` 에 테스트 하나 — `video((1 * H, 1500), (1 * H + 5 * M, 1450))` 이 업로드 0 과 최신(1450)으로 재짐: `views_per_hour == 1450 * 60 / 65`, 같은 짝으로 `judge_trigger` 의 경계(`min_views_per_hour` 1338 에서 yes, 1339 에서 `too_slow`). 같은 손으로 `TestFirstSample` docstring(tests/test_trigger.py:315 "시각이 다른 기록이 하나면 …")을 "최신보다 10분 이상 앞선 기록이 없으면 …" 으로 넓힌다 — 코드 · 계약 변경 없음
- touches: tests/test_trigger.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-15 · last seen: 2026-10-15

### S-105 — 크롬 주소 판정의 포트를 ASCII 숫자로 잠그는 빨강 표본 하나(전각 숫자 포트)
- source: cycle 20261015-211343-adw/phase-7g-chrome-url-sample-gap · tracker plans/interview-marketing-agent.md#phase-7g · deferred by ship-check
- evidence: src/agent/config.py:124 `_LOOPBACK_URL` 의 `[0-9]{1,5}` 를 `\d{1,5}` 로 바꿔도 전체 스위트 887개 `OK (skipped=3)`(ship-check 2회차 감사 5 와 이 단계가 따로 확인, `.git` 없는 임시 복사본 — 건너뜀 3은 그 탓) — 그 판본은 `http://localhost:９２２２` · `http://127.0.0.1:٩٢٢٢` 를 받음(HEAD 는 둘 다 거절, 메모리 확인). 받은 주소는 파이썬 `urlsplit` 의 `.port` 가 `ValueError`, WHATWG `new URL` 이 `ERR_INVALID_URL` 이라 설정 읽기만 지나고 준비 도구 rc 2 · 게시마다 연결 실패로 늦게 터짐. tests/test_config.py:908 `LoopbackUrlTest.RED` 에 ASCII 가 아닌 숫자 포트 표본이 없고, `S-103` 의 표본 여덟은 이 변이를 잡지 못함(그중 전각은 호스트 `ｌｏｃａｌｈｏｓｔ` 뿐)
- direction: `LoopbackUrlTest.RED` 에 `"http://localhost:９２２２"`(포트 숫자만 전각)를 더하고 한 줄 주석으로 꼴 종류(포트 숫자의 전각 닮은 꼴 — 두 해석기 모두 포트로 읽지 못함)와 색의 근거(트래커 Phase 7G Decisions "HC1 질문 1 A" 의 `https` 줄 "받아도 게시 때 `chrome_unreachable`" · `:123456` 줄 "계약 2절 숫자 1–5자리")를 적는다 — 코드 · 계약 변경 없음. `S-103` 과 같은 묶음이라 한 스윕에서 함께 넣어도 된다. 더한 뒤 `\d{1,5}` 변이가 빨강인지 임시 복사본에서 확인한다
- touches: tests/test_config.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-106 — README 문제 해결의 '에이전트를 시작할 수 없습니다' 줄을 코드대로 좁히기(설정 오류는 그 문구 없이 `ERROR where=config`)
- source: cycle 20261015-211335-adw/phase-8-submission-docs · tracker plans/interview-marketing-agent.md#phase-8 · deferred by ship-check
- evidence: README.md:167 "SDK 나 키가 없거나, 설정에 오류가 있습니다" — src/agent/run.py:554-556 은 그 문구를 `connect_real` 의 EnvError · QuotaError · ImportError · ValueError · OSError 에만 찍고, 설정 오류는 src/agent/run.py:492-494 가 `ERROR where=config` 를 쓰고 그 문구 없이 종료 코드 2 로 끝남. 계약 '실행 진입점 — run.py (Phase 7)' 절 "(설정은 `ERROR where=config` … 도 남김)". ship-check 감사 1 재현: 깨진 config.yaml → rc 2 · stderr 빈 칸 · 화면에 `ERROR where=config reason="ConfigError: …"`. 틀린 문장은 Phase 8 계획 R8 줄에서 옴
- direction: 그 줄을 SDK · 키 · 쿼터 장부 문제로 좁히고, 설정 오류는 그 문구 없이 `ERROR where=config` 한 줄과 종료 코드 2 로 보인다는 줄을 더함 — 코드 · 계약 변경 없음
- touches: README.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-107 — 공개용 사본 테스트 빈칸 셋: 알려진 목록의 글자 그대로 비교 · 형식이 틀린 .env · 기본 --env
- source: cycle 20261015-211335-adw/phase-8-submission-docs · tracker plans/interview-marketing-agent.md#phase-8 · deferred by ship-check
- evidence: tests/public_copy.py:316 `if found not in known` 을 부분 일치(`any(k in found …)` · `any(found in k …)`)로 바꿔도 스위트 `Ran 938 … OK`(ship-check 감사 5 변이 M2 · M2b) — 표본이 글자 바꿈 · 대소문자뿐(tests/test_public_copy.py:313-320 · :376-380 · :515-522); tests/public_copy.py:344-345 `except EnvError` 를 건너뜀으로 바꿔도 OK(M5a — 없는 파일 표본은 :347 빈 값 갈래로 감); :438 기본 `source / ".env"` 를 지워도 OK(M5c). 계약 '공개용 사본' 절 "한 글자라도 다르면 목록 밖입니다" · "파일이 없거나 세 값이 모두 비면 이 검사가 걸리고" · "`--env`(기본: 원본의 `.env`)"
- direction: tests/test_public_copy.py 에 — 알려진 연락처 · 키 · 홈 글자에 한 글자를 덧붙인 꼴과 끝 글자를 자른 꼴이 빨강(홈은 이름 칸에서) · `이름=값` 꼴이 아닌 줄이 든 .env 로 `✗ 비밀 값`(건너뜀 아님) · `--env` · `--no-env` 없이 돌리면 가짜 원본 뿌리의 .env 값을 찾아 빨강 — 세 표본을 더함, 코드 변경 없음
- touches: tests/test_public_copy.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-108 — README 의 실행 줄을 줄마다 잠그기(맥 첫 실행 · 녹화 3단계 · 윈도우)
- source: cycle 20261015-211335-adw/phase-8-submission-docs · tracker plans/interview-marketing-agent.md#phase-8 · deferred by ship-check
- evidence: tests/test_submission_docs.py:62-64 가 `PYTHONPATH=src python3 -m agent.run --once --dry-run` 을 `assertIn` 으로만 봄 — 같은 명령이 README.md:90 과 :154 에 두 번 있어 한 줄만 틀려도 OK(ship-check 감사 5 변이 R1b · R2), 윈도우 줄 README.md:91 은 잠기지 않음. Phase 8A 가 README 줄을 옮길 예정(트래커 Phase 8A 질문 3 A)
- direction: 그 명령이 README 에 2번 이상 나오는지, 윈도우 줄이 `$env:PYTHONPATH = "src"` 와 `python -m agent.run --once --dry-run` 을 함께 갖는지 단언을 더함 — 테스트만, 코드 · 문서 변경 없음
- touches: tests/test_submission_docs.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-109 — 결과 화면 테스트 빈칸 셋: 표시 글 일곱의 글자 고정 · 리허설 줄 reason 표시 글 · 보이지 않는 U+2028 두 자
- source: cycle 20261015-211359-adw/phase-7d-run-report-html · tracker plans/interview-marketing-agent.md#phase-7d · deferred by ship-check
- evidence: src/agent/report.py:26-35 의 표시 글 일곱(`NO_POST` "게시 기록 없음" · `NO_DRAFT` "댓글 안 씀" · `OTHER` "기타 — 로그 참고" · `RESERVED` · `FAILED` · `NOT_JUDGED` · `NOT_TIMED`)이 tests/test_report.py · tests/test_run.py 에 글자로 0번 — 테스트가 상수와만 비교해 글을 바꿔도 스위트 초록이고 계약 '결과 화면' 절만 낡음(이번엔 verify 의 V22 가 잡았지만 V22 는 스위트 밖); tests/test_report.py:95-98 `rehearsal()` 이 `reason=DRY_RUN` 을 박아 :590 의 모양 갖춘 리허설 줄 reason 에 표시 글이 없음(plan Test plan 은 표시 글을 약속); tests/test_report.py:517 · :524 의 날 U+2028 두 자는 편집기 · diff 에서 안 보임(.adw/ship-report.md § Test integrity)
- direction: 테스트만 고침 — `test_listed_codes_get_labels` 처럼 표시 글(위 일곱과 `REHEARSED` · `POSTED` · `LOG_UNREADABLE`)을 계약의 글자 그대로 assertEqual 하는 표 하나 · `rehearsal()` 이 reason 을 받게 하고 :590 줄의 reason 을 `mark(...)` 으로 심어 화면에 없음을 단언 · :517 · :524 의 날 글자를 `"
"` 이스케이프로; 코드 · 계약 변경 없음
- touches: tests/test_report.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-110 — 요청 전체 상한을 테스트로 잠그기: 상한을 두 배로 늘려도 스위트가 초록
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · deferred by ship-check
- evidence: src/agent/youtube.py:214 `if not done.wait(timeout):` 을 `done.wait(2 * timeout)` 으로 바꿔도 `python3 -m unittest discover` 900개가 `OK`(ship-check 감사 5 손 변이 M2 — drip 테스트 2.079 · 2.009 · 2.007 s); tests/test_youtube.py:841-848 과 tests/test_watcher_network.py:151 이 1초 상한 둘레에 `assertLess(elapsed, 2.5)` 만 둠
- direction: 테스트만 — tests/test_youtube.py 의 머리줄 · 본문 drip 테스트와 tests/test_watcher_network.py 의 drip 테스트가 1초 상한에 거는 시간 한도를 2.5초에서 상한의 두 배보다 작은 값(예: 1.8초)으로 좁혀 두 배 상한이 빨강이 되게; 코드 · 계약 변경 없음
- touches: tests/test_youtube.py, tests/test_watcher_network.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-111 — 쿼터 장부 48시간 보관 경계를 스위트 테스트로 잠그기
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · deferred by ship-check
- evidence: tests/test_youtube.py:290-293 `test_old_entries_are_pruned_on_write` 의 씨앗(−50h · −30h · −1s)과 빠른 시계 테스트는 src/agent/youtube.py:47 `_KEEP` 이 (30h, 50h] 의 어느 값이어도 통과(ship-check 감사 5 소견 5, .adw/guard-matrix.md Coverage notes) — 48시간 경계는 verify 때의 V25 스크립트만 잼
- direction: 테스트만 — 쓰기 한 번 뒤 NOW−48h 항목은 지워지고 NOW−48h+1s 항목은 남음을 단언(V25 가 잰 경계, 계약 '쓸 때 48시간이 지난 항목은 지움'); 코드 · 계약 변경 없음
- touches: tests/test_youtube.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-112 — 조용한 서버 테스트가 일꾼 스레드를 실제로 봤는지 · 읽기마다의 timeout 값 전달을 단언하기
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · deferred by ship-check
- evidence: tests/test_youtube.py:921 은 `thread.name == "http_get"` 으로 거른 목록이 비었는지만 봐 스레드를 하나도 못 찾아도 통과(ship-check 감사 5 소견 3); HttpGetTest 를 루프백으로 옮기며 base 의 `kwargs == {"timeout": timeout}` 단언(cc80dd8 tests/test_youtube.py:754)이 빠져 src/agent/youtube.py:226 `open(request, timeout=timeout)` 은 값이 아니라 있음만 잠김(소견 2)
- direction: 테스트만 — 조용한 서버 테스트가 새 `http_get` 스레드를 적어도 하나 봤음을 단언하고, `OpenerDirector.open` 을 감싼 spy 로 `_get` 이 받은 timeout 값을 그대로 넘기는지 단언; 코드 변경 없음
- touches: tests/test_youtube.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-113 — 테스트 가짜의 '모르는 호출' · '네트워크 금지' 가드가 _call 의 예외 잡기에 삼켜지지 않게
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · deferred by ship-check
- evidence: src/agent/youtube.py:354 `except Exception as exc:` 가 테스트 가짜의 `AssertionError` 도 `YouTubeError` 로 바꿈 — tests/test_live_check.py:1951 `raise AssertionError(f"모르는 호출입니다: {endpoint}")` 와 :2008-2009 소켓 금지 가드는 tests/live_check.py:1513 · 1526 `except YouTubeError: continue` 에서 조용히 건너뛰어지고, tests/test_watcher_network.py:31 · 33 의 LoopbackFetch 가드는 :66 · :93 의 `reason.startswith("network ")` 를 그대로 통과(ship-check 감사 3 메모 6)
- direction: 테스트만 — World 의 모르는 호출 가드 · 소켓 금지 가드 · LoopbackFetch 주소 가드가 걸린 횟수를 기록하고 addCleanup 에서 0 이 아니면 실패하게; 소스 변경 없음
- touches: tests/test_live_check.py, tests/test_watcher_network.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-114 — 요청 전체 상한을 테스트로 잠그기: 상한을 두 배로 늘려도 스위트가 초록
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: drip 테스트의 시간 한도를 상한의 두 배보다 작은 값으로 좁혀 두 배 상한이 빨강이 되게, 코드 · 계약 변경 없음
- touches: tests/test_youtube.py, tests/test_watcher_network.py
- base: adw/phase-7a-watcher-network-fixes
- phase: plans/interview-marketing-agent.md#phase-7a
- status: resolved
- attempts: 0 · last failure: —

### S-115 — 쿼터 장부 48시간 보관 경계를 스위트 테스트로 잠그기
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 쓰기 한 번 뒤 NOW−48h 항목은 지워지고 NOW−48h+1s 항목은 남음을 단언, 코드 · 계약 변경 없음
- touches: tests/test_youtube.py
- base: adw/phase-7a-watcher-network-fixes
- phase: plans/interview-marketing-agent.md#phase-7a
- status: resolved
- attempts: 0 · last failure: —

### S-116 — 조용한 서버 테스트가 일꾼 스레드를 실제로 봤는지 · 읽기마다의 timeout 값 전달을 단언하기
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 새 http_get 스레드를 적어도 하나 봤음과 OpenerDirector.open 에 넘긴 timeout 이 받은 값 그대로임을 단언, 코드 변경 없음
- touches: tests/test_youtube.py
- base: adw/phase-7a-watcher-network-fixes
- phase: plans/interview-marketing-agent.md#phase-7a
- status: resolved
- attempts: 0 · last failure: —

### S-117 — 테스트 가짜의 '모르는 호출' · '네트워크 금지' 가드가 _call 의 예외 잡기에 삼켜지지 않게
- source: cycle 20261015-213331-adw/phase-7a-watcher-network-fixes · tracker plans/interview-marketing-agent.md#phase-7a · filed by smoke-file (one-pass)
- evidence: .adw/ship-report.md
- direction: 가드가 걸린 횟수를 기록하고 addCleanup 에서 0 이 아니면 실패, 소스 변경 없음
- touches: tests/test_live_check.py, tests/test_watcher_network.py
- base: adw/phase-7a-watcher-network-fixes
- phase: plans/interview-marketing-agent.md#phase-7a
- status: resolved
- attempts: 0 · last failure: —

### S-118 — 작성 단계 울타리 오류를 기억한 명단 밖 영상이 초안을 이미 저장했으면 다음 새 기록에서 게시 단계가 불리는 빈틈 막기
- source: cycle 20261016-075749-adw/phase-7c-comment-yield-variety · tracker plans/interview-marketing-agent.md#phase-7c · deferred by ship-check
- evidence: src/agent/run.py:519 (`_post` 는 `STAGE_POST` 기억만 봄) · src/agent/run.py:442-451 (`_write` 는 댓글이 있으면 `_recalled` 앞에서 돌아감) · src/agent/store.py:106-107 (`put` 이 메모리 쪽을 먼저 바꾸고 저장) — docs/contracts.md:1616 "울타리 오류는 그 단계부터 다시 부르지 않습니다". ship-check 재현(HEAD 081b9f8 사본, tests/test_run.py 가짜): 명단 밖 C 의 초안 저장이 한 번 `OSError` → 기억 `(stage_error, run.write)` + 댓글 → 다음 새 기록에서 `post_video` 1회 · `POST mode=test result=saved reason=not_in_allowlist`, 반복 `SKIP` 없음
- direction: `_post` 의 기억 관문이 `STAGE_POST` 기억과 함께 `STAGE_WRITE` 기억에서도 반복 SKIP 을 남기고 멈추게 하고(명단 영상은 지금처럼 읽지 않음), tests/test_run.py 에 "초안 저장이 한 번 실패한 명단 밖 영상은 다음 새 기록에서 post_video 0회 · `SKIP reason=stage_error memory=run.write` 가 그 TRIGGER 뒤" 테스트를 더한다
- touches: src/agent/run.py, tests/test_run.py
- status: escalated
- attempts: 0 · last failure: entry criterion fails on inspection (스윕 20261016-101456-adw/smoke-sweep-s118-s121)
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-119 — 프로브로만 잰 기억 관문 행(연애 고민 없음 · jev 오류 둘)과 7H 기준 아래 이유 배지를 스위트 테스트로 잠그기
- source: cycle 20261016-075749-adw/phase-7c-comment-yield-variety · tracker plans/interview-marketing-agent.md#phase-7c · deferred by ship-check
- evidence: tests/test_run.py 에 `has_love_concern: False` 답과 jev 오류 행이 없음 — ship-check 변이 `THIN_HEADS = (NO_SCENE, NO_CONCERN)`(src/agent/run.py:67) → `(NO_SCENE,)` 가 스위트 1063개 초록, jev 머리말을 얇은 쪽으로 치기 · jev 기억을 붙잡지 않기 · 명단 영상이 jev 기억만 읽기 세 변이도 초록. 이 행들은 추적되지 않는 사이클 파일 .adw/verify.sh 의 V12 · V13 만 잼. 또 트래커 7C 조건 줄(plans/interview-marketing-agent.md:898) — 7H 가 먼저 착지(main 2c48a16)해 "기억한 영상이 새 표본으로 다시 다뤄진 뒤에도 결과 화면의 이유 배지가 남는다" 테스트가 7C 몫
- direction: tests/test_run.py 의 TestMemory 에 V12 · V13 을 옮긴다 — 명단 밖 `재료에 연애 고민 없음` 은 인기 댓글이 늘 때만 다시 씀, 명단 밖 `jev 검사 호출 실패` · `jev 검사 응답 이상` 은 다음 새 기록에서 Claude · jev · commentThreads 0회와 머리말만 든 반복 SKIP, 명단 영상은 같은 두 jev 정지 뒤 다시 씀 — 그리고 7H 의 `test_reason_badge_survives_reprocessing_with_same_reason` 꼴로 명단 밖 기억 영상의 둘째 주기 `trigger.at` 이 첫 주기 마지막 줄보다 늦은데도 이유 배지가 남는 테스트를 더한다(main 에 7C · 7H 가 함께 있을 때, 코드 변경 없음)
- touches: tests/test_run.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-120 — 짜임 고르기가 최근 20개 창을 넘어서도 도는지 테스트로 잠그기
- source: cycle 20261016-075749-adw/phase-7c-comment-yield-variety · tracker plans/interview-marketing-agent.md#phase-7c · deferred by ship-check
- evidence: src/agent/writer.py:508 `pick_shape(previous)` 를 `pick_shape(recent)`(:507, `RECENT_WINDOW = 20` :147)로 바꾼 변이가 스위트 초록 — 그 변이에서는 저장된 댓글이 20개를 넘으면 늘 `scene_first`. 지금 테스트(tests/test_writer.py:691 test_shape_rotates_with_comment_count)는 댓글 수 0–9 만 봄
- direction: tests/test_writer.py 에 previous 길이 20 · 21 · 24 · 25 로 write_comment 를 불러 첫 사용자 메시지의 SHAPE_INSTRUCTION 이 `list(SHAPES)[n % len(SHAPES)]` 를 따르는지 단언 — 코드 변경 없음
- touches: tests/test_writer.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-121 — 계약 '댓글 작성' 절을 7C 코드와 맞추기(WriteResult.head · 실행 흐름의 기억 갈래 · 실행기의 빈 목록)
- source: cycle 20261016-075749-adw/phase-7c-comment-yield-variety · tracker plans/interview-marketing-agent.md#phase-7c · deferred by ship-check
- evidence: docs/contracts.md:970 `WriteResult(draft, skip_reason)` 가 실행 흐름이 읽는 `head`(src/agent/writer.py `WriteResult.head`, compare=False)를 말하지 않음 · :959-967 "Phase 7 이 영상마다 부르는 모양" 이 초안 갈래만 있고 기억 쓰기 · 작성기를 부르지 않는 경우가 없음 · :1000 은 실행기가 `top_comments=()` 를 넘긴다고 쓰지만 tests/live_check.py:1635 는 거른 목록(막힌 영상이면 `[]`)을 넘김
- direction: 세 곳을 지금 코드대로 고쳐 쓴다 — 결정 · 동작 변경 없음
- touches: docs/contracts.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-122 — PROCESS '실제 실행' 절의 명단 밖 영상 줄: 중복 규칙을 명단 밖 영상으로 좁히고 '게시 단계에 한 번' 을 `POST` 줄로 고쳐 쓰기
- source: cycle 20261016-105037-adw/phase-8a-submission-live-run · tracker plans/interview-marketing-agent.md#phase-8a · deferred by ship-check
- evidence: PROCESS.md:243 끝 구절 "한 폴더에서 테스트 시도가 한 번이라도 있으면 다음 실행부터 중복입니다" 가 주어 없이 일반 규칙으로 읽힘 — src/agent/store.py:42-44 `_is_duplicate(live=True)` 는 `live` 시도만 셈, docs/contracts.md:283-284 "허용 목록의 데모 영상은 먼저 테스트 모드로 돌린 뒤 실제 게시할 수 있습니다", 트래커 8A 질문 2 A(plans/interview-marketing-agent.md:1165)는 "명단 밖 영상은" 으로 좁힘 · 같은 줄 앞머리 "명단 밖 영상이 게시 단계에 온 것은 사전 점검의 한 번" — 녹화 실행 14:12:00 에 같은 영상이 src/agent/poster.py:157-161 `check_post` 까지 가 `SKIP … reason=duplicate_video`(logs/sample.log:1219) · 글은 .adw/plan.md:188 이 받아쓰게 한 것이고 두 구절을 잠근 테스트 없음(.adw/ship-report.md § Quality review)
- direction: PROCESS.md:243 의 두 구절만 고쳐 쓴다 — "명단 밖 영상의 `POST` 줄은 사전 점검의 한 줄이고" · "명단 밖 영상은 한 폴더에서 테스트 시도가 한 번이라도 있으면 다음 실행부터 중복입니다(명단 영상의 실제 게시는 `live` 시도만 셉니다)". 스위트가 잠근 글자(`` `POST video=C_Ylul6a6y0 mode=test result=saved reason=not_in_allowlist`(13:47:42) `` · `` 같은 영상은 녹화 실행에서 `SKIP … reason=duplicate_video` `` · "이유가 `dry_run` 이 아니라 …" 문장)는 그대로 두고, 고친 줄에 `녹화`/`시연` 과 게시한 꼴을 함께 쓰지 않는다 — 결정 · 숫자 · 코드 변경 없음
- touches: PROCESS.md
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-123 — 8A 문서 판정기 표본을 판정기 상수와 떼어 적기(게시한 꼴 15 × 녹화 · 시연 · `allowlist`)
- source: cycle 20261016-105037-adw/phase-8a-submission-live-run · tracker plans/interview-marketing-agent.md#phase-8a · deferred by ship-check
- evidence: tests/test_submission_docs.py:669-682 `test_recording_post_reach` 가 판정기와 같은 `RECORDING_WORDS` · `POSTED_SHAPES`(:81-98)로 표본을 만들어, 15개 꼴 가운데 12개(`올렸` · `달았` · `등록했` · `mode=live` 등)나 낱말 `시연` 을 상수에서 지워도 모듈 초록(ship-check 돌연변이 — 하나씩 지우기에서 `게시했` · `게시됐` · `result=posted` 셋만 빨강) · :79 `LIST_WORDS` 의 `allowlist` 를 지워도 초록(빨강 표본 없음, .adw/guard-matrix.md:12 "C1 only")
- direction: 판정기 상수를 읽지 않고 글자 그대로 적은 표본(15 꼴 × `녹화` · `시연` 의 30개, 또는 상수 길이 15 · 2 고정 단언)으로 reach 를 잠그고, `committed_list_claims` 에 `allowlist` 빨강 표본 하나를 더한다(인용: 트래커 8A 질문 4 A). 지금 README · PROCESS 에서 걸리는 줄 0개는 그대로여야 한다 — 테스트 파일만, 판정기 · 문서 · 코드 변경 없음
- touches: tests/test_submission_docs.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16

### S-124 — 8A 문서 잠금 셋을 제 줄에 묶기(막은 줄의 reason · README `남의 채널 다섯` 두 곳 · 시연 링크 줄의 '실제 게시는 없습니다')
- source: cycle 20261016-105037-adw/phase-8a-submission-live-run · tracker plans/interview-marketing-agent.md#phase-8a · deferred by ship-check
- evidence: tests/test_submission_docs.py:162-169 `sample_log_failures` 의 blocked 조건에서 `and fields.get("reason") == "not_in_allowlist"` 를 지워도 초록(깨진 사본 `noblock.log` 는 그 줄을 통째로 지울 뿐) · :626 V9 포트가 `남의 채널 다섯의 인기 영상` 을 README 전체에 `assertIn` 해 README.md:149 · :156 중 하나만 `넷의` 로 바꿔도 초록(헌법 13조 — 포트 테스트가 쥔다고 한 것) · :416 `실제 게시는 없습니다` 가 README.md:7 대신 :156 으로도 채워져, README.md:7 의 그 구절을 지워도 초록
- direction: 막은 줄의 `reason=` 만 다른 값(예: `dry_run`)으로 바꾼 사본을 더해 `["sha256", "blocked"]` 를 기대하고, README 의 `남의 채널 {n}의 인기 영상` 은 개수(2)로, `실제 게시는 없습니다` 는 `- 시연 영상:` 줄 안에서 단언한다 — 테스트 파일만, 문서 · 코드 변경 없음
- touches: tests/test_submission_docs.py
- status: resolved
- attempts: 0 · last failure: —
- first seen: 2026-10-16 · last seen: 2026-10-16
