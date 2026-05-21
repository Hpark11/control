from gate_control.protocol import commands
from gate_control.protocol.frames import build_frame, parse_frame
from gate_control.protocol.parser import parse_heartbeat, parse_response


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


def test_parse_heartbeat_offsets() -> None:
    data = bytearray(34)
    data[0] = 0
    data[1:7] = bytes([26, 5, 21, 15, 30, 10])
    data[7] = 0xAA
    data[8] = 30
    data[9] = 1
    data[10] = 0x31
    data[11] = 2
    data[12] = 3
    data[13:17] = b"\x00\x00\x00\x00"
    data[17] = 4
    data[18] = 12
    data[19:21] = (23456).to_bytes(2, "little")
    data[21:27] = b"1A6097"
    data[27:29] = b"\x34\x12"
    data[29:33] = (7).to_bytes(4, "little")
    data[33] = 1

    frame = parse_frame(build_frame(0x56, bytes(data)))
    heartbeat = parse_heartbeat(frame)

    assert heartbeat.card_num_in_pack == 30
    assert heartbeat.system_option == 0x31
    assert heartbeat.serial_no == "1A6097"
    assert heartbeat.index_cmd == 7
    assert heartbeat.cmd_ok == 1
