"""Governance engine for local-first safety and review checks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from paideia_engines.contracts import default_local_policy


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


class GovernanceEngine:
    """Validate actions against local-only governance policy."""

    schema = "paideia-governance-engine/v1"

    def __init__(self, policy: dict[str, object] | None = None) -> None:
        self.policy = dict(policy or default_local_policy())
        self.created_at = _utc_now()
        self.reviews = []

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
            "timestamp": self.created_at,
        }
        return board

    def _is_blocked(self, action: str, context: dict[str, Any] | None) -> bool:
        ctx = dict(context or {})
        if ctx.get("contains_private_assets") or ctx.get("private_assets") or ctx.get("private_asset_access"):
            return True
        if ctx.get("external_upload"):
            return True
        action_key = str(action).lower()
        return action_key in _EXPLICITLY_SENSITIVE_ACTIONS

    def review_action(self, action: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        blocked = self._is_blocked(action, context)
        decision = "blocked" if blocked else "allowed"
        requires_boss_review = blocked or action == "memory_promotion"
        review = {
            "schema": "paideia-governance-review/v1",
            "action": action,
            "decision": decision,
            "requires_boss_review": requires_boss_review,
            "timestamp": _utc_now(),
            "policy_version": self.policy.get("schema", "paideia-local-policy/v1"),
            "noted": {
                "private_asset": bool((context or {}).get("contains_private_assets")),
                "external_upload_risk": blocked and str(action).lower() in _EXPLICITLY_SENSITIVE_ACTIONS,
            },
        }
        self.reviews.append(review)
        return review


__all__ = ["GovernanceEngine"]
