from __future__ import annotations

import hashlib
from typing import Any, Iterable

from .contracts import CurriculumPlan, WeaknessRecord


CURRICULUM_GENERATION_SCHEMA = "paideia-curriculum-generation-report/v1"

LESSON_MAP: dict[str, tuple[str, ...]] = {
    "freshness_gap": ("source_recency_checks", "current_data_verification", "staleness_risk_review"),
    "knowledge_gap": ("core_domain_principles", "case_examples", "boundary_conditions"),
    "reasoning_gap": ("premise_tracking", "evidence_to_claim_mapping", "decision_trace_review"),
    "risk_gap": ("downside_mapping", "failure_pre_mortem", "risk_sizing"),
    "transfer_gap": ("near_transfer_cases", "far_transfer_limits", "domain_boundary_review"),
    "counterargument_gap": ("opposing_case_generation", "assumption_attack", "red_team_summary"),
}

GOAL_MAP: dict[str, tuple[str, ...]] = {
    "macro_regime_analysis": ("yield_curve", "interest_rate_cycles", "liquidity_analysis", "inflation_regimes"),
    "fresh_external_data": ("freshness_window_selection", "source_timestamp_review", "current_data_citation"),
    "risk_assessment": ("downside_risk", "sensitivity_analysis", "loss_scenario_design"),
    "counterargument_review": ("steelman_opposition", "missing_counterevidence", "assumption_register"),
}


def generate_curriculum_plan(
    weakness: WeaknessRecord,
    *,
    related_skills: Iterable[str] = (),
) -> CurriculumPlan:
    goals = _unique(
        (
            weakness.skill_id,
            *GOAL_MAP.get(weakness.skill_id, ()),
            *related_skills,
        )
    )
    lessons = _unique(
        (
            *LESSON_MAP.get(weakness.weakness_type, ("diagnostic_review", "targeted_practice")),
            *GOAL_MAP.get(weakness.skill_id, ()),
        )
    )
    exam_requirements = (
        f"score_at_least_{target_score_for_weakness(weakness):.2f}",
        "include_failure_memory_prevention_rule",
        "pass_transfer_case_without_repeating_trigger",
    )
    return CurriculumPlan(
        curriculum_id=_stable_id("curriculum", weakness.weakness_id, weakness.recurrence_count),
        weakness_id=weakness.weakness_id,
        domain=weakness.domain,
        learning_goals=goals,
        lesson_units=lessons,
        exam_requirements=exam_requirements,
        target_score=target_score_for_weakness(weakness),
    )


def build_curriculum_generation_report(
    weaknesses: Iterable[WeaknessRecord],
    *,
    related_skill_map: dict[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    related_skill_map = related_skill_map or {}
    plans = [
        generate_curriculum_plan(
            weakness,
            related_skills=related_skill_map.get(weakness.skill_id, ()),
        )
        for weakness in weaknesses
    ]
    return {
        "schema": CURRICULUM_GENERATION_SCHEMA,
        "curriculum_count": len(plans),
        "curricula": [plan.to_dict() for plan in plans],
        "policy": {
            "generated_from_weakness_records": True,
            "external_database_required": False,
        },
    }


def target_score_for_weakness(weakness: WeaknessRecord) -> float:
    if weakness.severity >= 0.8 or weakness.recurrence_count >= 3:
        return 0.85
    if weakness.severity >= 0.6:
        return 0.80
    return 0.75


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
