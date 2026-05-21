from __future__ import annotations

import os
from pathlib import Path


def user_config_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "GateControl"
    return Path.cwd() / ".gate-control"
