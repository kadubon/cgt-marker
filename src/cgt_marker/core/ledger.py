from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from cgt_marker.core.claim import Claim
from cgt_marker.core.detector import ConflictDetector
from cgt_marker.core.evidence import EvidenceRef
from cgt_marker.core.ids import IdGenerator, UUIDGenerator
from cgt_marker.core.marker import Marker, MarkerDraft, MarkerStatus
from cgt_marker.core.policy import MarkerPolicy, PolicyResult
from cgt_marker.core.store import LedgerStore
from cgt_marker.core.time import Clock, SystemClock
from cgt_marker.policies.marker_policy import finalize_marker
from cgt_marker.storage.jsonl import JsonlStore
from cgt_marker.storage.memory import InMemoryStore


class MarkerLedger:
    """Coordinates claims, detectors, policy finalization, storage, and rendering.

    The ledger is the retained state. Renderer output is only a projection of this
    state and should not be treated as a replacement for it.
    """

    def __init__(
        self,
        *,
        detectors: Sequence[ConflictDetector] = (),
        policy: MarkerPolicy = MarkerPolicy.MARK_ONLY,
        store: LedgerStore | None = None,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.detectors = tuple(detectors)
        self.policy = policy
        self.store = store if store is not None else InMemoryStore()
        self.id_generator = id_generator if id_generator is not None else UUIDGenerator()
        self.clock = clock if clock is not None else SystemClock()

    @classmethod
    def default(
        cls,
        *,
        policy: MarkerPolicy = MarkerPolicy.MARK_ONLY,
        store: LedgerStore | None = None,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> MarkerLedger:
        from cgt_marker.detectors import (
            ExactSlotConflictDetector,
            NumericIntervalConflictDetector,
            StatusConflictDetector,
            TemporalConflictDetector,
        )

        return cls(
            detectors=(
                StatusConflictDetector(),
                TemporalConflictDetector(),
                NumericIntervalConflictDetector(),
                ExactSlotConflictDetector(),
            ),
            policy=policy,
            store=store,
            id_generator=id_generator,
            clock=clock,
        )

    def add_claim(self, claim: Claim) -> PolicyResult:
        """Add one claim, run detectors, and persist generated markers.

        Successful policies keep the claim and any created markers. `BLOCK_ACTION`
        records state and returns a block signal for the caller's next action. For
        reserved policy modes, conflict finalization raises before the new claim is
        saved, avoiding silent fallback behavior.
        """

        prepared = self._prepare_claim(claim)
        existing_claims = self.store.list_claims()
        drafts = self._dedupe_drafts(
            draft
            for detector in self.detectors
            for draft in detector.detect(prepared, existing_claims)
        )
        marker_results = [
            finalize_marker(
                draft,
                policy=self.policy,
                id_generator=self.id_generator,
                clock=self.clock,
            )
            for draft in drafts
        ]
        markers = tuple(marker for result in marker_results for marker in result.markers)

        self.store.add_claim(prepared)
        for marker in markers:
            self.store.add_marker(marker)

        blocked = any(result.blocked for result in marker_results)
        return PolicyResult(
            policy=self.policy,
            markers=markers,
            blocked=blocked,
            requires_review=any(result.requires_review for result in marker_results),
            message="Action blocked by marker policy." if blocked else None,
            metadata={"draft_count": len(drafts), "marker_count": len(markers)},
        )

    def add_claims(self, claims: Sequence[Claim]) -> PolicyResult:
        """Add claims in order and aggregate policy results."""

        results = [self.add_claim(claim) for claim in claims]
        markers = tuple(marker for result in results for marker in result.markers)
        return PolicyResult(
            policy=self.policy,
            markers=markers,
            blocked=any(result.blocked for result in results),
            requires_review=any(result.requires_review for result in results),
            message="Action blocked by marker policy." if any(r.blocked for r in results) else None,
            metadata={"claim_count": len(claims), "marker_count": len(markers)},
        )

    def list_claims(self) -> list[Claim]:
        return self.store.list_claims()

    def list_markers(self) -> list[Marker]:
        return self.store.list_markers()

    def open_markers(self) -> list[Marker]:
        return [marker for marker in self.list_markers() if marker.status is MarkerStatus.OPEN]

    def list_open_markers(self) -> list[Marker]:
        return self.open_markers()

    def resolve_marker(self, marker_id: str, *, metadata: dict[str, Any] | None = None) -> Marker:
        return self._set_marker_status(marker_id, MarkerStatus.RESOLVED, metadata=metadata)

    def ignore_marker(self, marker_id: str, *, metadata: dict[str, Any] | None = None) -> Marker:
        return self._set_marker_status(marker_id, MarkerStatus.IGNORED, metadata=metadata)

    def supersede_marker(self, marker_id: str, *, metadata: dict[str, Any] | None = None) -> Marker:
        return self._set_marker_status(marker_id, MarkerStatus.SUPERSEDED, metadata=metadata)

    def export_state(self) -> dict[str, Any]:
        """Return a JSON-compatible state snapshot."""

        return {
            "claims": [claim.to_dict() for claim in self.list_claims()],
            "markers": [marker.to_dict() for marker in self.list_markers()],
        }

    def import_state(self, state: dict[str, Any]) -> None:
        """Replace current store contents from an exported state snapshot."""

        self.store.clear()
        for claim_data in state.get("claims", ()):
            self.store.add_claim(Claim.from_dict(claim_data))
        for marker_data in state.get("markers", ()):
            self.store.add_marker(Marker.from_dict(marker_data))

    @classmethod
    def from_state(
        cls,
        state: dict[str, Any],
        *,
        policy: MarkerPolicy = MarkerPolicy.MARK_ONLY,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> MarkerLedger:
        ledger = cls.default(policy=policy, id_generator=id_generator, clock=clock)
        ledger.import_state(state)
        return ledger

    def save_jsonl(self, path: str | Path) -> None:
        JsonlStore.save_state(path, claims=self.list_claims(), markers=self.list_markers())

    @classmethod
    def load_jsonl(
        cls,
        path: str | Path,
        *,
        policy: MarkerPolicy = MarkerPolicy.MARK_ONLY,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> MarkerLedger:
        ledger = cls.default(policy=policy, id_generator=id_generator, clock=clock)
        ledger.store = JsonlStore(path)
        return ledger

    def render_marker_context(self) -> str:
        from cgt_marker.renderers.prompt import PromptContextRenderer

        return PromptContextRenderer().render(self.open_markers())

    def _prepare_claim(self, claim: Claim) -> Claim:
        if claim.id:
            return claim
        return replace(claim, id=self.id_generator.new_id("C"))

    def _set_marker_status(
        self,
        marker_id: str,
        status: MarkerStatus,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> Marker:
        for marker in self.list_markers():
            if marker.id == marker_id:
                merged_metadata = dict(marker.metadata)
                if metadata:
                    merged_metadata.update(metadata)
                updated = replace(
                    marker,
                    status=status,
                    updated_at=self.clock.now(),
                    metadata=merged_metadata,
                )
                self.store.update_marker(updated)
                return updated
        raise KeyError(f"Unknown marker id: {marker_id}")

    @staticmethod
    def _dedupe_drafts(drafts: Iterable[MarkerDraft]) -> list[MarkerDraft]:
        merged: dict[tuple[object, ...], MarkerDraft] = {}
        for draft in drafts:
            key = (
                draft.kind,
                draft.subject,
                draft.predicate,
                frozenset(draft.claim_ids),
            )
            if key not in merged:
                merged[key] = draft
                continue
            merged[key] = MarkerLedger._merge_drafts(merged[key], draft)
        return list(merged.values())

    @staticmethod
    def _merge_drafts(left: MarkerDraft, right: MarkerDraft) -> MarkerDraft:
        return replace(
            left,
            evidence=MarkerLedger._merge_evidence(left.evidence, right.evidence),
            dimensions=MarkerLedger._ordered_union(left.dimensions, right.dimensions),
            severity=MarkerLedger._max_optional(left.severity, right.severity),
            confidence=MarkerLedger._min_optional(left.confidence, right.confidence),
            metadata=MarkerLedger._merge_metadata(left.metadata, right.metadata),
        )

    @staticmethod
    def _merge_evidence(
        left: Sequence[EvidenceRef],
        right: Sequence[EvidenceRef],
    ) -> tuple[EvidenceRef, ...]:
        seen: set[tuple[object, ...]] = set()
        merged: list[EvidenceRef] = []
        for evidence in (*left, *right):
            key = (
                evidence.id,
                evidence.claim_id,
                evidence.source,
                evidence.quote,
                evidence.uri,
                json.dumps(evidence.metadata, sort_keys=True),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(evidence)
        return tuple(merged)

    @staticmethod
    def _ordered_union(left: Sequence[str], right: Sequence[str]) -> tuple[str, ...]:
        seen: set[str] = set()
        values: list[str] = []
        for value in (*left, *right):
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
        return tuple(values)

    @staticmethod
    def _max_optional(left: float | None, right: float | None) -> float | None:
        if left is None:
            return right
        if right is None:
            return left
        return max(left, right)

    @staticmethod
    def _min_optional(left: float | None, right: float | None) -> float | None:
        if left is None:
            return right
        if right is None:
            return left
        return min(left, right)

    @staticmethod
    def _merge_metadata(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        detectors: list[str] = []
        for metadata in (left, right):
            MarkerLedger._collect_detectors(metadata, detectors)
            for key, value in metadata.items():
                if key in {"detector", "detectors"}:
                    continue
                if key not in merged:
                    merged[key] = value
                elif merged[key] != value:
                    merged[key] = MarkerLedger._merge_metadata_value(merged[key], value)
        if detectors:
            merged["detector"] = detectors[0]
            merged["detectors"] = detectors
        return merged

    @staticmethod
    def _collect_detectors(metadata: dict[str, Any], detectors: list[str]) -> None:
        detector = metadata.get("detector")
        if isinstance(detector, str) and detector not in detectors:
            detectors.append(detector)
        detector_list = metadata.get("detectors")
        if isinstance(detector_list, Sequence) and not isinstance(detector_list, str | bytes):
            for item in detector_list:
                if isinstance(item, str) and item not in detectors:
                    detectors.append(item)

    @staticmethod
    def _merge_metadata_value(left: Any, right: Any) -> list[Any]:
        values = left if isinstance(left, list) else [left]
        if right not in values:
            return [*values, right]
        return values
