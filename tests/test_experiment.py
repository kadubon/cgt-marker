from __future__ import annotations

import json
from pathlib import Path

from experiments.marker_context_effect import report, run_experiment
from experiments.marker_context_effect.score import score_response

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SCENARIO_KEYS = {"id", "title", "report", "claims", "expected"}
REQUIRED_CLAIM_KEYS = {"subject", "predicate", "value", "source"}


def test_scenarios_json_is_valid_and_has_required_fields() -> None:
    scenarios = run_experiment.load_scenarios()
    assert len(scenarios) == 5
    for scenario in scenarios:
        assert set(scenario) >= REQUIRED_SCENARIO_KEYS
        assert isinstance(scenario["claims"], list)
        assert scenario["claims"]
        for claim in scenario["claims"]:
            assert set(claim) >= REQUIRED_CLAIM_KEYS
        expected = scenario["expected"]
        assert isinstance(expected["has_conflict"], bool)
        assert isinstance(expected["values"], list)
        assert isinstance(expected["sources"], list)


def test_prompt_generation_keeps_same_report_and_adds_marker_context_only_when_aware() -> None:
    scenario = run_experiment.load_scenarios()[0]
    baseline = run_experiment.build_prompt(scenario, "baseline")
    marker_aware = run_experiment.build_prompt(scenario, "marker_aware")

    assert baseline["report"] == marker_aware["report"] == scenario["report"]
    assert "Marker context:" not in baseline["prompt"]
    assert "Marker context:" in marker_aware["prompt"]
    assert "Open contradiction markers" in marker_aware["prompt"]
    assert "Open contradiction markers" not in baseline["prompt"]


def test_dry_run_cli_generates_jsonl_without_ollama(tmp_path: Path) -> None:
    output = tmp_path / "dry-run.jsonl"
    manifest = tmp_path / "dry-run.manifest.json"
    exit_code = run_experiment.main(
        [
            "--dry-run",
            "--limit",
            "1",
            "--trials",
            "1",
            "--output",
            str(output),
            "--manifest-output",
            str(manifest),
        ]
    )

    assert exit_code == 0
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    records = [json.loads(line) for line in lines]
    assert {record["condition"] for record in records} == {"baseline", "marker_aware"}
    assert all(record["dry_run"] is True for record in records)
    assert all(record["think"] is False for record in records)
    assert all(record["response"] == "" for record in records)
    for record in records:
        assert record["experiment_name"] == run_experiment.EXPERIMENT_NAME
        assert record["scenario_version"] == run_experiment.SCENARIO_VERSION
        assert record["conditions"] == list(run_experiment.CONDITIONS)
        assert record["expected_has_conflict"] is True
        assert "scoring_version" in record

    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["model"] == run_experiment.DEFAULT_MODEL
    assert manifest_data["scenario_sha256"]
    assert manifest_data["output"] == str(output)


def test_scoring_function_handles_conflict_and_control_outputs() -> None:
    conflict_expected = {
        "has_conflict": True,
        "values": ["2026-06-01", "2026-06-03"],
        "sources": ["email", "calendar"],
    }
    conflict_scores = score_response(
        (
            "There is a conflict: email says 2026-06-01 while calendar says "
            "2026-06-03. Review the sources before proceeding."
        ),
        conflict_expected,
    )
    assert conflict_scores["mentions_conflict"]
    assert conflict_scores["mentions_conflict_term"]
    assert conflict_scores["asserts_visible_conflict"]
    assert conflict_scores["mentions_both_values"]
    assert conflict_scores["mentions_sources"]
    assert conflict_scores["recommends_review"]
    assert not conflict_scores["false_conflict_on_control"]
    assert conflict_scores["marker_success"]

    control_expected = {"has_conflict": False, "values": [], "sources": ["calendar"]}
    control_scores = score_response("Proceed with Room A.", control_expected)
    assert not control_scores["mentions_conflict"]
    assert not control_scores["false_conflict_on_control"]

    false_conflict_scores = score_response("There is a conflict to review.", control_expected)
    assert false_conflict_scores["false_conflict_on_control"]

    negated_scores = score_response(
        "No conflicting values are visible in the provided report.", conflict_expected
    )
    assert negated_scores["mentions_conflict_term"]
    assert not negated_scores["asserts_visible_conflict"]
    assert not negated_scores["mentions_conflict"]
    assert not negated_scores["marker_success"]


def test_report_generator_writes_public_summary_without_raw_text(tmp_path: Path) -> None:
    raw_output = tmp_path / "raw.jsonl"
    manifest = tmp_path / "manifest.json"
    output_md = tmp_path / "summary.md"
    output_json = tmp_path / "summary.json"
    run_experiment.main(
        [
            "--dry-run",
            "--limit",
            "1",
            "--trials",
            "1",
            "--output",
            str(raw_output),
            "--manifest-output",
            str(manifest),
        ]
    )

    exit_code = report.main(
        [
            "--input",
            str(raw_output),
            "--output-md",
            str(output_md),
            "--output-json",
            str(output_json),
        ]
    )

    assert exit_code == 0
    markdown = output_md.read_text(encoding="utf-8")
    summary = json.loads(output_json.read_text(encoding="utf-8"))
    assert "Condition-Level Means" in markdown
    assert "Interpretation Boundaries" in markdown
    assert "Report projection:" not in markdown
    assert "prompt" not in summary
    assert "response" not in summary
    assert summary["record_count"] == 2
    assert summary["conflict_record_count"] == 2
    assert summary["control_record_count"] == 0
    assert summary["unknown_expected_record_count"] == 0
    assert summary["primary_outcome"].startswith("marker_success")
    assert "no control records" in " ".join(summary["limitations"])


def test_readme_links_experiment_docs() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "experiments/marker_context_effect/README.md" in readme
    assert "experiments/marker_context_effect/report.py" in readme


def test_docs_explain_raw_data_policy_and_results_ignore() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "experiments/results/" in gitignore

    experiment_readme = (
        ROOT / "experiments" / "marker_context_effect" / "README.md"
    ).read_text(encoding="utf-8")
    assert "Raw JSONL" in experiment_readme
    assert "experiments/results/" in experiment_readme
    assert "experiments/reports/" in experiment_readme
    assert "marker_success" in experiment_readme
    assert "control records" in experiment_readme

    limitations = (ROOT / "docs" / "limitations.md").read_text(encoding="utf-8")
    assert "experiments/results/" in limitations
    assert "experiments/reports/" in limitations


def test_core_package_remains_ollama_free() -> None:
    for path in (ROOT / "src" / "cgt_marker").rglob("*.py"):
        assert "ollama" not in path.read_text(encoding="utf-8").casefold()
