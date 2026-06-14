from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ReviewLabel:
    score: int
    status: str
    reviewed_by: str
    notes: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.score, bool) or not isinstance(self.score, int):
            raise TypeError("score must be an integer.")
        if not 0 <= self.score <= 100:
            raise ValueError("score must be between 0 and 100.")
        if not isinstance(self.status, str):
            raise TypeError("status must be a string.")
        if not self.status.strip():
            raise ValueError("status must be a non-empty string.")
        if self.status != self.status.strip():
            raise ValueError("status must not contain surrounding whitespace.")
        if not isinstance(self.reviewed_by, str):
            raise TypeError("reviewed_by must be a string.")
        if not self.reviewed_by.strip():
            raise ValueError("reviewed_by must be a non-empty string.")
        if self.reviewed_by != self.reviewed_by.strip():
            raise ValueError("reviewed_by must not contain surrounding whitespace.")
        if not isinstance(self.notes, str):
            raise TypeError("notes must be a string.")

    def is_verified(self, *, minimum_score: int = 80) -> bool:
        return self.score >= minimum_score and self.status in {"verified", "approved", "passed"}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromotionDecision:
    experience_id: str
    status: str
    review: ReviewLabel
    requires_boss_review: bool = False
    reason: str = "verified_high_quality_experience"

    @classmethod
    def from_review(cls, experience_id: str, review: ReviewLabel) -> "PromotionDecision":
        if review.status != "verified" or not review.is_verified():
            raise ValueError("PromotionDecision requires a verified high-quality review label.")
        return cls(experience_id=experience_id, status="promoted", review=review)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["review"] = self.review.to_dict()
        return data


@dataclass(frozen=True)
class QuarantineDecision:
    experience_id: str
    status: str
    review: ReviewLabel
    requires_boss_review: bool = True
    reason: str = "do_not_promote_without_verified_quality_review"

    @classmethod
    def from_review(cls, experience_id: str, review: ReviewLabel) -> "QuarantineDecision":
        return cls(experience_id=experience_id, status="quarantined", review=review)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["review"] = self.review.to_dict()
        return data


@dataclass(frozen=True)
class EngineEvent:
    engine: str
    event_type: str
    subject_id: str
    decision: dict[str, Any] | None = None
    input_refs: list[str] = field(default_factory=list)
    output_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)
    schema: str = "paideia-engine-event/v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "engine": self.engine,
            "event_type": self.event_type,
            "subject_id": self.subject_id,
            "input_refs": list(self.input_refs),
            "output_refs": list(self.output_refs),
            "decision": self.decision or {},
            "created_at": self.created_at,
        }
