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

## Retired (history — one line each, never deleted)
- E-001 · gotcha — [stop:red-unbucketable · 1] ship-check BLOCKED 이고 통이 그 고침을 못 받는다 — 이 페이즈는 제 브랜치에서 아래 Blockers 를 범위로 다시 돈다 — retired 2026-10-13 (shipped (Phase 1 ship 게이트 승인 2026-10-13; `youtu.be/A/../B` 꼴은 `5352cf8` 로 막힘 — notes.md Expertise check))
