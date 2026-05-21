from __future__ import annotations

from gate_control.domain.models import SessionState


class StateStore:
    def __init__(self) -> None:
        self.state = SessionState()
