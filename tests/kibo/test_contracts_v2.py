import json
from pathlib import Path

import pytest

from paideia_engines.contracts import (
    cross_repo_compatibility_manifest,
    validate_cross_repo_compatibility_manifest,
)
from paideia_engines.kibo.contracts_v2 import (
    ActionNode,
    ActionPattern,
    ActionStepEvidence,
    BehavioralExamResult,
    CaseGraph,
    ConstraintSpec,
    EvidenceSource,
    ObservationRequirement,
    ObservationSpec,
    OutcomeAttributionReport,
    OutcomeEvidence,
    PatternRevisionProposal,
    PatternValidationProfile,
    Predicate,
    RetryPolicy,
    ScenarioResult,
    StepCredit,
    TokenUsageReceipt,
    Transition,
    TypedSlot,
    TypedValue,
)
from paideia_engines.kibo.schema_registry import (
    CONTRACT_NAMES,
    SCHEMA_DEFINITIONS,
    contract_hash,
    contract_hashes,
    get_schema,
    schema_registry,
)


ROOT = Path(__file__).resolve().parents[2]


def _case_graph():
    return CaseGraph(
        case_id="case-1",
        owner="Boss",
        domain="software_agent_engineering",
        task_family="implementation",
        goal="Implement a CLI command with tests.",
        context_variables=(TypedValue("repo", "path", "."),),
        observations=(ObservationSpec("obs-1", "test output", "text", True, None),),
        constraints=(ConstraintSpec("constraint-1", Predicate("p1", "exists", "tests", True), "hard"),),
        action_steps=(ActionStepEvidence("step-1", "inspect", "code_inspection", ("repo",), "plan", "receipt-1"),),
        branch_events=(),
        outcome_refs=("outcome-1",),
        failure_refs=(),
        source_kibo_ids=("kibo-1", "kibo-2", "kibo-3"),
        evidence_hashes=("hash-1",),
    )


def _action_pattern():
    return ActionPattern(
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        parent_pattern_version=None,
        owner="Boss",
        domain="software_agent_engineering",
        task_family="implementation",
        goal_template="Implement {feature} with tests.",
        input_slots=(TypedSlot("feature", "string", True),),
        preconditions=(Predicate("pre-1", "exists", "repo", True),),
        required_observations=(ObservationRequirement("obs-1", "text", None),),
        steps=(
            ActionNode(
                node_id="inspect",
                action_type="inspect",
                capability="code_inspection",
                input_bindings={"repo": "context.repo"},
                expected_effects=(Predicate("effect-1", "exists", "plan", True),),
                timeout_ms=1000,
                retry_policy=RetryPolicy(1, 0),
                on_success="test",
                on_failure=None,
                on_uncertain=None,
                human_review_required=False,
            ),
        ),
        transitions=(Transition("inspect", "test", None),),
        invariants=(Predicate("inv-1", "neq", "artifact.private_trace", True),),
        abort_conditions=(Predicate("abort-1", "eq", "safety_violation", True),),
        recovery_actions=(),
        success_conditions=(Predicate("success-1", "eq", "tests_passed", True),),
        forbidden_contexts=(Predicate("forbidden-1", "eq", "quarantined_source", True),),
        required_capabilities=("code_inspection", "test_execution"),
        source_case_ids=("case-1",),
        validation_profile_id=None,
        lifecycle_status="draft",
    )


def _behavioral_exam():
    return BehavioralExamResult(
        exam_id="exam-1",
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        scenario_pack_id="pack-1",
        scenario_results=(
            ScenarioResult("scenario-1", "near_transfer", True, True, False, (), "hash-trace"),
        ),
        task_success_rate=1.0,
        invariant_pass_rate=1.0,
        transfer_score=0.8,
        abstention_precision=1.0,
        efficiency_score=0.7,
        safety_violation_count=0,
        leakage_detected=False,
        passed=True,
        evidence_hashes=("hash-exam",),
    )


def _validation_profile():
    return PatternValidationProfile(
        profile_id="validation-1",
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        structural_exam_passed=True,
        behavioral_exam_passed=True,
        near_transfer_passed=True,
        far_transfer_passed=False,
        adversarial_exam_passed=False,
        shadow_validation_passed=False,
        field_validation_passed=False,
        critic_clearance_passed=True,
        evidence_fresh_until=None,
        high_risk_eligible=False,
        evidence_refs=("exam-1",),
    )


def _outcome_evidence():
    return OutcomeEvidence(
        evidence_id="evidence-1",
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        task_id="task-1",
        run_id="run-1",
        environment_fingerprint="env-hash",
        task_difficulty=0.6,
        started_at="2026-06-23T00:00:00Z",
        observed_at="2026-06-23T00:00:01Z",
        outcome_latency_seconds=1.0,
        technical_score=0.9,
        safety_score=1.0,
        user_utility_score=None,
        binary_success=True,
        baseline_ref="baseline-1",
        verifier_type="independent_test",
        verifier_id="pytest",
        provenance=(EvidenceSource("source-1", "action_receipt", 1.0, "hash-receipt"),),
        action_receipt_refs=("receipt-1",),
        artifact_hashes=("hash-artifact",),
        confidence=0.9,
        status="verified",
    )


def _attribution_report():
    return OutcomeAttributionReport(
        report_id="attr-1",
        outcome_evidence_id="evidence-1",
        pattern_contribution=0.7,
        llm_contribution=0.1,
        tool_contribution=0.1,
        human_contribution=0.0,
        environment_contribution=0.1,
        attribution_confidence=0.8,
        confounders=(),
        comparison_baseline="baseline-1",
        step_credits=(StepCredit("inspect", 0.5, 0.8, ("goal_progress",)),),
    )


ROUND_TRIP = [
    ("case_graph", _case_graph),
    ("action_pattern", _action_pattern),
    ("behavioral_exam", _behavioral_exam),
    ("validation_profile", _validation_profile),
    ("outcome_evidence", _outcome_evidence),
    ("attribution_report", _attribution_report),
    (
        "pattern_revision",
        lambda: PatternRevisionProposal(
            "revision-1",
            "pattern-1",
            "1.0.0",
            "1.0.1",
            ("negative_step_credit",),
            ({"op": "tighten_precondition", "field": "repo"},),
            ("attr-1",),
            True,
            True,
            "quarantined",
        ),
    ),
    (
        "token_usage_receipt",
        lambda: TokenUsageReceipt(
            "token-1",
            "run-1",
            "openai",
            "gpt-test",
            "critic",
            100,
            20,
            0,
            False,
            None,
            0.01,
            123,
            "2026-06-23T00:00:00Z",
        ),
    ),
]


def test_schema_registry_lists_every_pr1_contract():
    registry = schema_registry()

    assert tuple(registry["schema_ids"]) == CONTRACT_NAMES
    assert set(registry["contract_hashes"]) == set(CONTRACT_NAMES)
    assert all(len(value) == 64 for value in registry["contract_hashes"].values())


def test_review_schema_files_exist_for_every_registered_contract():
    for name in CONTRACT_NAMES:
        schema_path = ROOT / "schemas" / "kibo-v2" / f"{name}.schema.json"
        assert schema_path.exists()
        assert json.loads(schema_path.read_text(encoding="utf-8")) == get_schema(name)


@pytest.mark.parametrize(("contract_name", "factory"), ROUND_TRIP)
def test_v2_contracts_emit_hash_and_round_trip(contract_name, factory):
    artifact = factory()
    payload = artifact.to_dict()
    restored = artifact.__class__.from_dict(payload)

    assert payload["schema_version"] == "2.0.0"
    assert payload["contract_hash"] == contract_hash(contract_name)
    assert restored.to_dict() == payload


def test_v2_loader_fails_closed_on_unsupported_major_version():
    payload = _action_pattern().to_dict()
    payload["schema_version"] = "3.0.0"

    with pytest.raises(ValueError, match="Unsupported major schema_version"):
        ActionPattern.from_dict(payload)


def test_v2_loader_fails_closed_on_contract_hash_mismatch():
    payload = _validation_profile().to_dict()
    payload["contract_hash"] = "0" * 64

    with pytest.raises(ValueError, match="Contract hash mismatch"):
        PatternValidationProfile.from_dict(payload)


def test_v2_loader_fails_closed_on_missing_required_payload():
    payload = _action_pattern().to_dict()
    del payload["pattern_id"]

    with pytest.raises(ValueError, match="Missing required field"):
        ActionPattern.from_dict(payload)


def test_v2_loader_fails_closed_on_malformed_nested_payload():
    payload = _action_pattern().to_dict()
    payload["steps"] = [{"junk": True}]

    with pytest.raises(ValueError, match="Missing required field"):
        ActionPattern.from_dict(payload)


def test_cross_repo_compatibility_manifest_uses_registry_hashes():
    manifest = cross_repo_compatibility_manifest()
    report = validate_cross_repo_compatibility_manifest(manifest)

    assert manifest["contracts_release"] == "2.0.0"
    assert manifest["contract_hashes"] == contract_hashes()
    assert report["status"] == "passed"


def test_review_manifest_artifact_matches_runtime_manifest():
    manifest_path = ROOT / "docs" / "cross_repo_compatibility_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest == cross_repo_compatibility_manifest()


def test_cross_repo_compatibility_manifest_blocks_stale_hash():
    manifest = cross_repo_compatibility_manifest()
    manifest["contract_hashes"]["action_pattern"] = "0" * 64
    report = validate_cross_repo_compatibility_manifest(manifest)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "contract_hash" for issue in report["issues"])


def test_cross_repo_compatibility_manifest_blocks_missing_repo_range():
    manifest = cross_repo_compatibility_manifest()
    del manifest["paideia_agent"]
    report = validate_cross_repo_compatibility_manifest(manifest)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "repo_compatibility" for issue in report["issues"])
