from __future__ import annotations

from dataclasses import replace

from cgt_marker.core.ids import IdGenerator
from cgt_marker.core.marker import Marker, MarkerDraft, MarkerStatus
from cgt_marker.core.policy import MarkerPolicy, PolicyResult
from cgt_marker.core.time import Clock

UNSUPPORTED_POLICIES = frozenset(
    {
        MarkerPolicy.BRANCH_CONTEXT,
        MarkerPolicy.WEIGHTED_CONTINUE,
    }
)


def finalize_marker(
    draft: MarkerDraft,
    *,
    policy: MarkerPolicy,
    id_generator: IdGenerator,
    clock: Clock,
) -> PolicyResult:
    """Finalize one detector draft according to the selected marker policy."""

    if policy in UNSUPPORTED_POLICIES:
        raise NotImplementedError(
            f"{policy.value} is reserved for future work and is not implemented in the MVP."
        )

    metadata = dict(draft.metadata)
    blocked = False
    requires_review = False
    status = MarkerStatus.OPEN

    if policy is MarkerPolicy.REQUIRE_REVIEW:
        requires_review = True
        metadata["requires_review"] = True
    elif policy is MarkerPolicy.BLOCK_ACTION:
        blocked = True
        metadata["blocked"] = True
    elif policy is MarkerPolicy.QUARANTINE:
        status = MarkerStatus.QUARANTINED
        metadata["quarantined"] = True

    evidence = tuple(
        evidence if evidence.id else replace(evidence, id=id_generator.new_id("E"))
        for evidence in draft.evidence
    )
    marker = Marker(
        id=id_generator.new_id("M"),
        kind=draft.kind,
        status=status,
        subject=draft.subject,
        predicate=draft.predicate,
        claim_ids=draft.claim_ids,
        evidence=evidence,
        dimensions=draft.dimensions,
        severity=draft.severity,
        confidence=draft.confidence,
        message=draft.message,
        created_at=clock.now(),
        metadata=metadata,
    )
    return PolicyResult(
        policy=policy,
        markers=(marker,),
        blocked=blocked,
        requires_review=requires_review,
        message="Action blocked by marker policy." if blocked else None,
        metadata={"marker_count": 1},
    )
