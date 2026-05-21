from __future__ import annotations

import socket

from gate_control.domain.errors import GateConnectionError


class TcpTransport:
    def __init__(self, host: str, port: int, timeout: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: socket.socket | None = None

    @property
    def connected(self) -> bool:
        return self.socket is not None

    def connect(self) -> None:
        if self.socket is not None:
            return
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            sock.settimeout(self.timeout)
            self.socket = sock
        except OSError as exc:
            raise GateConnectionError(f"failed to connect {self.host}:{self.port}: {exc}") from exc

    def close(self) -> None:
        sock = self.socket
        self.socket = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def send(self, data: bytes) -> None:
        if self.socket is None:
            raise GateConnectionError("socket is not connected")
        self.socket.sendall(data)

    def recv(self, size: int = 4096) -> bytes:
        if self.socket is None:
            raise GateConnectionError("socket is not connected")
        return self.socket.recv(size)

    def __enter__(self) -> "TcpTransport":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.close()
