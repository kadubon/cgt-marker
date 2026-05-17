"""Deterministic status-opposition conflicts over already normalized-ish values."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from cgt_marker.core.claim import Claim
from cgt_marker.core.detector import evidence_from_claim
from cgt_marker.core.marker import MarkerDraft, MarkerKind

DEFAULT_OPPOSITES = frozenset(
    {
        frozenset(("done", "not_done")),
        frozenset(("approved", "rejected")),
        frozenset(("active", "cancelled")),
        frozenset(("enabled", "disabled")),
        frozenset(("true", "false")),
    }
)


@dataclass(frozen=True)
class StatusConflictDetector:
    """Detect configured opposite status pairs for the same subject and predicate."""

    opposite_pairs: frozenset[frozenset[str]] = field(default_factory=lambda: DEFAULT_OPPOSITES)
    name: str = "status"

    def detect(self, new_claim: Claim, existing_claims: Sequence[Claim]) -> list[MarkerDraft]:
        drafts: list[MarkerDraft] = []
        new_value = self._normalize(new_claim.value)
        for existing in existing_claims:
            if existing.subject != new_claim.subject or existing.predicate != new_claim.predicate:
                continue
            existing_value = self._normalize(existing.value)
            if frozenset((existing_value, new_value)) not in self.opposite_pairs:
                continue
            drafts.append(
                MarkerDraft(
                    kind=MarkerKind.CONTRADICTION,
                    subject=new_claim.subject,
                    predicate=new_claim.predicate,
                    claim_ids=(existing.id, new_claim.id),
                    evidence=(evidence_from_claim(existing), evidence_from_claim(new_claim)),
                    dimensions=("status",),
                    severity=0.9,
                    message=(
                        f"{new_claim.subject} {new_claim.predicate} "
                        f"{existing.value!r} vs {new_claim.value!r}"
                    ),
                    metadata={"detector": self.name},
                )
            )
        return drafts

    @staticmethod
    def _normalize(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value).strip().lower().replace(" ", "_").replace("-", "_")
