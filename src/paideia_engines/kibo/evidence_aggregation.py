from __future__ import annotations

from datetime import datetime, timezone
import math
from math import sqrt
from typing import Any, Iterable

from .contracts_v2 import OutcomeEvidence
from .outcome_evidence_governance import evaluate_outcome_evidence_v2


EVIDENCE_SUMMARY_SCHEMA = "paideia-pattern-evidence-summary/v1"
PROMOTION_EVALUATION_SCHEMA = "paideia-pattern-promotion-evaluation-v2/v1"


def aggregate_pattern_evidence_v2(
    evidence_rows: Iterable[dict[str, Any]],
    *,
    pattern_id: str | None = None,
    pattern_version: str | None = None,
    as_of: str | None = None,
    freshness_days: int = 90,
) -> dict[str, Any]:
    parsed = [OutcomeEvidence.from_dict(row) for row in evidence_rows]
    if pattern_id is None and parsed:
        pattern_id = parsed[0].pattern_id
    if pattern_version is None and parsed:
        pattern_version = parsed[0].pattern_version
    scoped = [
        evidence
        for evidence in parsed
        if (pattern_id is None or evidence.pattern_id == pattern_id)
        and (pattern_version is None or evidence.pattern_version == pattern_version)
    ]
    reports = [evaluate_outcome_evidence_v2(evidence.to_dict()) for evidence in scoped]
    credited = [
        (evidence, report)
        for evidence, report in zip(scoped, reports)
        if _aggregation_credit(evidence, report)
    ]
    weights = [float(report["evidence_weight"]) for _, report in credited if float(report["evidence_weight"]) > 0.0]
    successes = [
        1.0 if evidence.binary_success is True else 0.0
        for evidence, report in credited
        if float(report["evidence_weight"]) > 0.0
    ]
    weighted_success_rate = _weighted_mean(successes, weights)
    technical_scores = [evidence.technical_score for evidence, _ in credited if evidence.technical_score is not None]
    safety_scores = [evidence.safety_score for evidence, _ in credited if evidence.safety_score is not None]
    utility_scores = [evidence.user_utility_score for evidence, _ in credited if evidence.user_utility_score is not None]
    effective_sample_size = _effective_sample_size(weights)
    as_of_dt = _parse_time(as_of) or datetime.now(timezone.utc)
    fresh_count = sum(1 for evidence, _ in credited if _is_fresh(evidence.observed_at, as_of_dt, freshness_days))
    critical_failure_count = sum(1 for evidence in scoped if _critical_failure(evidence))
    failure_count = sum(1 for evidence, _ in credited if evidence.binary_success is False)
    issue_codes = sorted({issue["code"] for report in reports for issue in report["issues"]})
    lower_bound = _wilson_lower_bound(weighted_success_rate, effective_sample_size)
    summary = {
        "schema": EVIDENCE_SUMMARY_SCHEMA,
        "pattern_id": pattern_id or "",
        "pattern_version": pattern_version or "",
        "verified_sample_count": len(credited),
        "effective_sample_size": round(effective_sample_size, 4),
        "environment_diversity": len({evidence.environment_fingerprint for evidence, _ in credited}),
        "independent_verified_count": sum(1 for _, report in credited if report["independent_verifier"]),
        "weighted_success_rate": None if weighted_success_rate is None else round(weighted_success_rate, 4),
        "success_lower_bound_95": None if lower_bound is None else round(lower_bound, 4),
        "weighted_technical_score": _rounded_mean(technical_scores),
        "weighted_safety_score": _rounded_mean(safety_scores),
        "weighted_user_utility": _rounded_mean(utility_scores),
        "critical_failure_count": critical_failure_count,
        "repeated_failure_rate": round(failure_count / len(credited), 4) if credited else 0.0,
        "evidence_freshness_score": round(fresh_count / len(credited), 4) if credited else 0.0,
        "confidence_grade": _confidence_grade(len(credited), effective_sample_size, lower_bound, critical_failure_count),
        "source_evidence_count": len(scoped),
        "blocked_evidence_count": len(scoped) - len(credited),
        "blocked_issue_codes": issue_codes,
    }
    return summary


def evaluate_pattern_promotion_v2(
    evidence_summary: dict[str, Any],
    *,
    min_verified_samples: int = 5,
    min_environment_diversity: int = 3,
    min_independent_verified: int = 2,
    min_success_lower_bound: float = 0.7,
    min_freshness_score: float = 0.6,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if evidence_summary.get("schema") != EVIDENCE_SUMMARY_SCHEMA:
        issues.append({"code": "summary_schema", "message": "unsupported evidence summary schema"})
    verified_sample_count = _summary_int(evidence_summary, "verified_sample_count", issues)
    environment_diversity = _summary_int(evidence_summary, "environment_diversity", issues)
    independent_verified_count = _summary_int(evidence_summary, "independent_verified_count", issues)
    critical_failure_count = _summary_int(evidence_summary, "critical_failure_count", issues)
    lower_bound = _summary_optional_score(evidence_summary, "success_lower_bound_95", issues)
    freshness_score = _summary_score(evidence_summary, "evidence_freshness_score", issues)
    if verified_sample_count < min_verified_samples:
        issues.append({"code": "sample_count", "message": "not enough verified outcome evidence"})
    if environment_diversity < min_environment_diversity:
        issues.append({"code": "environment_diversity", "message": "not enough environment diversity"})
    if independent_verified_count < min_independent_verified:
        issues.append({"code": "independent_verifier_count", "message": "not enough independent verifier evidence"})
    if lower_bound is None or lower_bound < min_success_lower_bound:
        issues.append({"code": "success_lower_bound", "message": "Wilson lower bound is below promotion threshold"})
    if critical_failure_count > 0:
        issues.append({"code": "critical_failure", "message": "critical safety failure requires quarantine review"})
    if freshness_score < min_freshness_score:
        issues.append({"code": "freshness", "message": "not enough recent evidence"})
    return {
        "schema": PROMOTION_EVALUATION_SCHEMA,
        "status": "passed" if not issues else "blocked",
        "pattern_id": evidence_summary.get("pattern_id"),
        "pattern_version": evidence_summary.get("pattern_version"),
        "promotion_allowed": not issues,
        "issues": issues,
    }


def _weighted_mean(values: list[float], weights: list[float]) -> float | None:
    if not values or not weights or len(values) != len(weights):
        return None
    denominator = sum(weights)
    if denominator <= 0.0:
        return None
    return sum(value * weight for value, weight in zip(values, weights)) / denominator


def _rounded_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _effective_sample_size(weights: list[float]) -> float:
    if not weights:
        return 0.0
    squared_sum = sum(weight * weight for weight in weights)
    if squared_sum <= 0.0:
        return 0.0
    return (sum(weights) ** 2) / squared_sum


def _wilson_lower_bound(success_rate: float | None, sample_size: float, *, z: float = 1.96) -> float | None:
    if success_rate is None or sample_size <= 0.0:
        return None
    denominator = 1.0 + (z * z / sample_size)
    center = success_rate + (z * z / (2.0 * sample_size))
    margin = z * sqrt((success_rate * (1.0 - success_rate) + (z * z / (4.0 * sample_size))) / sample_size)
    return max(0.0, (center - margin) / denominator)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _is_fresh(observed_at: str, as_of: datetime, freshness_days: int) -> bool:
    observed = _parse_time(observed_at)
    if observed is None:
        return False
    age_seconds = (as_of - observed).total_seconds()
    return 0 <= age_seconds <= max(0, freshness_days) * 24 * 60 * 60


def _critical_failure(evidence: OutcomeEvidence) -> bool:
    return evidence.safety_score is not None and evidence.safety_score < 0.5


def _aggregation_credit(evidence: OutcomeEvidence, report: dict[str, Any]) -> bool:
    return (
        evidence.status == "verified"
        and report["independent_verifier"]
        and report["receipt_provenance_verified"]
        and evidence.safety_score is not None
        and evidence.safety_score >= 0.95
    )


def _confidence_grade(sample_count: int, effective_sample_size: float, lower_bound: float | None, critical_failure_count: int) -> str:
    if critical_failure_count:
        return "quarantine"
    if sample_count >= 10 and effective_sample_size >= 8 and lower_bound is not None and lower_bound >= 0.7:
        return "high"
    if sample_count >= 5 and effective_sample_size >= 4 and lower_bound is not None and lower_bound >= 0.5:
        return "moderate"
    if sample_count > 0:
        return "low"
    return "none"


def _summary_int(summary: dict[str, Any], field_name: str, issues: list[dict[str, str]]) -> int:
    value = summary.get(field_name)
    if isinstance(value, bool):
        issues.append({"code": "invalid_summary_metric", "message": f"{field_name} must be a non-negative integer"})
        return 0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        issues.append({"code": "invalid_summary_metric", "message": f"{field_name} must be a non-negative integer"})
        return 0
    if not math.isfinite(numeric) or numeric < 0 or int(numeric) != numeric:
        issues.append({"code": "invalid_summary_metric", "message": f"{field_name} must be a non-negative integer"})
        return 0
    return int(numeric)


def _summary_score(summary: dict[str, Any], field_name: str, issues: list[dict[str, str]]) -> float:
    value = summary.get(field_name)
    if isinstance(value, bool):
        issues.append({"code": "invalid_summary_metric", "message": f"{field_name} must be a finite score"})
        return 0.0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        issues.append({"code": "invalid_summary_metric", "message": f"{field_name} must be a finite score"})
        return 0.0
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        issues.append({"code": "invalid_summary_metric", "message": f"{field_name} must be a finite score"})
        return 0.0
    return numeric


def _summary_optional_score(summary: dict[str, Any], field_name: str, issues: list[dict[str, str]]) -> float | None:
    if summary.get(field_name) is None:
        return None
    return _summary_score(summary, field_name, issues)
