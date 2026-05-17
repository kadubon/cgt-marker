from __future__ import annotations

from cgt_marker import Claim
from cgt_marker.adapters.langgraph import add_claims_to_state, render_marker_context_from_state


def main() -> None:
    state: dict[str, object] = {"messages": []}
    state = add_claims_to_state(
        state,
        [
            Claim("release.status", "status", "approved", "review-system"),
            Claim("release.status", "status", "rejected", "qa-system"),
        ],
    )

    print(render_marker_context_from_state(state))


if __name__ == "__main__":
    main()
