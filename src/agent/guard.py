"""허용 목록 가드 — 실제 게시를 정하는 유일한 함수 decide_post 가 여기 있습니다.

게시 버튼을 누르기 바로 직전에 decide_post 를 불러야 합니다. 허용 목록 밖의 영상은
언제나 테스트 모드이고, 이 판단을 건너뛰게 하는 설정 · 인자 · 환경 변수는 없습니다.
허용 목록 항목은 11자 영상 ID 로 바꿔 비교하며, 읽을 수 없는 항목은 어떤 영상과도
맞지 않습니다.

주소는 계약 5절의 형식만 정확히 읽습니다 — 가드와 브라우저가 같은 주소를 다르게 읽을
자리를 남기지 않기 위해서입니다. dry_run 은 정확히 False 일 때만 실제 게시로 갑니다.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit

from agent.models import VIDEO_ID_RE

_YOUTUBE_HOSTS = frozenset({"youtube.com", "www.youtube.com", "m.youtube.com"})
_SHORTS_PREFIX = "/shorts/"
# youtu.be · shorts 쿼리에서 받는 이름 — 공유 버튼이 붙이는 셋뿐입니다. 막을 이름 대신 받을 이름을 적어,
# 유튜브가 어떤 이름으로 재생 영상을 바꾸든 처음 보는 이름은 읽지 않는 쪽에 떨어집니다(계약 5절).
_SHARE_QUERY_NAMES = frozenset({"si", "t", "feature"})


@dataclass(frozen=True)
class PostDecision:
    """게시 판단. live 가 거짓이면 테스트 모드(저장만 하고 게시하지 않음)입니다."""

    video_id: str | None
    live: bool
    reason: str

    @property
    def mode(self) -> str:
        return "live" if self.live else "test"


def video_id_from_ref(ref: str) -> str | None:
    """영상 ID 나 유튜브 주소에서 11자 영상 ID 를 꺼냅니다. 못 꺼내면 None.

    받는 주소는 계약 5절의 형식뿐입니다 — youtu.be 는 경로가 정확히 `/<ID>`, shorts 는
    `/shorts/<ID>`(뒤 `/` 하나 허용), watch 는 `v` 값이 정확히 하나. 호스트 자리는 이름
    그대로여야 하고(사용자 정보 · 포트 없음), `\\` 가 든 주소는 읽지 않습니다. 경로의 `%` ·
    `.`/`..` 칸은 이 모양들을 통과하지 못합니다. 쿼리는 서버처럼 한 번 풀어(`%76` 은 `v`,
    `+` 는 공백) `&` 와 `;` 를 모두 매개변수 구분으로 봅니다. youtu.be · shorts 는 쿼리의 이름이
    모두 `si` · `t` · `feature` 중 하나와 대소문자까지 같을 때만 읽고 값은 보지 않습니다 — 그 밖의
    이름(`v` · `V` · `%56` · `+v` · 전각 v · 제어 문자가 붙은 v · `list` · 빈 이름 · 처음 보는 이름)이
    하나라도 있으면 읽지 않습니다. 막을 이름 대신 받을 이름을 적어, 유튜브가 어떤 이름으로 재생
    영상을 바꾸든 처음 보는 꼴은 읽지 않는 쪽에 떨어집니다. watch 는 `v` 를 푼 뒤에 세고 다른
    이름은 무시합니다(크롬 주소의 꼬리를 아직 재기 전 — H-023).
    """
    text = ref.strip()
    if VIDEO_ID_RE.fullmatch(text):
        return text
    if "\\" in text:
        return None
    try:
        parts = urlsplit(text)
    except ValueError:
        return None
    if parts.scheme not in ("http", "https"):
        return None
    host = parts.netloc.lower()
    pairs = parse_qsl(parts.query.replace(";", "&"), keep_blank_values=True)
    share_query = all(key in _SHARE_QUERY_NAMES for key, _ in pairs)
    if host == "youtu.be" and share_query:
        candidate = parts.path[1:]
    elif host in _YOUTUBE_HOSTS and parts.path == "/watch":
        values = [value for key, value in pairs if key == "v"]
        candidate = values[0] if len(values) == 1 else ""
    elif host in _YOUTUBE_HOSTS and parts.path.startswith(_SHORTS_PREFIX) and share_query:
        rest = parts.path[len(_SHORTS_PREFIX):]
        candidate = rest[:-1] if rest.endswith("/") else rest
    else:
        return None
    return candidate if VIDEO_ID_RE.fullmatch(candidate) else None


def allowed_video_ids(allowed_videos: Iterable[str]) -> frozenset[str]:
    """허용 목록을 영상 ID 집합으로 바꿉니다. 읽을 수 없는 항목은 버립니다."""
    ids = (video_id_from_ref(entry) for entry in allowed_videos)
    return frozenset(video_id for video_id in ids if video_id is not None)


def decide_post(video_ref: str, allowed_videos: Iterable[str], dry_run: bool) -> PostDecision:
    """실제 게시 여부를 정합니다: 읽을 수 없는 영상 → 허용 목록 밖 → 테스트 모드 플래그 순.

    dry_run 은 정확히 False 일 때만 실제 게시 — None · 0 · "" 같은 값은 테스트 모드입니다.
    """
    video_id = video_id_from_ref(video_ref)
    if video_id is None:
        return PostDecision(None, False, "invalid_video")
    allowed = allowed_video_ids(allowed_videos)
    if video_id not in allowed:
        return PostDecision(video_id, False, "not_in_allowlist")
    if dry_run is not False:
        return PostDecision(video_id, False, "dry_run")
    return PostDecision(video_id, True, "allowlisted")
