from __future__ import annotations

import os

from gate_control.domain.constants import DEFAULT_OEM_CODE, DEFAULT_PORT
from gate_control.domain.models import ControllerConfig
from gate_control.service.settings_store import SettingsStore


def resolve_controller(host: str | None = None, port: int | None = None, oem_code: int | None = None) -> ControllerConfig | None:
    store = SettingsStore()
    saved = store.load_default()

    env_host = os.environ.get("GATE_CONTROL_HOST")
    env_port = os.environ.get("GATE_CONTROL_PORT")
    env_oem = os.environ.get("GATE_CONTROL_OEM")

    resolved_host = host or env_host or (saved.host if saved else None)
    if not resolved_host:
        return None

    resolved_port = port or (int(env_port) if env_port else None) or (saved.port if saved else DEFAULT_PORT)
    resolved_oem = oem_code or (int(env_oem) if env_oem else None) or (saved.oem_code if saved else DEFAULT_OEM_CODE)
    return ControllerConfig(
        host=resolved_host,
        port=resolved_port,
        oem_code=resolved_oem,
        name=saved.name if saved else "default",
        serial_no=saved.serial_no if saved else None,
        last_verified_at=saved.last_verified_at if saved else None,
    )
