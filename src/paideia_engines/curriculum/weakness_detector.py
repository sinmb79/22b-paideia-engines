from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any, Iterable

from paideia_engines.kibo.contracts import FailureMemory

from .contracts import WeaknessRecord


WEAKNESS_DETECTION_SCHEMA = "paideia-weakness-detection-report/v1"
CURRICULUM_COMPLETION_SCHEMA = "paideia-curriculum-completion/v1"

ERROR_WEAKNESS_MAP: dict[str, tuple[str, str]] = {
    "freshness_error": ("fresh_external_data", "freshness_gap"),
    "macro_ignored": ("macro_regime_analysis", "knowledge_gap"),
    "market_regime_shift": ("macro_regime_analysis", "transfer_gap"),
    "overgeneralization": ("transfer_reasoning", "transfer_gap"),
    "domain_mismatch": ("domain_boundary_detection", "transfer_gap"),
    "risk_underestimated": ("risk_assessment", "risk_gap"),
    "missing_counterargument": ("counterargument_review", "counterargument_gap"),
    "user_style_mismatch": ("user_decision_fit", "reasoning_gap"),
}

SEVERITY_MAP = {
    "low": 0.25,
    "medium": 0.50,
    "high": 0.75,
    "critical": 0.90,
    "catastrophic": 0.95,
    "fatal": 1.00,
}
HIGH_WEAKNESS_THRESHOLD = SEVERITY_MAP["high"]


def detect_weaknesses(
    failures: Iterable[FailureMemory],
    *,
    owner: str = "Boss",
    domain: str = "general",
    existing_weaknesses: Iterable[WeaknessRecord] = (),
) -> list[WeaknessRecord]:
    """Map reviewable failure memories into durable weakness records."""

    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for failure in failures:
        skill_id, weakness_type = weakness_mapping_for_error(failure.error_type)
        key = (owner, domain, skill_id, weakness_type)
        current = grouped.setdefault(
            key,
            {
                "evidence_refs": [],
                "severity": 0.0,
                "recurrence_count": 0,
            },
        )
        current["evidence_refs"].append(failure.failure_id)
        current["severity"] = max(current["severity"], severity_value(failure.severity))
        current["recurrence_count"] += 1

    for weakness in existing_weaknesses:
        key = (weakness.owner, weakness.domain, weakness.skill_id, weakness.weakness_type)
        current = grouped.setdefault(
            key,
            {
                "evidence_refs": [],
                "severity": 0.0,
                "recurrence_count": 0,
            },
        )
        current["evidence_refs"].extend(weakness.evidence_refs)
        current["severity"] = max(current["severity"], weakness.severity)
        current["recurrence_count"] = max(current["recurrence_count"], weakness.recurrence_count)

    records: list[WeaknessRecord] = []
    for (record_owner, record_domain, skill_id, weakness_type), values in sorted(grouped.items()):
        evidence_refs = tuple(dict.fromkeys(str(item) for item in values["evidence_refs"] if str(item)))
        recurrence_count = max(int(values["recurrence_count"]), len(evidence_refs))
        recurrence_boost = min(0.20, 0.05 * max(0, recurrence_count - 1))
        severity = max(0.0, min(1.0, float(values["severity"]) + recurrence_boost))
        records.append(
            WeaknessRecord(
                weakness_id=_stable_id("weakness", record_owner, record_domain, skill_id, weakness_type),
                owner=record_owner,
                domain=record_domain,
                skill_id=skill_id,
                weakness_type=weakness_type,
                evidence_refs=evidence_refs,
                severity=severity,
                recurrence_count=recurrence_count,
            )
        )
    return records


def build_weakness_detection_report(
    failures: Iterable[FailureMemory],
    *,
    owner: str = "Boss",
    domain: str = "general",
    existing_weaknesses: Iterable[WeaknessRecord] = (),
) -> dict[str, Any]:
    weaknesses = detect_weaknesses(
        failures,
        owner=owner,
        domain=domain,
        existing_weaknesses=existing_weaknesses,
    )
    return {
        "schema": WEAKNESS_DETECTION_SCHEMA,
        "owner": owner,
        "domain": domain,
        "weakness_count": len(weaknesses),
        "weaknesses": [weakness.to_dict() for weakness in weaknesses],
        "policy": {
            "failures_are_training_opportunities": True,
            "hidden_chain_of_thought_used": False,
            "local_first_storage": True,
        },
    }


def apply_curriculum_completion(
    weakness: WeaknessRecord,
    *,
    passed: bool,
    score: float,
    target_score: float | None = None,
    evidence_refs: Iterable[str] = (),
) -> dict[str, Any]:
    normalized_score = max(0.0, min(1.0, float(score)))
    target = max(0.0, min(1.0, float(target_score))) if target_score is not None else 0.75
    completion_refs = tuple(str(ref) for ref in evidence_refs if str(ref))
    updated_refs = tuple(dict.fromkeys((*weakness.evidence_refs, *completion_refs)))
    effective_passed = bool(passed and normalized_score >= target)
    if effective_passed:
        reduction = max(0.10, 0.25 * normalized_score)
        updated = replace(
            weakness,
            evidence_refs=updated_refs,
            severity=max(0.0, weakness.severity - reduction),
            recurrence_count=max(0, weakness.recurrence_count - 1),
        )
        action = "weakness_reduced"
    else:
        updated = replace(
            weakness,
            evidence_refs=updated_refs,
            severity=min(1.0, weakness.severity + 0.10),
            recurrence_count=weakness.recurrence_count + 1,
        )
        action = "weakness_increased"
    return {
        "schema": CURRICULUM_COMPLETION_SCHEMA,
        "weakness_id": weakness.weakness_id,
        "passed": passed,
        "effective_passed": effective_passed,
        "score": round(normalized_score, 4),
        "target_score": round(target, 4),
        "evidence_refs": completion_refs,
        "action": action,
        "updated_weakness": updated.to_dict(),
    }


def weakness_mapping_for_error(error_type: str) -> tuple[str, str]:
    normalized = str(error_type or "").casefold()
    if normalized in ERROR_WEAKNESS_MAP:
        return ERROR_WEAKNESS_MAP[normalized]
    if "fresh" in normalized or "stale" in normalized:
        return ("fresh_external_data", "freshness_gap")
    if "risk" in normalized:
        return ("risk_assessment", "risk_gap")
    if "counter" in normalized or "objection" in normalized:
        return ("counterargument_review", "counterargument_gap")
    if "domain" in normalized or "transfer" in normalized:
        return ("transfer_reasoning", "transfer_gap")
    if "knowledge" in normalized or "ignored" in normalized:
        return ("domain_knowledge", "knowledge_gap")
    return ("general_reasoning", "reasoning_gap")


def severity_value(severity: str | float | int) -> float:
    if isinstance(severity, (int, float)) and not isinstance(severity, bool):
        return max(0.0, min(1.0, float(severity)))
    return SEVERITY_MAP.get(str(severity or "medium").casefold(), 0.50)


def weakness_blocks_direct_reuse(weakness: WeaknessRecord) -> bool:
    return weakness.severity >= HIGH_WEAKNESS_THRESHOLD or weakness.recurrence_count >= 3


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
