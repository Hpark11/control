from gate_control.domain.system_option import SystemOption


def test_system_option_flags() -> None:
    option = SystemOption(0x39)
    assert option.has_expiry
    assert option.has_name
    assert option.uses_pin4
