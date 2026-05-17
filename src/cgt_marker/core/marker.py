from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from cgt_marker.core.evidence import EvidenceRef
from cgt_marker.core.serialization import datetime_from_json, datetime_to_json
from cgt_marker.core.types import JSONDict


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MarkerKind(StrEnum):
    """Kinds of marker records the ledger can carry."""

    CONTRADICTION = "contradiction"
    TENSION = "tension"
    UNCERTAIN = "uncertain"
    STALE = "stale"
    SOURCE_CONFLICT = "source_conflict"
    POLICY_CONFLICT = "policy_conflict"
    CUSTOM = "custom"


class MarkerStatus(StrEnum):
    """Lifecycle status for a marker."""

    OPEN = "open"
    QUARANTINED = "quarantined"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class MarkerDraft:
    """Detector output before policy finalization."""

    kind: MarkerKind = MarkerKind.CONTRADICTION
    subject: str | None = None
    predicate: str | None = None
    claim_ids: tuple[str, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()
    dimensions: tuple[str, ...] = ()
    severity: float | None = None
    confidence: float | None = None
    message: str = ""
    metadata: JSONDict = field(default_factory=dict)


@dataclass(frozen=True)
class Marker:
    """First-class record of an unresolved or reviewed conflict/tension."""

    id: str = ""
    kind: MarkerKind = MarkerKind.CONTRADICTION
    status: MarkerStatus = MarkerStatus.OPEN
    subject: str | None = None
    predicate: str | None = None
    claim_ids: tuple[str, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()
    dimensions: tuple[str, ...] = ()
    severity: float | None = None
    confidence: float | None = None
    message: str = ""
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime | None = None
    metadata: JSONDict = field(default_factory=dict)

    def to_dict(self) -> JSONDict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "status": self.status.value,
            "subject": self.subject,
            "predicate": self.predicate,
            "claim_ids": list(self.claim_ids),
            "evidence": [item.to_dict() for item in self.evidence],
            "dimensions": list(self.dimensions),
            "severity": self.severity,
            "confidence": self.confidence,
            "message": self.message,
            "created_at": datetime_to_json(self.created_at),
            "updated_at": datetime_to_json(self.updated_at) if self.updated_at else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Marker:
        return cls(
            id=str(data.get("id", "")),
            kind=MarkerKind(data.get("kind", MarkerKind.CONTRADICTION.value)),
            status=MarkerStatus(data.get("status", MarkerStatus.OPEN.value)),
            subject=data.get("subject"),
            predicate=data.get("predicate"),
            claim_ids=tuple(str(item) for item in data.get("claim_ids", ())),
            evidence=tuple(EvidenceRef.from_dict(item) for item in data.get("evidence", ())),
            dimensions=tuple(str(item) for item in data.get("dimensions", ())),
            severity=data.get("severity"),
            confidence=data.get("confidence"),
            message=str(data.get("message", "")),
            created_at=datetime_from_json(str(data["created_at"])),
            updated_at=(
                datetime_from_json(str(data["updated_at"])) if data.get("updated_at") else None
            ),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, data: str) -> Marker:
        return cls.from_dict(json.loads(data))
