from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .contracts import KiboRecord, ReuseDecision, TaskFingerprint


APPROVED_STATUSES = {"promoted", "verified", "reviewed", "approved", "active"}
HIGH_WEAKNESS_THRESHOLD = 0.75


def _tokens(value: Any) -> set[str]:
    if isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    elif isinstance(value, (list, tuple, set)):
        text = " ".join(str(item) for item in value)
    else:
        text = str(value or "")
    return {token.casefold() for token in re.findall(r"[0-9A-Za-z가-힣_]+", text)}


def _domain_score(task_domain: str, record_domain: str) -> float:
    if task_domain == record_domain:
        return 1.0
    compatible_sets = [
        {"investment_research", "securities_research", "valuation"},
        {"software_agent_engineering", "software", "coding"},
    ]
    return 0.7 if any({task_domain, record_domain} <= item for item in compatible_sets) else 0.0


def _overlap(required: tuple[str, ...], record: KiboRecord) -> float:
    if not required:
        return 1.0
    haystack = _tokens([record.required_inputs, record.reusable_logic, record.problem_signature])
    matched = [item for item in required if item.casefold() in haystack or item in record.required_inputs]
    return len(matched) / len(required)


def score_reuse_candidate(task: TaskFingerprint, record: KiboRecord) -> dict[str, Any]:
    domain = _domain_score(task.domain, record.domain)
    task_type = 1.0 if task.task_type == record.task_type else 0.4
    capability = _overlap(task.required_capabilities, record)
    success = record.success_score / 100
    style = 0.5 if not task.user_style_markers else _overlap(task.user_style_markers, record)
    risk_penalty = 0.65 if task.risk_level == "high" else 0.25 if task.risk_level == "medium" else 0.0
    freshness_penalty = 0.4 if task.freshness_required and "fresh_external_data" not in record.required_inputs else 0.0
    score = (
        0.30 * domain
        + 0.25 * task_type
        + 0.20 * capability
        + 0.15 * success
        + 0.10 * style
        - 0.20 * risk_penalty
        - 0.20 * freshness_penalty
    )
    return {
        "record": record,
        "reuse_score": max(0.0, min(1.0, score)),
        "domain_score": domain,
        "task_type_score": task_type,
        "capability_overlap": capability,
        "success_score": success,
        "risk_penalty": risk_penalty,
        "freshness_penalty": freshness_penalty,
    }


def reuse_mode(score: float, *, risk_level: str) -> str:
    if score >= 0.85 and risk_level != "high":
        return "direct_reuse"
    if score >= 0.65:
        return "partial_reuse"
    if score >= 0.45:
        return "reference_only"
    return "reject_and_solve_fresh"


def decide_reuse(
    task: TaskFingerprint,
    records: list[KiboRecord],
    *,
    weakness_records: list[Any] | tuple[Any, ...] = (),
) -> ReuseDecision:
    scored = [
        score_reuse_candidate(task, record)
        for record in records
        if record.promotion_status.casefold() in APPROVED_STATUSES
    ]
    scored.sort(key=lambda item: item["reuse_score"], reverse=True)
    if not scored:
        return ReuseDecision(
            decision_id="reuse-" + hashlib.sha256(task.task_id.encode("utf-8")).hexdigest()[:12],
            task_id=task.task_id,
            selected_kibo_ids=(),
            similarity_score=0.0,
            confidence_score=0.0,
            risk_score=1.0 if task.risk_level == "high" else 0.5,
            reuse_mode="reject_and_solve_fresh",
            llm_required_parts=("novel_case",),
            reason="no_reviewed_kibo_available",
        )
    top = scored[0]
    mode = reuse_mode(float(top["reuse_score"]), risk_level=task.risk_level)
    llm_parts = []
    active_weaknesses = [
        weakness for weakness in weakness_records if _weakness_applies_to_task(weakness, task)
    ]
    weakness_blocks = any(
        _weakness_severity(weakness) >= HIGH_WEAKNESS_THRESHOLD or _weakness_recurrence(weakness) >= 3
        for weakness in active_weaknesses
    )
    if weakness_blocks and mode == "direct_reuse":
        mode = "reference_only"
        llm_parts.append("validation_failure:active_weakness")
    if task.freshness_required:
        llm_parts.append("fresh_external_data")
    if task.risk_level == "high":
        llm_parts.append("validation_failure")
    if mode == "reject_and_solve_fresh":
        llm_parts.append("novel_case")
    return ReuseDecision(
        decision_id="reuse-" + hashlib.sha256((task.task_id + top["record"].kibo_id).encode("utf-8")).hexdigest()[:12],
        task_id=task.task_id,
        selected_kibo_ids=(top["record"].kibo_id,) if mode != "reject_and_solve_fresh" else (),
        similarity_score=round(float(top["reuse_score"]), 4),
        confidence_score=round(max(0.0, float(top["reuse_score"]) - (0.1 if task.freshness_required else 0.0)), 4),
        risk_score=1.0 if task.risk_level == "high" else 0.5 if task.risk_level == "medium" else 0.1,
        reuse_mode=mode,
        llm_required_parts=tuple(dict.fromkeys(llm_parts)),
        reason=_decision_reason(task, top["reuse_score"], weakness_blocks),
        failure_warnings=tuple(
            f"active_weakness:{_weakness_id(weakness) or _weakness_skill(weakness)}"
            for weakness in active_weaknesses
        ),
    )


def _decision_reason(task: TaskFingerprint, score: float, weakness_blocks: bool) -> str:
    if weakness_blocks:
        return "active_weakness_blocks_direct_reuse"
    if task.risk_level == "high" and score >= 0.85:
        return "high_risk_direct_reuse_blocked"
    return "scored_by_reuse_formula"


def _weakness_applies_to_task(weakness: Any, task: TaskFingerprint) -> bool:
    owner = str(getattr(weakness, "owner", "") or _mapping_get(weakness, "owner") or "")
    if owner and owner != task.owner:
        return False
    domain = str(getattr(weakness, "domain", "") or _mapping_get(weakness, "domain") or "general")
    if domain not in {"", "general", task.domain}:
        return False
    skill_id = _weakness_skill(weakness)
    task_terms = _tokens(task.required_capabilities + task.constraints + (task.intent, task.task_type))
    return not skill_id or skill_id.casefold() in task_terms


def _weakness_skill(weakness: Any) -> str:
    return str(getattr(weakness, "skill_id", "") or _mapping_get(weakness, "skill_id") or "")


def _weakness_id(weakness: Any) -> str:
    return str(getattr(weakness, "weakness_id", "") or _mapping_get(weakness, "weakness_id") or "")


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
