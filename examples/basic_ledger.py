from __future__ import annotations

from datetime import UTC, datetime

from cgt_marker import Claim, CounterIdGenerator, FrozenClock, MarkerLedger


def main() -> None:
    ledger = MarkerLedger.default(
        id_generator=CounterIdGenerator(),
        clock=FrozenClock(datetime(2026, 6, 1, tzinfo=UTC)),
    )

    ledger.add_claim(
        Claim(
            subject="meeting.date",
            predicate="equals",
            value="2026-06-01",
            source="email",
        )
    )
    ledger.add_claim(
        Claim(
            subject="meeting.date",
            predicate="equals",
            value="2026-06-03",
            source="calendar",
        )
    )

    print(ledger.render_marker_context())


if __name__ == "__main__":
    main()
