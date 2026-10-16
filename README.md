# 연애 고민 영상 댓글 에이전트

유튜브의 새 연애 고민 영상을 ① 탐지 → ② 판별(jev) → ③ 타이밍 → ④ 작성(Claude) → ⑤ 게시(로그인된 크롬에 쳐 넣기) 다섯 단계로 사람 손 없이 잇는 에이전트입니다. 실제 게시는 `config.yaml` 의 `allowed_videos` 에 적은 영상에만 합니다 — 이 제한은 설정이 아니라 코드가 강제합니다.

저장소 지도 — 에이전트 코드 src/agent/ · 테스트 tests/ · 계약 docs/contracts.md · 제작 기록 plans/ · .adw/ · 제작 노트 PROCESS.md

- 시연 영상: https://www.youtube.com/watch?v=vwogTb6XHGk — 테스트 실행을 찍은 것이고 실제 게시는 없습니다(PROCESS.md '실제 실행' 절).

## 이것만 있으면 됩니다

"코드만 받고 `.env` 만 쓰면 되나요?" 에 대한 답입니다. 테스트 모드는 아래가 전부입니다.

- 이 저장소의 코드
- 파이썬 3.10 이상 (계약 1절)
- `pip install -r requirements.txt`
- `.env` 에 키 세 개 — YouTube · jev · Claude. jev 키는 얼리 액세스 대기 명단으로 받는 키이고, 이 판에서는 꼭 있어야 합니다. 시작 단계(`src/agent/run.py` 의 `connect_real`)가 세 키(`SECRET_NAMES`)를 모두 요구합니다.
- `allowed_videos` 에 실제 영상 ID 가 들어 있으면, 전용 프로필로 켠 크롬 — 테스트 실행도 명단 영상은 크롬에서 게시 버튼 앞까지 리허설합니다.

`data/` 와 `logs/` 는 코드가 만듭니다.

실제 게시에는 두 가지가 더 필요합니다 — `allowed_videos` 에 넣은 본인 테스트 영상, 그리고 그 크롬에서 한 번 해 둔 유튜브 로그인입니다.

## 설치 (맥 먼저)

1. 코드를 받습니다.
   - 맥: `git clone <공개 저장소 주소>` 뒤 `cd` 로 그 폴더에 들어갑니다.
   - 윈도우(PowerShell): 같은 명령입니다.
2. (선택) 가상 환경을 만듭니다.
   - 맥: `python3 -m venv .venv` 뒤 `source .venv/bin/activate`
   - 윈도우(PowerShell): `py -m venv .venv` 뒤 `.venv\Scripts\Activate.ps1`
3. 라이브러리를 설치합니다: `pip install -r requirements.txt` (맥 · 윈도우 같음).
   - 네 줄입니다 — `PyYAML`(설정 읽기) · `playwright`(크롬 연결) · `anthropic`(Claude SDK) · `typesafe-sdk`(jev SDK).
   - `playwright install` 은 하지 않아도 됩니다. 에이전트는 이미 설치된 크롬에 `connect_over_cdp` 로 붙습니다(계약 1절).
4. 키 파일을 만듭니다.
   - 맥: `cp .env.example .env`
   - 윈도우(PowerShell): `Copy-Item .env.example .env`
   - `.env` 의 `YOUTUBE_API_KEY` · `TYPESAFE_API_KEY` · `ANTHROPIC_API_KEY` 를 채웁니다(아래 'API 키 발급').

첫 실행은 크롬을 켠 뒤에 합니다 — '크롬 원격 제어' 를 마치고 '테스트 모드' 로 갑니다.

## API 키 발급

### YouTube Data API v3 — `YOUTUBE_API_KEY`

Google Cloud 콘솔(`https://console.cloud.google.com/`)에서 프로젝트를 고르고 → "YouTube Data API v3" 를 사용 설정한 뒤 → 사용자 인증 정보에서 API 키를 만듭니다.

### TypeSafe jev — `TYPESAFE_API_KEY`

얼리 액세스 콘솔 `https://console.typesafe.ai/` 에서 받습니다(`.env.example` 에 적힌 주소). 대기 명단에 올라 받는 키입니다.

- 키가 비어 있으면 시작 단계가 `에이전트를 시작할 수 없습니다 — EnvError: TYPESAFE_API_KEY 가 비어 있습니다 …` 를 내고 종료 코드 2 로 멈춥니다(2026-10-15 main `5d80cbc` 에서 잰 값).
- 이 판에서는 jev 키 없이 테스트 모드도 시작하지 않습니다. 키 없이 볼 수 있는 것은 '테스트 모드' 끝의 테스트 묶음입니다.

### Anthropic Claude — `ANTHROPIC_API_KEY`

`https://console.anthropic.com/` → API Keys 에서 만듭니다. 댓글을 쓰는 모델은 `config.yaml` 의 `comment.writer_model` 입니다.

## 크롬 원격 제어 (맥 · 윈도우)

에이전트는 크롬을 직접 켜지 않고, 전용 프로필로 켠 크롬에 디버깅 포트로 붙습니다(계약 8절).

1. 켤 명령을 받습니다. 저장소 뿌리에서:
   - 맥: `PYTHONPATH=src python3 -m agent.chrome --profile chrome-profile`
   - 윈도우(PowerShell): `$env:PYTHONPATH = "src"` 뒤 `python -m agent.chrome --profile chrome-profile`

   이 명령은 프로필 폴더를 검사하고 켤 명령을 보여 줄 뿐, 크롬을 켜지 않습니다. 크롬의 기본 데이터 폴더와, 저장소 안이면서 `chrome-profile/` 밖인 폴더는 거부합니다(종료 코드 2).
2. 보여 준 명령은 이런 모양입니다(`<…>` 는 이 컴퓨터의 값).
   - 맥:

     ```
     '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --remote-debugging-port=9222 --user-data-dir=<저장소 폴더>/chrome-profile --no-first-run --no-default-browser-check
     ```

   - 윈도우:

     ```
     "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=<저장소 폴더>\chrome-profile --no-first-run --no-default-browser-check
     ```

   포트 `9222` 는 `config.yaml` 의 `chrome_debug_url: http://localhost:9222` 에서 옵니다.
3. 보여 준 명령을 붙여 넣어 크롬을 켜고, 그 창에서 전용(브랜드) 유튜브 계정으로 한 번 로그인합니다.

- **디버깅 포트의 위험.** 포트가 열려 있는 동안 이 컴퓨터의 어떤 프로그램이든 그 크롬의 쿠키를 읽을 수 있습니다. 본 구글 계정이 아닌 전용 계정으로만 로그인하고, 에이전트를 쓰지 않을 때는 그 크롬을 닫습니다.
- Chrome 136 이상은 기본 데이터 폴더에서 이 포트를 무시합니다. 그렇게 켠 크롬에는 붙지 못해 게시가 `chrome_unreachable` 로 멈춥니다.
- **크롬 주소는 이 컴퓨터만.** `chrome_debug_url` 은 `localhost` · `127.0.0.1` · `[::1]` 과 포트만 받습니다. 그 밖의 주소는 설정 오류라 시작하지 않습니다(계약 2절).
- **WSL 에서 윈도우 크롬에 붙을 때.** 기본(NAT) 네트워크의 WSL 은 `.wslconfig` 에 `networkingMode=mirrored` 를 켜야 `localhost` 가 윈도우 크롬에 닿습니다.
- **터미널 프록시 설정이 있는 컴퓨터.** `http_proxy` · `all_proxy` 가 설정돼 있으면 `no_proxy` 에 `localhost,127.0.0.1,[::1]` 을 넣습니다. 없으면 크롬이 켜져 있어도 연결 찾기가 프록시로 가 `chrome_unreachable` 이 되고, 악의적인 프록시면 다른 브라우저에 붙습니다.

## 테스트 모드

첫 실행은 여기서, 위 '크롬 원격 제어' 뒤에 합니다. 저장소 뿌리에서:

- 맥: `PYTHONPATH=src python3 -m agent.run --once --dry-run`
- 윈도우(PowerShell): `$env:PYTHONPATH = "src"` 뒤 `python -m agent.run --once --dry-run`

- **스위치 둘, 뜻 하나.** `--dry-run` 과 `config.yaml` 의 `test_run: true` 는 같은 뜻입니다 — 둘 중 하나면 테스트 실행이고, 설정으로 `--dry-run` 을 끌 수는 없습니다(`config.yaml` 의 주석).
- **명단 영상은 테스트 실행에서도 크롬으로 갑니다.** 댓글 칸에 입력하고 게시 버튼이 켜졌는지까지 본 뒤, 누르지 않고 멈춥니다(리허설).
- **크롬이 켜져 있지 않으면** 명단 영상마다 `ERROR where=poster reason=chrome_unreachable … stage=before_click video=<ID>` 한 줄이 남고, 그 영상의 결과는 `stopped` 입니다.
- **다른 영상은** 크롬을 열지 않고 저장만 합니다.
- **결과 화면.** 주기가 끝날 때마다(`CYCLE` 줄 뒤) `data/report.html` 한 장을 다시 씁니다 — 영상마다 판별 · 타이밍 · 고민 한 줄 · 댓글 · 게시 결과 배지가 한 화면에 보입니다. 서버 없는 파일이라 브라우저로 엽니다: 맥 `open data/report.html` · 윈도우(PowerShell) `Invoke-Item data\report.html`. 주기가 끝난 뒤 새로고침하면 바뀝니다(계약 '결과 화면' 절).

### 결과 예시 — 모양 예시

아래는 계약에 적힌 예시 줄이고 실제 실행의 기록이 아닙니다. 로그는 `logs/agent.log` 에 쌓입니다. 실제 실행의 기록은 `logs/sample.log` 입니다 — 녹화 날 같은 폴더에서 돌린 사전 점검과 녹화한 테스트 실행의 로그 전체이고, 숫자는 PROCESS.md '실제 실행' 절에 있습니다.

탐지 · 조회수 (계약 '탐지 · 조회수 추적' 절의 로그 예시):

```
2026-10-12T21:00:00+09:00 DETECT video=abcdefghijk channel=UC123 keyword=썸 title="연락 텀 때문에 불안한 썸"
2026-10-12T21:00:00+09:00 VIEWS video=abcdefghijk views=1200 prev=- delta=-
2026-10-12T23:00:00+09:00 VIEWS video=abcdefghijk views=1450 prev=1200 delta=250
```

판별 · 타이밍 · 작성 (계약 7절의 예시 줄):

```
2026-10-12T21:30:00+09:00 CLASSIFY video=abcdefghijk verdict=yes reason="연애 고민 상담"
2026-10-12T21:30:00+09:00 TRIGGER video=abcdefghijk verdict=yes reason=views_per_hour per_hour=181.25
2026-10-12T21:30:00+09:00 COMMENT video=abcdefghijk concern="연락 빈도" text="연락 텀이 길어지면 마음이 먼저 앞서죠.\n천천히 물어보세요."
```

게시 — 명단 밖 영상의 테스트 저장(계약 7절 "`POST` 의 나머지 모양")과 명단 영상의 리허설(계약 '게시 단계 구현' 의 리허설 줄):

```
2026-10-12T21:30:00+09:00 POST video=zyxwvutsrqp mode=test result=saved reason=not_in_allowlist
POST … mode=test result=rehearsed reason=dry_run screenshot=… page_url=…
```

### 테스트 실행에서 보이는 이유

- `invalid_video` — 영상 주소를 읽을 수 없어 게시하지 않고 테스트 저장합니다.
- `not_in_allowlist` — 허용 목록 밖 영상이라 크롬을 열지 않고 테스트 저장합니다.
- `dry_run` — 테스트 실행의 명단 영상입니다. 저장 대신 크롬에서 게시 버튼 앞까지 리허설합니다(`result=rehearsed`).
- `allowlisted` — 명단 영상입니다. 타이밍 줄(`TRIGGER … reason=allowlisted`)에 보이고, 테스트 실행이 아니면 실제 게시의 이유입니다.
- `page_mismatch` — 크롬이 다른 영상에 있어 게시하지 않고 테스트 저장(리허설이면 저장 없이 멈춤)

`allowed_videos` 항목은 맨 영상 ID 나, 공유 버튼이 주는 주소를 그대로 적습니다(쿼리는 `?si=` · `?t=` · `?feature=` 만 받습니다). 재생목록에서 복사한 `?list=…` 처럼 그 밖의 꼬리가 붙으면 그 영상은 오류 없이 테스트 모드로만 돕니다.

### 키 없이 보는 길 — 테스트 묶음

```
python3 -X warn_default_encoding -W error::EncodingWarning -m unittest discover -s tests -t .
```

계약 1절의 명령입니다. 가짜 AI 로 돌아 키가 필요 없고, 마지막 줄이 `OK` 이면 통과입니다. 진짜 AI 가 도는 테스트 모드를 대신하지는 않습니다.

## 실제 게시 전에

- **커밋된 명단.** 제출본의 `allowed_videos` 는 자리 표시(`https://youtu.be/내-테스트-영상-ID`)라, 그대로 돌리면 어떤 영상에도 실제 게시하지 않습니다. 실제 게시를 보려면 제 테스트 영상 ID 를 넣으세요. 시연에 쓴 영상은 `logs/sample.log` 에 보입니다 — 본인 테스트 영상이 아니라 남의 채널 다섯의 인기 영상이고, 테스트 실행이라 게시하지 않았습니다.
- **명단 영상은 타이밍 규칙을 면제받습니다.** 키워드 검색과 타이밍 조건(조회수 1,000–5,000 · 시간당 150)은 새로 올린 본인 영상을 통과시키지 않아, 면제가 없으면 테스트 영상이 게시 단계에 닿지 못합니다. 판별 · 작성 · 게시 가드는 다른 영상과 같고, 실제 영상의 타이밍 기준은 그대로입니다.
- **테스트 영상의 설명란.** 연애 고민과 구체적인 장면이나 말을 설명란에 적어 두세요. 없으면 작성기가 지어내지 않고 그 영상을 건너뜁니다(`재료에 연애 고민 없음` · `재료에 장면 없음`).
- **`data/` 를 지우지 마세요.** 지우면 중복 게시를 막는 기록이 사라져, 같은 영상에 두 번째 댓글이 실제로 달릴 수 있습니다.

## 시연 준비 (녹화 순서)

제출한 시연 영상(맨 위 링크)은 이 순서의 3단계까지만 찍었습니다 — 1단계 사전 점검(명단을 비운 `--dry-run`) 뒤 3단계 테스트 실행을 찍었고, 명단에는 본인 테스트 영상 V 대신 남의 채널 다섯의 인기 영상을 넣어 크롬이 게시 버튼 앞에서 멈춘 데까지만 보입니다. 4단계(실제 게시)는 하지 않아 실제 게시는 없습니다(PROCESS.md '실제 실행' 절). 아래는 본인 테스트 영상 V 로 4단계까지 찍는 순서입니다.

1. 녹화 전에는 테스트 영상 V 를 `allowed_videos` 에 넣은 채 아무 실행도 돌리지 않습니다. 키 · 탐지 확인은 V 를 뺀 채 `--dry-run` 으로 합니다.
2. 외부 도구로 녹화를 켭니다.
3. `PYTHONPATH=src python3 -m agent.run --once --dry-run` — V 가 판별 · 작성을 거치고, 크롬이 게시 버튼 앞에서 멈춥니다.
4. `PYTHONPATH=src python3 -m agent.run --once` — V 에 같은 댓글이 실제로 게시됩니다.
5. 녹화를 3분 안팎으로 편집합니다.

- `--dry-run` 깃발을 쓰므로 두 실행 사이에 설정을 고치는 장면이 없습니다.
- 크롬이 첫 실행에서 실패해도 그 녹화본을 버리지 마세요 — 다시 찍어도 V 의 작성 장면은 돌아오지 않습니다.
- 게시 뒤 다음 명단 영상은 `channel_cooldown` 으로 건너뛰고, 로그에 그 줄이 남습니다. 명단 영상은 모두 본인 채널이라 실제 게시는 하루 1개입니다.

## 문제 해결

- **설정이 이모지 때문에 거절됩니다.** 글자 규칙은 실행 중인 파이썬의 유니코드 표를 따릅니다. 3.10 은 🥹 · 🫠 · 🫶 을, 3.12 · 3.13 은 🫩 을 모르는 글자로 보고 설정을 거절합니다. 그 이모지를 빼거나 더 새 파이썬을 씁니다.
- **ZWJ 이모지.** 주제 · 검색어에 ZWJ 로 이은 이모지(👩‍💻, 커플 이모지 등)를 넣으면 설정이 거절됩니다 — 이모지 선택기가 흔히 만드는 꼴입니다.
- **`chrome_unreachable`.** 크롬이 켜져 있지 않거나, 포트가 닫혔거나, 크롬을 기본 데이터 폴더로 켰거나, 터미널 프록시 설정이 연결 찾기를 이 컴퓨터 밖으로 보냈습니다('크롬 원격 제어' 의 프록시 줄).
- **`에이전트를 시작할 수 없습니다` 와 종료 코드 2.** SDK 나 키가 없거나, 쿼터 장부(`data/quota.json`)를 믿을 수 없습니다(계약 '실행 진입점' 절).
- **`ERROR where=config` 와 종료 코드 2.** `config.yaml` 에 오류가 있으면 위 문구 없이 `ERROR where=config` 한 줄만 남기고 종료 코드 2 로 끝납니다(계약 '실행 진입점' 절).
