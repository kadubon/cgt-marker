# Marker Context Effect Report

This report summarizes a lightweight local proxy experiment. It is not a general benchmark and does not validate CGT as a whole.

## Run Metadata

- Experiment: `marker_context_effect`
- Model: `gemma4:e4b`
- Options: `{"num_predict": 256, "seed": 7, "temperature": 0}`
- think: `False`
- Scoring version: `1.1.0`
- Scenario version: `1.0.0`
- Timestamp range: `2026-05-17T10:26:17.887929+00:00` to `2026-05-17T10:26:44.037555+00:00`
- Scenarios: `2`
- Trials: `1`
- Conditions: `2`
- Records: `4`
- Conflict records: `4`
- Control records: `0`
- Unknown expected-label records: `0`

## Condition-Level Means

| condition | marker_success | asserts_visible_conflict | mentions_both_values | mentions_sources | recommends_review | false_conflict_on_control |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.00 | 0.00 | 0.00 | 0.00 | 0.50 | 0.00 |
| marker_aware | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |

## Scenario-Level Compact Table

| scenario | condition | n | marker_success | asserts_visible_conflict | mentions_both_values | mentions_sources |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| deadline_date_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 |
| deadline_date_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 |
| release_status_conflict | baseline | 1 | 0.00 | 0.00 | 0.00 | 0.00 |
| release_status_conflict | marker_aware | 1 | 1.00 | 1.00 | 1.00 | 1.00 |

## Interpretation Boundaries

- This is a lightweight proxy evaluation, not a benchmark.
- String-matching scores can miss semantically correct answers and can count wording artifacts.
- The result evaluates rendered marker context under fixed scenarios, not CGT as a whole.
- This run contains no control records, so false_conflict_on_control is reported but not empirically evaluated here.
- Raw prompts and responses are intentionally excluded from this public summary.

Raw prompts and responses are not included here. Keep raw JSONL under `experiments/results/` for local inspection only.
