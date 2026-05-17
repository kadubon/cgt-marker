# Marker Context Effect Experiment

This is a lightweight local experiment for `cgt-marker`.

## Question

When a normal report projection hides a contradiction, does adding
`ledger.render_marker_context()` make `ollama gemma4:e4b` more likely to mention the
unresolved contradiction, conflicting values, and sources?

This is a smoke/proxy evaluation. It is not evidence that `cgt-marker` improves all
agents, all models, or all tasks.

## Conditions

- `baseline`: the model receives only the report projection.
- `marker_aware`: the model receives the same report projection plus rendered marker
  context from `cgt-marker`.

## Metrics

Scoring is deterministic string matching:

- `mentions_conflict_term`
- `asserts_visible_conflict`
- `mentions_conflict`, retained as a compatibility alias for
  `asserts_visible_conflict`
- `mentions_both_values`
- `mentions_sources`
- `recommends_review`
- `false_conflict_on_control`
- `marker_success`, the primary proxy outcome for conflict scenarios:
  `asserts_visible_conflict AND mentions_both_values AND mentions_sources`

These metrics are intentionally simple and should be treated as inspection aids, not
as a benchmark. The scorer separates raw conflict-term mentions from visible conflict
assertions so phrases such as "No conflicting values are visible" do not count as
positive conflict detection.

## Run

Dry-run without Ollama:

```powershell
uv run python experiments/marker_context_effect/run_experiment.py --dry-run --limit 1
```

Local Ollama run:

```powershell
uv run python experiments/marker_context_effect/run_experiment.py --model gemma4:e4b --limit 2 --trials 1
```

The script sends `think=false` to Ollama by default. This keeps `gemma4:e4b` from
spending the short `num_predict` budget on hidden thinking tokens and returning an
empty `response`.

The script writes JSONL results to `experiments/results/`, which is ignored by the
repository.

The core package does not import Ollama or make network calls. Only this experiment
script calls the local Ollama HTTP API.

## Raw and public artifacts

Raw JSONL under `experiments/results/` contains prompts, responses, ledger snapshots,
and timestamps. Treat it as local inspection data and do not publish it by default.

For public-facing results, generate compact reports:

```powershell
uv run python experiments/marker_context_effect/report.py --input experiments/results/marker_context_effect.jsonl --output-md experiments/reports/marker_context_effect.md --output-json experiments/reports/marker_context_effect.summary.json
```

The summary report includes model/options, timestamp range, scenario/trial counts,
condition-level means, scenario-level compact metrics, and interpretation limits. It
does not include raw prompt or response text.

If a smoke run uses `--limit`, the public report states how many conflict and
non-conflict control records were actually included. Do not interpret
`false_conflict_on_control` as evaluated unless the report includes control records.

## Reproducibility notes

`run_experiment.py` writes a manifest next to the raw JSONL by default. The manifest
records model name, Ollama URL, generation options, `think`, trial count, scenario
file hash, scenario version, and scoring version.

Because local model builds and hardware can affect generation, report any Ollama
version and model details you used when publishing results.
