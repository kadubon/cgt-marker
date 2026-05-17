from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from cgt_marker.core.claim import Claim


@dataclass(frozen=True)
class ValidationIssue:
    """Non-throwing validation issue for caller-supplied claims."""

    field: str
    code: str
    message: str


def validate_claim(claim: Claim) -> list[ValidationIssue]:
    """Return validation issues for a claim without mutating or rejecting it."""

    issues: list[ValidationIssue] = []
    if not claim.subject.strip():
        issues.append(
            ValidationIssue("subject", "required", "subject must be a non-empty string")
        )
    if not claim.predicate.strip():
        issues.append(
            ValidationIssue("predicate", "required", "predicate must be a non-empty string")
        )
    if not claim.source.strip():
        issues.append(ValidationIssue("source", "required", "source must be a non-empty string"))
    if claim.confidence is not None and not 0 <= claim.confidence <= 1:
        issues.append(
            ValidationIssue("confidence", "range", "confidence must be between 0 and 1")
        )
    if not is_json_value(claim.value):
        issues.append(ValidationIssue("value", "json", "value must be JSON-compatible"))
    if not _is_json_mapping(claim.scope):
        issues.append(ValidationIssue("scope", "json", "scope must be a JSON-compatible mapping"))
    if not _is_json_mapping(claim.metadata):
        issues.append(
            ValidationIssue("metadata", "json", "metadata must be a JSON-compatible mapping")
        )
    return issues


def is_json_value(value: object) -> bool:
    """Return whether a value is compatible with portable JSON state."""

    if value is None or isinstance(value, bool | str):
        return True
    if isinstance(value, int) and not isinstance(value, bool):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return all(is_json_value(item) for item in value)
    if isinstance(value, Mapping):
        return _is_json_mapping(value)
    return False


def _is_json_mapping(value: Mapping[Any, Any]) -> bool:
    return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())
