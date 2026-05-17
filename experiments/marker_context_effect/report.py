from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

METRICS = (
    "mentions_conflict",
    "mentions_conflict_term",
    "asserts_visible_conflict",
    "mentions_both_values",
    "mentions_sources",
    "recommends_review",
    "false_conflict_on_control",
    "marker_success",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load raw experiment records from JSONL."""

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def summarize_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a compact public summary without raw prompts or responses."""

    if not records:
        raise ValueError("No records to summarize.")

    timestamps = sorted(str(record["timestamp"]) for record in records)
    conditions = sorted({str(record["condition"]) for record in records})
    scenarios = sorted({str(record["scenario_id"]) for record in records})
    trials = sorted({int(record["trial"]) for record in records})

    condition_summary = _mean_scores(records, key_field="condition")
    scenario_condition_summary = _scenario_condition_scores(records)
    expected_counts = _expected_conflict_counts(records)
    first = records[0]

    return {
        "experiment_name": first.get("experiment_name", "marker_context_effect"),
        "model": first.get("model"),
        "options": first.get("options"),
        "think": first.get("think"),
        "scoring_version": first.get("scoring_version"),
        "scenario_version": first.get("scenario_version"),
        "timestamp_start": timestamps[0],
        "timestamp_end": timestamps[-1],
        "scenario_count": len(scenarios),
        "trial_count": len(trials),
        "condition_count": len(conditions),
        "record_count": len(records),
        **expected_counts,
        "conditions": conditions,
        "metrics": list(METRICS),
        "condition_summary": condition_summary,
        "scenario_condition_summary": scenario_condition_summary,
        "primary_outcome": (
            "marker_success = conflict scenario AND asserts_visible_conflict "
            "AND mentions_both_values AND mentions_sources"
        ),
        "limitations": [
            "This is a lightweight proxy evaluation, not a benchmark.",
            (
                "String-matching scores can miss semantically correct answers and can "
                "count wording artifacts."
            ),
            (
                "The result evaluates rendered marker context under fixed scenarios, "
                "not CGT as a whole."
            ),
            _control_limitation_note(expected_counts),
            "Raw prompts and responses are intentionally excluded from this public summary.",
        ],
    }


def write_markdown(summary: Mapping[str, Any], path: Path) -> None:
    """Write a compact Markdown report."""

    lines = [
        "# Marker Context Effect Report",
        "",
        "This report summarizes a lightweight local proxy experiment. It is not a "
        "general benchmark and does not validate CGT as a whole.",
        "",
        "## Run Metadata",
        "",
        f"- Experiment: `{summary['experiment_name']}`",
        f"- Model: `{summary['model']}`",
        f"- Options: `{json.dumps(summary['options'], sort_keys=True)}`",
        f"- think: `{summary['think']}`",
        f"- Scoring version: `{summary['scoring_version']}`",
        f"- Scenario version: `{summary['scenario_version']}`",
        f"- Timestamp range: `{summary['timestamp_start']}` to `{summary['timestamp_end']}`",
        f"- Scenarios: `{summary['scenario_count']}`",
        f"- Trials: `{summary['trial_count']}`",
        f"- Conditions: `{summary['condition_count']}`",
        f"- Records: `{summary['record_count']}`",
        f"- Conflict records: `{summary['conflict_record_count']}`",
        f"- Control records: `{summary['control_record_count']}`",
        f"- Unknown expected-label records: `{summary['unknown_expected_record_count']}`",
        "",
        "## Condition-Level Means",
        "",
        "| condition | marker_success | asserts_visible_conflict | mentions_both_values | "
        "mentions_sources | recommends_review | false_conflict_on_control |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    condition_summary = summary["condition_summary"]
    for condition, scores in sorted(condition_summary.items()):
        lines.append(
            f"| {condition} | {_fmt(scores.get('marker_success'))} | "
            f"{_fmt(scores.get('asserts_visible_conflict'))} | "
            f"{_fmt(scores.get('mentions_both_values'))} | "
            f"{_fmt(scores.get('mentions_sources'))} | "
            f"{_fmt(scores.get('recommends_review'))} | "
            f"{_fmt(scores.get('false_conflict_on_control'))} |"
        )

    lines.extend(
        [
            "",
            "## Scenario-Level Compact Table",
            "",
            "| scenario | condition | n | marker_success | asserts_visible_conflict | "
            "mentions_both_values | mentions_sources |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for row in summary["scenario_condition_summary"]:
        lines.append(
            f"| {row['scenario_id']} | {row['condition']} | {row['n']} | "
            f"{_fmt(row.get('marker_success'))} | "
            f"{_fmt(row.get('asserts_visible_conflict'))} | "
            f"{_fmt(row.get('mentions_both_values'))} | "
            f"{_fmt(row.get('mentions_sources'))} |"
        )

    lines.extend(["", "## Interpretation Boundaries", ""])
    lines.extend(f"- {item}" for item in summary["limitations"])
    lines.extend(
        [
            "",
            "Raw prompts and responses are not included here. Keep raw JSONL under "
            "`experiments/results/` for local inspection only.",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_json(summary: Mapping[str, Any], path: Path) -> None:
    """Write a compact machine-readable summary."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mean_scores(
    records: Sequence[Mapping[str, Any]],
    *,
    key_field: str,
) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        key = str(record[key_field])
        counts[key] += 1
        scores = record.get("scores", {})
        if not isinstance(scores, Mapping):
            continue
        for metric in METRICS:
            totals[key][metric] += int(bool(scores.get(metric, False)))
    return {
        key: {metric: totals[key][metric] / counts[key] for metric in METRICS}
        for key in sorted(counts)
    }


def _scenario_condition_scores(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(str(record["scenario_id"]), str(record["condition"]))].append(record)

    rows: list[dict[str, Any]] = []
    for (scenario_id, condition), group in sorted(grouped.items()):
        means = _mean_scores(group, key_field="condition")[condition]
        rows.append({"scenario_id": scenario_id, "condition": condition, "n": len(group), **means})
    return rows


def _expected_conflict_counts(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    conflict_count = 0
    control_count = 0
    unknown_count = 0
    for record in records:
        value = record.get("expected_has_conflict")
        if value is True:
            conflict_count += 1
        elif value is False:
            control_count += 1
        else:
            unknown_count += 1
    return {
        "conflict_record_count": conflict_count,
        "control_record_count": control_count,
        "unknown_expected_record_count": unknown_count,
    }


def _control_limitation_note(expected_counts: Mapping[str, int]) -> str:
    if expected_counts["control_record_count"] == 0:
        return (
            "This run contains no control records, so false_conflict_on_control is "
            "reported but not empirically evaluated here."
        )
    return (
        "false_conflict_on_control should be interpreted only over the included "
        "control records, not over conflict scenarios."
    )


def _fmt(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int | float):
        return f"{float(value):.2f}"
    return str(value)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build public summary reports from raw JSONL.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    summary = summarize_records(load_jsonl(args.input))
    write_markdown(summary, args.output_md)
    write_json(summary, args.output_json)
    print(f"Wrote Markdown report to {args.output_md}")
    print(f"Wrote JSON summary to {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
