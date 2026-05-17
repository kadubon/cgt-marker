from __future__ import annotations

from typing import Protocol

from cgt_marker.core.claim import Claim
from cgt_marker.core.marker import Marker


class ClaimStore(Protocol):
    """Storage boundary for claims."""

    def add_claim(self, claim: Claim) -> None: ...

    def list_claims(self) -> list[Claim]: ...


class MarkerStore(Protocol):
    """Storage boundary for markers."""

    def add_marker(self, marker: Marker) -> None: ...

    def update_marker(self, marker: Marker) -> None: ...

    def list_markers(self) -> list[Marker]: ...


class LedgerStore(ClaimStore, MarkerStore, Protocol):
    """Combined store used by MarkerLedger."""

    def clear(self) -> None: ...
