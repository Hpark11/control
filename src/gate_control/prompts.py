from __future__ import annotations

from gate_control.domain.constants import DEFAULT_OEM_CODE, DEFAULT_PORT
from gate_control.domain.models import ControllerConfig


def prompt_controller() -> ControllerConfig:
    host = ""
    while not host:
        host = input("Host/IP: ").strip()

    port_text = input(f"Port [{DEFAULT_PORT}]: ").strip()
    oem_text = input(f"OEM code [{DEFAULT_OEM_CODE}]: ").strip()
    return ControllerConfig(
        host=host,
        port=int(port_text or DEFAULT_PORT),
        oem_code=int(oem_text or DEFAULT_OEM_CODE),
    )


def confirm(message: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{message} {suffix}: ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}
