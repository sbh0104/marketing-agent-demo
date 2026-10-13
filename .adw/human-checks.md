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
