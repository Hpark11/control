from __future__ import annotations

from datetime import datetime

from gate_control.client.session import GateClientSession
from gate_control.domain.errors import UnsafeCommandError
from gate_control.domain.models import CommandResult
from gate_control.protocol import commands


class ControllerApi:
    def __init__(self, session: GateClientSession) -> None:
        self.session = session

    def status(self, timeout: float = 10.0):
        return self.session.wait_for_heartbeat(timeout=timeout)

    def open_door(self, door: int = 0) -> CommandResult:
        return self.session.send_command(commands.open_door(door), timeout=1.0)

    def close_door(self, door: int = 0) -> CommandResult:
        return self.session.send_command(commands.close_door(door), timeout=1.0)

    def open_door_long(self, door: int = 0) -> CommandResult:
        return self.session.send_command(commands.open_door_long(door), timeout=1.0)

    def lock_door(self, door: int, locked: bool) -> CommandResult:
        return self.session.send_command(commands.lock_door(door, locked), timeout=1.0)

    def set_time(self, value: datetime | None = None) -> CommandResult:
        return self.session.send_command(commands.set_time(value), timeout=2.0)

    def add_card_1door(
        self,
        index: int,
        card_no: int,
        pin: str,
        tz: int,
        expires: datetime,
        name: str = "",
        system_option: int | None = None,
        card_format: str = "captured",
        permission: bytes | None = None,
        rand: int = 0,
    ) -> CommandResult:
        heartbeat = self.session.require_heartbeat()
        option = heartbeat.system_option if system_option is None else system_option
        if card_format == "captured":
            option = 0x01
        if permission is not None:
            payload = commands.add_card_with_permission_bytes(option, index, name, card_no, pin, permission, expires, rand)
        else:
            payload = commands.add_card_1door(option, index, name, card_no, pin, tz, expires, rand)
        return self.session.send_command(payload, timeout=3.0)

    def clear_card_slot(self, index: int, pin: str = "00000000", tz: int = 0, confirm: bool = False) -> CommandResult:
        if not confirm:
            raise UnsafeCommandError("clear-card-slot requires confirmation")
        heartbeat = self.session.require_heartbeat()
        payload = commands.clear_card_slot(heartbeat.system_option, index, pin, tz)
        return self.session.send_command(payload, timeout=3.0)

    def clear_all_cards(self, confirm: bool = False) -> CommandResult:
        if not confirm:
            raise UnsafeCommandError("clear-all-cards requires confirmation")
        return self.session.send_command(commands.clear_all_cards(), timeout=5.0)

    def search_card(self, index: int) -> CommandResult:
        return self.session.send_command(commands.search_card(index), timeout=3.0)

    def send_hex(self, payload: bytes, expect_response: bool = True) -> CommandResult:
        return self.session.send_command(payload, timeout=3.0, expect_response=expect_response)
