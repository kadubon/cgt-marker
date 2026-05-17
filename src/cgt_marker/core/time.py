from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current time."""


@dataclass
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


@dataclass
class FrozenClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def tick(self, delta: timedelta = timedelta(seconds=1)) -> datetime:
        self.current = self.current + delta
        return self.current
