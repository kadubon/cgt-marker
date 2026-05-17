"""Deterministic temporal conflicts for normalized ISO date/datetime strings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import NamedTuple

from cgt_marker.core.claim import Claim
from cgt_marker.core.detector import evidence_from_claim
from cgt_marker.core.marker import MarkerDraft, MarkerKind


class TemporalValue(NamedTuple):
    precision: str
    value: date | datetime
    timezone_aware: bool = False


@dataclass(frozen=True)
class TemporalConflictDetector:
    """Detect conflicting ISO date/datetime values for the same subject/predicate.

    Policy:
    - date-only strings compare only with date-only strings;
    - datetime strings compare only with datetime strings;
    - timezone-aware datetimes normalize to UTC;
    - naive and timezone-aware datetimes are not comparable;
    - natural language date parsing is intentionally out of scope.
    """

    name: str = "temporal"

    def detect(self, new_claim: Claim, existing_claims: Sequence[Claim]) -> list[MarkerDraft]:
        drafts: list[MarkerDraft] = []
        new_temporal = self._parse_temporal(new_claim.value)
        if new_temporal is None:
            return drafts

        for existing in existing_claims:
            if existing.subject != new_claim.subject or existing.predicate != new_claim.predicate:
                continue
            existing_temporal = self._parse_temporal(existing.value)
            if existing_temporal is None or not self._comparable(existing_temporal, new_temporal):
                continue
            if existing_temporal.value == new_temporal.value:
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
    def _parse_temporal(value: object) -> TemporalValue | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
            try:
                if len(text) == 10:
                    return TemporalValue("date", date.fromisoformat(text[:10]))
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    return TemporalValue("datetime", parsed, timezone_aware=False)
                return TemporalValue(
                    "datetime",
                    parsed.astimezone(UTC),
                    timezone_aware=True,
                )
            except ValueError:
                return None
        return None

    @staticmethod
    def _comparable(left: TemporalValue, right: TemporalValue) -> bool:
        return (
            left.precision == right.precision
            and left.timezone_aware == right.timezone_aware
        )
