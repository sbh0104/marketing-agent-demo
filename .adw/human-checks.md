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
