from __future__ import annotations

from dataclasses import replace
from typing import Any, Iterable

from .contracts import CriticReport, PatternCandidate, PatternExamResult, RealWorldOutcome


PATTERN_REINFORCEMENT_SCHEMA = "paideia-pattern-reinforcement-review/v1"
HIGH_WEAKNESS_THRESHOLD = 0.75
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
    weakness_records: Iterable[Any] = (),
    curriculum_remediated: bool = False,
    remediated_weakness_ids: Iterable[str] = (),
) -> dict[str, Any]:
    related_exams = [exam for exam in exam_results if exam.pattern_id == pattern.pattern_id]
    related_outcomes = [outcome for outcome in outcomes if outcome.pattern_id == pattern.pattern_id]
    exam_failed = any((not exam.passed) or bool(exam.mistakes) for exam in related_exams)
    exam_score = _average(
        [exam.score if exam.passed and not exam.mistakes else 0.0 for exam in related_exams],
        pattern.exam_score,
    )
    real_world_score = _real_world_score(related_outcomes, pattern.real_world_score)
    feedback_score = _average(
        [outcome.user_feedback_score / 10 for outcome in related_outcomes if outcome.user_feedback_score is not None],
        0.5,
    )
    failure_penalty = _failure_penalty(related_outcomes)
    critic_passed = any(report.pattern_id == pattern.pattern_id and report.pass_gate for report in critic_reports)
    critical_failure = any((outcome.error_type or "").casefold() in CRITICAL_FAILURE_TYPES for outcome in related_outcomes)
    reinforcement_score = (
        0.35 * (exam_score or 0.0)
        + 0.40 * (real_world_score or 0.0)
        + 0.15 * feedback_score
        + 0.10 * max(0.0, min(1.0, reuse_stability_score))
        - 0.30 * failure_penalty
    )
    reinforcement_score = max(0.0, min(1.0, reinforcement_score))
    status = _status_for_score(
        reinforcement_score,
        critical_failure=critical_failure,
        critic_passed=critic_passed,
        current_status=pattern.status,
        exam_failed=exam_failed,
    )
    active_weaknesses = [
        weakness for weakness in weakness_records if _weakness_applies_to_pattern(weakness, pattern)
    ]
    remediated_ids = {str(item) for item in remediated_weakness_ids if str(item)}
    unremediated_weaknesses = [
        weakness for weakness in active_weaknesses if _weakness_id(weakness) not in remediated_ids
    ]
    if unremediated_weaknesses:
        status = _status_after_active_weakness(status, unremediated_weaknesses)
        reinforcement_score = min(
            reinforcement_score,
            _score_cap_after_active_weakness(unremediated_weaknesses),
        )
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
            "active_weakness_count": len(active_weaknesses),
            "curriculum_remediated": curriculum_remediated,
            "remediated_weakness_ids": tuple(sorted(remediated_ids)),
            "unremediated_weakness_count": len(unremediated_weaknesses),
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
    if any((outcome.error_type or "").casefold() in CRITICAL_FAILURE_TYPES for outcome in failures):
        penalty += 0.5
    return max(0.0, min(1.0, penalty))


def _status_for_score(
    score: float,
    *,
    critical_failure: bool,
    critic_passed: bool,
    current_status: str,
    exam_failed: bool = False,
) -> str:
    if current_status == "quarantined":
        return "quarantined"
    if critical_failure:
        return "quarantined"
    if exam_failed:
        return "draft" if score >= 0.40 else "weakened"
    if score >= 0.85:
        return "reinforced" if critic_passed else "field_validated"
    if score >= 0.70:
        return "field_validated"
    if score >= 0.55:
        return "exam_validated"
    if score >= 0.40:
        return "draft"
    return "weakened"


def _status_after_active_weakness(status: str, weakness_records: list[Any]) -> str:
    if status == "quarantined":
        return status
    if any(_weakness_recurrence(weakness) >= 3 for weakness in weakness_records):
        return "weakened"
    if any(_weakness_severity(weakness) >= HIGH_WEAKNESS_THRESHOLD for weakness in weakness_records):
        return "exam_validated" if status in {"field_validated", "reinforced"} else status
    if status == "reinforced":
        return "field_validated"
    return status


def _score_cap_after_active_weakness(weakness_records: list[Any]) -> float:
    if any(_weakness_recurrence(weakness) >= 3 for weakness in weakness_records):
        return 0.39
    if any(_weakness_severity(weakness) >= HIGH_WEAKNESS_THRESHOLD for weakness in weakness_records):
        return 0.69
    return 0.69


def _weakness_applies_to_pattern(weakness: Any, pattern: PatternCandidate) -> bool:
    domain = str(getattr(weakness, "domain", None) or _mapping_get(weakness, "domain") or "general")
    skill_id = str(getattr(weakness, "skill_id", None) or _mapping_get(weakness, "skill_id") or "")
    owner = str(getattr(weakness, "owner", None) or _mapping_get(weakness, "owner") or "")
    if owner and owner != pattern.owner:
        return False
    if domain not in {"", "general", pattern.domain}:
        return False
    pattern_terms = {
        item.casefold()
        for item in pattern.required_conditions
        + pattern.abstract_strategy
        + pattern.known_failure_modes
        + (pattern.task_family,)
    }
    return not skill_id or skill_id.casefold() in pattern_terms


def _weakness_id(weakness: Any) -> str:
    return str(getattr(weakness, "weakness_id", None) or _mapping_get(weakness, "weakness_id") or "")


def _weakness_severity(weakness: Any) -> float:
    value = getattr(weakness, "severity", None)
    if value is None:
        value = _mapping_get(weakness, "severity")
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _weakness_recurrence(weakness: Any) -> int:
    value = getattr(weakness, "recurrence_count", None)
    if value is None:
        value = _mapping_get(weakness, "recurrence_count")
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _mapping_get(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None
