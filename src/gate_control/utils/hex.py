from __future__ import annotations


def to_hex(data: bytes | bytearray | None, sep: str = "") -> str:
    if not data:
        return ""
    raw = bytes(data).hex().upper()
    if not sep:
        return raw
    return sep.join(raw[i : i + 2] for i in range(0, len(raw), 2))


def from_hex(value: str) -> bytes:
    cleaned = "".join(ch for ch in value if ch not in " \r\n\t:-")
    if len(cleaned) % 2:
        cleaned += "0"
    return bytes.fromhex(cleaned)
