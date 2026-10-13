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

- [x] [smoke] 스모크 스윕 — S-038
- [x] [smoke] 스모크 스윕 — S-038, S-039, S-040, S-041, S-042
- [x] [smoke] 스모크 스윕 — S-033, S-034, S-035, S-036, S-037
- [x] [smoke] 스모크 스윕 — S-029, S-030, S-031, S-032
- [x] [smoke] 스모크 스윕 — S-024, S-025, S-026, S-027, S-028
- [x] [smoke] 스모크 스윕 — S-019, S-020, S-021, S-022, S-023
- [x] [smoke] 스모크 스윕 — S-018
- [x] [smoke] 스모크 스윕 — S-011, S-012, S-013, S-014, S-015
- [x] [smoke] 스모크 스윕 — S-008, S-009, S-010
- [x] [smoke] 스모크 스윕 — S-007
- [x] [smoke] 스모크 스윕 — S-003
- [x] [smoke] 스모크 스윕 — S-001, S-002, S-004, S-005, S-006
- [x] Phase 1 — 뼈대와 계약 (plans/interview-marketing-agent.md#phase-1)
- [x] Phase 2 — ① 탐지 · 조회수 추적 (plans/interview-marketing-agent.md#phase-2)
- [x] Phase 3 — ② 판별 · 주제 일치 (plans/interview-marketing-agent.md#phase-3)
- [x] Phase 4 — ③ 타이밍 · 뜨기 직전 판단 (plans/interview-marketing-agent.md#phase-4)
- [x] Phase 5 — ④ 댓글 작성 · 자체 검사 (plans/interview-marketing-agent.md#phase-5)
- [x] Phase 6 — ⑤ 크롬 연결 · 게시 · 확인 (plans/interview-marketing-agent.md#phase-6)
- [~] Phase 1A — 파서 허용 쪽 규칙 (plans/interview-marketing-agent.md#phase-1a)
- [~] Phase 1B — 계약 절 이름 규칙 (plans/interview-marketing-agent.md#phase-1b)
- [ ] Phase 6A — 진짜 호출 준비 · 사람이 돌릴 실행기 (plans/interview-marketing-agent.md#phase-6a)
- [ ] Phase 6B — 진짜 결과 반영 · 정확도 기록 · 기준값 조정 (plans/interview-marketing-agent.md#phase-6b)
- [ ] Phase 7 — 파이프라인 연결 · 운영 규칙 통합 (plans/interview-marketing-agent.md#phase-7)
- [ ] Phase 8 — 제출물 (plans/interview-marketing-agent.md#phase-8)
- [ ] (example) Add social login buttons to the login screen
- [ ] (example) Add retry logic on payment failure
- [ ] (example) [ui] Redesign the product card grid (plans/interview-shop.md#phase-4)

- [x] ~~(retro 후보 · T4 경보) plan 설계 예산·꾸러미 규칙 재검토 — ⑶ 계획서 수리: 0 · ⑷ 계획 밖(트래커 plans/interview-*.md 제외): 13 — .env.example, .gitignore, config.yaml, data/.gitkeep, logs/.gitkeep … (cycle: 20261013-062542-adw/phase-1-foundation-contracts ⑷ 13)~~ — 흡수: E-011 줄 (2026-10-14 T4 경보 인터뷰 b7fbd89c) — 거짓 경보: 레인의 옛 수집기(T14 전)가 셈, 오늘 수집기로 3 · 되짚기 시작을 마지막 plan 단계로 잡으면 0 · 읽기 예산 25·자료 꾸러미 무변경
- [x] ~~(retro 후보 · E-005) Phase 1 파서의 열거형 방어를 ship-check 마다 새 꼴이 뚫음 — 최소 계약 고침: 트래커 Phase 1 · 7 결정을 허용 쪽 규칙으로 — 가드 쿼리 이름 허용 목록(ship-report Human checks 1) · 로그 증명은 UTF-8 로만 읽고 `\n` 으로만 나눔(Human checks 5) · 정수 설정 자릿수 상한(Human checks 6) (sightings: 20261013-033250-stop-1 · 20261013-075734-stop-1 · 20261013-122544-stop-1 · 20261013-062542-adw/phase-1-foundation-contracts)~~ — 새 페이즈로: `Phase 1A — 파서 허용 쪽 규칙` (2026-10-14 E-005 인터뷰 1836973d) — 가드 youtu.be · shorts 쿼리 이름은 `si` · `t` · `feature` 만 · 정수 설정 상한 필수 · 로그 날 글자는 L·M·N·P·S + 공백만 · 증명은 `read_log`(UTF-8 · `\n`)로만, Phase 7 의 로그 제어 문자 고침도 1A 로 옮김
- [x] ~~(retro 후보 · E-006) 민감 확인 줄로 머지 전 멈춘 ship-check 가 정지 부류 표에 없어 `unknown` 으로 남음 — 최소 계약 고침: 하네스 정지 부류 표에 "ship-check sensitive human checks — confirm in the interview before merge" 행 하나(stale harness: yes — 이미 있으면 닫음) (sightings: 20261013-075734-stop-1 · 20261013-122544-stop-1)~~ — ADWS E-274 로 넘김 (2026-10-14 원격 인터뷰 · 슬롯 1c92f3de · Q1 A) — 같은 두 목격을 `~/project/ADWS/.adw/backlog.md` 의 `(retro 후보 · stop:unknown:interview:-:104819ca · ship-check · E-274)` 줄이 이미 안고 있고, 고칠 파일 `scripts/stop_lesson.py` (`LESSONS`) 는 허브에만 있어 이 저장소에는 고칠 코드가 없다. ADWS `1a9b4236` 표 19행에 이 행은 아직 없음(이미 고쳐져 닫는 것이 아님) · `stale harness` 는 첫 목격 `no` 라 원인이 아님. ADWS 가 행을 넣을 때까지 민감 확인 정지는 `unknown` · 📖 로 찍힌다 — 다시 후보로 오르면 이 줄로 흡수해 닫는다

- [x] ~~(retro 후보 · E-009) 계약 문서 설명 문장이 코드보다 넓게 약속하고 ship-check 가 페이즈마다 사람 확인으로 올림 — 최소 계약 고침: `.claude/skills/verify-plan/SKILL.md` — diff 가 더한 계약 절의 보장 문장(뿐 · 않음 · 될 수 있음 · 에만)마다 그 문장을 재는 검사 한 줄을 요구 (sightings: 20261013-062542-adw/phase-1-foundation-contracts · 20261013-161358-adw/phase-4-trigger-timing)~~ — 헌법 9조로 닫음 (2026-10-14 원격 인터뷰 · 슬롯 62ba0a88 · Q1–Q6 A) — 고칠 자리로 적힌 `.claude/skills/verify-plan/SKILL.md` 는 하네스 파일이라 다음 설치가 덮으므로 이 프로젝트 헌법(`.adw/constitution.md` 9조)에 둠: 계획이 약속 줄마다 스위트 테스트를 짝짓고, 빨강이면 사이클 안에서 문장을 코드만큼 줄이고(plan-miss · verify-run 고침, 사람 확인 아님), verify-plan 이 낱말 넷 그물로 걸린 줄을 모두 정리. 앞으로 고치는 줄에만 — 2절은 Phase 1A, 트리거 11절은 H-008. ADWS 에는 보내지 않음(낱말이 한국어 계약 전용). 이 꼴이 다시 오르면 9조가 실제 사이클에서 어떻게 돌았는지부터 본다
- [x] ~~(retro 후보 · E-010) 하류 페이즈로 넘긴 일 · 받아들인 위험의 주인이 plan.md · 계약에만 남고 트래커 하류 절에 없음 — 최소 계약 고침: `.claude/skills/plan/SKILL.md:161` Out of scope 에 `- Handed to Phase N: <what>` 줄 꼴을 더하고 ship-check 가 그 줄을 `## Human checks`(트래커 하류 절에 옮길 후보)로 나르게 (sightings: 20261013-062542-adw/phase-1-foundation-contracts · 20261013-161358-adw/phase-4-trigger-timing)~~ — 헌법 10조로 닫음 (2026-10-14 원격 인터뷰 · 슬롯 96c52980 · Q1–Q4 A) — 끊긴 곳은 보내는 쪽이 아니라 받는 쪽이었다: 넘긴 일 다섯(H-007 · H-009 · H-017 · H-021 · H-027)이 이미 Human checks 를 거쳐 `.adw/human-checks.md` 에 open 으로 있는데 understand · plan 이 장부를 읽지 않았다. 그래서 받는 페이즈의 understand 가 제목에 제 번호(`Phase N`, 1 ≠ 1A)가 있는 열린 항목을 `notes.md` `## Inherited` 로 가져오고, plan 이 `Inherited H-###:` 한 줄로 닫으며(한다 · settled · `→ Phase M` · `→ human` — 혼자 받아들이지 않음), 계획서의 넘김은 `- Handed to Phase M:` 꼴(계약에 있으면 `(contract: <절 제목>)`)로 써서 ship-check 가 괄호 없는 줄만 번호를 달아 장부로 나른다. 하네스(`.claude/`)는 다음 설치가 덮어 고치지 않고, ADWS 에도 보내지 않음(다른 프로젝트는 그대로임을 받아들임). 계획서에만 남았던 넘김 하나("`SKIP` 한 영상 기억", Phase 5 → 7)는 트래커 Phase 7 결정으로 옮김. 지금 도는 Phase 2 레인은 10조 전에 시작해 H-009 의 Phase 2 몫을 못 봤다 — Phase 7 이 가져올 때 분류한다. 이 꼴이 다시 오르면 10조가 실제 사이클(첫 대상: Phase 1A · 6A)에서 어떻게 돌았는지부터 본다

- [x] (retro 후보 · E-011) **[→ 상류 ADWS 백로그로 이관 (2026-10-14 원격 인터뷰 · 슬롯 b7fbd89c · Q1 A) — `~/project/ADWS/.adw/backlog.md` To do 끝의 `(retro 후보 · marketing-agent-demo E-011 이관)` 줄. 고칠 자리 `.claude/` 는 동기화가 덮는 하네스라 이 저장소에서는 안 고치고 ADWS 에서 고쳐 다음 동기화로 들어온다. 그때까지 회고 ⑷ · T4 경보의 점 파일 · 되짚기 판 셈은 부풀려 읽는다 — 다시 울리면 이 줄로 흡수해 닫는다]** 수집기가 `Files:` 경로 앞의 점을 벗겨 점 파일(`.env.example` · `.gitignore`)이 plan 에 적혀도 늘 "계획 밖" · T4 ⑷ 에 들어감 — 최소 계약 고침: `.claude/skills/plan/scripts/retro_collect.py:437` `tok.strip("`,;.…")` 를 앞에서는 백틱만 벗기고 `.` 는 끝에서만 벗기게 · 같은 ⑷ 셈의 되짚기 판 시작(`run_start` :457)을 가장 이른 단계가 아니라 마지막 plan 단계의 `first_started_at` 으로 — Phase 1 다시 세기 3 → 0 (E-002, T4 경보 인터뷰 2026-10-14 b7fbd89c 흡수) · `.claude/` 는 하네스 소유라 같은 고침이 상류 ADWS `template/` 에도 가야 동기화 뒤에 남음 (sightings: 20261013-161343-adw/phase-3-classifier-topic · 20261013-161439-adw/phase-5-writer-comment)
- [x] ~~(retro 후보 · E-014) 레인마다 계약 새 절을 제 base 의 다음 번호(`## 11.`)로 매기고 본문 · 코드 주석이 그 번호("11절")를 가리켜, 착지 뒤 다른 절을 가리킴 — 최소 계약 고침: `docs/contracts.md` `## 10. 계약 변경 규칙` 에 "다른 절은 번호가 아니라 절 이름으로 가리킨다" 한 줄 (sightings: 20261013-161343-adw/phase-3-classifier-topic · 20261013-161439-adw/phase-5-writer-comment)~~ — 새 페이즈로: `Phase 1B — 계약 절 이름 규칙` (2026-10-14 원격 인터뷰 · 슬롯 be02ef18 · Q1–Q4 A) — 10절 뒤 절은 번호 없이 제목만 · 규칙 줄 + 스위트 테스트(10절 뒤 번호 제목 · "11절" 꼴 인용이면 빨강) · Phase 2 착지 뒤 그 제목과 8곳까지 · 옛 기록은 10절 풀이 한 줄로 읽고 장부 E-007 · E-012 는 이름으로 고침(H-008 · H-009 는 human-checks 규칙대로 그대로)
- [x] ~~(retro 후보 · E-015) smoke-file 이 PASS 인 verify-report 를 본문 줄머리 `FAIL` 로 FAIL 로 읽어 ship-report 스모크 후보를 두 번 올림(홈 S-019~S-023 = S-024~S-028) — 최소 계약 고침: `.claude/skills/plan/scripts/smoke_file.py:73-76` `verdict()` 가 `section_body(text, "Verdict")` 만 보게(ship 쪽 `:75` 도 같은 꼴) (sightings: 20261013-161439-adw/phase-5-writer-comment — 한 번이지만 원장에 중복 다섯 건을 남김)~~ — ADWS 백로그로 이관 (2026-10-14 원격 인터뷰 · 슬롯 e0faf70b · Q1 A) — `~/project/ADWS/.adw/backlog.md` To do 끝의 `(retro 후보 · marketing-agent-demo E-015 이관)` 줄(한 줄 고침 · ship 쪽 `:75` · Phase 5 verify-report 를 시험 재료로). 고칠 `smoke_file.py` 는 ADWS `1a9b4236` 과 글자까지 같은 하네스라 동기화가 덮고 헌법 7조도 직접 고침을 막아, 이 저장소에는 고칠 코드가 없다. 그때까지는 검사가 초록인데 본문 줄머리가 `FAIL` 인 READY WITH RISKS 판에서 같은 고침이 통에 두 번 적힐 수 있다 — 두 번째 묶음(`filed by smoke-file (one-pass)`)은 스윕 전에 닫거나 헛 스윕(이번 8분 · 변화 0줄)을 감수. 다시 오르면 이 줄로 흡수해 닫는다

- [ ] (retro 후보 · E-021) ship-check 가 받아들인 위험의 같은 코드 자리에서 새 입력을 찾아 다시 멈춤(받아들임을 입력으로 적음) — 최소 계약 고침: `.claude/skills/deep-interview/SKILL.md:98-99` Trade-offs accepted 꼴에 한 줄 — "ship-check 발견을 받아들일 때는 코드 자리(파일:함수 · 처리 줄)와 입력 부류로 적고, 재현한 입력은 경계가 아니라 예로 단다"(허브 🤖 attn-agent 의 답도 같은 꼴로). `.claude/` 는 ADWS 동기화 하네스라 고침은 상류에서(E-011 선례) (sightings: 20261013-062542-adw/phase-1-foundation-contracts (E-005) · 20261013-161159-adw/phase-2-watcher-detect)

## Done

<!-- Move finished items here, or mark them [x] above -->
