from __future__ import annotations

from gate_control.client.session import GateClientSession
from gate_control.controller.api import ControllerApi
from gate_control.domain.models import ControllerConfig


def create_api(config: ControllerConfig, timeout: float = 5.0) -> ControllerApi:
    session = GateClientSession(config, timeout=timeout)
    session.connect()
    return ControllerApi(session)
