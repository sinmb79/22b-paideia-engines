"""Promotion engine for classifying experiences into promoted or quarantined sets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from paideia_engines.contracts import EngineEvent, ReviewLabel


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
            "promoted_experiences": [],
            "quarantined_experiences": [],
        }
        self.events: list[dict[str, Any]] = []

    def _next_experience_id(self) -> str:
        self._counter += 1
        return f"{self.owner.replace(':', '_')}-exp-{self._counter:04d}"

    def _record_event(self, event: EngineEvent) -> None:
        self.events.append(event.to_dict())

    @staticmethod
    def _is_verified_and_high_quality(review: ReviewLabel, minimum_score: int) -> bool:
        return review.status == "verified" and review.score >= minimum_score

    @staticmethod
    def _extract_tokens(text: Any) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", str(text).lower())}

    def record_experience(
        self,
        source: str,
        event: dict[str, Any],
        review: ReviewLabel,
    ) -> dict[str, Any]:
        experience_id = self._next_experience_id()
        record = ExperienceRecord(experience_id=experience_id, source=source, event=event, review=review)

        if self._is_verified_and_high_quality(review, self.minimum_score):
            decision = {
                "experience_id": experience_id,
                "status": "promoted",
                "review": _normalize_review(review),
                "requires_boss_review": False,
                "reason": "verified_high_quality_experience",
            }
            promoted_entry = record.to_dict()
            promoted_entry["decision"] = decision
            self.ledger["promoted_experiences"].append(promoted_entry)
        else:
            decision = {
                "experience_id": experience_id,
                "status": "quarantined",
                "review": _normalize_review(review),
                "requires_boss_review": True,
                "reason": "do_not_promote_without_verified_quality_review",
                "flags": ["needs_human_review", "do_not_promote"],
            }
            quarantined_entry = record.to_dict()
            quarantined_entry.update({"flags": ["needs_human_review", "do_not_promote"]})
            self.ledger["quarantined_experiences"].append(quarantined_entry)

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
            "timestamp": _utc_now(),
            **decision,
        }

    def route_active_memory(self, query: str, *, max_entries: int = 5) -> dict[str, Any]:
        selected = []
        query_tokens = self._extract_tokens(query)

        for item in self.ledger["promoted_experiences"]:
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
