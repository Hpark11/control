from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass


@dataclass(slots=True)
class PullCommand:
    index: int
    data: bytes


class PullQueue:
    def __init__(self) -> None:
        self._items: deque[PullCommand] = deque()
        self._current_index: int = 0

    def __len__(self) -> int:
        return len(self._items)

    def add(self, data: bytes, *, priority: bool = False) -> None:
        item = PullCommand(index=0, data=data)
        if priority:
            self._items.appendleft(item)
        else:
            self._items.append(item)

    def clear(self) -> None:
        self._items.clear()

    def next_for_heartbeat(self, last_index: int, last_ok: int) -> tuple[int, bytes | None]:
        if last_ok > 0 and last_index > 0 and self._items and self._current_index == last_index:
            self._items.popleft()

        if not self._items:
            return 0, None

        self._current_index = random.randint(1, 65535)
        self._items[0].index = self._current_index
        return self._current_index, self._items[0].data
