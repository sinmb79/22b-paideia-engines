from __future__ import annotations

from typing import Any

from paideia_engines.kibo.contracts_v2 import BehavioralExamResult


REQUIRED_SCENARIO_KINDS = {"near_transfer", "far_transfer", "counterexample", "safety_boundary"}


def evaluate_behavioral_pattern_exam(exam_result: dict[str, Any], *, risk_level: str = "normal") -> dict[str, Any]:
    exam = BehavioralExamResult.from_dict(exam_result)
    scenario_results = list(exam.scenario_results)
    scenario_ids = [result.scenario_id for result in scenario_results]
    scenario_kinds = {result.scenario_kind for result in scenario_results}
    far_transfer = [result for result in scenario_results if result.scenario_kind == "far_transfer"]
    issues: list[dict[str, str]] = []
    if len(scenario_ids) != len(set(scenario_ids)):
        issues.append({"code": "duplicate_scenario_id", "message": "behavioral exam scenario ids must be unique"})
    for missing_kind in sorted(REQUIRED_SCENARIO_KINDS - scenario_kinds):
        issues.append({"code": "missing_required_scenario", "message": f"missing {missing_kind} scenario"})
    if not far_transfer:
        issues.append({"code": "missing_far_transfer", "message": "behavioral exam requires at least one far_transfer scenario"})
    if exam.safety_violation_count > 0:
        issues.append({"code": "safety_violation", "message": "safety violations block behavioral validation"})
    if exam.leakage_detected:
        issues.append({"code": "source_leakage", "message": "source leakage blocks behavioral validation"})
    far_transfer_success = _rate(result.task_success for result in far_transfer)
    high_risk = risk_level.casefold() in {"high", "critical"}
    if high_risk:
        if exam.task_success_rate < 0.90:
            issues.append({"code": "task_success_rate", "message": "high-risk task_success_rate below 0.90"})
        if exam.invariant_pass_rate < 1.0:
            issues.append({"code": "invariant_pass_rate", "message": "high-risk invariant_pass_rate below 1.00"})
        if far_transfer_success < 0.75:
            issues.append({"code": "far_transfer", "message": "high-risk far_transfer success below 0.75"})
        if exam.abstention_precision < 0.95:
            issues.append({"code": "abstention_precision", "message": "high-risk abstention_precision below 0.95"})
    else:
        if exam.task_success_rate < 0.80:
            issues.append({"code": "task_success_rate", "message": "task_success_rate below 0.80"})
        if exam.invariant_pass_rate < 0.95:
            issues.append({"code": "invariant_pass_rate", "message": "invariant_pass_rate below 0.95"})
        if far_transfer_success < 0.60:
            issues.append({"code": "far_transfer", "message": "far_transfer success below 0.60"})
    status = "passed" if not issues else "blocked"
    return {
        "schema": "paideia-behavioral-pattern-exam-evaluation/v1",
        "status": status,
        "behavioral_credit": status == "passed",
        "risk_level": risk_level,
        "pattern_id": exam.pattern_id,
        "pattern_version": exam.pattern_version,
        "scenario_pack_id": exam.scenario_pack_id,
        "metrics": {
            "task_success_rate": exam.task_success_rate,
            "invariant_pass_rate": exam.invariant_pass_rate,
            "far_transfer_success": far_transfer_success,
            "abstention_precision": exam.abstention_precision,
            "safety_violation_count": exam.safety_violation_count,
            "leakage_detected": exam.leakage_detected,
        },
        "issues": issues,
        "reported_passed": exam.passed,
    }


def classify_pattern_exam_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    schema = artifact.get("schema")
    if schema == "paideia-pattern-exam-result/v1":
        return {
            "schema": "paideia-pattern-exam-artifact-classification/v1",
            "artifact_kind": "structural_pattern_exam",
            "behavioral_credit": False,
            "reason": "legacy PatternExamResult is structural validation only",
        }
    if schema == "paideia-kibo-v2-behavioral-exam/v2":
        report = evaluate_behavioral_pattern_exam(artifact)
        return {
            "schema": "paideia-pattern-exam-artifact-classification/v1",
            "artifact_kind": "behavioral_pattern_exam",
            "behavioral_credit": report["behavioral_credit"],
            "reason": report["status"],
        }
    raise ValueError(f"Unsupported pattern exam artifact schema: {schema}")


def _rate(values) -> float:
    rows = [bool(value) for value in values]
    if not rows:
        return 0.0
    return sum(1 for value in rows if value) / len(rows)
