"""Governance engine for local-first safety and review checks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from paideia_engines.contracts import default_local_policy


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


_EXPLICITLY_SENSITIVE_ACTIONS = {
    "upload_training_data",
    "upload",
    "external_upload",
    "upload_file",
    "upload_assets",
    "share_data",
    "publish_training_data",
    "send_to_external_service",
}

_BOSS_APPROVAL_REQUIRED_ACTIONS = {
    "credential_use",
    "destructive_filesystem_action",
    "memory_promotion",
    "private_asset_access",
}


class GovernanceEngine:
    """Validate actions against local-only governance policy."""

    schema = "paideia-governance-engine/v1"

    def __init__(self, policy: dict[str, object] | None = None) -> None:
        self.policy = dict(policy or default_local_policy())
        self.created_at = _utc_now()
        self.reviews = []
        self._approval_counter = 0
        self._decision_counter = 0
        self.approval_ledger: dict[str, Any] = {
            "schema": "paideia-governance-approval-ledger/v1",
            "version": 0,
            "approvals": [],
        }
        self.decision_ledger: dict[str, Any] = {
            "schema": "paideia-governance-decision-ledger/v1",
            "version": 0,
            "decisions": [],
        }

    def create_board(self, program_id: str) -> dict[str, Any]:
        committees = ["education_committee", "oversight_committee"]

        board = {
            "schema": "paideia-governance-board/v1",
            "program_id": program_id,
            "committees": committees,
            "boss_review_required_for": [
                "external_upload",
                "private_asset_access",
                "memory_promotion",
                "credential_use",
            ],
            "policy": self.policy,
            "approval_ledger_schema": self.approval_ledger["schema"],
            "decision_ledger_schema": self.decision_ledger["schema"],
            "timestamp": self.created_at,
        }
        return board

    def _next_approval_id(self) -> str:
        self._approval_counter += 1
        return f"governance-approval-{self._approval_counter:04d}"

    def _next_decision_id(self) -> str:
        self._decision_counter += 1
        return f"governance-decision-{self._decision_counter:04d}"

    def _is_blocked(self, action: str, context: dict[str, Any] | None) -> bool:
        ctx = dict(context or {})
        if ctx.get("contains_private_assets") or ctx.get("private_assets") or ctx.get("private_asset_access"):
            return True
        if ctx.get("external_upload"):
            return True
        action_key = str(action).lower()
        return action_key in _EXPLICITLY_SENSITIVE_ACTIONS

    @staticmethod
    def _license_requires_manual_approval(context: dict[str, Any]) -> bool:
        license_tier = str(context.get("license_tier", "")).lower()
        return license_tier in {
            "manual_license_required",
            "login_or_agreement_required",
            "restricted",
            "copyright_review_required",
        }

    @staticmethod
    def _scope_matches(approval: dict[str, Any], context: dict[str, Any]) -> bool:
        scope = dict(approval.get("scope", {}))
        source_id = context.get("source_id")
        intended_use = context.get("intended_use")

        if source_id and scope.get("source_id") not in {None, source_id}:
            return False
        if intended_use and scope.get("allowed_use") not in {None, intended_use}:
            return False
        action = context.get("action")
        if action and scope.get("action") not in {None, action}:
            return False
        return approval.get("status") == "active"

    def _matching_approvals(
        self,
        approval_type: str,
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            approval
            for approval in self.approval_ledger["approvals"]
            if approval.get("approval_type") == approval_type and self._scope_matches(approval, context)
        ]

    def record_approval(
        self,
        *,
        approval_type: str,
        subject_id: str,
        approved_by: str,
        scope: dict[str, Any],
        notes: str = "",
    ) -> dict[str, Any]:
        if not approval_type:
            raise ValueError("approval_type is required.")
        if not subject_id:
            raise ValueError("subject_id is required.")
        if not approved_by:
            raise ValueError("approved_by is required.")

        self.approval_ledger["version"] += 1
        approval = {
            "schema": "paideia-governance-approval/v1",
            "approval_id": self._next_approval_id(),
            "approval_type": approval_type,
            "subject_id": subject_id,
            "approved_by": approved_by,
            "scope": dict(scope),
            "notes": notes,
            "status": "active",
            "ledger_version": self.approval_ledger["version"],
            "timestamp": _utc_now(),
        }
        self.approval_ledger["approvals"].append(approval)
        return approval

    def evaluate_policy(self, action: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = dict(context or {})
        action_key = str(action).lower()
        ctx["action"] = action_key

        matched_rules: list[str] = []
        required_approvals: list[str] = []
        override_allowed = True

        if action_key in _EXPLICITLY_SENSITIVE_ACTIONS or ctx.get("external_upload"):
            matched_rules.append("external_upload_ban")
            required_approvals.append("boss_approval")
            override_allowed = False

        if ctx.get("contains_private_assets") or ctx.get("private_assets") or ctx.get("private_asset_access"):
            matched_rules.append("private_asset_access")
            if "boss_approval" not in required_approvals:
                required_approvals.append("boss_approval")

        if action_key in _BOSS_APPROVAL_REQUIRED_ACTIONS:
            matched_rules.append("risky_permission")
            if "boss_approval" not in required_approvals:
                required_approvals.append("boss_approval")

        if self._license_requires_manual_approval(ctx):
            matched_rules.append("manual_license_required")
            if "license_approval" not in required_approvals:
                required_approvals.append("license_approval")

        approval_records: list[dict[str, Any]] = []
        missing_approvals: list[str] = []
        for approval_type in required_approvals:
            matches = self._matching_approvals(approval_type, ctx)
            if matches:
                approval_records.extend(matches)
            else:
                missing_approvals.append(approval_type)

        if not override_allowed:
            decision = "blocked"
        elif missing_approvals:
            decision = "blocked"
        elif approval_records:
            decision = "allowed_with_approval"
        else:
            decision = "allowed"

        return {
            "schema": "paideia-policy-evaluation/v1",
            "action": action,
            "context": ctx,
            "decision": decision,
            "matched_rules": matched_rules,
            "required_approvals": required_approvals,
            "approval_records": approval_records,
            "missing_approvals": missing_approvals,
            "override_allowed": override_allowed,
            "policy_version": self.policy.get("schema", "paideia-local-policy/v1"),
            "timestamp": _utc_now(),
        }

    def record_committee_decision(
        self,
        *,
        committee: str,
        subject_id: str,
        decision: str,
        reviewers: list[str],
        rationale: str,
    ) -> dict[str, Any]:
        if not committee:
            raise ValueError("committee is required.")
        if not subject_id:
            raise ValueError("subject_id is required.")
        if not decision:
            raise ValueError("decision is required.")
        if not reviewers:
            raise ValueError("reviewers is required.")

        self.decision_ledger["version"] += 1
        record = {
            "schema": "paideia-committee-decision/v1",
            "decision_id": self._next_decision_id(),
            "committee": committee,
            "subject_id": subject_id,
            "decision": decision,
            "reviewers": list(reviewers),
            "rationale": rationale,
            "ledger_version": self.decision_ledger["version"],
            "timestamp": _utc_now(),
        }
        self.decision_ledger["decisions"].append(record)
        return record

    def review_action(self, action: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        policy_evaluation = self.evaluate_policy(action, context)
        blocked = policy_evaluation["decision"] == "blocked"
        decision = "blocked" if blocked else "allowed"
        requires_boss_review = blocked or "boss_approval" in policy_evaluation["required_approvals"]
        review = {
            "schema": "paideia-governance-review/v1",
            "action": action,
            "decision": decision,
            "requires_boss_review": requires_boss_review,
            "timestamp": _utc_now(),
            "policy_version": self.policy.get("schema", "paideia-local-policy/v1"),
            "policy_evaluation": policy_evaluation,
            "noted": {
                "private_asset": bool((context or {}).get("contains_private_assets")),
                "external_upload_risk": blocked and str(action).lower() in _EXPLICITLY_SENSITIVE_ACTIONS,
            },
        }
        self.reviews.append(review)
        return review


__all__ = ["GovernanceEngine"]
