from __future__ import annotations

from gate_control.domain.models import ControllerConfig


class ControllerRegistry:
    def __init__(self) -> None:
        self._controllers: dict[str, ControllerConfig] = {}

    def add(self, config: ControllerConfig) -> None:
        self._controllers[config.name] = config

    def get(self, name: str = "default") -> ControllerConfig | None:
        return self._controllers.get(name)
