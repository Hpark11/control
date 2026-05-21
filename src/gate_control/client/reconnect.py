from __future__ import annotations

import time
from collections.abc import Callable


def retry(operation: Callable[[], None], attempts: int = 3, delay: float = 1.0) -> None:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            operation()
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(delay)
    if last_error:
        raise last_error
