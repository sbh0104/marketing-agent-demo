"""공개용 사본 — 비공개 하네스 경로를 모든 커밋에서 지운 사본을 새 폴더에 만들고 검사합니다(계약 '공개용 사본' 절).

    python3 -m tests.public_copy [--source <저장소>] [--branch main] [--dest <빈 새 폴더>] [--known <목록 파일>] [--env <.env> | --no-env]
    python3 -m tests.public_copy --scan-only [--branch <리비전>] [--env <.env> | --no-env]
    python3 -m tests.public_copy --print-known [--branch <리비전>]

종료 코드: 0 모든 검사 통과 · 1 검사 실패(사본은 지우지 않고 남깁니다 — push 하지 마세요) · 2 준비 실패.
원본은 읽기만 하고, 다시 쓰기는 새 복제본에서만 합니다. 이 스크립트는 push 하지 않습니다.
이 파일은 test*.py 가 아니라서 discover 가 줍지 않습니다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# 연락처 모양 · 키 값 가림은 tests/live_check.py (_contact_spans) · (Redactor) 를 그대로 부릅니다 — Phase 6G · 6A
from tests.live_check import KEY_NAMES, Redactor, _contact_spans
from agent.env import EnvError, read_env_file

REPO = Path(__file__).resolve().parent.parent
# 비공개 하네스 경로 — 이름만 둡니다. .adw/harness-paths 는 git 이 추적하지 않아 복제본에서 읽을 수 없습니다
HARNESS_PATHS = (
    ".claude",
    "docs/agents.html",
    ".adw/.gitignore",
    ".adw/cycle.yml",
    ".adw/workflow.yml",
    ".adw/workflow-ui.yml",
    ".adw/workflow-smoke.yml",
    ".adw/CLAUDE_sample.md",
)
HARNESS_LIST = ".adw/harness-paths"
KNOWN_FILE = Path(__file__).with_name("public_copy_known.json")
KNOWN_PATH = "tests/public_copy_known.json"
KNOWN_KEYS = ("contacts", "keys", "homes")
SUITE_ARGS = (
    "-X", "warn_default_encoding", "-W", "error::EncodingWarning",
    "-m", "unittest", "discover", "-s", "tests", "-t", ".",
)
EXIT_OK, EXIT_FAILED, EXIT_SETUP = 0, 1, 2
SHOW_MAX = 50

# 키 모양 — 알려진 접두어 뒤의 긴 키 글자, 또는 세 키 이름에 `=` 로 붙은 긴 값(대소문자 그대로 봅니다)
KEY_SHAPES = (
    r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{16,}",
    r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{35}",
    r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,}",
    r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{22,}",
    r"(?<![A-Za-z0-9])GOCSPX-[A-Za-z0-9_\-]{20,}",
    r"(?:YOUTUBE|TYPESAFE|ANTHROPIC)_API_KEY[ \t]*=[ \t]*[\"']?[A-Za-z0-9_\-]{16,}",
)
KEY_RE = re.compile("|".join(KEY_SHAPES))
# 홈 폴더 안으로 들어가는 경로 — 리눅스 · 맥의 홈 아래 이름 하나, 윈도우 드라이브의 Users 아래 이름 하나까지
HOME_PATH_RE = re.compile(
    r"(?:/(?:home|Users)/|(?<![A-Za-z])[A-Za-z]:[\\/]+Users[\\/]+)[A-Za-z0-9._\-]+[\\/]",
    re.IGNORECASE,
)
# filter-branch 의 --msg-filter — 메시지 안의 홈 경로를 `~/` 로 바꾸는 한 문장짜리 파이썬
MSG_FILTER_CODE = (
    "__import__('sys').stdout.buffer.write(__import__('re').sub("
    f"{HOME_PATH_RE.pattern!r}, '~/', "
    "__import__('sys').stdin.buffer.read().decode('utf-8', 'surrogateescape'), "
    "flags=__import__('re').IGNORECASE).encode('utf-8', 'surrogateescape'))"
)
HINT = (
    "알려진 가짜나 공개된 글이면 tests/public_copy_known.json 에 위 글자를 더해 커밋하세요. "
    "진짜 값이면 이 사본을 push 하지 마세요 — 이 저장소의 기록은 다시 쓰지 않으므로"
    "(트래커 Phase 8 질문 1 A) 사본에서 지울 규칙을 사람이 정합니다"
)
ENV_HINT = "  --env 로 실제 키를 쓴 .env 를 주거나, 키를 쓰지 않았으면 --no-env"
IDENTITY_FORMAT = "--format=%an%x00%ae%x00%cn%x00%ce%x00%at%x00%ct"


class SetupError(Exception):
    """사본을 만들거나 읽을 준비가 안 됨 — 종료 코드 2."""


@dataclass(frozen=True)
class Known:
    """사람이 가짜나 공개된 글로 확인한 글자 — 한 글자라도 다르면 목록 밖입니다."""

    contacts: frozenset[str]
    keys: frozenset[str]
    homes: frozenset[str]


@dataclass(frozen=True)
class Text:
    """검사할 글 하나와 그 자리 — `<경로> @ <커밋>` 또는 `커밋 <커밋> 메시지`."""

    where: str
    body: str


@dataclass
class Walk:
    """한 리비전에서 닿는 모든 커밋 — 경로와 blob 은 처음 본 커밋을 기억합니다."""

    rev: str
    tip_commit: str
    paths: dict[str, str] = field(default_factory=dict)
    blobs: dict[str, tuple[str, str]] = field(default_factory=dict)
    blob_paths: dict[str, set[str]] = field(default_factory=dict)
    tip: dict[str, str] = field(default_factory=dict)
    messages: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Check:
    """검사 하나의 결과 — details 가 비어 있으면 통과입니다."""

    name: str
    details: list[str]
    skipped: bool = False
    hint: bool = False
    count: int | None = None

    @property
    def failed(self) -> bool:
        return bool(self.details) and not self.skipped

    def lines(self) -> list[str]:
        if self.skipped:
            return [f"– {self.name} — 건너뜀 (--no-env)"]
        if not self.failed:
            return [f"✓ {self.name}"]
        count = len(self.details) if self.count is None else self.count
        lines = [f"✗ {self.name} — {count}곳", *self.details[:SHOW_MAX]]
        if len(self.details) > SHOW_MAX:
            lines.append(f"  … 외 {len(self.details) - SHOW_MAX}곳")
        if self.hint:
            lines.append(f"  {HINT}")
        return lines


def git(
    repo: Path,
    *args: str,
    input: str | None = None,
    ok: tuple[int, ...] = (0,),
    env: dict[str, str] | None = None,
) -> str:
    """repo 에서 git 한 번 — 받는 종료 코드 밖이면 SetupError(git 의 마지막 오류 줄)."""
    try:
        done = subprocess.run(
            ["git", "-C", str(repo), *args],
            input=input,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=env,
        )
    except OSError as exc:
        raise SetupError(f"git 을 실행할 수 없습니다: {exc}") from exc
    if done.returncode not in ok:
        tail = [line for line in done.stderr.splitlines() if line.strip()]
        reason = tail[-1] if tail else f"종료 코드 {done.returncode}"
        raise SetupError(f"git {args[0]} 실패 — {reason}")
    return done.stdout


def harness_paths(source: Path) -> tuple[str, ...]:
    """HARNESS_PATHS 에 원본의 추적 안 되는 HARNESS_LIST 줄을 더한 것 — 중복 없이, 상수가 먼저."""
    entries = list(HARNESS_PATHS)
    listed = Path(source) / HARNESS_LIST
    if listed.is_file():
        for raw in listed.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                entries.append(line.rstrip("/"))
    return tuple(entry for entry in dict.fromkeys(entries) if entry)


def is_under(path: str, entries: Iterable[str]) -> bool:
    """path 가 목록의 한 경로와 같거나 그 아래인지."""
    return any(path == entry or path.startswith(entry + "/") for entry in entries)


def load_known(path: Path) -> Known:
    """알려진 목록 — contacts · keys · homes 만 든 JSON 객체, 값은 글자 목록."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SetupError(f"알려진 목록이 없습니다: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SetupError(f"알려진 목록을 읽을 수 없습니다: {path} ({exc})") from exc
    if not isinstance(data, dict) or sorted(data) != sorted(KNOWN_KEYS):
        raise SetupError(f"알려진 목록은 {' · '.join(KNOWN_KEYS)} 만 든 JSON 객체여야 합니다: {path}")
    for name in KNOWN_KEYS:
        items = data[name]
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise SetupError(f"알려진 목록의 {name} 는 글자 목록이어야 합니다: {path}")
    return Known(*(frozenset(data[name]) for name in KNOWN_KEYS))


def walk(repo: Path, rev: str, exclude: Sequence[str] = ()) -> Walk:
    """`git rev-list <rev>` 의 커밋마다 `git ls-tree -r -z` — exclude 아래 경로는 빼고 봅니다."""
    tip_commit = git(repo, "rev-parse", "--short", rev).strip()
    walked = Walk(rev=rev, tip_commit=tip_commit)
    for commit in git(repo, "rev-list", "--abbrev-commit", rev).split():
        for path, blob in _tree(repo, commit, exclude):
            walked.paths.setdefault(path, commit)
            walked.blobs.setdefault(blob, (path, commit))
            walked.blob_paths.setdefault(blob, set()).add(path)
    walked.tip = dict(_tree(repo, rev, exclude))
    for record in git(repo, "log", "-z", "--format=%h%x01%B", rev).split("\0"):
        if record:
            commit, _, message = record.partition("\x01")
            walked.messages.append((commit, message))
    return walked


def _tree(repo: Path, treeish: str, exclude: Sequence[str]) -> list[tuple[str, str]]:
    """한 커밋의 (경로, blob) — 하위 모듈 같은 blob 아닌 항목은 뺍니다."""
    entries: list[tuple[str, str]] = []
    for entry in git(repo, "ls-tree", "-r", "-z", treeish).split("\0"):
        if not entry:
            continue
        meta, _, path = entry.partition("\t")
        _mode, kind, blob = meta.split()
        if kind == "blob" and not is_under(path, exclude):
            entries.append((path, blob))
    return entries


def read_blobs(repo: Path, blobs: Sequence[str]) -> dict[str, str]:
    """blob 내용을 `git cat-file --batch` 한 번으로 — 바이트로 받아 UTF-8 로 읽고 깨진 글자는 바꿉니다."""
    if not blobs:
        return {}
    try:
        done = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "--batch"],
            input="".join(f"{blob}\n" for blob in blobs).encode("ascii"),
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise SetupError(f"git 을 실행할 수 없습니다: {exc}") from exc
    if done.returncode:
        raise SetupError("git cat-file 실패")
    out, pos, texts = done.stdout, 0, {}
    for blob in blobs:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        if len(header) != 3:
            raise SetupError(f"blob 을 읽을 수 없습니다: {blob}")
        size = int(header[2])
        texts[blob] = out[end + 1 : end + 1 + size].decode("utf-8", errors="replace")
        pos = end + 1 + size + 1
    return texts


def message_texts(walked: Walk) -> list[Text]:
    return [Text(f"커밋 {commit} 메시지", message) for commit, message in walked.messages]


def history_texts(repo: Path, walked: Walk) -> list[Text]:
    """모든 커밋의 서로 다른 blob(알려진 목록 파일만인 blob 은 뺌)과 모든 커밋 메시지."""
    blobs = [
        blob for blob, paths in walked.blob_paths.items() if paths != {KNOWN_PATH}
    ]
    contents = read_blobs(repo, blobs)
    texts = []
    for blob in blobs:
        path, commit = walked.blobs[blob]
        texts.append(Text(f"{path} @ {commit}", contents[blob]))
    return texts + message_texts(walked)


def tip_texts(repo: Path, walked: Walk) -> list[Text]:
    """끝 판의 파일 내용 — 알려진 목록 파일은 뺍니다."""
    tip = [(path, blob) for path, blob in walked.tip.items() if path != KNOWN_PATH]
    contents = read_blobs(repo, list(dict.fromkeys(blob for _path, blob in tip)))
    return [Text(f"{path} @ {walked.tip_commit}", contents[blob]) for path, blob in tip]


def check_harness(walked: Walk, entries: Sequence[str]) -> Check:
    details = [
        f"  {path} @ {commit}" for path, commit in walked.paths.items() if is_under(path, entries)
    ]
    return Check("하네스 경로", details)


def check_ignored(walked: Walk, work_tree: Path) -> Check:
    """모든 커밋의 경로를 work_tree 의 무시 규칙에 묻습니다 — git 이 내놓는 경로만 걸립니다."""
    details: list[str] = []
    if walked.paths:
        out = git(
            work_tree,
            "check-ignore", "--no-index", "--stdin", "-z",
            input="".join(f"{path}\0" for path in walked.paths),
            ok=(0, 1),
        )
        details = [f"  {path} @ {walked.paths[path]}" for path in out.split("\0") if path]
    return Check("무시 규칙 경로", details)


def _shape_check(
    name: str, texts: Iterable[Text], known: Iterable[str], find: Callable[[str], list[str]]
) -> Check:
    known = frozenset(known)
    details = [
        f"  {json.dumps(found, ensure_ascii=False)} ← {text.where}"
        for text in texts
        for found in dict.fromkeys(find(text.body))
        if found not in known
    ]
    return Check(name, details, hint=True)


def find_contacts(body: str) -> list[str]:
    return [body[start:end] for start, end in _contact_spans(body)]


def check_contacts(texts: Iterable[Text], known: Iterable[str]) -> Check:
    return _shape_check("연락처 모양", texts, known, find_contacts)


def check_keys(texts: Iterable[Text], known: Iterable[str]) -> Check:
    return _shape_check("키 모양", texts, known, KEY_RE.findall)


def check_homes(texts: Iterable[Text], known: Iterable[str]) -> Check:
    return _shape_check("홈 경로", texts, known, HOME_PATH_RE.findall)


def check_secret_values(texts: Iterable[Text], env: Path | None) -> Check:
    """env 의 세 키 값과 그 앞 조각이 글에 있는지 — 자리와 키 이름만 적고 값은 쓰지 않습니다."""
    name = "비밀 값"
    if env is None:
        return Check(name, [], skipped=True)
    try:
        values = read_env_file(env)
    except EnvError as exc:
        return Check(name, [f"  {exc}", ENV_HINT], count=1)
    redactors = {key: Redactor({key: values[key]}) for key in KEY_NAMES if values.get(key)}
    if not redactors:
        return Check(name, [ENV_HINT])
    details = [
        f"  {key} 값 ← {text.where}"
        for text in texts
        for key, redact in redactors.items()
        if redact(text.body) != text.body
    ]
    return Check(name, details)


def check_suite(tree: Path) -> Check:
    """tree 에서 계약 1절의 테스트 명령 — 종료 코드 0 이고 stderr 마지막 줄이 OK 로 시작해야 통과."""
    done = subprocess.run(
        [sys.executable, *SUITE_ARGS],
        cwd=tree,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    lines = [line for line in done.stderr.splitlines() if line.strip()]
    if done.returncode == 0 and lines and lines[-1].startswith("OK"):
        return Check("스위트", [])
    details = [f"  {line}" for line in lines[-3:]] or [f"  종료 코드 {done.returncode}"]
    return Check("스위트", details, count=1)


def check_history(source: Path, branch: str, copy: Path) -> Check:
    """원본 가지와 사본 main 의 커밋 수 · 차례대로 본 이름표 — 메일은 화면에 쓰지 않습니다."""
    before = git(source, "log", IDENTITY_FORMAT, branch).splitlines()
    after = git(copy, "log", IDENTITY_FORMAT, "main").splitlines()
    if len(before) != len(after):
        return Check("커밋 수 · 이름표", [f"  커밋 수 — 원본 {len(before)} · 사본 {len(after)}"])
    for position, (old, new) in enumerate(zip(before, after), start=1):
        if old != new:
            detail = f"  최신부터 {position}번째 커밋의 이름 · 메일 · 날짜가 원본과 다릅니다"
            return Check("커밋 수 · 이름표", [detail])
    return Check("커밋 수 · 이름표", [])


def check_remote(copy: Path) -> Check:
    return Check("원격", [f"  {name}" for name in git(copy, "remote").split()])


def _prepare_dest(source: Path, dest: Path | None) -> Path:
    if dest is None:
        return Path(tempfile.mkdtemp(prefix="public-copy-"))
    dest = dest.resolve()
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise SetupError(f"--dest 는 없거나 빈 폴더여야 합니다: {dest}")
    if dest == source or source in dest.parents:
        raise SetupError(f"--dest 가 원본 안입니다: {dest}")
    return dest


def _clone(source: Path, branch: str, dest: Path) -> None:
    git(
        source,
        "clone", "-q", "--no-local", "--no-tags", "--single-branch", "--branch", branch,
        "--", str(source), str(dest),
    )
    current = git(dest, "symbolic-ref", "--short", "HEAD").strip()
    if current != "main":
        git(dest, "branch", "-m", current, "main")
    git(dest, "remote", "remove", "origin")


def _rewrite(dest: Path, entries: Sequence[str]) -> None:
    """사본의 모든 커밋에서 하네스 경로를 지우고 메시지의 홈 경로를 바꿉니다 — 한 번의 filter-branch."""
    remove = shlex.join(["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", *entries])
    rename = shlex.join([sys.executable, "-c", MSG_FILTER_CODE])
    env = {**os.environ, "FILTER_BRANCH_SQUELCH_WARNING": "1"}
    git(
        dest,
        "-c", "commit.gpgsign=false",
        "filter-branch", "-f", "--index-filter", remove, "--msg-filter", rename, "--", "main",
        env=env,
    )
    for ref in git(dest, "for-each-ref", "--format=%(refname)", "refs/original/").split():
        git(dest, "update-ref", "-d", ref)
    git(dest, "reflog", "expire", "--expire=now", "--all")
    git(dest, "gc", "--prune=now", "-q")
    if git(dest, "status", "--porcelain").strip():
        raise SetupError(f"다시 쓴 뒤 사본의 작업 폴더가 깨끗하지 않습니다: {dest}")


def _env_path(args: argparse.Namespace, source: Path) -> Path | None:
    if args.no_env:
        return None
    return args.env if args.env is not None else source / ".env"


def _print(checks: Sequence[Check]) -> int:
    for check in checks:
        for line in check.lines():
            print(line)
    return sum(check.failed for check in checks)


def run_copy(args: argparse.Namespace) -> int:
    source = args.source.resolve()
    try:
        known = load_known(args.known)
        dest = _prepare_dest(source, args.dest)
    except SetupError as exc:
        print(f"준비 실패 — {exc}")
        return EXIT_SETUP
    print(f"사본: {dest}")
    env = _env_path(args, source)
    try:
        entries = harness_paths(source)
        _clone(source, args.branch, dest)
        _rewrite(dest, entries)
        walked = walk(dest, "main")
        texts = history_texts(dest, walked)
        checks = [
            check_harness(walked, entries),
            check_ignored(walked, dest),
            check_contacts(texts, known.contacts),
            check_keys(texts, known.keys),
            check_secret_values(texts, env),
            check_homes(tip_texts(dest, walked) + message_texts(walked), known.homes),
            check_suite(dest),
            check_history(source, args.branch, dest),
            check_remote(dest),
        ]
    except SetupError as exc:
        print(f"준비 실패 — {exc}")
        return EXIT_SETUP
    failed = _print(checks)
    if failed:
        print(f"공개용 사본 검사 실패 — 검사 {failed}개 · 이 사본은 push 하지 마세요")
        return EXIT_FAILED
    skipped = " · 비밀 값 건너뜀" if env is None else ""
    print(f"공개용 사본 검사 통과 — {dest}{skipped}")
    return EXIT_OK


def _source_walk(args: argparse.Namespace) -> tuple[Path, Walk]:
    source = args.source.resolve()
    git(source, "rev-parse", "--verify", "--quiet", f"{args.branch}^{{commit}}")
    return source, walk(source, args.branch, exclude=harness_paths(source))


def run_scan_only(args: argparse.Namespace) -> int:
    """복제 · 다시 쓰기 없이 원본의 리비전을 읽기만 합니다 — 검사 2–6."""
    try:
        known = load_known(args.known)
        source, walked = _source_walk(args)
        env = _env_path(args, source)
        texts = history_texts(source, walked)
        checks = [
            check_ignored(walked, source),
            check_contacts(texts, known.contacts),
            check_keys(texts, known.keys),
            check_secret_values(texts, env),
            check_homes(tip_texts(source, walked), known.homes),
        ]
    except SetupError as exc:
        print(f"준비 실패 — {exc}")
        return EXIT_SETUP
    failed = _print(checks)
    if failed:
        print(f"공개 전 검사 실패 — 검사 {failed}개")
        return EXIT_FAILED
    skipped = " · 비밀 값 건너뜀" if env is None else ""
    print(f"공개 전 검사 통과 — {args.branch}{skipped}")
    return EXIT_OK


def run_print_known(args: argparse.Namespace) -> int:
    """--scan-only 와 같은 범위에서 모양 검사 셋이 찾은 글 — 판정하지 않고 목록 파일 꼴로만."""
    try:
        source, walked = _source_walk(args)
        texts = history_texts(source, walked)
        tip = tip_texts(source, walked)
    except SetupError as exc:
        print(f"준비 실패 — {exc}")
        return EXIT_SETUP
    found = {
        "contacts": {item for text in texts for item in find_contacts(text.body)},
        "keys": {item for text in texts for item in KEY_RE.findall(text.body)},
        "homes": {item for text in tip for item in HOME_PATH_RE.findall(text.body)},
    }
    print(json.dumps({name: sorted(found[name]) for name in KNOWN_KEYS}, ensure_ascii=False, indent=2))
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m tests.public_copy",
        description="비공개 하네스 경로를 모든 커밋에서 지운 공개용 사본을 만들고 검사합니다(push 하지 않음).",
    )
    parser.add_argument("--source", type=Path, default=REPO, help="원본 저장소 (기본: 이 파일이 든 저장소)")
    parser.add_argument("--branch", default="main", help="사본을 만들 가지 · 훑을 리비전 (기본 main)")
    parser.add_argument("--dest", type=Path, help="사본을 만들 없거나 빈 폴더 (기본: 새 임시 폴더)")
    parser.add_argument("--known", type=Path, default=KNOWN_FILE, help="알려진 목록 파일")
    secrets = parser.add_mutually_exclusive_group()
    secrets.add_argument("--env", type=Path, help="실제 키를 쓴 .env (기본: 원본의 .env)")
    secrets.add_argument("--no-env", action="store_true", help="비밀 값 검사를 건너뜁니다")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scan-only", action="store_true", help="복제 없이 원본을 읽기만 합니다")
    mode.add_argument("--print-known", action="store_true", help="모양 검사가 찾은 글을 목록 꼴로")
    args = parser.parse_args(argv)
    if (args.scan_only or args.print_known) and args.dest is not None:
        print("준비 실패 — --dest 는 사본을 만들 때만 씁니다")
        return EXIT_SETUP
    if args.print_known:
        return run_print_known(args)
    if args.scan_only:
        return run_scan_only(args)
    return run_copy(args)


if __name__ == "__main__":
    sys.exit(main())
