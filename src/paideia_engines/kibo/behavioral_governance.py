from __future__ import annotations

from typing import Any

from .contracts_v2 import PatternValidationProfile


def evaluate_validation_profile_v2(profile: dict[str, Any], *, risk_level: str = "normal") -> dict[str, Any]:
    validation_profile = PatternValidationProfile.from_dict(profile)
    issues: list[dict[str, str]] = []
    if validation_profile.behavioral_exam_passed and not validation_profile.near_transfer_passed:
        issues.append({"code": "near_transfer", "message": "behavioral pass requires near transfer evidence"})
    if validation_profile.field_validation_passed and not validation_profile.behavioral_exam_passed:
        issues.append({"code": "field_without_behavioral", "message": "field validation cannot precede behavioral validation"})
    if validation_profile.field_validation_passed and not validation_profile.shadow_validation_passed:
        issues.append({"code": "field_without_shadow", "message": "field validation requires shadow validation evidence"})
    if validation_profile.high_risk_eligible and not _strong_reuse_ready(validation_profile):
        issues.append({"code": "high_risk_evidence_required", "message": "high-risk eligibility requires behavioral, transfer, adversarial, shadow, field, and critic evidence"})
    if risk_level.casefold() in {"high", "critical"} and not validation_profile.high_risk_eligible:
        issues.append({"code": "high_risk_eligibility", "message": "high-risk reuse requires high_risk_eligible profile"})
    ceiling = validation_profile_reuse_ceiling_v2(validation_profile)
    if issues and ceiling == "strong_reuse":
        ceiling = "partial_reuse"
    return {
        "schema": "paideia-validation-profile-governance/v1",
        "status": "passed" if not issues else "blocked",
        "pattern_id": validation_profile.pattern_id,
        "pattern_version": validation_profile.pattern_version,
        "reuse_ceiling": ceiling,
        "behavioral_credit": validation_profile.behavioral_exam_passed and not issues,
        "high_risk_allowed": ceiling == "strong_reuse" and validation_profile.high_risk_eligible and not issues,
        "issues": issues,
    }


def validation_profile_reuse_ceiling_v2(profile: PatternValidationProfile) -> str:
    if _strong_reuse_ready(profile):
        return "strong_reuse"
    if profile.behavioral_exam_passed and profile.near_transfer_passed:
        return "partial_reuse"
    if profile.structural_exam_passed:
        return "reference_only"
    return "reject_and_solve_fresh"


def _strong_reuse_ready(profile: PatternValidationProfile) -> bool:
    return (
        profile.field_validation_passed
        and profile.behavioral_exam_passed
        and profile.near_transfer_passed
        and profile.far_transfer_passed
        and profile.adversarial_exam_passed
        and profile.shadow_validation_passed
        and profile.critic_clearance_passed
    )
