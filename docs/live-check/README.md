# 실제 호출 실행기 — 실행 안내 (Phase 6A · 6C)

1. 예시 22개의 정답 라벨을 훑습니다 — `tests/classifier_examples.py` 의 `EXAMPLES` 에서 `label` 이 제목 · 설명과 맞는지 봅니다(H-010). 틀린 라벨이 있으면 돌리지 말고 인터뷰로 옵니다.
2. 저장소 main 체크아웃의 뿌리에서 `.env.example` 을 `.env` 로 복사하고 `ANTHROPIC_API_KEY` · `YOUTUBE_API_KEY` · `TYPESAFE_API_KEY` 를 채웁니다. `.env` 는 커밋되지 않습니다(`.gitignore`). 실행은 이 main 체크아웃에서 합니다 — 레인 worktree 에는 `.env` 가 없습니다(레인은 커밋된 main 으로 만들어짐).
3. 이 기계에는 `pip` 이 없고 `uv` 가 있습니다. 저장소 뿌리에서:

       ~/.local/bin/uv venv
       ~/.local/bin/uv pip install -r requirements.txt

4. 실행합니다 — 진짜 jev · Claude · YouTube 를 부릅니다. 크롬 연결 · 게시는 하지 않습니다.

       .venv/bin/python -m tests.live_check

   - YouTube 호출은 운영과 같은 쿼터 장부 `data/quota.json` 을 씁니다. 검색은 많아야 키워드 수 × 2번(지금 10번, 1,000단위)이라 그날 운영 검색 몫이 그만큼 줄어듭니다.
   - 서비스마다 실행기 호출 천장(jev 120 · Claude 110 · YouTube 50)에 닿으면 그 자리에서 멈추고 결과에 적습니다. Claude 호출은 판별한 영상마다 영상 판별 채점 한 번이 더해집니다. 천장은 실행기가 부른 수이고, SDK 안의 다시 시도(Claude 는 호출당 많아야 2번 더, jev 는 SDK 기본 정책)는 따로입니다.
   - 서비스가 느리면 오래 걸릴 수 있습니다. Ctrl-C 로 멈추면 그때까지의 결과를 쓰고 판정에 `중단` 으로 적습니다.
   - 키나 SDK 가 없으면 아무것도 부르지 않고 없는 것을 한 줄로 알립니다(종료 코드 2).
   - 다시 돌리면 결과 두 파일을 덮어씁니다.
   - 결과 두 파일은 main 에 커밋하지 않습니다 — main 에 새 결과를 커밋하면 `tests.test_live_check_applied` 가 빨강이 됩니다(계약의 기록이 옛 결과의 숫자). 사람 칸의 다른 값(`ok` · `bad` 밖의 글)은 정답 없음으로 세어 빨강이 되지 않습니다. 결과는 그 다시 반영 페이즈(Phase 6D 다음은 6E 가 작성기를 고친 뒤의 Phase 6F)의 레인 브랜치에만 커밋합니다(9).
5. 화면 첫 줄이 판정입니다 — `6B: go` 또는 `6B: stop — <경우와 숫자>`. 결과는 `docs/live-check/result.json` 과 `docs/live-check/summary.md` 이고, 요약의 첫 줄도 같은 판정입니다. `재지 못함` 이면 요약의 `오류:` 줄(서비스 · 단계 · 상태)이 원인입니다 — 키 · 크레딧 · API 설정 문제일 수 있습니다. `채점 막힘` 이면 요약의 `채점 답 모양:` 줄과 `result.json` 초안의 `grade_shape` 칸이 원인입니다. 함께 나오면 `재지 못함` 의 오류 줄부터 봅니다 — 그 줄에 `claude` · `grade` 가 있으면 채점 호출이 실패한 것이고, 없으면 채점 막힘의 원인은 `채점 답 모양:` 줄입니다.
6. 화면 마지막 줄이 `키 검사: 결과 파일에 키 없음` 인지 봅니다. 다른 줄이면 커밋하지 말고 인터뷰로 옵니다.
7. 채점을 훑고, 동의하지 않는 것만 사람 칸에 적습니다 — 건너뛰어도 됩니다. 판정 줄은 사람 칸과 무관합니다.
   - 초안: `result.json` 의 `videos[].drafts[]` 마다 `claude_grade`(`ok` / `bad`)를 보고, 동의하지 않으면 그 초안의 `"human": ""` 을 `"human": "ok"` 또는 `"human": "bad"` 로 고칩니다.
   - 영상 판별: `videos[]` 마다 `topic_grade`(`연애` / `아님`)를 보고, 동의하지 않으면 그 영상의 `"topic_human": ""` 을 `"topic_human": "연애"` 또는 `"topic_human": "아님"` 으로 고칩니다. 제목과 설명은 그 영상의 `untrusted` 칸에 있습니다.
8. 판정이 `stop` 이면 결과를 9 처럼 레인 브랜치에 커밋하되 그 페이즈를 진행하지 않고 인터뷰로 옵니다. `go` 면 커밋한 뒤 그 페이즈를 시작합니다.
9. 결과 두 파일을 다시 반영 페이즈의 레인 브랜치에 커밋합니다. 허브가 그 페이즈의 레인을 아직 만들지 않았으면 먼저 만듭니다 — 레인을 만들면 그 페이즈의 사이클이 시작되어 결과 커밋 전에 `unmeasured` 로 한 번 멈출 수 있고, 두 파일을 커밋한 뒤 이어 갑니다. main 체크아웃의 뿌리에서:

       cp docs/live-check/result.json docs/live-check/summary.md ~/adw-lanes/marketing-agent-demo/6f/marketing-agent-demo/docs/live-check/ && git restore docs/live-check/result.json docs/live-check/summary.md

   그다음 레인 worktree 의 뿌리에서:

       git add docs/live-check/result.json docs/live-check/summary.md && git commit -m "docs(live-check): 실제 호출 결과 — Phase 6C 실행기"

   `git restore` 는 main 체크아웃의 두 파일을 커밋된 옛 결과로 되돌립니다 — main 은 옛 결과 그대로여야 초록입니다. 명령의 경로는 다시 반영 페이즈의 레인 경로입니다 — main 체크아웃의 뿌리에서 `python3 .claude/skills/plan/scripts/lane.py status` 가 그 레인의 `name` 과 `path` 를 찍고, 명령의 `6f` 는 허브가 Phase 6F 의 레인을 `6f` 로 만들었을 때의 모양이라 다르면 찍힌 `path` 로 바꿉니다. 복사가 실패하면(레인 경로가 없음) `git restore` 를 돌리지 않습니다.
