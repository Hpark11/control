from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from gate_control.domain.models import ControllerConfig
from gate_control.utils.windows import user_config_dir


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or user_config_dir() / "config.json"

    def load_default(self) -> ControllerConfig | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        default = data.get("default_controller")
        if not default:
            return None
        return ControllerConfig(**default)

    def save_default(self, config: ControllerConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"default_controller": asdict(config)}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()
