from __future__ import annotations

from dataclasses import dataclass, field

from cgt_marker.core.claim import Claim
from cgt_marker.core.marker import Marker


@dataclass
class InMemoryStore:
    """Simple process-local store for claims and markers."""

    _claims: list[Claim] = field(default_factory=list)
    _markers: dict[str, Marker] = field(default_factory=dict)

    def add_claim(self, claim: Claim) -> None:
        self._claims.append(claim)

    def list_claims(self) -> list[Claim]:
        return list(self._claims)

    def add_marker(self, marker: Marker) -> None:
        self._markers[marker.id] = marker

    def update_marker(self, marker: Marker) -> None:
        if marker.id not in self._markers:
            raise KeyError(f"Unknown marker id: {marker.id}")
        self._markers[marker.id] = marker

    def list_markers(self) -> list[Marker]:
        return list(self._markers.values())

    def clear(self) -> None:
        self._claims.clear()
        self._markers.clear()
