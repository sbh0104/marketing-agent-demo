# Human checks

## Rules — read this block before editing an entry

- rules version: HC1 2026-10-10
- **What lives here:** only the items of the route's last verdict doc's `## Human checks`
  section (`.adw/ship-report.md`, or `.adw/ui-validate.md` on the UI route) — the checks a
  person owes after the merge. It is not the smoke bucket and not the backlog: no machine
  picks an entry up as work.
- **Two owners.** Everything **above** `## Entries` is the template's: `install.sh --force`
  refreshes this block on every install. Everything **below** `## Entries` is the project's
  and no installer ever touches it.
- **Who writes:** only the landing hand (`lane.py`, at landing, under the registry lock, from
  the home tree) appends entries. Ids are `H-###`, three digits, monotonic, never reused — one
  above the highest in the home tree or the lane copy. A person edits only an entry's
  `- status:` line.
- **Entry shape** (indented two spaces here so it is not an entry):

  ### H-000 — <todo>
  - project: <project>
  - when: <YYYY-MM-DD> · <tracker ref or branch>
  - from: <doc> § Human checks — <from text>
  - source: <phase branch>
  - tag: plain | sensitive: <kind> | sensitive: <kind> · confirmed <date>
  - status: open | confirmed | done | dropped

- **Status meanings:** `open` — owed after the merge · `confirmed` — confirmed before the
  merge in the interview · `done` · `dropped`. Only a person moves `open` to `done` or
  `dropped`.

## Entries

### H-001 — `v` 거부 목록을 매개변수 이름 허용 목록(`si` · `t` · `feature` · `pp` …)으로 바꿀지 정하기 — 이번에 주소 끝 제어 문자(`youtu.be/A?v\x01`)가 거부 목록을 비켜 간다는 근거가 더해짐(R2, 다른 영상 0)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-1
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1-foundation-contracts
- tag: plain
- status: open

### H-002 — 진짜 영상 ID 둘로 `youtu.be/<내 ID>?V=<다른 ID>`, `?%56=`, `?+v=`, 전각 `v` 가 실제 YouTube 에서 다른 영상을 트는지 한 번 확인하기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-1
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1-foundation-contracts
- tag: plain
- status: open

### H-003 — Windows 와 macOS 에서 스위트를 한 번씩 돌리기(Windows 는 출력이 cp949 일 때 이모지 제목의 echo 도 봄)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-1
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1-foundation-contracts
- tag: plain
- status: open

### H-004 — Phase 8 직전 `git ls-files` 로 크롬 프로필 · 쿠키 · `.env` · `credentials.json` 류가 커밋되지 않았는지 확인하기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-1
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1-foundation-contracts
- tag: plain
- status: open

### H-005 — Phase 7 이 시작하기 전에 트래커 Phase 7 절의 로그 결정에 "로그 증명은 UTF-8 로만 읽고 `\n` 으로만 나눈다"를 더할지 정하기(R1 latin-1 가짜 POST · R5 계약 7절 문단과 함께)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-1
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-1-foundation-contracts
- tag: plain
- status: open

### H-006 — 정수 설정 키에 자릿수 상한을 둘지, 계약 2절의 "비교와 셈에만 쓰인다" 문장만 고칠지 정하기(R4)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-1
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-1-foundation-contracts
- tag: plain
- status: open

### H-007 — 트래커 Phase 2 · Phase 7 절에 Phase 1 이 넘긴 주인 줄(짝 없는 서로게이트 제목 → Phase 2 · 7, cp949 echo 이모지 → Phase 7)을 옮겨 적기 — 지금은 Phase 1 절 79행에만 있음
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-1
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-1-foundation-contracts
- tag: plain
- status: open

### H-008 — 계약 11절의 "판정이 바뀔 수 있나" 세 문장(`docs/contracts.md:485-492`)을 어떻게 바로잡을지 정하기 — 문장만 실제대로 고칠지("나이 창이 닫힌 영상은 reason 과 상관없이 다시 `yes` 가 될 수 없음", 줄어든 조회수가 `no` 일 수 있음, 설정을 고치면 `too_old` 도 바뀜) 아니면 나이 검사를 조회수 검사 앞으로 옮길지, Phase 7 계획 전에
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-4
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-4-trigger-timing
- tag: plain
- status: open

### H-009 — 트래커 Phase 2 · Phase 7 절에 이번 페이즈가 넘긴 일의 주인 적기 — 최소 기록 간격(재시작 · 시계 되감김), 한 번 튀거나 꺼진 조회수 읽기, 나이 창이 닫힌 영상의 추적 중단, `record.trigger` · `Store.put` · `TRIGGER` 연결과 새 기록마다 다시 판정, 모듈 목록 두 곳 — 지금은 `.adw/plan.md` 와 계약 11절에만 있음
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-4
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-4-trigger-timing
- tag: plain
- status: open
