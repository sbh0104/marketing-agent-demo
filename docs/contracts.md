# 계약 — Phase 1 뼈대

Phase 2–7 의 모든 단계가 기대는 계약입니다. 설정 읽기, 영상 기록 모양, 저장소 규칙,
허용 목록 가드, 게시 흐름, 로그 형식, 주기 실행을 여기서 정합니다. 코드는
`src/agent/` 패키지에 있고, 모듈을 다루는 절은 제목이 그 모듈을 적습니다.

## 1. 실행

- Python 3.10 이상. 3.11 이후에만 있는 기능(`datetime.UTC`, `enum.StrEnum`, `tomllib`,
  `typing.Self`, `except*`)은 쓰지 않습니다.
- 의존성 설치: `pip install -r requirements.txt` — `PyYAML>=6.0`(설정 읽기), jev 판별(Phase 3)의
  `typesafe-sdk>=0.7.4,<0.8`, 댓글 작성기(Phase 5, '댓글 작성' 절)의 Claude SDK `anthropic>=0.40`,
  게시 단계(Phase 6)의 `playwright>=1.40` 네 줄입니다. 게시 단계는 이미 설치된 크롬에 `connect_over_cdp` 로 붙으므로
  `playwright install`(브라우저 내려받기)은 필요 없습니다. 테스트는 SDK 와 Playwright 없이 돕니다 —
  판별 테스트는 가짜 jev 를, 작성기 테스트는 가짜 클라이언트를 씁니다. `agent.chrome` 이 크롬에
  연결할 때에만 Playwright 를 불러옵니다.
- 테스트(저장소 뿌리에서, 설치 없이):

  ```
  python3 -X warn_default_encoding -W error::EncodingWarning -m unittest discover -s tests -t .
  ```

  `tests/__init__.py` 가 `src/` 를 `sys.path` 맨 앞에 넣으므로 패키지를 설치하지 않아도
  됩니다. `-W error::EncodingWarning` 때문에 `encoding=` 없이 파일을 여는 코드는 리눅스에서도
  실패합니다 — 윈도우 인코딩 사고를 미리 막는 장치입니다.
- 실행 진입점은 저장소 뿌리에서 `PYTHONPATH=src python3 -m agent.run [--dry-run] [--once]` 입니다(윈도우
  PowerShell 은 먼저 `$env:PYTHONPATH = "src"`). `--dry-run` 이나 설정 `test_run: true` 가 테스트 실행을 켜고,
  테스트 실행은 `decide_post(..., dry_run=True)` 로 넘어갑니다(5절) — '실행 진입점 — run.py' 절.

## 2. 설정 — `config.yaml`

`load_config(path)` 가 읽고 `config_from_mapping` 이 검사합니다. **모든 키가 필요하고,
모르는 키는 오류이며, 타입은 정확해야 합니다.** 오류는 `ConfigError` 로, 메시지가 점으로 이은
키 경로(`limits.daily_max_searches`)나 줄 번호(`3번째 줄: …`)를 말합니다.

| 키 | 타입 | 규칙 | 과제 기본값 |
|---|---|---|---|
| `topic` | 글자 | 비어 있지 않고, 스페이스로 시작하거나 끝나지 않음, 글자 규칙(아래), 500자 이하 — 판별 질문에 세 번 들어가므로 한 글자 4바이트로 채워도 영상 글 몫이 22000 바이트 이상 남는 길이('주제 판별' 절) | `연애` |
| `keywords` | 글자 목록 | 1개 이상, 각 항목 비어 있지 않고, 스페이스로 시작하거나 끝나지 않음, 글자 규칙(아래) | `[연애, 썸, 연애 상담, 이별, 소개팅]` |
| `poll_interval_min` | 정수 | ≥ 1, ≤ 52560000 | `120` (과제 예시 `30` — 아래) |
| `trigger.min_views` | 정수 | ≥ 0, ≤ 1000000000000 | `1000` |
| `trigger.max_views` | 정수 | ≥ `min_views`, ≤ 1000000000000 | `5000` |
| `trigger.max_age_hours` | 숫자 | > 0, ≤ 876000 | `12` |
| `trigger.min_views_per_hour` | 숫자 | ≥ 0, ≤ 1000000000 | `150` |
| `limits.daily_max_comments` | 정수 | ≥ 0, ≤ 86400 | `10` |
| `limits.channel_cooldown_hours` | 숫자 | ≥ 0, ≤ 876000 | `24` |
| `limits.daily_max_searches` | 정수 | ≥ 0, ≤ 86400 | `90` (과제 밖에서 더한 키) |
| `comment.min_chars` | 정수 | ≥ 1, ≤ 10000 | `40` |
| `comment.max_chars` | 정수 | ≥ `min_chars`, ≤ 10000 | `120` |
| `comment.writer_model` | 글자 | 비어 있지 않고, 스페이스로 시작하거나 끝나지 않음, 글자 규칙(아래) — 댓글을 쓰는 Claude 모델 이름 ('댓글 작성' 절) | `claude-sonnet-5-5` |
| `comment.check_min_probability` | 숫자 | ≥ 0, ≤ 1 — jev 자체 검사 통과 하한 ('댓글 작성' 절) | `0.7` |
| `classifier.model` | 글자 | 비어 있지 않고, 스페이스로 시작하거나 끝나지 않음, 글자 규칙(아래) — jev 모델 이름 | `jev-latest` |
| `classifier.noul_yes_min` | 숫자 | > 0.5, ≤ 1 — 주제 일치 확률이 이 값 이상이어야 일치 | `0.8` |
| `classifier.noul_no_max` | 숫자 | ≥ 0, < `noul_yes_min` — 이 값 이하여야 불일치, 사이는 보류 | `0.2` |
| `classifier.choice_min_confidence` | 숫자 | ≥ 0, ≤ 1 — 이유 보기 확신이 이보다 낮으면 보류 | `0.5` |
| `classifier.on_topic_reasons` | 글자 목록 | 1개 이상, 각 1–40자이고 스페이스로 시작하거나 끝나지 않음, 글자 규칙(아래), 두 목록 합쳐 50개 이하, 이름 겹침 금지 | 4개 (config.yaml) |
| `classifier.off_topic_reasons` | 글자 목록 | 같은 규칙 — jev 에 먼저 보임 | 4개 (config.yaml) |
| `chrome_debug_url` | 글자 | 비어 있지 않고, 스페이스로 시작하거나 끝나지 않음, 글자 규칙(아래), 그다음 주소 글의 꼴 — 글 전체가 `http://` + `localhost` · `127.0.0.1` · `[::1]` 중 하나 + `:` 포트(숫자 1–5자리) + 끝의 `/` 하나까지. 그 밖의 꼴(사용자 이름 · `\` · 다른 호스트 이름 등)은 `이 컴퓨터 주소만 받습니다 (localhost · 127.0.0.1 · [::1] 와 포트): chrome_debug_url` 오류이고, 메시지는 이 글 그대로입니다 (Phase 7G) | `http://localhost:9222` |
| `allowed_videos` | 글자 목록 | 비워 두면 `()`; 항목은 쓴 그대로 보관 (글자 규칙 밖) | `- https://youtu.be/내-테스트-영상-ID` |
| `test_run` | 참 · 거짓 | `true` · `false` | `false` |

- "정수"는 bool 을 받지 않습니다. "숫자"는 정수나 실수(bool 제외)이고 실수로 저장되며,
  유한값만 받습니다 — `.inf` · `-.inf` · `.nan` 은 `유한한 숫자여야 합니다: <키>` 오류입니다.
- 숫자 키의 상한은 읽기를 통과한 값이 뒤 단계에서 넘치지 않게 둡니다. 시간 키의 876000 은
  100 × 365 × 24 시간(약 100년, 9절의 대기 상한과 같은 크기)이라 `now − timedelta(hours=…)`
  (`check_post` 의 채널 대기, Phase 4 의 나이 창)가 날짜 범위 안에 있습니다 — 2026년 기준 약
  1800만 시간부터 `OverflowError` 입니다. `trigger.min_views_per_hour` 의 1000000000 은 실제
  영상이 닿지 않는 값입니다. 넘으면 `<상한> 이하여야 합니다: <키>` 오류이고, 실행 중이면 이전
  설정을 유지합니다.
- 정수 키도 모두 상한이 있습니다 — 정수는 비교와 셈 말고도 글자로 쓰입니다: `START interval_min=` ·
  `QUOTA limit=` 로그 줄(7절), 댓글 작성 지시문과 코드 검사의 글자 수 문구('댓글 작성' 절). YAML 의
  16진수 · 60진수 표기(`0x…`, `1:30`)는 파이썬의 4,300자리 한도와 상관없이 정수로 읽혀서, 상한이
  없으면 `0x` 뒤에 `F` 3,700개를 쓴 값이 읽기를 통과한 뒤 글자로 바꾸는 자리에서 `ValueError` 를
  냅니다. 상한은 `_int` 의 필수 인자라 정수 키를 더하는 단계가 빠뜨릴 수 없습니다. 넘으면
  `<상한> 이하여야 합니다: <키>` 오류(값은 메시지에 쓰지 않음)이고, 실행 중이면 이전 설정을
  유지합니다. 키마다 근거:
  - `poll_interval_min` 52560000 — 100 × 365 × 24 × 60 분(약 100년), 9절의 대기 상한과 같은 크기.
  - `trigger.min_views` · `trigger.max_views` 1000000000000 — 지구 인구의 100배가 넘는 값, 어떤
    영상의 조회수보다도 큼.
  - `limits.daily_max_comments` · `limits.daily_max_searches` 86400 — 하루의 초 수. 게시는 한 번이
    1초보다 오래 걸려 이 수에 닿을 수 없고, 검색은 그보다 훨씬 앞서 쿼터 장부가 막습니다(아래).
  - `comment.min_chars` · `comment.max_chars` 10000 — 유튜브 댓글 한 개의 최대 길이.
- `limits.daily_max_searches` 는 과제 예시에 없는 키로, 최근 24시간(굴러가는 창) 안의
  `search.list` 호출 수 — 페이지 넘김 한 번도 한 번 — 의 상한입니다. 닿으면 호출하지 않고
  `QUOTA` 를 남깁니다('탐지 · 조회수 추적' 절). Google 은 2026-10-08 부터 `search.list` 를
  하루 100회짜리 별도 통으로 셉니다(https://developers.google.com/youtube/v3/determine_quota_cost,
  "Last updated 2026-10-08 UTC"). 이 장부는 일부러 더 엄격하게 검색 1회를 하루 10,000 단위 통에서
  100 단위씩 깎습니다 — 옛 규칙과 새 규칙 어느 쪽에서도 넘치지 않습니다. 그래서 기본 90 은
  90 × 100 = 9,000 단위이고, 1,000 단위 이상을 조회수 호출(`videos.list`, 1단위)에 남깁니다. 90 을
  넘기면 한 회마다 조회수 몫이 100 단위씩 줄고, 100 이면 남지 않아 조회수 호출이
  `QUOTA … counter=units` 로 막힙니다 — 95–100 으로 올려 조회수 몫이 줄거나 막히는 것은 Google 이
  아니라 이 장부 때문입니다(장부를 두 통으로 나누는 것은 따로 정할 일입니다). 0 이면 검색하지
  않습니다.
- `poll_interval_min` 기본값 120 과 키워드 5개는 하루 검색 60회입니다(트래커 Phase 2 후보 b).
  과제 예시 30분 × 5개 = 240회/일은 쿼터를 넘어 쓰지 않습니다. 30분으로 돌리려면 키워드를
  2개로 줄이고(96회/일) `daily_max_searches` 를 96 이상으로 올려야 합니다 — 그러면 조회수 몫이
  400 단위 이하로 줄고 페이지 넘김 여유는 거의 없습니다.
- `trigger.max_age_hours` 는 Phase 2 에서 검색 기간(`publishedAfter`)과 조회수 추적 기간도
  정합니다('탐지 · 조회수 추적' 절).
- `comment.writer_model` · `comment.check_min_probability` 는 과제 예시에 없는 키로, Phase 5 가
  댓글 작성 · 자체 검사를 위해 더했습니다('댓글 작성' 절). `check_min_probability` 의 상한 1 은 확률의
  끝입니다.
- **YAML 1.1 함정 — 글자 자리에서는 크게 실패합니다.** 따옴표 없는 `yes`/`no`/`on`/`off` 는
  bool, `2026-10-12` 는 날짜, `12345678901` 은 정수로 읽히므로 글자 자리에 오면 오류입니다
  (예: `keywords: [연애, no]`, `topic: yes`, `allowed_videos: [12345678901]`). 이런 값은
  따옴표로 감싸세요.
- **숫자 자리에서는 YAML 1.1 숫자 표기가 그대로 읽힙니다** — `017` 은 8진수 15, `1:30` 은
  60진수 90, `0x1F` 는 31, `1_000` 은 1000 이 되고 위 범위 검사만 받습니다. 숫자는 앞자리 0 ·
  `:` · `_` 없이 10진수로 쓰세요.
- 보기 이름에 `: ` 가 들어가면 따옴표로 감싸세요 — 따옴표 없는 `- 키워드만 겹침: 게임` 은
  YAML 이 '키: 값' 묶음으로 읽어
  `비어 있지 않은 글자여야 합니다: classifier.off_topic_reasons[0]` 오류입니다.
- **글자 규칙.** 글자 키 — `topic` · `keywords` 각 항목 · `comment.writer_model` ·
  `classifier.model` · 판별 보기 이름 · `chrome_debug_url` — 는 유니코드 범주 L(글자) · M(결합 표시) ·
  N(숫자) · P(문장부호) · S(기호)의 글자와 보통 스페이스(U+0020)로 씁니다 — 7절 로그의 날 글자와 같은 목록입니다.
  그 밖의 글자 — 줄바꿈 · 탭 같은 제어 글자, 폭 없는 공백(U+200B) 같은 서식 글자, U+0020 밖의 공백
  (U+00A0 · 전각 공백 U+3000), 줄 · 문단 구분, 사용자 정의 · 미할당 글자, 짝 없는 서로게이트(`"\ud800"`) — 가
  하나라도 들면 `글자 · 숫자 · 문장부호 · 기호와 보통 스페이스만 쓸 수 있습니다 (…): <키>` 오류입니다.
  범주는 실행 중인 파이썬의 `unicodedata` 판정을 따르므로, 그 판이 모르는 글자(Cn)는 다른 판에서 읽히던 값이라도
  이 오류입니다 — 예: U+1FAE9 는 파이썬 3.14(유니코드 16.0)에서 S 이고 3.12(유니코드 15.0)에서 Cn 입니다.
  범주 L · M · S 안에도 빈칸으로 그려지는 글자(한글 채움 문자 U+3164, 점자 빈칸 U+2800, 변형 선택자 U+FE0F 등)가
  있어, 이런 글자는 이 규칙을 지납니다.
  스페이스로 시작하거나 끝나는 값(`"   "` 포함)은 `스페이스로 시작하거나 끝나면 안 됩니다: <키>` 오류입니다.
  가운데 스페이스는 연속이어도 받고, 앞뒤 스페이스를 잘라 쓰지 않고 오류로 알립니다.
  두 오류 모두 메시지에 값을 쓰지 않으며, 실행 중이면 이전 설정을 유지합니다.
  YAML 은 따옴표 없는 값의 앞뒤 공백을 스스로 떼므로, 스페이스 규칙은 따옴표 안의 값에서 걸립니다.
  `allowed_videos` 항목은 이 규칙을 받지 않고 쓴 그대로 보관합니다 — 항목은 가드가 읽습니다.
- `test_run` 은 참 · 거짓 값만 받습니다 — `"false"` · `0` · 빈 값은
  `참 · 거짓(true 또는 false)이어야 합니다: test_run` 오류입니다. 참이면 테스트 실행입니다.
  거짓이어도 `--dry-run` 을 끄지 않습니다 — 둘 중 하나면 테스트 실행입니다('실행 진입점 — run.py' 절).
- 같은 키가 두 번 나오면 두 번째 줄 번호와 함께 오류입니다. 윈도우 메모장이 붙이는 BOM 은
  떼어 내고 읽습니다. UTF-8 이 아닌 저장(메모장의 ANSI·Unicode)은 `ConfigError` 입니다.
- 읽는 중 나는 그 밖의 모든 오류도 `ConfigError` 입니다 — 날짜 모양의 틀린 값
  (`topic: 2026-02-30`), 4300자를 넘는 정수, 실수로 바꿀 수 없는 큰 정수
  (`max_age_hours: 1000…0`), 아주 깊은 중첩. 메시지는
  `설정 값을 읽을 수 없습니다 (<원인 종류>: <원인>): <경로>` 이고 원인은 `__cause__` 에
  남습니다. `KeyboardInterrupt` 는 바꾸지 않고 그대로 올라갑니다.
- 주기 루프는 사이클마다 `config.yaml` 을 다시 읽습니다(9절). 실행 중에 값을 고치면 다음
  대기부터 적용됩니다. 잘못 고친 파일은 이전 설정을 유지하되, 다시 읽기가 받을 때까지 진입점이 실제 게시를
  하지 않습니다 — 그동안 게시는 명단 영상까지 모두 크롬 없이 테스트 저장(명단 영상은 `reason=config_rejected`, 명단 밖 영상은 가드의 이유)이고,
  거절마다 `ERROR where=config` 한 줄이 남습니다('실행 진입점 — run.py' 절).

## 3. 영상 기록 — `models.py`

영상 한 개를 탐지부터 게시 시도까지 담는 `VideoRecord`:

| 필드 | 타입 | 설명 |
|---|---|---|
| `video_id` | 글자 | 11자 영상 ID (`[A-Za-z0-9_-]{11}`, `VIDEO_ID_RE`) |
| `channel_id` | 글자 | 비어 있지 않음 — 채널 대기 계산의 기준 |
| `title` · `description` · `keyword` | 글자 | 탐지 때 본 값, `keyword` 는 찾은 검색어 |
| `published_at` · `detected_at` | 시각 | 시간대가 있어야 함 |
| `view_history` | `ViewSample(at, count)` 목록 | 조회수 기록, `count` 는 0 이상 정수 |
| `classification` | `Judgement` 또는 없음 | 주제 판별 (Phase 3) |
| `trigger` | `Judgement` 또는 없음 | 트리거 판정 (Phase 4) |
| `comment` | `CommentDraft(concern, text, at, self_check)` 또는 없음 | 작성한 댓글 (Phase 5) |
| `attempts` | `PostAttempt(at, mode, result, reason, screenshot)` 목록 | 게시 시도 — 저장소만 바꿈 |

- `Judgement(verdict, reason, at)` 의 `verdict` 는 `Verdict` 값 `yes` · `no` · `hold`.
- **게시 시도 결과 상태:**

  | mode | result | 뜻 |
  |---|---|---|
  | `live` | `reserved` | 클릭 *전에* 남긴 예약. 결과를 모름 — 게시로 셉니다 |
  | `live` | `posted` | 게시 성공 확인 |
  | `live` | `failed` | 게시 실패 — `reason` 에 원인, `screenshot` 에 캡처 경로 |
  | `test` | `saved` | 테스트 모드 저장 — `reason` 에 `PostDecision.reason`, 6절 3.2 에서 왔으면 그 이유(다른 영상이면 `page_mismatch`) |

- 시각은 모두 시간대가 있어야 하고(없으면 `ValueError`), JSON 에는 UTC ISO 8601 로 씁니다.
  `from_dict` 는 모르는 키나 빠진 필수 키에 `ValueError` 를 냅니다.

`data/videos.json` 예시 (실제 `Store.save` 출력 — 키 정렬, 2칸 들여쓰기, 한글 그대로, 끝에
줄바꿈):

```json
{
  "schema_version": 1,
  "videos": {
    "abcdefghijk": {
      "attempts": [
        {
          "at": "2026-10-12T03:32:00+00:00",
          "mode": "test",
          "reason": "dry_run",
          "result": "saved",
          "screenshot": null
        },
        {
          "at": "2026-10-12T03:41:00+00:00",
          "mode": "live",
          "reason": "allowlisted",
          "result": "posted",
          "screenshot": null
        }
      ],
      "channel_id": "UC123",
      "classification": {
        "at": "2026-10-12T03:30:00+00:00",
        "reason": "연애 고민 상담",
        "verdict": "yes"
      },
      "comment": {
        "at": "2026-10-12T03:31:00+00:00",
        "concern": "연락 빈도",
        "self_check": {
          "at": "2026-10-12T03:31:00+00:00",
          "reason": "자연스러움",
          "verdict": "yes"
        },
        "text": "연락 텀이 길어지면 마음이 먼저 앞서죠."
      },
      "description": "",
      "detected_at": "2026-10-12T03:00:00+00:00",
      "keyword": "썸",
      "published_at": "2026-10-11T23:00:00+00:00",
      "title": "연락 텀 때문에 불안한 썸",
      "trigger": {
        "at": "2026-10-12T03:30:00+00:00",
        "reason": "views_per_hour",
        "verdict": "yes"
      },
      "video_id": "abcdefghijk",
      "view_history": [
        {
          "at": "2026-10-12T03:00:00+00:00",
          "count": 1200
        },
        {
          "at": "2026-10-12T03:30:00+00:00",
          "count": 1450
        }
      ]
    }
  }
}
```

(`reason` 글자 `연애 고민 상담`, `views_per_hour` 같은 판정 이유는 예시입니다. 실제 값은
Phase 3–5 가 정합니다.)

## 4. 저장소 규칙 — `store.py`

`Store(path)` 는 `data/videos.json` 을 읽습니다. 파일이 없으면 빈 저장소이고 첫 변경 때
파일을 만듭니다. 쓰기는 임시 파일(`videos.json.tmp`)에 쓴 뒤 `os.replace` 로 바꿔 끼우므로,
같은 기록이면 언제나 같은 바이트입니다. JSON 이 깨졌거나, 최상위가 객체가 아니거나,
`schema_version` 이 1 이 아니거나, 키와 `video_id` 가 다르거나, 기록이 검사를 통과하지
못하면 `StoreError` 를 내고 **파일은 그대로 둡니다**(초기화하면 중복 방지 기록이 지워짐).

**API**

| 메서드 | 하는 일 |
|---|---|
| `get(video_id)` | 기록의 사본(없으면 `None`) — 사본을 바꿔도 저장소는 그대로 |
| `records()` | 모든 기록의 사본, `(detected_at, video_id)` 순 |
| `comments()` | 작성한 댓글 본문, `(comment.at, video_id)` 순 — Phase 5 의 반복 방지용 |
| `put(record)` | 기록을 넣거나 바꿈. **시도 기록(`attempts`)이 저장된 것과 다르면 `ValueError`** |
| `reserve_live(video_id, now)` | 클릭 전 예약 — 이미 `live` 시도가 있으면 `ValueError` |
| `resolve_live(video_id, result, now, reason="", screenshot=None)` | 마지막 `reserved` 를 `posted`/`failed` 로 확정 |
| `save_test(video_id, now, reason)` | 테스트 모드 저장(`test`/`saved`) |
| `check_post(video_id, channel_id, now, limits, live)` | 게시 가능 여부 → `PostCheck(allowed, reason)` |

- 시도 기록은 `reserve_live` · `resolve_live` · `save_test` 로만 바뀝니다. `put` 은 시도
  기록을 지우거나, 고치거나, 새 기록에 시도를 실어 오는 것을 모두 거부합니다.
- `resolve_live` 는 결과가 `posted`/`failed` 가 아니거나 열린 예약이 없으면
  `ValueError("확정할 게시 예약이 없습니다")` 입니다. 저장소에 없는 영상은
  `ValueError("저장소에 없는 영상입니다")`.
- 저장 중 오류는 그대로 올라갑니다. **`reserve_live` 가 오류를 내면 클릭하면 안 됩니다.**

**`check_post` 규칙** — 숨은 시계 없이 저장소와 넘겨받은 `now`(시간대 필수, 없으면
`ValueError`)로만 계산합니다. 같은 입력이면 같은 결과입니다. 순서대로 보고 처음 걸린 이유를
돌려줍니다:

1. **중복 영상** (`duplicate_video`) — 모드에 따라 다릅니다.
   - `live=True`: 그 영상에 `live` 시도가 하나라도 있으면(`reserved`/`posted`/`failed`) 막습니다.
     실패 뒤 재시도는 없습니다.
   - `live=False`: 그 영상에 시도가 하나라도 있으면 막습니다. 그래서 허용 목록의 데모 영상은
     먼저 테스트 모드로 돌린 뒤 실제 게시할 수 있습니다.
2. **최근 24시간 상한** (`daily_cap`) — 모든 영상의 `posted` + 확정되지 않은 `reserved` 시도 중
   `at > now − 24시간` 인 것이 `limits.daily_max_comments` 개 이상이면 막습니다. `failed` 와
   `saved` 는 세지 않습니다.
3. **채널 대기** (`channel_cooldown`) — 같은 `channel_id` 의 `posted` + `reserved` 시도 중
   `at > now − channel_cooldown_hours` 인 것이 있으면 막습니다.
4. 모두 통과하면 `PostCheck(True, "ok")`.

- 경계는 `>` 입니다. 정확히 24시간 전(또는 정확히 `channel_cooldown_hours` 전)의 게시는 더 이상
  세지 않습니다.
- 굴러가는 24시간 창이라 시간대가 필요 없고, 달력 하루 기준으로도 10개를 넘지 않습니다.
- 확정되지 않은 예약은 게시로 칩니다. 클릭 뒤 비정상 종료나 Ctrl-C 가 있어도 그 영상은 영원히
  막히고 상한과 채널 대기에 들어가므로, 에이전트를 끊었다 다시 켜도 두 번째 댓글이 달리지
  않습니다.

## 5. 허용 목록 가드 — `guard.py`

`decide_post(video_ref, allowed_videos, dry_run) -> PostDecision(video_id, live, reason)` 이
**실제 게시(`live=True`)를 돌려줄 수 있는 유일한 함수**입니다. 게시 버튼을 누르기 직전에
부릅니다. 인자는 정확히 이 셋이고, 이 판단을 건너뛰는 설정 · 인자 · 환경 변수는 없습니다.

| 순서 | 조건 | `live` | `reason` |
|---|---|---|---|
| 1 | 영상 주소를 읽을 수 없음 | `False` | `invalid_video` |
| 2 | 허용 목록에 없음 | `False` | `not_in_allowlist` |
| 3 | `dry_run` 이 정확히 `False` 가 아님 (참 · `None` · `0` · `""` 포함) | `False` | `dry_run` |
| 4 | 그 밖 | `True` | `allowlisted` |

- `PostDecision.mode` 는 `live` 가 참이면 `"live"`, 아니면 `"test"` 입니다.
- 허용 목록 이유가 `dry_run` 보다 앞서므로, 로그에는 언제나 허용 목록 원인이 남습니다.
- 허용 목록 항목과 영상 주소는 모두 11자 영상 ID 로 바꿔 비교합니다(`video_id_from_ref`).
  받는 형식은 아래뿐이고 정확히 이 모양이어야 합니다:
  - 맨 ID `abcdefghijk`
  - `https://youtu.be/abcdefghijk` — 경로가 정확히 `/<ID>` (쿼리가 붙으면 이름이 모두 `si` ·
    `t` · `feature` 중 하나 — 아래)
  - `https://www.youtube.com/watch?v=abcdefghijk` — 경로가 정확히 `/watch`, `v` 값이 정확히
    하나 (`&t=…` 등 다른 매개변수 무시)
  - `https://www.youtube.com/shorts/abcdefghijk` — 뒤 `/` 하나까지 (쿼리는 youtu.be 와 같은
    규칙 — 아래)
  - 호스트는 `youtu.be` · `youtube.com` · `www.youtube.com` · `m.youtube.com` 그대로(대소문자
    무시) — 사용자 정보(`…@`)나 포트(`:443`)가 붙으면 읽지 않습니다. 스킴은 `http`/`https` 만.
- 쿼리의 `%` 인코딩은 서버처럼 한 번 풀어 읽습니다 — `v` 의 수는 푼 뒤에 세므로
  `?%76=B&v=A` 는 `v` 가 두 개라 읽을 수 없고, watch 주소의 `&pp=…%3D%3D` · `&ab_channel=%EC…`
  같은 다른 매개변수는 무시됩니다.
- youtu.be · shorts 주소의 쿼리에서 받는 이름은 `si` · `t` · `feature` 셋뿐입니다. 쿼리를 한 번
  푼 뒤 `&` 와 `;` 로 나눈 이름이 모두 이 셋 중 하나와 대소문자까지 같을 때 읽고, 값은 보지
  않습니다 — `?si`, 빈 `?si=` 도 받습니다. 그 밖의 이름이 하나라도 있으면 읽을 수 없습니다:
  `v`, 풀면 `v` 인 `%76`, 빈 `?v=`, 대소문자가 다른 `V` · `SI`, 풀면 공백이 붙는 `+v`, 전각 `ｖ`,
  제어 문자가 붙은 `v\x01`, `list` 같은 다른 매개변수, 빈 이름(`?=x`), 처음 보는 이름 모두.
  유튜브는 `youtu.be/A?v=B` 를 `watch?v=B&v=A` 로, `/shorts/A?v=B` 를 `watch?v=B` 로 보내 B 를
  재생합니다 — 막을 이름 대신 받을 이름을 적어, 유튜브가 어떤 이름으로 재생 영상을 바꾸든 처음
  보는 꼴은 읽을 수 없는 쪽에 떨어집니다. 그래서 재생목록에서 복사한 `?list=…` 처럼 셋 밖의 꼬리가
  붙은 허용 목록 항목은 어떤 영상과도 맞지 않아 테스트 모드로만 돕니다 — 맨 ID 나 공유 버튼 주소를
  그대로 적으세요.
- 쿼리는 `&` 와 `;` 를 모두 매개변수 구분으로 봅니다 — 서버가 `;` 로도 나눌 때 숨는 이름을
  놓치지 않으려는 것이고(`?x=1;v=B`, HTML 에서 복사한 `?si=x&amp;v=B`), 그래서 `watch?v=<ID>;t=…`
  도 `&` 와 같이 읽힙니다. watch 주소는 `v` 값이 정확히 하나인지를 보고 다른 이름은 무시합니다 —
  클릭 직전 다시 묻기가 읽는 크롬 주소의 꼬리를 아직 재기 전이라서입니다(H-023).
- 그 밖의 호스트(`youtube.com.evil.example`, `youtube.com@evil.example` 같은 닮은꼴 포함),
  `ftp:` 같은 다른 스킴, 11자가 아닌 ID 는 읽을 수 없는 것으로 칩니다.
- 형식에서 벗어난 이웃 모양도 읽을 수 없는 것입니다: ID 뒤의 다른 경로 칸(`/<ID>/x`,
  `/<ID>/../<다른 ID>`, `/shorts/<ID>/../../watch?v=<다른 ID>`), 경로가 정확히 `/watch` 가
  아닌 watch 닮은꼴(`/watchx?v=…`, `/watch/?v=…`), 경로의 `.`/`..` 칸, 경로에
  `%` 가 든 주소(`%2e%2e`, `/%41…`), `v` 가 두 번 이상이거나 빈 `v` 가 섞인 주소(`?v=A&v=B`,
  `?v=&v=A`), 어디든 `\` 가 든 주소(`evil.com\@youtu.be/…`). 가드와 브라우저가 같은 주소를
  다르게 읽을 자리를 남기지 않기 위해서입니다. 그래서 경로에 `%` 가 든 정상 주소는 허용 목록
  항목으로도 쓸 수 없습니다 — 맨 ID 나 위 형식으로 적으세요.
- 읽을 수 없는 허용 목록 항목은 어떤 영상과도 맞지 않으므로, 과제의 자리표시자
  `https://youtu.be/내-테스트-영상-ID` 만 있으면 아무 영상도 실제 게시되지 않습니다.
- `dry_run` 은 `is not False` 로 검사합니다 — 참 · 거짓이 아닌 값(`None`, `0`, `""`)도 테스트
  모드입니다. 되돌릴 수 없는 남의 영상 댓글을 막는 쪽을 택했습니다.

## 6. 게시 흐름 — 모든 단계가 따릅니다

1. `decision = decide_post(video_ref, config.allowed_videos, dry_run)` 를 부른 뒤
   `check = store.check_post(video_id, channel_id, now, config.limits, live=decision.live)`.
2. 막혔으면(`check.allowed` 가 거짓) `SKIP` 을 남기고 다음 영상으로 넘어갑니다.
3. **실제 게시(`decision.live`):**
   1. 받은 주소 문자열(`video_ref`)은 크롬에 넘기지 않고 `https://www.youtube.com/watch?v={decision.video_id}` 를 새로 만들어 엽니다.
   2. 클릭 직전 확인: 크롬의 실제 주소로 `recheck = decide_post(page.url, config.allowed_videos, dry_run)` 를 한 번 더 부릅니다.
      `recheck.live` 가 거짓이거나 `recheck.video_id != decision.video_id` 이면 클릭하지 않고 4(테스트 모드)로 갑니다.
      이유는 `recheck.live` 가 거짓이면 `recheck.reason`, 다른 영상이면 `page_mismatch` 입니다.
   3. `store.reserve_live(video_id, now)`
   4. 로그 `POST … mode=live result=reserved reason=allowlisted`
   5. 클릭하고 게시를 확인 — 3.2 와 이 클릭 사이에는 예약과 로그 말고 다른 일(이동 · 기다림)을 두지 않습니다.
   6. `store.resolve_live(video_id, "posted" | "failed", now, reason, screenshot)`
   7. 로그 `POST … result=posted` 또는 `result=failed`
4. **테스트 모드:** `store.save_test(decision.video_id, now, reason=<decision.reason, 3.2 에서 왔으면 3.2 의 이유>)` 를 부르고 로그 `POST … mode=test result=saved reason=<그 reason>`.
   단 `decision.reason` 이 `dry_run` 이면(테스트 실행의 허용 목록 영상) 저장 대신 아래 **리허설** 입니다.
5. **`reserve_live` 가 오류를 냈으면 절대 클릭하지 않습니다.**

- 3.1 · 3.2 는 가드와 브라우저가 같은 주소를 다르게 읽을 자리를 없애는 두 겹 잠금입니다(가드의
  엄격함 하나에만 기대지 않음). 다시 확인을 예약 앞에 두는 까닭은 확정되지 않은 예약은 게시로
  치므로(4절) 예약 뒤에는 테스트 모드로 바꿀 수 없기 때문입니다. 같은 영상인지도 보는 까닭은
  자동 재생 · 다음 영상으로 크롬이 다른 허용 영상으로 옮겨 가면 저장소가 확인하지 않은 영상에
  댓글이 달리기 때문입니다. `page_mismatch` 는 `decide_post` 의 이유가 아니라 게시 단계가 남기는
  테스트 저장 이유입니다. 유튜브가 중간 화면(로그인 · 동의)을 띄우면 정상 게시도 테스트 모드로
  빠질 수 있습니다 — 안전한 쪽 실패로 받아들입니다. Phase 6 이 지킵니다.
  리허설(아래 '게시 단계 구현')에서는 다시 확인의 이 이유들이 저장 없이 `stopped` 의 원인이 됩니다.

### 게시 단계 구현 — poster.py · chrome.py (Phase 6)

```python
post_video(record, *, config, dry_run, store, logbook, open_page, clock,
           repo_root) -> PostOutcome
```

위 순서를 그대로 따릅니다. `video_ref` 는 `record.video_id` 입니다. `PostOutcome.result` 는
`skipped` · `saved` · `rehearsed` · `stopped` · `reserved` · `posted` · `failed` 중 하나입니다.

- **댓글 없음.** 댓글이 없는 기록은 `SKIP reason=no_comment` 입니다.
- **리허설 — 테스트 실행의 허용 목록 영상.** `decision.reason` 이 `dry_run` 이면 3.1 처럼 크롬에서
  `decision.video_id` 의 watch 주소를 열고, 댓글 칸에 입력해 게시 버튼이 켜졌는지까지 봅니다(준비).
  이어 3.2 처럼 `page.url` 로 `decide_post` 를 다시 부르고, 화면을 캡처한 뒤 입력한 글을 지우고
  탭을 닫습니다. 기록은 `POST … mode=test result=rehearsed reason=dry_run screenshot=… page_url=…`
  한 줄입니다. 캡처가 실패하면 `screenshot=` 을 빼고 씁니다. 글 지우기가 실패해도 버튼까지는
  닿았으므로 결과는 `rehearsed` 이고, 줄에 `detail="clear_failed <원인>: …"` 이 붙습니다.
- **리허설은 게시 버튼을 누르지 않습니다.**
  리허설은 저장소에 시도를 남기지 않습니다 — 그래서 채널 대기 · 24시간 상한 · 영상당 한 번을
  쓰지 않고, 같은 영상으로 다시 돌리면 다시 리허설하며, 그 뒤 보통 실행은 그 영상에 게시합니다.
  리허설 앞의 `check_post` 는 다른 테스트 모드처럼 `live=False` 로 불려, 그 영상에 시도가 이미
  있으면 `SKIP reason=duplicate_video`, 24시간 상한이나 채널 대기에 걸리면 그 이유의 `SKIP` 입니다.
- **리허설이 멈추면** 결과는 `stopped` 이고, '3.2 앞에서 멈춤' 과 같은
  `ERROR where=poster reason=<원인> … stage=before_click video=<ID>` 줄 하나를 남긴 채 다음
  영상으로 갑니다. 크롬 연결 · 영상 열기 · 준비에서 멈추면 원인은 원인 표의 이름이고, 글을 지우는
  단계 없이 탭을 닫습니다. 다시 확인에서 실제 게시였다면 3.2 에서 4(테스트 모드)로 빠졌을 화면이면
  원인은 그 이유(`not_in_allowlist` · `invalid_video` · `page_mismatch`)이고 `detail=` 은
  `page.url` 이며, 화면을 캡처한 뒤 입력한 글을 지웁니다.
- **허용 목록 밖 영상은 테스트 실행이든 아니든 크롬을 열지 않습니다** — 4(테스트 모드)로 저장합니다.
  `--dry-run` 의 "게시 직전까지"는 허용 목록 영상이면 게시 버튼 앞까지, 그 밖의 영상이면 댓글
  작성까지라는 뜻입니다.
- **3.2 앞에서 멈춤** (크롬 연결, 영상 열기, 댓글 칸 준비, 입력, 버튼 확인) — 아무것도 누르지
  않았으므로 저장소는 그대로이고 결과는 `stopped` 입니다. 남는 기록은
  `ERROR where=poster reason=<원인> detail=… screenshot=… stage=before_click video=<ID>` 한
  줄뿐이고, 다음 사이클이 다시 시도합니다.
- **3.2 의 되돌림**은 전처럼 4(테스트 모드)로 갑니다. 이때 `POST … mode=test result=saved` 줄에
  `screenshot=` 과 `page_url=` 이 붙습니다(저장소 기록에는 캡처 칸이 없습니다).
- **예약 뒤:**
  - 클릭 전에 게시 버튼이 없음 → `resolve_live(…, "failed", reason, screenshot)` 과
    `POST … result=failed`.
  - 클릭 중 예외, 확인 중 예외, "댓글이 보이지 않음" → 결과를 모르므로 `reserved` 를 그대로 두고
    `ERROR where=poster reason=<이유> detail=… screenshot=… stage=after_click video=<ID>` 를
    남깁니다(`detail=` 은 예외일 때만). 확정되지 않은 예약은 게시로 칩니다(4절).
  - 댓글이 보임 → `resolve_live(…, "posted", reason="allowlisted")`.
  - 예약 뒤의 Ctrl-C 도 `reserved` 로 남깁니다.
- **시계 읽기.** 실패 갈래마다 시계를 한 번 읽습니다. 저장된 시도의 `at` 과 그 캡처 파일 이름은
  같은 시각입니다.
- **원인 표.** 로그와 결과의 `reason` 에 남는 원인 이름입니다.

  | 이유 | 자리 | 뜻 |
  |---|---|---|
  | `no_comment` | 시작 | 기록에 댓글이 없음 — `SKIP` |
  | `playwright_missing` | 연결 | Playwright 가 설치되어 있지 않음 (`pip install -r requirements.txt`) |
  | `chrome_unreachable` | 연결 | `chrome_debug_url` 의 크롬에 붙지 못했거나, 붙은 크롬에 기본 컨텍스트가 없음 |
  | `login_required` | 준비 | 유튜브에 로그인되어 있지 않음 |
  | `comments_disabled` | 준비 | 이 영상은 댓글을 막아 둠 |
  | `comment_box_missing` | 준비 | 댓글 영역이나 입력 칸을 찾지 못함 |
  | `post_button_missing` | 준비 · 클릭 | 게시 버튼이 없거나 눌리지 않음 — 준비에서는 `stopped`, 클릭 직전이면 `failed` |
  | `page_error` | 연결 · 준비 | 그 밖의 예외 (탭 열기 · 영상 열기 시간 초과 등) |
  | `page_mismatch` | 다시 확인 | 크롬이 다른 영상에 있음 — 테스트 저장(리허설이면 저장 없이 `stopped`) |
  | `click_unknown` | 클릭 | 누르는 중 예외 — 결과를 모름, `reserved` |
  | `confirm_error` | 확인 | 게시 확인 중 예외 — 결과를 모름, `reserved` |
  | `not_confirmed` | 확인 | 기다리는 동안 댓글이 보이지 않음 — 결과를 모름, `reserved` |

- **캡처.**
  - 경로는 `logs/screenshots/<영상 ID>-<UTC YYYYMMDDTHHMMSSZ>.png` 입니다. 저장소 뿌리 기준
    상대 경로이고 `logs/*` 로 git 이 무시합니다.
  - 캡처가 실패하면 로그 줄에서 `screenshot=` 을 빼고 기록에는 `null` 을 저장하며, 나머지는
    모두 그대로 씁니다.
- **크롬 세션.** `ChromeSession(config.chrome_debug_url)` 은 `connect_over_cdp` 로
  `browser.contexts[0]`(로그인 쿠키가 있는 기본 컨텍스트)에 붙고, 영상마다 새 탭을 엽니다.
  `close()` 는 연결만 끊습니다.
- **선택자.** 유튜브 선택자는 `chrome.py` 맨 위의 상수입니다. 화면 구성이 바뀌면 여기를
  고칩니다(트래커 Trade-off).
- `post_video` · `check_profile_dir` 본문을 고칠 때도 10절의 음성 대조가 계속 1 로 끝나는지 함께
  확인합니다.

## 7. 로그 형식 — `logbook.py`

사건 하나에 한 줄입니다:

```
<KST ISO-8601 초> <EVENT> key=value key=value …
```

- 시각은 `at.astimezone(KST).isoformat(timespec="seconds")` — 예 `2026-10-12T21:30:00+09:00`.
  시간대 없는 시각은 `ValueError`.
- 필드 순서: 그 사건의 필수 필드를 정해진 순서로, 그 뒤 나머지 필드를 키 이름 순으로.
- 키는 `[a-z][a-z0-9_]*`. 필수 필드가 빠졌거나 키가 틀리면 `ValueError`.
- 값 쓰는 법:

  | 값 | 쓰는 모양 |
  |---|---|
  | `None` | `-` |
  | bool | `true` / `false` |
  | Enum | `.value` 를 글자로 |
  | 정수 | 그대로 |
  | 실수 | 소수 둘째 자리 (`181.25`) |
  | 시각 | KST ISO 8601 초 |
  | 글자 | 아래 날 글자로만 되어 있고 공백 · `"` · `=` · `\` 가 없으며 `-` 가 아니면 그대로, 아니면 JSON 따옴표(한글 그대로) |
  | 그 밖 | `TypeError` |

  값 안에 날 글자로 남는 것은 유니코드 범주 L(글자) · M(결합 표시) · N(숫자) · P(문장부호) ·
  S(기호)와 보통 공백 U+0020 뿐입니다. 그 밖의 모든 글자 — Cc(NUL · ESC · DEL · C1, `\n` 같은
  줄 경계 포함) · Cf(U+202E 같은 양방향 제어 · U+200B · U+200D) · 다른 공백 Zs(U+00A0 · U+3000) ·
  Zl · Zp · Co · Cn · Cs(짝 없는 서로게이트) — 는 언제나 따옴표 값 안의 이스케이프로 씁니다
  (`\n` · `\r` · `\t` · `\f` · `\b` 는 JSON 그대로, 나머지는 `\u0000` · `\u001b` · `\u0085` ·
  `\u2028` · `\u3000` · `\ud800` 처럼 `\uXXXX`, U+FFFF 위의 글자는 서로게이트 두 개). 그런 글자가
  든 값은 공백이 없어도 따옴표로 씁니다. 범주는 실행 중인 파이썬의 `unicodedata` 판정을 따르고,
  그 판이 모르는 글자(Cn)는 이스케이프 쪽입니다. 그래서 로그 파일에는 날 제어 문자도 서로게이트도
  없어, UTF-8 로캘의 GNU grep(`/usr/bin/grep`)이 파일을 바이너리로 보지 않고 제어 문자로 터미널에
  가짜 줄을 그릴 수 없습니다. 다만 긴 값이 화면 폭에서 접혀 줄처럼 보이는 것은 막지 않으므로, 게시
  증명은 화면이 아니라 `read_log` 로 읽습니다.
  여러 줄짜리 댓글도, 영상 제목에 숨긴 `U+2028` 도 `read_log` 의 읽기(UTF-8 ·
  `\n`)로 한 사건 한 줄이고, `parse_line` 이 원래 값을 되돌립니다(따로 들어온 서로게이트 두 개가
  짝을 이루면 한 글자로 읽힘). 줄 모양은 그대로입니다. 글자 `-` 는 `"-"` 로 써서 `None` 과
  구분됩니다.
- `parse_line(line)` 은 `format_line` 의 정확한 역으로 `(시각, Event, {키: 글자})` 를 돌려줍니다.
  이 규칙 전에 쓰인 줄(맨 값 속 날 제어 문자 등)도 그대로 읽습니다.
- `read_log(path)` 는 로그 파일을 읽는 단 하나의 방법입니다. 바이트를 UTF-8 로 엄격히 풀고
  `\n` 에서만 줄을 나눠, 빈 줄을 뺀 모든 줄을 `parse_line` 으로 읽은 `(시각, Event, {키: 글자})`
  목록을 파일 순서대로 돌려줍니다. 잘못된 UTF-8 바이트, 해석할 수 없는 줄, 끝 `\n` 이 없는
  마지막 줄(쓰기 중 끊긴 줄)은 건너뛰지 않고 `<n>번째 줄: …` `ValueError` 입니다. 파일을 열 수
  없으면 `OSError` 그대로입니다. Phase 7 · Phase 8 의 로그 증명(허용 목록 밖 영상의 게시 0건)은
  `read_log` 로 읽습니다 — latin-1 처럼 다른 글자 코드로 풀거나 `str.splitlines()` 로 나누면
  `갅`(`ea b0 85`) 같은 한글 속 `0x85` 가 줄 경계가 되어 제목 속 글이 가짜 줄로 읽힙니다.
- `Logbook(path, clock, echo)` 의 `write(event, **fields)` 는 줄을 만들어 파일에 UTF-8 로
  덧붙이고 같은 줄을 `echo` 로 냅니다. 실행 로그는 `logs/agent.log`(git 무시), 제출용 예시는
  `logs/sample.log`(커밋 가능)입니다.

| 사건 | 필수 필드 | 예시 줄 |
|---|---|---|
| `START` | mode, allowed, interval_min | `2026-10-12T21:30:00+09:00 START mode=test allowed=1 interval_min=30` |
| `CYCLE` | n | `2026-10-12T21:30:00+09:00 CYCLE n=1` |
| `DETECT` | video, channel, keyword, title | `2026-10-12T21:30:00+09:00 DETECT video=abcdefghijk channel=UC123 keyword=썸 title="연락 텀 때문에 불안한 썸"` |
| `VIEWS` | video, views, prev, delta | `2026-10-12T21:30:00+09:00 VIEWS video=abcdefghijk views=1450 prev=1200 delta=250` |
| `CLASSIFY` | video, verdict, reason | `2026-10-12T21:30:00+09:00 CLASSIFY video=abcdefghijk verdict=yes reason="연애 고민 상담"` |
| `TRIGGER` | video, verdict, reason | `2026-10-12T21:30:00+09:00 TRIGGER video=abcdefghijk verdict=yes reason=views_per_hour per_hour=181.25` |
| `COMMENT` | video, concern, text | `2026-10-12T21:30:00+09:00 COMMENT video=abcdefghijk concern="연락 빈도" text="연락 텀이 길어지면 마음이 먼저 앞서죠.\n천천히 물어보세요."` |
| `POST` | video, mode, result, reason | `2026-10-12T21:30:00+09:00 POST video=abcdefghijk mode=live result=reserved reason=allowlisted` |
| `SKIP` | video, reason | `2026-10-12T21:30:00+09:00 SKIP video=zyxwvutsrqp reason=channel_cooldown` |
| `QUOTA` | used, limit | `2026-10-12T21:30:00+09:00 QUOTA used=24 limit=100` |
| `ERROR` | where, reason | `2026-10-12T21:30:00+09:00 ERROR where=cycle reason="HTTP 403 quotaExceeded"` |
| `STOP` | reason | `2026-10-12T21:30:00+09:00 STOP reason=KeyboardInterrupt` |

`POST` 의 나머지 모양:

```
2026-10-12T21:30:00+09:00 POST video=abcdefghijk mode=live result=posted reason=allowlisted
2026-10-12T21:30:00+09:00 POST video=abcdefghijk mode=live result=failed reason="버튼을 찾지 못함" screenshot=logs/screenshots/abcdefghijk.png
2026-10-12T21:30:00+09:00 POST video=zyxwvutsrqp mode=test result=saved reason=not_in_allowlist
```

(필수 필드 밖의 `per_hour`, `screenshot` 같은 필드와 판정 이유 글자는 예시입니다.)

## 8. 비밀 값

- API 키는 `.env` 에만 둡니다. `.gitignore` 가 `.env`, `.env.*` 를 막고 `.env.example` 만
  커밋합니다. `.env.example` 에는 `YOUTUBE_API_KEY=` 와 `TYPESAFE_API_KEY=`(jev 판별 —
  `typesafe-sdk` 가 환경 변수에서 읽음)가 있고 값은 비워 둡니다. 댓글 작성 AI 의 키는 그것을
  쓰는 단계가 더합니다. `.env` 를 읽는 코드는 비밀 값을 처음 읽는 Phase 2 가 더합니다.
- 크롬 전용 프로필은 `chrome-profile/`(통째로 무시됩니다) 또는 저장소 밖에만 둡니다 — 저장소
  안의 다른 폴더는 금지입니다. Phase 6 · 8 의 실행 안내는 이 두 위치만 예시로 보입니다. 이 위치
  규칙이 첫 방어입니다.
- 크롬은 전용 프로필로 켭니다(`--user-data-dir` 를 기본 데이터 폴더가 아닌 곳으로) — Chrome
  136+ 는 기본 데이터 폴더에서 `--remote-debugging-port` 를 무시합니다.
  `python3 -m agent.chrome --profile <폴더>`(저장소 뿌리에서 `PYTHONPATH=src`, 윈도우
  PowerShell 은 먼저 `$env:PYTHONPATH = "src"`)가 켜기 전에 위치를 검사(`check_profile_dir`)하고
  켤 명령을 보여 줍니다 — 크롬을 직접 켜지는 않습니다. 기본 데이터 폴더(그 안 포함)와, 저장소
  안이면서 `chrome-profile/` 밖인 곳은 거부합니다(종료 코드 2). 상대 경로는 저장소 뿌리
  기준이고, 심볼릭 링크는 따라간 실제 위치로 봅니다. **이 검사는 켤 때의 안내입니다** — 에이전트는
  붙은 크롬의 프로필 위치를 실행 중에 확인하지 않습니다. 실행 중 방어는 둘입니다: 기본 데이터
  폴더로 켠 크롬은 포트가 열리지 않아 게시가 `chrome_unreachable` 로 멈추고, 저장소 안 다른
  폴더의 비밀 파일은 아래 둘째 방어(이름 목록)가 막습니다.

  ```
  PYTHONPATH=src python3 -m agent.chrome --profile chrome-profile
  PYTHONPATH=src python3 -m agent.chrome --profile ~/marketing-agent-chrome
  ```

  보여 준 명령으로 크롬을 켠 뒤 그 창에서 유튜브에 한 번 로그인합니다. **디버깅 포트의 위험:**
  포트가 열려 있는 동안 이 컴퓨터의 어떤 프로그램이든 인증 없이 그 크롬에 붙어 로그인된 계정의
  쿠키(HttpOnly 포함)를 읽을 수 있습니다 — Chrome 136 이 기본 프로필에서 포트를 막은 까닭이
  이것입니다. 그래서 이 프로필에는 본 구글 계정이 아닌 전용 유튜브(브랜드) 계정으로만 로그인하고,
  에이전트를 쓰지 않을 때는 그 크롬을 닫습니다.
- 둘째 방어 — 사람이 위치 규칙을 어겨도, 프로필 안의 비밀 파일은 폴더 이름과 상관없이 어느
  깊이에서든 이름으로 막습니다: `Cookies`, `Cookies-journal`, `Login Data*`, `Web Data*`,
  `Local State`, `Local Storage/`, `Session Storage/`, `Preferences`, `Secure Preferences`,
  `History*`, `IndexedDB/`, `Sessions/`, `Extension Cookies`, `Account Web Data`. 쿠키 · 로그인
  상태 내보내기(`cookies*.json`, `*storage_state*.json`)와 다른 도구의 비밀 · 인증 파일
  (`.envrc`, `.env-local`, `client_secret_*.json`, `token.json`)도 막습니다.
- 흔한 이름(`History`, `Preferences` 등)이라 저장소 어디서든 git 이 무시합니다 — 그런 이름의
  진짜 파일을 만들면 커밋되지 않습니다. 이름 목록은 크롬 버전이 바뀌면 뒤처질 수 있으므로
  Phase 8 직전 `git ls-files` 사람 확인은 그대로 남습니다. `tests/test_gitignore.py` 가 이
  목록을 임의 폴더 아래에서 `git check-ignore` 로 확인합니다.
- `data/` 와 `logs/` 는 폴더만(`.gitkeep`) 커밋합니다. `logs/sample.log` 는 제출물이라 커밋할
  수 있습니다.
- `.env.example` 에는 댓글 작성 Claude 키 `ANTHROPIC_API_KEY=` 도 있습니다(Phase 5).
  `anthropic_client()` 에 키를 넘기지 않으면 `anthropic` 패키지가 이 환경 변수를 읽습니다('댓글 작성' 절).

## 9. 주기 실행 — `scheduler.py`

```python
run_loop(cycle, reload, initial, *, on_error, sleep=time.sleep,
         monotonic=time.monotonic, max_cycles=None) -> int
```

한 바퀴의 순서:

1. `started = monotonic()`
2. `cycle(config)` — `Exception` 은 `on_error("cycle", exc)` 로 알리고 계속 돕니다.
   `KeyboardInterrupt` 는 위로 올라갑니다.
3. 돈 횟수를 더하고, `max_cycles` 에 닿으면 다시 읽기나 대기 없이 횟수를 돌려줍니다.
4. `config = reload()` — `ConfigError` 는 `on_error("config", exc)` 로 알리고 이전 설정을
   유지합니다. 진입점(`run.py`)이 넘기는 `reload` 는 거절을 기억해, 거절이 이어지는 동안 실제 게시를 멈춥니다(2절 끝).
5. `wait = min(poll_interval_min × 60, 약 100년) − (monotonic() − started)` 만큼, 하루 이하
   조각으로 나눠 `sleep` 합니다. `wait` 가 0 이하이면 `sleep(0.0)` 을 한 번 부릅니다.

- 주기는 사이클 *시작* 부터 잽니다. 사이클이 주기보다 오래 걸리면 쉬지 않고 바로 다음 사이클을
  돕니다.
- 아주 큰 `poll_interval_min` 도 루프를 죽이지 않습니다 — sleep 한 번은 하루까지(운영체제마다
  다른 sleep 한도에 닿지 않게), 대기 전체는 약 100년까지(아주 큰 정수를 실수로 바꾸다 나는
  OverflowError 방지). 하루 이하 주기는 지금처럼 sleep 한 번입니다. 설정에서 읽은 주기는 2절의
  상한(52560000분)이 이미 이 크기로 묶고, 이 묶음은 코드로 만든 설정에도 남습니다.
- `poll_interval_min` 만 고치면 재시작이나 OS 설정 없이 다음 대기부터 주기가 바뀝니다.
- 신호 처리나 fork 는 쓰지 않습니다. Phase 7 의 진입점이 `run_loop` 를 부릅니다.

## 10. 계약 변경 규칙

- 1–10절은 번호로, 그 뒤에 더하는 절은 번호 없이 제목만 달고 제목으로 가리킵니다 — 제목은
  `## 주제 판별 — …` 꼴, 인용은 `'주제 판별' 절` 꼴입니다. 이 문서의 `## <숫자>.` 제목 번호가
  차례대로 1–10 이 아니거나, `src/` · `tests/` · 이 문서에 10보다 큰 번호를 단 절 인용(ASCII
  숫자 바로 뒤에 '절')이 있으면 `tests/test_contract_sections.py` 가 빨강입니다.
- 번호를 뗀 2026-10-14 전의 기록(트래커 · 장부 · 일지)에서 옛 번호 11 · 12 로 가리킨 절은, 기록이
  그 자리에서 제목이나 함수 · 모듈 이름으로 밝힌 절입니다. 밝힌 것이 없으면 그 기록을 남긴
  페이즈가 더한 절입니다 — Phase 2 '탐지 · 조회수 추적' · Phase 3 '주제 판별' ·
  Phase 4 '트리거 판정' · Phase 5 '댓글 작성'.
- 여기 적은 모양(설정 키, `VideoRecord` 필드, 시도 상태, `check_post` 이유, `decide_post`
  인자와 이유, 로그 사건과 필수 필드)은 고정입니다.
- 더하는 것은 그 필드를 쓰는 단계(Phase)가 `models.py` · `config.py` 에서, 테스트와 함께, 이
  문서도 함께 고칩니다. 이미 있는 이름의 뜻을 바꾸거나 지우지 않습니다.
- 가드 · 저장소 · 설정 읽기 · 로그 한 줄 규칙 · 판별 규칙 · 쿼터 가드 · 탐지 입력 검사 · 인기 댓글 · 실제 호출 실행기 · 실제 결과 반영이 테스트로 지켜지는지는 음성 대조로 확인합니다. 각 명령은 가드 한 줄을
  메모리에서만 망가뜨리고 테스트를 돌리며, **종료 코드 1(테스트가 잡음)** 이어야 합니다. 2 는
  바꿀 글자를 찾지 못했다는 뜻이라 실패입니다:

  ```
  python3 -m tests.mutants poster-open-received-ref
  python3 -m tests.mutants poster-recheck-before-prepare
  python3 -m tests.mutants poster-no-recheck
  python3 -m tests.mutants poster-no-page-mismatch
  python3 -m tests.mutants poster-skip-reserve
  python3 -m tests.mutants poster-click-error-as-failed
  python3 -m tests.mutants poster-unconfirmed-as-posted
  python3 -m tests.mutants poster-ignore-check
  python3 -m tests.mutants poster-test-mode-opens-chrome
  python3 -m tests.mutants poster-dry-run-skips-rehearsal
  python3 -m tests.mutants poster-rehearse-not-allowlisted
  python3 -m tests.mutants poster-rehearsal-clicks
  python3 -m tests.mutants poster-rehearsal-keeps-text
  python3 -m tests.mutants poster-rehearsal-no-recheck
  python3 -m tests.mutants poster-rehearsal-no-page-mismatch
  python3 -m tests.mutants chrome-allow-default-profile
  python3 -m tests.mutants chrome-allow-repo-folder
  python3 -m tests.mutants chrome-clear-keeps-text
  python3 -m tests.mutants guard-allow-all
  python3 -m tests.mutants guard-ignore-dry-run
  python3 -m tests.mutants guard-dry-run-truthy
  python3 -m tests.mutants guard-first-v
  python3 -m tests.mutants guard-youtu-be-first-segment
  python3 -m tests.mutants guard-shorts-first-segment
  python3 -m tests.mutants guard-host-ignores-userinfo
  python3 -m tests.mutants guard-allow-backslash
  python3 -m tests.mutants guard-youtu-be-ignores-query-v
  python3 -m tests.mutants guard-shorts-ignores-query-v
  python3 -m tests.mutants guard-query-ampersand-only
  python3 -m tests.mutants guard-share-names-blocklist
  python3 -m tests.mutants guard-share-names-ignore-case
  python3 -m tests.mutants store-no-dedupe
  python3 -m tests.mutants store-no-cap
  python3 -m tests.mutants store-no-cooldown
  python3 -m tests.mutants store-reserved-not-counted
  python3 -m tests.mutants store-put-overwrites-attempts
  python3 -m tests.mutants store-double-reserve
  python3 -m tests.mutants config-narrow-read-errors
  python3 -m tests.mutants config-no-ceiling
  python3 -m tests.mutants config-no-int-ceiling
  python3 -m tests.mutants config-text-any-char
  python3 -m tests.mutants config-text-edge-spaces
  python3 -m tests.mutants config-debug-url-skips-text
  python3 -m tests.mutants config-debug-url-any-host
  python3 -m tests.mutants config-debug-url-prefix-only
  python3 -m tests.mutants config-no-topic-ceiling
  python3 -m tests.mutants scheduler-one-sleep
  python3 -m tests.mutants scheduler-unclamped-wait
  python3 -m tests.mutants logbook-raw-line-breaks
  python3 -m tests.mutants logbook-bare-control-chars
  python3 -m tests.mutants logbook-read-latin1
  python3 -m tests.mutants logbook-read-splitlines
  python3 -m tests.mutants logbook-read-skips-bad-lines
  python3 -m tests.mutants logbook-read-keeps-cut-line
  python3 -m tests.mutants youtube-no-search-cap
  python3 -m tests.mutants youtube-no-unit-cap
  python3 -m tests.mutants youtube-unguarded-call
  python3 -m tests.mutants youtube-window-never-expires
  python3 -m tests.mutants watcher-silent-hold
  python3 -m tests.mutants watcher-no-page-cap
  python3 -m tests.mutants watcher-silent-page-cap
  python3 -m tests.mutants watcher-keeps-surrogates
  python3 -m tests.mutants watcher-unicode-digits
  python3 -m tests.mutants watcher-published-any-shape
  python3 -m tests.mutants writer-hardcoded-model
  python3 -m tests.mutants writer-no-rewrite
  python3 -m tests.mutants writer-third-try
  python3 -m tests.mutants writer-ignore-self-check
  python3 -m tests.mutants writer-threshold-strict
  python3 -m tests.mutants writer-no-float-tolerance
  python3 -m tests.mutants writer-ad-not-inverted
  python3 -m tests.mutants writer-trusts-jev-answer
  python3 -m tests.mutants writer-no-length
  python3 -m tests.mutants writer-length-in-bytes
  python3 -m tests.mutants writer-no-link
  python3 -m tests.mutants writer-link-no-nfkc
  python3 -m tests.mutants writer-link-view-keeps-all
  python3 -m tests.mutants writer-link-ascii-separators-only
  python3 -m tests.mutants writer-link-latin-left-only
  python3 -m tests.mutants writer-link-no-handle
  python3 -m tests.mutants writer-no-repeat
  python3 -m tests.mutants writer-repeat-keeps-punctuation
  python3 -m tests.mutants writer-repeat-all-history
  python3 -m tests.mutants writer-unescaped-material
  python3 -m tests.mutants writer-api-error-unlogged
  python3 -m tests.mutants writer-self-skip-checked
  python3 -m tests.mutants writer-no-concern-ignored
  python3 -m tests.mutants writer-no-frame
  python3 -m tests.mutants writer-frame-counts-required-word
  python3 -m tests.mutants task-table-missing-sentence-ignored
  python3 -m tests.mutants classifier-error-yes
  python3 -m tests.mutants classifier-malformed-yes
  python3 -m tests.mutants classifier-unchecked-probability
  python3 -m tests.mutants classifier-no-confidence-floor
  python3 -m tests.mutants classifier-keyword-only-passes
  python3 -m tests.mutants classifier-no-truncation
  python3 -m tests.mutants classifier-error-hold-unmarked
  python3 -m tests.mutants classifier-swallows-faults
  python3 -m tests.mutants youtube-comments-free
  python3 -m tests.mutants youtube-comments-any-403-disabled
  python3 -m tests.mutants live-check-ceiling-plus-one
  python3 -m tests.mutants live-check-ceiling-swallowed
  python3 -m tests.mutants live-check-key-unredacted
  python3 -m tests.mutants live-check-views-exclusive
  python3 -m tests.mutants live-check-calls-without-key
  python3 -m tests.mutants live-check-unmeasured-ignored
  python3 -m tests.mutants live-check-call-errors-ignored
  python3 -m tests.mutants live-check-video-errors-ignored
  python3 -m tests.mutants live-check-api-failure-as-skip
  python3 -m tests.mutants live-check-no-margin
  python3 -m tests.mutants live-check-floor-above-one
  python3 -m tests.mutants live-check-skip-half-stops
  python3 -m tests.mutants live-check-one-model-stops
  python3 -m tests.mutants live-check-grader-in-agent
  python3 -m tests.mutants live-check-cli-exception-only
  python3 -m tests.mutants live-check-entry-skips-cli
  python3 -m tests.mutants live-check-grade-block-half-stops
  python3 -m tests.mutants live-check-grade-block-schema-ignored
  python3 -m tests.mutants live-check-popular-shortfall-ignored
  python3 -m tests.mutants live-check-contacts-unmasked
  python3 -m tests.mutants live-check-contact-line-blind
  python3 -m tests.mutants live-check-clip-before-mask
  python3 -m tests.mutants live-check-untrusted-unmasked-at-write
  python3 -m tests.mutants live-check-published-scan-blind
  python3 -m tests.mutants live-check-draft-masked-at-write-only
  python3 -m tests.mutants live-check-kept-contacts-before-keys
  python3 -m tests.mutants live-check-draft-contacts-before-keys
  python3 -m tests.mutants live-check-gap-ambiguous
  python3 -m tests.mutants live-check-dash-like-unbounded
  python3 -m tests.mutants live-check-code-failures-raw
  python3 -m tests.mutants live-check-code-failures-dropped
  python3 -m tests.mutants live-check-repeat-count-shifted
  python3 -m tests.mutants live-check-contact-keys-unread
  python3 -m tests.mutants live-check-contact-line-summary-blind
  python3 -m tests.mutants live-check-contact-line-one-place-passes
  python3 -m tests.mutants live-check-code-check-reads-masked
  python3 -m tests.mutants live-check-grade-reads-masked
  python3 -m tests.mutants live-check-passed-ignores-code-check
  python3 -m tests.mutants live-check-applied-yes-floor-lowered
  python3 -m tests.mutants live-check-applied-floor-lowered
  python3 -m tests.mutants live-check-applied-reads-jev-models
  python3 -m tests.mutants live-check-best-setting-tie-raised
  python3 -m tests.mutants live-check-applied-recount-ignored
  python3 -m tests.mutants live-check-applied-exception-any-run
  python3 -m tests.mutants live-check-applied-stored-verdicts-unchecked
  python3 -m tests.mutants live-check-applied-unknown-question-ignored
  python3 -m tests.mutants live-check-applied-recheck-no-tolerance
  python3 -m tests.mutants live-check-applied-answer-three-cells
  python3 -m tests.mutants live-check-applied-skip-reads-reason
  python3 -m tests.mutants live-check-skip-grade-every-skip
  ```

  `classify` · `read_answers` · `build_state` · `is_error_hold` · `sdk_ask` ·
  `decide_post` · `video_id_from_ref` · `put` · `reserve_live` · `check_post` · `load_config` ·
  `config_from_mapping` · `run_loop` · `format_line` · `QuotaLedger.reserve` ·
  `YouTubeClient._call` · `Watcher.run` · `YouTubeClient.top_comments` · `tests/live_check.py` 의
  `Calls.take` · `Redactor` · `mask_contacts` · `_kept` · `_scrub` · `_VideoRound._drafts` · `contact_places` ·
  `best_correct` · `best_setting` · `verdict_line` · `cli` · `main` ·
  `write_comment` · `code_failures` · `self_check_failure` · `link_fragment` · `repeated_run` 의
  본문을 고칠 때는 이 명령들이 계속 1 로 끝나는지 함께 확인합니다. `tests/test_live_check_applied.py` 의
  `measured_drift` · `recount` · `admitted` · `stored_verdict_mismatches` · `claude_answer` · `_skip_kind` 본문을 고칠 때도
  `live-check-applied-*` 명령이 계속 1 로 끝나는지 함께
  확인합니다. 음성 대조 실행기는 `agent.*` 모듈과 `tests.live_check` · `tests.test_live_check_applied`
  를 메모리에서 바꿉니다.

## 탐지 · 조회수 추적 — env.py · youtube.py · watcher.py (Phase 2)

**진입점**

```python
key = require_secret("YOUTUBE_API_KEY", Path(".env"), os.environ)
client = YouTubeClient(key, QuotaLedger(Path("data/quota.json")))
watcher = Watcher(Store(Path("data/videos.json")), logbook, client, clock)
```

`watcher.cycle(config)` 는 `watcher.run(config, clock())` 이고, `run_loop` 의 사이클 자리(9절)에
맞습니다 — Phase 7 이 잇습니다. 돌려주는 `CycleReport` 의 여섯 칸:

| 칸 | 뜻 |
|---|---|
| `searches` | 받은 검색 페이지 수 |
| `detected` | 새로 저장한 영상 ID, 찾은 순서대로 |
| `sampled` | 조회수 표본을 남긴 영상 수 |
| `truncated` | 페이지 상한에서 끊긴 검색어 수 — `QUOTA … counter=pages` 한 줄씩 |
| `held` | 쿼터 가드가 호출을 막았는지 — `QUOTA` 줄을 남김 |
| `failed` | `ERROR` 줄을 남겼는지 |

`held` 와 `truncated` 가 "새 영상이 없었음" 과 "한도에 막혀 다 보지 못했음" 을 가릅니다.

- **명단 영상(Phase 7).** 사이클마다 `allowed_videos` 의 영상 ID(`allowed_video_ids`, 5절 — 읽을 수 없는 항목은 버림)를
  검색 · 나이 창과 상관없이 추적 대기열에 한 번씩 더합니다.
  저장소에 없는 명단 영상은 처음 본 사이클에 기록을 만들고, `keyword` 는 그 사이클 검색이 찾았으면 그 검색어, 아니면 `allowed_videos` 입니다.
  명단 영상의 `DETECT` 줄에는 `allowlisted=true` 가 붙습니다.
- **한 벌 · 한 스레드.** 진입점(`run.py`)은 저장소와 쿼터 장부를 데이터 폴더마다 한 벌만 만들어 탐지 · 작성 · 게시가
  함께 쓰고, 다섯 단계를 한 스레드에서 차례로 돌립니다.

**비밀 값** — `require_secret(name, env_path, environ)`

- 비어 있지 않은 환경 변수가 먼저이고, 없으면 `.env` 의 값입니다. 둘 다 비었으면
  `EnvError("<이름> 가 비어 있습니다 — <경로> 에 <이름>=<키> 를 적으세요")`.
- `.env` 는 `이름=값` 줄(이름은 `[A-Za-z_][A-Za-z0-9_]*`), `#` 로 시작하는 주석 줄, 빈 줄만
  받습니다. 줄과 값의 앞뒤 공백은 지우고, 값 둘레의 같은 따옴표 한 쌍(`'…'` 또는 `"…"`)은
  떼어 냅니다. 값 뒤의 `#` 은 주석이 아니라 값의 일부입니다.
- 형식이 틀린 줄이나 두 번 나온 이름은 `EnvError` 이고, 메시지는 파일과 줄 번호
  (`<경로> 2번째 줄: …`)를 말하지만 값은 **절대** 담지 않습니다. 파일이 없으면 빈 것으로 읽고,
  BOM 은 떼어 내며, UTF-8 이 아닌 저장은 `EnvError` 입니다.
- 키는 `[A-Za-z0-9_-]+` 여야 합니다. 아니면(빈 글자, 끝에 남은 `\r`, 공백, 한글) `YouTubeClient`
  가 키를 되풀이하지 않는 `ValueError` 를 냅니다.

**한 사이클**

1. 검색 — `keywords` 를 설정 순서로, 같은 검색어는 한 번만 찾습니다. `search.list` 매개변수는
   `part=snippet` · `type=video` · `order=date`(최신순) · `q=<검색어>` · `regionCode=KR` ·
   `relevanceLanguage=ko` · `maxResults=50` · `publishedAfter=<now − trigger.max_age_hours, UTC …Z>`,
   다음 페이지면 `pageToken` 이 더해집니다.
2. 다음 페이지는 셋이 모두 맞을 때만 받습니다 — 그 페이지에 `nextPageToken` 이 있고, 사이클 시작
   때 저장소에 있던 영상이 그 페이지에 없고, 그 검색어로 받은 페이지가 `MAX_PAGES_PER_KEYWORD`
   (3) 보다 적을 때. `nextPageToken` 이 빈 글자 `""` 도, 영문자 · 숫자 · `_` · `-` 로 된 글자도
   아닌 값이면(글자가 아닌 값 포함) 그 페이지는 통째로 검색 오류입니다 — `ERROR where=search.list
   reason="HTTP 200 nextPageToken 이 영문자 · 숫자 · _ · - 가 아닙니다" keyword=<검색어>` 를 남기고
   남은 검색은 그만둔 채 추적으로 넘어갑니다('API 오류').
3. 페이지 상한이 토큰을 남긴 채(아는 영상 없이) 검색어를 끝내면 최신 150개 뒤의 결과를 보지 못한
   것이므로 `QUOTA used=3 limit=3 call=search.list counter=pages keyword=<검색어>` 를 남기고
   `truncated` 에 셉니다. 정한 한도도 다른 한도처럼 로그에 남깁니다.
4. 추적 — 이번에 찾은 새 영상(찾은 순서) 다음에 `published_at > now − trigger.max_age_hours` 인
   저장 영상(`records()` 순)을 50개씩 `videos.list`(`part=snippet,statistics`)로 묻습니다. 영상
   정보는 검색 결과가 아니라 `videos.list` 에서 씁니다 — 검색 제목은 HTML 이스케이프되고 설명은
   잘려 있습니다.
5. 새 영상은 `DETECT` 다음 `VIEWS` 를 남긴 뒤 `view_history=[ViewSample(now, 조회수)]` 로 저장하고,
   아는 영상(6번)도 `VIEWS` 를 남긴 뒤 저장합니다 — 줄이 먼저, 저장은 그다음입니다. 저장이 실패하면
   예외가 탐지기 밖으로 나가지만(9절) 그 주기 로그에 줄은 이미 있고, 다음 주기는 메모리가 그 영상을
   알므로 `DETECT` 없이 표본만 더해 저장합니다(그 사이 에이전트를 다시 켜면 새 영상으로 한 번 더
   `DETECT`). 로그 쓰기가 실패하면 저장 전에 멈추므로 그 영상은 저장소에 없고, 다음에 찾을 때 새
   영상으로 `DETECT` 를 남깁니다. `keyword` 는 처음 찾은 검색어입니다.
6. 아는 영상은 `get` 사본에 표본 하나를 덧붙여 `put` 합니다 — 제목 등은 처음 본 값 그대로이고
   `attempts` 는 건드리지 않습니다. 로그는 `VIEWS … prev=<이전 조회수> delta=<차이>` 입니다.

- `trigger.max_age_hours` 가 검색 기간(`publishedAfter`)과 추적 기간을 함께 정합니다(2절).

**쿼터 가드** — `youtube.py` 가 쿼터 단위를 아는 유일한 곳입니다.

- `UNIT_COST = {"search.list": 100, "videos.list": 1, "commentThreads.list": 1}`,
  `DAILY_QUOTA_UNITS = 10_000`(Google 기본 프로젝트 쿼터). Google 쿼터를 늘린 프로젝트는 이 상수
  하나만 바꿉니다.
- 모든 호출이 `YouTubeClient._call` 에서 `QuotaLedger.reserve(call, now, limits)` 를 거칩니다.
  하루는 굴러가는 24시간이고 경계는 `>` 입니다 — 정확히 24시간 전의 호출은 세지 않습니다
  (`check_post` 와 같음). 막는 조건은 둘입니다:
  1. `search.list` 이고 최근 24시간의 `search.list` 수가 `limits.daily_max_searches` 이상 →
     `counter=searches`
  2. 최근 24시간의 단위 합 + 이 호출의 비용이 `DAILY_QUOTA_UNITS` 를 넘음 → `counter=units`
- 허락된 호출은 요청을 보내기 *전에* `data/quota.json` 에 적습니다. 실패한 요청도 Google 이
  쿼터를 떼므로 셉니다. 페이지 넘김도 `search.list` 한 번이라 가드를 비켜 가지 못합니다.
- 기록 파일은 `{"calls": [{"at": "<UTC ISO>", "call": "search.list", "units": 100}, …],
  "schema_version": 1}` 모양입니다(키 정렬, 2칸 들여쓰기, 쓸 때 48시간이 지난 항목은 지움 — 셈은
  24시간 그대로이고, 시계가 하루 안쪽으로 앞서도 실제 호출 기록이 남게, 임시 파일에 쓴 뒤
  `os.replace`). JSON · 버전 · 항목 모양이 틀리면 `QuotaError` 를 내고
  **파일은 그대로 둡니다** — 지우면 오늘 쓴 쿼터를 잊으므로, 고치거나 오늘 쓴 쿼터를 확인한 뒤
  사람이 지웁니다.
- 막힌 호출은 보내지 않고, watcher 가 `QUOTA used=<사용> limit=<한도> call=<호출>
  counter=<searches|units|pages> [keyword=<검색어>]` 를 남깁니다.
- 검색이 막히면 남은 검색은 그만두지만 추적은 돕니다. `videos.list` 가 막히면 추적을 그만둡니다.
- 검색 1회 100 단위는 이 장부의 셈입니다. Google 은 2026-10-08 부터 `search.list` 를 하루 100회
  별도 통으로 세지만, 장부는 일부러 더 엄격하게 10,000 단위 통에서 깎습니다(옛 규칙과 새 규칙
  모두에서 넘치지 않게). 그래서 `daily_max_searches` 를 90 보다 올리면 한 회마다 조회수 호출 몫이
  100 단위씩 줄고, 100 이면 남지 않아 `videos.list` 가 `counter=units` 로 막힙니다 — Google 이
  아니라 이 장부 때문입니다(2절).
- Google 은 태평양 자정에 쿼터를 되돌리지만 여기는 굴러가는 24시간입니다. 서머타임이 끝나는
  25시간짜리 날에만 어긋날 수 있고, 그때는 `ERROR … reason="HTTP 403 quotaExceeded"` 줄로
  드러납니다.

**API 오류**

- HTTP 200 이 아니면 `ERROR where=<호출> reason="HTTP <상태> <Google reason>"` 입니다(예:
  `ERROR where=search.list reason="HTTP 403 quotaExceeded"`). 리다이렉트(301 · 302 · 303 · 307 ·
  308)도 따라가지 않고 그 상태로 같은 모양이며(본문에 Google reason 이 없으면 `reason="HTTP 302"`),
  오류 상태의 본문을 읽다 실패하면 Google reason 없이 `reason="HTTP <상태>"` 입니다. 요청이 예외로
  끝나면 — 연결 · 읽기 실패, 깨진 응답 틀, 요청 전체 30초 상한(`TimeoutError`) 등 무엇이든 —
  `reason="network <종류>: …"`, 본문이 JSON 객체가 아니면 `reason="HTTP 200 invalid JSON"`. 검색
  오류에는 `keyword` 가 붙습니다.
- 오류가 난 단계는 멈춥니다 — 검색 오류면 남은 검색을 그만두고 추적으로 넘어가고, 조회수 오류면
  추적을 그만둡니다.
- 오류 글 속 API 키는 `<YOUTUBE_API_KEY>` 로 가리고, 원래 예외(키가 든 URL)는 덧붙이지 않습니다.
- **음성 대조.** `python3 -m tests.mutants <이름>` — `youtube-narrow-network-catch` · `youtube-follows-redirects` ·
  `youtube-no-request-cap` · `youtube-open-without-read-timeout` · `youtube-error-body-failure-raises` ·
  `youtube-error-left-open` · `youtube-opener-without-https` · `youtube-opener-without-proxy` · `youtube-prune-at-window` ·
  `watcher-repr-any-value` · `watcher-any-page-token` · `watcher-put-before-lines`.

**인기 댓글** — `YouTubeClient.top_comments(video_id, now, limits, max_results) -> tuple[str, ...] | None`

- `commentThreads.list` 한 번(1단위, 쿼터 가드를 지남) — `part=snippet` · `videoId` · `order=relevance` ·
  `maxResults=<max_results>` · `textFormat=plainText`. `max_results` 가 1–100 밖이면 부르기 전에
  `ValueError` 입니다. 부르는 쪽은 `TOP_COMMENTS_MAX`(10, '댓글 작성' 절)를 넘깁니다.
- 돌려주는 것은 항목마다 `snippet.topLevelComment.snippet.textDisplay` 글뿐이고, 작성자 이름 ·
  채널 ID 는 읽지 않습니다. 모양이 다른 항목은 건너뛰고, 외톨이 서로게이트는 U+FFFD 로 바꿉니다.
  `items` 가 목록이 아니면 `YouTubeError("commentThreads.list", "HTTP 200 items 가 목록이 아닙니다")`.
- 오류 이유가 정확히 `HTTP 403 commentsDisabled` 이면 `None` 입니다 — 그 영상 하나의 일이고, 부르는
  쪽은 제목 · 설명으로 이어 갑니다. 다른 403(`quotaExceeded` 등)과 그 밖의 오류는 `YouTubeError`
  그대로 올라갑니다.
- `search(…, published_before=None)` — 주면 `publishedBefore=<UTC …Z>` 가 더해집니다(실제 호출 실행기의
  넓힌 창). 시간대가 없거나 `published_after` 와 같거나 이르면 `ValueError` 입니다. 탐지 사이클은
  기본값 `None` 으로 부릅니다.

**외부 글자**

- 밖에서 온 글자(제목 · 설명 · 채널 ID · 검색어 · 오류 이유)의 외톨이 서로게이트는 U+FFFD 로
  바꿉니다(HC1-2 R3) — 그대로 두면 `Store.save` 의 UTF-8 쓰기가 실패합니다.
- 허용한 모양만 받습니다(`fullmatch`): 영상 ID 는 `VIDEO_ID_RE`, `viewCount` 는 ASCII 숫자
  1–19자의 글자, `publishedAt` 은 `YYYY-MM-DDTHH:MM:SS[.소수]Z` 만입니다. `publishedAt` 은
  `strptime` 으로 읽어 3.10 과 3.14 에서 똑같이 읽힙니다. 다른 시간대 표기는 건너뜁니다 — 날짜
  끝의 `+14:00` 같은 표기는 `Store.save` 의 UTC 바꾸기를 넘치게 합니다.
- 그 밖의 항목은 `SKIP video=<ID> reason=invalid_item|unavailable call=<search.list|videos.list>
  [keyword=…] [detail=…]` 로 건너뜁니다. `unavailable` 은 `videos.list` 답에 그 ID 가 없을
  때입니다.
- 저장소 쓰기 오류는 잡지 않고 `run_loop` 까지 올라갑니다(9절).

**로그 예시**

```
2026-10-12T21:00:00+09:00 DETECT video=abcdefghijk channel=UC123 keyword=썸 title="연락 텀 때문에 불안한 썸"
2026-10-12T21:00:00+09:00 VIEWS video=abcdefghijk views=1200 prev=- delta=-
2026-10-12T23:00:00+09:00 VIEWS video=abcdefghijk views=1450 prev=1200 delta=250
2026-10-12T23:00:00+09:00 QUOTA used=90 limit=90 call=search.list counter=searches keyword=이별
2026-10-12T21:00:00+09:00 QUOTA used=3 limit=3 call=search.list counter=pages keyword=연애
2026-10-12T23:00:00+09:00 ERROR where=search.list reason="HTTP 403 quotaExceeded" keyword=연애
2026-10-12T23:00:00+09:00 SKIP video=zyxwvutsrqp reason=unavailable call=videos.list
```

## 댓글 작성 — `writer.py` (Phase 5)

Phase 7 이 영상마다 부르는 모양:

```python
result = write_comment(record, config=config.comment, claude=anthropic_client(),
                       check=jev_self_check(sdk_ask, config.classifier.model), previous=store.comments(),
                       logbook=logbook, now=now, transcript="", top_comments=<top_comments 또는 ()>)
if result.draft is not None:
    record.comment = result.draft
    store.put(record)
```

- `WriteResult(draft, skip_reason)` 는 둘 중 정확히 하나를 담습니다(둘 다 있거나 둘 다 없으면
  `ValueError`). `write_comment` 는 `COMMENT` · `SKIP` · `ERROR` 줄을 직접 남기고 저장소는
  건드리지 않습니다 — 초안을 `record.comment` 에 넣고 `store.put` 하는 것은 Phase 7 의
  몫입니다.
- **주제 판별 문** — `record.classification` 이 없거나 `verdict` 가 `yes` 가 아니면
  `ValueError("주제 판별이 yes 인 영상에만 댓글을 씁니다: <영상 ID>")` 이고 Claude 를 부르지
  않습니다.
- **`claude` 포트** — `anthropic.Anthropic` 과 같은 모양
  (`messages.create(model=, max_tokens=, system=, tools=, tool_choice=, messages=)`).
  `anthropic_client(api_key=None)`
  가 실제 클라이언트를 만듭니다. `anthropic` 패키지는 이 함수 안에서만 가져오므로 테스트는 설치
  없이 돕니다. 제한 시간은 60초(`CLAUDE_TIMEOUT_S` — SDK 기본값 10분이면 한 줄로 도는 루프가
  멈춥니다)이고, 429/529 재시도는 SDK 기본값 그대로입니다. 모델 이름은 `comment.writer_model`
  (2절)에서 읽습니다. 작성 답은 도구 `submit_comment` 의 입력으로 받습니다(`tool_choice` 는
  `auto`, 도구는 `strict` — 모델이 도구 대신 글로 답하면 읽을 수 없는 답이라 다시 쓰기 한 번을
  씁니다). 다시 쓰기 차례는 첫 답의 블록(생각 · 글 · 도구 호출)을 통째로 되돌려 붙이고, 도구
  호출마다 `tool_result` 하나로 답합니다. 모델이 `auto` 에서 그 도구로 답하는지와 되돌려 붙인
  생각 블록을 받는지는 다음 진짜 실행이 처음 확인합니다.
- **`check` 포트** — `check(state, questions) -> {질문 이름: P(예)}`. 초안 한 개에 `noul` 질문
  다섯 개(`CHECK_QUESTIONS`: `mentions_scene` · `reads_like_ad` · `follows_concern` ·
  `concern_is_love_worry` · `saju_story_fits`)를 **한 요청**으로 묻습니다. 접속(키 `TYPESAFE_API_KEY` · jev 모델 · `typesafe-sdk`)은 Phase 3 의
  것이고, 운영은 `jev_self_check(sdk_ask, config.classifier.model)`(이 모듈)을 이 자리에 넘깁니다.
- **오류 이유의 상태 코드.** `claude 호출 실패: …` · `jev 검사 호출 실패: …` 의 머리는 `<예외 종류> <상태 코드>: <메시지>` 입니다 —
  상태 코드는 예외의 `status_code`, 없으면 `status` 이고, 둘 다 없으면 `<예외 종류>: <메시지>` 입니다. 운영의 jev 검사는
  `sdk_ask` 를 거치므로 SDK 실패가 `JevError: TypeSafeError 401` 처럼 상태 코드를 머리 가까이 싣습니다.
- **자료의 출처** — 자막은 공식 API 로 남의 영상에서 받을 수 없어 비어 있습니다.
  `captions.download` 는 OAuth 와 그 영상의 편집 권한(200단위)을 요구하고, 비공식 긁기는 약관 · 차단
  위험이라 이 저장소의 방법이 아닙니다. 그래서 `transcript` 는 늘 `""` 이고, 인기 댓글은 탐지 절의
  `YouTubeClient.top_comments(video_id, now, limits, TOP_COMMENTS_MAX)` 가 가져옵니다. 댓글이 막힌
  영상(`None`)은 `top_comments=()` 로 제목 · 설명만 씁니다.

**흐름** — 시도마다(최대 두 번):

1. Claude 가 도구 `submit_comment` 로 답합니다 — `has_love_concern` · `has_scene`(JSON 참거짓)과,
   둘 다 참이면 `concern`(고민 한 줄) · `comment`(댓글). 도구 블록이 없거나 모양이 다르면 jev 를
   부르지 않고 그 시도는 `답을 읽을 수 없습니다` 로 떨어집니다. 글 블록이 함께 와도 도구 블록이
   답이고, 네 칸 밖의 키가 있어도 네 칸으로 읽습니다.
2. **스스로 건너뜀** — `has_love_concern` 이 거짓이면 `재료에 연애 고민 없음`, 고민은 참이고
   `has_scene` 이 거짓이면 `재료에 장면 없음` 입니다. jev 를 부르지 않고 다시 쓰지 않으며 바로
   `SKIP reason="<그 이유>"` 입니다(두 번째 시도의 답이면 `"<그 이유> — 1차: <1차 이유>"`).
   건너뜀 답에서 읽는 것은 두 참거짓뿐입니다.
3. jev 자체 검사.
4. 코드 검사 — 글자 수 · 링크 · 반복 · 문장 틀을 **모두** 돌립니다(코드가 마지막).

떨어진 이유(jev 이유가 먼저, 코드 이유는 위 순서)를 모두 `; ` 로 이어 다시 쓰기 이유 하나로
만들고, 원래 답에 도구 호출이 있으면 그 호출(assistant)과 그 호출의 `tool_result` 로 붙인
`REWRITE_PROMPT`(user)를, 없으면 원래 글과 `REWRITE_PROMPT` 를 같은 대화에 붙여 한 번 다시
씁니다. 두 번째도 떨어지면 `SKIP reason="검사 두 번 탈락 — 1차: … / 2차: …"` 입니다. 통과하면
`COMMENT` 를 남기고 초안을 돌려줍니다.

| 검사 | 통과 규칙 | 떨어질 때 이유 |
|---|---|---|
| 답 읽기 | 도구 `submit_comment` 입력 — 두 참거짓, 둘 다 참이면 `concern` · `comment` 가 비어 있지 않은 글자 | `답을 읽을 수 없습니다` |
| jev 자체 검사 | 질문마다 점수 + `_TOLERANCE` ≥ `check_min_probability` | `자체 검사 미달 — <이름표> <P(예)>, …` |
| 글자 수 | `min_chars` ≤ 글자 수 ≤ `max_chars` | `글자 수 <n>자 — <min>–<max>자여야 합니다` |
| 링크 | 링크 보기에 `_LINK_RE` 조각이 없음 | `링크·주소 모양이 들어 있습니다: <조각>` |
| 반복 | 최근 댓글과 같지 않고, 겹친 연속 글자 < 12 | `이전 댓글과 겹칩니다: <겹친 글자>` |
| 문장 틀 | 최근 댓글과 같은 6글자 조각이 없음('연애사주' 에 걸친 조각은 빼고) | `이전 댓글과 문장 틀이 같습니다: <조각>` |

- 이름표(`CHECK_LABELS`)는 `영상 속 장면·말 언급` · `광고처럼 읽힘` · `영상 고민과 이어짐` ·
  `고민 한 줄이 연애 고민` · `연애사주 경험이 고민과 이어짐` 이고, 확률은 소수 둘째
  자리입니다(`자체 검사 미달 — 영상 속 장면·말 언급 0.25`).
- **하한 비교** — 점수는 `mentions_scene` · `follows_concern` · `concern_is_love_worry` ·
  `saju_story_fits` 가 P(예), `reads_like_ad` 는 1 − P(예)입니다. jev 는 부정을 글자 그대로 읽으므로 광고 질문은 긍정으로 묻고 뒤집습니다.
  `score + _TOLERANCE < check_min_probability` 이면 떨어집니다(`_TOLERANCE = 1e-9`). 그냥 `<`
  로 비교하면 1 − P 의 부동소수 오차(`1 - 0.9 = 0.0999…98`) 때문에 두 자리 하한 99개 중 20개에서
  "하한과 같으면 통과" 가 깨집니다.
- **글자 수** — NFC 로 맞춘 댓글의 `len()`, 곧 코드 포인트 수이지 바이트가 아닙니다.
  `read_reply` 가 댓글을 NFC 로 맞추고 앞뒤 공백을 떼며, 고민은 한 줄로 모읍니다.
  서로게이트(U+D800–U+DFFF)가 든 고민 · 댓글은 읽을 수 없는 답으로 보아 다시 씁니다.
- **링크** — 링크 보기는 NFKC + casefold 한 글에서 글자 · 숫자(`isalnum`, 한글 포함)와 `@` 는
  그대로, 유니코드 이름에 `FULL STOP`/`DOT` 이 든 글자는 `.`, `SOLIDUS`/`SLASH` 는 `/`,
  `COLON` 은 `:` 로 남기고, 나머지(공백 · 괄호 · 보이지 않는 글자 · 다른 문장부호)는 모두
  버립니다. 링크는 `_LINK_RE` — `[^\W_]\.+[a-z]{2,}|@[^\W_]|:/|[0-9]{1,3}(?:\.[0-9]{1,3}){3}`,
  곧 글자 뒤 점 뒤 영문(호스트와 끝) · `@이름` · 스킴 · IPv4 입니다. 그래서 `연애사주.com` ·
  `naver . me` · `ｎａｖｅｒ．ｍｅ` · `naver[.]com` · `youtu·be` · 보이지 않는 글자로 가른 주소도
  걸리고, `1.5배` · `10:30` · `P.S. 저도` · `A/S` · `장면·말` · `봤는데, MBTI랑` 은 지나갑니다.
  - 받아들인 오탐: `좋았어요. MBTI도` 는 `요.mbti` 로 걸려 다시 쓰기 하나를 치릅니다(막는 쪽).
  - 남은 틈: 한글 끝(`연애사주.한국` · `saju.한국` 등)은 호스트 글자와 상관없이 문장 끊김과
    구분할 수 없어 코드 검사에서 빠지고, 광고 질문에 맡깁니다.
- **반복** — 두 글을 NFKC + casefold 한 뒤 `isalnum` 글자만 남겨 비교합니다. 최근 댓글과
  같거나, `difflib.SequenceMatcher(autojunk=False)` 로 찾은 가장 긴 연속 공통 글자가
  `REPEAT_MIN_CHARS`(12, 코드 상수) 이상이면 반복입니다. 비교 대상은 `previous` 의 마지막
  `RECENT_WINDOW`(20)개 — Claude 가 `<my_previous_comments>` 에서 보는 바로 그 댓글들입니다.
- **문장 틀** — 두 글을 반복과 같이 맞춘 뒤(NFKC + casefold, `isalnum` 글자만) 최근 댓글 하나와
  `FRAME_MIN_CHARS`(6, 코드 상수) 글자 조각이 하나라도 같으면 같은 문장 틀입니다. '연애사주'
  (`REQUIRED_WORD`, 과제가 반드시 넣으라는 낱말)에 걸친 조각은 문장 틀로 세지 않습니다 — 그래서
  `연애 사주` · `연애사주를 봤을 때` 만 겹치면 지나가고, `뜨끔했어요. 저도` 처럼 문장을 잇는 6글자
  조각이 겹치면 걸립니다. 이 검사가 잡는 것은 6글자 이상 같은 이음 조각입니다 — 6D 초안 11개 가운데
  이 검사가 잡는 것은 2개(`뜨끔했어요. 저도` 한 쌍)이고, 나머지가 나눈 두 문장 뼈대('[반응]어요. 저도
  … 연애사주를 봤을 때 … 말을 듣고 …')처럼 '연애사주' 에 걸친 조각과 6글자보다 짧은 이음으로 겹치는
  꼴은 지나갑니다. 그 몫은 프롬프트 규칙 6 입니다. 비교 대상은 반복과 같은 `RECENT_WINDOW`(20)
  개입니다. `FRAME_MIN_CHARS` 는 잰 값이 아닙니다 — 실행기는 한 실행에서 앞서 통과한 초안(몇 개)과만
  비교해 20개 창에서 얼마나 막는지 잴 수 없고, 운영(Phase 7)의 기록이 처음 잽니다. 실행기의 과제
  품질 ⓒ(`frame_overlap`)는 공백만 빼고 '연애사주' 조각도 세는 기록이라 이 검사와 다른 셈입니다.
- **잰 값 (Phase 6F).** `docs/live-check/result.json` 에서 읽은 숫자입니다('주제 판별' 절의 기록과 같은
  실행). 6E 가 고친 작성기의 숫자라 '6E 뒤' 기록입니다(트래커 Phase 6F 의 사람 실행 뒤 인터뷰 — '6F 예외로 착지').
  - 모델 이름: claude-sonnet-5-5 accepted · claude-haiku-5-5 accepted — 작성 claude-sonnet-5-5 · 채점 claude-haiku-5-5
  - `comment.writer_model` 은 `claude-sonnet-5-5` 그대로입니다 — 설정한 이름이 `accepted` 입니다.
  - 초안 운영 창: 쓴 영상 7 · SKIP 6 · 초안 2 · 정답 있음 2 (사람 칸 0 · Claude 채점 2) · 정답 ok 1 · 정답 bad 1 · 채점 오류 0 · 사람 칸과 Claude 채점이 다름 0 · 정답 bad 인데 통과 0 · 정답 ok 인데 탈락 0
  - 초안 넓힌 창: 쓴 영상 6 · SKIP 2 · 초안 9 · 정답 있음 9 (사람 칸 2 · Claude 채점 9) · 정답 ok 6 · 정답 bad 3 · 채점 오류 0 · 사람 칸과 Claude 채점이 다름 2 · 정답 bad 인데 통과 0 · 정답 ok 인데 탈락 1
  - 정답 있고 자체 검사를 통과한 초안 6(사람 칸 2) 가운데 정답 bad 가 0 이라 `check_min_probability` 는 0.7 그대로입니다(근거가 있어 그대로).
  - 정답은 사람 칸(`ok` · `bad`)이 있으면 그것, 없으면 Claude 채점 다섯 칸입니다 — 초안 채점 세
    칸(`claude_grade`: 장면 · 광고 · 고민 이음)과 과제 품질 ⓐ · ⓑ(`task_quality`) 가운데 하나라도
    나쁨이면 `bad`, 다섯이 모두 좋음이면 `ok`, 그 밖은 정답 없음입니다(트래커 Phase 6F — 6D 드리프트
    인터뷰 질문 3 A). Claude 채점은 또 하나의 AI 의견이라, 그 정답에 맞춰 옮긴 통과선은 단단하지 못합니다.
  - 6D 의 기록은 세 칸(`claude_grade` 만) 정답이라 `ok` · `bad` 수의 정의가 이 기록과 다릅니다 — 전후는
    아래 과제 품질 칸으로 견줍니다.
  - 통과선은 올리기만 하고 내리지 않습니다 — 정답이 `bad` 인데 jev 자체 검사를 통과한 초안이 있으면 초안
    `scores` 의 비교 점수(6E 뒤 결과는 다섯 — 장면 · 고민 이음 · 연애 고민 · 연애사주 이음은 P(예), 광고는
    1 − P(예)) 가운데 가장 낮은 것 + 0.05 로 올리고, 그런 초안이 여럿이면 초안마다 가장 낮은 비교 점수 중
    가장 높은 값 + 0.05 로 올리며, 그 값이 1 을 넘으면 고치지 않고 사람에게 넘깁니다, 정답이 `ok` 인데 자체
    검사에서 떨어진 초안은 숫자만 위에 적습니다. 내리는 쪽은 사람이 정합니다.
  - 알려진 한계 — jev 다섯 질문이 통과선 하나를 나눠 쓰므로(`src/agent/writer.py (self_check_failure)`), 올림은 막을 초안의 가장 낮은 비교 점수 + 0.05 이고 그 초안이 나쁨을 받은 질문과 상관없습니다.
    6D 에서 한 번(나쁨은 '고민 이음' · 그 질문의 jev 점수 0.90 · 올림은 '장면' 0.71 → 0.76), Phase 6F 의 실행에서 다시(아래 '사람 칸을 비우면' 줄) 일어났고, 두 번 다 사람 칸이 올림을 막았습니다.
    Phase 6F 의 사람 칸 둘(아래 줄의 두 초안 — 서로 다른 두 영상)은 실행 뒤 사람이 두 초안을 원문 · 재료와 함께 읽고 `ok` 로 적은 값입니다(커밋 `36ded73`).
    '나쁨' 은 Claude 채점 다섯 칸 가운데 나쁘다고 본 칸이고, 이름표는 `CHECK_LABELS` 입니다(광고의 비교 점수는 '아님' — 1 − P(예)).
    이 줄들은 기록이고 규칙은 그대로입니다(트래커 Phase 6F 보류 문 인터뷰 질문 3 A).
    - 사람 칸을 비우면: 정답 bad 인데 자체 검사를 통과한 초안 2 · 다시 셈 0.87 — 넓힌 창 om-TAoBO0Rc 시도 1(나쁨: 고민 한 줄이 연애 고민 / 가장 낮은 비교 점수: 광고처럼 읽힘 아님 0.74 → 0.79) · 넓힌 창 nPMEi5NDSnU 시도 2(나쁨: 영상 고민과 이어짐 / 가장 낮은 비교 점수: 광고처럼 읽힘 아님 0.82 → 0.87)
    - 가장 낮은 비교 점수의 질문: 초안 11 가운데 영상 속 장면·말 언급 3 · 광고처럼 읽힘 아님 7 · 영상 고민과 이어짐 0 · 고민 한 줄이 연애 고민 0 · 연애사주 경험이 고민과 이어짐 1
  - `REPEAT_MIN_CHARS`(12) 는 그대로입니다 — 표본 부족: 최근 내 댓글 20개끼리 비교하는 값이라 초안 약
    10개짜리 한 바퀴로는 잴 수 없습니다.
  - 과제 품질 운영 창: ⓐ 고민 한 줄이 연애 고민 1/2 · ⓑ 연애사주 경험이 고민과 이어짐 1/2 · 과제 칸 오류 0 · ⓒ 다른 영상 초안과 겹치는 6글자 조각이 있는 초안 1/2 · 겹친 조각 최다 7
  - 과제 품질 넓힌 창: ⓐ 고민 한 줄이 연애 고민 7/9 · ⓑ 연애사주 경험이 고민과 이어짐 6/9 · 과제 칸 오류 0 · ⓒ 다른 영상 초안과 겹치는 6글자 조각이 있는 초안 6/9 · 겹친 조각 최다 10
  - 인기 댓글 운영 창: 재료 초안 2 · 항목은 왔는데 글 0개인 영상 0
  - 인기 댓글 넓힌 창: 재료 초안 5 · 항목은 왔는데 글 0개인 영상 0
  - 과제 품질 ⓒ · 과제 칸 오류 · 인기 댓글 숫자는 기록입니다 — 통과선은 이 숫자로 움직이지 않습니다(트래커 Phase 6C 질문 1 A). 과제 품질 ⓐ · ⓑ 는 위 정답 다섯 칸에 들어 통과선을 움직입니다(트래커 Phase 6F — 6D 드리프트 인터뷰 질문 3 A).
  - 과제 품질 전후 — 6E 전(Phase 6D 의 실행 `2026-10-14T14:09:02.882902+00:00`, 6D 가 이 절에 적은 기록) → 6E 뒤(이번 실행 `2026-10-15T08:42:22.401654+00:00`)입니다. 전후는 과제 품질 세 칸으로 견주고, Phase 8 의 PROCESS.md '실패와 개선' 이 이 줄을 인용합니다(트래커 Phase 6F).
    - 과제 품질 전후 운영 창: ⓐ 고민 한 줄이 연애 고민 4/11 → 1/2 · ⓑ 연애사주 경험이 고민과 이어짐 4/11 → 1/2 · ⓒ 다른 영상 초안과 겹치는 6글자 조각이 있는 초안 10/11 → 1/2
    - 과제 품질 전후 넓힌 창: ⓐ 고민 한 줄이 연애 고민 실행 없음 → 7/9 · ⓑ 연애사주 경험이 고민과 이어짐 실행 없음 → 6/9 · ⓒ 다른 영상 초안과 겹치는 6글자 조각이 있는 초안 실행 없음 → 6/9
    - 초안 수는 운영 창 11 → 2 · 넓힌 창 실행 없음 → 9 라 전후 차이는 표본 안의 우연일 수 있습니다 — 두 실행의 창 비율이 달라 ⓐ · ⓑ 는 창마다 따로 견줍니다
    - ⓒ 는 초안마다 실행 전체의 다른 영상 초안과 겹친 조각을 센 칸(`frame_overlap`)이라 창 줄의 ⓒ 는 그 셈을 창으로 나눈 것입니다 — 6D 는 운영 창 하나뿐인 실행이라 실행 전체로 견주면 10/11 → 7/11 입니다(6F 는 연락처 모양을 가린 글로, 6D 는 가리기 전 글로 셌습니다 — Phase 6G)
    - 재료에 연애 고민이 없다고 보고 초안 없이 건너뛴 영상은 운영 창 3 · 넓힌 창 1 이고, 이 영상들은 ⓐ · ⓑ · ⓒ 의 분모 밖입니다 — ⓐ 와 같은 것(고민이 연애 고민인지)을 보고 거른 것이라 ⓐ 의 전후 차이에는 이 거름이 섞여 있을 수 있습니다
  - 정당한 건너뜀 운영 창: 재료에 장면 없음 3/3 · 재료에 연애 고민 없음 2/3 · 정답 없음 0 · 검사 두 번 탈락 0
  - 정당한 건너뜀 넓힌 창: 재료에 장면 없음 0/0 · 재료에 연애 고민 없음 1/1 · 정답 없음 0 · 검사 두 번 탈락 1
  - '정당한 건너뜀' 은 작성기가 스스로 건너뛴 영상을 이유별로 센 정당 수/그 이유로 건너뛴 수입니다. 정답은 사람 칸(`skip_human` 의 `정당` · `부당`)이 있으면 그것, 없으면 건너뜀 채점(`skip_grade`)에서 그 이유의 칸(장면 없음은 `material_has_scene`, 연애 고민 없음은 `material_has_love_worry`)이 거짓이면 정당 · 참이면 부당이고, 채점이 없으면(오류) 정답 없음입니다 — 빈 사람 칸은 동의가 아닙니다.
    재료 채점은 제목도 장면 출처로 세어, 제목만 장면 출처인 영상은 부당 쪽으로 기웁니다. 검사 두 번 탈락은 스스로 건너뜀이 아니라 수만 적습니다.
    이 숫자는 기록이고, 판정 줄과 통과선은 이 숫자로 움직이지 않습니다(트래커 Phase 6E 질문 2 A · 3 A).
- **자료** — 태그 블록 `<video_title>` · `<video_description>` · `<transcript>`(자막이 비었으면
  대신 `<top_comments>` — 비어 있지 않은 인기 댓글 앞 10개) · `<classification>` ·
  `<my_previous_comments>`(최근 댓글이 있을 때만). 시스템 프롬프트가 태그 안의 글을 지시가 아닌
  자료로 선언하고, 자료의 `<` `>` 는 `＜` `＞` 로 바꿔 태그를 닫지 못하게 합니다. 자르는 길이는
  제목 300 · 설명 2000 · 자막 6000자, 인기 댓글 · 판별 이유 · 이전 댓글 · 검사용 고민과 초안
  각 300자입니다. jev 상태는 같은 자료 블록에 `<video_concern>` · `<draft_comment>` 를 더한
  것입니다.
- **API 오류** — Claude 호출이나 jev 호출이 오류를 내거나 jev 답이 이상하면 다시 쓰지 않고(다시
  써도 고쳐지지 않음) `ERROR where=writer.claude` 또는 `where=writer.jev` 와, 같은 이유의
  `SKIP` 을 남깁니다:
  - `claude 호출 실패: <오류 종류>[ <상태 코드>][: <메시지 200자까지>]` (상태 코드는 있을 때만,
    메시지가 비면 `: …` 도 뺍니다)
  - `jev 검사 호출 실패: <오류 종류>[ <상태 코드>][: <메시지 200자까지>]` (상태 코드는 있을 때만,
    메시지가 비면 `: …` 도 뺍니다; Claude 틀과 같음)
  - `jev 검사 응답 이상: <질문 이름>` — 묶음이 아니거나, 질문이 빠졌거나, 값이 bool · 숫자
    아님 · 0–1 밖(NaN 포함)

  잘못된 모델 이름 · 취소된 키 · 크레딧 없음 · jev 포트 모양 불일치 같은 영구 오류도 이렇게
  원인과 함께 `ERROR` 로 보입니다. 그 `ERROR` 위에 멈춤 정책을 세우는 것은 Phase 7 의
  몫입니다. `try` 안에는 `messages.create` 와 `check` 호출만 있으므로, 모양이 틀린 Claude
  응답(작성기 버그)은 건너뛰기로 숨지 않고 그대로 오류가 됩니다.
- **로그** — `COMMENT` 는 필수 필드 뒤에 `attempt`(1 또는 2)와
  `check`(`mentions_scene=0.90 reads_like_ad=0.10 follows_concern=0.80 concern_is_love_worry=0.85
  saju_story_fits=0.75`)를 더합니다(7절의 "나머지 필드").
- **`self_check`** — 초안의 `self_check` 는 `Judgement(yes, "<질문>=<P(예)> …", now)` 입니다.
  `CommentDraft.at` 도 넘겨받은 `now` 이고, 숨은 시계는 없습니다.
- 프롬프트 원문(`SYSTEM_PROMPT` · `USER_INSTRUCTION` · `REWRITE_PROMPT` · `WRITE_TOOL` ·
  `CHECK_QUESTIONS` · `CHECK_LABELS`)은 `writer.py` 맨 위에만 있고, Phase 8 의 PROCESS.md 가 옮겨
  적습니다.
- **과제 문장 대조표 (Phase 6E).** 과제 안내 4쪽 ④ 여덟 문장과 7쪽 평가표 '댓글 품질' 세 문장마다 게시
  전에 막는 자리와 짝 테스트입니다(문장은 트래커 Phase 6E 인터뷰 질문 1 A 가 옮긴 원문). 스위트
  테스트(`tests/test_task_table.py`)가 열한 문장이 표에 하나씩 있는지, 표의 규칙 번호 · jev 질문 · 코드
  검사 · 스스로 건너뜀 · 짝 테스트 이름이 실제로 있는지, 칸이 비지 않았는지 봅니다 — 막는 자리가 없거나
  일부만 막는 행은 '막지 않음' 칸에 그 몫과 이유를 적습니다. 표는 막는 자리가 있는지만 지키고, 그 검사가
  잘 판단하는지는 실제 실행이 잽니다.

  | 번호 | 과제 문장 | 프롬프트 규칙 | jev 질문 | 코드 검사 | 스스로 건너뜀 | 짝 테스트 | 막지 않음 |
  |---|---|---|---|---|---|---|---|
  | ④-1 | 자막(없으면 제목·설명)과 인기 댓글을 읽고 | 규칙 7 | — | — | — | `tests/test_writer.py::test_transcript_replaces_top_comments` | 자막 — 공식 API 로 남의 영상 자막을 받을 수 없어 `transcript` 는 늘 비어 있습니다(트래커 Phase 6A); 제목 · 설명 · 인기 댓글은 자료 블록으로 넣습니다 |
  | ④-2 | 영상이 다루는 연애 고민을 먼저 한 줄로 정리 | 규칙 1 | `concern_is_love_worry` | — | `재료에 연애 고민 없음` | `tests/test_writer.py::test_new_questions_below_threshold_rewrite` · `tests/test_writer.py::test_no_concern_answer_skips_without_jev` | — |
  | ④-3 | 그 고민과 연결해 '비슷한 고민이 있었을 때 연애사주를 봤던 경험'을 담은 댓글 … 자연스럽게 이어지는 형태 | 규칙 2 | `saju_story_fits` · `follows_concern` | — | — | `tests/test_writer.py::test_new_questions_below_threshold_rewrite` · `tests/test_writer.py::test_each_question_can_fail_alone` | — |
  | ④-4 | 40 ~ 120자 | 규칙 4 | — | `min_chars` · `max_chars` | — | `tests/test_writer.py::test_length_bounds_come_from_config` | — |
  | ④-5 | 영상 속 구체적인 장면이나 말을 하나 이상 언급 | 규칙 3 | `mentions_scene` | — | `재료에 장면 없음` | `tests/test_writer.py::test_self_check_below_threshold_rewrites_once` · `tests/test_writer.py::test_no_scene_answer_skips_without_jev` | — |
  | ④-6 | 링크 금지 | 규칙 5 | — | `link_fragment` | — | `tests/test_writer.py::test_link_shapes_are_rejected` | — |
  | ④-7 | 이전 댓글과 같은 문장 반복 금지 | 규칙 6 | — | `repeated_run` · `shared_frame` | — | `tests/test_writer.py::test_repeated_sentence_inside_new_comment_is_found` · `tests/test_writer.py::test_frame_piece_shared_with_recent_comment_fails` · `tests/test_writer.py::test_six_d_skeleton_pair_is_not_caught` | 두 문장 뼈대만 같은 꼴 — '연애사주' 에 걸친 조각과 6글자보다 짧은 이음은 문장 틀로 세지 않아 프롬프트 규칙 6 에 맡깁니다 |
  | ④-8 | 영상 내용과 댓글이 잘 맞는지 AI가 다시 검사하는 단계를 두면 가점 | — | `mentions_scene` · `follows_concern` | — | — | `tests/test_writer.py::test_check_request_holds_five_questions_concern_and_draft` | — |
  | 평가-1 | 영상 속 고민을 정확히 짚고 | 규칙 1 | `concern_is_love_worry` · `follows_concern` | — | `재료에 연애 고민 없음` | `tests/test_writer.py::test_each_question_can_fail_alone` · `tests/test_writer.py::test_no_concern_answer_skips_without_jev` | — |
  | 평가-2 | 연애사주 경험과 자연스럽게 연결되는가 | 규칙 2 | `saju_story_fits` | — | — | `tests/test_writer.py::test_each_question_can_fail_alone` | — |
  | 평가-3 | 영상마다 다르게 쓰이는가 | 규칙 6 | — | `repeated_run` · `shared_frame` | — | `tests/test_writer.py::test_frame_piece_shared_with_recent_comment_fails` · `tests/test_writer.py::test_required_word_pieces_are_not_frames` · `tests/test_writer.py::test_six_d_skeleton_pair_is_not_caught` | 두 문장 뼈대만 같은 꼴 — '연애사주' 에 걸친 조각과 6글자보다 짧은 이음은 문장 틀로 세지 않아 프롬프트 규칙 6 에 맡깁니다 |

## 트리거 판정 — `trigger.py`

```python
judge_trigger(record, config, now) -> Judgement     # config 는 Config.trigger
views_per_hour(record) -> float | None             # TRIGGER per_hour — 판정과 같은 두 기록 사이, 잴 수 없으면 None
```

`judge_trigger` 는 영상 기록 하나를 지금(`now`) 댓글 대상으로 볼지 정해 `Judgement(verdict, reason, at=now)` 를
돌려줍니다. 기록은 바꾸지 않고, 같은 입력이면 언제나 같은 판정입니다. 기준은 부를 때마다 받은 `config` 에서
읽으므로 실행 중 고친 설정이 다음 판정부터 적용됩니다. 시간대 없는 `now` 는 `ValueError` 입니다. 저장
(`record.trigger`)과 `TRIGGER` 로그는 부르는 쪽(Phase 7)이 합니다.

- **최신과 직전:** 조회수 기록을 시각(`at`) 순으로 놓습니다 — 목록 순서는 보지 않고, 시간대가 달라도 같은
  순간이면 같은 시각이며, 같은 시각끼리는 조회수가 큰 쪽이 뒤입니다. 맨 뒤가 *최신*, 최신보다 최소 간격(10분) 이상
  앞선 기록 중 맨 뒤가 *직전*입니다 — 정확히 10분 앞선 기록은 직전이 되고, 그보다 가까운 기록(같은 시각 포함)은 건너뜁니다.
  그런 기록이 없으면 직전은 업로드 시각(`published_at`)의 조회수 0 이고, 이 짝에는 간격을 따지지 않습니다(2026-10-15 질문 3 B · 7G 질문 1 A).
  간격도 순간으로 잽니다(시간대가 달라도 같은 순간이면 같은 시각).
- **시간당 조회수** = (최신 조회수 − 직전 조회수) ÷ 두 시각 사이의 시간. 조회수가 그대로면 0 입니다.
  조회수가 줄었으면(삭제 · 비공개 · 조회수 정정) 재지 않습니다 — 음수 속도는 없습니다.

아래 차례대로 보고 처음 걸린 줄의 판정을 돌려줍니다:

| 차례 | 조건 | verdict | reason |
|---|---|---|---|
| 1 | 기록이 없음, 또는 최신보다 10분 이상 앞선 기록이 없고 업로드 시각이 최신 기록보다 앞이 아님(나이 0 · 미래 업로드) | `hold` | `too_few_samples` |
| 2 | 최신 조회수 < `min_views` | `no` | `views_below_min` |
| 3 | 최신 조회수 > `max_views` | `no` | `views_above_max` |
| 4 | `published_at` 이 `now` 보다 뒤 | `hold` | `published_in_future` |
| 5 | `now − published_at` > `max_age_hours` 시간 | `no` | `too_old` |
| 6 | 최신 조회수 < 직전 조회수 | `hold` | `views_decreased` |
| 7 | 시간당 조회수 < `min_views_per_hour` | `no` | `too_slow` |
| 8 | 그 밖 — 세 조건을 모두 만족 | `yes` | `views_per_hour` |

- 경계는 모두 통과입니다 — 조회수 정확히 `min_views` · `max_views`, 나이 정확히 `max_age_hours`(그리고
  `published_at` 이 `now` 와 같은 나이 0), 시간당 정확히 `min_views_per_hour` 는 대상입니다(과제의
  "1,000–5,000 · 12시간 이내 · 150 이상").
- 건너뛴 기록(최신보다 10분 안)은 판정 어디에도 쓰지 않습니다 — 줄어든 조회수(차례 6)도 최신과 직전 두 기록으로 봅니다.
- **판정은 모두 `at` 시각의 판정입니다.** 나이 창이 닫힌 영상(`now − published_at` > `max_age_hours`)은 이유와 상관없이
  다시 `yes` 가 되지 못합니다 — 조회수 검사가 나이 검사보다 앞이라 `views_below_min` · `views_above_max` 로 남기도 합니다.
  줄어든 조회수가 `min_views` 아래면 `hold views_decreased` 가 아니라 `no views_below_min` 입니다.
  설정의 `max_age_hours` 를 늘리면 `too_old` 도 바뀝니다.
  탐지기는 나이 창 밖 영상의 조회수를 더 재지 않으므로(명단 영상 제외 — 탐지 절) 그런 영상은 다시 판정되지 않습니다.
  `hold` 는 잴 수 없어 미룬 판정(기록 부족 · 미래 업로드 시각 · 줄어든 조회수)이고, `no` 는 재어 보니 지금은 아닌 판정입니다.
- 최신보다 10분 이상 앞선 기록이 없는 영상(처음 본 사이클 · 재시작 직후)은 업로드 시각의 조회수 0 을 직전 기록으로 쳐 판정합니다(2026-10-15
  질문 3 B — 트래커 Phase 4 의 절충을 바꿈 · 7G 질문 1 A). 업로드 시각이 최신 기록보다 앞이 아니면(나이 0 · 미래 업로드) 잴 시간이 없어
  `hold too_few_samples` 입니다.
  조회수가 범위(`min_views`–`max_views`) 안에서 직전보다 줄고 나이 창 안이면 `min_views_per_hour` 가 0 이어도 `hold views_decreased` 입니다 —
  최신과 직전 사이에서 줄어든 영상(지워졌거나 비공개가 된 영상)을 대상으로 올리지 않습니다. 줄어든 조회수가 범위 밖이면 `no views_below_min` · `no views_above_max`,
  나이 창이 닫혔으면 `no too_old` 입니다(표의 차례).
- 나이는 업로드 시각(`published_at`)부터 잽니다(탐지 시각이 아님). `published_at` 이 `now` 보다 뒤이면 이
  컴퓨터의 시계가 유튜브보다 늦다는 뜻이라 `hold published_in_future` 로 둡니다 — 시계가 따라잡으면 저절로
  풀리고, 로그에서 찾을 수 있습니다. 시계가 늦으면 다른 영상의 나이도 그만큼 적게 재지만, 이 판정이 그것까지
  고치지는 않습니다.
- **최소 간격 10분**(2026-10-15 7G 질문 1 A · 2 A): 재시작 직후 바로 도는 사이클이나 잇단 `--once` 의 기록은 앞 기록과 몇 초 사이라,
  그대로 재면 20초 사이 1회가 시간당 180회로 `yes` 였습니다. 그래서 10분보다 가까운 앞 기록은 건너뛰고 더 앞 기록(없으면 업로드 0)과
  잽니다. 두 기록 사이의 1회 차이는 시간당 최대 6 입니다 — 업로드 0 짝에는 간격이 없어 업로드 10분 안의 영상은 그보다 크게 흔들립니다.
  주기 10분 이상(기본 120 · 과제 예시 30)은 평소 판정이 전과 같고, 주기를 10분 밑으로 두면 두 기록 사이 구간이 늘 10분 이상입니다.
  간격은 설정 키가 아니라 `trigger.py` 상수(`_MIN_GAP`)라 바꾸려면 코드를 고칩니다. 기록 주기(30분 · 2시간)에 따라 정밀도가 달라지는 것은 트래커가 받아들인 절충입니다.
- 조건 차례는 과제가 적은 차례(조회수 · 나이 · 시간당 조회수)이고, 두 `hold`(미래 업로드 시각 · 줄어든
  조회수)는 그것이 망치는 측정만 막습니다.
- reason 은 모두 로그에 따옴표 없이 쓰이는 글자입니다. 3절 · 7절 예시의 `views_per_hour` 는 `yes` 의
  reason 입니다.
- **기준 제안:** 세 기준 값은 과제 값 그대로 둡니다(트래커 Phase 4 결정) — 실제 조회수 기록(Phase 2)이 아직
  없어 다른 숫자를 뒷받침할 근거가 없습니다. 대신 과제가 정하지 않은 재는 방법을 정했습니다: 시간당 조회수는 *최신과, 최신보다
  10분 이상 앞선 가장 늦은 기록* 사이로 잽니다. 그런 앞 기록이 없는 판정(첫 판정 · 재시작 직후)만 업로드 뒤 평균(조회수 ÷ 나이)입니다 — 120분 주기에서는 둘째 기록이
  2시간 뒤라 빨리 뜨는 영상이 둘째 판정 전에 5,000 을 넘어 대부분 놓쳤습니다(2026-10-15 질문 3 B).
  첫 판정의 업로드 뒤 평균은 이미 끝난 반짝 증가를 대상으로 올리기도 하지만, 12시간 안 영상이라 지금 속도와 크게 다르지 않다는 쪽에 겁니다.
  둘째 판정부터는 첫 기록부터의 평균을 쓰지 않습니다 — 지금의 가속을 느린 시작과 섞어 묽히기 때문입니다.
- 음성 대조 — 각 명령은 판정 한 줄을 메모리에서만 망가뜨리고 `tests.test_trigger` 를 돌리며, **종료 코드
  1(테스트가 잡음)** 이어야 합니다. `judge_trigger` 의 본문을 고칠 때 함께 확인합니다:

  ```
  python3 -m tests.mutants trigger-negative-speed
  python3 -m tests.mutants trigger-flat-is-decrease
  python3 -m tests.mutants trigger-list-order
  python3 -m tests.mutants trigger-same-instant
  python3 -m tests.mutants trigger-min-views-exclusive
  python3 -m tests.mutants trigger-max-views-exclusive
  python3 -m tests.mutants trigger-future-publish-passes
  python3 -m tests.mutants trigger-future-publish-inclusive
  python3 -m tests.mutants trigger-age-exclusive
  python3 -m tests.mutants trigger-rate-exclusive
  python3 -m tests.mutants trigger-gap-ignored
  python3 -m tests.mutants trigger-gap-exclusive
  python3 -m tests.mutants trigger-gap-wall-clock
  ```

## 주제 판별 — `classifier.py` (Phase 3)

- **부르기.**

  ```python
  classify(record, config, ask, now, *, transcript=None, language=QUESTION_LANGUAGE) -> Judgement
  ```

  자막은 `transcript` 인자로만 받습니다.
  자막은 공식 API 로 남의 영상에서 받을 수 없어 비어 있습니다 — 운영과 실제 호출 실행기는 `transcript=None` 으로 부릅니다.
- **부르는 쪽의 할 일.** 판정마다 `CLASSIFY video=… verdict=… reason=…` 를 씁니다. 오류
  보류(`is_error_hold(j)` 가 참)이면 `ERROR where=classify reason=<j.reason>` 도 함께 씁니다.
  운영(`run.py`)은 오류 보류를 `record.classification` 에 저장하지 않고, 그 영상에 새 조회수 기록이 붙는 다음 사이클에
  다시 판정합니다(트래커 Phase 7: 실패 후 재시도 없이 다음 영상 — '실행 진입점 — run.py' 절).
- **보류가 되는 실패.** SDK 가 알린 실패만 보류입니다 — 모든 `TypeSafeError`, 곧 401 · 422 ·
  429 · 529 · 연결 · 응답 검증. 429/529 의 다시 시도는 SDK 기본 정책을 따릅니다. 우리 코드가 잘못된 경우는
  예외가 그대로 올라갑니다 — 운영(`run.py`)에서는 영상마다 울타리가 `ERROR where=run.classify` 로 받습니다.
  SDK 가 없으면 운영은 켜지지 않습니다(종료 코드 2, '실행 진입점 — run.py' 절).
- **한 요청, 두 질문.** `matches_topic`(noul)과 `reason`(choice). choice 가 첫 보기 쪽으로
  기우는 경향 때문에 보기는 `off_topic_reasons` 를 먼저, 그다음 `on_topic_reasons` 를 보입니다.
- **믿지 않는 입력.** 영상 글은 `state` 에만 들어가고 질문에는 들어가지 않습니다. 두 답이 같은
  state 를 읽으므로 주입은 두 답을 함께 움직일 수 있습니다. 판별만으로는 아무것도 게시하지
  않으며, Phase 4 · 5 · 7 의 조건이 그대로 적용됩니다.
- **판정표.** `noul` 은 주제 일치 확률, `confidence` 는 이유 보기(choice) 답의 확신입니다.

  | 판정 | 조건 |
  |---|---|
  | `yes` | `confidence ≥ choice_min_confidence` ∧ `noul ≥ noul_yes_min` ∧ 보기 ∈ `on_topic_reasons` |
  | `no` | `confidence ≥ choice_min_confidence` ∧ `noul ≤ noul_no_max` ∧ 보기 ∈ `off_topic_reasons` |
  | `hold` | 그 밖의 모든 경우 — SDK 오류 · 응답 모양 오류 · 낮은 확신 · `noul` 이 두 기준값 사이 · 두 답이 엇갈림 |

- **이유 모양.**
  - 판정: `<보기> (<그 보기 확률>) · 일치 <noul> · 확신 <confidence>`, 숫자는 소수 둘째 자리까지.
  - 판단 보류: 위 모양 앞에 `확신 낮음: ` 또는 `판단 엇갈림: ` 이 붙습니다.
  - 오류 보류: `API 오류: <SDK 예외 이름> [<상태 코드>]` 또는
    `응답 모양 오류: <예외 이름>: <내용>`.
  - 3절과 7절의 `연애 고민 상담` 은 이 모양의 앞부분입니다.
- **자르기.** `state` 와 가장 긴 질문(JSON 을 UTF-8 바이트로 잰 것)의 합은 32000 바이트
  이하입니다 — 토큰 수는 UTF-8 바이트 수를 넘지 않습니다. 자막부터, 그다음 설명, 그다음 제목
  순으로 끝에서 잘라 내며 글자를 쪼개지 않습니다.
  설정 상한(2절의 `topic` 500자, 보기 50개 × 40자) 안에서는 한 글자가 4바이트여도 가장 긴 질문이
  10000 바이트 이하라서 state 에 22000 바이트 이상이 남습니다.
- 세기와 날짜 비교는 jev 에 묻지 않습니다.
- **질문 언어.** `QUESTION_LANGUAGE` 상수이고 기본값은 `ko` 입니다.
- **한국어 정확도.** 예시 묶음은 22개(일치 10 · 불일치 12, 그중 주입 2)입니다.
  `python3 -m tests.jev_accuracy` 를 돌리면 언어마다 맞음 · 잘못된 일치 · 잘못된 불일치 ·
  보류 · 오류 수를 찍습니다.
  - 통과는 잘못된 일치가 없고 22개 중 20개 이상 맞는 것입니다.
  - 종료 코드: 0 ko 통과 · 1 ko 미달 · 2 재지 않음 · 3 측정 실패(오류가 있음 — 모델 문제가
    아님).
  - 기록 — Phase 6F 가 `docs/live-check/result.json`(실행 2026-10-15T08:42:22.401654+00:00, 판정 줄 `6B: stop — 작성 막힘(SKIP 8/13)`)에서 읽은 숫자입니다. 이 실행의 작성 막힘은 트래커 Phase 6F 의 사람 실행 뒤 인터뷰('6F 예외로 착지')가 보고 '6E 뒤' 기록으로 반영했습니다('실제 호출 실행기' 절의 '결과 반영'). 지금 기준값은 `noul_yes_min` 0.8 · `noul_no_max` 0.2 · `choice_min_confidence` 0.5 입니다.
    - ko: 지금 기준값 맞음 20/22 · 잘못된 일치 0 · 잘못된 불일치 0 · 보류 2 · 오류 0 · 올리기만 범위 최다 맞음 20/22 — 통과
    - en: 지금 기준값 맞음 19/22 · 잘못된 일치 0 · 잘못된 불일치 0 · 보류 3 · 오류 0 · 올리기만 범위 최다 맞음 19/22 — 미달
    - 다시 셈한 기준값(ko 예시 행): `noul_yes_min` 0.8 · `noul_no_max` 0.2 · `choice_min_confidence` 0.5 · 맞음 20/22 — 같은 jev 답을 6B 규칙으로 다시 셈한 값이고, 진짜 jev 를 이 설정으로 돌린 숫자가 아닙니다
    - 영상 판별 운영 창: 판별 22 · 일치 7 · 보류 13 · 불일치 2
    - 영상 판별 넓힌 창: 판별 10 · 일치 6 · 보류 4 · 불일치 0
    - `QUESTION_LANGUAGE` 는 `ko` 그대로입니다 — 통과 ko · 미달 en.
    - 기준값 셋은 그대로입니다. 잘못된 일치가 0 이라 올릴 하한이 없고, 올리기만 범위의 최다 맞음이
      지금 기준값의 맞음과 같아 `noul_no_max` 를 옮겨 더 맞는 자리가 없습니다.
    - 표본 부족 — 두 `noul` 기준값 0.2 · 0.8 은 이 실행이 잰 값이 아니라 그대로 둔 값입니다. 예시의
      `noul` 이 두 기준값 사이에 없어, 0.2 · 0.8 과 그 사이의 다른 값이 같은 판정을 냅니다. 실제 영상은
      그 사이에 많고 채점(아래 진짜 영상 판별 채점)도 있지만 예시 22개와 다른 표본입니다.
      - ko: 기준값 사이(0.2 초과 0.8 미만) 예시 0개 · 가장 가까운 예시 0.13 · 0.86
      - en: 기준값 사이(0.2 초과 0.8 미만) 예시 0개 · 가장 가까운 예시 0.08 · 0.82
      - 기준값 사이 영상 운영 창: 10/22
      - 기준값 사이 영상 넓힌 창: 3/10
    - 진짜 영상 판별 채점 — 정답은 사람 칸(`topic_human`)이 있으면 그것, 없으면 Claude 채점(`topic_grade`)입니다.
      예시 22개의 숫자와 다른 표본이며 기준값을 움직이지 않습니다.
      하한을 내릴지는 사람이 이 숫자를 보고 정합니다(트래커 Phase 6C).
      - 영상 판별 채점 운영 창: 일치 7 중 정답 아님 0 · 보류 13 중 정답 연애 12 · 불일치 2 중 정답 연애 0 · 정답 없음 0 · 사람 칸 0/22
      - 영상 판별 채점 넓힌 창: 일치 6 중 정답 아님 0 · 보류 4 중 정답 연애 1 · 불일치 0 중 정답 연애 0 · 정답 없음 0 · 사람 칸 0/10
      - 보류 영상 하한 내림 운영 창: `noul_yes_min` 0.75 이면 새 일치 — 정답 연애 0 · 정답 아님 0 · 정답 없음 0 / `noul_yes_min` 0.6 이면 새 일치 — 정답 연애 2 · 정답 아님 1 · 정답 없음 0
      - 보류 영상 하한 내림 넓힌 창: `noul_yes_min` 0.75 이면 새 일치 — 정답 연애 0 · 정답 아님 0 · 정답 없음 0 / `noul_yes_min` 0.6 이면 새 일치 — 정답 연애 0 · 정답 아님 0 · 정답 없음 0
      - '보류 영상 하한 내림' 은 트래커 Phase 6D 의 기록 줄(결정 아님)이 본 두 하한으로 `noul_yes_min` 만 내리면(확신 · 이유 보기는 지금 기준 그대로) 새로 일치가 되는 보류 영상 수입니다.
    - `noul_yes_min` · `choice_min_confidence` 는 올리기만 하고, 내리는 쪽은 표본 22개로 정하지 않습니다 —
      보류를 줄여 댓글을 늘리는 쪽은 사람이 결과 숫자를 보고 정합니다(트래커 Phase 6B).
  - ko 가 미달이고 en 이 통과하면 `QUESTION_LANGUAGE` 를 `"en"` 으로 바꿉니다. 둘 다 미달이면
    사람이 정합니다(트래커 cross-cutting).
  - 실제 호출 실행기('실제 호출 실행기' 절)가 같은 측정(`tests/jev_accuracy.py` 의 `judge_examples` · `tally`)을 진짜 jev 로 돌려 예시마다 `docs/live-check/result.json` 에 남기고, 위 기록은 Phase 6F 가 그 파일에서 읽어 썼습니다 — `tests/test_live_check_applied.py` 가 기록의 숫자를 결과 파일에서 다시 세어 맞댑니다('실제 호출 실행기' 절의 '결과 반영').
- **음성 대조.** 음성 대조는 10절 목록.

## 실제 호출 실행기 — `tests/live_check.py` (Phase 6A)

사람이 셸에서 한 번 돌려 진짜 jev · Claude · YouTube 를 부르고 결과를 `docs/live-check/` 의 두
파일로 남기는 측정 도구입니다. 실행 안내는 `docs/live-check/README.md` 입니다. ADW 사이클은 이
실행기를 가짜 클라이언트로 테스트하고, 진짜 실행은 사람이 합니다. 크롬 연결 · 게시는 이 실행기의
일이 아닙니다.

```
python3 -m tests.live_check                         # 실행 — 결과를 docs/live-check/ 에 씁니다
python3 -m tests.live_check --verdict <결과 파일>     # 호출 없이 판정 줄을 다시 셉니다
```

- **차례.** ① 모델 이름 — `comment.writer_model` · `claude-sonnet-5-5` · `claude-haiku-5-5` 를 이름마다
  한 번(겹치면 한 번) `max_tokens=1` 로 부릅니다. 답하면 `accepted`, 상태 404 면 `rejected`, 그 밖의
  오류는 `error` 입니다. 작성 모델은 `comment.writer_model` 이 `accepted` 면 그것, 아니면 처음
  `accepted` 인 이름이고, 채점 모델은 작성 모델이 아닌 처음 `accepted` 이름(없으면 작성 모델)입니다.
  `accepted` 가 하나도 없으면 ③ 을 건너뜁니다. ② 정확도 — 예시 묶음 × `LANGUAGES` 를
  `tests/jev_accuracy.py` 의 `judge_examples` 로 판정하고 `tally` 로 셉니다. ③ 영상 한 바퀴 — 아래.
- **영상 고르기.** 운영 창은 키워드마다 `search.list` 한 페이지(탐지 절의 매개변수,
  `publishedAfter = now − trigger.max_age_hours`)입니다. 처음 보는 영상 ID 를 `videos.list` 로 읽어
  `trigger.min_views ≤ 조회수 ≤ trigger.max_views` 인 영상을 판별합니다.
  범위 밖 영상은 jev 에 보내지 않습니다.
  시간당 조회수는 표본이 둘 필요해 고르기 조건이 아닙니다.
- **넓힌 창.** 운영 창을 다 돈 뒤 초안이 `TARGET_DRAFTS`(10)개보다 적거나, 인기 댓글을 재료로 쓴
  초안(`material = "top_comments"` 인 영상의 초안)이 `POPULAR_DRAFTS_MIN`(3)개보다 적으면 키워드마다
  한 페이지를 `publishedAfter = now − WIDE_WINDOW_HOURS`(72시간) · `publishedBefore = now −
  trigger.max_age_hours` 로 한 번 더 찾습니다. 넓힌 창은 두 수가 모두 닿을 때까지 영상을 고릅니다.
  세 번째 창은 없습니다. 영상마다 `window` 칸에 `operation` 또는 `widened` 를 적습니다.
- **한도.** 판별은 실행마다 `CLASSIFY_MAX`(40)개, 댓글 작성은 `WRITE_MAX`(15)개 영상까지이고 두 창이
  함께 씁니다.
  운영 창은 초안이 `TARGET_DRAFTS` 에 닿으면, 넓힌 창은 초안 수와 인기 댓글 재료 초안 수가 모두
  닿으면 새 영상을 고르지 않습니다.
- **재료.** 판별이 `yes` 인 영상마다 `top_comments(video_id, now, limits, TOP_COMMENTS_MAX)` 로 인기
  댓글을 받아 `write_comment(…, transcript="", top_comments=…)` 에 넘깁니다.
  `previous` 는 이번 실행에서 앞서 통과한 초안(`write_comment` 가 돌려준 `draft.text`)의 목록입니다 —
  운영의 `store.comments()` 자리이고, 실행기의 `code_pass` 도 같은 목록으로 셉니다. 댓글이 막힌
  영상(`None`)과 댓글이 하나도 없는 영상은 제목 · 설명으로 이어 씁니다(`material =
  "title_description"`).
  영상마다 `material` · `top_comment_count`(읽은 글 수) · `comment_items`(`commentThreads.list` 가
  돌려준 항목 수 — 댓글이 막혔거나 호출이 실패하면 `null`) · `comments_disabled` 를 적습니다.
  항목 수는 실행기가 `YouTubeClient` 의 호출 한 번의 답에서 세고, `top_comments` 가 돌려주는 글은
  바뀌지 않습니다.
  자막은 공식 API 로 남의 영상에서 받을 수 없어 비어 있습니다.
- **jev 자체 검사 어댑터.** `jev_self_check(ask, model)` 이 '댓글 작성' 절의 `check` 포트를 채웁니다 —
  질문마다 `noul`(`criteria = {"true": "Yes, it does", "false": "No, it does not"}`)을 한 요청으로 묻고
  `answers[이름].noul` 을 돌려줍니다. 이 함수는 `agent.writer` 에 있고(Phase 7 이 옮김) 실행기와 운영이 같은 함수를 씁니다.
- **영상의 끝.** `result` 는 `comment`(통과) · `skip`(검사 두 번 탈락 또는 스스로 건너뜀 — `skip_kind` 가
  `checks_failed` · `no_scene` · `no_concern`; 실행기가 Claude 답을 `read_reply` 로 다시 읽어 정합니다) ·
  `error`(인기 댓글을 못 받음,
  또는 `write_comment` 가 Claude 호출 오류 · jev 검사 호출 오류 · jev 답 모양 이상으로 끝남 — 실행기의
  감싸개가 보고 `error_cause` 에 `comments` · `claude` · `jev` · `jev_answer` 로 적음) · `not_written`
  (판별이 `yes` 가 아님)입니다.
- **천장.** 실행 한 번의 서비스별 호출 수 천장은 실행기 상수 `CEILINGS`(jev 120 · claude 110 ·
  youtube 50)이고 설정 키가 아닙니다.
  천장이 세는 것은 실행기의 호출(감싸개 한 번)이고, SDK 안의 다시 시도는 그 밖입니다 — anthropic 은
  `max_retries=2`(호출당 요청 많아야 3번), typesafe 는 SDK 기본 정책입니다.
  천장에 닿은 다음 호출은 보내지 않고 실행 전체가 그 자리에서 멈춥니다.
  `CeilingReached` 는 `BaseException` 이라 `write_comment` 의 `except Exception` 이 삼키지 않습니다.
  결과에는 `stopped = {"kind": "ceiling", "service": …, "limit": …}` 를 적습니다. 쿼터 장부가 막으면
  (`QuotaExhausted`) `"kind": "quota"`, 그 밖의 예외와 Ctrl-C 는 `"kind": "aborted"` 와 예외 이름입니다.
  YouTube 호출은 운영과 같은 쿼터 장부 `data/quota.json` 을 지납니다.
- **키.** 키는 `require_secret`(환경 변수, 없으면 `.env`)으로 읽습니다.
  키 셋 중 하나라도 없거나 `typesafe-sdk` · `anthropic` 이 없으면 아무 서비스도 부르지 않고, 없는 것을
  한 줄로 알린 뒤 종료 코드 2 로 끝납니다.
  키 값과 그 앞 8글자 이상의 조각은 결과 파일 · 요약 · 화면 · 오류 줄 어디에도 쓰지 않습니다.
  내보내는 글은 모두 `<YOUTUBE_API_KEY>` · `<TYPESAFE_API_KEY>` · `<ANTHROPIC_API_KEY>` 로 가립니다.
  traceback 과 이어진 예외(`__context__`)는 찍지 않고 예외 이름만 찍습니다.
  `python3 -m tests.live_check` 의 진입은 `cli` 를 거치고, `cli` 는 `BaseException` 모두를 잡습니다.
  두 파일을 쓴 뒤 다시 읽어 키 조각이 보이면 두 파일을 지우고 종료 코드 3 입니다.
- **개인 정보.** 결과 두 파일에 쓰는 `untrusted` 칸의 글은 연락처 모양(`CONTACT_RE` — 이메일 · 전화번호 · 계좌번호 · `예금주` 뒤 구분 기호 다음 첫 덩이)을 `<연락처>` 로 바꿔 씁니다.
  칸은 지우지 않고 글 안의 모양만 바꿉니다.
  끝 줄의 `없음` 은 예금주 이름 전체를 보증하지 않습니다 — 이름이 `예금주` 뒤 첫 덩이가 아니면(조사가 붙음 · 여러 낱말 · 목록 밖 구분 기호 · 이름이 앞에 옴) 남은 이름은 가리지도 세지도 않습니다.
  제목 · 설명 · 인기 댓글은 길이로 자르기 전에 바꾸므로, 잘려 반쯤 남은 모양이 결과에 남지 않습니다.
  초안의 고민 · 글은 초안을 적는 자리에서 바꾸므로, `frame_overlap` 은 결과 파일에 남은 글로 다시 세어도 같습니다(서로 다른 연락처도 같은 `<연락처>` 로 셉니다).
  Claude · jev 에 보내는 글은 바꾸지 않습니다 — 운영과 같은 재료입니다.
  `untrusted` 밖의 칸(`fingerprint.jev_models` · `video_id` · 숫자 칸)은 바꾸지 않습니다.
  두 파일을 쓴 뒤 `result.json` 의 모든 글(키와 값)과 `summary.md` 전체를 같은 목록으로 세어, `키 검사` 줄 다음 마지막 줄에 없으면 `개인 정보 검사: 결과 파일에 연락처 모양 없음` 을 찍고, 있으면 `개인 정보 검사: 결과 파일에 연락처 모양 N곳 — 커밋하지 마세요` 를 찍고 종료 코드 4 로 끝납니다.
  이 줄은 곳 수만 찍고 그 글은 찍지 않습니다.
  두 파일은 지우지 않습니다.
  `tests/test_live_check_published.py` 가 커밋된 두 파일을 같은 목록으로 세어 한 곳이라도 있으면 빨강입니다(파일이 없으면 셀 글이 없어 초록).
- **결과 파일.** `result.json` 은 6B 가 읽는 기계용(키 정렬, 2칸 들여쓰기, UTF-8, `os.replace`),
  `summary.md` 는 사람용 숫자 요약이고 같은 실행이 둘을 덮어씁니다.
  `summary.md` 에는 영상 · 인기 댓글 · 초안의 글이 들어가지 않습니다.
  밖에서 온 글과 모델이 쓴 글은 `untrusted` 칸 안에만 둡니다(제목 · 설명 · 인기 댓글 · 고민 · 초안 ·
  판정 이유 · 건너뛴 이유 · 코드 검사 이유). 예외는 둘입니다. jev 가 답에 알린 모델 이름은 검사 없이
  `fingerprint.jev_models` 에 들어갑니다. YouTube 가 준 영상 ID 는 허용 모양(`VIDEO_ID_RE`, 11자)을
  거친 것이 `videos[].video_id` · `errors[].video_id` 에 들어갑니다. `untrusted` 밖의 칸은 이 둘을
  빼면 숫자 · 참거짓 · 정해진 낱말과 실행기가 만든 글(오류 이름)이고, 6B 는 판정과 기준값 계산에 이
  칸들을 쓰며 `jev_models` 는 믿을 수 없는 글로 보아 읽지 않습니다(아래 '결과 반영'). 댓글 작성자 이름 ·
  채널 ID 는 어느 칸에도 없습니다. 제목은 300자, 설명은 2000자, 인기 댓글은 하나에 300자까지입니다.
  코드 검사 이유(`drafts[].untrusted.code_failures`)에는 이유 이름과 숫자만 적습니다 — 반복은 `이전 댓글과 겹칩니다 (n글자)`(n 은 겹친 글자 수), 링크는 `링크·주소 모양이 들어 있습니다`, 글자 수는 작성기의 이유 그대로(`글자 수 n자 — a–b자여야 합니다`), 그 밖의 이유는 `그 밖의 코드 검사 이유` 입니다.
  이 칸에는 겹친 글자와 링크 조각을 적지 않습니다 — 작성기의 이유 글은 그 글자를 띄어쓰기 · 문장부호를 지운 꼴로 담아 연락처 모양 목록을 빠져나가기 때문입니다. `code_pass` · `passed` 는 원문으로 한 검사 그대로이고, 작성기와 운영의 이유 글('댓글 작성')은 그대로입니다.

  | 칸 | 뜻 |
  |---|---|
  | `schema_version` · `notice` · `run_at` · `example_count` | 모양 버전(지금 2 — 판 2 부터 채점 막힘을 셈) · `untrusted` 칸 안내 · 실행 시각(UTC) · 예시 수 |
  | `verdict` | 판정 줄(아래) |
  | `stopped` | `null` · 천장 · 쿼터 · 중단 |
  | `calls` · `ceilings` | 서비스별 실행기 호출 수와 천장 |
  | `models` · `writer_model` · `grader_model` | 이름마다 `accepted` · `rejected` · `error`(오류 이름 · 상태) |
  | `accuracy.<언어>[]` | 예시마다 `index` · `kind` · `label` · `verdict` · `error` · `noul` · `choice` · `probability` · `confidence` |
  | `accuracy_tally.<언어>` | 지금 기준값의 맞음 · 잘못된 일치 · 잘못된 불일치 · 보류 · 오류(`tally`) |
  | `windows.<창>` | 검색 수 · 찾은 영상 · 조회수 범위 안 · 판별한 영상 |
  | `videos[]` | `window` · `views` · `published_at` · `age_hours` · `classification` · `topic_grade` · `topic_grade_error` · `topic_grade_shape` · `topic_human` · `material` · `top_comment_count` · `comment_items` · `comments_disabled` · `result` · `error_cause` · `skip_kind` · `skip_grade` · `skip_grade_error` · `skip_grade_shape` · `skip_human` · `drafts[]` |
  | `drafts[]` | `attempt` · `parsed` · `scores`(질문 → P(예)) · `self_check_pass` · `code_pass` · `passed` · `grade` · `claude_grade` · `grade_error` · `task_quality` · `task_error` · `grade_shape` · `frame_overlap` · `human` (스스로 건너뜀 답은 줄이 없음) |
  | `errors[]` | 실패한 호출마다 `service` · `stage` · `error`(예외 이름) · `status` · `video_id` |
  | `fingerprint` | 판별 질문 문구(ko · en) · 예시 묶음 SHA-256 · 판별 설정 값 · jev 가 알린 모델 · 자체 검사 질문 · 통과선 · 트리거 조회수 범위 · 채점 프롬프트 · `MARGIN` · `PASS_CORRECT` · `claude_max_retries` |

  6E 뒤 실행의 판 2 결과는 `videos[]` 에 스스로 건너뜀 칸이 더해져 있습니다 — 칸을 더하기만 해 판은
  그대로입니다.

- **Claude 채점.** 초안마다(다시 쓴 초안 포함) 채점 모델을 한 번 부릅니다(`GRADE_SYSTEM`, `max_tokens`
  1024). 답은 도구 `record_grade` 의 입력으로 받습니다(`tool_choice` 로 그 도구를 정함 — 도구 블록이
  없으면 글 블록에서 JSON 하나를 찾습니다).
  다섯 질문 `scene_in_material`(초안이 짚은 장면이 재료에 있나) · `reads_like_ad` · `follows_concern` ·
  `concern_is_love_worry`(고민 한 줄이 재료 속 연애 고민인가) · `saju_story_fits`(댓글에 비슷한 고민 때
  연애사주를 봤던 경험이 있고 그 고민과 이어지나)의 true/false 가운데 앞 셋이 `grade`, 뒤 둘이
  `task_quality` 입니다.
  답에 다섯 이름 밖의 키가 있으면 두 몫 모두, 한 몫의 키가 빠졌거나 값이 참거짓이 아니면 그 몫만
  응답 모양입니다(`grade_error` · `task_error = "응답 모양"`).
  `scene_in_material` 이 참 · `reads_like_ad` 가 거짓 · `follows_concern` 이 참이면
  `claude_grade = "ok"`, 아니면 `"bad"` 입니다.
  `task_quality` · `task_error` 는 `claude_grade` 와 판정 줄에 들어가지 않습니다.
  응답 모양이면 `grade_shape` 에 답의 모양(`stop_reason` — 정해진 낱말 밖은 `other` · 도구 블록이
  있었나 · 글 블록 글자 수 · 답 객체를 읽었나 · 찾은 키 가운데 다섯 이름 · 그 밖 키 수 · 참거짓이 아닌
  키)을 적습니다.
  채점 답(초안 채점 · 영상 판별 채점)의 글 · 값 글자와 목록 밖 키 이름은 결과 파일 · 요약 어느
  칸에도 남기지 않습니다.
  채점은 이 실행기 안의 측정 도구입니다.
  `src/agent/` 의 모듈은 채점을 부르거나 담지 않습니다.
- **영상 판별 채점.** 판별한 영상마다(판정과 상관없이) 채점 모델을 한 번 부릅니다(`TOPIC_SYSTEM`,
  도구 `record_topic`).
  재료는 제목 · 설명이고, 묻는 것은 "이 영상은 연애가 주제인가(키워드만 겹침이 아닌가)"
  하나(`romance_topic`)입니다.
  참이면 `topic_grade = "연애"`, 거짓이면 `"아님"`, 답 모양이 다르면 `topic_grade_error = "응답 모양"`
  과 `topic_grade_shape` 입니다.
  `topic_human` 은 빈 글자로 두고, 사람은 동의하지 못하는 영상에 `연애` 또는 `아님` 을 적습니다.
  정답은 사람 칸이 있으면 그것, 없으면 채점입니다.
  판정 줄과 판별 기준값 셈은 `topic_grade` · `topic_grade_error` · `topic_grade_shape` · `topic_human`
  을 읽지 않습니다.
  영상 판별 채점 호출이 API 오류로 실패하면 다른 호출처럼 `errors[]` 에 남아 재지 못함(호출 오류)으로
  셉니다.
  진짜 영상 숫자로 기준값을 내릴지는 사람이 정합니다(트래커 Phase 6C).
- **스스로 건너뜀 채점 (Phase 6E).** 작성기가 스스로 건너뛴 영상(`skip_kind` 가 `no_scene` · `no_concern`)마다
  채점 모델을 한 번 부릅니다(`SKIP_GRADE_SYSTEM`, 도구 `record_material`).
  재료만 보내고 초안이나 건너뜀 답은 보내지 않습니다. 묻는 것은 `material_has_love_worry`(재료에 자료 속
  사람의 연애 고민이 있나) · `material_has_scene`(짚을 만한 영상 속 장면 · 말이 재료에 있나) 둘이고, 초안
  채점의 `concern_is_love_worry` · `scene_in_material` 과 같은 뜻입니다. 답은 `skip_grade`(두 참거짓)이고,
  모양이 다르면 `skip_grade_error = "응답 모양"` 과 `skip_grade_shape`, API 오류면 `skip_grade_error` 에 오류
  이름이며 그 호출은 `errors[]`(단계 `skip_grade`)에 남아 재지 못함(호출 오류)으로 셉니다.
  검사 두 번 탈락 · 댓글 · 오류로 끝난 영상은 이 채점을 부르지 않습니다.
  스스로 건너뜀 답은 초안 줄을 남기지 않아 `parsed: false` 로 세지 않습니다.
  판정 줄 · 초안 채점 칸 · 과제 품질 셈은 `skip_kind` · `skip_grade` · `skip_grade_error` · `skip_grade_shape` ·
  `skip_human` 을 읽지 않습니다. 실행기가 채우는 새 칸(`skip_kind` · `skip_grade` · `skip_grade_error` ·
  `skip_grade_shape`)은 참거짓 · 정해진 낱말 · 숫자 · 목록 안 이름뿐입니다.
  이 채점은 쓴 영상마다 많아야 한 번이고, 건너뜀 답 앞의 초안 채점과 합쳐도 영상마다 그 영상의 작성 호출
  수를 넘지 않아 최악 호출 수(claude 103)는 그대로입니다. 이유별 '정당한 건너뜀' 셈은 결과 파일에서
  Phase 6F 가 합니다.
- **다른 영상 초안과 겹침 (과제 품질 ⓒ).** 실행이 끝나면 초안마다 공백을 모두 뺀 6글자 조각 가운데
  다른 영상의 초안에도 있는 조각 수를 `frame_overlap` 에 적습니다.
  같은 영상의 다시 쓴 초안끼리는 세지 않고, AI 를 부르지 않습니다.
- **사람 칸.** 실행기는 `human` · `topic_human` · `skip_human` 을 빈 글자로 둡니다. 사람은 채점에 동의하지
  못하는 초안의 `human` 에 `ok` 또는 `bad` 를 적습니다(건너뛰어도 됨). 사람은 스스로 건너뜀 채점에 동의하지
  못하는 영상의 `skip_human` 에 `정당`(재료에 정말 없었음) 또는 `부당`(재료에 있었음)을 적습니다(건너뛰어도 됨).
  판정 줄은 `human` · `topic_human` · `skip_human` 을 읽지 않습니다.
- **판정 줄.** `verdict_line(result)` 이 결과 하나로 셉니다. `summary.md` 의 첫 줄, 화면의 첫 줄,
  `result.json` 의 `verdict` 가 같은 줄입니다. 걸린 경우를 아래 차례로 `; ` 로 이어
  `6B: stop — <경우들>` 을, 하나도 없으면 `6B: go` 를 씁니다.

  | 경우 | 걸리는 조건 | 모양 |
  |---|---|---|
  | 재지 못함 | 예시 판정에 오류 보류가 있음 · 예시 밖 호출 오류가 있음(404 로 답한 모델 확인은 뺌) · `result: "error"` 인 영상이 있음 · `stopped` 가 있음 — 하나라도 | `재지 못함(예시 오류 <n> · 호출 오류 <n> · 영상 오류 <n> · 천장 <서비스> <천장> · 쿼터 <호출> <counter> <사용>/<한도> · 중단 <예외 이름>)` — 있는 것만 |
  | 판별 미달 | 어느 언어도 "올리기만" 범위에서 잘못된 일치 0 · 맞음 `PASS_CORRECT`(20) 이상을 이루지 못함 | `판별 미달(ko <최다 맞음>/<예시 수> · en …)`, 잘못된 일치를 막을 설정이 없는 언어는 `<언어> 잘못된 일치 못 막음` |
  | 작성 막힘 | `skip`(검사 두 번 탈락 · 스스로 건너뜀 — 이유를 가리지 않음) × 2 > 쓴 영상(`comment` + `skip`, 두 창 모두) | `작성 막힘(SKIP <s>/<w>)` |
  | 모델 이름 | `claude-sonnet-5-5` · `claude-haiku-5-5` 가 둘 다 `rejected` | `모델 이름(claude-sonnet-5-5 · claude-haiku-5-5 둘 다 거절)` |
  | 채점 막힘 | 판 2 이상 결과에서 채점 오류(`grade_error` 가 있는 초안) × 2 > 초안(`parsed` 인 초안, 두 창 모두) | `채점 막힘(오류 <n>/<m>)` |

  API 실패로 끝난 영상(`result: "error"`)은 작성 막힘에 세지 않고 재지 못함에 셉니다.
  쓴 영상이 0 이고 오류도 없으면 `go` 쪽이고, 6B 가 "표본 없음" 으로 다룹니다. 재지 못함의 예시 밖
  오류 · 영상 오류는 이 계약의 읽기입니다 — 트래커 Phase 6A 의 ① 은 예시 오류와 천장을 적습니다.
  채점 막힘은 판 2 이상(`schema_version` ≥ 2) 결과에만 셉니다 — 판 1 결과는 옛 채점기로 잰 숫자라 위
  네 경우로 셉니다(트래커 Phase 6C 질문 5 A).
  초안이 0 이면 채점 막힘이 아닙니다.
  `task_error` 와 영상 판별 채점의 오류는 채점 막힘에 세지 않습니다.
  채점 호출이 API 오류로 실패한 초안은 재지 못함(호출 오류)과 채점 막힘에 함께 셉니다 — 둘이 함께
  나오면 재지 못함을 먼저 봅니다.
- **"올리기만" 범위.** 기준값의 출발점은 `fingerprint.classifier` 이고 판정은 `classifier._decide`
  그대로입니다. `noul_yes_min` 후보는 지금 값과, 정답이 `no` 인 예시마다 `noul + MARGIN`(0.05, 소수
  여섯째 자리 반올림) 가운데 지금 값보다 크고 1 이하인 값입니다. `choice_min_confidence` 도
  `confidence + MARGIN` 으로 같습니다. `noul_no_max` 는 자유 — 지금 값 · 0 · 정답이 `no` 인 예시의
  `noul` 가운데 `noul_yes_min` 후보보다 작은 값입니다. 1 을 넘는 하한은 후보가 아니므로, 그 하한으로
  막아야 하는 잘못된 일치가 남은 언어는 미달입니다. 오류 보류 예시는 어느 설정에서도 맞음이
  아닙니다.
  맞음이 같은 설정이 여럿이면 덜 올린 쪽 하나입니다(`best_setting`) — `noul_yes_min` 이 작은 쪽, 그다음 `choice_min_confidence` 가 작은 쪽, 그다음 `noul_no_max` 가 지금 값에 가까운 쪽(거리가 같으면 작은 쪽).
- **종료 코드.** 실행: 0 `go` · 1 `stop` · 2 시작 전 멈춤(인자 · 설정 · 키 · SDK · 키 모양 — 호출 0번,
  파일 없음) · 3 결과 파일을 쓰지 못함, 키 조각이 보여 지움, 또는 실행기 오류(예: 결과 파일을 읽다
  `RecursionError`) · 4 결과 두 파일은 썼으나 연락처 모양이 남음(두 파일은 남김 — 위 '개인 정보').
  `--verdict`: 0 `go` · 1 `stop` · 2 파일을 읽을 수 없음. 판정 줄과 다르게 저장된
  `verdict` 는 한 줄 더 알립니다.
- **알려진 한계.** jev 응답의 `answers[이름].noul` · `model`, Claude 의 404 `status_code`, typesafe 의
  다시 시도 · 제한 시간 정책은 문서와 SDK 소스로 맞춘 모양이고 첫 진짜 실행이 처음 확인합니다.
  Claude 채점은 정답이 아니라 또 하나의 의견입니다(트래커 Phase 6A).
  도구 강제(`tool_choice`)로 받은 채점 답의 모양은 SDK 로 맞춘 모양이고, 모델이 그 도구로 답하는지는
  다음 진짜 실행이 처음 확인합니다.
- **결과 반영 (Phase 6B · 6D · 6F).** 사람이 커밋한 결과를 `tests/test_live_check_applied.py` 가 계약 · 설정과
  맞댑니다. 결과 파일과 요약이 BOM 없이 있고, 결과가 판 2 이상(`schema_version` ≥ 2)이며, `--verdict` 가
  결과 파일로 다시 센 판정 줄 한 줄을 내고 요약 첫 줄이 같은 줄이며, 언어마다 예시 행 수가 `example_count` 와
  예시 묶음 수와 같아야 합니다.
  - 판정 줄은 `6B: go`(종료 코드 0)여야 합니다.
    예외는 하나뿐입니다 — 실행 `2026-10-15T08:42:22.401654+00:00` 의 `6B: stop — 작성 막힘(SKIP 8/13)`(종료 코드 1).
    트래커 Phase 6F 의 사람 실행 뒤 인터뷰('6F 예외로 착지')가 이 실행을 보고 '6E 뒤' 기록으로 반영했고, 다른
    실행이거나 다시 센 판정 줄이 한 글자라도 다르면 빨강입니다. Phase 6D 가 '고치기 전'(6E 전) 기록으로 반영한
    실행 `2026-10-14T14:09:02.882902+00:00` 의 `6B: stop — 작성 막힘(SKIP 5/7)` 도 이제 빨강입니다 — 그 예외는 그 결과 하나에만 걸렸습니다.
  - 지문 맞대기(`measured_drift`) — jev 의 답을 바꾸는 칸(`questions` · `examples_sha256` · `classifier.model` ·
    `classifier.on_topic_reasons` · `classifier.off_topic_reasons` · `margin` · `pass_correct`)은 결과와 지금 코드 ·
    `config.yaml` 이 같아야 합니다.
  - 다시 셈한 칸(`classifier.noul_yes_min` · `classifier.noul_no_max` · `classifier.choice_min_confidence` ·
    `check_min_probability`)은 결과 파일로 규칙을 다시 셈한 값(`recount`)과 지금 `config.yaml` 이 같아야 합니다.
    하한 셋은 질문 언어(ko 가 통과면 ko, en 만 통과면 en)의 예시 행에서 위 "올리기만" 범위의 최다 맞음 설정
    (`best_setting`)이고, 통과선은 '댓글 작성' 절의 규칙으로 다시 셈한 값(막을 초안이 없으면 결과의 값)입니다.
    그 값과 다른 설정은 손으로 넣은 값이든 뒤 페이즈가 바꾼 값이든 빨강입니다. 하한은 jev 답 위에 코드가
    나중에 대는 값(`classifier._decide`)이라 다시 셈한 판정은 같은 jev 답에서 코드가 낼 판정 그대로이고, 그
    설정으로 진짜 jev 를 돌린 숫자는 아닙니다.
    다시 셈의 출발점인 결과의 기준값(`fingerprint.classifier` 의 하한 셋 · `check_min_probability`)은 결과의 판정 ·
    `self_check_pass` 칸을 다시 판정한 값과 같아야 합니다(`stored_verdict_mismatches`) — 저장된 판정을 바꾸는 만큼
    옮긴 기준값은 결과와 설정을 함께 고쳐도 빨강입니다.
    통과선 다시 셈의 비교 점수와 저장된 `self_check_pass` 의 다시 판정은 초안마다 그 초안 `scores` 의 질문
    이름으로 셉니다(6D 결과는 질문 셋, 6E 뒤 결과는 다섯) — 다시 판정은 '댓글 작성' 절의 하한 비교
    (`_TOLERANCE` 포함) 그대로입니다. 이름이 비었거나 지금 `CHECK_QUESTIONS` 에 없는 이름이 하나라도 있으면
    빨강입니다 — 그래서 질문을 더하는 사이클도 사람의 재실행을 먼저 요구하지 않습니다.
  - 작성 쪽 칸(`check_questions` · `self_check_criteria` · `trigger` · `grade_system` · `target_drafts` ·
    `wide_window_hours` · `claude_max_retries`)과
    `fingerprint.jev_models` 는 맞대기에서 보지 않습니다.
    이 칸을 지키면 작성 질문이나 채점을 고치는 사이클마다 사람의 재실행이 먼저 있어야 합니다. 그래서 이 칸이
    바뀐 뒤의 초안 숫자는 옛 질문 · 채점으로 잰 숫자입니다.
  - 새 결과나 사람 칸에 `ok` · `bad` 를 적은 결과를 커밋하거나 맞대는 칸을 고치면 이 모듈이 빨강입니다
    — 기록이 지금 코드를 잰 숫자가 아니라는 뜻입니다. 사이클 안에서는 `unmeasured` 로 멈춥니다. 초록으로
    돌아오는 길은 사람이 실행기를 다시 돌려 결과를 커밋한 뒤, 이 페이즈와 같은 적용 사이클이 기록 줄과
    기준값을 새 결과로 다시 쓰는 것입니다. 그 사이클은 다시 반영 페이즈(트래커 — 6D 다음은 6F)가 맡고, 새 결과는 main 이
    아니라 그 페이즈의 레인 브랜치에만 커밋합니다 — 그 뒤의 재실행도 트래커에 다시 반영 페이즈를 열고
    같은 길로 갑니다. 영상의 사람 칸(`topic_human`)에 `연애` · `아님` 을 적은 결과도 기록 줄(영상 판별
    채점)을 바꾸어 이 모듈이 빨강입니다.
    스스로 건너뛴 영상의 사람 칸(`skip_human`)에 건너뜀 채점과 다른 `정당` · `부당` 을 적은 결과도 기록 줄(정당한 건너뜀)을 바꾸어 이 모듈이 빨강입니다.
    사람 칸의 다른 값(`human` 의 `ok` · `bad` 밖의 글, `topic_human` 의 `연애` · `아님` 밖의 글, `skip_human` 의 `정당` · `부당` 밖의 글)은 사람 칸으로 세지 않아 이 모듈을 빨강으로 만들지 않습니다.
- **음성 대조.** 10절 목록의 `youtube-comments-*` · `live-check-*` 명령.

## 실행 진입점 — `run.py` (Phase 7)

```
PYTHONPATH=src python3 -m agent.run [--dry-run] [--once]
```

- **켜기.** 단일 실행 잠금(`data/agent.lock`) → SDK 둘(`typesafe-sdk` · `anthropic`, `find_spec`) → 비밀 값 셋(`YOUTUBE_API_KEY` ·
  `TYPESAFE_API_KEY` · `ANTHROPIC_API_KEY`, 탐지 절의 `require_secret`) → `config.yaml` → 저장소 → `START` → `run_loop`(9절) 차례입니다.
  잠금을 다른 에이전트(`agent.run`)가 쥐고 있으면 로그를 한 줄도 쓰지 않고 종료 코드 3 으로 끝납니다.
  SDK · 비밀 값 · 쿼터 장부 · 설정 · 저장소를 쓸 수 없으면 종료 코드 2 입니다(설정은 `ERROR where=config`, 저장소는
  `ERROR where=store` 도 남김). 잠금은 운영체제가 쥐므로 프로세스가 죽으면 저절로 풀립니다.
  이 잠금은 에이전트끼리만 막습니다 — 실제 호출 실행기(`tests/live_check.py`)도 같은 쿼터 장부를 쓰지만 이 잠금을 쥐지 않으므로,
  에이전트가 도는 동안에는 실행기를 돌리지 않습니다(두 프로세스의 장부가 서로의 기록을 덮어씁니다).
- **로그 줄.** `START mode=live|test allowed=<명단 영상 수> interval_min=… dry_run=… once=… test_run=…`, 사이클마다
  `CYCLE n=… errors=… mode=live|test`, 끝에 `STOP reason=once|interrupted|error` 입니다.
  `errors` 는 울타리가 잡은 영상 수이고, 단계가 스스로 남긴 `ERROR`(판별 오류 보류 · 작성기 API 오류 · 유튜브 오류)는 세지 않습니다.
  화면 출력(echo)은 콘솔 인코딩이 못 쓰는 글자를 `\` 이스케이프(`backslashreplace`)로 바꿔 씁니다 — 로그 파일은 그대로 UTF-8 입니다.
- **한 벌 · 한 스레드.** 저장소(`data/videos.json`) · 쿼터 장부(`data/quota.json`) · 로그(`logs/agent.log`)를 한 벌씩 만들고,
  다섯 단계(탐지 → 판별 → 타이밍 → 작성 → 게시)를 주기 루프 하나 · 한 스레드에서 차례로 돌립니다.
- **사이클.** 탐지(`Watcher.cycle`) 뒤, 이 사이클에 새 조회수 기록이 붙은 영상마다 저장소 순서(`detected_at`, `video_id`)로
  판별 → 타이밍 → 작성 → 게시를 돌립니다.
- **판별.** `record.classification` 이 없으면 `classify(record, config, ask, now)` 를 부르고 `CLASSIFY` 를 씁니다.
  `yes` · `no` · 판정 보류는 저장하고 다시 묻지 않습니다.
  오류 보류(`is_error_hold`)는 `ERROR where=classify` 도 쓰고 저장하지 않아, 다음 새 기록 때 다시 묻습니다.
- **타이밍.** 새 기록마다 `judge_trigger` 로 다시 판정해 `record.trigger` 에 저장하고 `TRIGGER … per_hour=<views_per_hour>` 를
  씁니다. 명단 영상(`allowed_video_ids(config.allowed_videos)`)은 규칙 판정을 `rule_verdict=` · `rule_reason=` 에 함께 적고
  `verdict=yes reason=allowlisted` 로 통과합니다 — 다른 영상의 기준은 그대로입니다.
- **작성.** 판별 · 타이밍이 모두 `yes` 이고 댓글이 없으면 인기 댓글(`top_comments` 앞 10개, 댓글이 막힌 영상은 `()`) ·
  `previous=store.comments()` · `transcript=""` 로 `write_comment` 를 부르고, 초안을 `record.comment` 에 넣어 저장합니다.
  인기 댓글을 못 받은 영상(`QUOTA` 또는 `ERROR where=commentThreads.list`)은 이번 사이클에 쓰지 않습니다.
  명단 밖 영상의 댓글도 저장소와 `COMMENT` 줄에 남습니다.
- **게시.** 댓글이 있는 영상마다 `post_video(…, dry_run=<테스트 실행>, …)`(6절)를 부릅니다. 영상당 1개 · 하루 상한 · 채널
  대기는 명단 영상에도 저장소가 그대로 셉니다(4절). 테스트 실행은 `--dry-run` 또는 `config.test_run` 이고, 설정은
  `--dry-run` 을 끄지 못합니다. 명단 영상에는 게시마다 `ChromeSession(config.chrome_debug_url)` 을 새로 만들어 그 `new_page` 를
  `open_page` 로 넘기고, 게시가 끝나면(성공 · 실패 · 예외) `close()` 로 연결만 놓습니다 — 테스트 실행에서도 같습니다(그 탭을
  쓰는 길은 Phase 7F).
  명단 밖 영상에는 크롬을 여는 함수를 넘기지 않습니다 — 부르면 `PageError(chrome_withheld)` 를 내는 함수가 그 자리에 갑니다.
- **설정 거절.** `reload` 가 `ConfigError` 를 내면 진입점이 거절을 기억하고, 다시 읽기가 받으면 잊습니다.
  거절이 이어지는 동안 탐지 · 판별 · 타이밍 · 작성은 이전 설정으로 돌고, 게시는 `post_video` 를 부르지 않고 6절 1 · 2 · 4 를
  크롬 없이 따라 테스트 저장합니다 — 명단 영상의 이유는 `config_rejected`, 명단 밖 영상은 가드의 이유 그대로입니다.
  그래서 사람이 켠 테스트 실행(`dry_run`)과 로그에서 갈리고, Phase 7F 의 리허설 길로 가지 않습니다.
- **고친 설정이 닿는 때.** 설정은 사이클이 끝난 뒤 다시 읽습니다(9절). 대기 중에 고친 값(`test_run: true` · 명단에서 뺀 영상 포함)은
  그 대기 뒤 사이클이 옛 값으로 돈 다음, 그 사이클 뒤의 다시 읽기부터 적용됩니다.
  실제 게시를 바로 멈추려면 Ctrl-C 로 끄고 `--dry-run` 으로 다시 켭니다.
- **영상마다 울타리.** 판별 · 타이밍 · 작성 · 게시 중 한 영상에서 난 `Exception` 은
  `ERROR where=run.classify|run.trigger|run.write|run.post reason=<예외 종류>: <메시지 200자까지> video=<ID>` 한 줄로 남기고 다음 영상으로
  갑니다. `KeyboardInterrupt` 같은 `BaseException` 은 그대로 올라가 `STOP reason=interrupted`(종료 코드 130)로 끝납니다.
  울타리 줄과 `on_error` 의 `ERROR where=cycle|config` 줄은 예외 자신의 종류와 메시지만 쓰고, `__context__` · `__cause__` ·
  traceback 을 따라가지 않습니다(Phase 2 ship-report R6).
  그 영상을 다음 사이클에 다시 하지 않게 하는 기억은 아직 없습니다(Phase 7C).
- **음성 대조.** `python3 -m tests.mutants <이름>` — `run-rejected-posts-live` · `run-chrome-for-all` · `run-no-timing-exemption` ·
  `run-fence-catches-base` · `run-errors-uncounted` · `run-reason-follows-context` · `run-reloader-forgets-rejection` ·
  `run-lock-ignored` · `watcher-allowlist-untracked` · `trigger-first-sample-ignored` · `trigger-first-sample-age-zero` ·
  `config-test-run-any-value` · `writer-status-ignored` · `run-sdk-check-skipped` · `run-echo-strict` · `run-reason-str-unguarded`.

## 결과 화면 — `report.py` (Phase 7D)

- **언제 · 어디.** 사이클마다 `CYCLE` 줄을 쓴 바로 뒤에 `data/report.html` 한 장을 다시 씁니다. 서버 없는 정적 HTML 이라
  브라우저로 열고, 다음 사이클의 결과는 새로고침으로 봅니다. `data/` 가 git 무시라 이 화면도 커밋 대상 밖입니다.
- **입력.** 화면의 입력은 저장소 기록(`Store.records()`)과 `read_log` 로 읽은 `logs/agent.log`(7절) 둘뿐입니다.
  화면은 이 둘을 읽기만 하고 판단 · 게시 · 저장소를 바꾸지 않습니다. 같은 기록과 같은 로그면 같은 화면입니다 —
  `만든 시각` 은 마지막 로그 줄(그 사이클의 `CYCLE` 줄)의 시각이고, 로그를 읽지 못했을 때는 그때의 시계입니다.
- **모양.** 표 하나에 저장소의 모든 기록을 한 줄씩, `detected_at` 이 늦은 차례(같으면 `video_id` 역순)로 보입니다.
  칸은 영상(제목 링크와 ID) · 판별(`verdict · reason`) · 판단한 쪽 · 타이밍(`verdict · reason` 과 시간당 조회수, 명단 영상의
  이유는 `allowlisted`) · 고민 한 줄 · 댓글 · 게시 결과(결과 배지와 그 시각, 이유 배지)입니다.
  영상 설명 · 인기 댓글 · 채널 · 검색어 · 자체 검사 이유는 화면에 싣지 않습니다.
- **판단한 쪽.** 그 영상의 마지막 `CLASSIFY` 줄의 `judge=`, 그 줄에 없으면 그 줄 앞 마지막 `START` 줄의 `judge=` 입니다.
  둘 다 없거나(Phase 7B 전의 줄) 저장된 판별이 없는 영상(오류 보류)이면 빈칸입니다.
- **늦은 로그 줄.** 그 영상(`video=`)의 `SKIP` · `ERROR` · `POST … mode=test result=rehearsed` 줄 가운데 저장소의 마지막 결과
  (판별 시각 · 타이밍 시각 · 댓글 시각 · 마지막 시도 시각 가운데 가장 늦은 것)와 같은 초이거나 그보다 늦은 줄입니다 — 로그 시각이 초 단위라 같은 초는 늦은 쪽으로 셉니다.
  타이밍은 새 표본마다 다시 판정해 그 시각이 그 영상을 마지막으로 다룬 때이므로, 그 뒤 다시 적히지 않은 지난 주기의 이유 · 리허설은 쓰지 않습니다.
  판별 칸이 빈 영상(판별 보류)은 타이밍 시각을 세지 않습니다 — 보류 때도 같은 주기에 타이밍이 판정되어 그 시각이 판별 오류 줄보다 늦기 때문입니다.
  세는 시각이 하나도 없으면 그 영상의 그런 줄 모두입니다. 그보다 이른 줄은 이유로 쓰지 않습니다.
- **결과 배지.** 늦은 로그 줄 가운데 파일에서 마지막 줄이 리허설 `POST` 이면 "리허설 — 게시 버튼 앞에서 멈춤" 입니다.
  아니면 저장소의 마지막 시도로 정합니다 — `live/posted` "게시됨" · `live/reserved` "게시 결과 모름 — 로그 참고" ·
  `live/failed` "게시 실패 — 로그 참고" · `test/saved` 는 그 시도 `reason` 의 이름표(아래 표)입니다.
  시도도 리허설도 없으면 댓글이 있을 때 "게시 기록 없음", 없을 때 "댓글 안 씀" 입니다.
  결과 배지 아래에는 그 결과의 시각(시도의 `at`, 리허설 줄의 시각)을 KST 초로 적습니다 — 지난 사이클의 결과일 수 있습니다.
- **이유 배지.** 늦은 로그 줄 가운데 파일에서 마지막 줄이 `SKIP` 이면 그 `reason=` 의 이름표, `ERROR` 이면 그 `where=` 의 이름표입니다.
  마지막 줄이 리허설이거나 늦은 줄이 없으면 이유 배지는 없습니다.
- **이름표.** 이유 글이 아래 코드와 정확히 같거나 아래 머리말로 시작하면 그 이름표이고, 아니면 "기타 — 로그 참고" 입니다.
  `where=` 는 아래 단계와 정확히 같을 때 그 이름표이고, 아니면 "기타 — 로그 참고" 입니다.
  로그 줄의 글(`reason=` · `where=` · `detail=` · `page_url=` · `screenshot=` 등)은 화면에 한 글자도 옮기지 않습니다.
  새 건너뜀 · 오류 이유를 더하는 페이즈가 이 표에 한 줄을 더합니다.

  | 코드 · 머리말 | 이름표 |
  |---|---|
  | `channel_cooldown` | 같은 채널 대기 중 |
  | `daily_cap` | 하루 상한에 닿음 |
  | `duplicate_video` | 이미 처리한 영상 |
  | `not_in_allowlist` | 허용 목록 밖이라 게시하지 않음 |
  | `invalid_video` | 영상 주소를 읽을 수 없음 |
  | `invalid_item` | 영상 정보를 읽을 수 없음 |
  | `dry_run` | 테스트 실행 — 저장만 |
  | `no_comment` | 댓글 없음 |
  | `config_rejected` | 설정 거절로 저장만 |
  | `page_mismatch` | 열린 화면이 다른 영상이라 저장만 |
  | `unavailable` | 영상을 볼 수 없음 |
  | `재료에 장면 없음`으로 시작 | 작성 건너뜀 — 짚을 장면 없음 |
  | `재료에 연애 고민 없음`으로 시작 | 작성 건너뜀 — 연애 고민 없음 |
  | `검사 두 번 탈락`으로 시작 | 검사 두 번 탈락 |
  | `claude 호출 실패`로 시작 | AI 호출 오류 (Claude) |
  | `jev 검사 호출 실패`로 시작 | AI 호출 오류 (jev 검사) |
  | `jev 검사 응답 이상`으로 시작 | AI 응답 이상 (jev 검사) |

  | `where=` | 이름표 |
  |---|---|
  | `classify` · `run.classify` | 판별 단계 오류 |
  | `run.trigger` | 타이밍 단계 오류 |
  | `commentThreads.list` | 인기 댓글을 받지 못함 |
  | `writer.claude` | AI 호출 오류 (Claude) |
  | `writer.jev` | AI 호출 오류 (jev 검사) |
  | `run.write` | 작성 단계 오류 |
  | `poster` · `run.post` | 게시 단계 오류 |
- **바깥 글.** 제목 · 판별 이유 · 타이밍 이유 · 고민 · 댓글 · 판단한 쪽은 `html.escape`(따옴표 포함)를 거친 글자로 들어가고, 줄 경계는 `<br>` 입니다.
  영상 링크는 코드가 영상 ID 로 만든 `https://www.youtube.com/watch?v=<ID>` 뿐이고, 바깥 주소 · 리허설 캡처 경로는 넣지 않습니다.
  외부 스크립트 · 글꼴 · 스타일 파일을 불러오지 않습니다.
- **쓰기.** `data/` 를 만들고 `data/report.html.tmp` 에 UTF-8 로 쓴 뒤 `os.replace` 로 바꿔 끼웁니다(저장소 `save` 와 같은 길).
- **실패.** 로그를 읽지 못하면(`OSError` · `ValueError`) `ERROR where=report reason=<예외 종류>: <메시지>` 한 줄을 쓰고, 이유 배지를 모두
  "로그를 읽지 못함" 으로, 리허설 · 판단한 쪽을 비운 채 저장소 칸으로 화면을 씁니다. 화면을 만들거나 쓰다 난 그 밖의 `Exception` 도
  `ERROR where=report` 한 줄로 남기고 사이클은 그대로 끝납니다. `KeyboardInterrupt` 같은 `BaseException` 은 그대로 올라갑니다.
- **음성 대조.** `python3 -m tests.mutants <이름>` — `report-late-filter-off` · `report-floor-trigger-off` · `report-floor-hold-counts-trigger` ·
  `report-raw-reason` · `report-unescaped` · `report-prefix-anywhere` · `run-report-fence-narrow` · `run-report-log-degrade-silent`.

## 공개용 사본 — `tests/public_copy.py` (Phase 8)

공개는 이 저장소가 아니라, 비공개 개발 하네스의 경로를 모든 커밋에서 지운 사본으로 합니다(트래커 Phase 8). 사본을 만들고 push 하는 일은 사람이 합니다.

```
python3 -m tests.public_copy [--source <저장소>] [--branch main] [--dest <빈 새 폴더>] [--known <목록 파일>] [--env <.env> | --no-env]
python3 -m tests.public_copy --scan-only [--branch <리비전>] [--env <.env> | --no-env]
python3 -m tests.public_copy --print-known [--branch <리비전>]
```

- **복제.** `--source`(기본: 이 파일이 든 저장소)의 가지 `--branch`(기본 `main`) 하나를 `git clone --no-local --no-tags --single-branch` 로 `--dest`(주지 않으면 새 임시 폴더)에 복제합니다. `--dest` 가 비어 있지 않은 폴더이거나 원본 안이면 아무것도 만들지 않고 종료 코드 2 입니다. 원본에는 아무것도 쓰지 않습니다. 사본의 가지는 `main` 하나이고 원격은 지웁니다. 이 스크립트는 push 하지 않습니다.
- **다시 쓰기.** `HARNESS_PATHS` 여덟 경로(원본에 추적되지 않는 `.adw/harness-paths` 가 있으면 그 줄도 더함)와 그 아래를 `git filter-branch --index-filter` 로 사본의 모든 커밋에서 지우고, 같은 다시 쓰기에서 커밋 메시지 안의 홈 경로(`HOME_PATH_RE` 꼴)를 `~/` 로 바꿉니다. 빈 커밋도 지우지 않아 커밋 수와 작성자 · 커미터의 이름 · 메일 · 날짜는 원본 가지와 같습니다. 메시지는 홈 경로만 다르고, 커밋 번호(해시)는 모두 바뀝니다. 지난 커밋의 파일 내용은 하네스 경로를 지울 뿐 고치지 않습니다.
- **검사.** 아래 아홉 가지 중 하나라도 걸리면 종료 코드 1 이고 사본은 지우지 않고 남깁니다 — 그 사본은 push 하지 않습니다. 모두 통과하면 0 입니다.

  | 검사 | 보는 곳 | 걸리는 것 |
  |---|---|---|
  | 하네스 경로 | 모든 커밋의 파일 경로 | 여덟 경로나 그 아래 |
  | 무시 규칙 경로 | 모든 커밋의 파일 경로 | 사본 끝 판의 `.gitignore` 가 무시하는 경로 — `.env`(`.env.example` 밖), `docs/marketing-agent.pdf`, 8절의 크롬 프로필 이름, `chrome-profile/` |
  | 연락처 모양 | 모든 커밋의 파일 내용과 커밋 메시지 | `tests/live_check.py` 의 연락처 모양(Phase 6G)으로 찾은 글 중 알려진 목록 밖 |
  | 키 모양 | 모든 커밋의 파일 내용과 커밋 메시지 | `KEY_SHAPES` 로 찾은 글 중 알려진 목록 밖 |
  | 비밀 값 | 모든 커밋의 파일 내용과 커밋 메시지 | `--env`(기본: 원본의 `.env`)에 든 세 키 값과 그 앞 8글자 이상 조각(`tests/live_check.py` 의 `Redactor`) — 파일이 없거나 세 값이 모두 비면 이 검사가 걸리고, `--no-env` 를 주면 건너뜁니다 |
  | 홈 경로 | 끝 판의 파일 내용과 모든 커밋 메시지 | `/home/<이름>/` · `/Users/<이름>/` · `C:\Users\<이름>\` 꼴 중 알려진 목록 밖 |
  | 스위트 | 끝 판 | 1절의 테스트 명령이 종료 코드 0 과 `OK` 로 끝나지 않음 |
  | 커밋 수 · 이름표 | 모든 커밋 | 원본 가지와 커밋 수, 또는 차례대로 본 작성자 · 커미터의 이름 · 메일 · 날짜가 다름 |
  | 원격 | 사본 | 원격이 하나라도 있음 |

  작성자 · 커미터의 메일은 내용 검사에 넣지 않습니다(트래커 Phase 8 질문 2 B — 이름표는 그대로 둠). 걸린 비밀 값은 화면에 쓰지 않고 키 이름과 자리만 보입니다.
- **알려진 목록.** `tests/public_copy_known.json` 의 `contacts` · `keys` · `homes` 는 사람이 가짜나 공개된 글로 확인한 글자 그대로입니다. 한 글자라도 다르면 목록 밖입니다. 이 파일 자신은 내용 검사에서 뺍니다. 걸린 글은 목록에 붙여 넣을 수 있는 꼴(JSON 글자)과 자리(경로 · 커밋)로 보입니다. 진짜 연락처나 키는 목록에 넣는 대신 그 사본을 push 하지 않고, 사본에서 지울 규칙을 사람이 정합니다 — 이 저장소의 기록은 다시 쓰지 않습니다(트래커 Phase 8 질문 1 A).
- **원본 훑기.** `--scan-only` 는 복제와 다시 쓰기 없이 원본의 `--branch`(아무 리비전)를 읽기만 하며, 하네스 경로를 뺀 채 무시 규칙 경로 · 연락처 모양 · 키 모양 · 비밀 값 · 홈 경로 다섯 검사를 봅니다(무시 규칙은 원본 작업 폴더의 `.gitignore`, 홈 경로는 끝 판 파일만 — 메시지의 홈 경로는 사본이 바꿉니다). `--print-known` 은 같은 범위에서 모양 검사 셋이 찾은 글을 목록 파일 꼴로 보이기만 하고 판정하지 않습니다(종료 코드 0).
