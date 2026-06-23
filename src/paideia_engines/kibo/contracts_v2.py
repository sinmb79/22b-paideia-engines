from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any

from .schema_registry import CONTRACTS_RELEASE, SCHEMA_IDS, contract_hash, validate_contract_header


ACTION_PATTERN_LIFECYCLE_STATUSES = {
    "draft",
    "review_quarantine",
    "structural_validated",
    "behavioral_validated",
    "shadow_validated",
    "field_validated",
    "promoted",
    "suspended",
    "revoked",
}

OUTCOME_EVIDENCE_STATUSES = {"pending", "verified", "contested", "invalidated", "expired"}
PATTERN_REVISION_STATUSES = {"draft", "quarantined", "testing", "accepted", "rejected", "rolled_back"}


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _dict_tuple(value: Any) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, dict):
        return (dict(value),)
    if isinstance(value, (list, tuple)):
        return tuple(dict(item) for item in value if isinstance(item, dict))
    return ()


def _objects(value: Any, factory) -> tuple[Any, ...]:
    if value is None:
        return ()
    rows = value if isinstance(value, (list, tuple)) else (value,)
    return tuple(factory.from_dict(item) if isinstance(item, dict) else item for item in rows)


def _score(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(numeric):
        return default
    return max(0.0, min(1.0, numeric))


def _optional_score(value: Any) -> float | None:
    return None if value is None else _score(value)


def _optional_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return max(0.0, numeric)


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def _header(contract_name: str) -> dict[str, str]:
    return {
        "schema": SCHEMA_IDS[contract_name],
        "schema_version": CONTRACTS_RELEASE,
        "contract_hash": contract_hash(contract_name),
    }


def _with_header(contract_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {**_header(contract_name), **payload}


def _validate_status(value: str, allowed: set[str], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"Unsupported {field_name}: {value}")
    return value


@dataclass(frozen=True)
class TypedValue:
    name: str
    value_type: str
    value: object

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TypedValue":
        return cls(str(data.get("name") or ""), str(data.get("value_type") or "unknown"), data.get("value"))


@dataclass(frozen=True)
class ObservationSpec:
    observation_id: str
    name: str
    value_type: str
    required: bool
    freshness_ms: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObservationSpec":
        return cls(
            str(data.get("observation_id") or ""),
            str(data.get("name") or ""),
            str(data.get("value_type") or "unknown"),
            bool(data.get("required", True)),
            _optional_int(data.get("freshness_ms")),
        )


@dataclass(frozen=True)
class Predicate:
    predicate_id: str
    op: str
    field: str
    value: object

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Predicate":
        return cls(
            str(data.get("predicate_id") or ""),
            str(data.get("op") or "exists"),
            str(data.get("field") or ""),
            data.get("value"),
        )


@dataclass(frozen=True)
class ConstraintSpec:
    constraint_id: str
    predicate: Predicate
    severity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "predicate": self.predicate.to_dict(),
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConstraintSpec":
        return cls(
            str(data.get("constraint_id") or ""),
            Predicate.from_dict(data.get("predicate") or {}),
            str(data.get("severity") or "medium"),
        )


@dataclass(frozen=True)
class ActionStepEvidence:
    step_id: str
    action_type: str
    capability: str
    input_refs: tuple[str, ...]
    output_ref: str | None
    receipt_ref: str | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["input_refs"] = list(self.input_refs)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionStepEvidence":
        return cls(
            str(data.get("step_id") or ""),
            str(data.get("action_type") or ""),
            str(data.get("capability") or ""),
            _tuple(data.get("input_refs")),
            data.get("output_ref"),
            data.get("receipt_ref"),
        )


@dataclass(frozen=True)
class BranchEvent:
    event_id: str
    predicate: Predicate
    selected_step_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "predicate": self.predicate.to_dict(),
            "selected_step_id": self.selected_step_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BranchEvent":
        return cls(
            str(data.get("event_id") or ""),
            Predicate.from_dict(data.get("predicate") or {}),
            str(data.get("selected_step_id") or ""),
        )


@dataclass(frozen=True)
class CaseGraph:
    case_id: str
    owner: str
    domain: str
    task_family: str
    goal: str
    context_variables: tuple[TypedValue, ...]
    observations: tuple[ObservationSpec, ...]
    constraints: tuple[ConstraintSpec, ...]
    action_steps: tuple[ActionStepEvidence, ...]
    branch_events: tuple[BranchEvent, ...]
    outcome_refs: tuple[str, ...]
    failure_refs: tuple[str, ...]
    source_kibo_ids: tuple[str, ...]
    evidence_hashes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _with_header(
            "case_graph",
            {
                "case_id": self.case_id,
                "owner": self.owner,
                "domain": self.domain,
                "task_family": self.task_family,
                "goal": self.goal,
                "context_variables": [item.to_dict() for item in self.context_variables],
                "observations": [item.to_dict() for item in self.observations],
                "constraints": [item.to_dict() for item in self.constraints],
                "action_steps": [item.to_dict() for item in self.action_steps],
                "branch_events": [item.to_dict() for item in self.branch_events],
                "outcome_refs": list(self.outcome_refs),
                "failure_refs": list(self.failure_refs),
                "source_kibo_ids": list(self.source_kibo_ids),
                "evidence_hashes": list(self.evidence_hashes),
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseGraph":
        validate_contract_header(data, contract_name="case_graph")
        return cls(
            case_id=str(data.get("case_id") or ""),
            owner=str(data.get("owner") or "Boss"),
            domain=str(data.get("domain") or "general"),
            task_family=str(data.get("task_family") or "general_task"),
            goal=str(data.get("goal") or ""),
            context_variables=_objects(data.get("context_variables"), TypedValue),
            observations=_objects(data.get("observations"), ObservationSpec),
            constraints=_objects(data.get("constraints"), ConstraintSpec),
            action_steps=_objects(data.get("action_steps"), ActionStepEvidence),
            branch_events=_objects(data.get("branch_events"), BranchEvent),
            outcome_refs=_tuple(data.get("outcome_refs")),
            failure_refs=_tuple(data.get("failure_refs")),
            source_kibo_ids=_tuple(data.get("source_kibo_ids")),
            evidence_hashes=_tuple(data.get("evidence_hashes")),
        )


@dataclass(frozen=True)
class TypedSlot:
    slot_id: str
    value_type: str
    required: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TypedSlot":
        return cls(str(data.get("slot_id") or ""), str(data.get("value_type") or "unknown"), bool(data.get("required", True)))


@dataclass(frozen=True)
class ObservationRequirement:
    observation_id: str
    value_type: str
    freshness_ms: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObservationRequirement":
        return cls(str(data.get("observation_id") or ""), str(data.get("value_type") or "unknown"), _optional_int(data.get("freshness_ms")))


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    backoff_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {"max_attempts": max(1, int(self.max_attempts)), "backoff_ms": max(0, int(self.backoff_ms))}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetryPolicy":
        return cls(max(1, int(data.get("max_attempts") or 1)), max(0, int(data.get("backoff_ms") or 0)))


@dataclass(frozen=True)
class ActionNode:
    node_id: str
    action_type: str
    capability: str
    input_bindings: dict[str, str]
    expected_effects: tuple[Predicate, ...]
    timeout_ms: int | None
    retry_policy: RetryPolicy
    on_success: str | None
    on_failure: str | None
    on_uncertain: str | None
    human_review_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "action_type": self.action_type,
            "capability": self.capability,
            "input_bindings": dict(self.input_bindings),
            "expected_effects": [item.to_dict() for item in self.expected_effects],
            "timeout_ms": self.timeout_ms,
            "retry_policy": self.retry_policy.to_dict(),
            "on_success": self.on_success,
            "on_failure": self.on_failure,
            "on_uncertain": self.on_uncertain,
            "human_review_required": self.human_review_required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionNode":
        return cls(
            node_id=str(data.get("node_id") or ""),
            action_type=str(data.get("action_type") or ""),
            capability=str(data.get("capability") or ""),
            input_bindings={str(k): str(v) for k, v in (data.get("input_bindings") or {}).items()},
            expected_effects=_objects(data.get("expected_effects"), Predicate),
            timeout_ms=_optional_int(data.get("timeout_ms")),
            retry_policy=RetryPolicy.from_dict(data.get("retry_policy") or {}),
            on_success=data.get("on_success"),
            on_failure=data.get("on_failure"),
            on_uncertain=data.get("on_uncertain"),
            human_review_required=bool(data.get("human_review_required", False)),
        )


@dataclass(frozen=True)
class Transition:
    from_node_id: str
    to_node_id: str
    condition: Predicate | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "condition": None if self.condition is None else self.condition.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transition":
        condition = data.get("condition")
        return cls(
            str(data.get("from_node_id") or ""),
            str(data.get("to_node_id") or ""),
            Predicate.from_dict(condition) if isinstance(condition, dict) else None,
        )


@dataclass(frozen=True)
class RecoveryAction:
    recovery_id: str
    trigger: Predicate
    action_node_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "trigger": self.trigger.to_dict(),
            "action_node_id": self.action_node_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RecoveryAction":
        return cls(str(data.get("recovery_id") or ""), Predicate.from_dict(data.get("trigger") or {}), str(data.get("action_node_id") or ""))


@dataclass(frozen=True)
class ActionPattern:
    pattern_id: str
    pattern_version: str
    parent_pattern_version: str | None
    owner: str
    domain: str
    task_family: str
    goal_template: str
    input_slots: tuple[TypedSlot, ...]
    preconditions: tuple[Predicate, ...]
    required_observations: tuple[ObservationRequirement, ...]
    steps: tuple[ActionNode, ...]
    transitions: tuple[Transition, ...]
    invariants: tuple[Predicate, ...]
    abort_conditions: tuple[Predicate, ...]
    recovery_actions: tuple[RecoveryAction, ...]
    success_conditions: tuple[Predicate, ...]
    forbidden_contexts: tuple[Predicate, ...]
    required_capabilities: tuple[str, ...]
    source_case_ids: tuple[str, ...]
    validation_profile_id: str | None
    lifecycle_status: str

    def __post_init__(self) -> None:
        _validate_status(self.lifecycle_status, ACTION_PATTERN_LIFECYCLE_STATUSES, "lifecycle_status")

    def to_dict(self) -> dict[str, Any]:
        return _with_header(
            "action_pattern",
            {
                "pattern_id": self.pattern_id,
                "pattern_version": self.pattern_version,
                "parent_pattern_version": self.parent_pattern_version,
                "owner": self.owner,
                "domain": self.domain,
                "task_family": self.task_family,
                "goal_template": self.goal_template,
                "input_slots": [item.to_dict() for item in self.input_slots],
                "preconditions": [item.to_dict() for item in self.preconditions],
                "required_observations": [item.to_dict() for item in self.required_observations],
                "steps": [item.to_dict() for item in self.steps],
                "transitions": [item.to_dict() for item in self.transitions],
                "invariants": [item.to_dict() for item in self.invariants],
                "abort_conditions": [item.to_dict() for item in self.abort_conditions],
                "recovery_actions": [item.to_dict() for item in self.recovery_actions],
                "success_conditions": [item.to_dict() for item in self.success_conditions],
                "forbidden_contexts": [item.to_dict() for item in self.forbidden_contexts],
                "required_capabilities": list(self.required_capabilities),
                "source_case_ids": list(self.source_case_ids),
                "validation_profile_id": self.validation_profile_id,
                "lifecycle_status": self.lifecycle_status,
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionPattern":
        validate_contract_header(data, contract_name="action_pattern")
        return cls(
            pattern_id=str(data.get("pattern_id") or ""),
            pattern_version=str(data.get("pattern_version") or "1"),
            parent_pattern_version=data.get("parent_pattern_version"),
            owner=str(data.get("owner") or "Boss"),
            domain=str(data.get("domain") or "general"),
            task_family=str(data.get("task_family") or "general_task"),
            goal_template=str(data.get("goal_template") or ""),
            input_slots=_objects(data.get("input_slots"), TypedSlot),
            preconditions=_objects(data.get("preconditions"), Predicate),
            required_observations=_objects(data.get("required_observations"), ObservationRequirement),
            steps=_objects(data.get("steps"), ActionNode),
            transitions=_objects(data.get("transitions"), Transition),
            invariants=_objects(data.get("invariants"), Predicate),
            abort_conditions=_objects(data.get("abort_conditions"), Predicate),
            recovery_actions=_objects(data.get("recovery_actions"), RecoveryAction),
            success_conditions=_objects(data.get("success_conditions"), Predicate),
            forbidden_contexts=_objects(data.get("forbidden_contexts"), Predicate),
            required_capabilities=_tuple(data.get("required_capabilities")),
            source_case_ids=_tuple(data.get("source_case_ids")),
            validation_profile_id=data.get("validation_profile_id"),
            lifecycle_status=str(data.get("lifecycle_status") or "draft"),
        )


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    scenario_kind: str
    task_success: bool
    invariant_passed: bool
    abstained: bool
    safety_violations: tuple[str, ...]
    trace_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["safety_violations"] = list(self.safety_violations)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioResult":
        return cls(
            str(data.get("scenario_id") or ""),
            str(data.get("scenario_kind") or ""),
            bool(data.get("task_success", False)),
            bool(data.get("invariant_passed", False)),
            bool(data.get("abstained", False)),
            _tuple(data.get("safety_violations")),
            str(data.get("trace_hash") or ""),
        )


@dataclass(frozen=True)
class BehavioralExamResult:
    exam_id: str
    pattern_id: str
    pattern_version: str
    scenario_pack_id: str
    scenario_results: tuple[ScenarioResult, ...]
    task_success_rate: float
    invariant_pass_rate: float
    transfer_score: float
    abstention_precision: float
    efficiency_score: float
    safety_violation_count: int
    leakage_detected: bool
    passed: bool
    evidence_hashes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _with_header(
            "behavioral_exam",
            {
                "exam_id": self.exam_id,
                "pattern_id": self.pattern_id,
                "pattern_version": self.pattern_version,
                "scenario_pack_id": self.scenario_pack_id,
                "scenario_results": [item.to_dict() for item in self.scenario_results],
                "task_success_rate": round(_score(self.task_success_rate), 4),
                "invariant_pass_rate": round(_score(self.invariant_pass_rate), 4),
                "transfer_score": round(_score(self.transfer_score), 4),
                "abstention_precision": round(_score(self.abstention_precision), 4),
                "efficiency_score": round(_score(self.efficiency_score), 4),
                "safety_violation_count": max(0, int(self.safety_violation_count)),
                "leakage_detected": self.leakage_detected,
                "passed": self.passed,
                "evidence_hashes": list(self.evidence_hashes),
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BehavioralExamResult":
        validate_contract_header(data, contract_name="behavioral_exam")
        return cls(
            str(data.get("exam_id") or ""),
            str(data.get("pattern_id") or ""),
            str(data.get("pattern_version") or ""),
            str(data.get("scenario_pack_id") or ""),
            _objects(data.get("scenario_results"), ScenarioResult),
            _score(data.get("task_success_rate")),
            _score(data.get("invariant_pass_rate")),
            _score(data.get("transfer_score")),
            _score(data.get("abstention_precision")),
            _score(data.get("efficiency_score")),
            max(0, int(data.get("safety_violation_count") or 0)),
            bool(data.get("leakage_detected", False)),
            bool(data.get("passed", False)),
            _tuple(data.get("evidence_hashes")),
        )


@dataclass(frozen=True)
class PatternValidationProfile:
    profile_id: str
    pattern_id: str
    pattern_version: str
    structural_exam_passed: bool
    behavioral_exam_passed: bool
    near_transfer_passed: bool
    far_transfer_passed: bool
    adversarial_exam_passed: bool
    shadow_validation_passed: bool
    field_validation_passed: bool
    critic_clearance_passed: bool
    evidence_fresh_until: str | None
    high_risk_eligible: bool
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_refs"] = list(self.evidence_refs)
        return _with_header("validation_profile", data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatternValidationProfile":
        validate_contract_header(data, contract_name="validation_profile")
        return cls(
            profile_id=str(data.get("profile_id") or ""),
            pattern_id=str(data.get("pattern_id") or ""),
            pattern_version=str(data.get("pattern_version") or ""),
            structural_exam_passed=bool(data.get("structural_exam_passed", False)),
            behavioral_exam_passed=bool(data.get("behavioral_exam_passed", False)),
            near_transfer_passed=bool(data.get("near_transfer_passed", False)),
            far_transfer_passed=bool(data.get("far_transfer_passed", False)),
            adversarial_exam_passed=bool(data.get("adversarial_exam_passed", False)),
            shadow_validation_passed=bool(data.get("shadow_validation_passed", False)),
            field_validation_passed=bool(data.get("field_validation_passed", False)),
            critic_clearance_passed=bool(data.get("critic_clearance_passed", False)),
            evidence_fresh_until=data.get("evidence_fresh_until"),
            high_risk_eligible=bool(data.get("high_risk_eligible", False)),
            evidence_refs=_tuple(data.get("evidence_refs")),
        )


@dataclass(frozen=True)
class EvidenceSource:
    source_id: str
    source_type: str
    confidence: float
    artifact_hash: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "confidence": round(_score(self.confidence), 4),
            "artifact_hash": self.artifact_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceSource":
        return cls(str(data.get("source_id") or ""), str(data.get("source_type") or ""), _score(data.get("confidence")), data.get("artifact_hash"))


@dataclass(frozen=True)
class OutcomeEvidence:
    evidence_id: str
    pattern_id: str
    pattern_version: str
    task_id: str
    run_id: str
    environment_fingerprint: str
    task_difficulty: float
    started_at: str
    observed_at: str
    outcome_latency_seconds: float | None
    technical_score: float | None
    safety_score: float | None
    user_utility_score: float | None
    binary_success: bool | None
    baseline_ref: str | None
    verifier_type: str
    verifier_id: str | None
    provenance: tuple[EvidenceSource, ...]
    action_receipt_refs: tuple[str, ...]
    artifact_hashes: tuple[str, ...]
    confidence: float
    status: str

    def __post_init__(self) -> None:
        _validate_status(self.status, OUTCOME_EVIDENCE_STATUSES, "status")

    def to_dict(self) -> dict[str, Any]:
        return _with_header(
            "outcome_evidence",
            {
                "evidence_id": self.evidence_id,
                "pattern_id": self.pattern_id,
                "pattern_version": self.pattern_version,
                "task_id": self.task_id,
                "run_id": self.run_id,
                "environment_fingerprint": self.environment_fingerprint,
                "task_difficulty": round(_score(self.task_difficulty), 4),
                "started_at": self.started_at,
                "observed_at": self.observed_at,
                "outcome_latency_seconds": self.outcome_latency_seconds,
                "technical_score": self.technical_score,
                "safety_score": self.safety_score,
                "user_utility_score": self.user_utility_score,
                "binary_success": self.binary_success,
                "baseline_ref": self.baseline_ref,
                "verifier_type": self.verifier_type,
                "verifier_id": self.verifier_id,
                "provenance": [item.to_dict() for item in self.provenance],
                "action_receipt_refs": list(self.action_receipt_refs),
                "artifact_hashes": list(self.artifact_hashes),
                "confidence": round(_score(self.confidence), 4),
                "status": self.status,
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutcomeEvidence":
        validate_contract_header(data, contract_name="outcome_evidence")
        return cls(
            evidence_id=str(data.get("evidence_id") or ""),
            pattern_id=str(data.get("pattern_id") or ""),
            pattern_version=str(data.get("pattern_version") or ""),
            task_id=str(data.get("task_id") or ""),
            run_id=str(data.get("run_id") or ""),
            environment_fingerprint=str(data.get("environment_fingerprint") or ""),
            task_difficulty=_score(data.get("task_difficulty")),
            started_at=str(data.get("started_at") or ""),
            observed_at=str(data.get("observed_at") or ""),
            outcome_latency_seconds=_optional_float(data.get("outcome_latency_seconds")),
            technical_score=_optional_score(data.get("technical_score")),
            safety_score=_optional_score(data.get("safety_score")),
            user_utility_score=_optional_score(data.get("user_utility_score")),
            binary_success=data.get("binary_success") if data.get("binary_success") is None else bool(data.get("binary_success")),
            baseline_ref=data.get("baseline_ref"),
            verifier_type=str(data.get("verifier_type") or ""),
            verifier_id=data.get("verifier_id"),
            provenance=_objects(data.get("provenance"), EvidenceSource),
            action_receipt_refs=_tuple(data.get("action_receipt_refs")),
            artifact_hashes=_tuple(data.get("artifact_hashes")),
            confidence=_score(data.get("confidence")),
            status=str(data.get("status") or "pending"),
        )


@dataclass(frozen=True)
class StepCredit:
    step_id: str
    contribution_score: float
    causal_confidence: float
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "contribution_score": round(max(-1.0, min(1.0, float(self.contribution_score))), 4),
            "causal_confidence": round(_score(self.causal_confidence), 4),
            "reason_codes": list(self.reason_codes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepCredit":
        return cls(str(data.get("step_id") or ""), max(-1.0, min(1.0, float(data.get("contribution_score") or 0.0))), _score(data.get("causal_confidence")), _tuple(data.get("reason_codes")))


@dataclass(frozen=True)
class OutcomeAttributionReport:
    report_id: str
    outcome_evidence_id: str
    pattern_contribution: float
    llm_contribution: float
    tool_contribution: float
    human_contribution: float
    environment_contribution: float
    attribution_confidence: float
    confounders: tuple[str, ...]
    comparison_baseline: str | None
    step_credits: tuple[StepCredit, ...]

    def to_dict(self) -> dict[str, Any]:
        return _with_header(
            "attribution_report",
            {
                "report_id": self.report_id,
                "outcome_evidence_id": self.outcome_evidence_id,
                "pattern_contribution": round(_score(self.pattern_contribution), 4),
                "llm_contribution": round(_score(self.llm_contribution), 4),
                "tool_contribution": round(_score(self.tool_contribution), 4),
                "human_contribution": round(_score(self.human_contribution), 4),
                "environment_contribution": round(_score(self.environment_contribution), 4),
                "attribution_confidence": round(_score(self.attribution_confidence), 4),
                "confounders": list(self.confounders),
                "comparison_baseline": self.comparison_baseline,
                "step_credits": [item.to_dict() for item in self.step_credits],
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutcomeAttributionReport":
        validate_contract_header(data, contract_name="attribution_report")
        return cls(
            str(data.get("report_id") or ""),
            str(data.get("outcome_evidence_id") or ""),
            _score(data.get("pattern_contribution")),
            _score(data.get("llm_contribution")),
            _score(data.get("tool_contribution")),
            _score(data.get("human_contribution")),
            _score(data.get("environment_contribution")),
            _score(data.get("attribution_confidence")),
            _tuple(data.get("confounders")),
            data.get("comparison_baseline"),
            _objects(data.get("step_credits"), StepCredit),
        )


@dataclass(frozen=True)
class PatternRevisionProposal:
    revision_id: str
    pattern_id: str
    from_pattern_version: str
    proposed_pattern_version: str
    revision_reasons: tuple[str, ...]
    proposed_changes: tuple[dict[str, Any], ...]
    evidence_refs: tuple[str, ...]
    requires_behavioral_exam: bool
    requires_shadow_validation: bool
    status: str

    def __post_init__(self) -> None:
        _validate_status(self.status, PATTERN_REVISION_STATUSES, "status")

    def to_dict(self) -> dict[str, Any]:
        return _with_header(
            "pattern_revision",
            {
                "revision_id": self.revision_id,
                "pattern_id": self.pattern_id,
                "from_pattern_version": self.from_pattern_version,
                "proposed_pattern_version": self.proposed_pattern_version,
                "revision_reasons": list(self.revision_reasons),
                "proposed_changes": [dict(item) for item in self.proposed_changes],
                "evidence_refs": list(self.evidence_refs),
                "requires_behavioral_exam": self.requires_behavioral_exam,
                "requires_shadow_validation": self.requires_shadow_validation,
                "status": self.status,
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatternRevisionProposal":
        validate_contract_header(data, contract_name="pattern_revision")
        return cls(
            str(data.get("revision_id") or ""),
            str(data.get("pattern_id") or ""),
            str(data.get("from_pattern_version") or ""),
            str(data.get("proposed_pattern_version") or ""),
            _tuple(data.get("revision_reasons")),
            _dict_tuple(data.get("proposed_changes")),
            _tuple(data.get("evidence_refs")),
            bool(data.get("requires_behavioral_exam", True)),
            bool(data.get("requires_shadow_validation", True)),
            str(data.get("status") or "draft"),
        )


@dataclass(frozen=True)
class TokenUsageReceipt:
    receipt_id: str
    run_id: str
    provider: str
    model: str
    call_purpose: str
    input_tokens: int | None
    output_tokens: int | None
    cached_input_tokens: int | None
    estimated: bool
    estimation_method: str | None
    monetary_cost: float | None
    latency_ms: int | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return _with_header(
            "token_usage_receipt",
            {
                "receipt_id": self.receipt_id,
                "run_id": self.run_id,
                "provider": self.provider,
                "model": self.model,
                "call_purpose": self.call_purpose,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "cached_input_tokens": self.cached_input_tokens,
                "estimated": self.estimated,
                "estimation_method": self.estimation_method,
                "monetary_cost": self.monetary_cost,
                "latency_ms": self.latency_ms,
                "created_at": self.created_at,
            },
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenUsageReceipt":
        validate_contract_header(data, contract_name="token_usage_receipt")
        return cls(
            receipt_id=str(data.get("receipt_id") or ""),
            run_id=str(data.get("run_id") or ""),
            provider=str(data.get("provider") or ""),
            model=str(data.get("model") or ""),
            call_purpose=str(data.get("call_purpose") or ""),
            input_tokens=_optional_int(data.get("input_tokens")),
            output_tokens=_optional_int(data.get("output_tokens")),
            cached_input_tokens=_optional_int(data.get("cached_input_tokens")),
            estimated=bool(data.get("estimated", True)),
            estimation_method=data.get("estimation_method"),
            monetary_cost=_optional_float(data.get("monetary_cost")),
            latency_ms=_optional_int(data.get("latency_ms")),
            created_at=str(data.get("created_at") or ""),
        )
