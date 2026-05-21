from datetime import datetime

from gate_control.protocol import commands
from gate_control.utils.hex import to_hex


def test_search_card_command_shape() -> None:
    raw = commands.search_card(50000)
    assert raw[2] == 0x67
    assert raw[5:7] == b"\x02\x00"
    assert raw[7:9] == (50000).to_bytes(2, "little")


def test_open_door_command() -> None:
    assert to_hex(commands.open_door(0)).startswith("02002CFF010000")


def test_add_card_uses_system_option() -> None:
    raw = commands.add_card_1door(0x31, 1, "", 999998, "999998", 1, datetime(2027, 1, 1))
    assert raw[2] == 0x62
    assert raw[7:9] == b"\x01\x00"
