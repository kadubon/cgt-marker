# Marker Context Effect Report

This report summarizes a lightweight local proxy experiment. It is not a general benchmark and does not validate CGT as a whole.

## Run Metadata

- Experiment: `marker_context_effect`
- Model: `gemma4:e4b`
- Options: `{"num_predict": 256, "seed": 7, "temperature": 0}`
- think: `False`
- Scoring version: `1.1.0`
- Scenario version: `1.0.0`
- Timestamp range: `2026-05-17T10:29:43.263419+00:00` to `2026-05-17T10:30:51.688546+00:00`
- Scenarios: `5`
- Trials: `1`
- Conditions: `2`
- Records: `10`
- Conflict records: `8`
- Control records: `2`
- Unknown expected-label records: `0`

## Condition-Level Means

| condition | marker_success | asserts_visible_conflict | mentions_both_values | mentions_sources | recommends_review | false_conflict_on_control |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.00 | 0.40 | 0.00 | 0.00 | 0.60 | 0.00 |
| marker_aware | 0.80 | 0.80 | 0.80 | 0.80 | 0.80 | 0.00 |

## Scenario-Level Compact Table

| scenario | condition | n | marker_success | asserts_visible_conflict | mentions_both_values | mentions_sources |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| budget_interval_conflict | baseline | 1 | 0.00 | 1.00 | 0.00 | 0.00 |
| budget_interval_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| deadline_date_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadline_date_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| meeting_date_conflict | baseline | 1 | 0.00 | 1.00 | 0.00 | 0.00 |
| meeting_date_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| non_conflict_control | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 |
| non_conflict_control | marker_aware | 1 | 0.00 | 0.00 | 0.00 | 0.00 |
| release_status_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 |
| release_status_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 |

## Interpretation Boundaries

- This is a lightweight proxy evaluation, not a benchmark.
- String-matching scores can miss semantically correct answers and can count wording artifacts.
- The result evaluates rendered marker context under fixed scenarios, not CGT as a whole.
- false_conflict_on_control should be interpreted only over the included control records, not over conflict scenarios.
- Raw prompts and responses are intentionally excluded from this public summary.

Raw prompts and responses are not included here. Keep raw JSONL under `experiments/results/` for local inspection only.
