# 기술 결정 조사 — 로그인된 크롬 연결 방식 (⑤ 게시)

조사일 2026-10-12. 과제 문구: "로그인해둔 크롬을 `--remote-debugging-port=9222`로 실행 → Playwright `connect_over_cdp`로 연결".

## Decision brief
- Candidates: A 전용 프로필 크롬(`--user-data-dir`를 기본이 아닌 경로로 지정, 그 프로필에서 한 번 로그인) · B Chrome for Testing(자동화 전용 빌드) · C 평소 쓰는 기본 프로필 크롬(과제 문구 그대로)
- A: 비기본 데이터 디렉터리 + 원격 디버깅 포트는 동작. 로그인은 전용 프로필에서 1회 필요 (https://www.browserless.io/blog/chrome-remote-debugging, https://intellij-support.jetbrains.com/hc/en-us/articles/38172473762706)
- B: 크롬 팀이 자동화 용도로 권장하며 기존 동작 유지 (https://developer.chrome.com/blog/remote-debugging-port)
- C: 불가 — Chrome 136부터 `--remote-debugging-port`와 `--remote-debugging-pipe`가 기본 데이터 디렉터리에서는 무시됨 (https://developer.chrome.com/blog/remote-debugging-port). 한 보고서는 Chrome 151에서도 같은 현상을 확인 (https://github.com/trycua/cua/issues/2916)
- Recommendation: A — 과제의 "로그인해둔 크롬" 요구를 살리면서 실제로 동작하는 유일한 경로 (because C는 136+에서 포트 자체가 열리지 않음)
- Red flags: C를 택하면 게시 단계 전체가 실패. 쿠키·프로필 디렉터리는 저장소에 올리면 안 됨 (PDF p.8 체크리스트 — `.gitignore` 확인)
