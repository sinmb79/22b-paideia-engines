from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


TASK_FINGERPRINT_SCHEMA = "paideia-task-fingerprint/v1"
KIBO_RECORD_SCHEMA = "paideia-kibo-record/v1"
REUSE_DECISION_SCHEMA = "paideia-kibo-reuse-decision/v1"
PATTERN_CANDIDATE_SCHEMA = "paideia-pattern-candidate/v1"
PATTERN_EXAM_RESULT_SCHEMA = "paideia-pattern-exam-result/v1"
REAL_WORLD_OUTCOME_SCHEMA = "paideia-real-world-outcome/v1"
FAILURE_MEMORY_SCHEMA = "paideia-failure-memory/v1"
CRITIC_REPORT_SCHEMA = "paideia-critic-report/v1"

PATTERN_STATUSES = {
    "draft",
    "exam_validated",
    "field_validated",
    "reinforced",
    "weakened",
    "quarantined",
}


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _risk_level(value: Any, default: str = "medium") -> str:
    risk = str(value or default).casefold()
    return risk if risk in {"low", "medium", "high"} else default


@dataclass(frozen=True)
class TaskFingerprint:
    task_id: str
    owner: str
    domain: str
    task_type: str
    intent: str
    constraints: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    risk_level: str
    freshness_required: bool
    expected_output_type: str
    user_style_markers: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_level", _risk_level(self.risk_level))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = TASK_FINGERPRINT_SCHEMA
        for key in ("constraints", "required_capabilities", "user_style_markers"):
            data[key] = list(data[key])
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskFingerprint":
        return cls(
            task_id=str(data.get("task_id") or "task"),
            owner=str(data.get("owner") or "Boss"),
            domain=str(data.get("domain") or "general"),
            task_type=str(data.get("task_type") or "general_task"),
            intent=str(data.get("intent") or "answer_user_request"),
            constraints=_tuple(data.get("constraints")),
            required_capabilities=_tuple(data.get("required_capabilities")),
            risk_level=_risk_level(data.get("risk_level")),
            freshness_required=bool(data.get("freshness_required")),
            expected_output_type=str(data.get("expected_output_type") or "response"),
            user_style_markers=_tuple(data.get("user_style_markers")),
        )


@dataclass(frozen=True)
class KiboRecord:
    kibo_id: str
    source_run_id: str
    owner: str
    domain: str
    task_type: str
    problem_signature: str
    solution_steps: tuple[str, ...]
    reusable_logic: tuple[str, ...]
    failure_modes: tuple[str, ...]
    required_inputs: tuple[str, ...]
    output_template: str
    evidence_refs: tuple[str, ...]
    success_score: int
    promotion_status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = KIBO_RECORD_SCHEMA
        for key in ("solution_steps", "reusable_logic", "failure_modes", "required_inputs", "evidence_refs"):
            data[key] = list(data[key])
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KiboRecord":
        return cls(
            kibo_id=str(data.get("kibo_id") or data.get("id") or "kibo"),
            source_run_id=str(data.get("source_run_id") or ""),
            owner=str(data.get("owner") or "Boss"),
            domain=str(data.get("domain") or "general"),
            task_type=str(data.get("task_type") or "general_task"),
            problem_signature=str(data.get("problem_signature") or data.get("summary") or ""),
            solution_steps=_tuple(data.get("solution_steps")),
            reusable_logic=_tuple(data.get("reusable_logic")),
            failure_modes=_tuple(data.get("failure_modes")),
            required_inputs=_tuple(data.get("required_inputs")),
            output_template=str(data.get("output_template") or ""),
            evidence_refs=_tuple(data.get("evidence_refs")),
            success_score=max(0, min(100, int(data.get("success_score") or 0))),
            promotion_status=str(data.get("promotion_status") or "unreviewed"),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
        )


@dataclass(frozen=True)
class ReuseDecision:
    decision_id: str
    task_id: str
    selected_kibo_ids: tuple[str, ...]
    similarity_score: float
    confidence_score: float
    risk_score: float
    reuse_mode: str
    llm_required_parts: tuple[str, ...]
    reason: str
    pattern_id: str | None = None
    pattern_status: str | None = None
    exam_validated: bool = False
    field_validated: bool = False
    failure_warnings: tuple[str, ...] = ()
    critic_required: bool = False
    user_decision_fit_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = REUSE_DECISION_SCHEMA
        data["selected_kibo_ids"] = list(data["selected_kibo_ids"])
        data["llm_required_parts"] = list(data["llm_required_parts"])
        data["failure_warnings"] = list(data["failure_warnings"])
        return data


@dataclass(frozen=True)
class PatternCandidate:
    pattern_id: str
    owner: str
    domain: str
    task_family: str
    abstract_strategy: tuple[str, ...]
    required_conditions: tuple[str, ...]
    known_failure_modes: tuple[str, ...]
    source_kibo_ids: tuple[str, ...]
    exam_score: float | None
    real_world_score: float | None
    reinforcement_score: float
    status: str

    def __post_init__(self) -> None:
        if not self.source_kibo_ids:
            raise ValueError("PatternCandidate requires at least one source_kibo_id")
        if self.status not in PATTERN_STATUSES:
            raise ValueError(f"Unsupported pattern status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = PATTERN_CANDIDATE_SCHEMA
        for key in ("abstract_strategy", "required_conditions", "known_failure_modes", "source_kibo_ids"):
            data[key] = list(data[key])
        return data

    @property
    def exam_validated(self) -> bool:
        return self.status in {"exam_validated", "field_validated", "reinforced"}

    @property
    def field_validated(self) -> bool:
        return self.status in {"field_validated", "reinforced"}


@dataclass(frozen=True)
class PatternExamResult:
    exam_id: str
    pattern_id: str
    task_id: str
    score: float
    passed: bool
    mistakes: tuple[str, ...]
    improvement_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = PATTERN_EXAM_RESULT_SCHEMA
        data["mistakes"] = list(data["mistakes"])
        data["improvement_notes"] = list(data["improvement_notes"])
        return data


@dataclass(frozen=True)
class RealWorldOutcome:
    outcome_id: str
    pattern_id: str
    task_id: str
    applied_at: str
    outcome_type: str
    success: bool
    quantitative_result: float | None
    qualitative_result: str | None
    user_feedback_score: int | None
    error_type: str | None
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = REAL_WORLD_OUTCOME_SCHEMA
        data["notes"] = list(data["notes"])
        return data


@dataclass(frozen=True)
class FailureMemory:
    failure_id: str
    pattern_id: str
    task_id: str
    error_type: str
    severity: str
    trigger_conditions: tuple[str, ...]
    missed_signals: tuple[str, ...]
    prevention_rules: tuple[str, ...]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = FAILURE_MEMORY_SCHEMA
        for key in ("trigger_conditions", "missed_signals", "prevention_rules"):
            data[key] = list(data[key])
        return data


@dataclass(frozen=True)
class CriticReport:
    report_id: str
    pattern_id: str
    objections: tuple[str, ...]
    hidden_assumptions: tuple[str, ...]
    risk_flags: tuple[str, ...]
    required_safeguards: tuple[str, ...]
    pass_gate: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = CRITIC_REPORT_SCHEMA
        for key in ("objections", "hidden_assumptions", "risk_flags", "required_safeguards"):
            data[key] = list(data[key])
        return data
