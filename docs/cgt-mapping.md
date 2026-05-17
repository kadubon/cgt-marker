# CGT Mapping

This document states the implementation mapping only. It is not a replacement for
the paper and does not claim to implement the full CGT formal system.

Reference:

Takahashi, K. (2026). *Constraint Generative Theory: Typed Constraint Effects and
Scientific Availability*. Zenodo. https://doi.org/10.5281/zenodo.20254492

## Operational Mapping

- constraint presentation -> `Claim`, detector rule, marker policy, renderer rule
- effect profile fragment -> ledger state: claims, markers, statuses, provenance
- inconsistency policy -> `MarkerPolicy`
- inconsistency effect -> `Marker`
- scientific availability -> serializable claim/marker log with evidence references
- continuation -> downstream execution while unresolved markers remain visible
- report-forgetfulness -> renderer output may omit detail, while the ledger retains
  marker state

## What Is Preserved

The MVP preserves the marker-policy idea: contradiction does not collapse state.
Conflicting claims remain present, and the contradiction is represented as a marker
that downstream code can inspect.

The package also preserves the report/projection distinction in a software sense:
rendered prompt context is only a view. The ledger remains the source of retained
claims, markers, statuses, and provenance.

The local Ollama experiment uses this mapping narrowly. The baseline condition
passes only a report projection. The marker-aware condition passes the same report
projection plus rendered marker context. The experiment asks whether that extra
projection helps a model mention unresolved contradictions; it does not validate the
full CGT theory.

The experiment therefore tests a software projection behavior: whether adding the
marker projection changes one model's response under fixed prompts and deterministic
options. It does not test the truth of CGT, the completeness of the formal theory, or
general agent reliability.

## What Is Not Implemented

This package does not implement:

- the full CGT formal system;
- comparability bootstrap algorithms;
- constraint-marginal cover;
- interaction-marginal cover;
- certified finite categories;
- theorem proving;
- paraconsistent inference;
- belief revision;
- truth adjudication;
- automatic claim extraction.
