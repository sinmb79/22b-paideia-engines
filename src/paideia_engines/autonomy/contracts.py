from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


ACTION_PATTERN_SCHEMA = "paideia-edge-action-pattern/v1"
ACTION_RECEIPT_SCHEMA = "paideia-edge-action-receipt/v1"
BEHAVIORAL_EXAM_RESULT_SCHEMA = "paideia-edge-behavioral-exam-result/v1"
CAPABILITY_CONTRACT_SCHEMA = "paideia-edge-capability-contract/v1"
OUTCOME_EVIDENCE_SCHEMA = "paideia-edge-outcome-evidence/v1"
STEP_CREDIT_SCHEMA = "paideia-edge-step-credit/v1"
WEAKNESS_RECORD_SCHEMA = "paideia-edge-weakness-record/v1"
REMEDIATION_TICKET_SCHEMA = "paideia-edge-remediation-ticket/v1"
WORLD_STATE_SCHEMA = "paideia-edge-world-state/v1"
OBSERVATION_SCHEMA = "paideia-edge-observation/v1"

LEARNING_STATUSES = {
    "draft",
    "exam_validated",
    "field_validated",
    "reinforced",
    "weakened",
    "quarantined",
}


class RuntimeMode(str, Enum):
    CONNECTED = "connected"
    LOCAL_DELIBERATIVE = "local_deliberative"
    PATTERN_ONLY = "pattern_only"
    SAFE_DEGRADED = "safe_degraded"
    SAFE_HALT = "safe_halt"


class BrainState(str, Enum):
    BOOTSTRAP = "bootstrap"
    SELF_TEST = "self_test"
    IDLE = "idle"
    OBSERVE = "observe"
    PLAN = "plan"
    SAFETY_CHECK = "safety_check"
    EXECUTE = "execute"
    MONITOR = "monitor"
    RECOVER = "recover"
    SAFE_HALT = "safe_halt"


class DeploymentStatus(str, Enum):
    NOT_COMPILED = "not_compiled"
    COMPILED = "compiled"
    SIMULATION_VALIDATED = "simulation_validated"
    SHADOW_VALIDATED = "shadow_validated"
    LIMITED_FIELD = "limited_field"
    OPERATIONAL = "operational"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class SideEffectClass(str, Enum):
    READ_ONLY = "read_only"
    REVERSIBLE = "reversible"
    CONSEQUENTIAL = "consequential"
    SAFETY_CRITICAL = "safety_critical"
    PROHIBITED = "prohibited"


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


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _score(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _enum(value: Any, enum_cls: type[Enum], field_name: str) -> str:
    text = str(value or "")
    allowed = {item.value for item in enum_cls}
    if text not in allowed:
        raise ValueError(f"Unsupported {field_name}: {text}")
    return text


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_id: str
    schema_ref: str
    observed_at: str
    received_at: str
    payload_ref: str
    payload_digest: str
    confidence: float
    freshness_ms: int
    health_status: str
    provenance: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = OBSERVATION_SCHEMA
        data["confidence"] = round(_score(self.confidence), 4)
        data["freshness_ms"] = max(0, int(self.freshness_ms))
        data["provenance"] = list(self.provenance)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Observation":
        return cls(
            observation_id=str(data.get("observation_id") or "observation"),
            source_id=str(data.get("source_id") or "source"),
            schema_ref=str(data.get("schema_ref") or "unknown/v1"),
            observed_at=str(data.get("observed_at") or ""),
            received_at=str(data.get("received_at") or ""),
            payload_ref=str(data.get("payload_ref") or ""),
            payload_digest=str(data.get("payload_digest") or ""),
            confidence=_score(data.get("confidence"), 1.0),
            freshness_ms=max(0, _int(data.get("freshness_ms"))),
            health_status=str(data.get("health_status") or "unknown"),
            provenance=_tuple(data.get("provenance")),
        )


@dataclass(frozen=True)
class StateFact:
    key: str
    value: object
    confidence: float
    source_observation_ids: tuple[str, ...]
    valid_until: str | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["confidence"] = round(_score(self.confidence), 4)
        data["source_observation_ids"] = list(self.source_observation_ids)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateFact":
        return cls(
            key=str(data.get("key") or "fact"),
            value=data.get("value"),
            confidence=_score(data.get("confidence"), 1.0),
            source_observation_ids=_tuple(data.get("source_observation_ids")),
            valid_until=_optional_string(data.get("valid_until")),
        )


@dataclass(frozen=True)
class WorldState:
    state_id: str
    created_at: str
    facts: tuple[StateFact, ...]
    environment_tags: tuple[str, ...]
    sensor_health: tuple[str, ...]
    state_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": WORLD_STATE_SCHEMA,
            "state_id": self.state_id,
            "created_at": self.created_at,
            "facts": [fact.to_dict() for fact in self.facts],
            "environment_tags": list(self.environment_tags),
            "sensor_health": list(self.sensor_health),
            "state_digest": self.state_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldState":
        return cls(
            state_id=str(data.get("state_id") or "state"),
            created_at=str(data.get("created_at") or ""),
            facts=tuple(StateFact.from_dict(item) for item in data.get("facts", []) if isinstance(item, dict)),
            environment_tags=_tuple(data.get("environment_tags")),
            sensor_health=_tuple(data.get("sensor_health")),
            state_digest=str(data.get("state_digest") or ""),
        )


@dataclass(frozen=True)
class CognitiveBudget:
    max_cycle_ms: int
    max_local_model_tokens: int
    max_remote_model_tokens: int
    max_energy_units: float | None
    max_memory_mb: int | None
    network_allowed: bool
    remote_calls_allowed: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("max_cycle_ms", "max_local_model_tokens", "max_remote_model_tokens", "remote_calls_allowed"):
            data[key] = max(0, int(data[key]))
        if data["max_memory_mb"] is not None:
            data["max_memory_mb"] = max(0, int(data["max_memory_mb"]))
        if data["max_energy_units"] is not None:
            data["max_energy_units"] = max(0.0, float(data["max_energy_units"]))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CognitiveBudget":
        return cls(
            max_cycle_ms=max(0, _int(data.get("max_cycle_ms"))),
            max_local_model_tokens=max(0, _int(data.get("max_local_model_tokens"))),
            max_remote_model_tokens=max(0, _int(data.get("max_remote_model_tokens"))),
            max_energy_units=None if data.get("max_energy_units") is None else max(0.0, float(data.get("max_energy_units"))),
            max_memory_mb=None if data.get("max_memory_mb") is None else max(0, _int(data.get("max_memory_mb"))),
            network_allowed=bool(data.get("network_allowed")),
            remote_calls_allowed=max(0, _int(data.get("remote_calls_allowed"))),
        )


@dataclass(frozen=True)
class AutonomyEnvelope:
    envelope_id: str
    allowed_capabilities: tuple[str, ...]
    prohibited_capabilities: tuple[str, ...]
    allowed_side_effect_classes: tuple[str, ...]
    max_operation_duration_ms: int
    required_health_signals: tuple[str, ...]
    abort_conditions: tuple[dict[str, Any], ...]
    human_approval_scopes: tuple[str, ...]
    offline_policy: str

    def __post_init__(self) -> None:
        invalid = set(self.allowed_side_effect_classes) - {item.value for item in SideEffectClass}
        if invalid:
            raise ValueError(f"Unsupported side_effect_class: {sorted(invalid)}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("allowed_capabilities", "prohibited_capabilities", "allowed_side_effect_classes", "required_health_signals", "human_approval_scopes"):
            data[key] = list(data[key])
        data["abort_conditions"] = [dict(item) for item in self.abort_conditions]
        data["max_operation_duration_ms"] = max(0, int(self.max_operation_duration_ms))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutonomyEnvelope":
        return cls(
            envelope_id=str(data.get("envelope_id") or "envelope"),
            allowed_capabilities=_tuple(data.get("allowed_capabilities")),
            prohibited_capabilities=_tuple(data.get("prohibited_capabilities")),
            allowed_side_effect_classes=_tuple(data.get("allowed_side_effect_classes")),
            max_operation_duration_ms=max(0, _int(data.get("max_operation_duration_ms"))),
            required_health_signals=_tuple(data.get("required_health_signals")),
            abort_conditions=_dict_tuple(data.get("abort_conditions")),
            human_approval_scopes=_tuple(data.get("human_approval_scopes")),
            offline_policy=str(data.get("offline_policy") or "degrade"),
        )


@dataclass(frozen=True)
class CapabilityContract:
    capability_id: str
    version: str
    input_schema_ref: str
    output_schema_ref: str
    side_effect_class: str
    required_permissions: tuple[str, ...]
    idempotent: bool
    reversible: bool
    timeout_ms: int
    simulator_adapter: str
    runtime_adapter: str | None
    safe_fallback_capability_id: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "side_effect_class", _enum(self.side_effect_class, SideEffectClass, "side_effect_class"))
        object.__setattr__(self, "timeout_ms", max(0, int(self.timeout_ms)))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = CAPABILITY_CONTRACT_SCHEMA
        data["required_permissions"] = list(self.required_permissions)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityContract":
        return cls(
            capability_id=str(data.get("capability_id") or "capability"),
            version=str(data.get("version") or "v1"),
            input_schema_ref=str(data.get("input_schema_ref") or ""),
            output_schema_ref=str(data.get("output_schema_ref") or ""),
            side_effect_class=str(data.get("side_effect_class") or SideEffectClass.READ_ONLY.value),
            required_permissions=_tuple(data.get("required_permissions")),
            idempotent=bool(data.get("idempotent")),
            reversible=bool(data.get("reversible")),
            timeout_ms=max(0, _int(data.get("timeout_ms"))),
            simulator_adapter=str(data.get("simulator_adapter") or ""),
            runtime_adapter=_optional_string(data.get("runtime_adapter")),
            safe_fallback_capability_id=_optional_string(data.get("safe_fallback_capability_id")),
        )


@dataclass(frozen=True)
class ActionStep:
    step_id: str
    kind: str
    capability_id: str | None
    input_bindings: tuple[dict[str, Any], ...]
    guard: dict[str, Any] | None
    success_condition: dict[str, Any] | None
    timeout_ms: int
    max_attempts: int
    on_success: str | None
    on_failure: str | None
    fallback_step_id: str | None
    approval_scope: str | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["input_bindings"] = [dict(item) for item in self.input_bindings]
        data["timeout_ms"] = max(0, int(self.timeout_ms))
        data["max_attempts"] = max(1, int(self.max_attempts))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionStep":
        return cls(
            step_id=str(data.get("step_id") or "step"),
            kind=str(data.get("kind") or "capability"),
            capability_id=_optional_string(data.get("capability_id")),
            input_bindings=_dict_tuple(data.get("input_bindings")),
            guard=data.get("guard") if isinstance(data.get("guard"), dict) else None,
            success_condition=data.get("success_condition") if isinstance(data.get("success_condition"), dict) else None,
            timeout_ms=max(0, _int(data.get("timeout_ms"))),
            max_attempts=max(1, _int(data.get("max_attempts"), 1)),
            on_success=_optional_string(data.get("on_success")),
            on_failure=_optional_string(data.get("on_failure")),
            fallback_step_id=_optional_string(data.get("fallback_step_id")),
            approval_scope=_optional_string(data.get("approval_scope")),
        )


@dataclass(frozen=True)
class ActionPattern:
    action_pattern_id: str
    version: str
    source_pattern_id: str
    source_kibo_ids: tuple[str, ...]
    owner: str
    domain: str
    task_family: str
    required_observations: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    preconditions: tuple[dict[str, Any], ...]
    invariants: tuple[dict[str, Any], ...]
    postconditions: tuple[dict[str, Any], ...]
    steps: tuple[ActionStep, ...]
    start_step_id: str
    max_total_duration_ms: int
    cognitive_budget: CognitiveBudget
    autonomy_envelope: AutonomyEnvelope
    learning_status: str
    deployment_status: str
    evidence_refs: tuple[str, ...]
    content_digest: str

    def __post_init__(self) -> None:
        if self.learning_status not in LEARNING_STATUSES:
            raise ValueError(f"Unsupported learning_status: {self.learning_status}")
        object.__setattr__(self, "deployment_status", _enum(self.deployment_status, DeploymentStatus, "deployment_status"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": ACTION_PATTERN_SCHEMA,
            "action_pattern_id": self.action_pattern_id,
            "version": self.version,
            "source_pattern_id": self.source_pattern_id,
            "source_kibo_ids": list(self.source_kibo_ids),
            "owner": self.owner,
            "domain": self.domain,
            "task_family": self.task_family,
            "required_observations": list(self.required_observations),
            "required_capabilities": list(self.required_capabilities),
            "preconditions": [dict(item) for item in self.preconditions],
            "invariants": [dict(item) for item in self.invariants],
            "postconditions": [dict(item) for item in self.postconditions],
            "steps": [step.to_dict() for step in self.steps],
            "start_step_id": self.start_step_id,
            "max_total_duration_ms": max(0, int(self.max_total_duration_ms)),
            "cognitive_budget": self.cognitive_budget.to_dict(),
            "autonomy_envelope": self.autonomy_envelope.to_dict(),
            "learning_status": self.learning_status,
            "deployment_status": self.deployment_status,
            "evidence_refs": list(self.evidence_refs),
            "content_digest": self.content_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionPattern":
        return cls(
            action_pattern_id=str(data.get("action_pattern_id") or "action-pattern"),
            version=str(data.get("version") or "v1"),
            source_pattern_id=str(data.get("source_pattern_id") or "pattern"),
            source_kibo_ids=_tuple(data.get("source_kibo_ids")),
            owner=str(data.get("owner") or "Boss"),
            domain=str(data.get("domain") or "general"),
            task_family=str(data.get("task_family") or "general_task"),
            required_observations=_tuple(data.get("required_observations")),
            required_capabilities=_tuple(data.get("required_capabilities")),
            preconditions=_dict_tuple(data.get("preconditions")),
            invariants=_dict_tuple(data.get("invariants")),
            postconditions=_dict_tuple(data.get("postconditions")),
            steps=tuple(ActionStep.from_dict(item) for item in data.get("steps", []) if isinstance(item, dict)),
            start_step_id=str(data.get("start_step_id") or "start"),
            max_total_duration_ms=max(0, _int(data.get("max_total_duration_ms"))),
            cognitive_budget=CognitiveBudget.from_dict(data.get("cognitive_budget") or {}),
            autonomy_envelope=AutonomyEnvelope.from_dict(data.get("autonomy_envelope") or {}),
            learning_status=str(data.get("learning_status") or "draft"),
            deployment_status=str(data.get("deployment_status") or DeploymentStatus.NOT_COMPILED.value),
            evidence_refs=_tuple(data.get("evidence_refs")),
            content_digest=str(data.get("content_digest") or ""),
        )


@dataclass(frozen=True)
class ActionReceipt:
    receipt_id: str
    decision_cycle_id: str
    action_pattern_id: str
    step_id: str
    capability_id: str
    requested_at: str
    completed_at: str | None
    status: str
    input_digest: str
    output_ref: str | None
    output_digest: str | None
    observed_side_effects: tuple[str, ...]
    error_code: str | None
    rollback_status: str | None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = ACTION_RECEIPT_SCHEMA
        data["observed_side_effects"] = list(self.observed_side_effects)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionReceipt":
        return cls(
            receipt_id=str(data.get("receipt_id") or "receipt"),
            decision_cycle_id=str(data.get("decision_cycle_id") or "cycle"),
            action_pattern_id=str(data.get("action_pattern_id") or "action-pattern"),
            step_id=str(data.get("step_id") or "step"),
            capability_id=str(data.get("capability_id") or "capability"),
            requested_at=str(data.get("requested_at") or ""),
            completed_at=_optional_string(data.get("completed_at")),
            status=str(data.get("status") or "requested"),
            input_digest=str(data.get("input_digest") or ""),
            output_ref=_optional_string(data.get("output_ref")),
            output_digest=_optional_string(data.get("output_digest")),
            observed_side_effects=_tuple(data.get("observed_side_effects")),
            error_code=_optional_string(data.get("error_code")),
            rollback_status=_optional_string(data.get("rollback_status")),
        )


@dataclass(frozen=True)
class BehavioralExamResult:
    exam_id: str
    action_pattern_id: str
    scenario_id: str
    exam_kind: str
    score: float
    passed: bool
    receipts: tuple[ActionReceipt, ...]
    outcome_evidence_id: str | None
    safety_violations: tuple[str, ...]
    trace_digest: str
    replay_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": BEHAVIORAL_EXAM_RESULT_SCHEMA,
            "exam_id": self.exam_id,
            "action_pattern_id": self.action_pattern_id,
            "scenario_id": self.scenario_id,
            "exam_kind": self.exam_kind,
            "score": round(_score(self.score), 4),
            "passed": self.passed,
            "receipts": [receipt.to_dict() for receipt in self.receipts],
            "outcome_evidence_id": self.outcome_evidence_id,
            "safety_violations": list(self.safety_violations),
            "trace_digest": self.trace_digest,
            "replay_digest": self.replay_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BehavioralExamResult":
        return cls(
            exam_id=str(data.get("exam_id") or "exam"),
            action_pattern_id=str(data.get("action_pattern_id") or "action-pattern"),
            scenario_id=str(data.get("scenario_id") or "scenario"),
            exam_kind=str(data.get("exam_kind") or "nominal"),
            score=_score(data.get("score")),
            passed=bool(data.get("passed")),
            receipts=tuple(ActionReceipt.from_dict(item) for item in data.get("receipts", []) if isinstance(item, dict)),
            outcome_evidence_id=_optional_string(data.get("outcome_evidence_id")),
            safety_violations=_tuple(data.get("safety_violations")),
            trace_digest=str(data.get("trace_digest") or ""),
            replay_digest=str(data.get("replay_digest") or ""),
        )


@dataclass(frozen=True)
class OutcomeEvidence:
    outcome_id: str
    decision_cycle_id: str
    pattern_id: str
    action_pattern_id: str
    immediate_score: float | None
    delayed_score: float | None
    success: bool | None
    safety_violations: tuple[str, ...]
    error_type: str | None
    environment_tags: tuple[str, ...]
    confounders: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    attribution_confidence: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = OUTCOME_EVIDENCE_SCHEMA
        for key in ("safety_violations", "environment_tags", "confounders", "evidence_refs"):
            data[key] = list(data[key])
        data["immediate_score"] = None if self.immediate_score is None else round(_score(self.immediate_score), 4)
        data["delayed_score"] = None if self.delayed_score is None else round(_score(self.delayed_score), 4)
        data["attribution_confidence"] = round(_score(self.attribution_confidence), 4)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutcomeEvidence":
        return cls(
            outcome_id=str(data.get("outcome_id") or "outcome"),
            decision_cycle_id=str(data.get("decision_cycle_id") or "cycle"),
            pattern_id=str(data.get("pattern_id") or "pattern"),
            action_pattern_id=str(data.get("action_pattern_id") or "action-pattern"),
            immediate_score=None if data.get("immediate_score") is None else _score(data.get("immediate_score")),
            delayed_score=None if data.get("delayed_score") is None else _score(data.get("delayed_score")),
            success=None if data.get("success") is None else bool(data.get("success")),
            safety_violations=_tuple(data.get("safety_violations")),
            error_type=_optional_string(data.get("error_type")),
            environment_tags=_tuple(data.get("environment_tags")),
            confounders=_tuple(data.get("confounders")),
            evidence_refs=_tuple(data.get("evidence_refs")),
            attribution_confidence=_score(data.get("attribution_confidence")),
        )


@dataclass(frozen=True)
class StepCredit:
    outcome_id: str
    step_id: str
    contribution_score: float
    causal_confidence: float
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = STEP_CREDIT_SCHEMA
        data["contribution_score"] = round(max(-1.0, min(1.0, float(self.contribution_score))), 4)
        data["causal_confidence"] = round(_score(self.causal_confidence), 4)
        data["reason_codes"] = list(self.reason_codes)
        return data


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
    status: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = WEAKNESS_RECORD_SCHEMA
        data["evidence_refs"] = list(self.evidence_refs)
        data["severity"] = round(_score(self.severity), 4)
        data["recurrence_count"] = max(0, int(self.recurrence_count))
        return data


@dataclass(frozen=True)
class RemediationTicket:
    ticket_id: str
    weakness_id: str
    affected_pattern_ids: tuple[str, ...]
    affected_action_pattern_ids: tuple[str, ...]
    required_curriculum_units: tuple[str, ...]
    required_exam_kinds: tuple[str, ...]
    required_score: float
    blocks_operational_use: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["schema"] = REMEDIATION_TICKET_SCHEMA
        for key in ("affected_pattern_ids", "affected_action_pattern_ids", "required_curriculum_units", "required_exam_kinds"):
            data[key] = list(data[key])
        data["required_score"] = round(_score(self.required_score), 4)
        return data
