from __future__ import annotations

from gate_control.domain.constants import ACK_FAIL, ACK_OK, CMD_ALARM_EVENT, CMD_CARD_EVENT, CMD_CARD_STATUS_EVENT, CMD_HEARTBEAT
from gate_control.domain.models import AlarmEvent, CardEvent, CardStatusEvent, CommandResult, HeartbeatStatus
from gate_control.domain.errors import ProtocolError
from gate_control.utils.time import safe_datetime

from .frames import Frame, parse_frame


def parse_heartbeat(frame: Frame) -> HeartbeatStatus:
    raw = frame.raw
    if len(raw) < 40:
        raise ProtocolError("heartbeat frame is too short")

    year = raw[7] + 2000
    month = raw[8]
    day = raw[9]
    hour = raw[10]
    minute = raw[11]
    second = raw[12]
    serial = raw[27:33].decode("ascii", errors="ignore").strip("\x00 ")
    return HeartbeatStatus(
        serial_no=serial,
        datetime=safe_datetime(year, month, day, hour, minute, second),
        door_status=raw[13],
        card_num_in_pack=raw[14],
        system_option=raw[16],
        version=str(raw[24]),
        oem_code=int.from_bytes(raw[25:27], "little", signed=False),
        input_status=int.from_bytes(raw[33:35], "little", signed=False),
        index_cmd=int.from_bytes(raw[35:39], "little", signed=False),
        cmd_ok=raw[39],
    )


def parse_card_event(frame: Frame, serial_no: str | None = None) -> CardEvent:
    raw = frame.raw
    if len(raw) < 21:
        raise ProtocolError("card event frame is too short")
    card_no = int.from_bytes(raw[7:11], "little", signed=False)
    event = raw[17]
    return CardEvent(
        card_no=str(card_no),
        event_type=event & 0x7F,
        reader=(event & 0x80) >> 7,
        door=raw[18],
        return_index=raw[20],
        datetime=safe_datetime(raw[16] + 2000, raw[15], raw[14], raw[13], raw[12], raw[11]),
        serial_no=serial_no,
    )


def parse_alarm_event(frame: Frame) -> AlarmEvent:
    raw = frame.raw
    if len(raw) < 17:
        raise ProtocolError("alarm event frame is too short")
    return AlarmEvent(
        event_type=raw[13] & 0x7F,
        door=raw[14] & 0x0F,
        return_index=raw[16],
        datetime=safe_datetime(raw[12] + 2000, raw[11], raw[10], raw[9], raw[8], raw[7]),
    )


def parse_card_status_event(frame: Frame) -> CardStatusEvent:
    raw = frame.raw
    if len(raw) < 12:
        raise ProtocolError("card status frame is too short")
    return CardStatusEvent(
        card_index=int.from_bytes(raw[7:9], "little", signed=False),
        anti_passback_value=raw[9],
        return_index=raw[10],
    )


def parse_response(raw: bytes, expected_command: int | None = None) -> CommandResult:
    frame = parse_frame(raw)
    if expected_command is not None and frame.command != expected_command:
        return CommandResult(False, frame.command, frame.raw, f"unexpected command 0x{frame.command:02X}", frame.ack)
    if frame.data and frame.data[0] == ACK_OK:
        return CommandResult(True, frame.command, frame.raw, "ACK", frame.data[0])
    if frame.data and frame.data[0] == ACK_FAIL:
        return CommandResult(False, frame.command, frame.raw, "FAIL", frame.data[0])
    return CommandResult(True, frame.command, frame.raw, "response", frame.ack)


def parse_event(frame: Frame, serial_no: str | None = None) -> object | None:
    if frame.command == CMD_HEARTBEAT:
        return parse_heartbeat(frame)
    if frame.command == CMD_CARD_EVENT:
        return parse_card_event(frame, serial_no)
    if frame.command == CMD_ALARM_EVENT:
        return parse_alarm_event(frame)
    if frame.command == CMD_CARD_STATUS_EVENT:
        return parse_card_status_event(frame)
    return None
