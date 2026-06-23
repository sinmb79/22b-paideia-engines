import pytest

from paideia_engines.kibo import evaluate_outcome_evidence_v2
from paideia_engines.kibo.contracts_v2 import EvidenceSource, OutcomeEvidence


def _evidence(
    *,
    verifier_type="independent_test",
    status="verified",
    action_receipts=("receipt-1",),
    safety_score=1.0,
    binary_success=True,
    provenance=True,
):
    return OutcomeEvidence(
        evidence_id="outcome-1",
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        task_id="task-1",
        run_id="run-1",
        environment_fingerprint="env-1",
        task_difficulty=0.7,
        started_at="2026-06-23T00:00:00Z",
        observed_at="2026-06-23T00:00:01Z",
        outcome_latency_seconds=1.0,
        technical_score=0.95,
        safety_score=safety_score,
        user_utility_score=None,
        binary_success=binary_success,
        baseline_ref="baseline-1",
        verifier_type=verifier_type,
        verifier_id="pytest",
        provenance=(EvidenceSource("receipt-1", "action_receipt", 1.0, "hash-receipt"),) if provenance else (),
        action_receipt_refs=action_receipts,
        artifact_hashes=("hash-artifact",),
        confidence=0.9,
        status=status,
    ).to_dict()


def test_verified_independent_outcome_with_receipt_gets_field_credit():
    report = evaluate_outcome_evidence_v2(_evidence())

    assert report["status"] == "passed"
    assert report["field_validation_credit"] is True
    assert report["receipt_provenance_verified"] is True
    assert report["max_evidence_weight"] == 1.0
    assert report["evidence_weight"] > 0.0


def test_manual_verified_outcome_is_capped_and_blocked_for_field_credit():
    report = evaluate_outcome_evidence_v2(_evidence(verifier_type="manual"))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert report["max_evidence_weight"] == 0.25
    assert any(issue["code"] == "manual_verifier" for issue in report["issues"])
    assert any(issue["code"] == "non_independent_verifier" for issue in report["issues"])


def test_non_independent_verified_outcome_is_not_field_evidence():
    report = evaluate_outcome_evidence_v2(_evidence(verifier_type="peer_review"))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert any(issue["code"] == "non_independent_verifier" for issue in report["issues"])


def test_verified_outcome_without_action_receipt_is_not_field_evidence():
    report = evaluate_outcome_evidence_v2(_evidence(action_receipts=()))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert report["has_action_receipts"] is False
    assert any(issue["code"] == "missing_action_receipt" for issue in report["issues"])


def test_fake_receipt_ref_without_provenance_is_not_field_evidence():
    report = evaluate_outcome_evidence_v2(_evidence(provenance=False))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert report["receipt_provenance_verified"] is False
    assert any(issue["code"] == "receipt_provenance" for issue in report["issues"])


@pytest.mark.parametrize("status", ["contested", "invalidated", "expired"])
def test_non_verified_outcomes_have_zero_evidence_weight(status):
    report = evaluate_outcome_evidence_v2(_evidence(status=status))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert report["max_evidence_weight"] == 0.0


def test_low_safety_score_blocks_field_credit():
    report = evaluate_outcome_evidence_v2(_evidence(safety_score=0.6))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert any(issue["code"] == "safety_score" for issue in report["issues"])


def test_missing_safety_score_blocks_field_credit():
    report = evaluate_outcome_evidence_v2(_evidence(safety_score=None))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert any(issue["code"] == "missing_safety_score" for issue in report["issues"])


def test_failed_binary_outcome_is_weighted_but_never_field_credit():
    report = evaluate_outcome_evidence_v2(_evidence(binary_success=False))

    assert report["status"] == "blocked"
    assert report["field_validation_credit"] is False
    assert report["evidence_weight"] > 0.0
    assert any(issue["code"] == "binary_success" for issue in report["issues"])


def test_malformed_outcome_evidence_fails_closed():
    payload = _evidence()
    payload["contract_hash"] = "0" * 64

    with pytest.raises(ValueError, match="Contract hash mismatch"):
        evaluate_outcome_evidence_v2(payload)


def test_non_finite_safety_score_fails_closed():
    payload = _evidence(safety_score=float("nan"))

    with pytest.raises(ValueError):
        evaluate_outcome_evidence_v2(payload)
