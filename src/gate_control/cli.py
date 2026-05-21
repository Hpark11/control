from __future__ import annotations

import argparse
import sys
from datetime import datetime

from gate_control.app import create_api
from gate_control.client.session import GateClientSession
from gate_control.config import resolve_controller
from gate_control.domain.errors import GateControlError, UnsafeCommandError
from gate_control.domain.models import ControllerConfig, HeartbeatStatus
from gate_control.prompts import confirm, prompt_controller
from gate_control.protocol.frames import parse_frame
from gate_control.service.settings_store import SettingsStore
from gate_control.utils.hex import from_hex, to_hex
from gate_control.utils.time import now_iso


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gate-control")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--oem", type=int, dest="oem_code")
    sub = parser.add_subparsers(dest="command")

    setup = sub.add_parser("setup", help="configure default controller")
    setup.add_argument("--verify", choices=["heartbeat", "connect-only"], default="heartbeat")
    setup.set_defaults(func=cmd_setup)

    sub.add_parser("menu", help="interactive menu").set_defaults(func=cmd_menu)
    sub.add_parser("status", help="connect and read heartbeat/status").set_defaults(func=cmd_status)
    sub.add_parser("monitor", help="print incoming frames").set_defaults(func=cmd_monitor)

    open_door = sub.add_parser("open-door")
    open_door.add_argument("--door", type=int, default=0)
    open_door.set_defaults(func=cmd_open_door)

    close_door = sub.add_parser("close-door")
    close_door.add_argument("--door", type=int, default=0)
    close_door.set_defaults(func=cmd_close_door)

    sub.add_parser("set-time").set_defaults(func=cmd_set_time)

    add_card = sub.add_parser("add-card-1door")
    add_card.add_argument("--index", type=int, required=True)
    add_card.add_argument("--card-no", type=int, required=True)
    add_card.add_argument("--pin", required=True)
    add_card.add_argument("--tz", type=int, default=1)
    add_card.add_argument("--expires", required=True, help="YYYY-MM-DD")
    add_card.add_argument("--name", default="")
    add_card.add_argument("--system-option", type=lambda v: int(v, 0))
    add_card.set_defaults(func=cmd_add_card_1door)

    clear_slot = sub.add_parser("clear-card-slot")
    clear_slot.add_argument("--index", type=int, required=True)
    clear_slot.add_argument("--pin", default="00000000")
    clear_slot.add_argument("--tz", type=int, default=0)
    clear_slot.add_argument("--confirm", action="store_true")
    clear_slot.set_defaults(func=cmd_clear_card_slot)

    clear_all = sub.add_parser("clear-all-cards")
    clear_all.add_argument("--confirm", action="store_true")
    clear_all.set_defaults(func=cmd_clear_all_cards)

    search = sub.add_parser("search-card")
    search.add_argument("--index", type=int, required=True)
    search.set_defaults(func=cmd_search_card)

    send_hex = sub.add_parser("send-hex")
    send_hex.add_argument("hex")
    send_hex.add_argument("--no-wait", action="store_true")
    send_hex.set_defaults(func=cmd_send_hex)

    config = sub.add_parser("config")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    config_sub.add_parser("show").set_defaults(func=cmd_config_show)
    config_sub.add_parser("reset").set_defaults(func=cmd_config_reset)

    parser.set_defaults(func=cmd_menu)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nCanceled.")
    except GateControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def resolve_or_prompt(args: argparse.Namespace) -> ControllerConfig:
    config = resolve_controller(args.host, args.port, args.oem_code)
    if config:
        return config
    print("No controller is configured.")
    return prompt_controller()


def print_status(heartbeat: HeartbeatStatus) -> None:
    print("Connection: connected")
    print(f"Serial No: {heartbeat.serial_no}")
    print(f"OEM Code: {heartbeat.oem_code}")
    print(f"Version: {heartbeat.version}")
    print(f"System Option: 0x{heartbeat.system_option:02X}")
    print(f"Card Num In Pack: {heartbeat.card_num_in_pack}")
    print(f"Door Status: 0x{heartbeat.door_status:02X}")
    print(f"Input Status: 0x{heartbeat.input_status:04X}")
    print(f"Device Time: {heartbeat.datetime}")


def print_result(result) -> None:  # noqa: ANN001
    print("OK" if result.ok else "FAIL")
    print(f"Command: 0x{result.command:02X}")
    if result.message:
        print(f"Message: {result.message}")
    if result.response:
        print(f"RX: {to_hex(result.response, ' ')}")


def cmd_setup(args: argparse.Namespace) -> None:
    config = (
        ControllerConfig(host=args.host, port=args.port, oem_code=args.oem_code)
        if args.host and args.port and args.oem_code
        else prompt_controller()
    )
    print(f"Trying {config.host}:{config.port} ...")
    session = GateClientSession(config)
    session.connect()
    try:
        if args.verify == "heartbeat":
            print("Connected. Waiting for heartbeat/status ...")
            heartbeat = session.wait_for_heartbeat(timeout=10)
            if heartbeat is None:
                raise GateControlError("connected, but heartbeat/status was not received")
            config.serial_no = heartbeat.serial_no
            print_status(heartbeat)
        else:
            print("Connected.")

        config.last_verified_at = now_iso()
        if confirm("Save this controller as default?", default=True):
            SettingsStore().save_default(config)
            print("Saved default controller.")
    finally:
        session.close()


def cmd_status(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        heartbeat = api.status(timeout=10)
        if heartbeat is None:
            raise GateControlError("heartbeat/status was not received")
        print_status(heartbeat)
    finally:
        api.session.close()


def cmd_monitor(args: argparse.Namespace) -> None:
    config = resolve_or_prompt(args)
    session = GateClientSession(config)
    session.connect()
    try:
        print(f"Monitoring {config.host}:{config.port}. Press Ctrl+C to stop.")
        session.monitor()
    finally:
        session.close()


def cmd_open_door(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        print_result(api.open_door(args.door))
    finally:
        api.session.close()


def cmd_close_door(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        print_result(api.close_door(args.door))
    finally:
        api.session.close()


def cmd_set_time(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        print_result(api.set_time())
    finally:
        api.session.close()


def cmd_add_card_1door(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        api.status(timeout=10)
        expires = datetime.strptime(args.expires, "%Y-%m-%d")
        result = api.add_card_1door(args.index, args.card_no, args.pin, args.tz, expires, args.name, args.system_option)
        print_result(result)
    finally:
        api.session.close()


def cmd_clear_card_slot(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        api.status(timeout=10)
        print_result(api.clear_card_slot(args.index, args.pin, args.tz, args.confirm))
    except UnsafeCommandError:
        print("This command requires --confirm.")
    finally:
        api.session.close()


def cmd_clear_all_cards(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        print_result(api.clear_all_cards(args.confirm))
    except UnsafeCommandError:
        print("This command requires --confirm.")
    finally:
        api.session.close()


def cmd_search_card(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        print_result(api.search_card(args.index))
    finally:
        api.session.close()


def cmd_send_hex(args: argparse.Namespace) -> None:
    api = create_api(resolve_or_prompt(args))
    try:
        payload = from_hex(args.hex)
        frame = parse_frame(payload, validate_checksum=False)
        print(f"TX command: 0x{frame.command:02X}")
        print_result(api.send_hex(payload, expect_response=not args.no_wait))
    finally:
        api.session.close()


def cmd_config_show(args: argparse.Namespace) -> None:
    config = SettingsStore().load_default()
    if config is None:
        print("No default controller configured.")
        return
    print(f"Host: {config.host}")
    print(f"Port: {config.port}")
    print(f"OEM Code: {config.oem_code}")
    print(f"Serial No: {config.serial_no or '-'}")
    print(f"Last Verified At: {config.last_verified_at or '-'}")


def cmd_config_reset(args: argparse.Namespace) -> None:
    if confirm("Reset saved controller config?", default=False):
        SettingsStore().reset()
        print("Config reset.")


def cmd_menu(args: argparse.Namespace) -> None:
    while True:
        print()
        print("Gate Control Menu")
        print("1. 상태 확인")
        print("2. 모니터링 시작")
        print("3. 문 열기")
        print("4. 문 닫기")
        print("5. 카드 추가")
        print("6. 카드 슬롯 비우기")
        print("7. 전체 카드 삭제")
        print("8. 시간 동기화")
        print("9. Raw HEX 전송")
        print("10. 설정")
        print("0. 종료")
        choice = input("Select: ").strip()

        if choice == "0":
            return
        if choice == "1":
            cmd_status(args)
        elif choice == "2":
            cmd_monitor(args)
        elif choice == "3":
            args.door = int(input("Door [0]: ").strip() or "0")
            cmd_open_door(args)
        elif choice == "4":
            args.door = int(input("Door [0]: ").strip() or "0")
            cmd_close_door(args)
        elif choice == "5":
            args.index = int(input("Card index: ").strip())
            args.card_no = int(input("Card No: ").strip())
            args.pin = input("PIN: ").strip()
            args.tz = int(input("Timezone [1]: ").strip() or "1")
            args.expires = input("Expires YYYY-MM-DD: ").strip()
            args.name = input("Name []: ").strip()
            args.system_option = None
            cmd_add_card_1door(args)
        elif choice == "6":
            args.index = int(input("Card index: ").strip())
            args.pin = input("PIN [00000000]: ").strip() or "00000000"
            args.tz = int(input("Timezone [0]: ").strip() or "0")
            args.confirm = confirm("Clear this card slot?", default=False)
            cmd_clear_card_slot(args)
        elif choice == "7":
            args.confirm = confirm("Delete all cards?", default=False)
            cmd_clear_all_cards(args)
        elif choice == "8":
            cmd_set_time(args)
        elif choice == "9":
            args.hex = input("HEX: ").strip()
            args.no_wait = False
            cmd_send_hex(args)
        elif choice == "10":
            config = SettingsStore().load_default()
            if config:
                cmd_config_show(args)
            if confirm("Run setup?", default=False):
                args.verify = "heartbeat"
                cmd_setup(args)
        else:
            print("Unknown menu item.")
