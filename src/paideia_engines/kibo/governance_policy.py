from __future__ import annotations

from typing import Any

from .contracts import ReuseDecision, TaskFingerprint


GOVERNANCE_SCHEMA = "paideia-kibo-governance-review/v1"


def evaluate_kibo_governance(
    decision: ReuseDecision,
    *,
    task: TaskFingerprint | None = None,
) -> dict[str, Any]:
    blocked_reasons: list[str] = []
    if decision.reuse_mode == "direct_reuse" and (task and task.risk_level == "high"):
        if not decision.pattern_id:
            blocked_reasons.append("high_risk_direct_reuse_forbidden")
        if decision.pattern_id and not decision.field_validated:
            blocked_reasons.append("high_risk_pattern_requires_field_validation")
        if "validation_failure:self_critic_gate" in decision.llm_required_parts:
            blocked_reasons.append("self_critic_gate_required")
    if decision.reuse_mode == "quarantine_required":
        blocked_reasons.append("quarantine_required")
    if decision.pattern_status == "quarantined":
        blocked_reasons.append("quarantined_pattern_forbidden")
    if decision.failure_warnings and decision.reuse_mode == "direct_reuse":
        blocked_reasons.append("failure_memory_blocks_direct_reuse")
    if "validation_failure" in decision.llm_required_parts and decision.reuse_mode == "direct_reuse":
        blocked_reasons.append("validation_required_before_direct_reuse")
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
            "high_risk_direct_reuse_allowed": "field_validated_pattern_with_critic_only",
        },
    }
