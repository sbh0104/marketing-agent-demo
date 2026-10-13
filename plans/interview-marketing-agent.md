# 마케팅 AI 에이전트 — Plan & Phase Tracker

<!-- Maintained by the deep-interview skill. Re-running the interview updates this file in place. -->

- Created: 2026-10-12
- Last updated: 2026-10-13
- Overall status: In progress

## Summary
유튜브 댓글 에이전트 (과제 안내: `docs/marketing-agent.pdf`). 주제 키워드로 새 영상을 찾고(탐지), AI가 주제 일치를 판별하고(판별), 조회수 조건으로 '뜨기 직전' 영상을 고르고(타이밍), 영상 고민에 맞춘 댓글을 쓰고(작성), 로그인된 크롬에 자동 게시합니다(게시). 빠른 제작이 목표라 뼈대(Phase 1)를 먼저 만들고, Phase 2–6은 뼈대의 계약만 따르므로 동시에 진행합니다. 실제 게시는 허용 목록 영상에만, 코드에서 강제합니다. 언어는 Python + Playwright입니다. 판단(주제 판별 · 댓글 자체 검사)은 `systemone model jev`(TypeSafe)가 하고, 글쓰기(고민 한 줄 정리 · 댓글 작성)는 Claude가 합니다 — jev는 글을 생성하지 않기 때문입니다 (`docs/research/jev.md`). Phase 3 · 5는 키 없이 공식 문서 · SDK 소스 · 가짜 jev/Claude로만 만들고 테스트했으므로, Phase 7 전에 진짜 키로 한 번 붙여 봅니다 — 진짜 호출은 사람이 셸에서 돌리고 사이클은 커밋된 결과 파일만 읽습니다 (Phase 6A · 6B, 2026-10-13).

## Phases
- [x] Phase 1 — 뼈대와 계약 (설정 · 데이터 모양 · 저장 · 운영 가드)
- [ ] Phase 2 — ① 탐지 · 조회수 추적 (watcher)
- [x] Phase 3 — ② 판별 · 주제 일치 (classifier)
- [x] Phase 4 — ③ 타이밍 · 뜨기 직전 판단 (trigger)
- [x] Phase 5 — ④ 댓글 작성 · 자체 검사 (writer)
- [x] Phase 6 — ⑤ 크롬 연결 · 게시 · 확인 (poster)
- [ ] Phase 6A — 진짜 호출 준비 · 사람이 돌릴 실행기 (live check)
- [ ] Phase 6B — 진짜 결과 반영 · 정확도 기록 · 기준값 조정
- [ ] Phase 7 — 파이프라인 연결 · 운영 규칙 통합
- [ ] Phase 8 — 제출물 (README · PROCESS.md · sample.log · 시연)

Parallel shape: Phase 1 → (Phase 2 ‖ 3 ‖ 4 ‖ 5 ‖ 6) → Phase 6A → [사람이 진짜 실행 · 결과 커밋] → Phase 6B → Phase 7 → Phase 8. Phases 2–6 run at the same time only when `lane.max` ≥ 5 (see Cross-cutting open questions).

---

## Phase 1 — 뼈대와 계약 (설정 · 데이터 모양 · 저장 · 운영 가드)
- Status: Done (스모크 스윕이 페이즈 브랜치를 병합 · 2026-10-13)
- Slug: foundation-contracts
- Goal: 다섯 모듈이 같은 약속(설정 값, 영상 한 건의 데이터 모양, 처리 기록 저장소, 허용 목록 가드, 테스트 모드 플래그, 로그 형식)을 쓰도록 뼈대를 만든다. 이후 Phase 2–6은 이 계약에만 의존한다.

Decisions
- 구현 언어 Python 3 + Playwright — 공식 Python 문서가 `connect_over_cdp`를 명시하고 다섯 모듈이 한 언어라 계약이 단순함 (`docs/research/stack.md`).
- 설정 파일 `config.yaml`이 과제 예시의 값(topic, keywords, poll_interval_min, trigger 세 값, limits, comment 길이, chrome_debug_url, allowed_videos)을 모두 담는다. 값을 코드에 박지 않는다 — 과제 요구사항.
- 허용 목록 강제는 게시 직전 한 함수에서 한다. 목록 밖 영상은 항상 테스트 모드 (과제: "이 제한은 설정이 아니라 코드에서 강제").
- 비밀 값(API 키, 크롬 프로필, 쿠키)은 `.env`와 프로필 디렉터리에만 두고 `.gitignore`로 막는다. `.env.example`만 커밋한다 (과제 체크리스트).
- **The plan decides** — 영상 기록 저장 방식: JSON 파일 vs SQLite · 과제의 `data/` 폴더 요구를 만족하는 쪽 · 중복 방지(영상당 댓글 1개)와 하루 상한(10개)·채널 대기(24시간)를 이 저장소에서 계산 · 조건: 같은 입력이면 같은 결과가 나와야 함.
- **The plan decides** — 주기 실행 방식: 프로세스 안 루프 vs OS 스케줄러 · 기본 30분 (`poll_interval_min`) · 조건: 설정 값 변경만으로 주기가 바뀌어야 함.
- **The plan decides** — 로그 형식: 탐지 · 판별 결과 · 조회수 변화 · 작성한 댓글 · 게시 성공/실패를 모두 한 줄씩 기록 · 과제가 `logs/sample.log`를 요구.
- NFR (기록하는 결정 — 해당 없음 포함):
  - 성능 목표: 없음 (쿼터와 주기가 사실상 상한, Phase 2 참조).
  - 접근성: 해당 없음 (UI 없는 CLI 에이전트).
  - 다국어: 한국어 한정 (검색 `ko`, 한국 지역, 한국어 댓글).
  - 가용성·복구: 로컬 프로세스 한 개, 가동 시간 목표 없음. 실패 시 원인과 화면 캡처를 기록하고 다음 영상으로 넘어감 (과제 ⑤).
  - 호환성: Mac과 Windows에서 실행 가능해야 함 (과제 README 필수 항목).
- 2026-10-13 ship-check BLOCKED 복구 (분류 `code miss` — 결정은 맞고 코드가 어김, `.adw/ship-report.md` § Blockers). 같은 브랜치에서 아래를 고친 뒤 ship-check 를 다시 받는다:
  - 허용 목록 가드(`guard.py`)는 계약 5절의 형식을 **정확히** 받는다 — `youtu.be` 는 경로가 정확히 `/<ID>`, shorts 는 `/shorts/<ID>` (뒤 `/` 하나 허용), `watch` 는 `v` 값이 정확히 하나. 경로의 `.`/`..` 칸, `%`, `\` 가 든 주소는 읽을 수 없는 것(`invalid_video`)으로 친다. `dry_run` 은 `is not False` 로 검사해 참·거짓이 아닌 값은 테스트 모드로 간다 — 되돌릴 수 없는 남의 영상 댓글을 막는 쪽을 최적화 (인터뷰 답변: 질문 1 A).
  - 계약 6절(게시 흐름)에 두 줄을 더한다 — ① 게시 단계는 받은 주소 문자열을 크롬에 넘기지 않고 `https://www.youtube.com/watch?v={decision.video_id}` 를 새로 만들어 연다. ② 클릭 직전 크롬의 실제 주소(`page.url`)로 `decide_post` 를 한 번 더 부르고, `live` 가 아니면 클릭하지 않는다(테스트 모드로 저장). 가드와 브라우저가 같은 주소를 다르게 읽을 자리 자체를 없애기 위함 — 가드의 엄격함 하나에만 기대지 않는 두 겹 잠금 (질문 1 A).
  - 설정 로더(`load_config`)는 읽기 중 나는 모든 오류(`ValueError`·`OverflowError`·`RecursionError` 포함 — 날짜 모양 값 `2026-02-30`, 아주 큰 정수, 깊은 중첩)를 `ConfigError` 로 바꾼다. plan 결정 "잘못 고친 설정은 이전 설정을 유지하고 `on_error("config", …)` 로 알린다"의 이행이며 결정 변경은 아님.
  - 계약 8절(비밀 값): 크롬 프로필은 `chrome-profile/` 또는 저장소 밖에만 둔다 — 저장소 안 다른 폴더는 금지. Phase 6·8 의 실행 안내는 이 두 위치만 예시로 보인다. 이와 별도로 `.gitignore` 와 계약 8절 이름 목록에 측정된 11개를 더한다: `Preferences`, `Secure Preferences`, `History*`, `IndexedDB/`, `Sessions/`, `Extension Cookies`, `Account Web Data`, `.envrc`, `.env-local`, `client_secret_*.json`, `token.json` — 위치 규칙이 첫 방어, 이름 목록이 사람이 규칙을 어겼을 때의 둘째 방어 (질문 2 C).
- **The plan decides** — 위 복구의 테스트 모양 · 후보: 거부해야 할 이웃 주소 표(`/../`, `%2e%2e`, `/shorts/A/../../watch?v=B`, `evil.com\@youtu.be/A`, `watch?v=A&v=B`, ID 뒤 추가 경로, `dry_run=None/0/""`)를 `tests/test_guard.py` 에 · 실제 파일을 고쳐 다시 읽는 재로딩 테스트를 `tests/test_config.py` 에 · 프로필 파일 이름 목록을 임의 폴더 아래에서 `git check-ignore` 로 확인하는 검사 · 조건: ship-report 의 재현 입력 다섯 가지와 날짜 모양 값이 모두 테스트에 실제 입력으로 들어가야 함.
- 2026-10-13 두 번째 ship-check(`READY WITH RISKS`, 민감 확인 줄 2개로 머지 전 정지) 뒤 인터뷰 — 분류 `drift`: 형식 목록이라는 결정 자체가 한 모양을 놓쳤음. 같은 브랜치에서 아래를 고친 뒤 ship-check 를 다시 받는다 (HC1 인터뷰 질문 1–3, 모두 A):
  - 허용 목록 가드: `youtu.be` · `/shorts/` 주소의 쿼리에 `v` 키가 있으면 `invalid_video` — 쿼리를 서버처럼 한 번 푼 뒤 세므로 `%76` 도 `v` 다. `?si=` · `&t=` · `&feature=` 같은 다른 쿼리는 지금처럼 무시한다. 계약 5절 형식 목록의 "뒤에 `?si=…` 등 매개변수는 붙어도 됨"에 "단 `v` 는 안 됨"을 더한다. watch 경로는 정확히 `/watch` 이고 `/watchx` · `/watch/` 는 읽을 수 없음 — 코드는 이미 그렇고, 이번에 테스트 행으로 고정한다(ship-report R7). 근거: 유튜브는 `youtu.be/A?v=B` 를 `watch?v=B&v=A` 로, `/shorts/A?v=B` 를 `watch?v=B` 로 보내 B 를 재생하는데(실측 `303`) 가드는 A 로 읽어 `live=True` 를 줬다. 계약 6절의 두 잠금은 아직 문서뿐이라, 가드 혼자서도 막아 잠금을 세 겹으로 한다 — 되돌릴 수 없는 남의 영상 댓글을 막는 쪽을 최적화 (질문 1 A).
  - 계약 6절 3.2 의 같은 영상 확인 조항을 확정한다: 클릭 직전 `recheck.video_id != decision.video_id` 이면 둘 다 허용 목록에 있어도 클릭하지 않고 `page_mismatch` 로 테스트 저장. `page_mismatch` 는 `decide_post` 의 이유가 아니라 게시 단계가 남기는 테스트 저장 이유다. 근거: 자동 재생이나 같은 크롬을 쓰는 사람의 조작으로 크롬이 다른 허용 영상으로 옮겨 가면, 저장소·로그는 A 에 달았다고 적고 실제 댓글은 A2 에 달린다 — 다음 주기에 A2 에 두 번째 댓글이 달려 "영상당 1개"와 기록 증명이 깨진다. 계약 문서(`docs/contracts.md:283-286, 295-301`)에 이미 이렇게 적혀 있어 Phase 1 코드 변경은 없음 (질문 2 A).
  - 로그(`logbook.py`)는 값 안에서 `str.splitlines()` 가 줄 경계로 세는 모든 글자(`\n` `\r` `\v` `\f` `\x1c` `\x1d` `\x1e` `\x85` `U+2028` `U+2029`)를 따옴표 값 안의 이스케이프로 쓴다 — 한 사건이 어떤 읽기 방식으로도 한 줄이고, `parse_line` 으로 원래 값이 되돌아온다. 근거: 영상 제목에 숨긴 `U+2028` 로 `splitlines()` 독자에게 가짜 `POST … mode=live result=posted` 줄이 읽혔다(인터뷰에서 재현, ship-report R3). 로그 형식(계약 7절)의 줄 모양은 그대로이고 이스케이프 대상만 넓어진다 (질문 3 A).
  - 설정 숫자(`_number`)는 유한값만 받고(`.inf` · `-.inf` · `.nan` 은 `ConfigError`) 상한을 둔다. 근거: `channel_cooldown_hours: .inf` · `20000000` 은 읽기를 통과한 뒤 `check_post` 에서 `OverflowError` 를 내 "잘못 고친 설정은 이전 설정 유지"가 지켜지지 않았다(인터뷰에서 재현, ship-report R2). `trigger.max_age_hours` 도 같다 (질문 3 A).
  - ship-report R7 의 테스트 행을 함께 더한다 — 설정 하한 셋(`limits.channel_cooldown_hours: -1` · `.nan`, `trigger.max_age_hours: 0`, `limits.daily_max_comments: -1`), 로그 값 속 줄 바꿈(`"x\ny"` · `"x\ry"` 처럼 공백 없는 값), 가드의 `/watchx?v=A` · `/watch/?v=A`. 지금 코드는 맞지만 다음 수정이 깨도 스위트가 초록이던 약속들이다 (질문 3 A).
- **The plan decides** — 설정 숫자 상한 값(키마다, 예: 채널 대기 시간 · `max_age_hours` · `poll_interval_min`) · 조건: 읽기를 통과한 값은 뒤 단계(`check_post` 의 `timedelta`, 주기 대기)에서 `OverflowError` 등을 내지 않아야 하고, 상한을 넘으면 `ConfigError` 라 이전 설정이 유지됨을 실제 파일 재로딩 테스트가 잠근다. 상한은 계약 2절 표에 적는다.
- **The plan decides** — YAML 1.1 숫자 변환(`017` → 15, `1:30` → 90.0): 거부할지, 아니면 방어 범위를 실제보다 넓게 적은 문장(`config.py:3-5`, `contracts.md:52-55`)만 실제대로 고칠지 · 조건: 문서와 동작이 일치해야 하고, 고르는 쪽을 테스트 한 행이 잠근다.
- 2026-10-13 세 번째 ship-check(`READY WITH RISKS`, 민감 확인 줄 1개로 머지 전 정지) 뒤 인터뷰 — 분류: 확인(코드와 결정은 그대로, 위험을 받아들이고 주인을 정함). 로그 값 속 제어 문자(NUL · ESC · DEL · C1 · 양방향 제어)는 Phase 1 에서 고치지 않고 출하한다 — 고침은 Phase 7 이 맡는다(아래 Phase 7 결정). 근거: 코드는 HC1 질문 3 의 규칙(줄 바꿈 글자 10개)과 계약 7절을 정확히 지키고, 계약이 증명용으로 정한 `parse_line` 은 정확하며 *파싱되는* 가짜 사건은 만들 수 없다(ship-report R1). Phase 7 은 Phase 2–6 이 모두 끝난 뒤 혼자 돌아 `logbook.py` 를 고쳐도 다른 레인과 부딪히지 않고, 평가자가 읽는 `logs/sample.log`(Phase 8)보다 앞선다. 주인 없이 받아들인 지난 로그 위험(U+2028)이 다음 ship-check 에 정지로 돌아온 선례(아래 Responsibilities 의 "(2026-10-13 HC1) 위 줄의 지난 R3…" 줄) 때문에 주인을 정해 둔다 — 출하 속도를 최적화하되 같은 정지가 되풀이되지 않게 (HC1-2 질문 1 A).
- **The plan decides** — 이번 고침의 테스트 모양 · 조건: 이 인터뷰의 재현 입력이 모두 테스트의 실제 입력이어야 함 — `https://youtu.be/AAAAAAAAAAA?v=BBBBBBBBBBB`, `https://www.youtube.com/shorts/AAAAAAAAAAA?v=BBBBBBBBBBB`, `https://youtu.be/AAAAAAAAAAA?%76=BBBBBBBBBBB`, `https://youtu.be/AAAAAAAAAAA?si=x&v=BBBBBBBBBBB` 는 거부, `https://youtu.be/AAAAAAAAAAA?si=xYz12` 는 계속 A 로 읽힘 · 위의 줄 바꿈류 글자 각각이 든 제목을 쓴 한 사건이 `splitlines()` 로 한 줄이고 `parse_line` 으로 되돌아옴 · `channel_cooldown_hours: .inf` 와 아주 큰 수가 `ConfigError`. 각 고침을 되돌리는 변이를 `tests/mutants.py` 에 더할지는 plan 이 정한다.

Trade-offs accepted
- 바로 쓸 수 있는 프레임워크 대신 얇은 직접 구현을 택함 — 빠른 제작을 위해 기능이 적음.
- (2026-10-13) 클릭 직전 `page.url` 재확인 때문에 유튜브가 중간 화면(로그인·동의 화면 등)을 띄우면 정상 게시도 테스트 모드로 빠질 수 있다 — 위험한 쪽이 아니라 안전한 쪽 실패로 받아들임.
- (2026-10-13) 계약 5절 목록 밖의 주소 모양(예: 경로에 `%` 가 든 정상 주소)은 허용 목록 항목으로도 쓸 수 없다 — 허용 목록 작성자가 맨 ID 나 표준 형식으로 적어야 함.
- (2026-10-13) `History`·`Preferences` 같은 흔한 이름이 저장소 어디서든 git 에서 무시된다 — 그런 이름의 진짜 파일을 만들면 커밋되지 않음.
- (2026-10-13 HC1) 가드가 막는 쿼리 이름은 `v` 하나뿐이다(거부 목록 방식) — 유튜브가 다른 쿼리 이름으로 재생 영상을 바꾸는 경우가 나중에 발견되면 그때 다시 막아야 한다. 쿼리를 통째로 거부하는 쪽은 공유 버튼 주소(`youtu.be/ID?si=…`)로 쓴 허용 목록 항목이 조용히 읽히지 않게 되어 택하지 않음.
- (2026-10-13 HC1) 크롬이 다른 영상으로 옮겨 간 날은 그 게시 기회를 버리고 `page_mismatch` 로 테스트 저장된다(다음 주기에 다시 시도). 로그를 읽는 사람은 가드의 네 이유 밖의 다섯째 이유를 하나 더 알아야 한다.
- (2026-10-13 HC1) 고침 사이클이 커진다(가드 3–4줄 + 로그 이스케이프 + 숫자 유한·상한, 테스트 행 10여 개) — 고칠 곳이 늘어 ship-check 가 새 흠을 찾아 한 번 더 멈출 가능성을 받아들임. 대신 Phase 2–6 다섯 레인이 출발하기 전에 바닥 파일(`config.py` · `logbook.py`)이 바로 서고, 뒤 페이즈가 이 파일을 고치며 다섯 레인과 부딪힐 일이 없다.
- (2026-10-13 HC1-2) Phase 7 이 고칠 때까지 HC1 질문 3 의 "한 사건은 어떤 읽기 방식으로도 한 줄"은 "줄 바꿈 글자 10개에 한해"로 좁아진다. Phase 2–6 이 도는 동안(실제 영상 제목이 처음 로그에 들어가는 기간) 제목에 NUL 이 하나 들어오면 GNU grep 은 로그 전체를 `binary file matches` 로 가리고, ESC 는 `cat` 한 터미널에 가짜 게시 줄을 그릴 수 있다 — 이 기간에 로그를 볼 때는 `parse_line` 이나 `grep -a` 로 읽는다. 실제 유튜브 제목에 제어 문자가 오는지는 재지 못했다.

Responsibilities & risks to guard against
- 계약을 바꾸면 Phase 2–6 전부에 영향 — Phase 1의 데이터 모양은 변경하지 않는 것을 원칙으로 함.
- `.env`, 크롬 프로필, 쿠키가 커밋되지 않았는지 Phase 8 전에 다시 확인.
- (2026-10-13) 계약 6절의 두 줄은 Phase 6 이 지킨다 — Phase 6 리뷰에서 크롬에 여는 주소가 `decision.video_id` 로 만든 것인지, `PostDecision` 이 `decide_post` 에서만 오는지 확인 (ship-report R8).
- (2026-10-13) 이름 목록은 크롬 버전이 바뀌면 뒤처진다 — 위치 규칙이 주 방어이고, Phase 8 직전 `git ls-files` 사람 확인은 그대로 남는다.
- (2026-10-13) ship-report 의 나머지 위험(R1–R6, R9–R17)은 이번 복구 범위가 아니다 — Phase 7(R5 `on_error`, R10 단일 실행 잠금)과 Phase 6(R12 결과 모르는 게시는 `reserved` 유지)이 각자 지킨다.
- (2026-10-13 HC1) 위 줄의 지난 R3(로그 `U+2028` 위조)과 R6(검증을 통과한 `.inf` · 큰 수)은 주인이 없어 두 번째 ship-check 에 R3 · R2 로 다시 나왔다 — 이번 고침 사이클(Phase 1)이 맡는다. 두 번째 ship-report 의 나머지: R4(가드의 유니코드 공백 자르기, 다른 영상·호스트로 가는 경우 0건)는 받아들인 위험, R5(`config.yaml` 병합 키 `<<:` 메모리 폭탄)는 설정 파일 주인만 일으킬 수 있는 자가 서비스 거부라 이번 범위 밖이며 주인 페이즈가 없다, R6(이름 목록 밖 비밀 파일)은 위 절충 그대로, R8(실제 Mac·Windows 기기, 크롬의 실제 `page.url`)은 사람 확인 · Phase 6 몫.
- (2026-10-13 HC1-2) 세 번째 ship-report 의 R1(로그 제어 문자)은 Phase 7 이 맡는다. 나머지: R2(남은 쿼리 철자 — 진짜 영상 ID 둘로 한 번 확인)와 Windows · macOS 스위트, Phase 8 직전 `git ls-files` 는 사람 확인으로 남는다. R3(짝 없는 서로게이트 제목이 저장소 쓰기를 재시작까지 막음)은 제목을 받는 Phase 2 · 오류를 처리하는 Phase 7, R4(cp949 echo 의 이모지)는 echo 스트림을 고르는 Phase 7 몫. R5(`;` 둘 이상 테스트 행)는 `.adw/smoke-log.md` S-NEW-3, R7(정수 설정 키 상한 없음)은 계약 2절에 적힌 결정, R8(이름 목록 밖 비밀 파일)은 위 절충 그대로, R9(pip-audit 못 돌림)는 도구가 있는 기계에서 다시.

Dependencies
- Depends on: none
- Unlocks: Phase 2, Phase 3, Phase 4, Phase 5, Phase 6

Open questions
- none

---

## Phase 2 — ① 탐지 · 조회수 추적 (watcher)
- Status: Not started
- Slug: watcher-detect
- After: Phase 1
- Goal: YouTube Data API v3로 키워드별 최신순 검색(한국 지역 · 한국어 · 최근 12시간 업로드)을 주기마다 실행하고, 찾은 영상의 조회수를 주기마다 다시 기록한다. 하루 검색 호출 수를 설정으로 제한한다.

Decisions
- 검색 쿼터 가드를 이 모듈에 둔다 — 하루 검색 호출이 설정 한도를 넘으면 호출하지 않고 기록만 남긴다 (`docs/research/search-quota.md`).
- **The plan decides** — 주기와 키워드 수 조합. 조건: 하루 검색 호출 ≤ 100회 (쿼터 약 100회/일). 후보: (a) 30분 × 키워드 2개 = 96회/일 · (b) 2시간 × 키워드 5개 = 60회/일 (키워드 5개는 과제 예시 그대로 유지). 근거는 `docs/research/search-quota.md`. 어느 쪽이든 `config.yaml`에서 바꿀 수 있어야 함.
- **The plan decides** — YouTube 클라이언트: 공식 Google 클라이언트 라이브러리 vs 직접 HTTP 호출 · 조건: 쿼터 단위 계산이 한 곳에 모여야 함.

Trade-offs accepted
- 키워드 5개를 30분마다 돌리는 과제 예시는 쿼터를 넘으므로 그대로 쓰지 않음.
- 조회수 추적 호출의 정확한 쿼터 단위는 구현 전에 공식 표로 재확인 (이번 조사에서 미확인).

Responsibilities & risks to guard against
- 쿼터 초과 시 조용히 빈 결과를 내면 안 됨 — 한도 도달을 로그에 남긴다.
- 페이지 넘김(pagination)도 쿼터를 쓴다 — 가드에 포함한다.

Dependencies
- Depends on: Phase 1
- Unlocks: Phase 4 (조회수 기록), Phase 7

Open questions
- none

---

## Phase 3 — ② 판별 · 주제 일치 (classifier)
- Status: Done
- Slug: classifier-topic
- After: Phase 1
- Goal: 영상의 제목 · 설명 · 자막(있을 경우)을 읽고 주제 일치 여부와 이유를 기록한다. 키워드만 겹치는 영상(예: '연애'가 들어간 게임 영상)을 걸러낸다.

Decisions
- 판별 AI는 `systemone model jev`를 쓴다 — 사용자가 "내용 판단은 systemone model jev로 진행"이라고 확정 (인터뷰 답변 2).
- jev 접속: `POST https://api.typesafe.ai/v1/systemone`, Python SDK `typesafe-sdk` (`TypeSafeClient`), 모델 이름 `jev-latest`(현재 `jev-1.13.0`)는 `config.yaml`에, 키 `TYPESAFE_API_KEY`는 `.env`에 둔다. 이 페이즈가 `.env.example`에 `TYPESAFE_API_KEY=` 줄을 추가한다 (`docs/research/jev.md`).
- 판별 결과는 `일치 여부 · 이유` 두 필드로 저장한다 (과제: "주제 일치 여부와 이유를 기록"). jev는 문장을 쓰지 않으므로 '이유'는 jev가 고른 보기 이름과 확률로 기록한다 — 예: `키워드만 겹침: 게임 (0.91)`. 일치 여부는 `noul` 질문, 이유는 `choice` 질문 하나씩을 한 요청에 묶어 보낸다.
- **The plan decides** — 이유 보기 목록(예: 연애 고민 상담 · 키워드만 겹침: 게임 · 음악 · 예능 …)과 일치 판정 기준값(`noul` 확률 · `confidence` 하한)을 `config.yaml`에 둔다 · 조건: 기준값 아래나 API 오류는 '보류'로 기록하고 '일치'로 처리하지 않음을 테스트가 잠근다.
- **The plan decides** — 한국어 정확도 확인: jev는 영어가 주 언어이고 CJK는 정확도가 같지 않다 (`docs.typesafe.ai/models`). 사람이 일치/불일치를 붙인 한국어 영상 예시 묶음(제목 · 설명)을 테스트 자료로 두고, 실제 키가 있으면 정확도를 기록한다. 정확도가 낮으면 질문 문구(`instructions`·`criteria`)를 영어로 쓰는 것까지는 plan이 정한다 (영상 내용은 한국어 그대로).
- 긴 자막은 잘라서 보낸다 — `state`와 가장 긴 질문 합계 32k 토큰 한도.

Trade-offs accepted
- 얼리 액세스 키가 없으면 가짜(mock) 응답으로 테스트만 가능 — 실제 판별 품질은 키가 `.env`에 들어온 뒤에만 검증.
- 이유가 문장이 아니라 보기 이름이라 설명이 짧다 — 대신 확률이 함께 남아 기준을 숫자로 조정할 수 있다.

Responsibilities & risks to guard against
- 키워드 일치만으로 통과시키지 않는다 (과제 요구).
- API 오류(401 · 422 · 429 · 529)나 낮은 확신일 때 '일치'로 처리하지 않는다 — '보류'로 기록. 429·529 재시도는 SDK 기본 정책에 맡긴다.
- 영상 설명·자막은 믿을 수 없는 입력 — 안에 든 지시문에 판별이 흔들릴 수 있다 (jev 알려진 약점). 판별 결과만으로 게시하지 않고 Phase 4 · 5 · 7의 조건을 모두 통과해야 한다.
- 숫자 세기·날짜 비교는 jev에 묻지 않는다 (알려진 약점) — 코드가 계산한다.

Dependencies
- Depends on: Phase 1
- Unlocks: Phase 5, Phase 7

Open questions
- none (2026-10-12: jev 접속 방법은 공식 문서로 확인 — `docs/research/jev.md`. 키는 `.env`의 `TYPESAFE_API_KEY`.) (2026-10-13 메모, 결정 변경 아님: 이 페이즈는 키 · SDK 없이 가짜 jev로만 검증됐다 — 키 보유 여부를 인터뷰가 묻지 않았음. 진짜 정확도 측정과 기준값 조정은 Phase 6A · 6B가 맡는다.)

---

## Phase 4 — ③ 타이밍 · 뜨기 직전 판단 (trigger)
- Status: Done
- Slug: trigger-timing
- After: Phase 1
- Goal: 조회수 1,000–5,000, 업로드 후 12시간 이내, 시간당 조회수 150 이상 — 세 조건을 모두 만족하면 대상으로 표시한다. 세 값은 `config.yaml`에서 바꾼다.

Decisions
- 기본 기준은 과제 값 그대로 (min_views 1000, max_views 5000, max_age_hours 12, min_views_per_hour 150).
- **The plan decides** — 더 나은 기준 제안 여부. 과제는 근거와 함께 제안을 허용 (`min_views_per_hour`는 조회수 기록이 두 번 이상일 때만 계산 가능 — Phase 2의 주기 기록에 의존).

Trade-offs accepted
- 시간당 조회수는 기록 주기(30분 또는 2시간)에 따라 정밀도가 달라짐. 기록이 한 번뿐인 영상은 '판단 보류'로 둔다.

Responsibilities & risks to guard against
- 조회수가 줄어드는 기록(삭제·비공개 등)을 음수 속도로 계산하지 않는다.

Dependencies
- Depends on: Phase 1 (영상 데이터 모양). 조회수 기록 자체는 Phase 2 결과를 입력으로 받지만, 입력 모양은 Phase 1 계약으로 고정.
- Unlocks: Phase 7

Open questions
- none

---

## Phase 5 — ④ 댓글 작성 · 자체 검사 (writer)
- Status: Done (스모크 스윕이 페이즈 브랜치를 병합 · 2026-10-13)
- Slug: writer-comment
- After: Phase 1
- Goal: 영상의 고민을 한 줄로 정리하고, 그 고민과 이어지는 '연애사주 경험' 댓글을 40–120자로 쓴다. 영상 속 구체적인 장면이나 말을 하나 이상 언급하고, 링크를 넣지 않으며, 이전 댓글과 같은 문장을 반복하지 않는다.

Decisions
- 글쓰기 AI는 Claude(Anthropic API)를 쓴다 — 고민 한 줄 정리와 댓글 작성 모두. jev는 글을 생성하지 않으므로 작성을 맡을 수 없다 (`docs/research/jev.md`; 인터뷰 2026-10-12 jev 갱신 답변 A). 키 `ANTHROPIC_API_KEY`는 `.env`에 두고, 이 페이즈가 `.env.example`에 그 줄을 추가한다.
- 자체 검사는 jev가 한다 — 초안 한 개에 `noul` 질문 여러 개를 한 요청으로: 영상 속 장면·말을 언급했나 · 광고처럼 읽히나 · 영상의 고민과 이어지나 (과제 가점 항목). 판단은 jev라는 사용자 원칙과 맞고, 검사 비용은 거의 0.
- 검사에 떨어지면 Claude가 한 번 다시 쓴다. 두 번째도 떨어지면 그 영상은 건너뛰고 이유를 기록한다 (Phase 7의 '재시도 없이 다음 영상' 원칙과 같은 방향).
- 글자 수(40–120자) · 링크 금지 · 이전 댓글 중복은 AI가 아니라 코드가 마지막에 검사한다 — jev는 숫자 세기를 못 한다 (알려진 약점).
- 자막이 없으면 제목·설명과 인기 댓글을 입력으로 쓴다 (과제 ④).
- **The plan decides** — Claude 모델: `claude-sonnet-5-5` vs `claude-haiku-5-5` · 모델 이름은 `config.yaml`에 둔다 · 조건: 모델 이름을 설정에서 읽는지 테스트가 잠그고, 테스트는 가짜 Claude 응답으로 돈다.
- **The plan decides** — 자체 검사 통과 기준값(`noul` 확률 하한)을 `config.yaml`에 둔다 · 조건: 기준값 아래면 다시 쓰기, 두 번째 실패면 건너뛰기를 테스트가 잠근다.
- **The plan decides** — 이전 댓글 중복 검사 방식: 최근 작성 문장과 비교 방법 (정확 일치 vs 유사도). 조건: '같은 문장 반복 금지'를 코드로 확인 가능해야 함.

Trade-offs accepted
- API 키가 두 개(`TYPESAFE_API_KEY`, `ANTHROPIC_API_KEY`)가 되고 요금을 두 회사에 낸다. README 키 발급 안내도 두 개 (Phase 8).
- 자체 검사와 다시 쓰기는 호출을 늘린다 — 하루 상한 10개 안팎이라 규모는 작다.
- 두 번 실패한 영상은 댓글 기회를 버린다.

Responsibilities & risks to guard against
- 광고처럼 읽히는 댓글 (과제 PROCESS.md 예시) — 링크 금지 규칙과 함께 검사 규칙을 프롬프트에 기록.
- 길이 기준(40–120자)을 글자 수로 검사 — 바이트가 아니라 글자 기준.
- 영상 설명·자막·인기 댓글은 믿을 수 없는 입력 — Claude 프롬프트에서 지시문이 아닌 자료로 구분해 넣는다.
- 판별·작성 프롬프트 원문은 PROCESS.md에 들어가야 한다 (Phase 8) — 프롬프트를 코드 곳곳에 흩지 말고 한 곳에 둔다.

Dependencies
- Depends on: Phase 1, Phase 3 (판별 결과가 작성 입력의 일부)
- Unlocks: Phase 6, Phase 7

Open questions
- none (2026-10-12: 작성은 Claude, 검사는 jev로 확정. jev 접속은 Phase 3과 같다.) (2026-10-13 메모, 결정 변경 아님: 이 페이즈는 가짜 Claude · 가짜 jev로만 검증됐다. 모델 id 확인과 통과 하한 조정은 Phase 6A · 6B가 맡는다.)

---

## Phase 6 — ⑤ 크롬 연결 · 게시 · 확인 (poster)
- Status: Done
- Slug: poster-chrome
- After: Phase 1
- Goal: 로그인된 크롬에 연결해 영상을 열고, 댓글 창까지 이동해 입력하고, 게시하고, 내 댓글이 실제로 보이는지 확인한다. 실패하면 원인과 화면 캡처를 기록하고 다음 영상으로 넘어간다.

Decisions
- 크롬 연결은 Playwright `connect_over_cdp`로 한다 (언어 결정과 같은 근거, `docs/research/stack.md`).
- **The plan decides** — 크롬 프로필: 기본 프로필 불가. Chrome 136부터 기본 데이터 디렉터리에서 `--remote-debugging-port`가 무시되므로 전용 프로필(`--user-data-dir`를 기본 경로가 아닌 곳으로)을 쓰고 한 번 로그인한다. 대안: Chrome for Testing (자동화 전용 빌드, 크롬 팀 권장). 근거 `docs/research/browser-cdp.md`. 테스트가 프로필 경로 검증을 잠가야 함.
- 게시 직전 허용 목록 확인 — 목록에 없으면 게시하지 않고 작성 결과만 파일로 저장 (과제 ⑤). Phase 1 가드를 호출한다.
- 테스트 모드(`--dry-run`): 게시 직전까지만 실행하고 댓글을 파일로 저장.
- (2026-10-13, Phase 1 계약 6절) 크롬에는 받은 주소 문자열이 아니라 `https://www.youtube.com/watch?v={decision.video_id}` 만 연다. 클릭 직전 `page.url` 로 `decide_post` 를 한 번 더 부르고 `live` 가 아니면 클릭하지 않는다 — 가드와 브라우저의 주소 해석 차이로 남의 영상에 게시되는 것을 막음 (Phase 1 복구 질문 1 A).
- (2026-10-13 HC1, Phase 1 계약 6절 3.2) 클릭 직전 다시 묻기에서 `recheck.video_id != decision.video_id` 이면 둘 다 허용 목록에 있어도 클릭하지 않고 `store.save_test(…, reason="page_mismatch")` 로 끝낸다 — 자동 재생이나 사람의 조작으로 크롬이 다른 허용 영상으로 옮겨 가도 저장소 기록과 실제 댓글이 같은 영상을 가리키게 함 (Phase 1 HC1 질문 2 A).
- (2026-10-13, Phase 1 계약 8절) 프로필 위치는 `chrome-profile/` 또는 저장소 밖으로 한정 — 위 "The plan decides" 의 프로필 선택은 이 두 위치 안에서 고른다. 실행 안내에도 이 두 위치만 예시로 보인다 (Phase 1 복구 질문 2 C).

Trade-offs accepted
- 게시 자동화는 웹 화면 구조에 기대므로 유지 보수가 필요 — 실패 기록으로 대응.
- `connect_over_cdp`는 Playwright 고유 프로토콜 연결보다 기능이 제한될 수 있음 (`docs/research/stack.md` 경고).

Responsibilities & risks to guard against
- 로그인 풀림, 댓글 막힘, 화면 구조 변경 — 각각 원인을 기록하고 멈추지 않는다.
- 쿠키·프로필 디렉터리가 저장소에 들어가지 않도록 Phase 1 `.gitignore`를 따른다.
- 실제 게시는 허용 목록의 본인 테스트 영상에서만. 실제 테스트 영상 ID가 없으면 테스트 모드로만 검증.

Dependencies
- Depends on: Phase 1, Phase 5 (댓글 입력)
- Unlocks: Phase 7

Open questions
- none

---

## Phase 6A — 진짜 호출 준비 · 사람이 돌릴 실행기 (live check)
- Status: Not started
- Slug: live-check-prepare
- After: Phase 2, Phase 3, Phase 5
- Goal: 사람이 셸에서 한 번 돌리면 진짜 jev · Claude · YouTube를 부르고 결과를 `docs/live-check/` 아래 파일로 남기는 실행기와 실행 안내를 만든다. 이 사이클 안에서는 진짜 호출을 하지 않는다.

Decisions
- (2026-10-13 인터뷰 질문 2 C) 진짜 외부 호출(jev · Claude · YouTube)은 사람이 셸에서 돌리고, 사이클은 실행기를 만들어 가짜로만 테스트한다 — 외부 전송 버튼은 언제나 사람이 누르고 키는 사이클 손에 들어가지 않는 쪽을 최적화. 헌법 Never 절(자동 승인은 계획 · 배포 승인만 대신함)과 레인에 `.env`가 없다는 사실(`.gitignore:2`, 레인은 커밋된 main으로 만들어짐)에 맞춘다.
- 실행기가 하는 일 두 가지: (1) 정확도 측정 — 기존 러너 `tests/jev_accuracy.py`의 측정(한국어 예시 22개 × 질문 언어 2개)을 진짜 jev로 · (2) 실제 영상 한 바퀴 — 설정 키워드로 YouTube 공개 영상 몇 개를 검색 → jev 판별 → Claude 고민 정리 · 댓글 초안 → jev 자체 검사 → 코드 검사. **크롬 연결 · 게시는 하지 않는다** (되돌릴 수 없는 일은 이 페이즈 밖).
- 결과는 `docs/live-check/` 아래 파일로 쓰고 사람이 커밋한다 — 커밋하지 않은 파일은 Phase 6B의 레인에 보이지 않는다. 실행 안내 마지막 줄에 커밋 명령을 적는다.
- 서비스마다 호출 수 천장을 두고, 닿으면 그 자리에서 멈추며 결과 파일에 천장 도달을 적는다 — 사람이 돌려도 반복 버그로 호출이 끝없이 나가지 않게.
- 키 문자열은 결과 파일 · 화면 출력 · 오류 메시지 어디에도 나오지 않는다 — 결과 파일은 커밋되기 때문. 테스트가 가짜 키 문자열로 잠근다.
- 키나 SDK가 없으면 아무것도 부르지 않고 무엇이 없는지 한 줄로 알리고 끝난다 (러너의 기존 "키 없으면 부르지 않음"과 같음). 키 읽기는 Phase 2가 더하는 `.env` 읽기를 쓴다.
- 실행 안내는 이 기계 기준으로 쓴다: `pip`이 없고 `uv`가 있다(`~/.local/bin/uv`) — `uv venv` → `uv pip install -r requirements.txt` → 실행 → 커밋. 실행 전에 사람이 예시 22개의 정답 라벨을 훑는 단계(H-010)를 첫 줄에 둔다.
- **The plan decides** — 결과 파일 모양(JSON · JSONL · 사람이 읽는 Markdown 요약을 함께 둘지) · 명령 수(하나 vs 측정 · 한 바퀴 둘) · 실제 영상 개수 · 서비스별 천장 숫자 · 자막 · 설명을 결과 파일에 얼마나 잘라 남길지 · 조건: Phase 6B가 결과 파일만으로 판별 기준값과 자체 검사 하한을 다시 계산할 수 있어야 하고(예시마다 noul 확률 · choice 보기와 신뢰도 · 판정 · 이유, 초안마다 검사 점수 · 코드 검사 결과, 호출마다 오류 이름과 상태 코드, Claude 모델 id 수락 여부), 천장 도달 · 키 미노출 · 키 없을 때 호출 0번을 테스트가 가짜 SDK · 가짜 클라이언트로 잠근다.

Trade-offs accepted
- 사이클은 "진짜로 되는가"를 혼자 확인하지 못한다 — 사람이 돌린 뒤 Phase 6B에서야 안다.
- 사람이 한 번 손을 써야 한다(라벨 훑기 · 키 넣기 · 설치 · 실행 · 커밋, 10–15분). jev 키는 얼리 액세스 대기 명단이라 키가 늦으면 Phase 6B와 Phase 7이 그만큼 기다린다 (질문 1 A의 대가로 받아들임).
- 공개 영상 제목 · 설명 일부와 AI 초안이 저장소에 남는다 — 키와 개인 정보는 없다.

Responsibilities & risks to guard against
- 키 노출: 결과 파일은 커밋되므로 키가 섞이면 바로 공개된다 — 테스트와 실행 안내 둘 다에서 막는다.
- YouTube 검색은 쿼터를 쓴다(검색 1번 100단위) — Phase 2의 하루 한도 가드를 지나게 한다.
- 결과 파일은 믿을 수 없는 입력(영상 글)을 담는다 — 6B가 숫자만 읽고 글 속 지시문을 따르지 않게 모양을 정한다.

Dependencies
- Depends on: Phase 2 (YouTube 클라이언트 · `.env` 읽기), Phase 3 (판별 · 정확도 러너), Phase 5 (작성 · 자체 검사)
- Unlocks: Phase 6B (사람 실행 뒤)

Open questions
- none

---

## Phase 6B — 진짜 결과 반영 · 정확도 기록 · 기준값 조정
- Status: Not started
- Slug: live-check-apply
- After: Phase 6A
- Goal: 사람이 커밋한 `docs/live-check/` 결과로 계약서의 정확도 기록을 채우고, 판별 기준값과 자체 검사 통과 하한을 잰 값으로 바꿔 테스트로 잠근다.

Decisions
- 첫 단계에서 `docs/live-check/`에 사람이 돌린 결과 파일이 커밋돼 있는지 본다. 없으면 아무것도 고치지 않고 `unmeasured`로 멈춘다 — 가짜 결과로 기준값을 바꾸지 않는다.
- 정확도 기록: 계약 '주제 판별' 절의 정확도 칸(`docs/contracts.md`, 지금 "아직 재지 않음 — 2026-10-13 키 없음")에 언어별 결과 두 줄을 적는다 (H-011이 사람에게 맡겼던 기록).
- 정확도에 따른 길은 기존 결정 그대로: ko 통과면 그대로 · en만 통과면 질문 문구를 영어로(`QUESTION_LANGUAGE`) · 둘 다 미달이면 drift로 인터뷰에 돌아온다 (판단 AI 교체는 사람 결정, Cross-cutting).
- Claude 모델 id: 결과 파일에 `claude-sonnet-5-5` 거절(404)이 있으면 Phase 5의 다른 후보 `claude-haiku-5-5`로 `config.yaml`을 바꾼다 (Phase 5 "The plan decides"의 후보 안).
- **The plan decides** — 새 기준값(`noul_yes_min` 0.8 · `noul_no_max` 0.2 · `choice_min_confidence` 0.5 · 자체 검사 통과 하한 0.7 · `REPEAT_MIN_CHARS` 12)을 무엇으로 정할지, 표본이 모자라 그대로 두는 값은 무엇인지 · 조건: 예시 22개에서 잘못된 일치 0을 지키고(러너의 통과 조건), 바꾼 값마다 근거 숫자를 계약에 함께 적으며, 설정 테스트가 새 값을 잠근다. 그대로 둔 값은 "표본 부족" 이유를 적는다.

Trade-offs accepted
- 예시 22개 + 영상 몇 개는 작은 표본이다 — 기준값은 "잰 값"이지만 단단하지 않다. Phase 8의 실제 실행 뒤 다시 볼 수 있다.

Responsibilities & risks to guard against
- 계약에 적은 숫자와 결과 파일의 숫자가 같아야 한다 — 손으로 옮겨 적지 말고 결과 파일에서 읽은 값을 쓴다.
- 이 페이즈의 보고서에 H-011 · H-012 · H-018을 닫을 근거를 남긴다 (`status`를 `done`으로 바꾸는 것은 사람).

Dependencies
- Depends on: Phase 6A, 사람의 진짜 실행과 결과 커밋
- Unlocks: Phase 7

Open questions
- none

---

## Phase 7 — 파이프라인 연결 · 운영 규칙 통합
- Status: Not started
- Slug: pipeline-rules
- After: Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 6B
- Goal: 다섯 모듈을 한 흐름으로 묶고, 운영 규칙 다섯 가지(영상당 댓글 1개 · 하루 상한 10개 · 채널 대기 24시간 · 허용 목록 강제 · 테스트 모드)가 실제로 작동하는지 확인한다.

Decisions
- 영상당 댓글 1개와 채널 대기 시간은 게시 기록 저장소(Phase 1)에서 확인한다.
- 하루 상한(기본 10개)은 게시 성공 기록만 센다.
- (2026-10-13, Phase 1 HC1-2 질문 1 A) 로그(`logbook.py`)는 값 속 제어 문자 — 유니코드 범주 Cc(NUL · ESC · DEL · C1 등)와 Cf(U+202E 같은 양방향 제어, U+200B 등) — 를 언제나 따옴표 값 안의 `\uXXXX` 이스케이프로 쓴다. 공백이 없어도 이런 글자가 든 값은 따옴표 없이 쓰지 않는다. 계약 7절 "값 쓰는 법" 표와 그 아래 문단을 함께 고친다(이미 있는 이름의 뜻은 그대로, 이스케이프 대상만 넓어짐 — 계약 10절). 근거: Phase 1 은 줄 바꿈 글자 10개만 이스케이프해서, 제목 속 NUL 하나로 GNU grep 이 로그 전체를 `binary file matches` 로 가리고 ESC 는 터미널에 가짜 `mode=live result=posted` 줄을 그렸다(Phase 1 세 번째 ship-report R1, 인터뷰에서 재현). 이 페이즈는 Phase 2–6 이 모두 끝난 뒤 혼자 돌아 다른 레인과 부딪히지 않고, 평가자가 읽는 `logs/sample.log`(Phase 8)보다 앞선다 — 제출 증명을 어떤 도구로 읽어도 같게 하는 쪽을 최적화.
- **The plan decides** — 위 로그 고침의 세부 · 후보: 이스케이프 범위(Cc · Cf 전부 vs Cc 와 양방향 제어만) · `parse_line` 이 고치기 전에 쓰인 날 제어 문자 줄을 계속 읽을지 거부할지 · `tests/mutants.py` 에 이 고침을 되돌리는 변이를 더할지 · 조건: Phase 1 ship-report R1 의 재현 입력(제목 `x\x00y\x00z`, `a\x1b[2Kb`)이 테스트의 실제 입력이어야 하고, 그 제목들과 `POST … result=posted` 줄을 쓴 파일에서 GNU grep `posted` 가 게시 줄을 보여 주며(binary 판정 없음) 파일에 날 제어 문자가 0개이고 `parse_line` 이 원래 값을 되돌림을 테스트가 잠근다.

Trade-offs accepted
- 실패 후 재시도는 하지 않고 다음 영상으로 넘어간다 (과제 ⑤).
- (2026-10-13, Phase 1 HC1-2) 로그 제어 문자 고침이 이 페이즈로 와서 일이 조금 늘어난다(코드 몇 줄 · 테스트 행 · 계약 7절 표). Phase 2–6 이 도는 동안 쓰인 `logs/agent.log` 는 이 고침 전 모양이다 — 실행 로그는 git 무시이고 실행마다 쌓이는 파일이라 제출물(`sample.log`)에는 영향이 없다.

Responsibilities & risks to guard against
- 허용 목록 밖 영상이 게시되지 않았다는 증거를 코드와 기록으로 보여줄 수 있어야 함 (과제 체크리스트).
- (2026-10-13, Phase 1 HC1-2) 로그를 사람이 grep · 터미널로 읽어도 `parse_line` 과 같은 내용이 보여야 한다 — 이 페이즈의 리뷰에서 로그 파일에 날 제어 문자가 남지 않는지 확인.

Dependencies
- Depends on: Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 6B (잰 기준값 — 2026-10-13 질문 1 A)
- Unlocks: Phase 8

Open questions
- none

---

## Phase 8 — 제출물 (README · PROCESS.md · sample.log · 시연)
- Status: Not started
- Slug: submission-docs
- After: Phase 7
- Goal: 처음 보는 사람이 README만 보고 10분 안에 테스트 모드를 실행하게 하고, 제작 노트와 실제 실행 기록을 채운다.

Decisions
- README 필수 항목: 설치 · 실행 순서, 크롬 원격 제어 방법(Mac / Windows), API 키 발급 (YouTube Data API, TypeSafe jev — 얼리 액세스 콘솔 `console.typesafe.ai`, Anthropic Claude), 테스트 모드 실행과 결과 예시.
- PROCESS.md: 단계를 나눈 이유, '뜨기 직전' 기준 근거, 판별·작성 프롬프트 원문(jev 질문 문구와 보기 목록 · Claude 작성 프롬프트), 사용한 AI 도구 목록, 판단은 jev · 글쓰기는 Claude로 나눈 이유, 실패와 개선 2가지 이상, 총 소요 시간.
- `logs/sample.log`: 실제 실행 기록 (과제 체크리스트).
- 시연 영상(3분 내외)은 사람이 찍는다 — 이 페이즈에서 만들지 않고 링크 자리만 둔다.

Responsibilities & risks to guard against
- 키 노출 여부를 마지막에 확인 (과제 평가 항목).
- (2026-10-13, Phase 1 HC1 질문 2) 로그의 테스트 저장 이유에 가드의 네 이유(`invalid_video` · `not_in_allowlist` · `dry_run` · `allowlisted`) 밖의 `page_mismatch` 가 있다 — README 의 테스트 모드 결과 설명이나 PROCESS.md 에 한 줄로 뜻을 적는다.

Dependencies
- Depends on: Phase 7
- Unlocks: none

Open questions
- (2026-10-13 질문 3 B — "Phase 8은 그때 정한다") `logs/sample.log`의 실제 실행은 누가 돌리나: Phase 6A · 6B처럼 사람이 셸에서 돌리고(로그인된 크롬 · 허용 목록 영상) 사이클은 커밋된 기록만 읽을지, 다른 방법을 쓸지. 사이클은 지금 진짜로 부를 수 없다 — 레인에 `.env`가 없고(`.gitignore:2`) 헌법 Never 절이 승인 없는 외부 전송을 막으며, 로그인된 크롬은 사람만 준비할 수 있다. 정하면 Phase 8을 사람 실행 앞뒤로 나눌지도 함께 정한다. 이 질문이 열려 있으면 Phase 8 사이클은 계획 전 첫 관문(미결 질문 판정)에서 멈추고 사람에게 묻는다 — 결정문에 답이 없어 판정자가 대신 풀 수 없다. 실행 단계에서 멈춰 반나절을 잃는 것보다 시작할 때 정하는 쪽.

---

## Cross-cutting open questions
- 병렬 진행 설정: 현재 `.adw/cycle.yml:83`의 `lane.max`는 1이라 페이즈가 한 번에 하나씩 돈다. Phase 2–6을 동시에 돌리려면 허브 ⚙ Settings → Cycle에서 5 이상으로 올려야 한다 (최대 9). 사용자가 설정한다. 막히는 항목은 아님 — 1이어도 순서대로 진행된다.
- 판단 AI 교체는 사람 결정: Phase 6B가 잰 jev의 한국어 정확도가 낮게 나와도 jev를 다른 모델로 바꾸는 것은 사용자 원칙("내용 판단은 jev")을 바꾸는 일이라 사이클이 혼자 정하지 않는다. 막히는 항목은 아님 — 발생하면 drift로 이 인터뷰에 돌아온다.

## Decision log
| Date | Phase | Decision | Why |
|------|-------|----------|-----|
| 2026-10-12 | 1 | 구현 언어 Python 3 + Playwright | 공식 Python 문서가 `connect_over_cdp`를 명시하고, 다섯 모듈이 한 언어라 계약이 단순함 (인터뷰 답변 1) |
| 2026-10-12 | 3, 5 | 판별·작성 AI는 `systemone model jev` | 사용자가 "내용 판단은 systemone model jev로 진행" 확정 (인터뷰 답변 2) |
| 2026-10-12 | 2 | 기본 키워드 5개 × 30분은 쿼터 초과 (240회/일 > 약 100회/일) → 주기·키워드 조합은 Plan에서 결정 | 쿼터 계산, `docs/research/search-quota.md` |
| 2026-10-12 | 6 | 기본 크롬 프로필 사용 불가 → 전용 프로필 또는 Chrome for Testing | Chrome 136+ 기본 프로필에서 디버깅 포트 무시, `docs/research/browser-cdp.md` |
| 2026-10-12 | 1 | NFR: 성능 목표 없음, 접근성 해당 없음, 한국어 한정, 가동 시간 목표 없음, Mac·Windows 호환 | 과제 PDF 요구 · CLI 에이전트 특성 |
| 2026-10-12 | 3, 5 | jev 접속 확정: TypeSafe API `POST https://api.typesafe.ai/v1/systemone`, `typesafe-sdk`, `jev-latest`, 키 `.env`의 `TYPESAFE_API_KEY` | 사용자가 준 블로그 · 공식 문서 (`docs/research/jev.md`) — 열린 질문 해소 |
| 2026-10-12 | 5 | 작성 AI를 jev → Claude로 변경 (고민 정리 · 댓글 작성). jev는 판별과 자체 검사만 | jev는 글을 생성하지 않음 (공식 문서). 사용자 선택 A — 처음 원칙 "판단은 jev"와 일치 |
| 2026-10-12 | 3 | 판별 '이유'는 jev가 고른 보기 이름 + 확률로 기록 | jev는 이유 문장을 쓸 수 없음 |
| 2026-10-12 | 3 | 한국어 정확도는 사람이 표시한 예시 묶음으로 확인, 낮으면 질문 문구만 영어로 (plan 결정) | jev는 영어가 주 언어, CJK 정확도 미보장 (`docs.typesafe.ai/models`) |
| 2026-10-13 | 1 | ship-check BLOCKED 분류: `code miss` — 가드 주소 해석과 설정 로더 예외가 기존 결정을 어김, 같은 브랜치에서 수정 후 ship-check 재실행 | `youtu.be/A/../B` 가 A 로 `live=True`, 날짜 모양 설정 값이 `run_loop` 를 죽임 (`.adw/ship-report.md` § Blockers, 인터뷰에서 재현) |
| 2026-10-13 | 1, 6 | 가드는 계약 5절 형식만 정확히 받고, 계약 6절에 "크롬에는 `watch?v={decision.video_id}` 만 열고 클릭 직전 `page.url` 로 재확인"을 더함 (두 겹 잠금) | 가드와 브라우저가 같은 주소를 다르게 읽는 자리를 없앰 · Phase 6 시작 전이라 비용 0 (복구 질문 1 A) |
| 2026-10-13 | 1, 6 | 크롬 프로필은 `chrome-profile/` 또는 저장소 밖에만 · `.gitignore` 와 계약 8절에 측정된 이름 11개 추가 | 위치가 첫 방어, 이름 목록이 규칙을 어겼을 때의 둘째 방어 · 계정 이메일·방문 기록 공개 방지 (복구 질문 2 C, ship-report R13) |
| 2026-10-13 | 1 | 두 번째 ship-check 의 민감 확인 정지 → 분류 `drift`(형식 목록 결정이 `?v=` 모양을 놓침) · 같은 브랜치에서 고침 사이클 후 ship-check 재실행 | 민감 줄은 확인(받아들임)이 아니라 고침으로 닫음 — `human_checks.py confirm` 은 부르지 않음 (HC1 인터뷰) |
| 2026-10-13 | 1 | 가드: `youtu.be` · `/shorts/` 쿼리에 `v` 키(한 번 푼 뒤 셈, `%76` 포함)가 있으면 `invalid_video`, 다른 쿼리는 계속 허용 · `/watchx` · `/watch/` 거부 행 고정 | 유튜브가 꼬리의 `v` 로 B 를 재생(실측 `303`)하는데 가드는 A 로 읽음 · 계약 6절 잠금은 아직 문서뿐 → 가드 혼자서도 막음. 쿼리 전부 거부는 공유 버튼 주소(`?si=`) 허용 목록 항목을 조용히 무력화해 택하지 않음 (HC1 질문 1 A) |
| 2026-10-13 | 1, 6 | 계약 6절 3.2 같은 영상 확인 조항 확정(`recheck.video_id != decision.video_id` → 클릭 안 함, `page_mismatch` 테스트 저장) | 자동 재생 · 사람 조작으로 크롬이 다른 허용 영상으로 옮겨 가면 기록은 A, 댓글은 A2 → 영상당 1개 · 기록 증명이 깨짐. plan 이 트래커보다 넓게 적은 것을 사람이 확인 (HC1 질문 2 A) |
| 2026-10-13 | 1 | 지난 R3(로그 줄 바꿈류 글자 위조) · R6(`.inf` · 큰 수 설정) 과 ship-report R7 테스트 행을 이번 고침 사이클에 포함 | 두 파일 모두 Phase 1 소유 · Phase 2–6 다섯 레인이 동시에 출발하기 전이 가장 쌈 · 주인 없이 두 번 다시 나옴 (HC1 질문 3 A) |
| 2026-10-13 | 1, 7 | 세 번째 ship-check(`READY WITH RISKS`)의 민감 줄 확인: 로그 값 속 제어 문자는 Phase 1 에서 받아들이고 출하, 고침(Cc · Cf 는 언제나 따옴표 안 `\uXXXX`, 계약 7절 표 함께)은 Phase 7 이 맡음 · `human_checks.py confirm` 으로 민감 줄을 닫음 | 코드는 결정대로이고 `parse_line` 은 정확 · 고침 사이클 한 번(약 1시간 50분)과 네 번째 ship-check 를 아낌 · Phase 7 은 혼자 돌아 레인 충돌이 없고 `sample.log`(Phase 8)보다 앞섬 · 주인 없는 위험이 다시 정지로 돌아온 선례를 피함 (HC1-2 질문 1 A) |
| 2026-10-13 | 6A, 6B, 7 | Phase 7 앞에 '진짜로 붙여 보기'(6A 준비 · 6B 반영)를 끼움. Phase 7은 6B 뒤 | jev · Claude는 키 · SDK 없이 공식 문서 · SDK 소스 · 가짜로만 만들고 테스트됐고 계약 정확도 칸은 "아직 재지 않음". 2026-10-12 인터뷰가 접속 방법만 닫고 키 보유 여부를 묻지 않은 빈틈. 다섯 모듈을 묶기 전이 고칠 곳이 한 군데인 마지막 시점 (사용자 "jev api 제공한 적 없는데" · 질문 1 A) |
| 2026-10-13 | 6A, 6B | 진짜 외부 호출은 사람이 셸에서 돌리고, 사이클은 실행기를 만들어 가짜로 테스트 · 커밋된 결과 파일만 읽음 | 외부 전송 버튼은 늘 사람이, 키는 사이클 손에 안 감 · 헌법 Never 절과 레인에 `.env` 없음에 맞음. 대가로 사람 실행을 사이에 두고 두 페이즈로 나뉨 (질문 2 C) |
| 2026-10-13 | 8 | 위 규칙을 Phase 8(`sample.log` 실제 실행)에 쓸지는 Phase 8 시작 전에 정함 → Phase 8 Open questions | 지금 바꾸는 범위를 좁게. Open question으로 두어 Phase 8이 실행 단계에서 멈추기 전에 인터뷰로 오게 함 (질문 3 B) |
