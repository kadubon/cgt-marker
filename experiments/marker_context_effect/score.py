from __future__ import annotations

from collections.abc import Mapping, Sequence

SCORING_VERSION = "1.1.0"

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
    marker_success = (
        has_conflict and asserts_visible_conflict and mentions_both_values and mentions_sources
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
    }


def _mentions_all(text: str, items: Sequence[str]) -> bool:
    return bool(items) and all(item in text for item in items)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return []
    return [str(item).casefold() for item in value]
