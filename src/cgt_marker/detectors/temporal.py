"""Deterministic temporal conflicts for normalized ISO date/datetime strings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from cgt_marker.core.claim import Claim
from cgt_marker.core.detector import evidence_from_claim
from cgt_marker.core.marker import MarkerDraft, MarkerKind


@dataclass(frozen=True)
class TemporalConflictDetector:
    """Detect conflicting ISO date/datetime values for the same subject/predicate."""

    name: str = "temporal"

    def detect(self, new_claim: Claim, existing_claims: Sequence[Claim]) -> list[MarkerDraft]:
        drafts: list[MarkerDraft] = []
        new_time = self._parse_temporal(new_claim.value)
        if new_time is None:
            return drafts

        for existing in existing_claims:
            if existing.subject != new_claim.subject or existing.predicate != new_claim.predicate:
                continue
            existing_time = self._parse_temporal(existing.value)
            if existing_time is None or existing_time == new_time:
                continue
            drafts.append(
                MarkerDraft(
                    kind=MarkerKind.CONTRADICTION,
                    subject=new_claim.subject,
                    predicate=new_claim.predicate,
                    claim_ids=(existing.id, new_claim.id),
                    evidence=(evidence_from_claim(existing), evidence_from_claim(new_claim)),
                    dimensions=("temporal",),
                    severity=0.8,
                    message=(
                        f"{new_claim.subject} {new_claim.predicate} "
                        f"{existing.value!r} vs {new_claim.value!r}"
                    ),
                    metadata={"detector": self.name},
                )
            )
        return drafts

    @staticmethod
    def _parse_temporal(value: object) -> date | datetime | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
            try:
                if len(text) == 10:
                    return date.fromisoformat(text[:10])
                return datetime.fromisoformat(text)
            except ValueError:
                return None
        return None
