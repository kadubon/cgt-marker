from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from cgt_marker.core.claim import Claim
from cgt_marker.core.ledger import MarkerLedger


def add_claims_to_state(
    state: Mapping[str, Any],
    claims: Sequence[Claim],
    ledger_key: str = "cgt_marker",
) -> dict[str, Any]:
    """Return a new dict-like state with claims added to a serialized ledger."""

    ledger = MarkerLedger.from_state(dict(state.get(ledger_key, {})))
    ledger.add_claims(claims)
    next_state = dict(state)
    next_state[ledger_key] = ledger.export_state()
    return next_state


def render_marker_context_from_state(
    state: Mapping[str, Any],
    ledger_key: str = "cgt_marker",
) -> str:
    """Render unresolved marker context from a dict-like serialized ledger state."""

    ledger = MarkerLedger.from_state(dict(state.get(ledger_key, {})))
    return ledger.render_marker_context()
