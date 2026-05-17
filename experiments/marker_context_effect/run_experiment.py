from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from cgt_marker import Claim, CounterIdGenerator, FrozenClock, MarkerLedger

EXPERIMENT_NAME = "marker_context_effect"
SCENARIO_VERSION = "1.1.0"
DEFAULT_MODEL = "gemma4:e4b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OPTIONS: dict[str, int | float] = {
    "temperature": 0,
    "seed": 7,
    "num_predict": 256,
}
DEFAULT_THINK = False

EXPERIMENT_DIR = Path(__file__).resolve().parent
if __package__ in {None, ""}:
    sys.path.insert(0, str(EXPERIMENT_DIR.parents[1]))

from experiments.marker_context_effect.score import SCORING_VERSION, score_response  # noqa: E402

SCENARIOS_PATH = EXPERIMENT_DIR / "scenarios.json"
DEFAULT_OUTPUT = EXPERIMENT_DIR.parent / "results" / "marker_context_effect.jsonl"
DEFAULT_MANIFEST_OUTPUT = EXPERIMENT_DIR.parent / "results" / "marker_context_effect.manifest.json"
CONDITIONS = ("baseline", "marker_aware")


def load_scenarios(path: Path = SCENARIOS_PATH) -> list[dict[str, Any]]:
    """Load experiment scenarios from JSON."""

    return cast(list[dict[str, Any]], json.loads(path.read_text(encoding="utf-8")))


def build_ledger(scenario: Mapping[str, Any]) -> MarkerLedger:
    """Build a deterministic ledger for one scenario."""

    ledger = MarkerLedger.default(
        id_generator=CounterIdGenerator(),
        clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    for raw_claim in scenario["claims"]:
        claim = Claim(
            subject=str(raw_claim["subject"]),
            predicate=str(raw_claim["predicate"]),
            value=raw_claim["value"],
            source=str(raw_claim["source"]),
            metadata=dict(raw_claim.get("metadata", {})),
        )
        ledger.add_claim(claim)
    return ledger


def build_prompt(scenario: Mapping[str, Any], condition: str) -> dict[str, Any]:
    """Build one baseline or marker-aware prompt without calling an LLM."""

    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")

    ledger = build_ledger(scenario)
    report = str(scenario["report"])
    sections = [
        "You are assisting a long-running agent.",
        "Use only the report projection and explicitly provided marker context.",
        "",
        "Report projection:",
        report,
    ]
    if condition == "marker_aware":
        sections.extend(["", "Marker context:", ledger.render_marker_context()])

    sections.extend(
        [
            "",
            "Task:",
            (
                "In 2-4 sentences, state the next operational step. If unresolved "
                "contradictions are visible, name the conflicting values and sources. "
                "If none are visible, do not invent one."
            ),
        ]
    )
    return {
        "condition": condition,
        "scenario_id": scenario["id"],
        "prompt": "\n".join(sections),
        "ledger_state": ledger.export_state(),
        "marker_context": ledger.render_marker_context(),
        "report": report,
    }


def call_ollama(
    *,
    prompt: str,
    model: str,
    ollama_url: str,
    options: Mapping[str, int | float],
    think: bool,
    timeout: int,
) -> str:
    """Call Ollama's local generate API using only the Python standard library."""

    from urllib import request

    endpoint = f"{ollama_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": think,
        "options": dict(options),
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return str(body.get("response", ""))


def run_records(
    scenarios: Sequence[Mapping[str, Any]],
    *,
    model: str,
    ollama_url: str,
    options: Mapping[str, int | float],
    think: bool,
    trials: int,
    dry_run: bool,
    include_raw: bool,
    timeout: int,
) -> list[dict[str, Any]]:
    """Generate prompts, optionally call Ollama, and return JSONL-ready records."""

    records: list[dict[str, Any]] = []
    for scenario in scenarios:
        expected = scenario["expected"]
        expected_has_conflict = bool(expected.get("has_conflict", False))
        for trial in range(1, trials + 1):
            for condition in CONDITIONS:
                prompt_record = build_prompt(scenario, condition)
                response = ""
                if not dry_run:
                    print(
                        (
                            f"Running scenario={scenario['id']} trial={trial} "
                            f"condition={condition}"
                        ),
                        file=sys.stderr,
                        flush=True,
                    )
                    response = call_ollama(
                        prompt=prompt_record["prompt"],
                        model=model,
                        ollama_url=ollama_url,
                        options=options,
                        think=think,
                        timeout=timeout,
                    )
                prompt = str(prompt_record["prompt"])
                record = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "experiment_name": EXPERIMENT_NAME,
                    "scenario_version": SCENARIO_VERSION,
                    "conditions": list(CONDITIONS),
                    "scoring_version": SCORING_VERSION,
                    "scenario_id": scenario["id"],
                    "scenario_type": scenario.get("scenario_type"),
                    "expected_has_conflict": expected_has_conflict,
                    "condition": condition,
                    "trial": trial,
                    "model": model,
                    "options": dict(options),
                    "think": think,
                    "dry_run": dry_run,
                    "include_raw": include_raw,
                    "prompt_hash": hash_text(prompt),
                    "response_hash": hash_text(response),
                    "response_length": len(response),
                    "scores": score_response(response, expected),
                }
                if include_raw:
                    record.update(
                        {
                            "report": prompt_record["report"],
                            "marker_context": prompt_record["marker_context"],
                            "ledger_state": prompt_record["ledger_state"],
                            "prompt": prompt,
                            "raw_response": response,
                        }
                    )
                records.append(record)
    return records


def write_jsonl(records: Sequence[Mapping[str, Any]], path: Path) -> None:
    """Write experiment records to JSONL."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def write_manifest(manifest: Mapping[str, Any], path: Path) -> None:
    """Write a JSON manifest for reproducing a run."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def hash_text(value: str) -> str:
    """Return a stable SHA-256 hex digest for prompt/response tracking."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_manifest(args: argparse.Namespace, raw_argv: Sequence[str]) -> dict[str, Any]:
    """Build reproducibility metadata without depending on external CLI tools."""

    scenario_hash = hashlib.sha256(SCENARIOS_PATH.read_bytes()).hexdigest()
    return {
        "experiment_name": EXPERIMENT_NAME,
        "generated_at": datetime.now(UTC).isoformat(),
        "command": ["run_experiment.py", *raw_argv],
        "model": args.model,
        "ollama_url": args.ollama_url,
        "options": dict(DEFAULT_OPTIONS),
        "think": DEFAULT_THINK,
        "timeout": args.timeout,
        "dry_run": args.dry_run,
        "include_raw": args.include_raw,
        "limit": args.limit,
        "trials": args.trials,
        "conditions": list(CONDITIONS),
        "scenario_version": SCENARIO_VERSION,
        "scenario_path": str(SCENARIOS_PATH),
        "scenario_sha256": scenario_hash,
        "scoring_version": SCORING_VERSION,
        "output": str(args.output),
        "python_version": sys.version,
        "notes": (
            "Raw prompt/response JSONL is intended for local inspection. Publish compact "
            "summary reports instead of raw experiment output."
        ),
    }


def summarize(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    """Return condition-level mean scores."""

    totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        condition = str(record["condition"])
        counts[condition] += 1
        scores = record["scores"]
        if not isinstance(scores, Mapping):
            continue
        for key, value in scores.items():
            totals[condition][str(key)] += int(bool(value))

    return {
        condition: {
            metric: value / counts[condition]
            for metric, value in sorted(metrics.items())
        }
        for condition, metrics in sorted(totals.items())
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate whether cgt-marker context makes contradictions visible."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST_OUTPUT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-raw", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else list(argv)
    args = parse_args(raw_argv)
    scenarios = load_scenarios()
    if args.limit is not None:
        scenarios = scenarios[: args.limit]
    records = run_records(
        scenarios,
        model=args.model,
        ollama_url=args.ollama_url,
        options=DEFAULT_OPTIONS,
        think=DEFAULT_THINK,
        trials=args.trials,
        dry_run=args.dry_run,
        include_raw=args.include_raw,
        timeout=args.timeout,
    )
    write_jsonl(records, args.output)
    write_manifest(build_manifest(args, raw_argv), args.manifest_output)
    print(json.dumps(summarize(records), indent=2, sort_keys=True))
    print(f"Wrote {len(records)} records to {args.output}")
    print(f"Wrote manifest to {args.manifest_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
