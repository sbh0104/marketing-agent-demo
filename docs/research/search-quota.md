# 기술 결정 조사 — 검색 쿼터 · 주기 · 키워드 수 (① 탐지)

조사일 2026-10-12. 과제 기준: 30분마다 검색, 무료 쿼터 하루 약 100회 검색 (PDF p.3).

## Decision brief
- Candidates: 설정 파일 기본값(30분 × 키워드 5개) / 30분 × 키워드 2개 / 2시간 × 키워드 5개
- 계산: 하루 검색 호출 = (24 × 60 ÷ 주기분) × 키워드 수. 30분이면 48 × 키워드 수
- 쿼터: 프로젝트 기본 10,000 units/일, `search.list` 1회 = 100 units → 약 100회/일 (https://developers.google.com/youtube/v3/determine_quota_cost, https://developers.google.com/youtube/v3/getting-started)
- 30분 × 키워드 5개 = 240회/일 → 쿼터의 약 2.4배, 그대로 돌리면 쿼터 초과
- 30분 × 키워드 2개 = 96회/일 → 여유 4회. 페이지 넘김과 조회수 확인 호출은 별도 비용 (Google: 추가 페이지도 쿼터 소비)
- 2시간 × 키워드 5개 = 60회/일 → 여유 있음, 대신 '뜨기 직전' 판단의 시간 해상도가 떨어짐
- Recommendation: 아직 없음 — 주기와 키워드 수 사이의 trade-off이므로 사용자 결정 (because 쿼터 수치는 확정, 어느 쪽을 줄일지는 제품 판단)
- Red flags: 설정 파일 예시(키워드 5개 · 30분)는 쿼터를 초과. 조회수 추적 호출의 정확한 단위 비용은 이번 조사에서 공식 표로 확인하지 못함 — 구현 전 재확인

## Decision (Phase 2 plan, 2026-10-13)
- 후보 (b) 2시간 × 키워드 5개 = 하루 60회 — `poll_interval_min: 120`. (a) 는 페이지 넘김 여유가 하루 4회뿐이라 가드가 하루 후반 탐지를 끊습니다.
- `limits.daily_max_searches: 90` — 9,000 단위. 남는 1,000 단위는 조회수 호출 몫.
- `videos.list` = 1 단위, ID 50개까지 한 번에. 비용표는 `src/agent/youtube.py` 의 `UNIT_COST` 한 곳이고, 공식 표 재확인은 사람 확인으로 남깁니다.
- 하루 = 굴러가는 24시간 (Google 리셋은 태평양 자정 — 계약 11절).
- 정정 2026-10-14: Google 은 2026-10-08 부터 `search.list` 를 하루 100회짜리 별도 통으로 셉니다
  (https://developers.google.com/youtube/v3/determine_quota_cost, "Last updated 2026-10-08 UTC").
  위 Decision brief 의 쿼터 줄은 그 전 표이고, `daily_max_searches: 90` 줄의 9,000 단위는 이제
  Google 의 셈이 아니라 장부의 셈입니다. 장부는 트래커 Phase 2 결정 HC1 질문 2 A 대로 일부러
  엄격한 옛 계산(10,000 단위 통에서 검색 1회 100)을 유지합니다 — 옛 규칙과 새 규칙 모두에서
  넘치지 않습니다.
