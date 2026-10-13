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

### E-011 · tooling — `retro_collect.py` 의 `_tokens` 는 `Files:` 줄 경로의 양끝에서 `.` 를 벗긴다 — 점으로 시작하는 파일은 plan 이 `Files:` 에 적어도 "계획 밖 파일" · T4 경보 ⑷ 에 늘 들어간다(`.env.example` → `env.example`, `.gitignore` → 점이 없어져 경로로 안 보고 버림)
- evidence: `.claude/skills/plan/scripts/retro_collect.py:437` `tok = tok.strip("`,;.…").lstrip("+")`. `python3 -I` 로 `declared_paths(plan.md)` → `'env.example'` 있음 · `'.env.example'` 없음, `_tokens('Files: .gitignore, .env.example')` → `{'env.example'}`. 이 사이클 plan.md:495 `Files: requirements.txt, .env.example, docs/research/jev.md, docs/contracts.md` 인데 번들 ⑷ = 1 — `.env.example` (cycle 20261013-161343-adw/phase-3-classifier-topic). Phase 1 의 ⑷ 13 에 든 `.env.example` · `.gitignore` 도 같은 벗김을 거쳤다(그 사이클의 원인 설명은 E-002)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-012 · tooling — 이 기계에는 `typesafe_sdk` 도 `pip-audit` 도 없고 `TYPESAFE_API_KEY` 도 없다 — 판별 테스트는 `tests/test_classifier.py` 의 가짜 SDK 로만 돌고, 정확도 러너 `python3 -m tests.jev_accuracy` 와 의존성 감사는 아직 한 번도 돌지 않았다
- evidence: `python3 -c "import typesafe_sdk"` → ModuleNotFoundError (notes.md Expertise check, 2026-10-13); ship-report R12 (`pip-audit` 없음 · 미측정) · R13 (계약 11절 `기록: 아직 재지 않음`); 가짜 `TypeSafeAPIResponseValidationError`(tests/test_classifier.py:147)의 부모가 진짜 0.7.4 휠 `_core/errors.py:176` 과 다름(R4 → S-016) (cycle 20261013-161343-adw/phase-3-classifier-topic)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-013 · codebase — `docs/contracts.md:5-6` 머리 문단은 `src/agent/` 모듈을 하나씩 열거하는데, 모듈을 더한 페이즈가 그 목록을 고치지 않는다 — main 에는 `trigger.py`(Phase 4)가 빠졌고 이 브랜치는 `classifier.py` 도 빠뜨렸다
- evidence: `git show main:docs/contracts.md` 5-6행 = `config.py` · `models.py` · `store.py` · `guard.py` · `logbook.py` · `scheduler.py` 뿐인데 `git ls-tree --name-only main src/agent/` 에 `trigger.py` 가 있음; 이 브랜치 ship-report R5 → S-017 (`classifier.py`) (cycle 20261013-161343-adw/phase-3-classifier-topic; 첫 목격 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-014 · hazard — 계약의 새 절 번호는 레인마다 자기 base 에서 매긴다 — main 의 `## 11. 트리거 판정 — trigger.py` 와 이 브랜치의 `## 11. 주제 판별 — classifier.py (Phase 3)` 가 같은 번호라, 착지 때 절 번호와 `config.py` 키 꼬리 · `config.yaml` · `VALID` · `CommittedConfigTest` · `requirements.txt` 의 겹친 추가분을 합쳐야 한다
- evidence: `git show main:docs/contracts.md | grep -n '^## 1[0-9]\.'` → 452행 `## 11. 트리거 판정 — trigger.py`; 이 브랜치 `docs/contracts.md:472` `## 11. 주제 판별 — classifier.py (Phase 3)`; ship-report Human checks 4번째 줄 (lane 2 · 4 · 5 와 겹침) (cycle 20261013-161343-adw/phase-3-classifier-topic)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-015 · tooling — `smoke_file.py` 의 `verdict()` 는 verify-report **전체**에서 줄머리 `FAIL` 을 찾고 그것을 `PASS` 보다 먼저 본다 — `## Verdict` 가 PASS 여도 본문에 검사 출력 줄(`  FAIL labels: …`)이 있으면 "verify FAIL" 로 읽고, ship-report 의 스모크 후보를 one-pass 로 한 번 더 올린다
- evidence: `.claude/skills/plan/scripts/smoke_file.py:73-76` (`V_FAIL.search(text)` 를 리포트 전체에), 패턴 `.claude/skills/plan/scripts/retro_collect.py:109` `^[^\w]*\**\s*FAIL\b` (re.M). `python3 -I` 로 이 사이클 verify-report 를 읽으면 `verdict(전체)` = FAIL · `verdict(section_body(…, "Verdict"))` = PASS · 첫 일치 62행 `  FAIL labels: check_probability_above_o…`(V4 음성 대조 출력). 결과: 스텝 note "ship READY · verify FAIL · 5 candidate(s)", 홈 `.adw/smoke-log.md` 에 같은 다섯 고침이 두 번 열림 — S-019~S-023(`deferred by ship-check`) = S-024~S-028(`filed by smoke-file (one-pass)`) (cycle 20261013-161439-adw/phase-5-writer-comment)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-016 · tooling — 이 기계에는 `anthropic` 도 없다 — 댓글 작성기 테스트는 `tests/test_writer.py` 의 가짜 Claude 로만 돌고, `anthropic_client()` · 모델 id `claude-sonnet-5-5` · 통과 하한 0.7 은 실제 API 로 한 번도 돌지 않았다 (jev 쪽은 E-012)
- evidence: `python3 -c "import anthropic"` → `ModuleNotFoundError: No module named 'anthropic'` (이 retro, 2026-10-13; notes.md Expertise check 도 같음); ship-report `## Human checks` 1번째 줄(실제 키 확인 남음) · R8(감사 4 가 호출 모양을 이 기계 밖 1.13.0 에서 따로 맞춤) (cycle 20261013-161439-adw/phase-5-writer-comment)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

### E-017 · hazard — 작성기 링크 검사 `_link_char`(src/agent/writer.py:115-124)는 유니코드 이름에 `_SEPARATOR_NAMES`(`DOT` · `FULL STOP` 등)가 든 글자만 점으로 남기고 나머지 기호는 버리며, `_LINK_RE` 의 끝은 `[a-z]{2,}` 다 — 점 닮은꼴(U+2027 `‧` · U+2022 · U+2219 · U+00B0) · 키릴 끝 · U+202E 뒤집기로 쓴 주소는 코드 검사를 지나고 jev 광고 질문만 남는다. E-005 와 같은 "열거한 꼴" 부류가 Phase 1 밖에서 처음 목격된 것
- evidence: ship-report R1 — `bit‧ly/3xYzAb` 가 `bitly/3xyzab` 로 읽혀 통과(감사 재현); `## Human checks` 3번째 줄 — 어디까지 막을지는 사람 결정(보이지 않는 글자를 다 막으면 U+200D 이모지 잇기도 막힘). 실제 게시는 허용 목록뿐(`src/agent/guard.py:94`) (cycle 20261013-161439-adw/phase-5-writer-comment)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-13

## Retired (history — one line each, never deleted)
- E-001 · gotcha — [stop:red-unbucketable · 1] ship-check BLOCKED 이고 통이 그 고침을 못 받는다 — 이 페이즈는 제 브랜치에서 아래 Blockers 를 범위로 다시 돈다 — retired 2026-10-13 (shipped (Phase 1 ship 게이트 승인 2026-10-13; `youtu.be/A/../B` 꼴은 `5352cf8` 로 막힘 — notes.md Expertise check))
