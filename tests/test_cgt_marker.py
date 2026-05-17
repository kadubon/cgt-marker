from __future__ import annotations

import importlib
import runpy
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cgt_marker import (
    Claim,
    CounterIdGenerator,
    EvidenceRef,
    ExactSlotConflictDetector,
    FrozenClock,
    Marker,
    MarkerDraft,
    MarkerKind,
    MarkerLedger,
    MarkerPolicy,
    MarkerStatus,
    ValidationIssue,
    is_json_value,
    validate_claim,
)
from cgt_marker.adapters.langgraph import add_claims_to_state, render_marker_context_from_state
from cgt_marker.storage import JsonlStore

ROOT = Path(__file__).resolve().parents[1]
DOC_FILES = {
    "concepts.md",
    "architecture.md",
    "extending.md",
    "cgt-mapping.md",
    "limitations.md",
    "api.md",
}


def ledger(policy: MarkerPolicy = MarkerPolicy.MARK_ONLY) -> MarkerLedger:
    return MarkerLedger.default(
        policy=policy,
        id_generator=CounterIdGenerator(),
        clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)),
    )


def test_adding_single_claim_creates_no_marker() -> None:
    state = ledger()
    result = state.add_claim(Claim("meeting.date", "equals", "2026-06-01", "email"))
    assert result.markers == ()
    assert state.open_markers() == []


def test_conflicting_equals_claim_creates_one_open_marker() -> None:
    state = ledger()
    state.add_claim(Claim("meeting.date", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("meeting.date", "equals", "2026-06-03", "calendar"))
    markers = state.open_markers()
    assert len(markers) == 1
    assert markers[0].kind is MarkerKind.CONTRADICTION
    assert markers[0].status is MarkerStatus.OPEN


def test_non_conflicting_claim_creates_no_marker() -> None:
    state = ledger()
    state.add_claim(Claim("meeting.date", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("meeting.room", "equals", "A", "calendar"))
    assert state.open_markers() == []


def test_status_conflicts_are_detected() -> None:
    state = ledger()
    state.add_claim(Claim("task", "status", "done", "tracker"))
    state.add_claim(Claim("task", "status", "not_done", "chat"))
    assert len(state.open_markers()) == 1
    assert set(state.open_markers()[0].dimensions) == {"status", "value"}


def test_temporal_conflicts_are_detected_for_normalized_dates() -> None:
    state = ledger()
    state.add_claim(Claim("deadline", "date", "2026-06-01", "email"))
    state.add_claim(Claim("deadline", "date", "2026-06-03", "ticket"))
    assert len(state.open_markers()) == 1
    assert state.open_markers()[0].dimensions == ("temporal",)


def test_numeric_interval_conflict_is_detected() -> None:
    state = ledger()
    state.add_claim(Claim("budget", "lte", 100, "finance-a"))
    state.add_claim(Claim("budget", "gte", 200, "finance-b"))
    assert len(state.open_markers()) == 1
    assert state.open_markers()[0].dimensions == ("numeric_interval",)


def test_mark_only_policy_does_not_delete_claims() -> None:
    state = ledger()
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    assert len(state.list_claims()) == 2
    assert len(state.open_markers()) == 1


def test_require_review_policy_marks_review_metadata() -> None:
    state = ledger(MarkerPolicy.REQUIRE_REVIEW)
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    result = state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    assert result.requires_review
    assert state.open_markers()[0].metadata["requires_review"] is True


def test_block_action_policy_reports_block_without_deleting_data() -> None:
    state = ledger(MarkerPolicy.BLOCK_ACTION)
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    result = state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    assert result.blocked
    assert len(state.list_claims()) == 2
    assert state.open_markers()[0].metadata["blocked"] is True


def test_open_markers_returns_only_open_markers() -> None:
    state = ledger()
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    marker_id = state.open_markers()[0].id
    state.resolve_marker(marker_id)
    assert state.open_markers() == []
    assert state.list_markers()[0].status is MarkerStatus.RESOLVED


def test_marker_status_helpers() -> None:
    ignored = ledger()
    ignored.add_claim(Claim("x", "equals", 1, "a"))
    ignored.add_claim(Claim("x", "equals", 2, "b"))
    ignored.ignore_marker(ignored.open_markers()[0].id)
    assert ignored.list_markers()[0].status is MarkerStatus.IGNORED

    superseded = ledger()
    superseded.add_claim(Claim("x", "equals", 1, "a"))
    superseded.add_claim(Claim("x", "equals", 2, "b"))
    superseded.supersede_marker(superseded.open_markers()[0].id)
    assert superseded.list_markers()[0].status is MarkerStatus.SUPERSEDED


def test_claim_json_roundtrip() -> None:
    claim = Claim("deadline", "equals", "2026-06-01", "email", id="C-001")
    assert Claim.from_json(claim.to_json()) == claim


def test_marker_json_roundtrip() -> None:
    marker = Marker(
        id="M-001",
        kind=MarkerKind.CONTRADICTION,
        status=MarkerStatus.OPEN,
        subject="deadline",
        predicate="equals",
        claim_ids=("C-001", "C-002"),
        message="deadline equals conflict",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert Marker.from_json(marker.to_json()) == marker


def test_ledger_export_import_roundtrip() -> None:
    state = ledger()
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    restored = MarkerLedger.from_state(
        state.export_state(),
        id_generator=CounterIdGenerator(),
        clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    assert restored.export_state() == state.export_state()


def test_jsonl_store_save_load(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "ledger.jsonl"
    state = ledger()
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    state.save_jsonl(path)

    store = JsonlStore(path)
    assert len(store.list_claims()) == 2
    assert len(store.list_markers()) == 1


def test_jsonl_store_replay_keeps_latest_marker_status(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "ledger.jsonl"
    store = JsonlStore(path)
    state = MarkerLedger.default(
        store=store,
        id_generator=CounterIdGenerator(),
        clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    marker_id = state.open_markers()[0].id
    state.resolve_marker(marker_id)

    reloaded = JsonlStore(path)
    assert reloaded.list_markers()[0].id == marker_id
    assert reloaded.list_markers()[0].status is MarkerStatus.RESOLVED


def test_prompt_renderer_includes_unresolved_markers() -> None:
    state = ledger()
    state.add_claim(Claim("deadline", "equals", "2026-06-01", "email"))
    state.add_claim(Claim("deadline", "equals", "2026-06-03", "ticket"))
    rendered = state.render_marker_context()
    assert "Open contradiction markers" in rendered
    assert "deadline equals" in rendered
    assert "email, ticket" in rendered


def test_langgraph_adapter_import_is_safe_without_langgraph_installed() -> None:
    module = importlib.import_module("cgt_marker.adapters.langgraph")
    assert hasattr(module, "add_claims_to_state")


def test_dict_state_helper_adds_claims_and_preserves_markers() -> None:
    state: dict[str, object] = {}
    state = add_claims_to_state(
        state,
        [
            Claim("release.status", "status", "approved", "review"),
            Claim("release.status", "status", "rejected", "qa"),
        ],
    )
    assert len(state["cgt_marker"]["claims"]) == 2  # type: ignore[index]
    assert len(state["cgt_marker"]["markers"]) == 1  # type: ignore[index]
    assert "release.status" in render_marker_context_from_state(state)


def test_dict_state_helper_accepts_custom_ledger_factory() -> None:
    def factory(serialized: dict[str, object]) -> MarkerLedger:
        custom = MarkerLedger(
            detectors=[ExactSlotConflictDetector(predicates=frozenset({"equals"}))],
            policy=MarkerPolicy.REQUIRE_REVIEW,
            id_generator=CounterIdGenerator(),
            clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)),
        )
        custom.import_state(serialized)
        return custom

    state = add_claims_to_state(
        {},
        [Claim("x", "equals", "a", "left"), Claim("x", "equals", "b", "right")],
        ledger_factory=factory,
    )
    marker = state["cgt_marker"]["markers"][0]  # type: ignore[index]
    assert marker["metadata"]["requires_review"] is True
    assert "x equals" in render_marker_context_from_state(state, ledger_factory=factory)


def test_cgt_principle_contradiction_is_not_failure() -> None:
    state = ledger()
    first = state.add_claim(Claim("claim", "equals", "A", "source-a"))
    second = state.add_claim(Claim("claim", "equals", "B", "source-b"))
    state.add_claim(Claim("other", "equals", "C", "source-c"))

    assert not first.blocked
    assert not second.blocked
    assert len(state.list_claims()) == 3
    assert len(state.open_markers()) == 1
    assert state.open_markers()[0].claim_ids == ("C-001", "C-002")


def test_notice_file_is_absent_and_readme_does_not_reference_notice() -> None:
    assert not (ROOT / "NOTICE").exists()
    assert "NOTICE" not in (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_links_every_docs_file() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for filename in DOC_FILES:
        assert f"docs/{filename}" in readme


def test_docs_do_not_reference_removed_notice_file() -> None:
    for path in (ROOT / "docs").glob("*.md"):
        assert "NOTICE" not in path.read_text(encoding="utf-8")


def test_docs_explain_supported_reserved_policies_and_limitations() -> None:
    api = (ROOT / "docs" / "api.md").read_text(encoding="utf-8")
    assert "Supported Policies" in api
    assert "Reserved Policies" in api
    for policy in ("MARK_ONLY", "REQUIRE_REVIEW", "BLOCK_ACTION", "QUARANTINE"):
        assert policy in api
    for policy in ("BRANCH_CONTEXT", "WEIGHTED_CONTINUE"):
        assert policy in api
    assert "NotImplementedError" in api

    limitations = (ROOT / "docs" / "limitations.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "truth oracle",
        "theorem prover",
        "belief-revision",
        "natural language",
        "jsonl storage",
        "reserved policy",
    ):
        assert phrase in limitations


def test_examples_run_from_files() -> None:
    for filename in ("basic_ledger.py", "marker_aware_prompt.py", "langgraph_like_state.py"):
        runpy.run_path(str(ROOT / "examples" / filename), run_name="__main__")


def test_public_package_exports_stable_mvp_surface() -> None:
    module = importlib.import_module("cgt_marker")
    for name in (
        "Claim",
        "EvidenceRef",
        "Marker",
        "MarkerDraft",
        "MarkerLedger",
        "MarkerPolicy",
        "PolicyResult",
        "ExactSlotConflictDetector",
        "StatusConflictDetector",
        "TemporalConflictDetector",
        "NumericIntervalConflictDetector",
        "InMemoryStore",
        "JsonlStore",
        "MarkdownRenderer",
        "PromptContextRenderer",
        "ValidationIssue",
        "is_json_value",
        "validate_claim",
    ):
        assert name in module.__all__


def test_reserved_policy_modes_raise_on_conflict_without_silent_fallback() -> None:
    for policy in (MarkerPolicy.BRANCH_CONTEXT, MarkerPolicy.WEIGHTED_CONTINUE):
        state = ledger(policy)
        state.add_claim(Claim("release.status", "status", "approved", "review"))
        with pytest.raises(NotImplementedError):
            state.add_claim(Claim("release.status", "status", "rejected", "qa"))
        assert len(state.list_claims()) == 1
        assert state.list_markers() == []


def test_marker_evidence_preserves_source_quote_and_uri() -> None:
    state = ledger()
    state.add_claim(
        Claim(
            "deadline",
            "equals",
            "june-first",
            "email",
            metadata={"quote": "The deadline is June 1.", "uri": "mail://message/123"},
        )
    )
    state.add_claim(
        Claim(
            "deadline",
            "equals",
            "june-third",
            "ticket",
            metadata={"quote": "The deadline is June 3.", "uri": "ticket://issue/456"},
        )
    )

    marker = state.open_markers()[0]
    assert [evidence.source for evidence in marker.evidence] == ["email", "ticket"]
    assert marker.evidence[0].quote == "The deadline is June 1."
    assert marker.evidence[0].uri == "mail://message/123"
    assert marker.evidence[1].quote == "The deadline is June 3."
    assert marker.evidence[1].uri == "ticket://issue/456"
    assert "sources: email, ticket" in state.render_marker_context()


class _DimensionDetector:
    def __init__(self, name: str, dimension: str, severity: float, confidence: float) -> None:
        self.name = name
        self.dimension = dimension
        self.severity = severity
        self.confidence = confidence

    def detect(self, new_claim: Claim, existing_claims: list[Claim]) -> list[MarkerDraft]:
        drafts: list[MarkerDraft] = []
        for existing in existing_claims:
            if existing.subject == new_claim.subject and existing.value != new_claim.value:
                drafts.append(
                    MarkerDraft(
                        subject=new_claim.subject,
                        predicate=new_claim.predicate,
                        claim_ids=(existing.id, new_claim.id),
                        evidence=(
                            EvidenceRef(source=existing.source, claim_id=existing.id),
                            EvidenceRef(source=new_claim.source, claim_id=new_claim.id),
                        ),
                        dimensions=(self.dimension,),
                        severity=self.severity,
                        confidence=self.confidence,
                        message="first detector message",
                        metadata={"detector": self.name},
                    )
                )
        return drafts


def test_duplicate_marker_drafts_merge_dimensions_evidence_and_detector_metadata() -> None:
    state = MarkerLedger(
        detectors=[
            _DimensionDetector("alpha", "alpha_dimension", 0.4, 0.9),
            _DimensionDetector("beta", "beta_dimension", 0.8, 0.6),
        ],
        id_generator=CounterIdGenerator(),
        clock=FrozenClock(datetime(2026, 1, 1, tzinfo=UTC)),
    )
    state.add_claim(Claim("x", "equals", "a", "left"))
    result = state.add_claim(Claim("x", "equals", "b", "right"))

    assert len(result.markers) == 1
    marker = result.markers[0]
    assert marker.status is MarkerStatus.OPEN
    assert marker.dimensions == ("alpha_dimension", "beta_dimension")
    assert marker.severity == 0.8
    assert marker.confidence == 0.6
    assert marker.metadata["detectors"] == ["alpha", "beta"]
    assert len(marker.evidence) == 2
    assert len(state.list_claims()) == 2


def test_claim_validation_utilities() -> None:
    valid = Claim("subject", "equals", {"value": [1, "a"]}, "source", confidence=0.5)
    assert validate_claim(valid) == []
    assert is_json_value(valid.value)

    invalid = Claim("", "", object(), "", confidence=1.5)
    issues = validate_claim(invalid)
    assert ValidationIssue("subject", "required", "subject must be a non-empty string") in issues
    assert {issue.field for issue in issues} >= {
        "subject",
        "predicate",
        "source",
        "confidence",
        "value",
    }


def test_claim_validation_detects_non_json_scope_and_metadata() -> None:
    claim = Claim(
        "subject",
        "equals",
        "value",
        "source",
        scope={"bad": object()},  # type: ignore[dict-item]
        metadata={1: "not a string key"},  # type: ignore[dict-item]
    )
    issues = validate_claim(claim)
    assert {issue.field for issue in issues} == {"scope", "metadata"}


def test_temporal_detector_precision_and_timezone_policy() -> None:
    same_date = ledger()
    same_date.add_claim(Claim("deadline", "date", "2026-06-01", "a"))
    same_date.add_claim(Claim("deadline", "date", "2026-06-01", "b"))
    assert same_date.open_markers() == []

    different_date = ledger()
    different_date.add_claim(Claim("deadline", "date", "2026-06-01", "a"))
    different_date.add_claim(Claim("deadline", "date", "2026-06-02", "b"))
    assert len(different_date.open_markers()) == 1

    precision_mismatch = ledger()
    precision_mismatch.add_claim(Claim("deadline", "date", "2026-06-01", "a"))
    precision_mismatch.add_claim(Claim("deadline", "date", "2026-06-01T00:00:00", "b"))
    assert precision_mismatch.open_markers() == []

    same_instant = ledger()
    same_instant.add_claim(Claim("handoff", "date", "2026-06-01T12:00:00+09:00", "tokyo"))
    same_instant.add_claim(Claim("handoff", "date", "2026-06-01T03:00:00+00:00", "utc"))
    assert same_instant.open_markers() == []

    different_instant = ledger()
    different_instant.add_claim(Claim("handoff", "date", "2026-06-01T12:00:00+09:00", "tokyo"))
    different_instant.add_claim(Claim("handoff", "date", "2026-06-01T04:00:00+00:00", "utc"))
    assert len(different_instant.open_markers()) == 1
