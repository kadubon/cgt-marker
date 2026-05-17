from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from cgt_marker.core.types import JSONDict


@dataclass(frozen=True)
class EvidenceRef:
    """Lightweight provenance pointer copied from a claim into a marker."""

    source: str
    id: str = ""
    claim_id: str | None = None
    quote: str | None = None
    uri: str | None = None
    metadata: JSONDict = field(default_factory=dict)

    def to_dict(self) -> JSONDict:
        return {
            "id": self.id,
            "claim_id": self.claim_id,
            "source": self.source,
            "quote": self.quote,
            "uri": self.uri,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceRef:
        return cls(
            id=str(data.get("id", "")),
            claim_id=data.get("claim_id"),
            source=str(data["source"]),
            quote=data.get("quote"),
            uri=data.get("uri"),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, data: str) -> EvidenceRef:
        return cls.from_dict(json.loads(data))
