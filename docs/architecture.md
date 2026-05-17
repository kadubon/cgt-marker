# Architecture

`cgt-marker` is organized around small protocols and dataclasses. The core package
does not depend on any agent framework.

## Boundaries

- `core`: data models, protocols, ID generation, clocks, and `MarkerLedger`.
- `detectors`: deterministic conflict detectors.
- `policies`: marker finalization behavior.
- `storage`: in-memory and JSONL stores.
- `renderers`: prompt/report projections of marker state.
- `adapters`: optional framework-shaped helpers, currently plain dict-state helpers.

## Data Flow

```text
Claim
  -> ConflictDetector.detect(...)
  -> MarkerDraft
  -> MarkerPolicy finalization
  -> MarkerLedger storage
  -> Renderer projection
```

The ledger stores claims before returning a successful policy result. For reserved
policy modes that are not implemented, conflict finalization raises before the new
claim is saved. This avoids silent fallback to `MARK_ONLY`.

## Loose Coupling

Detectors do not know about stores. Stores do not know about detector rules.
Renderers receive markers and do not mutate the ledger. The LangGraph-like adapter
uses exported/imported dict state and does not import LangGraph.

This separation is intentional: a TypeScript, Rust, or Go port should be able to keep
the same concepts without copying Python-specific implementation details.
