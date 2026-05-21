from gate_control.protocol.frames import build_frame, parse_frame


def test_build_and_parse_empty_frame() -> None:
    raw = build_frame(0x2C, door=1)
    frame = parse_frame(raw)
    assert frame.command == 0x2C
    assert frame.data == b""
    assert frame.raw == raw
