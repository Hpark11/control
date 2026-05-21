from __future__ import annotations


def xor_checksum(data: bytes | bytearray) -> int:
    value = 0
    for item in data:
        value ^= item
    return value & 0xFF
