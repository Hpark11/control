from __future__ import annotations

from datetime import datetime

from gate_control.domain.constants import *
from gate_control.domain.system_option import SystemOption

from .codec import bool_byte, put_card_no, put_date, put_hour_minute, put_name, put_pin2, put_pin4, u16le, u32le
from .frames import build_frame


def door_addr(index: int) -> int:
    return int(index) + 1


def ack_heart(index_cmd: int, oem_code: int, embedded_command: bytes | None = None) -> bytes:
    data = bytearray()
    data.extend(bytes([(oem_code >> 8) & 0xFF, oem_code & 0xFF]))
    data.extend(b"\x00\x00")
    data.extend(u32le(index_cmd))
    if embedded_command:
        data.extend(embedded_command)
    return build_frame(CMD_HEARTBEAT, bytes(data))


def history_event_ack(command: int, return_index: int) -> bytes:
    return build_frame(command, bytes([return_index & 0xFF]))


def clear_all_cards() -> bytes:
    return build_frame(CMD_CLEAR_ALL_CARDS, door=0)


def delete_card(index: int) -> bytes:
    return build_frame(CMD_DELETE_CARD, u16le(index), door=0)


def set_card_status(index: int, status: int) -> bytes:
    return build_frame(CMD_SET_CARD_STATUS, u16le(index) + bytes([status & 0xFF]), door=0)


def add_card(
    system_option: int,
    index: int,
    name: str,
    card_no: int,
    pin: str,
    tz1: int,
    tz2: int = 0,
    tz3: int = 0,
    tz4: int = 0,
    status: int = 1,
    expires: datetime | None = None,
) -> bytes:
    option = SystemOption(system_option)
    payload = bytearray()
    payload.extend(u16le(index))
    payload.extend(put_card_no(card_no))
    payload.extend(put_pin4(pin) if option.uses_pin4 else put_pin2(pin))
    payload.extend(bytes([tz1 & 0xFF, tz2 & 0xFF, tz3 & 0xFF, tz4 & 0xFF]))

    if option.has_expiry:
        end = expires or datetime.now().replace(year=datetime.now().year + 1)
        payload.extend(put_date(end))
        payload.extend(bytes([end.hour, end.minute]))
    else:
        payload.extend(bytes([0, 0, 0, 0, status & 0xFF]))

    if option.has_name:
        payload.extend(put_name(name, 8))

    return build_frame(CMD_ADD_CARD, bytes(payload), door=0)


def add_card_1door(system_option: int, index: int, name: str, card_no: int, pin: str, tz: int, expires: datetime) -> bytes:
    return add_card(
        system_option=system_option,
        index=index,
        name=name,
        card_no=card_no,
        pin=pin,
        tz1=tz & 0xFF,
        tz2=(tz >> 8) & 0xFF,
        expires=expires,
    )


def add_card_2door(
    system_option: int,
    index: int,
    name: str,
    card_no: int,
    pin: str,
    tz1: int,
    tz2: int,
    expires: datetime,
) -> bytes:
    return add_card(
        system_option,
        index,
        name,
        card_no,
        pin,
        tz1 & 0xFF,
        (tz1 >> 8) & 0xFF,
        tz2 & 0xFF,
        (tz2 >> 8) & 0xFF,
        expires=expires,
    )


def add_card_4door(
    system_option: int,
    index: int,
    name: str,
    card_no: int,
    pin: str,
    tz1: int,
    tz2: int,
    tz3: int,
    tz4: int,
    expires: datetime,
) -> bytes:
    return add_card(system_option, index, name, card_no, pin, tz1, tz2, tz3, tz4, expires=expires)


def clear_card_slot(system_option: int, index: int, pin: str = "00000000", tz: int = 0) -> bytes:
    return add_card_1door(
        system_option=system_option,
        index=index,
        name="",
        card_no=0,
        pin=pin,
        tz=tz,
        expires=datetime.now(),
    )


def restart() -> bytes:
    return build_frame(CMD_RESTART)


def reset() -> bytes:
    return build_frame(CMD_RESET)


def set_time(value: datetime | None = None) -> bytes:
    dt = value or datetime.now()
    csharp_day_of_week = (dt.weekday() + 1) % 7
    data = bytes([dt.second, dt.minute, dt.hour, csharp_day_of_week + 1, dt.day, dt.month, (dt.year - 2000) & 0xFF])
    return build_frame(CMD_SET_TIME, data)


def open_door(index: int = 0) -> bytes:
    return build_frame(CMD_OPEN_DOOR, door=door_addr(index))


def close_door(index: int = 0) -> bytes:
    return build_frame(CMD_CLOSE_DOOR, door=door_addr(index))


def open_door_long(index: int = 0) -> bytes:
    return build_frame(CMD_OPEN_DOOR_LONG, door=door_addr(index))


def lock_door(index: int, lock: bool) -> bytes:
    value = bool_byte(lock)
    return build_frame(CMD_LOCK_DOOR, bytes([value, value]), door=door_addr(index))


def set_pass(index: int, reader: int, passed: bool) -> bytes:
    return build_frame(CMD_SET_PASS, bytes([0, reader & 0xFF, 0, bool_byte(not passed)]), door=door_addr(index))


def set_alarm(close_alarm: bool, long_alarm: bool) -> bytes:
    return build_frame(CMD_SET_ALARM, bytes([bool_byte(close_alarm), bool_byte(long_alarm)]))


def set_fire(close_fire: bool, long_fire: bool) -> bytes:
    return build_frame(CMD_SET_FIRE, bytes([bool_byte(close_fire), bool_byte(long_fire)]))


def delete_timezone(door: int) -> bytes:
    return build_frame(CMD_DELETE_TIMEZONE, door=door_addr(door))


def add_timezone(
    door: int,
    index: int,
    from_time: datetime,
    to_time: datetime,
    week: int,
    passback: bool,
    identify: int,
    end_datetime: datetime,
    group: int,
) -> bytes:
    identify_value = identify | (0x80 if passback else 0)
    data = bytes([index & 0xFF]) + put_hour_minute(from_time) + put_hour_minute(to_time)
    data += bytes([week & 0xFF, identify_value & 0xFF]) + put_date(end_datetime) + bytes([group & 0xFF])
    return build_frame(CMD_ADD_TIMEZONE, data, door=door_addr(door))


def send_to_485(value: bytes) -> bytes:
    return build_frame(CMD_SEND_TO_485, value)


def set_control(system_option: int, fire_time: int, alarm_time: int, duress_pin: str, lock_each: int) -> bytes:
    option = SystemOption(system_option)
    payload = bytearray([lock_each & 0xFF])
    payload.extend(u16le(fire_time))
    payload.extend(u16le(alarm_time))
    payload.extend(put_pin4(duress_pin or "0") if option.uses_pin4 else put_pin2(duress_pin or "0"))
    return build_frame(CMD_SET_CONTROL, bytes(payload))


def set_door(
    door: int,
    open_time: int,
    out_time: int,
    double_path: bool,
    too_long_alarm: bool,
    alarm_mask: int,
    alarm_time: int,
    m_cards: int,
    m_cards_in_out: int,
) -> bytes:
    payload = bytes(
        [
            open_time & 0xFF,
            out_time & 0xFF,
            bool_byte(double_path),
            bool_byte(too_long_alarm),
            (open_time >> 8) & 0xFF,
            alarm_mask & 0xFF,
        ]
    )
    payload += u16le(alarm_time)
    payload += bytes([m_cards & 0xFF, m_cards_in_out & 0xFF])
    return build_frame(CMD_SET_DOOR, payload, door=door_addr(door))


def delete_holiday() -> bytes:
    return build_frame(CMD_DELETE_HOLIDAY)


def add_holiday(index: int, from_date: datetime, to_date: datetime) -> bytes:
    return build_frame(CMD_ADD_HOLIDAY, bytes([index & 0xFF]) + put_date(from_date) + put_date(to_date))


def search_card(index: int) -> bytes:
    return build_frame(CMD_SEARCH_CARD, u16le(index), door=0)
