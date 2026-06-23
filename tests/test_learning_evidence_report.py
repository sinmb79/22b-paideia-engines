from paideia_engines.evaluation import build_learning_evidence_report, validate_learning_evidence_report
from paideia_engines.kibo.contracts_v2 import TokenUsageReceipt


def _receipt(run_id="run-1", *, estimated=False):
    return TokenUsageReceipt(
        receipt_id=f"token-{run_id}",
        run_id=run_id,
        provider="openai",
        model="gpt-test",
        call_purpose="benchmark",
        input_tokens=100,
        output_tokens=20,
        cached_input_tokens=0,
        estimated=estimated,
        estimation_method="paideia_local_token_estimate" if estimated else None,
        monetary_cost=0.01,
        latency_ms=100,
        created_at="2026-06-23T00:00:00Z",
    ).to_dict()


def test_learning_evidence_report_passes_with_benchmark_contract_and_token_receipts():
    report = build_learning_evidence_report(
        release="behavioral-learning-evidence-loop-2026-Q3",
        benchmark_report={
            "schema": "paideia-pattern-loop-benchmark-report/v1",
            "status": "passed",
            "benchmark_comparison": {"success_rate_delta": 0.12, "net_token_saving_ratio": 0.30},
            "safety_metrics": {"critical_safety_violations": 0},
            "checks": {
                "success_lift_passed": True,
                "token_saving_passed": True,
                "actual_token_receipt_comparison": True,
                "critical_safety_violation_free": True,
            },
        },
        token_usage_receipts=[_receipt()],
        contract_conformance={"passed": True, "percent": 100.0},
        retrieval_metrics={"false_direct_reuse_rate": 0.0},
        behavioral_exam_metrics={"holdout_success_rate": 0.85},
    )

    assert report["schema"] == "paideia-learning-evidence-report/v1"
    assert report["status"] == "passed"
    assert report["checks"]["contract_conformance_100_percent"] is True
    assert report["token_cost_metrics"]["actual_receipt_count"] == 1
    assert validate_learning_evidence_report(report)["accepted"] is True


def test_learning_evidence_report_blocks_failed_benchmark_or_missing_conformance():
    report = build_learning_evidence_report(
        release="behavioral-learning-evidence-loop-2026-Q3",
        benchmark_report={
            "schema": "paideia-pattern-loop-benchmark-report/v1",
            "status": "blocked",
            "benchmark_comparison": {"net_token_saving_ratio": 0.0},
            "safety_metrics": {"critical_safety_violations": 1},
            "checks": {"success_lift_passed": False},
        },
        token_usage_receipts=[_receipt(estimated=True)],
        contract_conformance={"percent": 99.0},
    )

    validation = validate_learning_evidence_report(report)
    assert report["status"] == "blocked"
    assert report["checks"]["benchmark_passed"] is False
    assert report["checks"]["contract_conformance_100_percent"] is False
    assert validation["accepted"] is False


def test_learning_evidence_report_does_not_trust_status_without_schema_and_checks():
    report = build_learning_evidence_report(
        release="behavioral-learning-evidence-loop-2026-Q3",
        benchmark_report={
            "schema": "wrong/v1",
            "status": "passed",
            "benchmark_comparison": {"net_token_saving_ratio": 0.30},
            "safety_metrics": {"critical_safety_violations": 0},
            "checks": {"success_lift_passed": False},
        },
        token_usage_receipts=[_receipt()],
        contract_conformance={"passed": True, "percent": 100.0},
    )

    assert report["status"] == "blocked"
    assert report["checks"]["benchmark_schema_matches"] is False
    assert report["checks"]["benchmark_checks_passed"] is False


def test_learning_evidence_report_cannot_mask_benchmark_safety_violation_with_override():
    report = build_learning_evidence_report(
        release="behavioral-learning-evidence-loop-2026-Q3",
        benchmark_report={
            "schema": "paideia-pattern-loop-benchmark-report/v1",
            "status": "passed",
            "benchmark_comparison": {"net_token_saving_ratio": 0.30},
            "safety_metrics": {"critical_safety_violations": 1},
            "checks": {
                "success_lift_passed": True,
                "token_saving_passed": True,
                "actual_token_receipt_comparison": True,
                "critical_safety_violation_free": True,
            },
        },
        token_usage_receipts=[_receipt()],
        contract_conformance={"passed": True, "percent": 100.0},
        safety_metrics={"critical_safety_violations": 0},
    )

    assert report["status"] == "blocked"
    assert report["checks"]["critical_safety_violation_free"] is False


def test_learning_evidence_report_requires_actual_token_receipts():
    report = build_learning_evidence_report(
        release="behavioral-learning-evidence-loop-2026-Q3",
        benchmark_report={
            "schema": "paideia-pattern-loop-benchmark-report/v1",
            "status": "passed",
            "benchmark_comparison": {"net_token_saving_ratio": 0.30},
            "safety_metrics": {"critical_safety_violations": 0},
            "checks": {
                "success_lift_passed": True,
                "token_saving_passed": True,
                "actual_token_receipt_comparison": True,
                "critical_safety_violation_free": True,
            },
        },
        token_usage_receipts=[],
        contract_conformance={"passed": True, "percent": 100.0},
    )

    assert report["status"] == "blocked"
    assert report["checks"]["actual_or_flagged_token_usage"] is False
    assert validate_learning_evidence_report(report)["accepted"] is False
