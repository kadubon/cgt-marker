# API Status

This page describes the MVP API surface. It is not a full generated API reference.

## Stable MVP API

Core:

- `Claim`
- `EvidenceRef`
- `Marker`
- `MarkerDraft`
- `MarkerKind`
- `MarkerStatus`
- `MarkerPolicy`
- `PolicyResult`
- `MarkerLedger`

Utilities:

- `CounterIdGenerator`
- `UUIDGenerator`
- `FrozenClock`
- `SystemClock`

Default detectors:

- `ExactSlotConflictDetector`
- `StatusConflictDetector`
- `TemporalConflictDetector`
- `NumericIntervalConflictDetector`

Storage and rendering:

- `InMemoryStore`
- `JsonlStore`
- `MarkdownRenderer`
- `PromptContextRenderer`

Adapter helpers:

- `add_claims_to_state`
- `render_marker_context_from_state`

## Supported Policies

- `MARK_ONLY`: supported and default.
- `REQUIRE_REVIEW`: supported.
- `BLOCK_ACTION`: supported as a caller signal. It is not rollback.
- `QUARANTINE`: implemented but experimental.

## Reserved Policies

- `BRANCH_CONTEXT`
- `WEIGHTED_CONTINUE`

Reserved policies are not silently treated as `MARK_ONLY`. If a conflict reaches
marker finalization under a reserved policy, the library raises `NotImplementedError`.

## Compatibility Notes

The project uses typed dataclasses and JSON-compatible state shapes to keep ports to
other languages straightforward. The Python package should remain import-safe without
LangGraph or any LLM framework installed.
