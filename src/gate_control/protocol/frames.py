from __future__ import annotations

from dataclasses import dataclass

from gate_control.domain.constants import (
    DEFAULT_ADDRESS,
    DEFAULT_DOOR,
    ETX,
    LOC_COMMAND,
    LOC_DATA,
    LOC_LEN,
    STX,
)
from gate_control.domain.errors import ProtocolError

from .checksum import xor_checksum


@dataclass(frozen=True, slots=True)
class Frame:
    command: int
    data: bytes
    raw: bytes
    address: int
    door: int
    ack: int | None = None


def build_frame(command: int, data: bytes = b"", *, door: int = DEFAULT_DOOR, address: int = DEFAULT_ADDRESS) -> bytes:
    if not 0 <= command <= 0xFF:
        raise ValueError("command must be a byte")
    if not 0 <= door <= 0xFF:
        raise ValueError("door must be a byte")
    if not 0 <= address <= 0xFF:
        raise ValueError("address must be a byte")

    length = len(data)
    header = bytearray([STX, 0x00, command, address, door, length & 0xFF, (length >> 8) & 0xFF])
    body = header + bytearray(data)
    body.append(xor_checksum(body))
    body.append(ETX)
    return bytes(body)


def frame_length(raw: bytes, *, compatible: bool = True) -> int:
    if len(raw) < LOC_DATA + 2:
        raise ProtocolError("frame is too short")
    if raw[0] != STX:
        raise ProtocolError("frame does not start with STX")

    little_len = raw[LOC_LEN] + (raw[LOC_LEN + 1] << 8)
    little_total = LOC_DATA + little_len + 2
    if little_total <= len(raw) and raw[little_total - 1] == ETX:
        return little_total

    if compatible:
        big_len = (raw[LOC_LEN] << 8) + raw[LOC_LEN + 1]
        big_total = LOC_DATA + big_len + 2
        if big_total <= len(raw) and raw[big_total - 1] == ETX:
            return big_total

    raise ProtocolError("frame length or ETX is invalid")


def parse_frame(raw: bytes, *, compatible: bool = True, validate_checksum: bool = True) -> Frame:
    total = frame_length(raw, compatible=compatible)
    packet = raw[:total]

    if validate_checksum:
        expected = xor_checksum(packet[:-2])
        actual = packet[-2]
        if expected != actual:
            raise ProtocolError(f"checksum mismatch: expected 0x{expected:02X}, got 0x{actual:02X}")

    command = packet[LOC_COMMAND]
    data = packet[LOC_DATA:-2]
    ack = data[0] if data else None
    return Frame(command=command, data=data, raw=packet, address=packet[3], door=packet[4], ack=ack)


def extract_frames(buffer: bytearray) -> list[Frame]:
    frames: list[Frame] = []
    while buffer:
        try:
            start = buffer.index(STX)
        except ValueError:
            buffer.clear()
            break

        if start:
            del buffer[:start]

        try:
            total = frame_length(bytes(buffer))
        except ProtocolError:
            break

        raw = bytes(buffer[:total])
        del buffer[:total]
        frames.append(parse_frame(raw))
    return frames
