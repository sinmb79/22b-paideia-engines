"""Promotion engine for classifying experiences into promoted or quarantined sets."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from paideia_engines.contracts import EngineEvent, ReviewLabel


GOVERNANCE_BLOCKED_PROMOTION = "governance_blocked_promotion"
GOVERNANCE_REVIEW_SCHEMA = "paideia-governance-review/v1"
GOVERNANCE_RECONSIDERATION_ACTION = "memory_promotion"
GOVERNANCE_RECONSIDERATION_USE = "active_memory"
GOVERNANCE_QUARANTINE_REF_KEY = "quarantine_ref"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc_timestamp(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _normalize_review(review: ReviewLabel) -> dict[str, Any]:
    return review.to_dict()


@dataclass(frozen=True)
class ExperienceRecord:
    experience_id: str
    source: str
    event: dict[str, Any]
    review: ReviewLabel

    def to_dict(self) -> dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "source": self.source,
            "event": dict(self.event),
            "review": _normalize_review(self.review),
            "review_status": "active",
        }


class PromotionEngine:
    """Classify experiences by review quality and keep a deterministic ledger."""

    schema = "paideia-promotion-engine/v1"

    def __init__(self, owner: str, minimum_score: int = 80) -> None:
        self.owner = owner
        self.minimum_score = minimum_score
        self._counter = 0
        self.ledger: dict[str, Any] = {
            "schema": "paideia-promotion-ledger/v1",
            "owner": owner,
            "version": 0,
            "promoted_experiences": [],
            "quarantined_experiences": [],
            "history": [],
        }
        self.events: list[dict[str, Any]] = []

    def _next_experience_id(self) -> str:
        self._counter += 1
        return f"{self.owner.replace(':', '_')}-exp-{self._counter:04d}"

    def _next_ledger_version(self) -> int:
        self.ledger["version"] += 1
        return int(self.ledger["version"])

    def _record_event(self, event: EngineEvent) -> None:
        self.events.append(event.to_dict())

    def _append_history(
        self,
        *,
        version: int,
        action: str,
        experience_id: str,
        status: str,
        source: str,
        supersedes: str | None = None,
        notes: str | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "version": version,
            "timestamp": _utc_now(),
            "action": action,
            "experience_id": experience_id,
            "status": status,
            "source": source,
        }
        if supersedes is not None:
            entry["supersedes"] = supersedes
        if notes:
            entry["notes"] = notes
        self.ledger["history"].append(entry)

    @staticmethod
    def _is_verified_and_high_quality(review: ReviewLabel, minimum_score: int) -> bool:
        return review.status == "verified" and review.score >= minimum_score

    @staticmethod
    def _extract_tokens(text: Any) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", str(text).lower())}

    @staticmethod
    def _quarantine_reason(entry: dict[str, Any]) -> str:
        return str(entry.get("decision", {}).get("reason") or entry.get("reason", ""))

    @staticmethod
    def _fresh_governance_error() -> ValueError:
        return ValueError("Governance-blocked quarantine requires a fresh allowed governance decision.")

    @staticmethod
    def _new_quarantine_ref() -> str:
        return f"quarantine-ref-{secrets.token_hex(16)}"

    @staticmethod
    def _approval_record_authorizes_reconsideration(
        record: dict[str, Any],
        *,
        experience_id: Any,
        quarantine_ref: Any,
    ) -> bool:
        scope = record.get("scope")
        return (
            record.get("schema") == "paideia-governance-approval/v1"
            and bool(record.get("approval_id"))
            and record.get("approval_type") == "boss_approval"
            and record.get("status") == "active"
            and record.get("subject_id") == experience_id
            and isinstance(scope, dict)
            and scope.get("action") == GOVERNANCE_RECONSIDERATION_ACTION
            and scope.get("source_id") == experience_id
            and scope.get("allowed_use") == GOVERNANCE_RECONSIDERATION_USE
            and scope.get(GOVERNANCE_QUARANTINE_REF_KEY) == quarantine_ref
        )

    @staticmethod
    def _approval_record_is_in_ledger(
        record: dict[str, Any],
        governance_approval_ledger: dict[str, Any] | None,
    ) -> bool:
        if not isinstance(governance_approval_ledger, dict):
            return False
        if governance_approval_ledger.get("schema") != "paideia-governance-approval-ledger/v1":
            return False
        approvals = governance_approval_ledger.get("approvals")
        if not isinstance(approvals, list):
            return False

        identity_keys = (
            "schema",
            "approval_id",
            "approval_type",
            "subject_id",
            "approved_by",
            "status",
            "ledger_version",
            "timestamp",
        )
        for ledger_record in approvals:
            if not isinstance(ledger_record, dict):
                continue
            identity_matches = all(ledger_record.get(key) == record.get(key) for key in identity_keys)
            if identity_matches and ledger_record.get("scope") == record.get("scope"):
                return True
        return False

    def _validate_reconsideration_governance_review(
        self,
        original: dict[str, Any],
        governance_review: dict[str, Any] | None,
        governance_approval_ledger: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(governance_review, dict):
            raise self._fresh_governance_error()
        if governance_review.get("schema") != GOVERNANCE_REVIEW_SCHEMA:
            raise self._fresh_governance_error()
        if governance_review.get("decision") != "allowed":
            raise self._fresh_governance_error()
        if str(governance_review.get("action", "")).lower() != GOVERNANCE_RECONSIDERATION_ACTION:
            raise self._fresh_governance_error()

        policy_evaluation = governance_review.get("policy_evaluation")
        if not isinstance(policy_evaluation, dict):
            raise self._fresh_governance_error()
        if policy_evaluation.get("decision") not in {"allowed", "allowed_with_approval"}:
            raise self._fresh_governance_error()
        missing_approvals = policy_evaluation.get("missing_approvals")
        if missing_approvals not in ([], ()):
            raise self._fresh_governance_error()
        if policy_evaluation.get("override_allowed") is not True:
            raise self._fresh_governance_error()

        context = policy_evaluation.get("context")
        if not isinstance(context, dict):
            raise self._fresh_governance_error()
        if context.get("source_id") != original.get("experience_id"):
            raise self._fresh_governance_error()
        if context.get("intended_use") != GOVERNANCE_RECONSIDERATION_USE:
            raise self._fresh_governance_error()
        if str(context.get("action", "")).lower() != GOVERNANCE_RECONSIDERATION_ACTION:
            raise self._fresh_governance_error()
        quarantine_ref = original.get("decision", {}).get(GOVERNANCE_QUARANTINE_REF_KEY)
        if not quarantine_ref:
            raise self._fresh_governance_error()
        if context.get(GOVERNANCE_QUARANTINE_REF_KEY) != quarantine_ref:
            raise self._fresh_governance_error()

        approval_records = policy_evaluation.get("approval_records")
        if not isinstance(approval_records, list) or not any(
            isinstance(record, dict)
            and self._approval_record_authorizes_reconsideration(
                record,
                experience_id=original.get("experience_id"),
                quarantine_ref=quarantine_ref,
            )
            and self._approval_record_is_in_ledger(record, governance_approval_ledger)
            for record in approval_records
        ):
            raise self._fresh_governance_error()

        review_timestamp = _parse_utc_timestamp(governance_review.get("timestamp"))
        original_timestamp = _parse_utc_timestamp(original.get("timestamp") or original.get("decision", {}).get("timestamp"))
        if review_timestamp is None:
            raise self._fresh_governance_error()
        if original_timestamp is not None and review_timestamp < original_timestamp:
            raise self._fresh_governance_error()

        return dict(governance_review)

    def record_experience(
        self,
        source: str,
        event: dict[str, Any],
        review: ReviewLabel,
        *,
        quarantine_reason: str | None = None,
    ) -> dict[str, Any]:
        experience_id = self._next_experience_id()
        ledger_version = self._next_ledger_version()
        timestamp = _utc_now()
        record = ExperienceRecord(experience_id=experience_id, source=source, event=event, review=review)
        must_quarantine = quarantine_reason is not None

        if not must_quarantine and self._is_verified_and_high_quality(review, self.minimum_score):
            decision = {
                "experience_id": experience_id,
                "status": "promoted",
                "ledger_version": ledger_version,
                "review": _normalize_review(review),
                "requires_boss_review": False,
                "reason": "verified_high_quality_experience",
                "timestamp": timestamp,
            }
            promoted_entry = record.to_dict()
            promoted_entry.update({"version": ledger_version, "timestamp": timestamp, "decision": decision})
            self.ledger["promoted_experiences"].append(promoted_entry)
        else:
            decision = {
                "experience_id": experience_id,
                "status": "quarantined",
                "ledger_version": ledger_version,
                "review": _normalize_review(review),
                "requires_boss_review": True,
                "reason": quarantine_reason or "do_not_promote_without_verified_quality_review",
                "flags": ["needs_human_review", "do_not_promote"],
                "timestamp": timestamp,
            }
            if quarantine_reason == GOVERNANCE_BLOCKED_PROMOTION:
                decision[GOVERNANCE_QUARANTINE_REF_KEY] = self._new_quarantine_ref()
            quarantined_entry = record.to_dict()
            quarantined_entry.update(
                {
                    "version": ledger_version,
                    "timestamp": timestamp,
                    "flags": ["needs_human_review", "do_not_promote"],
                    "decision": decision,
                }
            )
            self.ledger["quarantined_experiences"].append(quarantined_entry)

        self._append_history(
            version=ledger_version,
            action="record_experience",
            experience_id=experience_id,
            status=decision["status"],
            source=source,
        )
        self._record_event(
            EngineEvent(
                engine="promotion",
                event_type="experience.recorded",
                subject_id=experience_id,
                decision=decision,
                input_refs=[source],
                output_refs=[decision["status"]],
            )
        )
        return {
            "schema": "paideia-promotion-decision/v1",
            "owner": self.owner,
            "timestamp": timestamp,
            **decision,
        }

    def reconsider_quarantined(
        self,
        experience_id: str,
        *,
        review: ReviewLabel,
        notes: str,
        governance_review: dict[str, Any] | None = None,
        governance_approval_ledger: dict[str, Any] | None = None,
        governance_decision: str | None = None,
    ) -> dict[str, Any]:
        original = self._find_entry("quarantined_experiences", experience_id)
        if original is None:
            raise KeyError(f"Unknown quarantined experience_id: {experience_id}")
        if original.get("review_status") == "superseded":
            raise ValueError(f"Quarantined experience is already superseded: {experience_id}")

        allowed_governance_review = None
        original_reason = self._quarantine_reason(original)
        if original_reason == GOVERNANCE_BLOCKED_PROMOTION:
            if governance_decision is not None and governance_review is None:
                raise ValueError(
                    "Governance-blocked quarantine requires a fresh allowed governance review payload, "
                    "not a decision string."
                )
            allowed_governance_review = self._validate_reconsideration_governance_review(
                original,
                governance_review,
                governance_approval_ledger,
            )

        if not self._is_verified_and_high_quality(review, self.minimum_score):
            ledger_version = self._next_ledger_version()
            decision = {
                "experience_id": experience_id,
                "status": "quarantined",
                "ledger_version": ledger_version,
                "review": _normalize_review(review),
                "requires_boss_review": True,
                "reason": "reconsideration_failed_verified_quality_gate",
                "flags": ["needs_human_review", "do_not_promote"],
                "notes": notes,
            }
            self._append_history(
                version=ledger_version,
                action="reconsider_quarantined",
                experience_id=experience_id,
                status="quarantined",
                source="quarantine_reconsideration",
                notes=notes,
            )
            return {
                "schema": "paideia-promotion-decision/v1",
                "owner": self.owner,
                "timestamp": _utc_now(),
                **decision,
            }

        original["review_status"] = "superseded"
        new_experience_id = self._next_experience_id()
        ledger_version = self._next_ledger_version()
        decision = {
            "experience_id": new_experience_id,
            "status": "promoted",
            "ledger_version": ledger_version,
            "review": _normalize_review(review),
            "requires_boss_review": False,
            "reason": "verified_quarantine_reconsideration",
            "supersedes": experience_id,
            "notes": notes,
        }
        if allowed_governance_review is not None:
            decision["governance_review"] = allowed_governance_review
        promoted_entry = {
            "experience_id": new_experience_id,
            "source": "quarantine_reconsideration",
            "event": dict(original.get("event", {})),
            "review": _normalize_review(review),
            "review_status": "active",
            "version": ledger_version,
            "supersedes": experience_id,
            "notes": notes,
            "decision": decision,
        }
        self.ledger["promoted_experiences"].append(promoted_entry)
        self._append_history(
            version=ledger_version,
            action="reconsider_quarantined",
            experience_id=new_experience_id,
            status="promoted",
            source="quarantine_reconsideration",
            supersedes=experience_id,
            notes=notes,
        )
        self._record_event(
            EngineEvent(
                engine="promotion",
                event_type="experience.reconsidered",
                subject_id=new_experience_id,
                decision=decision,
                input_refs=[experience_id],
                output_refs=["promoted"],
            )
        )
        return {
            "schema": "paideia-promotion-decision/v1",
            "owner": self.owner,
            "timestamp": _utc_now(),
            **decision,
        }

    def supersede_promoted(
        self,
        experience_id: str,
        *,
        event: dict[str, Any],
        review: ReviewLabel,
        reason: str,
    ) -> dict[str, Any]:
        original = self._find_entry("promoted_experiences", experience_id)
        if original is None:
            raise KeyError(f"Unknown promoted experience_id: {experience_id}")
        if original.get("review_status") == "superseded":
            raise ValueError(f"Promoted experience is already superseded: {experience_id}")
        if not self._is_verified_and_high_quality(review, self.minimum_score):
            raise ValueError("A promoted replacement requires verified high-quality review.")

        original["review_status"] = "superseded"
        new_experience_id = self._next_experience_id()
        ledger_version = self._next_ledger_version()
        decision = {
            "experience_id": new_experience_id,
            "status": "promoted",
            "ledger_version": ledger_version,
            "review": _normalize_review(review),
            "requires_boss_review": False,
            "reason": reason,
            "supersedes": experience_id,
        }
        promoted_entry = {
            "experience_id": new_experience_id,
            "source": original.get("source", "promotion_supersession"),
            "event": dict(event),
            "review": _normalize_review(review),
            "review_status": "active",
            "version": ledger_version,
            "supersedes": experience_id,
            "decision": decision,
        }
        self.ledger["promoted_experiences"].append(promoted_entry)
        self._append_history(
            version=ledger_version,
            action="supersede_promoted",
            experience_id=new_experience_id,
            status="promoted",
            source=str(promoted_entry["source"]),
            supersedes=experience_id,
            notes=reason,
        )
        self._record_event(
            EngineEvent(
                engine="promotion",
                event_type="experience.superseded",
                subject_id=new_experience_id,
                decision=decision,
                input_refs=[experience_id],
                output_refs=["promoted"],
            )
        )
        return {
            "schema": "paideia-promotion-decision/v1",
            "owner": self.owner,
            "timestamp": _utc_now(),
            **decision,
        }

    def _find_entry(self, bucket: str, experience_id: str) -> dict[str, Any] | None:
        for entry in self.ledger[bucket]:
            if entry.get("experience_id") == experience_id:
                return entry
        return None

    def route_active_memory(self, query: str, *, max_entries: int = 5) -> dict[str, Any]:
        selected = []
        query_tokens = self._extract_tokens(query)

        for item in self.ledger["promoted_experiences"]:
            if item.get("review_status", "active") != "active":
                continue
            if not query_tokens:
                is_match = True
            else:
                source = self._extract_tokens(item.get("source", ""))
                summary = self._extract_tokens(item.get("event", {}).get("summary", ""))
                skills = self._extract_tokens(item.get("event", {}).get("skills", ""))
                is_match = bool(query_tokens & (source | summary | skills))
            if is_match:
                selected.append(item)
            if len(selected) >= max_entries:
                break

        return {
            "schema": "paideia-active-memory-route/v1",
            "owner": self.owner,
            "query": str(query),
            "selected": selected,
            "quarantined_experiences": "excluded",
            "total_promoted": len(self.ledger["promoted_experiences"]),
            "matched": len(selected),
        }


__all__ = ["PromotionEngine", "ExperienceRecord"]
