from __future__ import annotations

from datetime import UTC, datetime

from cgt_marker import Claim, CounterIdGenerator, FrozenClock, MarkerLedger


def main() -> None:
    ledger = MarkerLedger.default(
        id_generator=CounterIdGenerator(),
        clock=FrozenClock(datetime(2026, 6, 1, tzinfo=UTC)),
    )
    ledger.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    ledger.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))

    prompt = f"""Use the following unresolved marker context when answering.

{ledger.render_marker_context()}

Task: draft the next response without hiding unresolved contradictions.
"""
    print(prompt)


if __name__ == "__main__":
    main()
