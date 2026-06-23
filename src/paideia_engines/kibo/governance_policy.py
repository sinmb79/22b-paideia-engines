from __future__ import annotations

import math
from typing import Any, Iterable

from .contracts import ReuseDecision, TaskFingerprint


GOVERNANCE_SCHEMA = "paideia-kibo-governance-review/v1"
HIGH_WEAKNESS_THRESHOLD = 0.75


def evaluate_kibo_governance(
    decision: ReuseDecision,
    *,
    task: TaskFingerprint | None = None,
    weakness_records: Iterable[Any] = (),
) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    validation_required = any(
        part == "validation_failure" or part.startswith("validation_failure:")
        for part in decision.llm_required_parts
    )
    if decision.reuse_mode == "direct_reuse" and (task and task.risk_level == "high"):
        blocked_reasons.append("high_risk_direct_reuse_forbidden")
    if decision.reuse_mode == "quarantine_required":
        blocked_reasons.append("quarantine_required")
    if decision.pattern_status == "quarantined":
        blocked_reasons.append("quarantined_pattern_forbidden")
    if decision.failure_warnings and decision.reuse_mode == "direct_reuse":
        blocked_reasons.append("failure_memory_blocks_direct_reuse")
    if validation_required and decision.reuse_mode == "direct_reuse":
        blocked_reasons.append("validation_required_before_direct_reuse")
    applicable_weaknesses = [
        weakness for weakness in weakness_records if _weakness_applies_to_task(weakness, task)
    ]
    if decision.reuse_mode == "direct_reuse" and any(
        _weakness_severity(weakness) >= HIGH_WEAKNESS_THRESHOLD or _weakness_recurrence(weakness) >= 3
        for weakness in applicable_weaknesses
    ):
        blocked_reasons.append("active_weakness_blocks_direct_reuse")
    if decision.pattern_status in {"field_validated", "reinforced"} and any(
        _weakness_severity(weakness) >= HIGH_WEAKNESS_THRESHOLD for weakness in applicable_weaknesses
    ):
        blocked_reasons.append("high_severity_weakness_requires_reexam")
    if any(_weakness_recurrence(weakness) >= 3 for weakness in applicable_weaknesses):
        blocked_reasons.append("repeated_weakness_forces_pattern_weakened")
    return {
        "schema": GOVERNANCE_SCHEMA,
        "decision_id": decision.decision_id,
        "task_id": decision.task_id,
        "decision": "blocked" if blocked_reasons else "allowed",
        "blocked_reasons": blocked_reasons,
        "runtime_policy": {
            "reviewable_kibo_only": True,
            "quarantined_records_must_not_influence_runtime": True,
            "hidden_chain_of_thought_reuse": False,
            "pattern_direct_reuse_requires_exam_validation": True,
            "high_risk_direct_reuse_allowed": False,
            "curriculum_remediation_required_before_reinforcement": True,
        },
    }


def _weakness_applies_to_task(weakness: Any, task: TaskFingerprint | None) -> bool:
    if task is None:
        return True
    domain = str(getattr(weakness, "domain", "") or _mapping_get(weakness, "domain") or "general")
    skill_id = str(getattr(weakness, "skill_id", "") or _mapping_get(weakness, "skill_id") or "")
    owner = str(getattr(weakness, "owner", "") or _mapping_get(weakness, "owner") or "")
    if owner and owner != task.owner:
        return False
    if domain not in {"", "general", task.domain}:
        return False
    task_terms = {item.casefold() for item in task.required_capabilities + task.constraints + (task.intent, task.task_type)}
    return not skill_id or skill_id.casefold() in task_terms


def _weakness_severity(weakness: Any) -> float:
    value = getattr(weakness, "severity", None)
    if value is None:
        value = _mapping_get(weakness, "severity")
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(numeric):
        return 0.0
    return max(0.0, min(1.0, numeric))


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
