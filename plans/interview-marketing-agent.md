# 마케팅 AI 에이전트 — Plan & Phase Tracker

<!-- Maintained by the deep-interview skill. Re-running the interview updates this file in place. -->

- Created: 2026-10-12
- Last updated: 2026-10-12
- Overall status: Planning

## Summary
유튜브 댓글 에이전트 (과제 안내: `docs/marketing-agent.pdf`). 주제 키워드로 새 영상을 찾고(탐지), AI가 주제 일치를 판별하고(판별), 조회수 조건으로 '뜨기 직전' 영상을 고르고(타이밍), 영상 고민에 맞춘 댓글을 쓰고(작성), 로그인된 크롬에 자동 게시합니다(게시). 빠른 제작이 목표라 뼈대(Phase 1)를 먼저 만들고, Phase 2–6은 뼈대의 계약만 따르므로 동시에 진행합니다. 실제 게시는 허용 목록 영상에만, 코드에서 강제합니다. 언어는 Python + Playwright, 판별과 작성에는 `systemone model jev`를 씁니다.

## Phases
- [ ] Phase 1 — 뼈대와 계약 (설정 · 데이터 모양 · 저장 · 운영 가드)
- [ ] Phase 2 — ① 탐지 · 조회수 추적 (watcher)
- [ ] Phase 3 — ② 판별 · 주제 일치 (classifier)
- [ ] Phase 4 — ③ 타이밍 · 뜨기 직전 판단 (trigger)
- [ ] Phase 5 — ④ 댓글 작성 · 자체 검사 (writer)
- [ ] Phase 6 — ⑤ 크롬 연결 · 게시 · 확인 (poster)
- [ ] Phase 7 — 파이프라인 연결 · 운영 규칙 통합
- [ ] Phase 8 — 제출물 (README · PROCESS.md · sample.log · 시연)

Parallel shape: Phase 1 → (Phase 2 ‖ 3 ‖ 4 ‖ 5 ‖ 6) → Phase 7 → Phase 8. Phases 2–6 run at the same time only when `lane.max` ≥ 5 (see Cross-cutting open questions).

---

## Phase 1 — 뼈대와 계약 (설정 · 데이터 모양 · 저장 · 운영 가드)
- Status: Not started
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

Trade-offs accepted
- 바로 쓸 수 있는 프레임워크 대신 얇은 직접 구현을 택함 — 빠른 제작을 위해 기능이 적음.

Responsibilities & risks to guard against
- 계약을 바꾸면 Phase 2–6 전부에 영향 — Phase 1의 데이터 모양은 변경하지 않는 것을 원칙으로 함.
- `.env`, 크롬 프로필, 쿠키가 커밋되지 않았는지 Phase 8 전에 다시 확인.

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
- Status: Not started
- Slug: classifier-topic
- After: Phase 1
- Goal: 영상의 제목 · 설명 · 자막(있을 경우)을 읽고 주제 일치 여부와 이유를 기록한다. 키워드만 겹치는 영상(예: '연애'가 들어간 게임 영상)을 걸러낸다.

Decisions
- 판별 AI는 `systemone model jev`를 쓴다 — 사용자가 "내용 판단은 systemone model jev로 진행"이라고 확정 (인터뷰 답변 2).
- 판별 결과는 `일치 여부 · 이유` 두 필드로 저장한다 (과제: "주제 일치 여부와 이유를 기록").

Trade-offs accepted
- 호출 방식을 모르는 상태에서는 가짜(mock) 응답으로 테스트만 가능 — 실제 판별 품질은 접속 정보가 들어온 뒤에만 검증.

Responsibilities & risks to guard against
- 키워드 일치만으로 통과시키지 않는다 (과제 요구).
- 모델 응답 형식이 깨졌을 때 '일치'로 처리하지 않는다 — 불일치 또는 보류로 기록.

Dependencies
- Depends on: Phase 1
- Unlocks: Phase 5, Phase 7

Open questions
- `systemone model jev`의 접속 방법이 필요합니다: 제공사 이름, API 주소(또는 실행 방식), 인증 방법(키 이름). 사용자가 이 정보를 알려주기 전까지 실제 호출 코드는 막혀 있고, mock 기반 구현까지만 진행합니다. (사용자는 "지정 파일에 작성하겠다"고 답했으나 파일 위치는 인터뷰에서 확정되지 않음.)

---

## Phase 4 — ③ 타이밍 · 뜨기 직전 판단 (trigger)
- Status: Not started
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
- Status: Not started
- Slug: writer-comment
- After: Phase 1
- Goal: 영상의 고민을 한 줄로 정리하고, 그 고민과 이어지는 '연애사주 경험' 댓글을 40–120자로 쓴다. 영상 속 구체적인 장면이나 말을 하나 이상 언급하고, 링크를 넣지 않으며, 이전 댓글과 같은 문장을 반복하지 않는다.

Decisions
- 작성 AI는 `systemone model jev`를 쓴다 (인터뷰 답변 2).
- 자막이 없으면 제목·설명과 인기 댓글을 입력으로 쓴다 (과제 ④).
- 자체 검사 단계를 둔다 — 영상 내용과 댓글이 맞는지 AI가 다시 검사 (과제 가점 항목). 같은 모델을 쓸지 여부는 구현 시 결정.
- **The plan decides** — 이전 댓글 중복 검사 방식: 최근 작성 문장과 비교 방법 (정확 일치 vs 유사도). 조건: '같은 문장 반복 금지'를 코드로 확인 가능해야 함.

Trade-offs accepted
- 자체 검사는 호출을 한 번 더 쓴다 — 비용과 지연이 늘어남.

Responsibilities & risks to guard against
- 광고처럼 읽히는 댓글 (과제 PROCESS.md 예시) — 링크 금지 규칙과 함께 검사 규칙을 프롬프트에 기록.
- 길이 기준(40–120자)을 글자 수로 검사 — 바이트가 아니라 글자 기준.

Dependencies
- Depends on: Phase 1, Phase 3 (판별 결과가 작성 입력의 일부)
- Unlocks: Phase 6, Phase 7

Open questions
- `systemone model jev`의 접속 방법 (Phase 3과 같은 항목). 판별과 작성이 같은 접속을 쓰는 것으로 가정.

---

## Phase 6 — ⑤ 크롬 연결 · 게시 · 확인 (poster)
- Status: Not started
- Slug: poster-chrome
- After: Phase 1
- Goal: 로그인된 크롬에 연결해 영상을 열고, 댓글 창까지 이동해 입력하고, 게시하고, 내 댓글이 실제로 보이는지 확인한다. 실패하면 원인과 화면 캡처를 기록하고 다음 영상으로 넘어간다.

Decisions
- 크롬 연결은 Playwright `connect_over_cdp`로 한다 (언어 결정과 같은 근거, `docs/research/stack.md`).
- **The plan decides** — 크롬 프로필: 기본 프로필 불가. Chrome 136부터 기본 데이터 디렉터리에서 `--remote-debugging-port`가 무시되므로 전용 프로필(`--user-data-dir`를 기본 경로가 아닌 곳으로)을 쓰고 한 번 로그인한다. 대안: Chrome for Testing (자동화 전용 빌드, 크롬 팀 권장). 근거 `docs/research/browser-cdp.md`. 테스트가 프로필 경로 검증을 잠가야 함.
- 게시 직전 허용 목록 확인 — 목록에 없으면 게시하지 않고 작성 결과만 파일로 저장 (과제 ⑤). Phase 1 가드를 호출한다.
- 테스트 모드(`--dry-run`): 게시 직전까지만 실행하고 댓글을 파일로 저장.

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

## Phase 7 — 파이프라인 연결 · 운영 규칙 통합
- Status: Not started
- Slug: pipeline-rules
- After: Phase 2, Phase 3, Phase 4, Phase 5, Phase 6
- Goal: 다섯 모듈을 한 흐름으로 묶고, 운영 규칙 다섯 가지(영상당 댓글 1개 · 하루 상한 10개 · 채널 대기 24시간 · 허용 목록 강제 · 테스트 모드)가 실제로 작동하는지 확인한다.

Decisions
- 영상당 댓글 1개와 채널 대기 시간은 게시 기록 저장소(Phase 1)에서 확인한다.
- 하루 상한(기본 10개)은 게시 성공 기록만 센다.

Trade-offs accepted
- 실패 후 재시도는 하지 않고 다음 영상으로 넘어간다 (과제 ⑤).

Responsibilities & risks to guard against
- 허용 목록 밖 영상이 게시되지 않았다는 증거를 코드와 기록으로 보여줄 수 있어야 함 (과제 체크리스트).

Dependencies
- Depends on: Phase 2, Phase 3, Phase 4, Phase 5, Phase 6
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
- README 필수 항목: 설치 · 실행 순서, 크롬 원격 제어 방법(Mac / Windows), API 키 발급 (YouTube Data API, 사용한 AI 모델), 테스트 모드 실행과 결과 예시.
- PROCESS.md: 단계를 나눈 이유, '뜨기 직전' 기준 근거, 판별·작성 프롬프트 원문, 사용한 AI 도구 목록, 실패와 개선 2가지 이상, 총 소요 시간.
- `logs/sample.log`: 실제 실행 기록 (과제 체크리스트).
- 시연 영상(3분 내외)은 사람이 찍는다 — 이 페이즈에서 만들지 않고 링크 자리만 둔다.

Responsibilities & risks to guard against
- 키 노출 여부를 마지막에 확인 (과제 평가 항목).

Dependencies
- Depends on: Phase 7
- Unlocks: none

Open questions
- none

---

## Cross-cutting open questions
- 병렬 진행 설정: 현재 `.adw/cycle.yml:83`의 `lane.max`는 1이라 페이즈가 한 번에 하나씩 돈다. Phase 2–6을 동시에 돌리려면 허브 ⚙ Settings → Cycle에서 5 이상으로 올려야 한다 (최대 9). 사용자가 설정한다. 막히는 항목은 아님 — 1이어도 순서대로 진행된다.
- `systemone model jev` 접속 방법 (Phase 3·5의 Open question과 같은 항목).

## Decision log
| Date | Phase | Decision | Why |
|------|-------|----------|-----|
| 2026-10-12 | 1 | 구현 언어 Python 3 + Playwright | 공식 Python 문서가 `connect_over_cdp`를 명시하고, 다섯 모듈이 한 언어라 계약이 단순함 (인터뷰 답변 1) |
| 2026-10-12 | 3, 5 | 판별·작성 AI는 `systemone model jev` | 사용자가 "내용 판단은 systemone model jev로 진행" 확정 (인터뷰 답변 2) |
| 2026-10-12 | 2 | 기본 키워드 5개 × 30분은 쿼터 초과 (240회/일 > 약 100회/일) → 주기·키워드 조합은 Plan에서 결정 | 쿼터 계산, `docs/research/search-quota.md` |
| 2026-10-12 | 6 | 기본 크롬 프로필 사용 불가 → 전용 프로필 또는 Chrome for Testing | Chrome 136+ 기본 프로필에서 디버깅 포트 무시, `docs/research/browser-cdp.md` |
| 2026-10-12 | 1 | NFR: 성능 목표 없음, 접근성 해당 없음, 한국어 한정, 가동 시간 목표 없음, Mac·Windows 호환 | 과제 PDF 요구 · CLI 에이전트 특성 |
