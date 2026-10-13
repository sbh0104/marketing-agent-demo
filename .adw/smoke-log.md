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
- status: open
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

### S-NEW-1 — 추적 영상이 50개를 넘을 때 두 번째 videos.list 묶음까지 표본이 붙는지 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:222 — `range(0, len(queue), MAX_IDS_PER_CALL)` → `range(0, min(len(queue), MAX_IDS_PER_CALL), MAX_IDS_PER_CALL)`(처음 50개만 추적) 변이가 스위트에서 초록(201개 OK). 50개 넘는 테스트는 tests/test_watcher.py:421-433 하나뿐이고 첫 묶음이 500(.adw/ship-report.md § Test integrity). 지금 코드는 맞음 — 새 영상 120개 → `['videos:50', 'videos:50', 'videos:20']`, sampled 120(ship-check 에서 확인)
- direction: tests/test_watcher.py 에 창 안 영상 51개(새 ID 51개 또는 저장 영상 51개)와 두 묶음 모두 200 인 행을 더해 videos 호출 2번(50 · 1), `sampled == 51`, VIEWS 51줄을 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-2 — 검색어 둘 이상에서 오류·보류 뒤 남은 검색과 남은 묶음을 멈추는지 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:181, src/agent/watcher.py:177, src/agent/watcher.py:230 — 검색 오류 뒤 `return`→`break`, 검색 보류 뒤 `return`→`break`, videos 보류 뒤 `return`→`continue` 변이가 모두 초록. ApiErrorTest · QuotaTest 는 키워드 하나(tests/test_watcher.py:30 CONFIG)라 "남은 검색을 그만둠"(계약 11절)이 안 걸림(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 키워드 2개 Config 로 (a) 첫 검색 403 → search 호출 1번 · ERROR 1줄, (b) daily_max_searches 1 + 첫 키워드가 다음 페이지 토큰 → search 1번 · QUOTA 1줄, (c) 추적 51개 + 단위 한도로 첫 videos 묶음 보류 → QUOTA 1줄 · videos 호출 0번 을 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-3 — 제목·설명 밖 외부 글자 다섯 자리의 서로게이트 정리를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:72, src/agent/watcher.py:167, src/agent/watcher.py:207, src/agent/watcher.py:268, src/agent/watcher.py:296 — 각 자리의 `_clean` 을 뺀 변이가 tests.test_watcher 에서 초록. `Logbook.write(Event.ERROR, reason="HTTP 400 \ud800bad")` 는 UnicodeEncodeError 를 내므로 :296 이 깨지면 주기가 ERROR 줄 없이 끝남(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py IntakeTest/ApiErrorTest 에 channelId `"UC\ud800"`, 키워드 `"연애\ud800"`, search videoId `"x\ud800"`, 잘못된 viewCount 의 detail, 403 본문 reason `"bad\ud800"` 행을 더해 run 이 CycleReport 를 돌려주고 로그 값이 U+FFFD 로 parse_line 되는지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-4 — 경계값 넷(publishedAt 초 · 추적 창 경계와 설정값 · 단위 한도 경계 · 빈 nextPageToken)을 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:55 (`value[:16]` 변이 초록), src/agent/watcher.py:220 (`>`→`>=` 초록), src/agent/watcher.py:152 (`timedelta(hours=12)` 로 박은 변이 초록), src/agent/youtube.py:110 (`>`→`>=` 초록), src/agent/watcher.py:213 (빈 토큰을 따라가는 변이 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 `publishedAt "2026-10-12T10:00:37Z"` → `published_at` 초 37, `max_age_hours 6` 에서 정확히 NOW−6h 영상은 비추적 · NOW−5h 는 추적, `nextPageToken: ""` 이면 다음 페이지를 부르지 않음 을, tests/test_youtube.py 에 9,999 단위에서 videos.list 1회 허용 뒤 다음 호출 보류(units 10000/10000) 를 더한다 — 코드 변경 없음
- touches: tests/test_watcher.py, tests/test_youtube.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-5 — http_get 의 HTTPError → (code, body) 변환을 단위 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/youtube.py:181-188 — `grep -n -e http_get -e HTTPError -e urlopen tests/*.py` 결과 없음. 지금 증명은 verify 러너 V9(실제 루프백 403)뿐이라 스위트 밖(.adw/ship-report.md § Spec compliance)
- direction: tests/test_youtube.py 에 `urllib.request.urlopen` 을 patch 한 테스트를 더해 HTTPError(403, 본문) → `(403, 본문)`, 200 응답 → `(200, 본문)`, 요청의 `Accept: application/json` 헤더와 timeout 전달을 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-6 — 계약 첫 문단의 모듈 목록과 config.yaml 첫 주석을 지금 코드에 맞춤
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: docs/contracts.md:3-6 — 코드 위치로 Phase 1 파일 6개만 나열하고 11절의 env.py · youtube.py · watcher.py 를 빠뜨림. config.yaml:1 — "과제 안내의 예시 값입니다" 인데 poll_interval_min · daily_max_searches 는 과제와 다름(.adw/verify-plan.md § Out of scope (b), .adw/ship-report.md § Smoke candidates)
- direction: docs/contracts.md:3-6 의 모듈 목록에 `env.py` · `youtube.py` · `watcher.py`(11절)를 더하고, config.yaml:1 주석을 "과제 예시 값이 기본이고, 주기와 검색 상한은 계약 2절대로 바꿈" 으로 고친다 — 값과 계약 조항은 그대로
- touches: docs/contracts.md, config.yaml
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-7 — 검색 쿼터 비용을 "구글의 계산"이 아니라 "우리 장부의 일부러 엄격한 계산"으로 바로 적음
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by deep-interview (ship-check R3 → HC1 질문 2 A)
- evidence: docs/contracts.md:58-67, docs/contracts.md:535-536, docs/contracts.md:553-554, config.yaml:14, docs/research/search-quota.md:8, docs/research/search-quota.md:17 — 검색 1회를 "Google 의 100 단위(하루 10,000 단위 한 통)"로 적음. 구글 공식 표는 2026-10-08 부터 `search.list` 를 하루 100회 별도 통(1회 1), `videos.list` 를 나머지 10,000 단위 통에서 1로 셈(https://developers.google.com/youtube/v3/determine_quota_cost "Last updated 2026-10-08 UTC", .adw/ship-report.md § Risks R3). 장부(src/agent/youtube.py:32-33, :107-111)는 트래커 Phase 2 결정(HC1 질문 2 A)대로 옛 계산을 일부러 유지 — 코드는 맞고 문서의 이유가 틀림
- direction: 계약 2절 · 11절과 config.yaml:14 주석을 "구글은 검색을 하루 100회 별도 통으로 센다 · 우리 장부는 더 엄격하게 검색 1회를 10,000 단위 통에서 100씩 깎는다(옛 규칙과 새 규칙 모두에서 넘치지 않게) · 그래서 기본 90회면 조회수 몫은 1,000 단위 이상이고, daily_max_searches 를 95–100 으로 올려 조회수가 막히는 것은 구글이 아니라 우리 장부 때문(그때는 장부를 두 통으로 나누는 결정이 따로 필요)"으로 고친다(출처 URL · 갱신일 포함). docs/research/search-quota.md 는 조사 기록이라 :8 · :17 을 지우지 않고 `## Decision` 아래에 날짜 붙은 정정 줄을 더한다 — 값 · 코드 · 장부 파일 모양 · 계약 조항의 동작은 그대로
- touches: docs/contracts.md, config.yaml, docs/research/search-quota.md
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-8 — 표본 2개 이상인 기록의 VIEWS prev/delta 와, 조회수 호출만 막혔을 때의 held 를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:274 (`view_history[-2]`→`[0]` 변이 초록), src/agent/watcher.py:220 (표본 2개 이상인 기록을 추적에서 빼는 변이 초록), src/agent/watcher.py:229 (`_track` 의 `tally.held = True` 를 지운 변이 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 창 안 저장 영상의 view_history 가 [1000, 1300] 일 때 새 조회수 1450 이면 `VIEWS prev=1300 delta=150` 인지, 장부를 검색 99회(9,900단위)로 채우고 daily_max_searches 200 에서 검색 1회는 통과 · videos.list 는 막히면 `CycleReport.held is True` 와 `QUOTA … call=videos.list counter=units` 한 줄인지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-9 — 실패할 수 없는 단언 둘을 고침
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: tests/test_youtube.py:276 (`QuotaLedger(...)` 가 먼저 QuotaError 를 내서 `fetch.urls == []` 는 늘 참), tests/test_watcher.py:613-617 (src/agent/watcher.py:150-151 을 지워도 src/agent/youtube.py:211 의 다른 ValueError 로 통과)(.adw/ship-report.md § Test integrity)
- direction: tests/test_youtube.py:276 의 단언을 지우거나 장부 거부를 직접 단언하는 것으로 바꾸고, tests/test_watcher.py ClockTest.test_naive_now_is_rejected 는 `assertRaisesRegex(ValueError, "now 에 시간대가 없습니다")` 로 문구까지 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py, tests/test_watcher.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-10 — 탐지 입력 가장자리 여섯 가지를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:213 (`isinstance(token, str)` 제거 초록), src/agent/watcher.py:207 (SKIP 의 `raw[:40]`→`raw` 초록), src/agent/watcher.py:74 (description 기본값 `""` 제거 초록), src/agent/watcher.py:202 (검색 ID `fullmatch`→`match` 초록), src/agent/watcher.py:53 (publishedAt `fullmatch`→`match` 초록), src/agent/watcher.py:55 (`.replace(tzinfo=utc)`→`.astimezone(utc)` 는 TZ=UTC 호스트에서 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 nextPageToken 이 str 이 아니면(예: 5) 다음 페이지를 부르지 않음 · 40자보다 긴 잘못된 검색 ID 의 SKIP video 값이 40자 · description 이 없는 영상은 description "" 로 저장 · 12자 검색 ID 는 search.list 단계에서 SKIP 되고 videos.list 로 가지 않음 · INVALID_ITEMS 에 publishedAt "2026-10-12T10:00:00Zjunk" 행 · publishedAt 고정 테스트를 로컬 시간대가 UTC 가 아닐 때(TZ=Asia/Seoul + time.tzset, 끝나면 되돌림, tzset 이 없는 곳은 skip)도 돌림 을 더한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-11 — 쿼터 장부 · 클라이언트 가장자리 일곱 가지를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/youtube.py:148 (`utf-8-sig`→`utf-8` 초록), src/agent/youtube.py:130-135 (장부 `indent=None` · `sort_keys=False` 초록), src/agent/youtube.py:124 (`astimezone(utc)` 없는 `isoformat()` 초록), src/agent/youtube.py:242-243 (URL 만들기와 reserve 순서 바꾸기 초록), src/agent/youtube.py:104-105 (모르는 호출 ValueError 제거 초록), src/agent/youtube.py:259 (`replace(key, mask, 1)` 초록), src/agent/youtube.py:252 (`status != 200`→`status >= 400` 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_youtube.py 에 BOM 붙은 유효한 quota.json 을 읽음 · 쓴 장부 파일이 키 정렬 · 2칸 들여쓰기 · KST 인 now 로 reserve 해도 저장된 at 이 `+00:00` · page_token="\ud800" 처럼 URL 을 못 만드는 호출은 장부에 안 적히고 fetch 0회 · `reserve("comments.list", …)` 는 ValueError · URL 을 두 번 담은 OSError 문구에서 키가 둘 다 가려짐 · `(302, b'{"items": []}')` 은 `YouTubeError` 의 reason `"HTTP 302"` 를 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-12 — .env 읽기 가장자리 셋을 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/env.py:34 (`raw.strip()`→`raw` 초록), src/agent/env.py:39 (`not sep` 제거 초록), src/agent/env.py:28-29 (`except OSError` 제거 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_env.py 에 공백만 있는 줄과 들여 쓴 `# 주석` 줄은 건너뜀 · `=` 없는 `JUSTNAME` 줄은 줄 번호를 대고 값은 말하지 않는 `EnvError` · `.env` 자리가 폴더면 `EnvError` 를 단언한다 — 코드 변경 없음
- touches: tests/test_env.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-13 · last seen: 2026-10-13

### S-NEW-13 — 쿼터 장부의 임시 파일 쓰기와 구글 reason 이 글자가 아닐 때를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/youtube.py:136 (`tmp = self.path` 로 바꿔 임시 파일 없이 바로 쓰는 변이 초록), src/agent/youtube.py:273 (`return str(reason)` 변이 초록 — 오류 줄이 `HTTP 404 None` 이 됨)(.adw/ship-report.md § Test integrity)
- direction: tests/test_youtube.py 에 reserve 하는 동안 `os.replace` 를 가로채 첫 인자가 `quota.json.tmp` 이고 둘째가 `quota.json` 인지 · 404 본문의 `error.errors[0].reason` 이 `5` 나 `null` 이면 `YouTubeError` reason 이 정확히 `"HTTP 404"` 인지 단언한다 — 코드 변경 없음
- touches: tests/test_youtube.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-NEW-14 — 저장소 쓰기 오류 전파 · publishedAt 소수 자릿수 · 글자 아닌 id · 다음 페이지의 publishedAfter 를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:271 (`self._store.put(record)` 를 `try/except: return` 으로 감싼 변이 초록 — 계약 11절 "저장소 쓰기 오류는 run_loop 로 올라감"), src/agent/watcher.py:32 (소수 `{1,9}`→`{1,3}` 변이 초록), src/agent/watcher.py:89 (`isinstance(item.get("id"), str)` 제거 변이 초록), src/agent/youtube.py:220-225 (pageToken 이 있을 때 publishedAfter 를 빼는 변이 초록)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py 에 `put` 이 `OSError` 를 내는 Store 하위 클래스를 넣으면 `Watcher.run` 이 그 `OSError` 를 그대로 내는지 · publishedAt `"2026-10-12T10:00:00.123456789Z"` 가 저장되고 10자리 소수는 SKIP 인지 · videos.list 응답에 `{"id": {"x": 1}}` 항목이 섞여도 주기가 끝나고 그 항목이 무시되는지 · 다음 페이지 요청에도 첫 페이지와 같은 publishedAfter 가 실리는지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14

### S-NEW-15 — SKIP 줄의 detail 내용과 200 이 아닌 2xx 상태를 테스트로 고정
- source: cycle 20261013-161159-adw/phase-2-watcher-detect · tracker plans/interview-marketing-agent.md#phase-2 · deferred by ship-check
- evidence: src/agent/watcher.py:268 (`detail=_clean(str(exc))` 를 `detail=None` · `detail="x"` 로 바꾼 변이 둘 다 초록 — tests/test_watcher.py:518 이 `assertTrue(fields.pop("detail"))` 로 참/거짓만 봄), src/agent/youtube.py:186 (`response.status` 를 `200` 으로 박은 변이 초록 — S-NEW-5 가 요구한 403 · 200 행으로는 잡히지 않음)(.adw/ship-report.md § Test integrity)
- direction: tests/test_watcher.py IntakeTest 의 INVALID_ITEMS 행마다 SKIP 줄 detail 의 앞부분을 지금 코드가 내는 글 그대로 단언하고(예: viewCount `-5` 행은 `statistics.viewCount:` 로 시작), tests/test_youtube.py 에 `urllib.request.urlopen` 을 patch 해 204 응답이 `http_get` 에서 `(204, b"")` 로 돌아오는지 단언한다 — 코드 변경 없음
- touches: tests/test_watcher.py, tests/test_youtube.py
- status: open
- attempts: 0 · last failure: —
- first seen: 2026-10-14 · last seen: 2026-10-14
