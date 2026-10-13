# ADW Backlog

> The local work queue. Replaces GitHub-issue polling.
> The hub's ▶ picker (or `/adw-run <a line verbatim>`) claims **the item you chose**; since 2026-09-21 nothing picks the topmost item on its own (scripts may pass `--pick-top`),
> processes it through the workflow.yml order, and marks it `[x]` when done.
> A scripted `/loop` drains item by item only with `--pick-top`; the hub picker is the normal entry.

## Rules

- `- [ ]` : pending (next execution target)
- `- [~]` : in progress (claimed by adw-run)
- `- [x]` : done
- Priority is **top to bottom**. Move urgent items up.
- One item = one requirement handed to a single `/adw-run` cycle.
- **Items that came from an interview** carry a tracker reference in parentheses so
  adw-run loads that phase's decisions and trade-offs as context:
  `- [ ] Phase 1 — data layer (plans/interview-my-feature.md#phase-1)`
- **UI/UX items start with `[ui]`** — the driver routes them through the UI cycle
  (`workflow-ui.yml`: N variants → validate → human selection) instead of the
  standard cycle. The tag stays in the text; everything else works the same:
  `- [ ] [ui] Phase 4 — product card redesign (plans/interview-shop.md#phase-4)`
- **One item per lane (2026-09-21).** A cycle runs in its own lane (worktree), so several
  items may be `[~]` at once — each claimed by one lane under the registry lock; a lane sees
  only its own line as in-progress. Items that touch the same files are still allowed: the
  second lane's finalize stops on the merge conflict and a human resolves it in that lane.
  `lane.max` in `.adw/cycle.yml` caps the lanes (default 1 = the old one-at-a-time rule).

## To do

- [x] [smoke] 스모크 스윕 — S-007
- [x] [smoke] 스모크 스윕 — S-003
- [x] [smoke] 스모크 스윕 — S-001, S-002, S-004, S-005, S-006
- [x] Phase 1 — 뼈대와 계약 (plans/interview-marketing-agent.md#phase-1)
- [~] Phase 2 — ① 탐지 · 조회수 추적 (plans/interview-marketing-agent.md#phase-2)
- [~] Phase 3 — ② 판별 · 주제 일치 (plans/interview-marketing-agent.md#phase-3)
- [x] Phase 4 — ③ 타이밍 · 뜨기 직전 판단 (plans/interview-marketing-agent.md#phase-4)
- [~] Phase 5 — ④ 댓글 작성 · 자체 검사 (plans/interview-marketing-agent.md#phase-5)
- [~] Phase 6 — ⑤ 크롬 연결 · 게시 · 확인 (plans/interview-marketing-agent.md#phase-6)
- [ ] Phase 7 — 파이프라인 연결 · 운영 규칙 통합 (plans/interview-marketing-agent.md#phase-7)
- [ ] Phase 8 — 제출물 (plans/interview-marketing-agent.md#phase-8)
- [ ] (example) Add social login buttons to the login screen
- [ ] (example) Add retry logic on payment failure
- [ ] (example) [ui] Redesign the product card grid (plans/interview-shop.md#phase-4)

- [ ] (retro 후보 · T4 경보) plan 설계 예산·꾸러미 규칙 재검토 — ⑶ 계획서 수리: 0 · ⑷ 계획 밖(트래커 plans/interview-*.md 제외): 13 — .env.example, .gitignore, config.yaml, data/.gitkeep, logs/.gitkeep … (cycle: 20261013-062542-adw/phase-1-foundation-contracts ⑷ 13)
- [ ] (retro 후보 · E-005) Phase 1 파서의 열거형 방어를 ship-check 마다 새 꼴이 뚫음 — 최소 계약 고침: 트래커 Phase 1 · 7 결정을 허용 쪽 규칙으로 — 가드 쿼리 이름 허용 목록(ship-report Human checks 1) · 로그 증명은 UTF-8 로만 읽고 `\n` 으로만 나눔(Human checks 5) · 정수 설정 자릿수 상한(Human checks 6) (sightings: 20261013-033250-stop-1 · 20261013-075734-stop-1 · 20261013-122544-stop-1 · 20261013-062542-adw/phase-1-foundation-contracts)
- [ ] (retro 후보 · E-006) 민감 확인 줄로 머지 전 멈춘 ship-check 가 정지 부류 표에 없어 `unknown` 으로 남음 — 최소 계약 고침: 하네스 정지 부류 표에 "ship-check sensitive human checks — confirm in the interview before merge" 행 하나(stale harness: yes — 이미 있으면 닫음) (sightings: 20261013-075734-stop-1 · 20261013-122544-stop-1)

- [ ] (retro 후보 · E-009) 계약 문서 설명 문장이 코드보다 넓게 약속하고 ship-check 가 페이즈마다 사람 확인으로 올림 — 최소 계약 고침: `.claude/skills/verify-plan/SKILL.md` — diff 가 더한 계약 절의 보장 문장(뿐 · 않음 · 될 수 있음 · 에만)마다 그 문장을 재는 검사 한 줄을 요구 (sightings: 20261013-062542-adw/phase-1-foundation-contracts · 20261013-161358-adw/phase-4-trigger-timing)
- [ ] (retro 후보 · E-010) 하류 페이즈로 넘긴 일 · 받아들인 위험의 주인이 plan.md · 계약에만 남고 트래커 하류 절에 없음 — 최소 계약 고침: `.claude/skills/plan/SKILL.md:161` Out of scope 에 `- Handed to Phase N: <what>` 줄 꼴을 더하고 ship-check 가 그 줄을 `## Human checks`(트래커 하류 절에 옮길 후보)로 나르게 (sightings: 20261013-062542-adw/phase-1-foundation-contracts · 20261013-161358-adw/phase-4-trigger-timing)

## Done

<!-- Move finished items here, or mark them [x] above -->
