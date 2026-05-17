# Concepts

This document defines the small vocabulary used by `cgt-marker`. The goal is to
make the package easy to inspect, port, and modify.

## Claim

A `Claim` is a structured assertion supplied by the caller. It is not extracted by
the library.

Required fields:

- `subject`: what the claim is about, such as `deadline` or `meeting.date`.
- `predicate`: the relation, such as `equals`, `status`, `gte`, or `lte`.
- `value`: a JSON-compatible value.
- `source`: where the claim came from.

Optional fields:

- `confidence`: caller-supplied confidence, if available.
- `scope`: caller-defined JSON-compatible context.
- `metadata`: extra context such as `quote` and `uri`.

Claim construction stays lightweight. Callers that want explicit checks can use
`validate_claim`, which returns non-throwing `ValidationIssue` records for empty
required fields, invalid confidence, or non-JSON-compatible values.

## EvidenceRef

`EvidenceRef` is a lightweight pointer copied into markers. The default detectors
copy the claim `source`, plus `metadata.quote` and `metadata.uri` when present. This
keeps markers inspectable without making the ledger a document store.

## MarkerDraft

A `MarkerDraft` is a detector result before policy handling. Detectors should return
drafts rather than final markers so policy behavior remains swappable.

## Marker

A `Marker` is a first-class record of contradiction or tension. It stores:

- marker kind and status;
- related subject/predicate;
- claim ids;
- evidence refs;
- dimensions such as `value`, `status`, `temporal`, or `numeric_interval`;
- message and metadata.

Markers are not removed automatically. They leave the open set only when the caller
explicitly resolves, ignores, supersedes, or quarantines them.

## MarkerPolicy

The default policy is `MARK_ONLY`: keep claims and create an open marker. Other MVP
policies are documented in [API status](api.md).

`BLOCK_ACTION` does not roll back the claim. It records the claim and marker, then
returns `PolicyResult.blocked = True` so the caller can decide whether to stop a
downstream action.

## MarkerLedger

`MarkerLedger` coordinates stores, detectors, policy finalization, and rendering.
The ledger is the state object. Renderer output is a projection of that state, not a
replacement for it.
