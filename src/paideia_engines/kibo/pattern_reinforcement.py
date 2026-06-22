from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from .contracts import CriticReport, PatternCandidate, PatternExamResult, RealWorldOutcome


PATTERN_REINFORCEMENT_SCHEMA = "paideia-pattern-reinforcement-review/v1"
CRITICAL_FAILURE_TYPES = {
    "freshness_error",
    "domain_mismatch",
    "risk_underestimated",
    "market_regime_shift",
}


def reinforce_pattern(
    pattern: PatternCandidate,
    *,
    exam_results: Iterable[PatternExamResult] = (),
    outcomes: Iterable[RealWorldOutcome] = (),
    critic_reports: Iterable[CriticReport] = (),
    reuse_stability_score: float = 0.5,
) -> dict[str, Any]:
    related_exams = [exam for exam in exam_results if exam.pattern_id == pattern.pattern_id]
    related_outcomes = [outcome for outcome in outcomes if outcome.pattern_id == pattern.pattern_id]
    exam_score = _average([exam.score for exam in related_exams], pattern.exam_score)
    real_world_score = _real_world_score(related_outcomes, pattern.real_world_score)
    feedback_score = _average(
        [outcome.user_feedback_score / 10 for outcome in related_outcomes if outcome.user_feedback_score is not None],
        0.5,
    )
    failure_penalty = _failure_penalty(related_outcomes)
    critic_passed = any(report.pattern_id == pattern.pattern_id and report.pass_gate for report in critic_reports)
    critical_failure = any((outcome.error_type or "") in CRITICAL_FAILURE_TYPES for outcome in related_outcomes)
    reinforcement_score = (
        0.35 * (exam_score or 0.0)
        + 0.40 * (real_world_score or 0.0)
        + 0.15 * feedback_score
        + 0.10 * max(0.0, min(1.0, reuse_stability_score))
        - 0.30 * failure_penalty
    )
    reinforcement_score = max(0.0, min(1.0, reinforcement_score))
    status = _status_for_score(reinforcement_score, critical_failure=critical_failure, critic_passed=critic_passed)
    updated = replace(
        pattern,
        exam_score=exam_score,
        real_world_score=real_world_score,
        reinforcement_score=reinforcement_score,
        status=status,
    )
    return {
        "schema": PATTERN_REINFORCEMENT_SCHEMA,
        "pattern": updated.to_dict(),
        "inputs": {
            "exam_result_count": len(related_exams),
            "real_world_outcome_count": len(related_outcomes),
            "critic_passed": critic_passed,
            "failure_penalty": round(failure_penalty, 4),
        },
    }


def _average(values: list[float], fallback: float | None) -> float | None:
    if not values:
        return fallback
    return sum(values) / len(values)


def _real_world_score(outcomes: list[RealWorldOutcome], fallback: float | None) -> float | None:
    if not outcomes:
        return fallback
    values = [
        outcome.quantitative_result if outcome.quantitative_result is not None else 1.0 if outcome.success else 0.0
        for outcome in outcomes
    ]
    return sum(values) / len(values)


def _failure_penalty(outcomes: list[RealWorldOutcome]) -> float:
    if not outcomes:
        return 0.0
    failures = [outcome for outcome in outcomes if not outcome.success or outcome.error_type]
    penalty = len(failures) / len(outcomes)
    if any((outcome.error_type or "") in CRITICAL_FAILURE_TYPES for outcome in failures):
        penalty += 0.5
    return max(0.0, min(1.0, penalty))


def _status_for_score(score: float, *, critical_failure: bool, critic_passed: bool) -> str:
    if critical_failure:
        return "quarantined"
    if score >= 0.85:
        return "reinforced" if critic_passed else "field_validated"
    if score >= 0.70:
        return "field_validated"
    if score >= 0.55:
        return "exam_validated"
    if score >= 0.40:
        return "draft"
    return "weakened"
