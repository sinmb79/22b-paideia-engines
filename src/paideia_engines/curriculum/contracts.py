from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


WEAKNESS_RECORD_SCHEMA = "paideia-weakness-record/v1"
CURRICULUM_PLAN_SCHEMA = "paideia-curriculum-plan/v1"
ADAPTIVE_EXAM_SCHEMA = "paideia-adaptive-exam/v1"

WEAKNESS_TYPES = {
    "knowledge_gap",
    "reasoning_gap",
    "risk_gap",
    "transfer_gap",
    "freshness_gap",
    "counterargument_gap",
}


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric if math.isfinite(numeric) else default


def _int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp_score(value: Any, default: float = 0.0) -> float:
    return max(0.0, min(1.0, _float(value, default)))


@dataclass(frozen=True)
class WeaknessRecord:
    weakness_id: str
    owner: str
    domain: str
    skill_id: str
    weakness_type: str
    evidence_refs: tuple[str, ...]
    severity: float
    recurrence_count: int

    def __post_init__(self) -> None:
        if not self.weakness_id:
            raise ValueError("weakness_id is required")
        if not self.skill_id:
            raise ValueError("skill_id is required")
        if self.weakness_type not in WEAKNESS_TYPES:
            raise ValueError(f"Unsupported weakness_type: {self.weakness_type}")
        object.__setattr__(self, "severity", _clamp_score(self.severity))
        object.__setattr__(self, "recurrence_count", max(0, int(self.recurrence_count)))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = WEAKNESS_RECORD_SCHEMA
        data["evidence_refs"] = list(data["evidence_refs"])
        data["severity"] = round(float(data["severity"]), 4)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeaknessRecord":
        return cls(
            weakness_id=str(data.get("weakness_id") or "weakness"),
            owner=str(data.get("owner") or "Boss"),
            domain=str(data.get("domain") or "general"),
            skill_id=str(data.get("skill_id") or "general_reasoning"),
            weakness_type=str(data.get("weakness_type") or "reasoning_gap"),
            evidence_refs=_tuple(data.get("evidence_refs")),
            severity=_clamp_score(data.get("severity")),
            recurrence_count=max(0, _int(data.get("recurrence_count"), 0)),
        )


@dataclass(frozen=True)
class CurriculumPlan:
    curriculum_id: str
    weakness_id: str
    domain: str
    learning_goals: tuple[str, ...]
    lesson_units: tuple[str, ...]
    exam_requirements: tuple[str, ...]
    target_score: float

    def __post_init__(self) -> None:
        if not self.curriculum_id:
            raise ValueError("curriculum_id is required")
        if not self.weakness_id:
            raise ValueError("weakness_id is required")
        object.__setattr__(self, "target_score", _clamp_score(self.target_score, 0.8))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = CURRICULUM_PLAN_SCHEMA
        for key in ("learning_goals", "lesson_units", "exam_requirements"):
            data[key] = list(data[key])
        data["target_score"] = round(float(data["target_score"]), 4)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CurriculumPlan":
        return cls(
            curriculum_id=str(data.get("curriculum_id") or "curriculum"),
            weakness_id=str(data.get("weakness_id") or "weakness"),
            domain=str(data.get("domain") or "general"),
            learning_goals=_tuple(data.get("learning_goals")),
            lesson_units=_tuple(data.get("lesson_units")),
            exam_requirements=_tuple(data.get("exam_requirements")),
            target_score=_clamp_score(data.get("target_score"), 0.8),
        )


@dataclass(frozen=True)
class AdaptiveExam:
    exam_id: str
    curriculum_id: str
    difficulty: str
    questions: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.difficulty not in {"maintenance", "standard", "advanced", "remediation"}:
            raise ValueError(f"Unsupported exam difficulty: {self.difficulty}")
        if not self.questions:
            raise ValueError("AdaptiveExam requires at least one question")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = ADAPTIVE_EXAM_SCHEMA
        data["questions"] = list(data["questions"])
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AdaptiveExam":
        return cls(
            exam_id=str(data.get("exam_id") or "exam"),
            curriculum_id=str(data.get("curriculum_id") or "curriculum"),
            difficulty=str(data.get("difficulty") or "standard"),
            questions=_tuple(data.get("questions")),
        )
