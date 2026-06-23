from __future__ import annotations

from typing import Any, Iterable

from paideia_engines.kibo.contracts_v2 import TokenUsageReceipt


LEARNING_EVIDENCE_REPORT_SCHEMA = "paideia-learning-evidence-report/v1"


def build_learning_evidence_report(
    *,
    release: str,
    benchmark_report: dict[str, Any],
    token_usage_receipts: Iterable[dict[str, Any]] = (),
    contract_conformance: dict[str, Any] | None = None,
    retrieval_metrics: dict[str, Any] | None = None,
    behavioral_exam_metrics: dict[str, Any] | None = None,
    safety_metrics: dict[str, Any] | None = None,
    known_limitations: Iterable[str] = (),
) -> dict[str, Any]:
    receipts = [TokenUsageReceipt.from_dict(dict(row)).to_dict() for row in token_usage_receipts]
    token_metrics = _token_metrics(receipts, benchmark_report)
    benchmark_safety = dict(benchmark_report.get("safety_metrics") or {})
    safety = {**dict(safety_metrics or {}), **benchmark_safety}
    conformance = dict(contract_conformance or {})
    benchmark_checks = benchmark_report.get("checks") if isinstance(benchmark_report.get("checks"), dict) else {}
    checks = {
        "benchmark_schema_matches": benchmark_report.get("schema") == "paideia-pattern-loop-benchmark-report/v1",
        "benchmark_passed": benchmark_report.get("status") == "passed",
        "benchmark_checks_passed": bool(benchmark_checks) and all(value is True for value in benchmark_checks.values()),
        "contract_conformance_100_percent": _conformance_passed(conformance),
        "critical_safety_violation_free": int(benchmark_safety.get("critical_safety_violations") or 0) == 0
        and int(safety.get("critical_safety_violations") or 0) == 0,
        "actual_or_flagged_token_usage": token_metrics["receipt_count"] > 0
        and token_metrics["actual_receipt_count"] > 0
        and token_metrics["receipt_count"] == token_metrics["actual_receipt_count"] + token_metrics["estimated_receipt_count"],
    }
    return {
        "schema": LEARNING_EVIDENCE_REPORT_SCHEMA,
        "release": release,
        "status": "passed" if all(checks.values()) else "blocked",
        "contract_conformance": conformance,
        "retrieval_metrics": dict(retrieval_metrics or {}),
        "behavioral_exam_metrics": dict(behavioral_exam_metrics or {}),
        "benchmark_comparison": dict(benchmark_report.get("benchmark_comparison") or {}),
        "token_cost_metrics": token_metrics,
        "safety_metrics": safety,
        "checks": checks,
        "known_limitations": list(known_limitations),
    }


def validate_learning_evidence_report(report: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if report.get("schema") != LEARNING_EVIDENCE_REPORT_SCHEMA:
        issues.append({"code": "schema_mismatch", "message": "learning evidence report schema mismatch"})
    if not report.get("release"):
        issues.append({"code": "release_missing", "message": "release is required"})
    checks = report.get("checks")
    if not isinstance(checks, dict) or not checks:
        issues.append({"code": "checks_missing", "message": "checks are required"})
    elif not all(value is True for value in checks.values()):
        issues.append({"code": "checks_not_passed", "message": "all learning evidence checks must pass"})
    return {
        "schema": "paideia-learning-evidence-report-validation/v1",
        "accepted": not issues,
        "issues": issues,
    }


def _token_metrics(receipts: list[dict[str, Any]], benchmark_report: dict[str, Any]) -> dict[str, Any]:
    total_input = sum(item.get("input_tokens") or 0 for item in receipts)
    total_output = sum(item.get("output_tokens") or 0 for item in receipts)
    total_cached = sum(item.get("cached_input_tokens") or 0 for item in receipts)
    total_cost = sum(item.get("monetary_cost") or 0.0 for item in receipts)
    estimated_count = sum(1 for item in receipts if item.get("estimated") is True)
    comparison = benchmark_report.get("benchmark_comparison") or {}
    return {
        "receipt_count": len(receipts),
        "actual_receipt_count": len(receipts) - estimated_count,
        "estimated_receipt_count": estimated_count,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cached_input_tokens": total_cached,
        "total_tokens": total_input + total_output,
        "monetary_cost": round(total_cost, 6),
        "net_token_saving_ratio": float(comparison.get("net_token_saving_ratio") or 0.0),
    }


def _conformance_passed(conformance: dict[str, Any]) -> bool:
    if not conformance:
        return False
    if conformance.get("passed") is True:
        return True
    percent = conformance.get("percent")
    try:
        return float(percent) >= 100.0
    except (TypeError, ValueError):
        return False
