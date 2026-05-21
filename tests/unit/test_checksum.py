from gate_control.protocol.checksum import xor_checksum


def test_xor_checksum() -> None:
    assert xor_checksum(bytes.fromhex("020067FF0002005000")) == 0xC8
