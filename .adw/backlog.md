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

- [x] [smoke] 스모크 스윕 — S-064, S-065, S-066, S-067
- [x] [smoke] 스모크 스윕 — S-059, S-060, S-061, S-062, S-063
- [x] [smoke] 스모크 스윕 — S-057, S-058
- [x] [smoke] 스모크 스윕 — S-056
- [x] [smoke] 스모크 스윕 — S-051, S-052, S-053, S-054, S-055
- [x] [smoke] 스모크 스윕 — S-049, S-050
- [x] [smoke] 스모크 스윕 — S-048
- [x] [smoke] 스모크 스윕 — S-043, S-044, S-045, S-046, S-047
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
- [x] Phase 1A — 파서 허용 쪽 규칙 (plans/interview-marketing-agent.md#phase-1a)
- [x] Phase 1B — 계약 절 이름 규칙 (plans/interview-marketing-agent.md#phase-1b)
- [x] Phase 6A — 진짜 호출 준비 · 사람이 돌릴 실행기 (plans/interview-marketing-agent.md#phase-6a)
- [x] Phase 1C — 글자 설정값 허용 규칙 (plans/interview-marketing-agent.md#phase-1c)
- [x] Phase 6B — 진짜 결과 반영 · 정확도 기록 · 기준값 조정 (plans/interview-marketing-agent.md#phase-6b)
- [ ] Phase 6C — 채점 고치기 · 다시 잴 준비 (plans/interview-marketing-agent.md#phase-6c)
- [ ] Phase 6D — 다시 잰 결과 반영 (plans/interview-marketing-agent.md#phase-6d)
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

- [x] ~~(retro 후보 · E-021) ship-check 가 받아들인 위험의 같은 코드 자리에서 새 입력을 찾아 다시 멈춤(받아들임을 입력으로 적음) — 최소 계약 고침: `.claude/skills/deep-interview/SKILL.md:98-99` Trade-offs accepted 꼴에 한 줄 — "ship-check 발견을 받아들일 때는 코드 자리(파일:함수 · 처리 줄)와 입력 부류로 적고, 재현한 입력은 경계가 아니라 예로 단다"(허브 🤖 attn-agent 의 답도 같은 꼴로). `.claude/` 는 ADWS 동기화 하네스라 고침은 상류에서(E-011 선례) (sightings: 20261013-062542-adw/phase-1-foundation-contracts (E-005) · 20261013-161159-adw/phase-2-watcher-detect)~~ — ADWS 백로그로 이관 + 그 사이 헌법 11조 (2026-10-14 원격 인터뷰 · 슬롯 a0f6ca48 · Q1 B · Q2 B) — `~/project/ADWS/.adw/backlog.md` To do 끝의 `(retro 후보 · marketing-agent-demo E-021 이관)` 줄(고칠 자리 둘: 트래커 틀 · 🤖 지시문, 읽는 쪽 짝 ship-check). 글귀는 세 칸으로 넓힘 — 자리(파일:함수 · 처리 줄) · 입력 부류 · **결과**, 재현 입력은 예; ship-check 는 세 칸이 모두 같을 때만 그 줄의 예(`## Risks`), 결과가 다르거나 모호하면 새 위험(R18 근거). 이 저장소는 동기화까지 `.adw/constitution.md` 11조로 받는다 — 🤖 는 헌법을 읽지 않아 그때까지 🤖 의 받아들임은 입력 꼴일 수 있다. 상류 고침이 들어오면 11조를 남길지 정한다. 다시 오르면 이 줄로 흡수해 닫는다

- [x] ~~(retro 후보 · E-022) 열거한 꼴(정규식 · 이름 목록)로 판정하는 코드에 verify-plan 이 Property-based 를 N/A 로 두고, ship-check 감사가 목록 밖 가까운 꼴을 찾아서야 빈틈이 드러남 — 최소 계약 고침: `.claude/skills/verify-plan/references/test-taxonomy.md:116-118` Property-based 행 `applies:` 에 "열거한 꼴로 판정하는 코드(정규식 · 허용/금지 목록) — N/A 대신 목록 밖 가까운 꼴 표본을 점검 줄로 두고 각 꼴을 빨강/초록으로 정한다" 한 줄 (sightings: 20261013-163932-adw/phase-6-poster-chrome(E-019, verify-plan Property-based N/A "새 파서 없음" 이 가림) · 20261014-035724-adw/phase-1b-contract-section-names(verify-plan.md:127 N/A, ship-report Risks 2); 같은 부류 E-005(Phase 1 → Phase 1A) · E-017(Phase 5))~~ — 헌법 12조로 닫음 (2026-10-14 원격 인터뷰 · 슬롯 0bd7add3 · Q1–Q5 A) — 고칠 자리로 적힌 `test-taxonomy.md` 는 ADWS `template/` 사본과 글자까지 같은 하네스라 동기화가 덮으므로, 이 프로젝트 헌법 `.adw/constitution.md` 12조에 바로 두고 같은 고침을 `~/project/ADWS/.adw/backlog.md` 의 `(retro 후보 · marketing-agent-demo E-022 이관)` 줄로 넘김(상류가 들어오면 12조를 줄임). 12조: 이번 페이즈가 더하거나 고친, 바깥 글을 정해 둔 모양 목록으로 받거나 막는 코드(허용 목록 · `tests/` 안 판정 테스트 포함, 우리 값끼리의 비교 · `except` 목록 제외)마다 목록 밖 닮은 꼴 표본을 계획 `## Test plan` 에 `Near-miss:` 줄로 적고, 색은 트래커 줄 인용으로만(근거가 막으려던 꼴 빨강 · 이름으로 통과시킨 꼴 초록 · 둘 다 아니면 undecided → 사람), 빨강 · 초록은 스위트 테스트로; verify-plan 은 계획이 놓친 판정 코드를 같은 꼴로 더하고 Property-based 를 N/A 로 두지 않으며, ship-check 는 표본 유무 · 인용을 세고 undecided 를 Human checks 로 나름. 남은 빈틈: 1B 위험 2번의 제목 꼴 넷은 트래커 Phase 1B "출하 뒤 고침" 줄과 스모크 S-056(테스트 파일만, 12조 첫 본보기)으로, `### 11.` 소제목 번호는 1B 받아들인 사각지대로. 출하된 링크 검사 · 크롬 폴더 점검의 빈틈은 H-020 · H-029 그대로(12조는 고친 코드에만). 지금 도는 1C · 6B 레인은 12조 전에 떠서 보지 못함 — 처음 닿는 것은 Phase 7 · 8 · 스윕. 이 꼴이 다시 오르면 12조가 실제 사이클에서 어떻게 돌았는지부터 본다

- [x] ~~(retro 후보 · E-009) 계약 설명 문장이 코드보다 넓게 약속한 꼴이 헌법 9조가 선 뒤에도 다시 오름 — 9조는 돌았고(약속 짝 있음 · 초록) 짝 테스트가 문장이 묶은 출처 하나(jev `model`)에 표시 글을 안 심어 못 봄(E-023) — 최소 계약 고침: `.adw/constitution.md:41-46`(9조 plan 줄)에 한 구 — "여러 출처를 묶는 약속(밖에서 온 글 · 모든 ~)은 짝 줄에 그 출처를 칸 이름으로 적고 짝 테스트가 출처마다 표시 글을 심는다; 심지 않은 출처는 `not a promise: <why>` 이거나 문장을 그만큼 줄인다" (sightings: 20261013-062542-adw/phase-1-foundation-contracts · 20261013-161358-adw/phase-4-trigger-timing · 20261014-035728-adw/phase-6a-live-check-prepare — 9조 뒤 첫 목격)~~ — 헌법 9조 고침으로 닫음 (2026-10-14 원격 인터뷰 · 슬롯 0bb8fd92 · Q1–Q6 A · `0f84d40`) — 원안(출처를 칸 이름으로 나열)은 놓친 jev `model` 이 문장 괄호에도 없어 계획자가 떠올린 만큼만 잡으므로 경계에서 표시로 바꿈: 흐름 약속(바깥 글이 어디에만 / 어디에는 없다)은 계획이 뜻으로 가려 짝 줄에 `[boundary: … — unmarked: …]` 꼬리표, 짝 테스트는 가짜가 돌려주는 글 칸 모두에 표시(모양 칸은 `MRK…`, 숫자 · 날짜 · 참거짓 칸만 이유와 함께 뺌), 계획이 놓친 줄은 verify-plan 이 표시 검사 V<m> 로 메워 사이클 안에서 줄임. 길 축(1A 화면 접힘, E-026)은 넣지 않음 — 다시 목격되면 retro 가 올림. Phase 7 · 8 부터, 6B · 1C 레인은 옛 9조. 덧: 6A 의 영상 ID(`videos[].video_id` · `errors[].video_id`)도 계약 "`untrusted` 칸 안에만" 문장 밖 — H-049 를 정하는 6B 에 사람이 전함

- [x] ~~(retro 후보 · E-030) 인터뷰가 민감 확인 줄을 트래커만 고쳐 확정해도(코드 그대로) 사이클이 verify-run 부터 다시 돌아 같은 트리에서 verify-run · ship-check 전체를 한 번 더 함 — 최소 계약 고침: 허브의 확인 인터뷰 뒤 재개 자리(`hub:move` → `step: verify-run`)를, 판정한 트리와 HEAD 사이 `plans/` 밖 diff 가 비었을 때 ship-check 로 두고 ship-check 는 앞 보고서를 옮겨 새 트래커 결정 줄만 다시 추적 — 허브 · `.claude/skills/ship-check/SKILL.md` 는 ADWS 동기화 하네스라 고침은 상류에서(E-011 선례) (sightings: 20261014-035715-adw/phase-1a-parser-allow-rules · 20261014-112313-adw/phase-1c-text-config-allow)~~ — ADWS 백로그로 이관 (2026-10-14 원격 인터뷰 · 슬롯 40effaa6 · Q1 A · Q2 A) — `~/project/ADWS/.adw/backlog.md` To do 끝의 `(retro 후보 · marketing-agent-demo E-030 이관)` 줄. 원인은 확인 도장 `human_checks.py confirm` 이 ship-report 만 다시 쓰는 것이었다: 인터뷰의 트래커 커밋 뒤 verify-report 가 "마지막 커밋보다 낡음"이 되어 허브 ↪ Move 의 R2″(`scripts/hub/lanemove.py:500-503`)가 ship-explain 을 막는다(커밋 없이 도장만 찍은 1B 는 다시 돌지 않음). 고침은 원안(재개 자리를 ship-check 로 · ship-check 옮겨 쓰기 모드, 세 곳)보다 작게 넘김: `confirm` 이, 판정 뒤 바뀐 경로가 모두 `plans/` 이고 PASS 일 때만 verify-report 도 이어받아 ↪ Move → ship-explain 이 열리게 하고, 허브 · 드라이버의 낡음 규칙은 그대로 둔다. 받아들인 값: 새 트래커 줄은 기계가 다시 대조하지 않고, 1C 에서 R7 · R8 을 건진 우연한 두 번째 감사도 사라짐. 1A 처럼 계약 문서도 고친 확인은 고침 뒤에도 전부 다시 돎(맞는 동작). 그 사이 헌법 임시 조항은 두지 않음 — 인터뷰가 verify-report 를 손으로 이어받으면 경로를 잘못 읽은 날 autonomy full 게이트가 검사 안 된 변경을 병합하므로. 고침이 올 때까지 인터뷰가 레인에 커밋한 민감 확인 정지마다 verify-run · ship-check 재실행(18–30분 · $9–15)을 감수한다. 다시 오르면 이 줄로 흡수해 닫는다

- [ ] (retro 후보 · E-034) 트래커만 고친 확인 인터뷰 뒤 두 번째 ship-check 가 같은 코드 트리에서 새 결함을 찾음(1C R7 · R8, 6B R12 · S-075) — E-030 상류 고침이 받아들인 "새 트래커 줄은 기계가 다시 대조하지 않음"을 다시 볼지 — 최소 계약 고침: ADWS 백로그 `(retro 후보 · marketing-agent-demo E-030 이관)` 줄의 받아들인 값 — `human_checks.py confirm` 이 verify-report 를 이어받을 때 인터뷰가 더한 트래커 줄만 Spec compliance 로 다시 추적하는 좁은 ship-check 하나를 남김 (sightings: 20261014-112313-adw/phase-1c-text-config-allow · 20261014-112322-adw/phase-6b-live-check-apply)

## Done

<!-- Move finished items here, or mark them [x] above -->
