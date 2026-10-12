# 기술 결정 조사 — 구현 언어·런타임

조사일 2026-10-12. 대상: 탐지 · 판별 · 타이밍 · 작성 · 게시 다섯 모듈(과제 안내 PDF p.6 구조).

## Decision brief
- Candidates: Python + Playwright / TypeScript(Node.js) + Playwright
- Python + Playwright: 공식 문서가 `connect_over_cdp`를 Chromium 계열 전용 연결로 명시 (https://playwright.dev/python/docs/api/class-browsertype)
- TypeScript + Playwright: Node용 `connectOverCDP`는 검색 예제로만 확인, 공식 Node 레퍼런스는 이번 조사에서 미확인 — 채택 전 검증 필요
- Recommendation: Python + Playwright — 공식 문서가 Python 메서드명을 직접 명시하고, 다섯 모듈이 한 런타임이면 모듈 간 데이터 계약이 단순해 병렬 진행에 유리
- Red flags: 공식 문서는 `connect_over_cdp`가 Playwright 고유 프로토콜 `connect()`보다 "significantly lower fidelity"라고 경고 — 게시 단계에서 기능 제약이 나오면 `connect()` 또는 다른 도구를 재검토 (https://playwright.dev/python/docs/api/class-browsertype)
