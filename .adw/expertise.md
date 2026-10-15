# Expertise

## Open items

### E-002 · tooling — 계획 밖 파일 · T4 경보 ⑷ 는 `main..브랜치` 전체 diff 를 **마지막** plan.md 의 `Files:` 줄과만 대조한다 — 앞 사이클이나 understand 부터 다시 돈 사이클이 남긴 커밋의 파일은 모두 "계획 밖"으로 센다
- evidence: 이번 ⑷ 13개(`.env.example` · `.gitignore` · `config.yaml` · `src/agent/store.py` · `src/agent/scheduler.py` · `tests/test_gitignore.py` …)는 모두 `1baaf13` 앞 커밋(첫 implement `63fab05`…`bce162f`, 07:08 복구 plan 의 `9a4b6c5` · `2262eca` · `56eec24`)의 파일이고, 11:09 에 다시 쓴 plan.md:402-473 의 `Files:` 줄은 HC1 고침 10개만 이름 붙인다 — verify-run V18 이 `git diff --name-only 1baaf13 7e39c3a` = 정확히 그 10개로 초록 (cycle 20261013-062542-adw/phase-1-foundation-contracts)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-15

### E-009 · reviewer — ship-check 가 두 페이즈 연속 계약 문서의 설명 문장이 코드보다 넓게 약속한 것(보장 · "바뀌지 않음" · "~에만" 꼴)을 찾아 사람 확인으로 올렸다 — 코드와 표는 맞고 그 아래 문장이 틀린 꼴이며, 고치는 길이 공개 계약을 건드려 스모크 통에 못 들어간다
- evidence: Phase 1 — 계약 2절 "비교와 셈에만"(R4) · 7절 문단(R5) (journal 20261013-062542-adw-phase-1-foundation-contracts summary flagged ②③); Phase 4 — '트리거 판정' 절 세 문장 R1/Q2 → Human checks 1 (E-007) (cycle 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-15

### E-010 · reviewer — 페이즈가 하류 페이즈에 넘긴 일과 주인 없이 받아들인 위험이 `plan.md` · 계약에만 남고 트래커의 하류 페이즈 절에는 오르지 않는다 — ship-check 가 두 페이즈 연속 "트래커 Phase 2 · 7 절에 주인 줄 적기"를 사람 확인으로 올렸고, Phase 1 에서는 주인 없이 받아들인 위험이 다음 ship-check 에 돌아왔다
- evidence: Phase 1 summary flagged ②④ · Coverage ①(R3 · R6 가 두 번째 ship-check 에 돌아와 understand 부터 다시); Phase 4 ship-report R4 · R5 → Human checks 2 — 트래커 Phase 2 · 7 절 `간격|spacing` 검색 → 없음, 넘긴 일은 `.adw/plan.md:573-588` 과 계약 '트리거 판정' 절에만 (cycle 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-14

### E-013 · codebase — `docs/contracts.md:5-6` 머리 문단은 `src/agent/` 모듈을 하나씩 열거하는데, 모듈을 더한 페이즈가 그 목록을 고치지 않는다 — main 에는 `trigger.py`(Phase 4)가 빠졌고 이 브랜치는 `classifier.py` 도 빠뜨렸다
- evidence: `git show main:docs/contracts.md` 5-6행 = `config.py` · `models.py` · `store.py` · `guard.py` · `logbook.py` · `scheduler.py` 뿐인데 `git ls-tree --name-only main src/agent/` 에 `trigger.py` 가 있음; 이 브랜치 ship-report R5 → S-017 (`classifier.py`) (cycle 20261013-161343-adw/phase-3-classifier-topic; 첫 목격 20261013-161358-adw/phase-4-trigger-timing)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-14

### E-015 · tooling — `smoke_file.py` 의 `verdict()` 는 verify-report **전체**에서 줄머리 `FAIL` 을 찾고 그것을 `PASS` 보다 먼저 본다 — `## Verdict` 가 PASS 여도 본문에 검사 출력 줄(`  FAIL labels: …`)이 있으면 "verify FAIL" 로 읽고, ship-report 의 스모크 후보를 one-pass 로 한 번 더 올린다
- evidence: `.claude/skills/plan/scripts/smoke_file.py:73-76` (`V_FAIL.search(text)` 를 리포트 전체에), 패턴 `.claude/skills/plan/scripts/retro_collect.py:109` `^[^\w]*\**\s*FAIL\b` (re.M). `python3 -I` 로 이 사이클 verify-report 를 읽으면 `verdict(전체)` = FAIL · `verdict(section_body(…, "Verdict"))` = PASS · 첫 일치 62행 `  FAIL labels: check_probability_above_o…`(V4 음성 대조 출력). 결과: 스텝 note "ship READY · verify FAIL · 5 candidate(s)", 홈 `.adw/smoke-log.md` 에 같은 다섯 고침이 두 번 열림 — S-019~S-023(`deferred by ship-check`) = S-024~S-028(`filed by smoke-file (one-pass)`) (cycle 20261013-161439-adw/phase-5-writer-comment)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-14

### E-017 · hazard — 작성기 링크 검사 `_link_char`(src/agent/writer.py:115-124)는 유니코드 이름에 `_SEPARATOR_NAMES`(`DOT` · `FULL STOP` 등)가 든 글자만 점으로 남기고 나머지 기호는 버리며, `_LINK_RE` 의 끝은 `[a-z]{2,}` 다 — 점 닮은꼴(U+2027 `‧` · U+2022 · U+2219 · U+00B0) · 키릴 끝 · U+202E 뒤집기로 쓴 주소는 코드 검사를 지나고 jev 광고 질문만 남는다. E-005 와 같은 "열거한 꼴" 부류가 Phase 1 밖에서 처음 목격된 것
- evidence: ship-report R1 — `bit‧ly/3xYzAb` 가 `bitly/3xyzab` 로 읽혀 통과(감사 재현); `## Human checks` 3번째 줄 — 어디까지 막을지는 사람 결정(보이지 않는 글자를 다 막으면 U+200D 이모지 잇기도 막힘). 실제 게시는 허용 목록뿐(`src/agent/guard.py:94`) (cycle 20261013-161439-adw/phase-5-writer-comment)
- first confirmed: 2026-10-13 · last confirmed: 2026-10-15

### E-022 · hazard — 계약 절 이름 테스트 `tests/test_contract_sections.py` 는 열거한 꼴만 잡는다 — 제목은 `HEADING_RE = ^## ([0-9]+)\.`(:20), 인용은 `([0-9]+)절`(:21) 뿐이라 `## 11 제목`(마침표 없음) · `## 11) 제목` · `##  11.`(공백 둘) · `### 11.` · 앞 공백 셋 `   ## 11.`(마크다운에서는 여전히 제목) 과 `§11` · `11 절` · ASCII 아닌 숫자는 초록으로 지나간다. E-005 · E-017 · E-019 와 같은 "열거한 꼴" 부류
- evidence: `tests/test_contract_sections.py:20-21`; 감사관이 다섯 제목 꼴을 `[]` 로 읽음 — journal `20261014-035724-adw-phase-1b-contract-section-names/ship-report.md:177-181`(Risks 2) · 돌연변이 표 `:145-148`; 인용 쪽 사각지대는 트래커 Phase 1B 질문 1 trade-off 가 받아들임, 제목 쪽은 아직 결정 없음(질문 2 A 빨강 꼴 ① 밖). verify-plan.md:127 Property-based N/A "two regexes over a small enumerated shape set" 가 이 꼴들을 ship-check 까지 가렸다 (cycle 20261014-035724-adw/phase-1b-contract-section-names)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-14

### E-023 · reviewer — 헌법 9조의 약속 짝은 짝 테스트가 초록이면 지나간다 — "밖에서 온 글 … 에만"처럼 여러 출처를 묶는 약속은 짝 테스트의 가짜가 표시 글을 심은 출처까지만 재고, 심지 않은 출처(가짜 jev 의 `model`)로 넓은 문장이 남아 ship-check 가 E-009 꼴로 다시 사람 확인에 올린다
- evidence: `.adw/plan.md:1042` `Promise: "밖에서 온 글과 모델이 쓴 글은 \`untrusted\` 칸 안에만" → tests/test_live_check.py::ResultShapeTest::test_untrusted_text_only_under_untrusted`(`tests/test_live_check.py:2118`, 초록) · 코드는 jev 답의 `model` 을 검사 없이 100자까지 `fingerprint.jev_models` 에 둔다(`tests/live_check.py:503-509`) · `docs/contracts.md:1078-1080` · ship-report R3 "짝지은 약속 테스트 … 가짜 jev 의 모델 이름에 표시 글을 넣지 않아 이것을 보지 못합니다" (cycle 20261014-035728-adw/phase-6a-live-check-prepare)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-024 · codebase — 저장소의 손편집 파일 읽기는 모두 `utf-8-sig`(BOM 허용)이고 이 관례는 코드에만 있다 — 새 읽기 `tests/live_check.py:445`(`--verdict`)는 `utf-8` 이라, 사람이 사람 칸을 고친 `result.json` 에 편집기가 BOM 을 붙이면 종료 2 "읽을 수 없음"이 난다
- evidence: `grep -rn utf-8-sig src/` → `src/agent/config.py:322` · `src/agent/store.py:59` · `src/agent/env.py:25` · `src/agent/youtube.py:155`; `tests/live_check.py:445` `json.loads(Path(path).read_text(encoding="utf-8"))`; ship-report Quality review 3 · R4 (cycle 20261014-035728-adw/phase-6a-live-check-prepare)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-025 · codebase — `YouTubeError` 는 글자열 두 개(`call` · `reason`)만 든다(상태 코드 · 오류 이유 속성 없음) — 403 종류 구분은 글자열 같음 비교(`exc.reason == COMMENTS_DISABLED`)에 기대고, 200 모양 오류도 같은 예외라 받는 쪽이 오류 종류를 가르지 못한다
- evidence: `src/agent/youtube.py:69-75`(`__init__(self, call, reason)`) · `:41` `COMMENTS_DISABLED = "HTTP 403 commentsDisabled"` · `:277` `if exc.reason == COMMENTS_DISABLED:`; 모양 오류가 `except YouTubeError: continue` 로 삼켜지는 자리는 ship-report R1(`tests/live_check.py:1026-1029`) (cycle 20261014-035728-adw/phase-6a-live-check-prepare · understand 후보 2)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-14

### E-026 · reviewer — 헌법 9조 짝 테스트가 초록이어도 약속 문장은 그 테스트가 재는 것보다 넓을 수 있다 — 9조 첫 사례(Phase 1A)에서 빠진 짝은 0 이었지만 PARTIAL 이 7개였고, 짝이 초록인 계약 7절 "터미널에 가짜 줄이 그려지지 않습니다" 는 화면 폭 접힘까지 약속해 ship-check 가 사이클 안 줄이기가 아니라 사람 확인(R4)으로 올렸다
- evidence: `.adw/ship-report.md:350-362` (Promise 정산 — MISSING 0 · PROVES L68 · L301 · L445 · PARTIAL 7, L445-446 짝은 입력 넷뿐이라 변이 l14 가 짝을 통과) · `:442-450` (R4) · `:477` (민감 확인 줄, confirmed 2026-10-14); 인터뷰가 `3a4a6e7` 로 문장을 짝이 재는 만큼으로 좁힘. E-009 부류의 9조 뒤 첫 목격 (cycle 20261014-035715-adw/phase-1a-parser-allow-rules)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-14

### E-027 · gotcha — 가드의 youtu.be · shorts 거절 행이 한 검사(`;` 나누기 등)를 재려면 쿼리의 다른 이름이 모두 받는 이름(`si` · `t` · `feature`)이어야 한다 — 셋 밖 이름은 먼저 막혀 행이 다른 이유로 초록이 된다. Phase 1 의 S-003 잠금 행 `?x=1;y=2;v=B` 가 1A 뒤 그렇게 풀려, `guard.py:65` 의 `replace(";", "&")` 를 첫 구분자만 바꾸게 한 변이 g1 이 스위트 461개 초록으로 산다
- evidence: `tests/test_guard.py:47` (S-003 행) · `src/agent/guard.py:23,65`; `.adw/ship-report.md:405` (가드 표 G1 의 `;` 행은 하나짜리 꼴만) · `:418-421` (R1) → S-056 이 받는 이름만 든 행으로 다시 잠금 (cycle 20261014-035715-adw/phase-1a-parser-allow-rules)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-028 · tooling — `tests/mutants.py` 의 변이는 소스에서 바꿀 글자가 **정확히 한 번** 나와야 돈다(아니면 종료 코드 2) — 가드 · 로그 · 설정의 한 줄을 고치는 페이즈는 그 줄을 겨눈 변이 문자열도 함께 고쳐야 하고, 같은 글자를 한 번 더 쓰는 줄을 더하기만 해도 기존 변이가 깨진다
- evidence: `tests/mutants.py:9-10` 머리말("2 는 이름을 모르거나 바꿀 글자가 정확히 한 번 나오지 않았다는 뜻"); 1A 가 고친 가드 줄을 겨눈 `guard-youtu-be-ignores-query-v` · `guard-shorts-ignores-query-v` · `guard-query-ampersand-only`(`tests/mutants.py:139,145,151`); 등록부 82 → 90 (cycle 20261014-035715-adw/phase-1a-parser-allow-rules)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-029 · tooling — PyYAML 이 읽은 16진수(`0x…`) 정수는 파이썬의 4,300자리 문자열 변환 한도를 읽기에서 거치지 않는다(2의 거듭제곱 진법은 한도 밖) — 십진 `str()` · `format` 에 닿아서야 `ValueError` 가 나므로, 십진수 행만 있는 시험은 이 꼴을 재지 않는다. 정수 키는 1A 의 필수 상한(`src/agent/config.py:174`)이 막지만, 새 숫자 읽기는 같은 꼴을 다시 만날 수 있다
- evidence: `python3 -I -c "import yaml; n=yaml.safe_load('k: 0x'+'F'*3700)['k']; str(n)"` → 14,800비트 int 로 읽힌 뒤 `ValueError: Exceeds the limit (4300 digits) for integer string conversion` (이 retro 실측); Phase 1 ship-report R4 · 트래커 Phase 1A 결정 2 (cycle 20261014-035715-adw/phase-1a-parser-allow-rules)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-14

### E-030 · tooling — 민감 확인 줄로 머지 앞에서 멈춘 사이클은 인터뷰가 트래커만 고치고 코드를 한 바이트도 바꾸지 않아도 허브가 verify-run 부터 다시 돌린다 — 같은 코드 트리에서 verify-run 과 ship-check 전체(감사 포함)가 한 번 더 돈다
- evidence: 이번 사이클 `.adw/gate/history/20261014-140655-cycle-control.json` `{"action": "retry", "issued_by": "hub:move", "step": "verify-run"}`; ship-report § Verdict "코드는 첫 판정 때와 한 바이트도 다르지 않고(그 뒤 바뀐 것은 트래커 10줄)" — 인터뷰 커밋 `4e859be` 는 `plans/` 만(+10줄); retro-bundle Steps verify-run 시도 2 · ship-check 시도 2 $15.4151 · 감사 부름 8(시도 2권 합) (cycle 20261014-112313-adw/phase-1c-text-config-allow). 앞 목격: Phase 1A — 인터뷰가 문서만 두 커밋(`3a4a6e7` · `681acc5`), `git diff 2e58209 HEAD -- src tests` 0바이트인데 verify-run · ship-check 시도 2 (journal 20261014-035715-adw-phase-1a-parser-allow-rules summary.md:17)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-031 · codebase — 설정 읽기 `_construct_mapping` 은 중복 키 검사보다 먼저 `loader.flatten_mapping(node)` 를 부른다 — YAML 병합 키(`<<`)로 앵커를 겹겹이 이은 작은 파일이 항목을 기하급수로 복사해, "키가 두 번 나옵니다" 오류나 "이전 설정 유지"에 닿기 전에 메모리를 다 쓸 수 있다
- evidence: `src/agent/config.py:84-85` (`def _construct_mapping` 첫 줄이 `loader.flatten_mapping(node)`, 중복 검사 `seen` 은 그 뒤 `:86-92`); ship-report R7 — 2,144바이트 파일 n=25 에서 2.97초 · 최대 RSS 1,081,456 KB 뒤 `키가 두 번 나옵니다`, n=30 은 약 32 GB 추정, base 와 HEAD 같음(n=22 0.36초 대 0.35초). 막으려면 설정 파일 형식(병합 키 · 별칭 금지) 결정이 필요해 주인 없음 (cycle 20261014-112313-adw/phase-1c-text-config-allow)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-14

### E-032 · tooling — 글자 규칙(`logbook._is_raw`, 설정 `_text` 가 같은 함수)의 판정은 실행 중인 파이썬의 `unicodedata` 판을 따르는데, 이 기계의 파이썬은 판이 둘이다 — `/usr/bin/python3` · `python3.14` 는 3.14.4(유니코드 16.0.0), `~/.local/bin/python3.12` 는 3.12.13(15.0.0)이고 `python3.10` · `python3.13` 은 PATH 에 없다
- evidence: 이 retro 실측 — `python3 -I -c "…unicodedata.unidata_version, unicodedata.category(chr(0x1FAE9))"` → `/usr/bin/python3 3.14.4 16.0.0 So` · `~/.local/bin/python3.12 3.12.13 15.0.0 Cn` · `/usr/bin/python3.14 3.14.4 16.0.0 So`; 트래커 Phase 1C Trade-offs(HC1 질문 1 B) — `topic: "연애 고민 🫩"` 이 3.14.4 에서 `load OK`, 3.12.13 에서 `ConfigError`(인터뷰가 잰 3.10.20 은 PATH 밖 다른 경로) (cycle 20261014-112313-adw/phase-1c-text-config-allow)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-14

### E-034 · reviewer — 트래커만 고친 확인 인터뷰 뒤의 두 번째 ship-check 는 코드가 같은 트리에서도 새 결함을 찾는다 — 6B 에서는 인터뷰가 막 쓴 트래커 줄 자체(Phase 6C 결정 문장, R12)가 6B 테스트보다 넓었다. E-030 상류 고침이 받아들인 "새 트래커 줄은 기계가 다시 대조하지 않음"이 이런 결함을 잃는다
- evidence: 이번 ship-report R12 — `plans/interview-marketing-agent.md:477` "이 페이즈가 채점을 고쳐도 main 은 초록 그대로다"를 감사 3 이 재현했다: 6C 후보 ① → `test_verdict_recount_is_go_with_one_line` · `test_summary_first_line_is_the_recount` FAIL, 새 지문 칸 → `test_every_fingerprint_key_is_sorted` FAIL. 같은 두 번째 실행이 R5 의 중복 줄 꼴(S-075)도 새로 찾았다. 인터뷰 커밋 `7bdb488` 은 `plans/` 만; retro-bundle Steps ship-check 시도 2 $26.0421 (cycle 20261014-112322-adw/phase-6b-live-check-apply). 앞 목격: 1C — 홈 `.adw/backlog.md` E-030 이관 줄 "1C 에서 R7 · R8 을 건진 우연한 두 번째 감사도 사라짐" (journal 20261014-112313-adw-phase-1c-text-config-allow)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-033 · tooling — 이 기계에는 여전히 `typesafe_sdk` 도 `anthropic` 도 없어 진짜 jev · Claude 호출은 사람 환경에서만 돈다 — 진짜 호출의 기록은 사람이 커밋한 `docs/live-check/result.json` 하나뿐이고(6A 실행기 `tests/live_check.py`), 스위트는 가짜 SDK(`tests/test_classifier.py`) · 가짜 Claude(`tests/test_writer.py`)로만 돈다. 다시 재려면 사람 재실행이 필요하다(트래커 6C → 6D 길)
- evidence: `python3 -I -c "import typesafe_sdk"` · `python3 -I -c "import anthropic"` → 둘 다 `ModuleNotFoundError` (이 retro 실측, 2026-10-14); `docs/live-check/result.json` `run_at 2026-10-14T04:28:16.180435+00:00` · `calls {'claude': 23, 'jev': 72, 'youtube': 17}` · `models` 두 이름 `accepted`; `tests/live_check.py:72` `from tests.jev_accuracy import PASS_CORRECT, REPO_CONFIG, judge_examples, tally`. E-012 · E-016 을 잇는다 (cycle 20261014-112322-adw/phase-6b-live-check-apply)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-037 · codebase — 실행기 테스트의 가짜 Claude(`tests/test_live_check.py` `FakeClaude.create`)는 `system` 글이 `GRADE_SYSTEM` · `TOPIC_SYSTEM` · `SKIP_GRADE_SYSTEM` 중 무엇과 같은지로 호출 종류를 가리고, 셋 다 아니면 오류 없이 `write`(작성)로 센다 — 실행기에 새 system 글로 Claude 를 부르는 호출을 더하는 페이즈가 가짜에 갈래를 더하지 않으면 그 호출은 작성 큐의 답을 받는다. 최악 호출 수를 글자로 잠근 `test_default_limits_fit_under_ceilings` 도 함께 본다
- evidence: `tests/test_live_check.py:1583-1594`(`system is None` → probe · `GRADE_SYSTEM` → grade · `TOPIC_SYSTEM` → topic · `SKIP_GRADE_SYSTEM` → skip_grade · `else` → write) · `:2229`(`{"jev": 114, "claude": 103, "youtube": 35}`, 6E 에서 그대로). 6C 가 `topic` 갈래를, 6E 가 `skip_grade` 갈래를 더했다 — 6E understand 가 옛 E-035 로 이 자리를 짚었고 plan-repairs R1 의 가짜 로그 `['topic', 'write', 'write', 'grade', 'skip_grade']` 가 새 갈래가 도는 것을 보였다 (cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · 20261015-091934-adw/phase-6e-comment-quality-fix)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-038 · tooling — 과제 안내 `docs/marketing-agent.pdf` 는 홈 체크아웃에 추적되지 않은 파일(`??`)로만 있어 레인 worktree 에는 없다 — 레인 안의 사이클(understand · plan · ship-check)은 과제 원문을 다시 읽지 못하고 트래커가 인용한 문장만 쓴다
- evidence: 레인에서 `ls docs/marketing-agent.pdf` → `No such file or directory`; `git -C <홈 체크아웃> status --short --ignored docs/marketing-agent.pdf` → `?? docs/marketing-agent.pdf`(무시 아님 · 추적 아님). 6E notes.md Expertise check 후보 3. 그래서 ship-report Human checks 3번째 줄은 계약 대조표의 ④-3 이 PDF 의 둥근 따옴표 “…” 대신 트래커 인용의 '…' 와 줄임을 따랐는지를 사람에게 넘겼다 (cycle 20261015-091934-adw/phase-6e-comment-quality-fix)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-039 · codebase — 실행기의 재료 채점(`SKIP_GRADE_SYSTEM`)과 작성 규칙의 '장면' 은 뜻이 다르다 — 재료 채점의 `material_has_scene` 은 `<video_title>` 도 장면 출처로 세지만, 작성 규칙 3 은 제목을 되풀이하는 것을 장면으로 치지 않는다. 제목만 있는 영상의 스스로 건너뜀('재료에 장면 없음')은 재료 채점에서 '부당' 쪽으로 기운다
- evidence: `tests/live_check.py:189-190`(`material_has_scene — … <video_title> · <video_description> · <top_comments> 안에 실제로 있습니까?`) · `src/agent/writer.py:33`(규칙 3 "장면 · 말은 설명이나 인기 댓글이 전하는 영상 속 장면 · 말뿐이고, 제목을 되풀이하는 것은 장면이 아닙니다"). ship-report Risks 4 · Human checks 7번째 줄(6F 가 "정당한 건너뜀 n/m" 을 셀 때 감안) (cycle 20261015-091934-adw/phase-6e-comment-quality-fix)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-040 · hazard — 작성 프롬프트 규칙 2 가 과제 문구 "비슷한 고민이 있었을 때" 를 그대로 담는다 — Claude 가 두 영상의 댓글에 이 문구를 베끼면 반복 검사(`REPEAT_MIN_CHARS = 12`)와 문장 틀 검사(`FRAME_MIN_CHARS = 6`)가 함께 걸려 다시 쓰기, 또는 '검사 두 번 탈락' `SKIP` 이 된다. 진짜 모델로는 재현 안 됨
- evidence: `src/agent/writer.py:32`(규칙 2 원문) · `:106` · `:112`. ship-report Risks 2 의 검사 출력 `이전 댓글과 겹칩니다: 비슷한고민이있었을때연애사주` 와 문장 틀 조각 `비슷한고민이`. 6F 의 SKIP 이유를 읽을 때 · Phase 7 이 `writer.py` 를 고칠 때 볼 자리 (cycle 20261015-091934-adw/phase-6e-comment-quality-fix)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-041 · reviewer — plan 이 등록한 변이(`tests/mutants.py`)는 새 판정의 경계(비교 연산 `<` ↔ `<=` · 범위 끝 한 글자)를 비틀지 않고, ship-check 의 변이 점검이 거기서 살아남은 변이를 찾아 테스트만 고치는 스모크 항목으로 보낸다 — 두 페이즈 연속. 착지와 스윕 사이에 다른 페이즈가 그 경계를 잘못 고치면 그 사이클의 스위트는 초록이다
- evidence: 6C — Guard B 첫 행 `target 2, min 0` 으로 `<=` 변이 M8a 생존 → R3 · S-077, 분모 변이 M23 생존 → R4 · S-078(6C summary.md Coverage decisions). 6E — verify-run V5 `mutants new: 8 run · caught 8` · V6 `47/47` 인데 ship-check 가 `_frame_pieces` 의 '연애사주' 빼기 앞 끝 · 뒤 끝과 `skip_human` 값 변이 생존을 재현 → S-093 · S-094(ship-report.md:173-176). 가드 매트릭스 행 규칙은 `.claude/skills/plan/SKILL.md:128`(변이 행만 `unmeasured` 허용) (cycle 20261014-172227-adw/phase-6c-live-check-grader-fix · 20261015-091934-adw/phase-6e-comment-quality-fix)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-043 · reviewer — 받아들인 위험 줄이 코드 자리를 적어도 입력 종류를 재현 입력의 조건으로 좁히면, 다음 ship-check 는 같은 자리에서 더 넓은 입력을 찾아 사람 확인으로 다시 올린다 — 헌법 11조의 ship-check 규칙("same site … different input class is a new risk")대로다. 멈춤이 끝나려면 그 자리가 받는 입력 전체를 입력 종류로 적어야 한다
- evidence: Phase 2 — 입력으로 적은 줄을 ship-check 가 같은 `except`(`src/agent/youtube.py:245`)에서 새 예외 꼴로 세 번 뚫었고, 자리로 다시 적은 뒤 다섯째 ship-check 는 새 멈춤이 없었다(옛 E-021, cycle 20261013-161159-adw/phase-2-watcher-detect). 6G — 🤖 브리핑(gate `20261015-153916-cycle-control.unconsumed.json`)이 적은 `skip_reason` 대가 줄(`fa66b56`)은 자리 `tests/live_check.py:1621` 를 이름 붙였지만 입력 종류가 "두 번 모두 코드 검사에서 떨어진" 경우뿐이었다. 같은 코드 트리의 다음 ship-check 가 "한 번만 반복 검사에서 떨어져도" 꼴을 찾아 `[sensitive: …]` 로 올렸고(journal 20261015-130935 ship-report.md:12 · :217), HC1 인터뷰가 "어느 한 번이라도 … 다른 시도가 무엇으로 떨어졌든" 으로 넓혀 다시 썼다(`92bf38f`) (cycle 20261015-130935-adw/phase-6g-live-check-redact)
- first confirmed: 2026-10-14 · last confirmed: 2026-10-15

### E-044 · gotcha — 레인 착지는 squash 없는 `merge --no-ff` 라(`.claude/skills/plan/scripts/finalize_step.py:1054`), 레인 끝 판에서만 지우거나 바꾼 내용도 앞 레인 커밋마다 남아 main 기록에 붙는다. 제출 때 main 이 공개되므로, 공개되면 안 되는 값은 그 값을 처음 더한 커밋에서부터 없어야 한다
- evidence: 6D — 허브가 결과 파일의 연락처를 끝 판에서만 지웠고(`f5cef6a`), ship-check 06:13 이 BLOCKED 했다(앞 커밋 9개에 그대로 남음). 드리프트 인터뷰가 레인 기록을 다시 썼다(cycle 20261014-225050-adw/phase-6d-live-check-reapply). 6G — 질문 4 A ④ 는 옛 표본(`795989b` · `5ad1374`: 실제 은행 앞자리 꼴 계좌와 `gmail.com`, 더한 줄 9개)을 끝 트리에서만 바꿨다. 세 번째 ship-check 이 역사에서 그 표본을 찾아 사람 확인으로 올렸고(journal 20261015-130935 ship-report.md:257), 다시 쓰지 않고 트래커 6G 대가 줄로 남겼다 (cycle 20261015-130935-adw/phase-6g-live-check-redact)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-045 · codebase — 실행기 결과 파일에는 작성기 · 판별기가 가공한 이유 글을 원문 그대로 싣는 칸이 아직 남아 있다. `videos[].untrusted.skip_reason`(`tests/live_check.py:1621` ← `src/agent/writer.py:379` "검사 두 번 탈락 — 1차: … / 2차: …", 반복 이유의 겹친 글자 · 링크 조각을 담음)와 `videos[].untrusted.classification_reason` · `accuracy[].untrusted.reason`(`tests/live_check.py:1569` · `:1393` ← `src/agent/classifier.py:125` `{choice!r}`)이 그렇다. 6G 가 이름과 숫자만 적게 바꾼 칸은 `drafts[].untrusted.code_failures` 하나다. 가공한 조각에서는 연락처 · 키 모양이 목록 밖 꼴이 되어, 쓰는 순간의 가림도 끝 줄도 그 모양을 보지 못한다
- evidence: 위 줄 번호는 트리 `92bf38f` 에서 grep 으로 확인. 두 번째 ship-check 막힘 1과 세 번째 ship-check 민감 줄 ① ② ③ → 트래커 6G Trade-offs accepted 의 `skip_reason` · 키 소문자 · `repr` 줄 셋. 트래커 6G Responsibilities "그때 고칠 자리는 이유 칸을 이름과 숫자만 적기(`skip_reason` · 판별 이유 칸, 질문 3 A 꼴)" (cycle 20261015-130935-adw/phase-6g-live-check-redact)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-046 · reviewer — plan 이 등록한 음성 대조는 새 판정 규칙의 줄은 비틀지만, 모듈을 잇는 진입점의 연결 줄(단계 호출 하나 · 울타리 뒤 저장 · 시작 거절 예외 묶음 · 출력 연결)은 비틀지 않는다. 그래서 그 줄을 망가뜨려도 스위트가 초록이다. ship-check 의 변이 점검이 거기서 살아남은 변이를 찾아, 테스트만 고치는 스모크 항목으로 보낸다. E-041(새 판정의 경계)과 같은 부류를 세 페이즈 연속(6C · 6E · 7) 본 것이다. 다른 점은 줄의 종류뿐이다
- evidence: 계획의 음성 대조 16개(`e27e7e3`)는 모두 빨강이다. 그런데 ship-check 가 `src/agent/run.py:266`(자체 검사 연결 `jev_self_check(self._services.ask, …)`) · `:331`(울타리 뒤 판별 `self._store.put`) · `:137`(이유 200자 · 공백 접기) · `:559`(main 의 `echo_stream` 연결) · `:492-496` · `:551`(시작 거절 묶음)에서 변이가 사는 것을 재현했다 → S-100 · S-101 · S-102(ship-report.md:187-190). 같은 자리들은 가드 매트릭스에도 행이 없었다(ship-report.md:220-224) (cycle 20261015-154340-adw/phase-7-pipeline-rules)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-047 · codebase — `decide_post` 는 허용 목록 검사를 지난 영상에만 `dry_run` 이유를 준다(목록 밖은 그보다 먼저 `not_in_allowlist`) — 그래서 `live=False` · `dry_run` 이 곧 "테스트 실행의 명단 영상" 이고 7F 리허설 갈래가 이것으로 나뉜다. 한편 테스트 쪽 중복 판정 `_is_duplicate(live=False)` 는 모드와 결과를 가리지 않고 시도가 하나라도 있으면 참이다(`COUNTED_RESULTS` 는 `posted` · `reserved` 만 센다) — 리허설이 시도를 하나라도 저장하면 같은 영상의 다음 리허설은 `SKIP duplicate_video` 가 된다
- evidence: `src/agent/guard.py:94-98` · `src/agent/store.py:27` · `:42-45`(트리 `bd90bf0`). ship-report R5 — 7F 전 테스트 실행의 `("test","saved","dry_run")` 시도나 `config_rejected` 시도가 있는 영상은 리허설되지 않음. verify-run V10 — 리허설은 저장소 파일을 한 바이트도 바꾸지 않아 같은 영상을 다시 리허설하고 보통 실행도 게시함 (cycle 20261015-182947-adw/phase-7f-chrome-rehearsal)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

### E-048 · hazard — 리허설의 글 지우기 `_clear` 는 `Exception` 을 모두 잡아 `rehearsed` 줄의 `detail="clear_failed …"` 로만 남긴다 — `CommentPage` 포트에 메서드를 더한 뒤, 그 메서드가 없는 가짜로 도는 테스트는 `AttributeError` 를 detail 에 삼키고 초록이다. `submits == []` 와 시도 `[]` 만 단언하는 테스트는 이 꼴을 잡지 못한다
- evidence: `src/agent/poster.py:331-336`. main 의 `tests/test_run.py:181` `FakeTab` 에 `clear_comment` 가 없다(`git show main:tests/test_run.py`). ship-check 감사 3 재현 `POST mode=test result=rehearsed reason=dry_run detail="clear_failed page_error: AttributeError: 'FakeTab' object has no attribute 'clear_comment'"`(journal ship-report.md R2 :144 · verify-report.md N1 :125). run 단위 잠금은 Phase 7G 로 넘김(ship-report Human checks 1) (cycle 20261015-182947-adw/phase-7f-chrome-rehearsal)
- first confirmed: 2026-10-15 · last confirmed: 2026-10-15

## Retired (history — one line each, never deleted)
- E-006 · tooling — [stop:unknown · 1] 정지 부류 표에 "ship-check sensitive human checks — confirm in the interview before merge" 행이 없다 — 민감 확인 줄로 머지 전에 멈춘 ship-check 는 부류 `unknown` 으로 남는다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-14)
- E-007 · codebase — `judge_trigger` 는 기록 한 번(`too_few_samples`) · 조회수 미달/초과(`views_below_min` · `views_above_max`) 검사를 나이 검사(`too_old`)보다 먼저 한다 — 나이 창이 닫힌 영상도 그 셋 중 하나면 영원히 `too_old` 를 받지 못하고, 계약 '트리거 판정' 절의 설명 문장("바뀌지 않는 것은 `too_old` 뿐 … `views_below_min` 과 모든 `hold` 는 `yes` 가 될 수 있다", "조회수가 줄면 … `hold` … 나이 창이 닫히면 `too_old` 로 끝남")은 이 영상들에 대해 틀린다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-14)
- E-004 · tooling — 이 기계의 셸 `grep` 은 GNU grep 이 아니라 ugrep 7.8.4 를 부르는 셸 함수다 — GNU grep 의 동작(NUL 이 든 파일의 `binary file matches` 등)을 재는 시험은 `/usr/bin/grep` 을 경로로 불러야 같은 것을 잰다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-14)
- E-021 · reviewer — 받아들인 위험을 재현한 **입력**으로 적으면 다음 ship-check 가 같은 코드 자리에서 다음 입력을 찾아 다시 멈춘다 — 자리(함수 · `except` 줄)로 적자 멈춤이 끝났다 — retired 2026-10-15 (꼬리 "자리로 적자 멈춤이 끝났다" 가 6G 에서 틀림: 자리(`tests/live_check.py:1621`)를 적은 `skip_reason` 대가 줄이 좁은 입력 종류 때문에 다음 ship-check 에서 다시 올라옴(journal 20261015-130935 ship-report.md:217) — 고친 사실을 E-043 에 다시 씀)
- E-036 · gotcha — 레인 착지는 squash 없는 `merge --no-ff` 라(`.claude/skills/plan/scripts/finalize_step.py:1054`), 레인 끝 판에서만 지운 내용은 앞 레인 커밋마다 남아 main 기록에 붙는다(제출 때 공개) — 실행기는 영상마다 `untrusted.description` 을 `_clean` · 길이 자르기만 하고 결과 파일에 쓰므로(`tests/live_check.py:1380`), 사람이 커밋한 `docs/live-check/result.json` 에 채널 주인 연락처가 그대로 들어갈 수 있다 — retired 2026-10-15 (뒤 절 "실행기는 … `_clean` · 길이 자르기만 하고 결과 파일에 쓰므로" 가 6G 에서 틀림: `_kept`(`tests/live_check.py:353-360`)가 키 가림 → 연락처 가림 → 자르기 순서로 씀 — 앞 절(착지가 레인 역사를 main 에 붙임)은 E-044 에 다시 씀)
- E-042 · gotcha — [stop:red-unbucketable · 6g] ship-check BLOCKED 이고 통이 그 고침을 못 받는다 — 이 페이즈는 제 브랜치에서 아래 Blockers 를 범위로 다시 돈다 — retired 2026-10-15 (shipped)
- E-003 · gotcha — `verify-run` 부터 다시(control retry)는 옛 verify-plan 을 그대로 쓴다 — 그 사이 인터뷰가 트래커만 커밋해도 범위 끝을 `HEAD` 로 둔 검사는 빨개진다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-14)
- E-035 · codebase — 실행기 테스트의 가짜 Claude(`tests/test_live_check.py` `FakeClaude.create`)는 `system` 글이 `GRADE_SYSTEM` · `TOPIC_SYSTEM` 과 같은지로 호출 종류를 가리고, 둘 다 아니면 오류 없이 `write`(작성)로 센다 — 실행기에 새 system 글로 Claude 를 부르는 호출을 더하는 페이즈가 가짜에 갈래를 더하지 않으면 그 호출은 작성 큐의 답을 받는다. 최악 호출 수를 글자로 잠근 `test_default_limits_fit_under_ceilings` 도 함께 고쳐야 한다 — retired 2026-10-15 (6E 가 세 번째 갈래(`SKIP_GRADE_SYSTEM` → `skip_grade`, `tests/test_live_check.py:1591`)를 더해 "둘 다 아니면" 과 인용 줄(:1417-1426)이 코드와 어긋남 — 같은 사실을 고친 줄로 E-037 에 다시 씀)
- E-011 · tooling — `retro_collect.py` 의 `_tokens` 는 `Files:` 줄 경로의 양끝에서 `.` 를 벗긴다 — 점으로 시작하는 파일은 plan 이 `Files:` 에 적어도 "계획 밖 파일" · T4 경보 ⑷ 에 늘 들어간다(`.env.example` → `env.example`, `.gitignore` → 점이 없어져 경로로 안 보고 버림) — retired 2026-10-15 (over cap; unconfirmed since 2026-10-13)
- E-018 · tooling — 이 기계에는 `playwright` 도 `pip-audit` 도 설치돼 있지 않다 — 브라우저 층 시험은 가짜 객체로만 돌고, `requirements.txt` 를 바꾼 사이클의 의존성 감사는 미측정이라 ship 판정이 ⚠️ READY WITH RISKS 위로 올라가지 못한다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-13)
- E-019 · hazard — Phase 6 의 크롬 프로필 점검(`src/agent/chrome.py:70-85` 기본 폴더 목록 + `_same_or_inside`)도 E-005 처럼 열거한 꼴로 막는다 — `posixpath.normcase` 는 대소문자를 접지 않아 대소문자 무구분 파일 시스템(macOS APFS · WSL `/mnt/c`)의 다른 철자가 통과하고, 목록에 없는 Chrome Beta · Dev · Canary · Edge 기본 폴더도 통과한다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-13)
- E-020 · codebase — `tests/test_chrome.py` · `tests/test_poster.py` 의 가짜 Playwright 객체는 기다리지도 시간 초과를 내지도 않고 CDP 연결 끊김을 흉내 내지 못한다 — 실제 `is_enabled()`(기본 30초) · `click(timeout=3000)` 의 자동 대기와 크롬 재시작 뒤 낡은 연결(`TargetClosedError`)은 스위트가 재지 못한다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-13)
- E-008 · codebase — `VideoRecord` 는 일반(`frozen` 아님) dataclass 이고 `__post_init__` 에서만 검증한다 — 생성 뒤 필드 대입은 검증을 건너뛰고, `view_history` 검증(`_items`)은 원소 타입만 볼 뿐 시각 순서 · 중복 · 시간대 종류를 보지 않는다 — retired 2026-10-15 (over cap; unconfirmed since 2026-10-13)
- E-012 · tooling — 이 기계에는 `typesafe_sdk` 도 `pip-audit` 도 없고 `TYPESAFE_API_KEY` 도 없다 — 판별 테스트는 `tests/test_classifier.py` 의 가짜 SDK 로만 돌고, 정확도 러너 `python3 -m tests.jev_accuracy` 와 의존성 감사는 아직 한 번도 돌지 않았다 — retired 2026-10-14 (contradicted by `docs/live-check/result.json` — 사람이 6A 실행기로 진짜 jev 를 불렀다(`run_at 2026-10-14T04:28:16Z` · `calls` jev 72 · Claude 23 · YouTube 17; 예시 판정은 `tests/live_check.py:72` 가 들여오는 `tests.jev_accuracy.judge_examples`) — 정확도 러너는 돌았다. 이 기계의 SDK 없음은 E-033 로, `pip-audit` 없음은 E-018 로 남는다 (cycle 20261014-112322-adw/phase-6b-live-check-apply))
- E-016 · tooling — 이 기계에는 `anthropic` 도 없다 — 댓글 작성기 테스트는 `tests/test_writer.py` 의 가짜 Claude 로만 돌고, `anthropic_client()` · 모델 id `claude-sonnet-5-5` · 통과 하한 0.7 은 실제 API 로 한 번도 돌지 않았다 (jev 쪽은 E-012) — retired 2026-10-14 (contradicted by `docs/live-check/result.json` `models` — `claude-sonnet-5-5` · `claude-haiku-5-5` 둘 다 `accepted`, 작성 sonnet · 채점 haiku 로 진짜 Claude API 를 불렀다. 이 기계의 `anthropic` 없음은 E-033 로 남는다 (cycle 20261014-112322-adw/phase-6b-live-check-apply))
- E-005 · hazard — Phase 1 의 세 파서(가드 주소 읽기 · 로그 줄 이스케이프 · 설정 숫자 읽기)는 열거한 꼴 목록으로 막는다 — ship-check 네 번이 매번 목록 밖 꼴을 하나 이상 더 찾았다 — retired 2026-10-14 (contradicted by `src/agent/guard.py:23` `_SHARE_QUERY_NAMES = frozenset({"si", "t", "feature"})` · `src/agent/config.py:174` `_int(value, path, minimum, maximum)` 상한 필수 · `src/agent/logbook.py:59,70` 날 글자 범주 허용 목록(L·M·N·P·S + U+0020) — Phase 1A 가 세 파서를 받는 쪽 목록으로 바꿈 (cycle 20261014-035715-adw/phase-1a-parser-allow-rules))
- E-014 · hazard — 계약의 새 절 번호는 레인마다 자기 base 에서 매긴다 — main 의 `## 11. 트리거 판정 — trigger.py` 와 이 브랜치의 `## 11. 주제 판별 — classifier.py (Phase 3)` 가 같은 번호라, 착지 때 절 번호와 `config.py` 키 꼬리 · `config.yaml` · `VALID` · `CommittedConfigTest` · `requirements.txt` 의 겹친 추가분을 합쳐야 한다 — retired 2026-10-14 (shipped Phase 1B (cycle 20261014-035724-adw/phase-1b-contract-section-names): 계약 10절 규칙 줄로 10절 뒤 절은 번호 없이 제목만 달고, `tests/test_contract_sections.py` 가 `## <숫자>.` 제목과 10 넘는 절 인용을 착지 전에 빨강으로 막는다 — 남은 틈은 E-022)
- E-001 · gotcha — [stop:red-unbucketable · 1] ship-check BLOCKED 이고 통이 그 고침을 못 받는다 — 이 페이즈는 제 브랜치에서 아래 Blockers 를 범위로 다시 돈다 — retired 2026-10-13 (shipped (Phase 1 ship 게이트 승인 2026-10-13; `youtu.be/A/../B` 꼴은 `5352cf8` 로 막힘 — notes.md Expertise check))
