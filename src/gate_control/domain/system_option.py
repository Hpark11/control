from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemOption:
    raw: int

    @property
    def has_expiry(self) -> bool:
        return (self.raw & 0x01) == 0x01

    @property
    def has_name(self) -> bool:
        return (self.raw & 0x08) == 0x08

    @property
    def uses_pin4(self) -> bool:
        return (self.raw & 0x30) > 0

    @property
    def flags(self) -> dict[str, bool]:
        return {
            "has_expiry": self.has_expiry,
            "has_name": self.has_name,
            "uses_pin4": self.uses_pin4,
        }

    def describe(self) -> str:
        enabled = [name for name, value in self.flags.items() if value]
        return ", ".join(enabled) if enabled else "default"
