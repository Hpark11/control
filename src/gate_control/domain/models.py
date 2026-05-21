from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ControllerConfig:
    host: str
    port: int
    oem_code: int = 23456
    name: str = "default"
    serial_no: str | None = None
    last_verified_at: str | None = None


@dataclass(slots=True)
class HeartbeatStatus:
    serial_no: str
    datetime: datetime | None
    door_status: int
    input_status: int
    system_option: int
    card_num_in_pack: int
    version: str
    oem_code: int
    index_cmd: int
    cmd_ok: int


@dataclass(slots=True)
class CardEvent:
    card_no: str
    event_type: int
    reader: int
    door: int
    return_index: int
    datetime: datetime | None
    serial_no: str | None = None


@dataclass(slots=True)
class AlarmEvent:
    event_type: int
    door: int
    return_index: int
    datetime: datetime | None


@dataclass(slots=True)
class CardStatusEvent:
    card_index: int
    anti_passback_value: int
    return_index: int


@dataclass(slots=True)
class CommandResult:
    ok: bool
    command: int
    response: bytes | None = None
    message: str = ""
    ack: int | None = None


@dataclass(slots=True)
class SessionState:
    connected: bool = False
    busy: bool = False
    last_command: int | None = None
    last_rx_at: datetime | None = None
    heartbeat: HeartbeatStatus | None = None
    events: list[object] = field(default_factory=list)
