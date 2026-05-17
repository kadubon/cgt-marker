# Extending

The extension points are intentionally small.

## Custom Detector

A detector implements the `ConflictDetector` protocol:

```python
from collections.abc import Sequence

from cgt_marker import Claim, MarkerDraft


class MyDetector:
    name = "my_detector"

    def detect(self, new_claim: Claim, existing_claims: Sequence[Claim]) -> list[MarkerDraft]:
        return []
```

Then pass it to `MarkerLedger`:

```python
from cgt_marker import MarkerLedger

ledger = MarkerLedger(detectors=[MyDetector()])
```

Detectors should be deterministic and should not mutate the ledger. They should
return `MarkerDraft` records and let policy code finalize marker status and metadata.

## Custom Store

A store implements the `LedgerStore` protocol: add/list claims, add/update/list
markers, and clear state. Stores should preserve all claims and markers unless the
caller explicitly clears or replaces state.

## Custom Renderer

Renderers receive marker sequences and return text. A renderer is a projection of
ledger state. It should not delete or resolve markers.

## Framework Adapters

Adapters should remain optional. If an adapter targets a framework, importing
`cgt_marker` should still work without that framework installed.
