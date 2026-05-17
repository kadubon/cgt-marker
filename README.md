# cgt-marker

`cgt-marker` is a small Python state layer for agents that need to keep working
after they encounter contradictory information.

Instead of overwriting one claim with another, it records structured claims, detects
simple conflicts, creates typed contradiction markers, preserves provenance, and
renders unresolved markers back into prompts or downstream workflow state. It does
not decide what is true, revise beliefs automatically, prove logical theorems, or
replace an agent framework.

The default behavior is:

1. keep every claim that was added;
2. detect deterministic conflicts between a new claim and existing claims;
3. create an open marker when a conflict is found;
4. let the caller continue while unresolved markers remain visible.

## What this repo is for

Use `cgt-marker` when an agent can receive incompatible claims from tools, users,
documents, memory, or system events, and you want those contradictions to remain
explicit instead of being overwritten or hidden in a summary. The core abstraction is
a marker ledger: a retained, serializable state object containing claims, markers,
marker statuses, timestamps, and provenance.

The package is intentionally small. The core has no LLM calls, no network calls, no
database requirement, and no required dependency on LangGraph, AutoGen, CrewAI, or
any other agent framework.

## What the library does

The core data flow is:

```text
Claim -> ConflictDetector -> MarkerDraft -> MarkerPolicy -> MarkerLedger -> Renderer
```

- `Claim` stores a typed assertion such as `deadline equals 2026-06-01`.
- `ConflictDetector` compares a new claim with claims already in the ledger.
- `MarkerDraft` is a detector result before policy handling.
- `MarkerPolicy` decides how to finalize a marker.
- `MarkerLedger` stores claims, markers, status, timestamps, and provenance.
- Renderers produce prompt/report context. A rendered context is only a projection
  of the ledger, not the ledger itself.

The central rule is: contradiction is not failure. A contradiction becomes a marker,
and both conflicting claims remain in the ledger unless the caller explicitly builds
different behavior outside this package.

## Why marker ledger?

Long-running agents often receive incompatible claims from different tools or
documents. A normal summary can accidentally overwrite one side. `cgt-marker` keeps a
small ledger of claims and typed markers so unresolved tension remains inspectable
by later code, prompts, or human review.

## Why not belief revision?

Belief revision tries to decide how a belief set should change when new information
arrives. This package does not decide which claim should win. It records the claims,
marks configured conflicts, and leaves resolution to explicit downstream code.

## Why not paraconsistent theorem proving?

Paraconsistent logic studies inference under inconsistency. `cgt-marker` does not
perform logical inference or prove formulas. It is only a state layer for retaining
structured claims, provenance, and contradiction markers.

## Install

From a checkout:

```powershell
uv sync
```

Run checks:

```powershell
uv run pytest
uv run ruff check .
uv run mypy
```

## Quickstart

```python
from cgt_marker import Claim, MarkerLedger

ledger = MarkerLedger.default()

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
```

Example output:

```text
Open contradiction markers:
- M-001 [contradiction] meeting.date equals '2026-06-01' vs '2026-06-03'
  sources: email, calendar
  status: open
```

## Provenance

Every claim has a required `source`. Optional evidence details can be stored in
`metadata`:

```python
Claim(
    subject="deadline",
    predicate="equals",
    value="2026-06-01",
    source="email",
    metadata={
        "quote": "The deadline is June 1.",
        "uri": "mail://message/123",
    },
)
```

When a marker is created, the detector copies `source`, `metadata.quote`, and
`metadata.uri` into lightweight `EvidenceRef` records. This is the reproducibility
surface for the MVP: enough source context to inspect why a marker exists.

## Policies

Supported MVP policies:

- `MARK_ONLY`: create an `OPEN` marker and keep all claims. This is the default.
- `REQUIRE_REVIEW`: create an `OPEN` marker with `requires_review: true` metadata.
- `BLOCK_ACTION`: create an `OPEN` marker and return `PolicyResult.blocked = True`.
  The claim and marker are still recorded; the block signal is for the caller's next
  action, not a rollback.
- `QUARANTINE`: create a `QUARANTINED` marker. This is experimental but implemented.

Reserved policy names:

- `BRANCH_CONTEXT`
- `WEIGHTED_CONTINUE`

These names are present so the API can grow without renaming the enum, but they are
not implemented in the MVP. If a conflict reaches marker finalization under either
policy, the library raises `NotImplementedError` instead of silently treating it like
`MARK_ONLY`.

## Detectors

Default deterministic detectors:

- `ExactSlotConflictDetector`: same subject and predicate, incompatible values for
  predicates such as `equals`, `is`, `status`, and `value`.
- `StatusConflictDetector`: configurable opposite pairs such as `approved/rejected`.
- `TemporalConflictDetector`: conflicting normalized ISO date/datetime values.
- `NumericIntervalConflictDetector`: simple non-overlapping numeric constraints from
  `lt`, `lte`, `gt`, `gte`, and `equals`.

Detectors are plugin-like. A custom detector only needs a `detect(new_claim,
existing_claims)` method that returns marker drafts.

## Examples

```powershell
uv run python examples/basic_ledger.py
uv run python examples/marker_aware_prompt.py
uv run python examples/langgraph_like_state.py
```

The LangGraph-like example uses plain dictionaries. It does not import LangGraph.

## Experiments

The repository includes a lightweight local experiment for checking whether rendered
marker context makes unresolved contradictions more visible in responses from
`ollama gemma4:e4b`.

The Ollama experiment is a reproducibility smoke test for marker-aware prompting on
synthetic scenarios. Do not treat the numbers as a general benchmark or compare them
across models without a controlled evaluation design.

Dry-run without Ollama:

```powershell
uv run python experiments/marker_context_effect/run_experiment.py --dry-run --limit 1
```

Local Ollama run, after the model is available on the machine:

```powershell
uv run python experiments/marker_context_effect/run_experiment.py --model gemma4:e4b --limit 2 --trials 1
```

Generate a public summary report from local raw JSONL:

```powershell
uv run python experiments/marker_context_effect/report.py --input experiments/results/marker_context_effect.jsonl --output-md experiments/reports/marker_context_effect.md --output-json experiments/reports/marker_context_effect.summary.json
```

This experiment is a small smoke/proxy evaluation, not a proof of general
effectiveness. The experiment script sends `think=false` to Ollama so `gemma4:e4b`
returns visible response text within the short generation budget. The core package
still has no Ollama, LLM, or network dependency. Raw JSONL under
`experiments/results/` is ignored; publish compact reports under `experiments/reports/`
when sharing results. See
[Marker context effect experiment](experiments/marker_context_effect/README.md).

### v0.1.1 local experiment result

A local run was performed on 2026-05-17 against the v0.1.1 synthetic scenario set
(`scenario_version=1.1.0`, `scoring_version=1.2.1`) with `ollama gemma4:e4b`,
`trials=1`, 8 scenarios, 2 conditions, `temperature=0`, `seed=7`,
`num_predict=256`, and `think=false`. This produced 16 records: 14 conflict records
and 2 non-conflict control records.

Reproduction command:

```powershell
uv run python experiments/marker_context_effect/run_experiment.py --model gemma4:e4b --trials 1 --include-raw --output experiments/results/marker_context_effect_v0.1.1.jsonl --manifest-output experiments/results/marker_context_effect_v0.1.1.manifest.json
```

Public report command:

```powershell
uv run python experiments/marker_context_effect/report.py --input experiments/results/marker_context_effect_v0.1.1.jsonl --output-md experiments/reports/marker_context_effect_v0.1.1.md --output-json experiments/reports/marker_context_effect_v0.1.1.summary.json
```

The primary proxy outcome is `primary_success`, a deterministic scenario-aware
score derived from visible conflict assertion, both conflicting values, both
sources, overwrite avoidance, clarification behavior where requested, and no false
visible-conflict assertion on control records.

Condition-level means:

| condition | primary_success | marker_success | asserts_visible_conflict | mentions_both_values | mentions_sources | avoids_silent_overwrite | false_conflict_on_control |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.38 | 0.00 |
| marker_aware | 1.00 | 0.88 | 0.88 | 0.88 | 0.88 | 1.00 | 0.00 |

These condition-level means include the non-conflict control record. Looking only
at the 7 conflict scenarios, `marker_aware` satisfied the primary outcome in 7/7
cases, while `baseline` satisfied it in 0/7 cases. The control scenario did not
produce a positive visible-conflict assertion under either condition.

Interpretation: in this small fixed scenario set, adding rendered marker context made
`gemma4:e4b` more likely to explicitly mention unresolved contradiction, conflicting
values, and sources while avoiding silent overwrite. The baseline sometimes used
conflict-related terms, but did not name both values and both sources and did not
satisfy the conflict-scenario primary outcome.

This is a lightweight proxy result, not a benchmark and not a validation of CGT as a
whole. It uses one local model, one prompt template, one trial, deterministic
string-matching metrics, and hand-written scenarios. The result supports only the
narrow claim that marker context can make retained contradictions more visible under
these fixed conditions.

Public reports:

- [v0.1.1 Markdown report](experiments/reports/marker_context_effect_v0.1.1.md)
- [v0.1.1 JSON summary](experiments/reports/marker_context_effect_v0.1.1.summary.json)

Raw JSONL and manifests remain under `experiments/results/`, which is ignored and
may include prompts, responses, local file paths, and environment details.

### Public artifact policy

The intended public artifacts are source code, docs, examples, experiment scripts,
scenarios, and compact reports under `experiments/reports/`. Raw experiment outputs
under `experiments/results/` are ignored because they can contain prompt/response
text, local paths, and environment details. The Python wheel contains only the
`cgt_marker` package; the source distribution includes docs, examples, tests,
experiment scripts, scenarios, and compact public reports, but not raw JSONL
results.

## Documentation

- [Concepts](docs/concepts.md): core data types and state transitions.
- [Architecture](docs/architecture.md): module boundaries and loose coupling.
- [Extending](docs/extending.md): custom detectors, stores, and renderers.
- [CGT mapping](docs/cgt-mapping.md): operational mapping from the paper to code.
- [Limitations](docs/limitations.md): honest MVP boundaries and non-goals.
- [API status](docs/api.md): stable, experimental, and reserved API surfaces.

## CGT mapping

This project is inspired by:

Takahashi, K. (2026). *Constraint Generative Theory: Typed Constraint Effects and
Scientific Availability*. Zenodo. https://doi.org/10.5281/zenodo.20254492

The implementation uses only the practical state-layer reading:

- constraint -> claim, detector rule, marker policy, renderer rule
- effect profile -> ledger state: claims, markers, marker status, provenance
- inconsistency policy -> marker policy
- inconsistency effect -> marker
- scientific availability -> reproducible claim/marker log with provenance
- continuation -> downstream execution while unresolved markers remain visible
- report-forgetfulness -> a rendered prompt may omit detail, but the ledger retains it

This package is not an implementation of the full CGT formal system. It borrows the
marker-policy intuition and turns it into a small software component.

## Limitations

- Not a truth oracle. A marker means the configured detectors found a conflict; it
  does not prove which claim is true.
- Not a theorem prover, paraconsistent logic engine, or belief-revision system.
- No natural-language claim extraction. Callers must provide structured `Claim`
  objects.
- No automatic resolution. Markers change status only through explicit calls such as
  `resolve_marker`, `ignore_marker`, or `supersede_marker`.
- No global consistency enforcement. The ledger can contain many unresolved markers.
- Temporal parsing is deliberately narrow and expects normalized ISO date/datetime
  strings. Date-only strings are not compared with datetime strings.
- JSONL storage is a simple append/replay log. It is not a concurrent database.
- Framework adapters are optional helpers, not core dependencies.
- Reserved policy modes are future work and raise on conflict finalization.

## What this is not

- not a paraconsistent logic prover
- not a belief-revision system
- not a replacement for LangGraph, AutoGen, or CrewAI
- not a vector database
- not an LLM memory manager
- not a truth oracle

## Roadmap

- source-conflict and stale-information detectors
- richer evidence rendering
- optional SQLite storage
- TypeScript reference port
- optional framework adapters that remain outside the core dependency set

## License

Apache License 2.0. See `LICENSE`.

## Citation

Takahashi, K. (2026). *Constraint Generative Theory: Typed Constraint Effects and
Scientific Availability*. Zenodo. https://doi.org/10.5281/zenodo.20254492
