from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from .contracts import KiboRecord, ReuseDecision


OUTCOME_SCHEMA = "paideia-kibo-outcome-evaluation/v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def evaluate_kibo_outcome(
    decision: ReuseDecision,
    *,
    validation_passed: bool,
    quality_score: int,
    evidence_ref: str,
) -> dict[str, Any]:
    if validation_passed and quality_score >= 80:
        outcome = "success"
    elif validation_passed and quality_score >= 60:
        outcome = "partial_success"
    else:
        outcome = "failure"
    return {
        "schema": OUTCOME_SCHEMA,
        "decision_id": decision.decision_id,
        "task_id": decision.task_id,
        "selected_kibo_ids": list(decision.selected_kibo_ids),
        "outcome": outcome,
        "validation_passed": validation_passed,
        "quality_score": quality_score,
        "evidence_ref": evidence_ref,
        "timestamp": _now(),
        "quarantine_required": outcome == "failure",
    }


def apply_outcome(record: KiboRecord, evaluation: dict[str, Any]) -> KiboRecord:
    outcome = evaluation.get("outcome")
    if outcome == "success":
        return replace(
            record,
            success_score=min(100, record.success_score + 3),
            promotion_status="promoted",
            updated_at=evaluation.get("timestamp", _now()),
            evidence_refs=tuple(dict.fromkeys([*record.evidence_refs, str(evaluation.get("evidence_ref"))])),
        )
    if outcome == "partial_success":
        return replace(
            record,
            success_score=min(100, record.success_score + 1),
            updated_at=evaluation.get("timestamp", _now()),
            failure_modes=tuple(dict.fromkeys([*record.failure_modes, "partial_reuse_caveat_added"])),
            evidence_refs=tuple(dict.fromkeys([*record.evidence_refs, str(evaluation.get("evidence_ref"))])),
        )
    return replace(
        record,
        success_score=max(0, record.success_score - 20),
        promotion_status="quarantine",
        updated_at=evaluation.get("timestamp", _now()),
        failure_modes=tuple(dict.fromkeys([*record.failure_modes, "reuse_failed_validation"])),
        evidence_refs=tuple(dict.fromkeys([*record.evidence_refs, str(evaluation.get("evidence_ref"))])),
    )
