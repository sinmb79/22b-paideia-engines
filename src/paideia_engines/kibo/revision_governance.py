from __future__ import annotations

from typing import Any

from .contracts_v2 import BehavioralExamResult, PatternRevisionProposal


REVISION_GOVERNANCE_SCHEMA = "paideia-pattern-revision-governance/v1"


def evaluate_pattern_revision_v2(
    revision: dict[str, Any],
    *,
    behavioral_exam: dict[str, Any] | None = None,
    shadow_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proposal = PatternRevisionProposal.from_dict(revision)
    issues: list[dict[str, str]] = []
    if proposal.proposed_pattern_version == proposal.from_pattern_version:
        issues.append({"code": "version_lineage", "message": "proposed version must differ from source version"})
    if not _version_advances(proposal.from_pattern_version, proposal.proposed_pattern_version):
        issues.append({"code": "version_downgrade", "message": "proposed version must advance source version"})
    if proposal.status in {"quarantined", "testing", "accepted"} and not proposal.proposed_changes:
        issues.append({"code": "empty_revision", "message": "non-draft revision requires proposed changes"})
    if proposal.status in {"quarantined", "testing", "accepted"} and any(not _valid_change(change) for change in proposal.proposed_changes):
        issues.append({"code": "invalid_change", "message": "revision changes require op and node_id or field"})
    behavioral_passed = _behavioral_exam_passed(proposal, behavioral_exam, issues)
    shadow_passed = _shadow_passed(proposal, shadow_report, issues)
    if proposal.status == "accepted":
        if not behavioral_passed:
            issues.append({"code": "behavioral_exam_required", "message": "accepted revision requires passing behavioral exam"})
        if not shadow_passed:
            issues.append({"code": "shadow_validation_required", "message": "accepted revision requires passing shadow validation"})
    testing_allowed = proposal.status in {"quarantined", "testing"} and bool(proposal.proposed_changes) and not issues
    promotion_allowed = proposal.status == "accepted" and not issues
    return {
        "schema": REVISION_GOVERNANCE_SCHEMA,
        "status": "passed" if not issues else "blocked",
        "revision_id": proposal.revision_id,
        "pattern_id": proposal.pattern_id,
        "from_pattern_version": proposal.from_pattern_version,
        "proposed_pattern_version": proposal.proposed_pattern_version,
        "testing_allowed": testing_allowed,
        "promotion_allowed": promotion_allowed,
        "requires_behavioral_exam": proposal.requires_behavioral_exam,
        "requires_shadow_validation": proposal.requires_shadow_validation,
        "behavioral_exam_passed": behavioral_passed,
        "shadow_validation_passed": shadow_passed,
        "issues": issues,
    }


def _behavioral_exam_passed(
    proposal: PatternRevisionProposal,
    behavioral_exam: dict[str, Any] | None,
    issues: list[dict[str, str]],
) -> bool:
    if not behavioral_exam:
        return False
    exam = BehavioralExamResult.from_dict(behavioral_exam)
    if exam.pattern_id != proposal.pattern_id:
        issues.append({"code": "behavioral_pattern_mismatch", "message": "behavioral exam pattern_id mismatch"})
        return False
    if exam.pattern_version != proposal.proposed_pattern_version:
        issues.append({"code": "behavioral_version_mismatch", "message": "behavioral exam must target proposed version"})
        return False
    if exam.leakage_detected or exam.safety_violation_count:
        issues.append({"code": "behavioral_safety", "message": "behavioral exam has leakage or safety violations"})
        return False
    return bool(exam.passed)


def _shadow_passed(proposal: PatternRevisionProposal, shadow_report: dict[str, Any] | None, issues: list[dict[str, str]]) -> bool:
    if not isinstance(shadow_report, dict):
        return False
    if shadow_report.get("schema") != "paideia-pattern-shadow-validation/v1":
        return False
    if shadow_report.get("revision_id") != proposal.revision_id:
        issues.append({"code": "shadow_revision_mismatch", "message": "shadow report revision_id mismatch"})
        return False
    if shadow_report.get("pattern_id") != proposal.pattern_id:
        issues.append({"code": "shadow_pattern_mismatch", "message": "shadow report pattern_id mismatch"})
        return False
    if shadow_report.get("pattern_version") != proposal.proposed_pattern_version:
        issues.append({"code": "shadow_version_mismatch", "message": "shadow report must target proposed version"})
        return False
    return bool(shadow_report.get("passed") is True and shadow_report.get("regression_detected") is not True)


def _version_advances(from_version: str, proposed_version: str) -> bool:
    from_parts = _version_parts(from_version)
    proposed_parts = _version_parts(proposed_version)
    if from_parts is None or proposed_parts is None:
        return proposed_version != from_version
    return proposed_parts > from_parts


def _version_parts(version: str) -> tuple[int, ...] | None:
    parts = version.split(".")
    if not parts or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _valid_change(change: dict[str, Any]) -> bool:
    if not isinstance(change, dict):
        return False
    if not isinstance(change.get("op"), str) or not change["op"]:
        return False
    return bool(change.get("node_id") or change.get("field"))
