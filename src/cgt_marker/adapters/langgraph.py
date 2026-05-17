from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from cgt_marker.core.claim import Claim
from cgt_marker.core.ledger import MarkerLedger

LedgerFactory = Callable[[Mapping[str, Any]], MarkerLedger]


def add_claims_to_state(
    state: Mapping[str, Any],
    claims: Sequence[Claim],
    ledger_key: str = "cgt_marker",
    ledger_factory: LedgerFactory | None = None,
) -> dict[str, Any]:
    """Return a new dict-like state with claims added to a serialized ledger."""

    ledger = _ledger_from_state(state, ledger_key=ledger_key, ledger_factory=ledger_factory)
    ledger.add_claims(claims)
    next_state = dict(state)
    next_state[ledger_key] = ledger.export_state()
    return next_state


def render_marker_context_from_state(
    state: Mapping[str, Any],
    ledger_key: str = "cgt_marker",
    ledger_factory: LedgerFactory | None = None,
) -> str:
    """Render unresolved marker context from a dict-like serialized ledger state."""

    ledger = _ledger_from_state(state, ledger_key=ledger_key, ledger_factory=ledger_factory)
    return ledger.render_marker_context()


def _ledger_from_state(
    state: Mapping[str, Any],
    *,
    ledger_key: str,
    ledger_factory: LedgerFactory | None,
) -> MarkerLedger:
    serialized = dict(state.get(ledger_key, {}))
    if ledger_factory is not None:
        return ledger_factory(serialized)
    return MarkerLedger.from_state(serialized)
