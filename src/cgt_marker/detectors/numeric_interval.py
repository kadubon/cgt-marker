"""Deterministic numeric interval conflicts for a small predicate vocabulary."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import NamedTuple

from cgt_marker.core.claim import Claim
from cgt_marker.core.detector import evidence_from_claim
from cgt_marker.core.marker import MarkerDraft, MarkerKind


class Bound(NamedTuple):
    value: float
    inclusive: bool


class Interval(NamedTuple):
    lower: Bound | None
    upper: Bound | None


@dataclass(frozen=True)
class NumericIntervalConflictDetector:
    """Detect non-overlapping numeric interval constraints for the same subject."""

    name: str = "numeric_interval"

    def detect(self, new_claim: Claim, existing_claims: Sequence[Claim]) -> list[MarkerDraft]:
        drafts: list[MarkerDraft] = []
        new_interval = self._interval_for(new_claim)
        if new_interval is None:
            return drafts

        for existing in existing_claims:
            if existing.subject != new_claim.subject:
                continue
            existing_interval = self._interval_for(existing)
            if existing_interval is None or self._overlaps(existing_interval, new_interval):
                continue
            drafts.append(
                MarkerDraft(
                    kind=MarkerKind.CONTRADICTION,
                    subject=new_claim.subject,
                    predicate="numeric_interval",
                    claim_ids=(existing.id, new_claim.id),
                    evidence=(evidence_from_claim(existing), evidence_from_claim(new_claim)),
                    dimensions=("numeric_interval",),
                    severity=0.85,
                    message=(
                        f"{new_claim.subject} interval conflict: "
                        f"{existing.predicate} {existing.value!r} vs "
                        f"{new_claim.predicate} {new_claim.value!r}"
                    ),
                    metadata={"detector": self.name},
                )
            )
        return drafts

    @staticmethod
    def _interval_for(claim: Claim) -> Interval | None:
        if not isinstance(claim.value, int | float):
            return None
        value = float(claim.value)
        predicate = claim.predicate.lower()
        if predicate == "equals":
            bound = Bound(value, True)
            return Interval(bound, bound)
        if predicate == "gte":
            return Interval(Bound(value, True), None)
        if predicate == "gt":
            return Interval(Bound(value, False), None)
        if predicate == "lte":
            return Interval(None, Bound(value, True))
        if predicate == "lt":
            return Interval(None, Bound(value, False))
        return None

    @classmethod
    def _overlaps(cls, left: Interval, right: Interval) -> bool:
        lower = cls._max_lower(left.lower, right.lower)
        upper = cls._min_upper(left.upper, right.upper)
        if lower is None or upper is None:
            return True
        if lower.value < upper.value:
            return True
        if lower.value > upper.value:
            return False
        return lower.inclusive and upper.inclusive

    @staticmethod
    def _max_lower(left: Bound | None, right: Bound | None) -> Bound | None:
        if left is None:
            return right
        if right is None:
            return left
        if left.value > right.value:
            return left
        if right.value > left.value:
            return right
        return Bound(left.value, left.inclusive and right.inclusive)

    @staticmethod
    def _min_upper(left: Bound | None, right: Bound | None) -> Bound | None:
        if left is None:
            return right
        if right is None:
            return left
        if left.value < right.value:
            return left
        if right.value < left.value:
            return right
        return Bound(left.value, left.inclusive and right.inclusive)
