from __future__ import annotations

import socket
from datetime import datetime

from gate_control.domain.constants import CMD_ALARM_EVENT, CMD_CARD_EVENT, CMD_CARD_STATUS_EVENT, CMD_HEARTBEAT
from gate_control.domain.errors import CommandTimeoutError, MissingHeartbeatError
from gate_control.domain.models import CommandResult, ControllerConfig, HeartbeatStatus, SessionState
from gate_control.protocol import commands
from gate_control.protocol.frames import Frame, extract_frames
from gate_control.protocol.parser import parse_alarm_event, parse_card_event, parse_card_status_event, parse_heartbeat, parse_response
from gate_control.utils.hex import to_hex

from .transport import TcpTransport


class GateClientSession:
    def __init__(self, config: ControllerConfig, timeout: float = 5.0) -> None:
        self.config = config
        self.transport = TcpTransport(config.host, config.port, timeout=timeout)
        self.timeout = timeout
        self.state = SessionState()
        self._buffer = bytearray()

    @property
    def heartbeat(self) -> HeartbeatStatus | None:
        return self.state.heartbeat

    def connect(self) -> None:
        self.transport.connect()
        self.state.connected = True

    def close(self) -> None:
        self.transport.close()
        self.state.connected = False

    def require_heartbeat(self) -> HeartbeatStatus:
        if self.state.heartbeat is None:
            raise MissingHeartbeatError("heartbeat/status has not been received yet")
        return self.state.heartbeat

    def receive_once(self, timeout: float | None = None) -> list[Frame]:
        if timeout is not None and self.transport.socket is not None:
            self.transport.socket.settimeout(timeout)
        try:
            data = self.transport.recv()
        except socket.timeout:
            return []
        finally:
            if timeout is not None and self.transport.socket is not None:
                self.transport.socket.settimeout(self.timeout)

        if not data:
            self.close()
            return []

        self._buffer.extend(data)
        frames = extract_frames(self._buffer)
        for frame in frames:
            self._handle_frame(frame)
        return frames

    def wait_for_heartbeat(self, timeout: float = 10.0) -> HeartbeatStatus | None:
        deadline = datetime.now().timestamp() + timeout
        while datetime.now().timestamp() < deadline:
            self.receive_once(timeout=max(0.1, min(1.0, deadline - datetime.now().timestamp())))
            if self.state.heartbeat is not None:
                return self.state.heartbeat
        return None

    def send_command(self, payload: bytes, timeout: float = 3.0, expect_response: bool = True) -> CommandResult:
        command = payload[2]
        self.state.busy = True
        self.state.last_command = command
        try:
            self.transport.send(payload)
            if not expect_response:
                return CommandResult(True, command, request=payload, message="sent")

            deadline = datetime.now().timestamp() + timeout
            while datetime.now().timestamp() < deadline:
                frames = self.receive_once(timeout=max(0.1, min(1.0, deadline - datetime.now().timestamp())))
                for frame in frames:
                    if frame.command == command:
                        result = parse_response(frame.raw, expected_command=command)
                        result.request = payload
                        return result
            raise CommandTimeoutError(f"timeout waiting for command 0x{command:02X}")
        finally:
            self.state.busy = False

    def monitor(self) -> None:
        while self.state.connected:
            frames = self.receive_once(timeout=1.0)
            for frame in frames:
                print(f"RX {to_hex(frame.raw, ' ')}")

    def _handle_frame(self, frame: Frame) -> None:
        self.state.last_rx_at = datetime.now()
        if frame.command == CMD_HEARTBEAT:
            heartbeat = parse_heartbeat(frame)
            self.state.heartbeat = heartbeat
            ack = commands.ack_heart(heartbeat.index_cmd, self.config.oem_code)
            self.transport.send(ack)
            return

        serial_no = self.state.heartbeat.serial_no if self.state.heartbeat else None
        if frame.command == CMD_CARD_EVENT:
            event = parse_card_event(frame, serial_no=serial_no)
            self.state.events.append(event)
            self.transport.send(commands.history_event_ack(CMD_CARD_EVENT, event.return_index))
            return

        if frame.command == CMD_ALARM_EVENT:
            event = parse_alarm_event(frame)
            self.state.events.append(event)
            self.transport.send(commands.history_event_ack(CMD_ALARM_EVENT, event.return_index))
            return

        if frame.command == CMD_CARD_STATUS_EVENT:
            event = parse_card_status_event(frame)
            self.state.events.append(event)
            self.transport.send(commands.history_event_ack(CMD_CARD_STATUS_EVENT, event.return_index))
