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

### H-010 — 22개 예시의 일치 · 불일치 라벨을 사람이 검토하기(`tests/classifier_examples.py`) — 정확도 숫자를 믿기 전에
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-011 — `pip install -r requirements.txt` 후 `.env` 의 키를 export 하고 `python3 -m tests.jev_accuracy` 실행. exit 3 이면 키 · SDK · 연결부터 고침. 권고 줄 없이 traceback 과 exit 1 이면 설치 · 설정 문제지 모델 문제가 아님(R7). 결과 두 줄을 계약 '주제 판별' 절의 정확도 기록에 적고, 권고가 en 이면 후속 사이클, 둘 다 미달이면 인터뷰로
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-012 — 실제 `CLASSIFY` 이유를 보고 `noul_yes_min` · `noul_no_max` · `choice_min_confidence`(지금 0.8 / 0.2 / 0.5, 잰 값 아님) 조정하기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-013 — 착지 때 lane 2 · 4 · 5 가 먼저 `## 11.` 을 붙였으면 이 절 번호를 다시 매기고, `config.py` 키 꼬리 · `config.yaml` · `VALID` · `CommittedConfigTest` · `requirements.txt` · 계약 1 · 2 · 8 · 10절의 겹친 추가분을 합치기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-014 — topic 길이에 상한을 둘지(계약 2절), 아니면 state 몫이 2만 2천 바이트 아래면 보류할지 정하기 — 지금은 아주 긴 topic 에서 영상 글 없이 판정이 나옴(R6)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-015 — 판정에 고른 보기의 확률(`probabilities[choice]`)도 볼지 정하기 — 지금은 확률 0.01 인 보기도 confidence 만 높으면 일치(R8)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-016 — `pip-audit` 가 있는 기계에서 `pip-audit -r requirements.txt` 를 돌리고, `typesafe-sdk==0.7.4` 해시 고정으로 좁힐지 정하기(R12)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-017 — 트래커 Phase 7 절에 이번 주인 줄 옮겨 적기 — `on_error` 는 예외 이름 · 상태만 쓰고 `__cause__` · traceback 을 로그에 남기지 않음, `응답 모양 오류` 이유 길이 자르기(R11)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-3
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-3-classifier-topic
- tag: plain
- status: open

### H-018 — 실제 `ANTHROPIC_API_KEY` 와 jev 키로 영상 몇 개를 돌려, 모델 id `claude-sonnet-5-5` 가 받아들여지는지(`ERROR where=writer.claude … 404` 가 아니면 됨) 확인하고, 통과 하한 `0.7` 과 `REPEAT_MIN_CHARS` 12 를 다시 쓰기 · 건너뛰기 비율과 jev 한국어 정확도에 맞춰 조정하기(이번에 더해진 둘도 함께 봄: 규칙 5 와 '연애사주' 언급이 부딪혀 광고 질문 점수가 오르는지(R4), 자료에 넣은 전각 `＜draft_comment＞` 가짜 초안에 jev 가 흔들리는지(R3))
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-5
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-5-writer-comment
- tag: plain
- status: open

### H-019 — 착지 때 lane-merge 가 6개 파일 충돌(config.yaml · docs/contracts.md · requirements.txt · src/agent/config.py · tests/mutants.py · tests/test_config.py)을 NEEDS-HUMAN 으로 넘기면 Phase 3 · 5 의 설정 키와 `requirements.txt` 줄이 모두 살아남게 풀기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-5
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-5-writer-comment
- tag: plain
- status: open

### H-020 — 링크 검사의 빈틈(점 닮은꼴 `‧` `•` `∙` `°` · 키릴 끝 · U+202E 뒤집기 · `saju.한국`)을 jev 광고 질문에 맡겨 받아들일지, 구분점 무리를 넓히고 양방향 제어 글자를 댓글에서 막을지 정하기(R1)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-5
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-5-writer-comment
- tag: plain
- status: open

### H-021 — Phase 7 이 계획을 세우기 전에, 트래커 Phase 7 절에 "`write_comment` 가 던진 예외는 그 영상 하나의 오류로 받아 `ERROR` 로 남기고 다음 영상으로 · jev 포트 어댑터는 상태 코드를 `status_code` 나 메시지로 싣는다"를 더할지 정하기(R2 · R5)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-5
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-5-writer-comment
- tag: plain
- status: open

### H-022 — 크롬을 `PYTHONPATH=src python3 -m agent.chrome --profile chrome-profile`(또는 저장소 밖 폴더)이 찍어 주는 명령으로 켜고, 전용 유튜브(브랜드) 계정으로 한 번 로그인한 뒤 `http://localhost:9222/json/version` 이 `webSocketDebuggerUrl` 을 돌려주는지 보기 — 그 전에 계약 8절의 디버깅 포트 경고를 읽고 노출을 받아들일지 정하고, 에이전트를 안 쓸 때는 그 크롬을 닫기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/verify-plan.md § Checks (V12) · .adw/plan.md § Out of scope
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-023 — Phase 7 이 진입점을 이은 뒤, 본인 허용 목록 테스트 영상에서만 첫 실제 게시를 하고 네 가지를 보기: 댓글이 보이는지, `data/videos.json` 이 `live/posted` 인지, 로그가 `POST … result=reserved` 다음 `result=posted` 인지, `chrome.py` 선택자 상수가 실제 화면과 맞는지(R8)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-024 — 실제 사이트에서 로그아웃된 프로필 · 댓글이 막힌 영상 · 화면 배치가 다른 경우마다 `ERROR … stage=before_click` 줄이 맞는 원인과 `logs/screenshots/` 캡처로 남고, 다음 영상으로 넘어가는지 보기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-025 — Phase 8 제출 직전에 `git ls-files` 로 프로필 · 쿠키 · 스크린샷이 추적되지 않는지 확인하기(H-004 와 같은 일) — 저장소 폴더를 통째로 압축해 낼 경우 git 이 무시하는 `chrome-profile/` · `logs/screenshots/` 를 묶음에서 빼기
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-026 — `--dry-run`(테스트 모드)이 크롬을 아예 열지 않는다는 해석이 뜻한 바와 맞는지 확인하기 — 트래커의 "게시 직전까지만 실행"을 탐지 · 판별 · 타이밍 · 작성까지로 읽었고(계약 6절 4), 그래서 시험 실행은 로그인과 선택자를 한 번도 거치지 않음
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-027 — Phase 7 계획 때 `ChromeSession` 의 수명을 정하기 — 주기마다 붙고 닫을지, 크롬이 꺼졌다 켜지면 다시 붙도록 고칠지(지금은 크롬을 재시작하면 `page_error` 로 계속 멈춤, R3)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-028 — Windows 에서 CLI 가 찍는 실행 줄을 PowerShell 과 cmd.exe 에 붙여 넣어 보고, PowerShell 용 모양(`& '…' '…'`)으로 바꾸거나 경로의 셸 특수 문자를 거절할지 정하기(R4)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-029 — 프로필 위치 점검의 빈틈을 메울지 정하기 — macOS · WSL `/mnt/c` 에서 대소문자만 다른 경로, Chrome Beta · Dev · Canary · Edge 의 기본 폴더(R5)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-030 — 다시 확인과 클릭 사이의 틈을 줄일지 정하기 — `submit()` 안에서 누르기 직전 `page.url` 을 다시 읽어 영상이 바뀌었으면 누르지 않기, 게시 뒤 줄에 `page_url=` 남기기(R1)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-031 — `pip-audit` 이 있는 기계에서 `pip-audit -r requirements.txt` 를 돌리고, CVE-2025-59288 이 PyPI `playwright` 에도 해당하면 하한을 `playwright>=1.55.1` 로 올릴지 정하기(R6)
- project: marketing-agent-demo
- when: 2026-10-13 · plans/interview-marketing-agent.md#phase-6
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6-poster-chrome
- tag: plain
- status: open

### H-032 — ship-check가 통(`.adw/smoke-log.md`)에 `S-NEW`로 미룬 결함을 같은 보고서의 `## Smoke candidates`에도 적으면, smoke-file이 같은 결함을 한 번 더 접수합니다(S-019–S-023 → S-024–S-028). ADW 템플릿의 ship-check/smoke-file 규칙에서 이 중복 접수를 어떻게 막을지 정하기
- project: marketing-agent-demo
- when: 2026-10-13 · adw/smoke-sweep-s024-s028
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/smoke-sweep-s024-s028
- tag: plain
- status: open

### H-033 — 조회수 표본 주기를 검색 주기와 나눌지(선택지 c, 예: 표본 30분 · 검색 120분)는 Phase 4가 필요한 해상도를 정한 뒤 다시 보기
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-2
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-2-watcher-detect
- tag: plain
- status: open

### H-034 — https://developers.google.com/youtube/v3/determine_quota_cost 를 사람이 직접 열어 `videos.list` = 1단위와 `search.list` 별도 통(2026-10-08 갱신)을 눈으로 확인하기(지금까지는 요약 모델을 거쳐 읽음)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-2
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-2-watcher-detect
- tag: plain
- status: open

### H-035 — 실제 `YOUTUBE_API_KEY`로 한 주기를 돌려 `DETECT`/`VIEWS` 줄, `data/quota.json` 항목, 실제 `publishedAt`의 `…Z` 모양, 요청 매개변수가 받아들여지는지 확인하기(Phase 7 `--once`가 생긴 뒤)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-2
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-2-watcher-detect
- tag: plain
- status: open

### H-036 — Windows와 macOS에서 실행해 보기(메모장으로 BOM 붙여 저장한 `.env`, python.org macOS 빌드의 HTTPS 인증서)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-2
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-2-watcher-detect
- tag: plain
- status: open

### H-037 — S-038 이 되돌려진 뒤 다음 스윕 전에, 통의 S-038 방향에서 "계약 머리 문단의 모듈 목록에 더함"을 빼고 config.yaml 1행 주석만 남길지 정하기 — 머리 문단에는 S-029(2026-10-13) 이후 목록이 없음
- project: marketing-agent-demo
- when: 2026-10-14 · adw/smoke-sweep-s038-s042
- from: ship-report.md § Human checks — .adw/verify-report.md § Handoff
- source: adw/smoke-sweep-s038-s042
- tag: plain
- status: open

### H-038 — H-037에 답하기: 이번 스윕은 계약 머리 문단 부분을 빼고 `config.yaml` 1행 주석만 고쳤습니다. 이 선택이 맞는지 확인하고, 맞으면 H-037을 닫습니다
- project: marketing-agent-demo
- when: 2026-10-14 · adw/smoke-sweep-s038
- from: ship-report.md § Human checks — .adw/smoke-batch.md § S-038
- source: adw/smoke-sweep-s038
- tag: plain
- status: open

### H-039 — `docs/contracts.md:534-537` 의 좁힌 풀이 줄이 트래커 Phase 1B 질문 4 A 의 뜻에 맞는지 확인하세요. 트래커 문장은 "옛 11 · 12절 = 그 기록을 남긴 페이즈가 더한 절" 입니다. 계약 줄은 그 앞에 "기록이 그 자리에서 제목이나 함수 · 모듈 이름으로 밝힌 절이 먼저" 를 둡니다. 반례는 Phase 5 출하 보고서의 "11절(트리거 판정)과 12절(주제 판별)" 입니다. 맞으면 확인하고, 아니면 트래커를 고칠지 정하세요.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1b-contract-section-names
- tag: sensitive: tracker decision · confirmed 2026-10-14
- status: confirmed

### H-040 — 트래커 Phase 1B 의 낡은 개수를 고칠지 정하세요. 트래커는 Phase 2 가 "`## 11.` 제목 하나와 계약 11절 8곳(레인 계약서 60 · 69행 포함)"을 들였다고 적었습니다. 기준점 `7575fe6` 에서는 그 제목이 이미 번호가 없었고, 인용은 7곳(src 6 · docs/research 1)이었습니다. 질문 2 A 의 "1–10절 인용 8개 파일 13곳"도 Phase 2 파일을 빼고 센 수입니다. 기준점에서는 16곳이고, 모두 그대로 남았습니다.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1b-contract-section-names
- tag: plain
- status: open

### H-041 — H-013(Phase 3 이 남긴 열린 사람 확인)의 앞 절반 "착지 때 다른 갈래가 먼저 `## 11.` 을 붙였으면 이 절 번호를 다시 매기기"는 이번 규칙(10절 뒤 절은 번호 없음)으로 할 일이 없어졌습니다. 뒤 절반(겹친 추가분 합치기)이 아직 남았는지 보고, 항목을 닫을지 정하세요.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1b
- from: ship-report.md § Human checks — .adw/ship-report.md § Spec compliance
- source: adw/phase-1b-contract-section-names
- tag: plain
- status: open

### H-042 — README 를 처음부터 끝까지 돌린다 — H-010 라벨 훑기 → `.env` 키 → `uv venv` · `uv pip install` → 실행 → 판정 줄과 `오류:` 줄 읽기 → `키 검사: 결과 파일에 키 없음` 확인 → 채점 훑고 `human` 칸 → 두 파일 커밋 → `stop` 이면 Phase 6B 대신 인터뷰
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-043 — Phase 6B 전에 계획의 ① "재지 못함" 읽기(영상 쪽 호출 오류와 `result: "error"` 영상도 ①로 셈, ③은 "검사 두 번 탈락"만)를 받아들일지 정한다 — 받아들이지 않으면 트래커 결정이 필요하다
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-044 — Phase 6B 전에 영상 쪽 응답 모양 오류(`videos.list` · `search.list` 의 200 모양 이상, 영상 판별 · 채점의 답 모양 오류)를 ①에 셀지 정한다 — 지금은 어디에도 세지 않아 영상 0개로 `6B: go` 가 날 수 있다(R1)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-045 — 첫 진짜 실행에서 SDK 동작을 확인한다 — jev `answers[이름].noul` 과 `model`, Claude 모르는 모델 → `status_code == 404`, 400 · 크레딧 오류가 `error`, `max_retries=2` 수락, typesafe 재시도 횟수 · 제한 시간
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-046 — 커밋 전에 `docs/live-check/result.json` · `summary.md` 에 키 조각이 없는지 확인한다 — `키 검사` 줄은 키의 앞 조각만 보므로, 키마다 끝 8글자로도 두 파일을 `grep -F` 한다(R2)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-047 — H-011(Phase 3 에서 온 열린 항목, `tests.jev_accuracy` 결과 두 줄 기록)을 이번 진짜 실행이 닫는지 사람이 정한다
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-048 — Phase 6B: `docs/live-check/result.json` · `summary.md` 를 읽어 계약 '주제 판별'의 정확도 기록 줄을 적고, 6B 결정대로 기준값을 올리고, `fingerprint` 가 지금 코드와 다를 때 할 일을 정한다
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-049 — Phase 6B: 계약 `docs/contracts.md:1078-1080` 의 "`untrusted` 칸 안에만" 문장을 코드만큼 줄일지(`fingerprint.jev_models` 는 jev 가 알린 모델 이름, 100자, 검사 없음) 그 칸을 이름 모양으로 검사하게 할지 정하고, 그때까지 `jev_models` 를 믿을 수 없는 글로 읽는다(R3)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-050 — Phase 6B: `--verdict` 출력은 종료 코드와 첫 줄만 믿고(둘째 줄은 저장된 글을 그대로 찍음), 예시 행 수가 예시 수와 다른 결과 파일은 다시 세지 않으며, 사람이 고친 `result.json` 이 BOM 없이 저장됐는지 본다(R4)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6a
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6a-live-check-prepare
- tag: plain
- status: open

### H-051 — 문자열 설정값(`_text`)을 고칠 주인 페이즈를 정하기 — 짝 없는 서로게이트가 든 `topic` 이 `load_config` 를 통과한 뒤 주기마다 `classify` 의 질문 예산 계산(`try` 밖)에서 `UnicodeEncodeError` 로 터지고, `topic` 길이 상한도 없음(H-014 와 겹침). Phase 1A 결정 밖이라 이 페이즈는 넓히지 않음(헌법 5)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1a-parser-allow-rules
- tag: sensitive: tracker decision · confirmed 2026-10-14
- status: confirmed

### H-052 — 계약 7절 `docs/contracts.md:444-446` 의 "… 터미널에 가짜 줄이 그려지지 않습니다" 를 잰 만큼("제어 문자로 그리는 가짜 줄은 없습니다 — 긴 값이 화면 폭에서 접혀 줄처럼 보이는 것은 막지 않으며, 증명은 `read_log` 로")으로 좁힐지 정하기(헌법 9, R4)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1a
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-1a-parser-allow-rules
- tag: sensitive: public contract · confirmed 2026-10-14
- status: confirmed

### H-053 — H-001 · H-005 · H-006 의 status 를 이 페이즈 증거(가드 받는 이름 목록 · `read_log` · 정수 상한)로 바꾸기. H-002 는 이름 철자 넷을 이제 가드가 막아 필요 없지만, 받는 이름의 값을 유튜브가 한 번 더 푸는지(`?si=x%26v%3DB`, R6)는 재지 않았다는 점을 보고 닫을지 정하기. H-007 은 로그 쪽 절반이 끝났다고 적기
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1a-parser-allow-rules
- tag: plain
- status: open

### H-054 — Phase 8 README 에 "허용 목록 항목은 맨 ID 나 공유 버튼 주소 그대로 — `?list=…` 처럼 `si` · `t` · `feature` 밖 꼬리가 붙으면 그 영상은 오류 없이 테스트 모드로만 돈다" 한 줄 쓰기(R3)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1a-parser-allow-rules
- tag: plain
- status: open

### H-055 — Phase 7 첫 실제 게시(H-023) 때 shorts 영상도 하나 게시해 크롬 `page.url` 꼬리를 보기 — `/shorts/<ID>?pp=…` 처럼 셋 밖 이름이 붙으면 그 영상의 실제 게시는 오류 없이 테스트 모드로 빠짐(R2)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1a
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-1a-parser-allow-rules
- tag: plain
- status: open

### H-056 — Phase 7 이 계획을 세우기 전에, 설정 다시 읽기가 거절되면(1A 의 정수 상한 포함) 옛 `allowed_videos` 로 계속 실제 게시할지, 테스트 모드로 떨어질지, 적어도 그 거절을 크게 알릴지 정하기 — 지금은 허용 목록에서 지운 영상이 같은 저장의 다른 오타 하나로 계속 허용됨(R5)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1a
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-1a-parser-allow-rules
- tag: plain
- status: open

### H-057 — H-014 의 status 를 바꾸기 — 이 페이즈가 topic 상한 500자를 넣었고, 가장 나쁜 합법 보기(50개 × 40자, 한 글자 4바이트)에서 state 몫이 23,391 B(en) / 23,397 B(ko)로 2만 2천 바이트 선 위임을 쟀음(StateTest · 감사 1)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1c
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1c-text-config-allow
- tag: plain
- status: open

### H-058 — 미할당 글자(Cn)를 설정 거절 목록에 계속 둘지 정하기 — 14:03 인터뷰가 계속 거절로 정함(트래커 Phase 1C HC1 질문 1 B, 커밋 4e859be; 메시지 고침은 S-NEW-1, README 한 줄은 Phase 8). 확인 도장은 앞 보고서(.adw/gate/history/20261014-140655-prev-ship-report.md)에 human_checks.py confirm 이 찍은 것을 옮김
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1c
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1c-text-config-allow
- tag: sensitive: tracker decision · confirmed 2026-10-14
- status: confirmed

### H-059 — 범주 L · M · S 안의 빈칸처럼 보이는 글자가 규칙을 지나는 것에 서명하기 — 14:03 인터뷰가 받아들임으로 정하고 글자 부류와 코드 자리로 적음(트래커 Phase 1C HC1 질문 2 A, 커밋 4e859be; 같은 부류의 다른 글자는 새 위험이 아니라 그 줄의 예). 확인 도장은 앞 보고서에서 옮김
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1c
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-1c-text-config-allow
- tag: sensitive: tracker decision · confirmed 2026-10-14
- status: confirmed

### H-060 — Phase 8 README 에 "주제 · 검색어에 ZWJ 로 이은 이모지(👩‍💻, 커플 이모지 등)를 넣으면 설정이 거절된다 — 이모지 선택기가 흔히 만드는 꼴" 한 줄을 쓸지, 이대로 받을지 정하기(R1)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1c
- from: ship-report.md § Human checks — .adw/verify-report.md § Non-gating observations
- source: adw/phase-1c-text-config-allow
- tag: plain
- status: open

### H-061 — Phase 7 계획 전에 chrome_debug_url 을 루프백 주소(localhost · 127.0.0.1 · ::1)로만 받을지 정하기 — http://evil.example\@localhost:9222 는 포트 읽기를 9222 로 지나는데 WHATWG 주소 해석은 호스트를 evil.example 로 읽음(R3, 이 페이즈 전부터)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-1c
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-1c-text-config-allow
- tag: plain
- status: open

### H-062 — 하한을 내리는 쪽 인터뷰를 열지 정하기 — 운영 창 영상 18개 중 11개 보류(9개는 noul 0.2–0.8 사이, 2개는 확신 0.5 미만); 예시로는 `choice_min_confidence` 를 0.47 이하로 내리면 두 언어 21/22 · 잘못된 일치 0(예시 16 풀림, 예시 21 은 보류 그대로) (R9)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6b-live-check-apply
- tag: plain
- status: open

### H-063 — 채점 고침(6C) 착지 뒤 실제 호출 실행기를 다시 돌려 결과 두 파일을 Phase 6D 레인 브랜치에만 커밋하기 — main 에 커밋하면 `tests.test_live_check_applied` 가 빨강(트래커 HC1 질문 2 A); 진짜 jev · Claude · YouTube 호출과 비용(지난 실행 Claude 23 · jev 72 · YouTube 17)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6b-live-check-apply
- tag: plain
- status: open

### H-064 — Phase 6C 결정 "이 페이즈가 채점을 고쳐도 main 은 초록 그대로다"(plans/interview-marketing-agent.md:477)를 고치거나 후보를 좁히기 — 6C 후보 "채점 오류를 판정 줄에 셈"이나 새 지문 칸은 커밋된 결과의 재셈을 바꿔 main 의 `tests.test_live_check_applied` 를 빨강으로 만듦(R12)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6b
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6b-live-check-apply
- tag: plain
- status: open

### H-065 — H-010 을 받아들이거나 주인을 정하기 — 예시 22개 라벨을 실행 전에 사람이 훑었는지는 결과로 알 수 없음; 이번 근거는 두 언어 20/22 · 잘못된 일치 0 · 잘못된 불일치 0 · 놓친 둘은 `no` 예시 16 · 21 의 보류
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6b-live-check-apply
- tag: plain
- status: open

### H-066 — H-018 을 받아들이거나 주인을 정하기 — 트래커는 작성 쪽 근거를 Phase 6D 보고서에 다시 남기게 함; 이번 기록은 모델 이름 둘 다 `accepted` · 0.7 "표본 없음" · 12 "표본 부족" · 광고 P(예) 0.04–0.25 · 자체 검사 탈락 6(장면 5 · 고민 1); R3(전각 가짜 태그)는 재지 않음
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6b-live-check-apply
- tag: plain
- status: open

### H-067 — H-043 을 받아들이거나 주인을 정하기 — 이번 실행은 예시 · 호출 · 영상 오류가 0 이라 ① "재지 못함" 읽기가 판정을 바꾸지 않았음; 트래커 6C 절은 이 항목을 고치지 않으면 장부에 그대로 둔다고 적음
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6b-live-check-apply
- tag: plain
- status: open

### H-068 — H-044 를 받아들이거나 주인을 정하기 — 트래커는 채점 몫(채점 오류를 판정 줄에 셀지)의 주인을 Phase 6C 로 정했고 영상 쪽 응답 모양 몫은 남음; 이번 실행은 채점 `응답 모양` 오류 10/10 이 ①에 세이지 않은 채 판정 `go`, 작성 쪽 정답 0 (R10)
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6b
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6b-live-check-apply
- tag: plain
- status: open

### H-069 — main 체크아웃에서 `docs/live-check/README.md` 대로 `python3 -m tests.live_check` 를 돌리고, 결과 두 파일을 main 이 아니라 Phase 6D 레인 브랜치에 커밋합니다. 판정에 `채점 막힘` 이 있으면 인터뷰 전에 요약의 `채점 답 모양:` 줄과 `result.json` 초안의 `grade_shape` 칸을 먼저 봅니다. 결과를 처음 훑는 탐색 검사도 이 실행이 맡습니다.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6c
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6c-live-check-grader-fix
- tag: plain
- status: open

### H-070 — README 9단계를 S-NEW-1 이 고치기 전에 돌린다면, `cp` 가 오류 없이 끝난 것을 본 뒤에만 `git restore` 를 칩니다. 레인 경로의 `6d` 가 실제 레인 이름인지도 먼저 봅니다.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6c
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6c-live-check-grader-fix
- tag: plain
- status: open

### H-071 — `claude-haiku-5-5` 가 강제 도구로 답하는지 실제 실행에서 확인합니다. 모양 칸이 생긴 초안이 있으면 그 `grade_shape.tool_used` 가 `true` 인지 봅니다.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6c
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6c-live-check-grader-fix
- tag: plain
- status: open

### H-072 — (선택) 동의하지 않는 Claude 채점에만 `human`(`ok`/`bad`)과 `topic_human`(`연애`/`아님`)을 적습니다. 건너뛰어도 판정은 같습니다.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6c
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6c-live-check-grader-fix
- tag: plain
- status: open

### H-073 — 영상 판별 채점 호출 최대 40번이 이제 측정 호출이라는 점을 받아들일지 정합니다. SDK 재시도 뒤에도 하나가 실패하면 실행 전체가 `재지 못함` 이 되어 다시 돌려야 합니다. 받아들이지 않으면 그 호출을 빼는 트래커 변경을 이름 지어 주세요.
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6c
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6c-live-check-grader-fix
- tag: plain
- status: open

### H-074 — Phase 6D 전에, ⓒ 의 "다른 영상 초안과 겹치는 6글자 조각 수 > 0" 을 6D 규칙의 "같은 틀 1쌍 이상" 으로 읽어도 되는지 실제 실행 숫자를 보고 판단합니다. 거의 모든 초안이 0 보다 크면 `6E: 할 일 있음` 이 늘 나옵니다(R5).
- project: marketing-agent-demo
- when: 2026-10-14 · plans/interview-marketing-agent.md#phase-6c
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6c-live-check-grader-fix
- tag: plain
- status: open

### H-075 — S-079–S-082 를 `.adw/smoke-log.md` 에서 S-075–S-078 의 중복(이미 고침: `56bdfd8` · `41de530` · `184bb74` · `7776b1d`)으로 닫기 — `smoke-close` 가 `escalated` 로 둔 뒤, `smoke-triage` 로 단계를 만들지 말 것
- project: marketing-agent-demo
- when: 2026-10-14 · adw/smoke-sweep-s079-s082
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/smoke-sweep-s079-s082
- tag: plain
- status: open

### H-076 — H-018 · H-044(H-066 · H-068 과 함께)를 done 으로 바꿀지 Risks R9 의 근거를 보고 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-077 — H-063 · H-069 를 done 으로 바꾼다 — 실행과 이 레인 커밋(`6626629`)이 끝났고 판정에 `채점 막힘` 이 없음
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-078 — `draft_answer` 의 "OK" · " ok" · "ok." · "ｏｋ" · "good" 과 `topic_answer` 의 "연애 " · "연 애" · "아님." · "아니" 를 정답 없음으로 둘지 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-079 — 기록 하한 고정의 빈틈(0.77–0.80, 그리고 `noul` 을 비워 피하는 길 N2)을 받아들일지 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-080 — 이 보고서 첫 줄 `6E: 할 일 있음 — …` 을 보고 Phase 6E 를 시작한다(6G 와 나란히)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-081 — H-074 의 "같은 틀 1쌍 이상" 을 ⓒ(겹치는 6글자 조각이 있는 초안 10/11, 최다 9)로 읽어도 되는지 6F 보고서 전에 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-082 — 보류 11 중 채점 '연애' 6 을 보고 `noul_yes_min` 을 내릴지 정한다 — 0.75 면 연애 1 이 더, 0.6 이면 연애 2 · 아님 2 가 더 들어와 깨끗하게 가르는 값이 없음
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-083 — `6E:` 줄의 "작성기 답을 JSON 으로 못 읽은 초안 2/11"(2 = 못 읽은 시도, 11 = 읽힌 초안)을 6F 보고서에서 다른 분모로 적을지 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-084 — README 실행 안내(특히 9단계의 복사 경로와 `lane.py status` 문장)를 직접 읽고, 6F 때 헷갈리지 않을지와 6G 착지 전에는 돌리지 않는다는 순서를 확인한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6d
- from: ship-report.md § Human checks — .adw/verify-plan.md § Coverage decisions
- source: adw/phase-6d-live-check-reapply
- tag: plain
- status: open

### H-085 — 6F 실제 실행에서 `claude-sonnet-5-5` 가 강제된 `submit_comment` 도구로 답하고 `tool_result` 다시 쓰기 턴을 받아 주는지 본다(V3 는 SDK 쪽까지만 확인)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-086 — 6F 실제 실행에서 jev 가 새 두 질문(`concern_is_love_worry` · `saju_story_fits`)을 채점기 `task_quality` 와 맞게 답하는지 본다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-087 — `docs/marketing-agent.pdf` 4쪽 ④ · 7쪽과 계약 대조표 열한 문장을 대조한다. 측정으로는 10/11 이 그대로이고, ④-3 만 PDF 의 둥근 따옴표 “…” 가 표에서 홑따옴표 '…' 로 바뀌었으며 가운데가 "…" 로 줄었다(트래커 D-Q1 인용을 따름). 그대로 둘지 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-088 — Phase 6F 초안을 영상끼리 맞대어 읽고 아직 같은 두 문장 골격을 나누는지 본다. `src/agent/writer.py::_frame_pieces` 의 undecided 표본(6D 골격 쌍 `SKELETON_A` / `SKELETON_B`, 지금은 통과로 고정)의 색을 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-089 — Phase 6F 보고서에서 ⓒ(`frame_overlap`)를 그 골격 읽기와 함께 읽는다. ⓒ 하나만으로는 문장 틀 검사가 일하는지 알 수 없다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-090 — Phase 7: 게시 댓글 20개 창(`RECENT_WINDOW`)이 찬 뒤 운영 로그에서 `이전 댓글과 문장 틀이 같습니다` 다시 쓰기와 그 때문에 생긴 SKIP 을 세고, `FRAME_MIN_CHARS`(6)를 그대로 둘지 정한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-091 — Phase 6F: 건너뜀 이유 · 창별 "정당한 건너뜀 n/m" 을 `result.json` 의 `skip_kind` · `skip_grade`(사람 칸 `skip_human` 먼저)로 세어 계약에 기록으로 적는다. 셀 때 두 가지를 감안한다 — `skip_grade` 가 오류로 null 인 영상의 빈 `skip_human` 은 동의가 아니다. 재료 채점은 `<video_title>` 도 장면 출처로 세지만 작성 규칙 3 은 제목 되풀이를 장면으로 치지 않으므로, 제목만 있는 영상은 '부당' 쪽으로 기운다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-092 — Phase 6F: `tests/test_live_check_applied.py` 의 `todo_line` 을 6E 뒤 결과에 다시 쓸지 정한다. 다시 쓴다면 "작성기 답을 JSON 으로 못 읽은 초안"(이제는 도구 답을 못 읽은 초안)과 "이번 결과는 늘 할 일 있음" 문구를 고친다. 5문항 결과를 커밋할 때는 점수 이름 완전성 단언(지금은 3이름 결과에만, :1266)을 5이름으로 옮긴다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/ship-report.md § Quality review
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-093 — `tests/test_task_table.py::table_problems` 의 undecided 표본 넷의 색을 정한다. 넷 모두 지금 통과하고, 답은 트래커 결정이다 — ① 모든 자리가 "—" 인 행의 막지 않음 칸에 닮은 대시(`-` · `–` · `−` · `ー`) ② 자리가 프롬프트 규칙뿐인 행의 막지 않음 칸 "—"(④-1 자막 이유를 지움) ③ jev 칸을 지워 프롬프트 규칙만 남은 행(④-3) ④ 코드 검사 칸의 `len` · `append`(`code_failures` 안의 이름이지만 검사가 아님)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6e
- from: ship-report.md § Human checks — .adw/verify-plan.md § Checks
- source: adw/phase-6e-comment-quality-fix
- tag: plain
- status: open

### H-094 — 트래커 666 의 입력 종류를 "어느 한 시도라도 반복 · 링크 이유에 연락처가 실림"으로 넓혀 고쳐 쓸지, 아니면 `skip_reason` 도 이유 이름과 숫자만으로 고칠지 정하기 — 섞인 탈락(1차 반복 · 2차 JSON)에서 `요상담hp01000001234` 가 남고 끝 줄 "없음" · 종료 코드 0 으로 재현됨. 같은 줄의 "종료 코드 0" 도 "판정대로 0 또는 1" 로
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-095 — `skip_reason` 으로 API 키가 소문자 · 기호 지운 꼴로 나가는 길(키 줄 "키 없음", 종료 코드 3 아님, 6G 전부터 있음)을 대가 줄로 받아들일지 고칠지 정하기
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-096 — 판별 이유 칸(`classification_reason` · `accuracy[].untrusted.reason`)에 jev 의 목록 밖 답이 `repr` 꼴로 남는 길(NBSP 가 `\xa0` 글자가 되어 0곳)을 받아들일지, 이 칸에도 이유 이름만 적을지 정하기
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-097 — 계약 '개인 정보' 줄과 README 4 · 6단계에, 끝 줄 `없음` 이 받아들인 길(662 · 666 · 667)을 덮지 않는다는 단서를 적을지 정하기
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-098 — 레인 역사의 옛 실제 같은 표본(795989b · 5ad1374, 더한 줄 9개)을 착지 전에 가짜로 다시 쓸지, 끝 트리만 바꾼 것을 트래커 줄로 받아들일지 정하기 — `merge --no-ff` 로 main 에 들어가고 제출 때 공개됨
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-099 — 다시 보는 고리의 제곱 비용을 고칠지 정하기(한 번에 찾기, 또는 인기 댓글 길이 상한) — `'+822000ㅡ1234'*833` 9.85초, 영상 하나 최악 84초
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-100 — `tests/live_check.py::_EDGE`/`_JOINED_EDGE` 표본 색 정하기 — 하이픈 · `_DASH` · 가로줄 닮은 글자 뒤에 붙은 계좌: `후원-000-000-123456`, `카카오뱅크-0000-00-1234567-가나다`, `계좌—000-000-123456`, `1ㅡ000ㅡ000ㅡ123456`, `2024.10.15ㅡ000ㅡ000ㅡ123456` (모두 0곳, 끝 줄 "없음")
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-101 — `tests/live_check.py::_match_view` 의 undecided 표본 색 정하기: `010<U+2007>0000<U+2007>1234`, `010ㅡㅡ0000ㅡㅡ1234`, `01<U+200B>0-0000-1234`, `fake.owner@exa<U+200B>mple.com`, `000<U+200B>000<U+200B>123456`, `예금주: 가나<U+200B>다`(첫 판은 통째로 가림, 지금은 `<연락처><U+200B>다`), 계좌 하이픈 옆 NBSP `000-<NBSP>000-<NBSP>123456` · `000<NBSP>-<NBSP>000<NBSP>-<NBSP>123456`, 목록 밖 가로줄 닮은 글자 U+4E00 · U+1173 · U+2F00 · U+FFDA · U+2E3A · U+02D7 · U+2796 · U+23AF · U+2574 · U+2043 (`010X0000X1234` · `000X000X123456` 모두 0곳)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-102 — `tests/live_check.py::CONTACT_SHAPES`(영문자 뒤 전화) undecided 표본 색 정하기: `HP010 0000 1234`, `HP010-00001234`, 숫자 바로 뒤에 붙은 전화 `92024010-0000-1234`
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-103 — `tests/live_check.py::_GAP` undecided 표본 색 정하기: `010--0000--1234`
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-6g
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6g-live-check-redact
- tag: sensitive: tracker decision · confirmed 2026-10-15
- status: confirmed

### H-104 — 다음 진짜 `tests.live_check` 실행에서 Sonnet 5.5 가 `auto` 에서도 `submit_comment` 도구로 답하는지, 되돌려 붙인 생각 블록을 받는지 확인(작성 오류 400 없음 · 초안 > 0 · 글로만 답해 다시 쓰기로 간 횟수)
- project: marketing-agent-demo
- when: 2026-10-15 · adw/smoke-sweep-s093
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/smoke-sweep-s093
- tag: plain
- status: open

### H-105 — 실행 중 대기 동안 고친 설정(명단에서 뺀 영상 · `test_run: true` · 깨진 파일)이 한 주기 늦게 게시에 닿는 것을 받아들일지, 고칠지 정하기 — 그 한 주기 동안 방금 명단에서 뺀 영상에도 실제 게시가 날 수 있고, 지금 바로 멈추는 길은 Ctrl-C 뒤 `--dry-run` 으로 다시 켜기뿐(docs/contracts.md '실행 진입점 — `run.py` (Phase 7)' 절 '고친 설정이 닿는 때'). 명단이 본인 채널뿐이고 채널 대기가 24시간이라 실제로 닿는 경우는 좁음
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-106 — 윈도우에서 `python -m agent.run` 을 두 번 켜, 둘째가 종료 코드 3 과 "이미 실행 중입니다 — …agent.lock …" 으로 끝나는지 보기(msvcrt 잠금 분기는 이 리눅스 스위트가 돌리지 못함)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-107 — `src/agent/config.py::_flag` 의 undecided 표본 색 정하기 — `test_run: no`(지금 거짓으로 읽힘)와 같은 YAML 1.1 낱말 `yes` · `on`(참) · `off` · `NO`(거짓). 트래커 질문 9 A 는 "참 · 거짓만" 이라고만 하고 이 낱말들을 말하지 않음
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-108 — `src/agent/run.py::parse_args` 의 undecided 표본 여섯 색 정하기 — `--dry`(지금 `--dry-run` 으로 읽힘, 안전한 쪽) · `--Dry-Run` · `--dryrun` · `--dry_run` · `—dry-run` · `--test-run`(이 다섯은 사용법 오류로 종료 2)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/verify-plan.md § Checks
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-109 — `src/agent/config.py::_check_keys` 의 undecided 표본 다섯 색 정하기 — `test-run` · `Test_run` · `testrun` · `dry_run` · `ｔｅｓｔ_run`(모두 "알 수 없는 설정입니다" 로 거절 — 첫 읽기면 종료 2, 다시 읽기면 거절이라 게시는 `config_rejected` 테스트 저장)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/verify-plan.md § Checks
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-110 — 실제 호출 실행기(`tests/live_check.py`)와 에이전트가 `data/quota.json` 을 함께 쓰는데 실행기는 `RunLock` 을 쥐지 않음 — 함께 돌면 서로의 예약을 덮어써(벤치 실측 6건 중 5건 잃음) 검색 · 단위 상한을 덜 셈. 받아들일지, 주인 페이즈를 정할지
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-111 — Phase 7G 가 크롬 주소(`chrome_debug_url`)를 이 컴퓨터(루프백)로만 받게 한다(H-061) — 그 전까지는 아무 주소나 받음
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-112 — Phase 7G 가 최소 표본 간격을 정한다(H-009 의 남은 몫 — 재시작 직후 몇 초 사이 두 표본이 큰 속도로 읽히는 일)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-113 — H-023 — 진짜 키로 첫 `--once` 와 녹화의 첫 실제 게시를 본인 허용 목록 테스트 영상에서만 보기(Phase 8A 사람 실행): 이대로 사람 몫으로 받아들일지, 주인을 정할지
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-114 — H-035 — 실제 `YOUTUBE_API_KEY` 로 첫 주기의 `DETECT` · `VIEWS` 줄과 `data/quota.json` 보기(Phase 8A 사람 실행): 이대로 받아들일지, 주인을 정할지
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-115 — H-055 — 첫 실제 게시 때 shorts 영상도 하나 게시해 크롬 `page.url` 꼬리 보기(Phase 8A 사람 실행): 이대로 받아들일지, 주인을 정할지
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-116 — H-090 — 게시 댓글 20개 창이 찬 뒤 운영 로그의 문장 틀 다시 쓰기 보기(실제 게시가 하루 1개라 마감 안에 차지 않음): 이대로 받아들일지, 주인을 정할지
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7-pipeline-rules
- tag: plain
- status: open

### H-117 — Phase 7G: main 의 `tests/test_run.py` `FakeTab` 에 `clear_comment` 를 주고, `--once --dry-run` 주기에서 명단 영상이 `detail` 없는 `POST … result=rehearsed reason=dry_run` 을 남기며 `ERROR where=poster` 줄이 없고 `submits == []` 임을 잠그는 run 단위 테스트를 하나 더한다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7f
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7f-chrome-rehearsal
- tag: plain
- status: open

### H-118 — 착지 뒤 lander 가 합친 트리에서 `python3 -m unittest discover -s tests -t .` 가 `OK` 인지 확인한다(오늘 main `10c2de7` 과 미리 합친 트리는 870개 `OK (skipped=3)`, 건너뜀은 `.git` 없는 임시 폴더 탓)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7f
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7f-chrome-rehearsal
- tag: plain
- status: open

### H-119 — Phase 8A 녹화의 첫 실행(로그인된 진짜 크롬, 테스트 실행)에서 V 의 댓글이 입력되고 게시 버튼이 켜졌지만 눌리지 않는지, `fill("")` 이 YouTube 의 `#contenteditable-root` 를 실제로 비우는지, 로그가 `detail` 없는 `POST … result=rehearsed reason=dry_run` 인지 본다
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7f
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7f-chrome-rehearsal
- tag: plain
- status: open

### H-120 — 착지 뒤 `.adw/human-checks.md` 의 H-026 `status:` 를 고친다(트래커 7F Responsibilities: 마감 축소 인터뷰 질문 9 A 와 이 페이즈가 답함)
- project: marketing-agent-demo
- when: 2026-10-15 · plans/interview-marketing-agent.md#phase-7f
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7f-chrome-rehearsal
- tag: plain
- status: open

### H-121 — 착지 전에 정한다: `d2d8942` 가 커밋한 `docs/live-check/result.json` 의 `videos[].untrusted.description`(영상 6 · 14 · 15 · 18 · 21 · 29)에 채널 주인의 메신저 연락처(카카오톡 아이디 넷 · 텔레그램 링크 · 디스코드 초대 · `@` 아이디)가 있다 — 6G 연락처 모양 밖이라 검사는 0. 공개 저장소 역사에 그대로 둘지, 레인 기록을 가린 글로 다시 쓸지(트래커 6F Q9 의 길)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-6f
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6f-live-check-reapply-after-fix
- tag: sensitive: sensitive area · confirmed 2026-10-16
- status: confirmed

### H-122 — 트래커에서 `claude_answer` 의 색 미정 표본 "grade ok · task_quality None"(과제 채점 오류)의 색을 정한다 — 그 답이 계약 C:1028 '과제 칸 오류 … 통과선은 이 숫자로 움직이지 않습니다' 를 좁힐지도 정한다
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-6f
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6f-live-check-reapply-after-fix
- tag: plain
- status: open

### H-123 — ⓐ 의 전후 차이 가운데 '재료에 연애 고민 없음' 거름이 얼마를 설명하는지는 재지 않았다 — PROCESS.md 가 ⓐ 의 오름을 개선이라 불러도 되는지 사람이 읽고 정한다
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-6f
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-6f-live-check-reapply-after-fix
- tag: plain
- status: open

### H-124 — 제출 공개 전에 커밋 author · committer 메일(레인 17개와 main 역사 전체)을 그대로 공개할지 정한다
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-6f
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-6f-live-check-reapply-after-fix
- tag: plain
- status: open

### H-125 — Phase 8: README 에 한 줄 — 크롬 주소는 이 컴퓨터만 받으므로, 기본(NAT) 네트워크의 WSL 은 `.wslconfig` 에 `networkingMode=mirrored` 를 켜야 `localhost` 가 윈도우 크롬에 닿는다(트래커 Phase 8 1031행 · 8A 1078행이 같은 일을 적음)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7g
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7g-chrome-url-sample-gap
- tag: plain
- status: open

### H-126 — Phase 8A: README 에 한 줄 — 터미널 프록시 설정(`http_proxy` · `all_proxy`)이 있는 컴퓨터는 `no_proxy` 에 `localhost,127.0.0.1,[::1]` 을 넣는다. 없으면 연결 찾기가 이 컴퓨터를 떠나 `chrome_unreachable` 이 되고, 악의적인 프록시면 다른 브라우저에 붙는다(트래커 Phase 8A 1078행)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7g
- from: ship-report.md § Human checks — plans/interview-marketing-agent.md § Phase 7G Decisions (HC1 질문 2 A)
- source: adw/phase-7g-chrome-url-sample-gap
- tag: plain
- status: open

### H-127 — Phase 8A 녹화의 두 실행(`--once --dry-run` 뒤 몇 분 안에 `--once`)에서 `logs/` 를 본다. 둘째 실행의 `TRIGGER` 줄 `per_hour` 가 업로드 0 짝이나 10분 넘게 앞선 기록과의 짝으로 재졌는지 확인한다. 20초 사이 1회가 시간당 180 같은 값이면 7G 가 착지하지 않은 트리로 돈 것이다. 같은 줄의 `VIEWS … delta` 와 숫자가 어긋나는 것은 정상이다(Risks 7). 실제 `agent.run` 프로세스는 바깥 서비스가 필요해 이 사이클에서 돌리지 못했다
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7g
- from: ship-report.md § Human checks — .adw/verify-plan.md § Coverage decisions
- source: adw/phase-7g-chrome-url-sample-gap
- tag: plain
- status: open

### H-128 — 계획의 🚨 좁히기 셋을 받아들일지 고쳐 쓸지 정하기 — (a) 트래커 "연락처 모양 0" 을 "검토한 알려진 목록(103개, `Co-Authored-By` 꼬리의 Anthropic 주소 포함) 밖 0" 으로, (b) "끝 판 `/home/` 경로 0" 을 "홈 폴더 안 경로(끝 판 파일 · 커밋 메시지)" 로 좁히고 메시지 49개는 사본에서 `~/` 로 바꾸되 옛 `.adw/expertise.md` 9판과 트래커 1028줄의 맨 사용자 이름은 남김, (c) 남기는 `.adw/` 기록물의 ADWS 설치 머리글을 공개함 — 계획 관문이 `autonomy: full` 로 자동 승인돼 사람이 본 기록이 없음
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Approach
- source: adw/phase-8-submission-docs
- tag: sensitive: tracker decision · confirmed 2026-10-16
- status: confirmed

### H-129 — 공개용 사본 도구의 남은 위험 셋을 진짜 사본을 뜨기 전에 고칠지, 대가로 받아들일지 정하기 — R1 git 훅처럼 git 환경 변수가 내보내진 셸에서는 원본을 다시 쓰고 걷어내지 않은 사본에 통과를 냄 · R2 `키 모양` · `--print-known` 이 진짜 키를 화면에 통째로 찍음 · R3 알려진 목록 파일 안의 값은 비밀 값 검사도 보지 않음
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-8-submission-docs
- tag: sensitive: tracker decision · confirmed 2026-10-16
- status: confirmed

### H-130 — `tests/public_copy.py::HARNESS_PATHS` 의 undecided 표본 둘의 색을 정하기 — `.claude-notes/a.md`(앞글자만 같은 형제) · `.Claude/settings.json`(대소문자); 답은 트래커 결정
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Test plan
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-131 — `.gitignore` 의 과제 PDF 줄의 undecided 표본 둘의 색을 정하기 — `docs/Marketing-Agent.pdf`(대소문자) · `docs/marketing-agent (1).pdf`(내려받기 중복); 답은 트래커 결정
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Test plan
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-132 — `tests/public_copy.py::check_contacts` 의 undecided 표본 둘의 색을 정하기 — 알려진 목록에 든 가짜 전화번호(🚨 (a)) · `Co-Authored-By` 꼬리의 Anthropic 주소(알려진 목록); 답은 트래커 결정
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Test plan
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-133 — `tests/public_copy.py::KEY_SHAPES` 의 undecided 표본 둘의 색을 정하기 — 대문자 `SK-ANT-` + 30글자 · YAML 쌍점 꼴 `TYPESAFE_API_KEY: ` + 24글자(모양 판정은 못 잡고 비밀 값 검사만 잡음); 답은 트래커 결정
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Test plan
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-134 — `tests/public_copy.py::check_secret_values` 의 undecided 표본 둘의 색을 정하기 — 값의 앞 7글자 · 대소문자를 바꾼 값; 답은 트래커 결정
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Test plan
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-135 — `tests/public_copy.py::HOME_PATH_RE` 의 undecided 표본 셋의 색을 정하기 — 뒤 구분자 없는 맨 홈 이름(트래커 자신의 Phase 8 줄, 🚨 (b)) · `tests/test_chrome.py` 의 가짜 윈도우 홈 경로(알려진 목록) · 옛 blob 에만 있는 홈 경로(🚨 (b), 9판); 답은 트래커 결정
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Test plan
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-136 — `tests/public_copy.py::MSG_FILTER_CODE` 의 undecided 표본 하나의 색을 정하기 — 커밋 메시지 속 홈 경로를 사본에서 `~/` 로 바꿈(🚨 (b), 메시지 49개); 답은 트래커 결정
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Test plan
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-137 — 제출 직전 공개용 사본에서 `git ls-files` 로 계약 8절 밖 이름(`credentials.json` 류 · 스크린샷)이 추적되지 않는지 보기 — 사본의 `무시 규칙 경로` 검사는 `.gitignore` 에 적힌 이름만 봄(H-004 · H-025 를 사람에게 넘김; 받아들이거나 주인을 정하기)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-138 — Phase 8A 가 README 시연 링크 · PROCESS 실제 실행 숫자 · Phase 8 뒤 착지한 페이즈의 README/PROCESS 줄 옮기기를 맡음
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-139 — Phase 8A 가 착지 직전 `python3 -m tests.public_copy --scan-only --branch HEAD --no-env` 를 돌려 이 페이즈 뒤 착지분이 들인 새 연락처 · 키 모양 글을 검토함(검토한 가짜면 `tests/public_copy_known.json` 에 더해 커밋, 아니면 사람에게 멈춤)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-140 — Phase 8A 착지 뒤 홈 체크아웃에서, git 훅이 아닌 평범한 터미널(R1)에서 `python3 -m tests.public_copy --dest <저장소 밖 새 폴더> --env <실제로 키를 쓴 .env — 맥에서 돌렸다면 맥의 것>` 을 돌려 종료 코드 0 · 마지막 줄 `공개용 사본 검사 통과` · `비밀 값 건너뜀` 없음을 확인하고, `✗` 글은 하나씩 본 뒤에만 알려진 목록에 더하기
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-141 — 새 GitHub 저장소를 만들고 사본의 `main` 만 push 하기(이 저장소 · `adw/*` 가지는 올리지 않음), 제출 때 Public 으로(과제 8쪽)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-142 — GitHub 설정 "Block command line pushes that expose my email"(GH007)을 push 전에 확인해 끄거나 트래커 Phase 8 질문 2 를 다시 열기
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-143 — `config.yaml` 의 `allowed_videos` 자리 표시를 본인 테스트 영상 ID 로 바꿔 커밋하기(ID 가 공개됨; README.md:145 의 문장이 이때 참이 됨)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-144 — 맥에서 깨끗한 복제본으로 README 를 따라 하며 `playwright install` 이 필요 없는지와 크롬을 먼저 켠 뒤 약 10분 안에 테스트 모드가 켜지는지 확인하기
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-145 — README '시연 준비' 순서대로 시연을 녹화하기(링크는 Phase 8A 가 채움)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-8
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-8-submission-docs
- tag: plain
- status: open

### H-146 — 늦은 로그 줄의 기준인 "저장소의 마지막 결과"에 판별 · 타이밍 시각도 넣을지 정하기. 지금은 댓글 · 시도가 없는 영상이면 지난 사이클의 `ERROR where=classify` · `SKIP unavailable` 같은 줄이 이유 배지로 계속 남음(1회차 판별 오류 보류, 2회차 `no` 판별 → "댓글 안 씀" + "판별 단계 오류")
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7d
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/phase-7d-run-report-html
- tag: sensitive: tracker decision · confirmed 2026-10-16
- status: confirmed

### H-147 — 색을 정하지 않은 이름표 표본 셋 정하기: `invalid_item`(watcher 의 저장된 영상 SKIP, 이유 배지로 닿음) · `page_mismatch`(test/saved 시도 reason, 결과 배지로 닿음) · `search.list`(`where_label`, `video=` 가 없어 행에 닿지 않음). 지금은 모두 "기타 — 로그 참고"
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7d-run-report-html
- tag: sensitive: tracker decision · confirmed 2026-10-16
- status: confirmed

### H-148 — 테스트 실행에서 저장만 된 영상을 나중에 `allowed_videos` 에 넣으면 다음 테스트 실행에서 리허설할지 정하기. 지금은 저장소 `_is_duplicate(live=False)` 때문에 `SKIP duplicate_video` 가 되고, 화면은 그 영상의 옛 시도("허용 목록 밖이라 게시하지 않음" + 그 시각)를 보임(poster · store 의 동작)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7d-run-report-html
- tag: sensitive: tracker decision · confirmed 2026-10-16
- status: confirmed

### H-149 — 진짜 `python3 -m agent.run --once --dry-run`(명단 영상 하나 · 명단 밖 영상 하나) 뒤 `data/report.html` 을 브라우저로 열어, "리허설 — 게시 버튼 앞에서 멈춤" · "허용 목록 밖이라 게시하지 않음" 과 그 시각이 맞게 읽히는지, 한글과 표 배치가 깨지지 않는지 보기(verify-plan 의 manual 행과 같은 일)
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7d
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7d-run-report-html
- tag: plain
- status: open

### H-150 — 7A 가 main 에 착지한 뒤, 저장소를 공개하기 전에 이 컴퓨터에서 실제 키로 `--once` 한 번 — `search.list` · `videos.list` 가 새 opener 로 200 을 받고 `logs/agent.log` 에 `unknown url type` · SSL 오류가 없으며, 운영자 프록시가 있으면 그대로 먹히는지, 그리고 로그에 키 · 프록시 비밀번호가 없는지 본다
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7a-watcher-network-fixes
- tag: plain
- status: open

### H-151 — `python3 -m unittest tests.test_youtube tests.test_watcher_network` 를 Windows 와 macOS 에서 한 번씩 돌린다 — 소켓 시간 제한과 `Event.wait` 중 Ctrl+C 는 Linux 에서만 쟀다
- project: marketing-agent-demo
- when: 2026-10-16 · plans/interview-marketing-agent.md#phase-7a
- from: ship-report.md § Human checks — .adw/plan.md § Out of scope
- source: adw/phase-7a-watcher-network-fixes
- tag: plain
- status: open

### H-152 — S-114–S-117 이 이번 스윕이 닫는 S-110–S-113 과 같은 일인지(이미 착지한 Phase 7A 브랜치를 base 로 한 중복) 확인하고, 맞으면 `.adw/smoke-log.md` 에서 닫기
- project: marketing-agent-demo
- when: 2026-10-16 · adw/smoke-sweep-s110-s113
- from: ship-report.md § Human checks — .adw/ship-report.md § Risks
- source: adw/smoke-sweep-s110-s113
- tag: plain
- status: open
