from gate_control.protocol import commands
from gate_control.protocol.frames import parse_frame
from gate_control.protocol.parser import parse_response


def test_parse_ack_response() -> None:
    raw = commands.history_event_ack(0x2C, 0x06)
    result = parse_response(raw, expected_command=0x2C)
    assert result.ok
    assert result.ack == 0x06


def test_parse_frame_rejects_bad_checksum() -> None:
    raw = bytearray(commands.open_door(0))
    raw[-2] ^= 0xFF
    try:
        parse_frame(bytes(raw))
    except Exception as exc:
        assert "checksum" in str(exc)
    else:
        raise AssertionError("expected checksum error")
