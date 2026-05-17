# Marker Context Effect Report

This report summarizes a lightweight local proxy experiment. It is not a general benchmark and does not validate CGT as a whole.

## Run Metadata

- Experiment: `marker_context_effect`
- Model: `gemma4:e4b`
- Options: `{"num_predict": 256, "seed": 7, "temperature": 0}`
- think: `False`
- Scoring version: `1.2.1`
- Scenario version: `1.1.0`
- Timestamp range: `2026-05-17T11:05:39.023266+00:00` to `2026-05-17T11:07:34.699430+00:00`
- Scenarios: `8`
- Trials: `1`
- Conditions: `2`
- Records: `16`
- Conflict records: `14`
- Control records: `2`
- Unknown expected-label records: `0`

## Condition-Level Means

| condition | primary_success | marker_success | asserts_visible_conflict | mentions_both_values | mentions_sources | avoids_silent_overwrite | asks_for_clarification_when_needed | false_conflict_on_control |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.38 | 0.12 | 0.00 |
| marker_aware | 1.00 | 0.88 | 0.88 | 0.88 | 0.88 | 1.00 | 0.12 | 0.00 |

## Scenario-Level Compact Table

| scenario | condition | n | primary_success | marker_success | asserts_visible_conflict | mentions_both_values | mentions_sources |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ambiguous_owner_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ambiguous_owner_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| budget_interval_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| budget_interval_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| deadline_date_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadline_date_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| non_conflict_control | baseline | 1 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| non_conflict_control | marker_aware | 1 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| policy_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| policy_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| release_status_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| release_status_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| source_claim_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| source_claim_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| stale_newer_claim_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| stale_newer_claim_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

## Interpretation Boundaries

- This is a lightweight proxy evaluation, not a benchmark.
- String-matching scores can miss semantically correct answers and can count wording artifacts.
- The result evaluates rendered marker context under fixed scenarios, not CGT as a whole.
- false_conflict_on_control should be interpreted only over the included control records, not over conflict scenarios.
- Raw prompts and responses are intentionally excluded from this public summary.

Raw prompts and responses are not included here. Keep raw JSONL under `experiments/results/` for local inspection only.
