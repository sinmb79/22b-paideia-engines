from paideia_engines.kibo import aggregate_pattern_evidence_v2, evaluate_pattern_promotion_v2
from paideia_engines.kibo.contracts_v2 import EvidenceSource, OutcomeEvidence


def _evidence(index: int, *, success=True, env=None, verifier_type="independent_test", status="verified", safety_score=1.0):
    return OutcomeEvidence(
        evidence_id=f"outcome-{index}",
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        task_id=f"task-{index}",
        run_id=f"run-{index}",
        environment_fingerprint=env or f"env-{index % 3}",
        task_difficulty=0.7,
        started_at="2026-06-23T00:00:00Z",
        observed_at="2026-06-23T00:00:01Z",
        outcome_latency_seconds=1.0,
        technical_score=0.95 if success else 0.2,
        safety_score=safety_score,
        user_utility_score=None,
        binary_success=success,
        baseline_ref="baseline-1",
        verifier_type=verifier_type,
        verifier_id="pytest",
        provenance=(EvidenceSource(f"receipt-{index}", "action_receipt", 1.0, f"hash-receipt-{index}"),),
        action_receipt_refs=(f"receipt-{index}",),
        artifact_hashes=(f"hash-artifact-{index}",),
        confidence=0.9,
        status=status,
    ).to_dict()


def test_evidence_aggregation_promotes_high_confidence_diverse_successes():
    summary = aggregate_pattern_evidence_v2(
        [_evidence(index) for index in range(10)],
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        as_of="2026-06-23T00:10:00Z",
    )
    promotion = evaluate_pattern_promotion_v2(summary)

    assert summary["verified_sample_count"] == 10
    assert summary["effective_sample_size"] == 10.0
    assert summary["environment_diversity"] == 3
    assert summary["success_lower_bound_95"] >= 0.7
    assert summary["confidence_grade"] == "high"
    assert promotion["status"] == "passed"


def test_evidence_aggregation_counts_verified_failures_in_wilson_bound():
    rows = [_evidence(index, success=index < 6) for index in range(10)]
    summary = aggregate_pattern_evidence_v2(rows, as_of="2026-06-23T00:10:00Z")
    promotion = evaluate_pattern_promotion_v2(summary)

    assert summary["verified_sample_count"] == 10
    assert summary["weighted_success_rate"] == 0.6
    assert summary["success_lower_bound_95"] < 0.7
    assert summary["repeated_failure_rate"] == 0.4
    assert any(issue["code"] == "success_lower_bound" for issue in promotion["issues"])


def test_manual_high_scores_do_not_count_toward_field_sample_size():
    summary = aggregate_pattern_evidence_v2(
        [_evidence(index, verifier_type="manual") for index in range(8)],
        as_of="2026-06-23T00:10:00Z",
    )
    promotion = evaluate_pattern_promotion_v2(summary)

    assert summary["verified_sample_count"] == 0
    assert summary["blocked_evidence_count"] == 8
    assert "manual_verifier" in summary["blocked_issue_codes"]
    assert any(issue["code"] == "sample_count" for issue in promotion["issues"])


def test_missing_safety_scores_do_not_count_toward_field_sample_size():
    rows = [_evidence(index, safety_score=None) for index in range(8)]
    summary = aggregate_pattern_evidence_v2(rows, as_of="2026-06-23T00:10:00Z")

    assert summary["verified_sample_count"] == 0
    assert "missing_safety_score" in summary["blocked_issue_codes"]


def test_promotion_gate_blocks_low_environment_diversity():
    summary = aggregate_pattern_evidence_v2(
        [_evidence(index, env="same-env") for index in range(10)],
        as_of="2026-06-23T00:10:00Z",
    )
    promotion = evaluate_pattern_promotion_v2(summary)

    assert summary["environment_diversity"] == 1
    assert promotion["status"] == "blocked"
    assert any(issue["code"] == "environment_diversity" for issue in promotion["issues"])


def test_critical_safety_failure_blocks_promotion_even_when_other_evidence_passes():
    rows = [_evidence(index) for index in range(10)]
    rows.append(_evidence(99, safety_score=0.1))
    summary = aggregate_pattern_evidence_v2(rows, as_of="2026-06-23T00:10:00Z")
    promotion = evaluate_pattern_promotion_v2(summary)

    assert summary["critical_failure_count"] == 1
    assert summary["confidence_grade"] == "quarantine"
    assert any(issue["code"] == "critical_failure" for issue in promotion["issues"])


def test_stale_evidence_blocks_promotion_freshness_gate():
    summary = aggregate_pattern_evidence_v2(
        [_evidence(index) for index in range(10)],
        as_of="2027-06-23T00:10:00Z",
        freshness_days=30,
    )
    promotion = evaluate_pattern_promotion_v2(summary)

    assert summary["evidence_freshness_score"] == 0.0
    assert any(issue["code"] == "freshness" for issue in promotion["issues"])


def test_promotion_gate_rejects_non_finite_or_wrong_schema_summary_metrics():
    summary = aggregate_pattern_evidence_v2(
        [_evidence(index) for index in range(10)],
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        as_of="2026-06-23T00:10:00Z",
    )
    summary["schema"] = "forged-summary/v1"
    summary["success_lower_bound_95"] = float("nan")

    promotion = evaluate_pattern_promotion_v2(summary)

    assert promotion["status"] == "blocked"
    assert promotion["promotion_allowed"] is False
    assert any(issue["code"] == "summary_schema" for issue in promotion["issues"])
    assert any(issue["code"] == "invalid_summary_metric" for issue in promotion["issues"])
    assert any(issue["code"] == "success_lower_bound" for issue in promotion["issues"])
