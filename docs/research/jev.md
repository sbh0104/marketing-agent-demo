# 기술 결정 조사 — systemone model jev (② 판별 · ④ 자체 검사)

조사일 2026-10-12. 출처: 사용자가 준 https://typesafe.ai/blog/introducing-system-one-models-and-jev 와 공식 문서 https://docs.typesafe.ai (llms.txt 색인).

## 무엇인가
- TypeSafe의 System One 모델. 글(state)과 미리 정한 질문을 받고, 정해진 답 중 하나를 확률과 함께 돌려준다.
- 질문 모양은 세 가지: `choice` (보기 중 하나, 최대 255개) · `score` (순서 있는 단계 2–10개) · `noul` (예/아니오 확률 0–1). 한 요청에 여러 질문을 섞어 보내면 서로 독립적으로 평가된다.
- **글을 생성하지 않는다** — "It does not generate text, write code, or hold a conversation." (https://docs.typesafe.ai/introduction/coding-agents). 그래서 댓글 작성(④)은 jev가 할 수 없다.

## 접속
- 엔드포인트: `POST https://api.typesafe.ai/v1/systemone`, 헤더 `Authorization: Bearer <API_KEY>` (https://docs.typesafe.ai/api)
- 키: 환경 변수 `TYPESAFE_API_KEY` (SDK가 자동으로 읽음) — 이 프로젝트에서는 `.env`에 둔다
- Python SDK: `pip install typesafe-sdk`, `from typesafe_sdk import Choice, Noul, Score, TypeSafeClient` (https://docs.typesafe.ai/introduction/quickstart)
- 모델: `jev-latest` (현재 `jev-1.13.0`을 가리킴) (https://docs.typesafe.ai/models)
- 요청 예: `{"state": "...", "model": "jev-latest", "questions": {"is_urgent": {"type": "noul", "instructions": "Does this convey urgency?"}}}`
- 응답 예: `"department": {"type": "choice", "choice": "billing", "probabilities": {...}, "confidence": 0.81}`
- 오류: `401` 키 문제 · `422` 요청 형식 오류 · `429` 속도 제한 · `529` 과부하 — 429/529는 지수 백오프 재시도 (SDK 기본 정책이 처리)
- 얼리 액세스: 콘솔 https://console.typesafe.ai/ 에서 대기 명단으로 발급

## 한도와 비용
- 요청당 64k 토큰, 그중 `state`와 가장 긴 질문이 32k 토큰까지 — 긴 자막은 잘라서 보낸다
- 속도 제한: 초당 100K 토큰 / 초당 80 요청
- 요금: 입력 100만 토큰당 $0.042, 출력 무료. 영상 1개 ≈ 5,000 토큰이면 하루 100개 판별에 약 $0.02
- 응답 시간: 70–500ms (블로그)

## 알려진 약점 (https://docs.typesafe.ai/model-jaggedness/jev-1.13)
- 언어: 영어가 주 학습 언어. 한국어 같은 CJK도 처리하지만 정확도가 같지 않음 — "자기 데이터로 먼저 시험" (models 페이지)
- 질문을 글자 그대로 읽는다 (부정·범위 표현 주의) · 이중 부정과 여러 단계 추론에 약함
- 숫자 세기·계산·날짜 비교를 못 한다 — 글자 수, 조회수 계산, 업로드 시각 비교는 코드가 한다
- `choice`에서 첫 번째 보기로 기우는 경향
- state 안의 지시문(프롬프트 주입)에 흔들릴 수 있음 — 영상 설명·댓글은 신뢰하지 않는 입력
- 관계없는 내용이 많을수록 정확도가 떨어짐 (context rot)

## Decision brief
- Candidates (댓글 작성 담당): Claude + jev 판단 / 다른 LLM + jev 판단 / jev만으로 미리 쓴 문장 고르기 / 그대로 둠
- Recommendation: Claude가 쓰고 jev가 판단·검사 (because jev는 글을 생성하지 않고, 문서가 판단은 jev · 글은 LLM 짝짓기를 권장 — intent-routing 패턴)
- 결정: 사용자가 A 선택 (2026-10-12)
- Red flags: 한국어 정확도 미검증 · 얼리 액세스 키가 없으면 mock으로만 검증 가능 · 이유(reason)를 문장으로 받을 수 없음 → 보기 이름 + 확률로 기록

## SDK 확인 — typesafe-sdk 0.7.4 (2026-10-13)
- **출처.** PyPI 의 wheel 소스를 설치하지 않고 읽었다. Python ≥3.10 이 필요하고, 의존성은 httpx2 · pydantic · tenacity 이며 다시 시도는 tenacity 가 한다.
- **클라이언트.** `TypeSafeClient(api_key=None → 환경 변수 TYPESAFE_API_KEY)` 는 `with` 블록으로 쓴다. `system_one(state, questions, *, model=…)` 이 `SystemOneResponse` 를 돌려준다.
- **응답.** `answers: dict[질문 id, 답]`. `nouls` · `choices` · `scores` 는 같은 answers 를 거른 보기다. `NoulAnswer.noul: float` 에는 confidence 가 없다. `ChoiceAnswer` 에는 `choice: str` · `probabilities: dict[str, float]` · `confidence: float` 가 있다.
- **질문.** `Noul(instructions=…, criteria=NoulCriteria(true=…, false=…))` — `NoulCriteria` 는 TypedDict 다. `Choice(instructions=…, criteria={보기: 설명 또는 None})`.
- **오류.** 모든 오류는 `TypeSafeError` 아래에 있다.
  - HTTP 실패는 `TypeSafeAPIError` 이고 코드는 `.status` 에 있다: 400 BadRequest · 401 Authentication · 403 PermissionDenied · 404 NotFound · 422 UnprocessableEntity · 429 RateLimit. 529 를 포함한 5xx 도 `TypeSafeAPIError` 의 하위 클래스다.
  - 연결 · 시간 초과 실패는 `TypeSafeAPIConnectionError` · `TypeSafeAPITimeoutError` 다.
  - 검증을 통과하지 못한 응답은 `TypeSafeAPIResponseValidationError` 다.
