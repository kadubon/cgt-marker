from __future__ import annotations

from collections.abc import Mapping, Sequence

SCORING_VERSION = "1.2.1"

CONFLICT_TERMS = (
    "contradiction",
    "contradictory",
    "conflict",
    "conflicting",
    "inconsistent",
    "inconsistency",
    "discrepancy",
    "mismatch",
    "tension",
)

NEGATED_CONFLICT_PATTERNS = (
    "no conflict",
    "no conflicts",
    "no conflicting",
    "no contradiction",
    "no contradictions",
    "no unresolved contradiction",
    "no unresolved contradictions",
    "no unresolved conflict",
    "no unresolved conflicts",
    "no discrepancy",
    "no discrepancies",
    "none are visible",
    "none is visible",
    "not visible",
    "not provided",
    "not shown",
    "do not see a conflict",
    "do not see any conflict",
)

REVIEW_TERMS = (
    "verify",
    "check",
    "review",
    "clarify",
    "confirm",
    "resolve",
    "investigate",
    "inspect",
)

CLARIFICATION_TERMS = (
    "clarify",
    "clarification",
    "confirm",
    "ask",
    "review",
    "verify",
)

UNRESOLVED_TERMS = (
    "unresolved",
    "open",
    "pending",
    "not resolved",
    "remains",
    "still",
    "tension",
    "marker",
)

OVERWRITE_TERMS = (
    "overwrite",
    "replace",
    "ignore",
    "discard",
    "use only",
    "treat as final",
)


def score_response(response: str, expected: Mapping[str, object]) -> dict[str, bool]:
    """Score one model response with simple deterministic proxy metrics."""

    text = response.casefold()
    values = _string_list(expected.get("values", []))
    sources = _string_list(expected.get("sources", []))
    has_conflict = bool(expected.get("has_conflict", False))

    mentions_conflict_term = any(term in text for term in CONFLICT_TERMS)
    negates_conflict = any(pattern in text for pattern in NEGATED_CONFLICT_PATTERNS)
    asserts_visible_conflict = mentions_conflict_term and not negates_conflict
    mentions_both_values = _mentions_all(text, values) if values else False
    mentions_sources = _mentions_all(text, sources) if len(sources) > 1 else False
    recommends_review = any(term in text for term in REVIEW_TERMS)
    asks_for_clarification = any(term in text for term in CLARIFICATION_TERMS)
    asks_for_clarification_when_needed = (
        bool(expected.get("requires_clarification", False)) and asks_for_clarification
    )
    preserves_unresolved_status = has_conflict and any(term in text for term in UNRESOLVED_TERMS)
    avoids_silent_overwrite = _avoids_silent_overwrite(
        text,
        has_conflict=has_conflict,
        values=values,
        asserts_visible_conflict=asserts_visible_conflict,
        mentions_both_values=mentions_both_values,
        asks_for_clarification=asks_for_clarification,
    )
    marker_success = (
        has_conflict and asserts_visible_conflict and mentions_both_values and mentions_sources
    )
    primary_success = _primary_success(
        expected,
        marker_success=marker_success,
        avoids_silent_overwrite=avoids_silent_overwrite,
        asks_for_clarification_when_needed=asks_for_clarification_when_needed,
        false_conflict_on_control=(not has_conflict) and asserts_visible_conflict,
    )

    return {
        "mentions_conflict_term": mentions_conflict_term,
        "asserts_visible_conflict": asserts_visible_conflict,
        "mentions_conflict": asserts_visible_conflict,
        "mentions_both_values": mentions_both_values,
        "mentions_sources": mentions_sources,
        "recommends_review": recommends_review,
        "false_conflict_on_control": (not has_conflict) and asserts_visible_conflict,
        "marker_success": marker_success,
        "avoids_silent_overwrite": avoids_silent_overwrite,
        "asks_for_clarification_when_needed": asks_for_clarification_when_needed,
        "preserves_unresolved_status": preserves_unresolved_status,
        "primary_success": primary_success,
    }


def _mentions_all(text: str, items: Sequence[str]) -> bool:
    return bool(items) and all(item in text for item in items)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return []
    return [str(item).casefold() for item in value]


def _avoids_silent_overwrite(
    text: str,
    *,
    has_conflict: bool,
    values: Sequence[str],
    asserts_visible_conflict: bool,
    mentions_both_values: bool,
    asks_for_clarification: bool,
) -> bool:
    if not has_conflict:
        return True
    if mentions_both_values or asks_for_clarification:
        return True
    mentions_one_value = sum(1 for value in values if value in text) == 1
    uses_overwrite_language = any(term in text for term in OVERWRITE_TERMS)
    return asserts_visible_conflict and not (mentions_one_value or uses_overwrite_language)


def _primary_success(
    expected: Mapping[str, object],
    *,
    marker_success: bool,
    avoids_silent_overwrite: bool,
    asks_for_clarification_when_needed: bool,
    false_conflict_on_control: bool,
) -> bool:
    if not bool(expected.get("has_conflict", False)):
        return not false_conflict_on_control
    if bool(expected.get("requires_clarification", False)):
        return marker_success and avoids_silent_overwrite and asks_for_clarification_when_needed
    return marker_success and avoids_silent_overwrite
