from __future__ import annotations

from datetime import datetime

from gate_control.domain.errors import ProtocolError


def u16le(value: int) -> bytes:
    return int(value).to_bytes(2, "little", signed=False)


def u16be(value: int) -> bytes:
    return int(value).to_bytes(2, "big", signed=False)


def u32le(value: int) -> bytes:
    return int(value).to_bytes(4, "little", signed=False)


def u32be(value: int) -> bytes:
    return int(value).to_bytes(4, "big", signed=False)


def put_card_no(card_no: int) -> bytes:
    return u32le(card_no)


def put_date(value: datetime) -> bytes:
    year = value.year - 2000 if value.year >= 2000 else value.year
    return bytes([year & 0xFF, value.month, value.day])


def put_hour_minute(value: datetime) -> bytes:
    return bytes([value.hour, value.minute])


def put_pin2(pin: str | int | None) -> bytes:
    try:
        value = int(pin or 0)
    except ValueError as exc:
        raise ProtocolError("PIN must be numeric in 2-byte PIN mode") from exc
    if not 0 <= value <= 0xFFFF:
        raise ProtocolError("PIN is too large for 2-byte PIN mode. Use 0-65535, or verify SystemOption/PIN mode.")
    return u16be(value)


def pin4_value(pin: str | int | None) -> int:
    text = "" if pin is None else str(pin)
    nibbles = [0xFF] * 8
    encoded = text.encode("ascii", errors="ignore")[:8]
    for i, item in enumerate(encoded):
        nibbles[i] = max(0, item - 0x30) & 0xFF

    packed = []
    for i in range(4):
        packed.append(((nibbles[i * 2] << 4) & 0xF0) + (nibbles[i * 2 + 1] & 0x0F))
    return packed[0] + (packed[1] << 8) + (packed[2] << 16) + (packed[3] << 24)


def put_pin4(pin: str | int | None) -> bytes:
    return u32le(pin4_value(pin))


def put_name(value: str | None, length: int = 8) -> bytes:
    text = value or ""
    try:
        raw = text.encode("gb2312")
    except UnicodeEncodeError:
        raw = text.encode("utf-8", errors="ignore")
    return raw[:length].ljust(length, b"\x00")


def bool_byte(value: bool) -> int:
    return 1 if value else 0
