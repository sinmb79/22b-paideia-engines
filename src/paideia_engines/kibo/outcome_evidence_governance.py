from __future__ import annotations

from statistics import mean
from typing import Any

from .contracts_v2 import OutcomeEvidence


INDEPENDENT_VERIFIER_TYPES = {
    "automated_verifier",
    "certified_controller",
    "external_audit",
    "independent_test",
    "independent_verifier",
}
MANUAL_VERIFIER_TYPES = {"", "manual", "none", "self_report", "user", "user_feedback"}


def evaluate_outcome_evidence_v2(evidence: dict[str, Any]) -> dict[str, Any]:
    outcome = OutcomeEvidence.from_dict(evidence)
    issues: list[dict[str, str]] = []
    verifier_type = outcome.verifier_type.casefold()
    independent_verifier = verifier_type in INDEPENDENT_VERIFIER_TYPES
    manual_verifier = verifier_type in MANUAL_VERIFIER_TYPES
    has_receipts = bool(outcome.action_receipt_refs)
    receipt_provenance_verified = _has_receipt_provenance(outcome)
    if outcome.status == "verified" and manual_verifier:
        issues.append({"code": "manual_verifier", "message": "manual outcome evidence cannot receive field validation credit"})
    if outcome.status == "verified" and not independent_verifier:
        issues.append({"code": "non_independent_verifier", "message": "field evidence requires an independent verifier"})
    if outcome.status == "verified" and not has_receipts:
        issues.append({"code": "missing_action_receipt", "message": "verified field evidence requires action receipt provenance"})
    if outcome.status == "verified" and has_receipts and not receipt_provenance_verified:
        issues.append({"code": "receipt_provenance", "message": "action receipt refs require matching provenance artifact hashes"})
    if outcome.status in {"contested", "invalidated", "expired"}:
        issues.append({"code": f"status_{outcome.status}", "message": f"outcome evidence is {outcome.status}"})
    if outcome.status == "verified" and outcome.safety_score is None:
        issues.append({"code": "missing_safety_score", "message": "field evidence requires an explicit safety score"})
    if outcome.safety_score is not None and outcome.safety_score < 0.95:
        issues.append({"code": "safety_score", "message": "safety score below field evidence threshold"})
    if outcome.binary_success is False:
        issues.append({"code": "binary_success", "message": "failed outcome evidence cannot receive field validation credit"})
    field_validation_credit = (
        outcome.status == "verified"
        and independent_verifier
        and receipt_provenance_verified
        and outcome.safety_score is not None
        and outcome.safety_score >= 0.95
        and outcome.binary_success is True
    )
    weight_cap = 1.0 if independent_verifier and receipt_provenance_verified else 0.25
    if outcome.status != "verified":
        weight_cap = 0.0
    evidence_weight = min(weight_cap, _raw_weight(outcome))
    return {
        "schema": "paideia-outcome-evidence-governance/v1",
        "status": "passed" if not issues else "blocked",
        "evidence_id": outcome.evidence_id,
        "pattern_id": outcome.pattern_id,
        "pattern_version": outcome.pattern_version,
        "field_validation_credit": field_validation_credit,
        "independent_verifier": independent_verifier,
        "has_action_receipts": has_receipts,
        "receipt_provenance_verified": receipt_provenance_verified,
        "max_evidence_weight": weight_cap,
        "evidence_weight": round(evidence_weight, 4),
        "issues": issues,
    }


def _raw_weight(outcome: OutcomeEvidence) -> float:
    provenance_confidence = mean([source.confidence for source in outcome.provenance]) if outcome.provenance else 0.0
    difficulty_weight = 0.5 + (0.5 * outcome.task_difficulty)
    return outcome.confidence * provenance_confidence * difficulty_weight


def _has_receipt_provenance(outcome: OutcomeEvidence) -> bool:
    refs = {ref for ref in outcome.action_receipt_refs if ref}
    if not refs:
        return False
    proven_refs = {
        source.source_id
        for source in outcome.provenance
        if source.source_type == "action_receipt" and isinstance(source.artifact_hash, str) and bool(source.artifact_hash)
    }
    return refs.issubset(proven_refs)
