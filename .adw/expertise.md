# Expertise

## Open items

### E-002 · tooling — 계획 밖 파일 · T4 경보 ⑷ 는 `main..브랜치` 전체 diff 를 **마지막** plan.md 의 `Files:` 줄과만 대조한다 — 앞 사이클이나 understand 부터 다시 돈 사이클이 남긴 커밋의 파일은 모두 "계획 밖"으로 센다
- evidence: 이번 ⑷ 13개(`.env.example` · `.gitignore` · `config.yaml` · `src/agent/store.py` · `src/agent/scheduler.py` · `tests/test_gitignore.py` …)는 모두 `1baaf13` 앞 커밋(첫 implement `63fab05`…`bce162f`, 07:08 복구 plan 의 `9a4b6c5` · `2262eca` · `56eec24`)의 파일이고, 11:09 에 다시 쓴 plan.md:402-473 의 `Files:` 줄은 HC1 고침 10개만 이름 붙인다 — verify-run V18 이 `git diff --name-only 1baaf13 7e39c3a` = 정확히 그 10개로 초록 (cycle 20261013-062542-adw/phase-1-foundation-contracts)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-003 · gotcha — `verify-run` 부터 다시(control retry)는 옛 verify-plan 을 그대로 쓴다 — 그 사이 인터뷰가 트래커만 커밋해도 범위 끝을 `HEAD` 로 둔 검사는 빨개진다
- evidence: 14:28 retry 본 패스에서 V18(`git diff --name-only 1baaf13 HEAD` = 10개)이 HC1-2 트래커 커밋 `a35981b` 때문에 11줄로 빨강; 범위를 verify-plan 이 잰 `7e39c3a` 로 고정하고 "그 뒤는 트래커 하나만"을 단언하자 초록, 음성 대조 3개는 그대로 빨강 (verify-report.md Fixes applied 1). `.adw/verify.sh` 는 git 이 무시해(`.adw/.gitignore:23`) 이 고침엔 커밋 SHA 가 없다 (cycle 20261013-062542-adw/phase-1-foundation-contracts)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-004 · tooling — 이 기계의 셸 `grep` 은 GNU grep 이 아니라 ugrep 7.8.4 를 부르는 셸 함수다 — GNU grep 의 동작(NUL 이 든 파일의 `binary file matches` 등)을 재는 시험은 `/usr/bin/grep` 을 경로로 불러야 같은 것을 잰다
- evidence: ship-report.md:320 (R5); `type grep` → "grep is a function", `/usr/bin/grep` 따로 있음 (cycle 20261013-062542-adw/phase-1-foundation-contracts)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-005 · hazard — Phase 1 의 세 파서(가드 주소 읽기 · 로그 줄 이스케이프 · 설정 숫자 읽기)는 열거한 꼴 목록으로 막는다 — ship-check 네 번이 매번 목록 밖 꼴을 하나 이상 더 찾았다
- evidence: 트래커 Phase 1 결정 기록 — `youtu.be/A/../B`(첫 BLOCKED) → `?v=B` · `U+2028` · `.inf`·큰 수(HC1) → 로그 NUL·ESC(HC1-2) → 이번 ship-report R1 · R2 · R4
- 남은 꼴(최종 트리 `a35981b`, 실측): `youtu.be/A?v\x01` · `shorts/A?v\x00` → A 로 live(다른 영상 · 호스트 0, ship-report.md:283-297) · 로그를 latin-1 로 읽고 `splitlines()` 하면 UTF-8 에 `0x85` 가 든 한글(11,172자 중 364자, 예 `갅` = `ea b0 85`)이 NEL 이 되어 가짜 `POST … mode=live result=posted` 조각이 `parse_line` 을 통과(ship-report.md:261-281) · `0x`+F 3,700개 같은 정수 설정이 4,456자리 int 로 `load_config` 를 통과한 뒤 `START interval_min=` 쓰기에서 파이썬 4300자리 한도 `ValueError`(ship-report.md:307-315)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-006 · tooling — [stop:unknown · 1] 정지 부류 표에 "ship-check sensitive human checks — confirm in the interview before merge" 행이 없다 — 민감 확인 줄로 머지 전에 멈춘 ship-check 는 부류 `unknown` 으로 남는다
- evidence: `.adw/journal/20261013-122544-stop-1/stop.md:1,5-6`(홈 트리) — "stop: ship-check · unknown · 1 · seen 2", "lesson: 표에 없는 정지 — 사유를 읽고 부류를 정한다"; 같은 꼴 첫 목격 20261013-075734-stop-1. 같은 stop.md 에 `stale harness: yes` — 현 하네스 표에 행이 이미 생겼는지는 이 retro 가 확인하지 못함
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-007 · codebase — `judge_trigger` 는 기록 한 번(`too_few_samples`) · 조회수 미달/초과(`views_below_min` · `views_above_max`) 검사를 나이 검사(`too_old`)보다 먼저 한다 — 나이 창이 닫힌 영상도 그 셋 중 하나면 영원히 `too_old` 를 받지 못하고, 계약 11절의 설명 문장("바뀌지 않는 것은 `too_old` 뿐 … `views_below_min` 과 모든 `hold` 는 `yes` 가 될 수 있다", "조회수가 줄면 … `hold` … 나이 창이 닫히면 `too_old` 로 끝남")은 이 영상들에 대해 틀린다
- evidence: `src/agent/trigger.py:48,51,53` 이 `:57`(`too_old`)보다 앞; `docs/contracts.md:485-492`; ship-report Q2 재현 — 72h 500→600 `('no', 'views_below_min')` · 72h 기록 한 번 `('hold', 'too_few_samples')` · 1450→0 삭제 `('no', 'views_below_min')`. 표(차례)는 결정대로, 틀린 것은 문장 — 고칠 방향은 Human checks 1 (cycle 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-008 · codebase — `VideoRecord` 는 일반(`frozen` 아님) dataclass 이고 `__post_init__` 에서만 검증한다 — 생성 뒤 필드 대입은 검증을 건너뛰고, `view_history` 검증(`_items`)은 원소 타입만 볼 뿐 시각 순서 · 중복 · 시간대 종류를 보지 않는다
- evidence: `src/agent/models.py:231-256` (`@dataclass` 인자 없음, `_items` 는 `isinstance` 만); `src/agent/trigger.py:23` 이 `(at, count)` 로 직접 정렬해 순서를 스스로 정함; verify-plan Fuzzing N/A 가 이 검증에 기대 DST 구멍(Q1 → `S-011`)을 숨김 (ship-report Coverage settlement) (cycle 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-009 · reviewer — ship-check 가 두 페이즈 연속 계약 문서의 설명 문장이 코드보다 넓게 약속한 것(보장 · "바뀌지 않음" · "~에만" 꼴)을 찾아 사람 확인으로 올렸다 — 코드와 표는 맞고 그 아래 문장이 틀린 꼴이며, 고치는 길이 공개 계약을 건드려 스모크 통에 못 들어간다
- evidence: Phase 1 — 계약 2절 "비교와 셈에만"(R4) · 7절 문단(R5) (journal 20261013-062542-adw-phase-1-foundation-contracts summary flagged ②③); Phase 4 — 11절 세 문장 R1/Q2 → Human checks 1 (E-007) (cycle 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-010 · reviewer — 페이즈가 하류 페이즈에 넘긴 일과 주인 없이 받아들인 위험이 `plan.md` · 계약에만 남고 트래커의 하류 페이즈 절에는 오르지 않는다 — ship-check 가 두 페이즈 연속 "트래커 Phase 2 · 7 절에 주인 줄 적기"를 사람 확인으로 올렸고, Phase 1 에서는 주인 없이 받아들인 위험이 다음 ship-check 에 돌아왔다
- evidence: Phase 1 summary flagged ②④ · Coverage ①(R3 · R6 가 두 번째 ship-check 에 돌아와 understand 부터 다시); Phase 4 ship-report R4 · R5 → Human checks 2 — 트래커 Phase 2 · 7 절 `간격|spacing` 검색 → 없음, 넘긴 일은 `.adw/plan.md:573-588` 과 계약 11절에만 (cycle 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

## Retired (history — one line each, never deleted)
- E-001 · gotcha — [stop:red-unbucketable · 1] ship-check BLOCKED 이고 통이 그 고침을 못 받는다 — 이 페이즈는 제 브랜치에서 아래 Blockers 를 범위로 다시 돈다 — retired 2026-10-13 (shipped (Phase 1 ship 게이트 승인 2026-10-13; `youtu.be/A/../B` 꼴은 `5352cf8` 로 막힘 — notes.md Expertise check))
