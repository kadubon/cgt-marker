"""Deterministic exact-slot conflicts over already structured claims.

This module performs no natural-language parsing and no truth adjudication.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from cgt_marker.core.claim import Claim
from cgt_marker.core.detector import evidence_from_claim
from cgt_marker.core.marker import MarkerDraft, MarkerKind


@dataclass(frozen=True)
class ExactSlotConflictDetector:
    """Detect different values for the same subject and compatible predicate slot."""

    predicates: frozenset[str] = field(
        default_factory=lambda: frozenset({"equals", "is", "status", "value"})
    )
    name: str = "exact_slot"

    def detect(self, new_claim: Claim, existing_claims: Sequence[Claim]) -> list[MarkerDraft]:
        drafts: list[MarkerDraft] = []
        predicate = new_claim.predicate.lower()
        if predicate not in self.predicates:
            return drafts

        for existing in existing_claims:
            if existing.subject != new_claim.subject or existing.predicate.lower() != predicate:
                continue
            if existing.value == new_claim.value:
                continue
            drafts.append(
                MarkerDraft(
                    kind=MarkerKind.CONTRADICTION,
                    subject=new_claim.subject,
                    predicate=new_claim.predicate,
                    claim_ids=(existing.id, new_claim.id),
                    evidence=(evidence_from_claim(existing), evidence_from_claim(new_claim)),
                    dimensions=("value",),
                    severity=0.8,
                    confidence=self._confidence(existing, new_claim),
                    message=(
                        f"{new_claim.subject} {new_claim.predicate} "
                        f"{existing.value!r} vs {new_claim.value!r}"
                    ),
                    metadata={"detector": self.name},
                )
            )
        return drafts

    @staticmethod
    def _confidence(existing: Claim, new_claim: Claim) -> float | None:
        values = [
            value
            for value in (existing.confidence, new_claim.confidence)
            if value is not None
        ]
        return min(values) if values else None
