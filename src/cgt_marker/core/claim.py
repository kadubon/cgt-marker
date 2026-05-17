from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from cgt_marker.core.serialization import datetime_from_json, datetime_to_json
from cgt_marker.core.types import JSONDict, JSONValue


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class Claim:
    """Structured assertion supplied by the caller.

    The library does not extract claims from natural language. A claim is the
    minimal typed record that detectors compare and markers cite.
    """

    subject: str
    predicate: str
    value: JSONValue
    source: str
    id: str = ""
    timestamp: datetime = field(default_factory=_utc_now)
    confidence: float | None = None
    scope: JSONDict = field(default_factory=dict)
    metadata: JSONDict = field(default_factory=dict)

    def to_dict(self) -> JSONDict:
        return {
            "id": self.id,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "source": self.source,
            "timestamp": datetime_to_json(self.timestamp),
            "confidence": self.confidence,
            "scope": dict(self.scope),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Claim:
        return cls(
            id=str(data.get("id", "")),
            subject=str(data["subject"]),
            predicate=str(data["predicate"]),
            value=data["value"],
            source=str(data["source"]),
            timestamp=datetime_from_json(str(data["timestamp"])),
            confidence=data.get("confidence"),
            scope=dict(data.get("scope", {})),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, data: str) -> Claim:
        return cls.from_dict(json.loads(data))
