from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from cgt_marker.core.marker import Marker
from cgt_marker.core.types import JSONDict


class MarkerPolicy(StrEnum):
    """Policy mode used when detector drafts are finalized into markers.

    `BRANCH_CONTEXT` and `WEIGHTED_CONTINUE` are reserved API names. They raise
    during conflict finalization until concrete semantics are implemented.
    """

    MARK_ONLY = "mark_only"
    QUARANTINE = "quarantine"
    REQUIRE_REVIEW = "require_review"
    BRANCH_CONTEXT = "branch_context"
    WEIGHTED_CONTINUE = "weighted_continue"
    BLOCK_ACTION = "block_action"


@dataclass(frozen=True)
class PolicyResult:
    """Result returned after applying a marker policy.

    `blocked=True` is a caller signal. It does not mean the claim or marker was
    rolled back.
    """

    policy: MarkerPolicy = MarkerPolicy.MARK_ONLY
    markers: tuple[Marker, ...] = ()
    blocked: bool = False
    requires_review: bool = False
    message: str | None = None
    metadata: JSONDict = field(default_factory=dict)
