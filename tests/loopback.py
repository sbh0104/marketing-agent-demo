"""날 바이트로 답하는 루프백 HTTP 서버 — 실제 http_get 을 이 컴퓨터 밖으로 내보내지 않고 잽니다. 음수 덩어리 크기 · 잘린 본문 · 깨진 Location · 조금씩 흘려 보내는 응답은 http.server 로 만들 수 없어 소켓에 바이트를 그대로 씁니다."""
from __future__ import annotations

import socket
import threading
import unittest
from collections.abc import Callable, Sequence
from unittest import mock

NEGATIVE_CHUNK = b"-2\r\nxx\r\n0\r\n\r\n"
_HEAD_CAP = 64 * 1024


def response(
    status: int,
    body: bytes = b"",
    *,
    reason: str = "X",
    headers: Sequence[str] = (),
    length: int | None = None,
) -> bytes:
    """상태 줄 · 머리 줄들 · Content-Length(length 를 주면 그 값) 뒤에 본문 — Connection 머리는 없습니다."""
    lines = [
        f"HTTP/1.1 {status} {reason}",
        *headers,
        f"Content-Length: {len(body) if length is None else length}",
    ]
    head = "".join(line + "\r\n" for line in lines) + "\r\n"
    return head.encode("latin-1") + body


def chunked(status: int, frames: bytes) -> bytes:
    """Transfer-Encoding: chunked 응답 — 덩어리 틀(frames)은 받은 그대로 씁니다."""
    head = f"HTTP/1.1 {status} X\r\nTransfer-Encoding: chunked\r\n\r\n"
    return head.encode("latin-1") + frames


def no_proxies(case: unittest.TestCase) -> None:
    """이 테스트 동안 환경의 프록시 설정을 비웁니다 — 루프백 요청이 프록시로 새지 않게."""
    patcher = mock.patch("urllib.request.getproxies", return_value={})
    patcher.start()
    case.addCleanup(patcher.stop)


class RawServer:
    """127.0.0.1 의 빈 포트에서 연결마다 route(target) 의 바이트를 그대로 답합니다.

    route 가 None 을 돌려주면 그 연결은 닫힐 때까지 말이 없습니다(멈춘 서버). drip_s 가 0 보다
    크면 앞 burst 바이트를 보낸 뒤 drip_s 마다 한 바이트씩 흘려 보냅니다. answer_first 면 요청을
    읽지 않고 연결 직후 route("") 를 보내고 닫습니다.
    """

    def __init__(
        self,
        route: Callable[[str], bytes | None],
        *,
        drip_s: float = 0.0,
        burst: int = 0,
        answer_first: bool = False,
    ) -> None:
        self._route = route
        self._drip_s = drip_s
        self._burst = burst
        self._answer_first = answer_first
        self.targets: list[str] = []
        self.heads: list[bytes] = []
        self.connections = 0
        self._stop = threading.Event()
        self._listener = socket.create_server(("127.0.0.1", 0))
        self._listener.settimeout(0.05)
        self.url = f"http://127.0.0.1:{self._listener.getsockname()[1]}"
        self._workers: list[threading.Thread] = []
        self._acceptor = threading.Thread(target=self._accept, name="RawServer", daemon=True)
        self._acceptor.start()

    def _accept(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            self.connections += 1
            worker = threading.Thread(
                target=self._serve, args=(conn,), name="RawServer-conn", daemon=True
            )
            self._workers.append(worker)
            worker.start()

    def _serve(self, conn: socket.socket) -> None:
        with conn:
            conn.settimeout(5.0)
            try:
                if self._answer_first:
                    reply = self._route("")
                    if reply is not None:
                        conn.sendall(reply)
                    return
                head = b""
                while b"\r\n\r\n" not in head and len(head) < _HEAD_CAP:
                    data = conn.recv(4096)
                    if not data:
                        return
                    head += data
                self.heads.append(head)
                self.targets.append(head.split(b" ", 2)[1].decode("latin-1"))
                reply = self._route(self.targets[-1])
                if reply is None:
                    self._stop.wait()
                    return
                if self._drip_s <= 0:
                    conn.sendall(reply)
                    return
                conn.sendall(reply[: self._burst])
                for n in range(self._burst, len(reply)):
                    if self._stop.wait(self._drip_s):
                        return
                    conn.sendall(reply[n : n + 1])
            except OSError:
                return

    def close(self) -> None:
        self._stop.set()
        self._acceptor.join(2)
        self._listener.close()
        for worker in self._workers:
            worker.join(2)

    def __enter__(self) -> RawServer:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
