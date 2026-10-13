# 계약 — Phase 1 뼈대

Phase 2–7 의 모든 단계가 기대는 계약입니다. 설정 읽기, 영상 기록 모양, 저장소 규칙,
허용 목록 가드, 게시 흐름, 로그 형식, 주기 실행을 여기서 정합니다. 코드는
`src/agent/` 패키지(`config.py` · `models.py` · `store.py` · `guard.py` · `logbook.py` ·
`scheduler.py`)에 있습니다.

## 1. 실행

- Python 3.10 이상. 3.11 이후에만 있는 기능(`datetime.UTC`, `enum.StrEnum`, `tomllib`,
  `typing.Self`, `except*`)은 쓰지 않습니다.
- 의존성 설치: `pip install -r requirements.txt` — 지금은 `PyYAML>=6.0` 한 줄입니다.
  Phase 6 이 Playwright 를 더합니다.
- 테스트(저장소 뿌리에서, 설치 없이):

  ```
  python3 -X warn_default_encoding -W error::EncodingWarning -m unittest discover -s tests -t .
  ```

  `tests/__init__.py` 가 `src/` 를 `sys.path` 맨 앞에 넣으므로 패키지를 설치하지 않아도
  됩니다. `-W error::EncodingWarning` 때문에 `encoding=` 없이 파일을 여는 코드는 리눅스에서도
  실패합니다 — 윈도우 인코딩 사고를 미리 막는 장치입니다.
- 실행 진입점(`run.py`, `--dry-run`, `--once`)은 Phase 7 이 더합니다. `--dry-run` 은
  `decide_post(..., dry_run=True)` 로 그대로 넘어가야 합니다(5절).

## 2. 설정 — `config.yaml`

`load_config(path)` 가 읽고 `config_from_mapping` 이 검사합니다. **모든 키가 필요하고,
모르는 키는 오류이며, 타입은 정확해야 합니다.** 오류는 `ConfigError` 로, 메시지가 점으로 이은
키 경로(`limits.daily_max_searches`)나 줄 번호(`3번째 줄: …`)를 말합니다.

| 키 | 타입 | 규칙 | 과제 기본값 |
|---|---|---|---|
| `topic` | 글자 | 비어 있지 않음 | `연애` |
| `keywords` | 글자 목록 | 1개 이상, 각 항목 비어 있지 않음 | `[연애, 썸, 연애 상담, 이별, 소개팅]` |
| `poll_interval_min` | 정수 | ≥ 1 | `30` |
| `trigger.min_views` | 정수 | ≥ 0 | `1000` |
| `trigger.max_views` | 정수 | ≥ `min_views` | `5000` |
| `trigger.max_age_hours` | 숫자 | > 0 | `12` |
| `trigger.min_views_per_hour` | 숫자 | ≥ 0 | `150` |
| `limits.daily_max_comments` | 정수 | ≥ 0 | `10` |
| `limits.channel_cooldown_hours` | 숫자 | ≥ 0 | `24` |
| `limits.daily_max_searches` | 정수 | ≥ 0 | `100` (과제 밖에서 더한 키) |
| `comment.min_chars` | 정수 | ≥ 1 | `40` |
| `comment.max_chars` | 정수 | ≥ `min_chars` | `120` |
| `chrome_debug_url` | 글자 | `http://` 또는 `https://` 로 시작 | `http://localhost:9222` |
| `allowed_videos` | 글자 목록 | 비워 두면 `()`; 항목은 쓴 그대로 보관 | `- https://youtu.be/내-테스트-영상-ID` |

- "정수"는 bool 을 받지 않습니다. "숫자"는 정수나 실수(bool 제외)이고 실수로 저장됩니다.
- `limits.daily_max_searches` 는 과제 예시에 없는 키입니다. Phase 2 의 하루 검색 상한을
  설정 값으로 두기 위해 지금 계약에 넣었습니다(쿼터 약 100회/일). Phase 2 가 값을 조정합니다.
- **YAML 1.1 함정은 크게 실패합니다.** 따옴표 없는 `yes`/`no`/`on`/`off` 는 bool,
  `2026-10-12` 는 날짜, `12345678901` 은 정수로 읽히므로 글자 자리에 오면 오류입니다
  (예: `keywords: [연애, no]`, `topic: yes`, `allowed_videos: [12345678901]`). 이런 값은
  따옴표로 감싸세요.
- 같은 키가 두 번 나오면 두 번째 줄 번호와 함께 오류입니다. 윈도우 메모장이 붙이는 BOM 은
  떼어 내고 읽습니다. UTF-8 이 아닌 저장(메모장의 ANSI·Unicode)은 `ConfigError` 입니다.
- 읽는 중 나는 그 밖의 모든 오류도 `ConfigError` 입니다 — 날짜 모양의 틀린 값
  (`topic: 2026-02-30`), 4300자를 넘는 정수, 실수로 바꿀 수 없는 큰 정수
  (`max_age_hours: 1000…0`), 아주 깊은 중첩. 메시지는
  `설정 값을 읽을 수 없습니다 (<원인 종류>: <원인>): <경로>` 이고 원인은 `__cause__` 에
  남습니다. `KeyboardInterrupt` 는 바꾸지 않고 그대로 올라갑니다.
- 주기 루프는 사이클마다 `config.yaml` 을 다시 읽습니다(9절). 실행 중에 값을 고치면 다음
  대기부터 적용되고, 잘못 고친 파일은 이전 설정을 유지합니다.

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
  | `test` | `saved` | 테스트 모드 저장 — `reason` 에 `PostDecision.reason` |

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
  - `https://youtu.be/abcdefghijk` — 경로가 정확히 `/<ID>` (뒤에 `?si=…` 등 매개변수는
    붙어도 됨, 단 `v` 는 안 됨)
  - `https://www.youtube.com/watch?v=abcdefghijk` — 경로가 정확히 `/watch`, `v` 값이 정확히
    하나 (`&t=…` 등 다른 매개변수 무시)
  - `https://www.youtube.com/shorts/abcdefghijk` — 뒤 `/` 하나까지 (`?feature=…` 등 매개변수는
    붙어도 됨, 단 `v` 는 안 됨)
  - 호스트는 `youtu.be` · `youtube.com` · `www.youtube.com` · `m.youtube.com` 그대로(대소문자
    무시) — 사용자 정보(`…@`)나 포트(`:443`)가 붙으면 읽지 않습니다. 스킴은 `http`/`https` 만.
- 쿼리의 `%` 인코딩은 서버처럼 한 번 풀어 읽습니다 — `v` 의 수는 푼 뒤에 세므로
  `?%76=B&v=A` 는 `v` 가 두 개라 읽을 수 없고, `&pp=…%3D%3D` · `&ab_channel=%EC…` 같은 다른
  매개변수는 무시됩니다.
- youtu.be · shorts 주소의 쿼리에 `v` 가 있으면 읽을 수 없습니다 — `v` 는 쿼리를 푼 뒤에
  세므로 `?%76=…` 도, 빈 `?v=` 도 `v` 입니다. 유튜브는 `youtu.be/A?v=B` 를 `watch?v=B&v=A` 로,
  `/shorts/A?v=B` 를 `watch?v=B` 로 보내 B 를 재생하기 때문입니다. 쿼리는 `&` 와 `;` 를 모두
  매개변수 구분으로 봅니다 — 서버가 `;` 로도 나눌 때 숨는 `v` 를 놓치지 않기 위해서이고
  (`?x=1;v=B`, HTML 에서 복사한 `?si=x&amp;v=B`), 그래서 `watch?v=<ID>;t=…` 도 `&` 와 같이
  읽힙니다. 막는 이름은 `v` 하나이고 `si` · `t` · `feature` 같은 다른 매개변수는 무시합니다 —
  유튜브가 다른 이름(대소문자 · 공백 · 전각 변형 포함)으로 재생 영상을 바꾸는 경우가 발견되면
  그때 더합니다.
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
5. **`reserve_live` 가 오류를 냈으면 절대 클릭하지 않습니다.**

- 3.1 · 3.2 는 가드와 브라우저가 같은 주소를 다르게 읽을 자리를 없애는 두 겹 잠금입니다(가드의
  엄격함 하나에만 기대지 않음). 다시 확인을 예약 앞에 두는 까닭은 확정되지 않은 예약은 게시로
  치므로(4절) 예약 뒤에는 테스트 모드로 바꿀 수 없기 때문입니다. 같은 영상인지도 보는 까닭은
  자동 재생 · 다음 영상으로 크롬이 다른 허용 영상으로 옮겨 가면 저장소가 확인하지 않은 영상에
  댓글이 달리기 때문입니다. `page_mismatch` 는 `decide_post` 의 이유가 아니라 게시 단계가 남기는
  테스트 저장 이유입니다. 유튜브가 중간 화면(로그인 · 동의)을 띄우면 정상 게시도 테스트 모드로
  빠질 수 있습니다 — 안전한 쪽 실패로 받아들입니다. Phase 6 이 지킵니다.

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
  | 글자 | 공백 · `"` · `=` · `\` 가 없고 `-` 가 아니면 그대로, 아니면 JSON 따옴표(한글 그대로) |
  | 그 밖 | `TypeError` |

  그래서 여러 줄짜리 댓글도 `\n` 으로 한 줄에 남고, 글자 `-` 는 `"-"` 로 써서 `None` 과
  구분됩니다.
- `parse_line(line)` 은 `format_line` 의 정확한 역으로 `(시각, Event, {키: 글자})` 를 돌려줍니다.
  Phase 7/8 은 이것으로 로그만 보고 허용 목록 밖 영상이 게시되지 않았음을 확인할 수 있습니다.
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
  커밋합니다. `.env.example` 에는 `YOUTUBE_API_KEY=` 가 있고, AI 접속 키 이름은 Phase 3 이
  더합니다. `.env` 를 읽는 코드는 비밀 값을 처음 읽는 Phase 2 가 더합니다.
- 크롬 전용 프로필은 `chrome-profile/`(통째로 무시됩니다) 또는 저장소 밖에만 둡니다 — 저장소
  안의 다른 폴더는 금지입니다. Phase 6 · 8 의 실행 안내는 이 두 위치만 예시로 보입니다. 이 위치
  규칙이 첫 방어입니다.
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
   유지합니다.
5. `wait = min(poll_interval_min × 60, 약 100년) − (monotonic() − started)` 만큼, 하루 이하
   조각으로 나눠 `sleep` 합니다. `wait` 가 0 이하이면 `sleep(0.0)` 을 한 번 부릅니다.

- 주기는 사이클 *시작* 부터 잽니다. 사이클이 주기보다 오래 걸리면 쉬지 않고 바로 다음 사이클을
  돕니다.
- 아주 큰 `poll_interval_min` 도 루프를 죽이지 않습니다 — sleep 한 번은 하루까지(운영체제마다
  다른 sleep 한도에 닿지 않게), 대기 전체는 약 100년까지(아주 큰 정수를 실수로 바꾸다 나는
  OverflowError 방지). 하루 이하 주기는 지금처럼 sleep 한 번이고, 설정 규칙
  (`poll_interval_min ≥ 1`)은 그대로입니다.
- `poll_interval_min` 만 고치면 재시작이나 OS 설정 없이 다음 대기부터 주기가 바뀝니다.
- 신호 처리나 fork 는 쓰지 않습니다. Phase 7 의 진입점이 `run_loop` 를 부릅니다.

## 10. 계약 변경 규칙

- 여기 적은 모양(설정 키, `VideoRecord` 필드, 시도 상태, `check_post` 이유, `decide_post`
  인자와 이유, 로그 사건과 필수 필드)은 고정입니다.
- 더하는 것은 그 필드를 쓰는 단계(Phase)가 `models.py` · `config.py` 에서, 테스트와 함께, 이
  문서도 함께 고칩니다. 이미 있는 이름의 뜻을 바꾸거나 지우지 않습니다.
- 가드 · 저장소 · 설정 읽기 규칙이 테스트로 지켜지는지는 음성 대조로 확인합니다. 각 명령은 가드 한 줄을
  메모리에서만 망가뜨리고 테스트를 돌리며, **종료 코드 1(테스트가 잡음)** 이어야 합니다. 2 는
  바꿀 글자를 찾지 못했다는 뜻이라 실패입니다:

  ```
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
  python3 -m tests.mutants store-no-dedupe
  python3 -m tests.mutants store-no-cap
  python3 -m tests.mutants store-no-cooldown
  python3 -m tests.mutants store-reserved-not-counted
  python3 -m tests.mutants store-put-overwrites-attempts
  python3 -m tests.mutants store-double-reserve
  python3 -m tests.mutants config-narrow-read-errors
  python3 -m tests.mutants scheduler-one-sleep
  python3 -m tests.mutants scheduler-unclamped-wait
  ```

  `decide_post` · `video_id_from_ref` · `put` · `reserve_live` · `check_post` · `load_config` ·
  `run_loop` 의 본문을 고칠 때는 이 명령들이 계속 1 로 끝나는지 함께 확인합니다.
