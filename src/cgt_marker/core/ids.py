from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol
from uuid import uuid4


class IdGenerator(Protocol):
    def new_id(self, prefix: str) -> str:
        """Return a new identifier with the requested prefix."""


@dataclass
class UUIDGenerator:
    def new_id(self, prefix: str) -> str:
        return f"{prefix}-{uuid4().hex}"


@dataclass
class CounterIdGenerator:
    start: int = 1
    width: int = 3
    _counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def new_id(self, prefix: str) -> str:
        if self._counters[prefix] == 0:
            self._counters[prefix] = self.start
        else:
            self._counters[prefix] += 1
        return f"{prefix}-{self._counters[prefix]:0{self.width}d}"
