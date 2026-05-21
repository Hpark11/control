from __future__ import annotations

from datetime import datetime


def safe_datetime(year: int, month: int, day: int, hour: int, minute: int, second: int) -> datetime | None:
    try:
        return datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
