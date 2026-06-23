from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any


CONTRACTS_RELEASE = "2.0.0"
SCHEMA_BASE = "https://github.com/sinmb79/22b-paideia-engines/schemas/kibo-v2"

CONTRACT_NAMES = (
    "case_graph",
    "action_pattern",
    "behavioral_exam",
    "validation_profile",
    "outcome_evidence",
    "attribution_report",
    "pattern_revision",
    "token_usage_receipt",
)

SCHEMA_IDS = {
    name: f"paideia-kibo-v2-{name.replace('_', '-')}/v2" for name in CONTRACT_NAMES
}


def _object_schema(name: str, title: str, required: tuple[str, ...], properties: dict[str, Any]) -> dict[str, Any]:
    base_properties = {
        "schema": {"const": SCHEMA_IDS[name]},
        "schema_version": {"type": "string", "pattern": r"^2\."},
        "contract_hash": {"type": "string", "minLength": 64, "maxLength": 64},
    }
    base_properties.update(properties)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/{name}.schema.json",
        "title": title,
        "type": "object",
        "required": ["schema", "schema_version", "contract_hash", *required],
        "properties": base_properties,
        "additionalProperties": False,
    }


def _typed_value_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["name", "value_type", "value"],
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "value_type": {"type": "string", "minLength": 1},
            "value": {},
        },
        "additionalProperties": False,
    }


def _observation_spec_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["observation_id", "name", "value_type", "required", "freshness_ms"],
        "properties": {
            "observation_id": {"type": "string", "minLength": 1},
            "name": {"type": "string", "minLength": 1},
            "value_type": {"type": "string", "minLength": 1},
            "required": {"type": "boolean"},
            "freshness_ms": {"type": ["integer", "null"], "minimum": 0},
        },
        "additionalProperties": False,
    }


def _predicate_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["predicate_id", "op", "field", "value"],
        "properties": {
            "predicate_id": {"type": "string", "minLength": 1},
            "op": {"type": "string", "minLength": 1},
            "field": {"type": "string", "minLength": 1},
            "value": {},
        },
        "additionalProperties": False,
    }


def _constraint_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["constraint_id", "predicate", "severity"],
        "properties": {
            "constraint_id": {"type": "string", "minLength": 1},
            "predicate": _predicate_schema(),
            "severity": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }


def _action_step_evidence_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["step_id", "action_type", "capability", "input_refs", "output_ref", "receipt_ref"],
        "properties": {
            "step_id": {"type": "string", "minLength": 1},
            "action_type": {"type": "string", "minLength": 1},
            "capability": {"type": "string", "minLength": 1},
            "input_refs": {"type": "array", "items": {"type": "string"}},
            "output_ref": {"type": ["string", "null"]},
            "receipt_ref": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    }


def _branch_event_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["event_id", "predicate", "selected_step_id"],
        "properties": {
            "event_id": {"type": "string", "minLength": 1},
            "predicate": _predicate_schema(),
            "selected_step_id": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }


def _typed_slot_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["slot_id", "value_type", "required"],
        "properties": {
            "slot_id": {"type": "string", "minLength": 1},
            "value_type": {"type": "string", "minLength": 1},
            "required": {"type": "boolean"},
        },
        "additionalProperties": False,
    }


def _observation_requirement_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["observation_id", "value_type", "freshness_ms"],
        "properties": {
            "observation_id": {"type": "string", "minLength": 1},
            "value_type": {"type": "string", "minLength": 1},
            "freshness_ms": {"type": ["integer", "null"], "minimum": 0},
        },
        "additionalProperties": False,
    }


def _retry_policy_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["max_attempts", "backoff_ms"],
        "properties": {
            "max_attempts": {"type": "integer", "minimum": 1},
            "backoff_ms": {"type": "integer", "minimum": 0},
        },
        "additionalProperties": False,
    }


def _action_node_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "node_id",
            "action_type",
            "capability",
            "input_bindings",
            "expected_effects",
            "timeout_ms",
            "retry_policy",
            "on_success",
            "on_failure",
            "on_uncertain",
            "human_review_required",
        ],
        "properties": {
            "node_id": {"type": "string", "minLength": 1},
            "action_type": {"type": "string", "minLength": 1},
            "capability": {"type": "string", "minLength": 1},
            "input_bindings": {"type": "object", "additionalProperties": {"type": "string"}},
            "expected_effects": {"type": "array", "items": _predicate_schema()},
            "timeout_ms": {"type": ["integer", "null"], "minimum": 0},
            "retry_policy": _retry_policy_schema(),
            "on_success": {"type": ["string", "null"]},
            "on_failure": {"type": ["string", "null"]},
            "on_uncertain": {"type": ["string", "null"]},
            "human_review_required": {"type": "boolean"},
        },
        "additionalProperties": False,
    }


def _transition_schema() -> dict[str, Any]:
    condition_schema = _predicate_schema()
    condition_schema["type"] = ["object", "null"]
    return {
        "type": "object",
        "required": ["from_node_id", "to_node_id", "condition"],
        "properties": {
            "from_node_id": {"type": "string", "minLength": 1},
            "to_node_id": {"type": "string", "minLength": 1},
            "condition": condition_schema,
        },
        "additionalProperties": False,
    }


def _recovery_action_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["recovery_id", "trigger", "action_node_id"],
        "properties": {
            "recovery_id": {"type": "string", "minLength": 1},
            "trigger": _predicate_schema(),
            "action_node_id": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }


def _scenario_result_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "scenario_id",
            "scenario_kind",
            "task_success",
            "invariant_passed",
            "abstained",
            "safety_violations",
            "trace_hash",
        ],
        "properties": {
            "scenario_id": {"type": "string", "minLength": 1},
            "scenario_kind": {"type": "string", "minLength": 1},
            "task_success": {"type": "boolean"},
            "invariant_passed": {"type": "boolean"},
            "abstained": {"type": "boolean"},
            "safety_violations": {"type": "array", "items": {"type": "string"}},
            "trace_hash": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    }


def _evidence_source_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["source_id", "source_type", "confidence", "artifact_hash"],
        "properties": {
            "source_id": {"type": "string", "minLength": 1},
            "source_type": {"type": "string", "minLength": 1},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "artifact_hash": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    }


def _step_credit_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["step_id", "contribution_score", "causal_confidence", "reason_codes"],
        "properties": {
            "step_id": {"type": "string", "minLength": 1},
            "contribution_score": {"type": "number", "minimum": -1, "maximum": 1},
            "causal_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason_codes": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }


SCHEMA_DEFINITIONS: dict[str, dict[str, Any]] = {
    "case_graph": _object_schema(
        "case_graph",
        "Paideia Kibo V2 Case Graph",
        (
            "case_id",
            "owner",
            "domain",
            "task_family",
            "goal",
            "context_variables",
            "observations",
            "constraints",
            "action_steps",
            "branch_events",
            "outcome_refs",
            "failure_refs",
            "source_kibo_ids",
            "evidence_hashes",
        ),
        {
            "case_id": {"type": "string", "minLength": 1},
            "owner": {"type": "string", "minLength": 1},
            "domain": {"type": "string", "minLength": 1},
            "task_family": {"type": "string", "minLength": 1},
            "goal": {"type": "string"},
            "context_variables": {"type": "array", "items": _typed_value_schema()},
            "observations": {"type": "array", "items": _observation_spec_schema()},
            "constraints": {"type": "array", "items": _constraint_schema()},
            "action_steps": {"type": "array", "items": _action_step_evidence_schema()},
            "branch_events": {"type": "array", "items": _branch_event_schema()},
            "outcome_refs": {"type": "array", "items": {"type": "string"}},
            "failure_refs": {"type": "array", "items": {"type": "string"}},
            "source_kibo_ids": {"type": "array", "items": {"type": "string"}},
            "evidence_hashes": {"type": "array", "items": {"type": "string"}},
        },
    ),
    "action_pattern": _object_schema(
        "action_pattern",
        "Paideia Kibo V2 Action Pattern",
        (
            "pattern_id",
            "pattern_version",
            "parent_pattern_version",
            "owner",
            "domain",
            "task_family",
            "goal_template",
            "input_slots",
            "preconditions",
            "required_observations",
            "steps",
            "transitions",
            "invariants",
            "abort_conditions",
            "recovery_actions",
            "success_conditions",
            "forbidden_contexts",
            "required_capabilities",
            "source_case_ids",
            "validation_profile_id",
            "lifecycle_status",
        ),
        {
            "pattern_id": {"type": "string", "minLength": 1},
            "pattern_version": {"type": "string", "minLength": 1},
            "parent_pattern_version": {"type": ["string", "null"]},
            "owner": {"type": "string", "minLength": 1},
            "domain": {"type": "string", "minLength": 1},
            "task_family": {"type": "string", "minLength": 1},
            "goal_template": {"type": "string"},
            "input_slots": {"type": "array", "items": _typed_slot_schema()},
            "preconditions": {"type": "array", "items": _predicate_schema()},
            "required_observations": {"type": "array", "items": _observation_requirement_schema()},
            "steps": {"type": "array", "items": _action_node_schema()},
            "transitions": {"type": "array", "items": _transition_schema()},
            "invariants": {"type": "array", "items": _predicate_schema()},
            "abort_conditions": {"type": "array", "items": _predicate_schema()},
            "recovery_actions": {"type": "array", "items": _recovery_action_schema()},
            "success_conditions": {"type": "array", "items": _predicate_schema()},
            "forbidden_contexts": {"type": "array", "items": _predicate_schema()},
            "required_capabilities": {"type": "array", "items": {"type": "string"}},
            "source_case_ids": {"type": "array", "items": {"type": "string"}},
            "validation_profile_id": {"type": ["string", "null"]},
            "lifecycle_status": {
                "enum": [
                    "draft",
                    "review_quarantine",
                    "structural_validated",
                    "behavioral_validated",
                    "shadow_validated",
                    "field_validated",
                    "promoted",
                    "suspended",
                    "revoked",
                ]
            },
        },
    ),
    "behavioral_exam": _object_schema(
        "behavioral_exam",
        "Paideia Kibo V2 Behavioral Exam Result",
        (
            "exam_id",
            "pattern_id",
            "pattern_version",
            "scenario_pack_id",
            "scenario_results",
            "task_success_rate",
            "invariant_pass_rate",
            "transfer_score",
            "abstention_precision",
            "efficiency_score",
            "safety_violation_count",
            "leakage_detected",
            "passed",
            "evidence_hashes",
        ),
        {
            "exam_id": {"type": "string", "minLength": 1},
            "pattern_id": {"type": "string", "minLength": 1},
            "pattern_version": {"type": "string", "minLength": 1},
            "scenario_pack_id": {"type": "string", "minLength": 1},
            "scenario_results": {"type": "array", "items": _scenario_result_schema()},
            "task_success_rate": {"type": "number", "minimum": 0, "maximum": 1},
            "invariant_pass_rate": {"type": "number", "minimum": 0, "maximum": 1},
            "transfer_score": {"type": "number", "minimum": 0, "maximum": 1},
            "abstention_precision": {"type": "number", "minimum": 0, "maximum": 1},
            "efficiency_score": {"type": "number", "minimum": 0, "maximum": 1},
            "safety_violation_count": {"type": "integer", "minimum": 0},
            "leakage_detected": {"type": "boolean"},
            "passed": {"type": "boolean"},
            "evidence_hashes": {"type": "array", "items": {"type": "string"}},
        },
    ),
    "validation_profile": _object_schema(
        "validation_profile",
        "Paideia Kibo V2 Pattern Validation Profile",
        (
            "profile_id",
            "pattern_id",
            "pattern_version",
            "structural_exam_passed",
            "behavioral_exam_passed",
            "near_transfer_passed",
            "far_transfer_passed",
            "adversarial_exam_passed",
            "shadow_validation_passed",
            "field_validation_passed",
            "critic_clearance_passed",
            "evidence_fresh_until",
            "high_risk_eligible",
            "evidence_refs",
        ),
        {
            "profile_id": {"type": "string", "minLength": 1},
            "pattern_id": {"type": "string", "minLength": 1},
            "pattern_version": {"type": "string", "minLength": 1},
            "structural_exam_passed": {"type": "boolean"},
            "behavioral_exam_passed": {"type": "boolean"},
            "near_transfer_passed": {"type": "boolean"},
            "far_transfer_passed": {"type": "boolean"},
            "adversarial_exam_passed": {"type": "boolean"},
            "shadow_validation_passed": {"type": "boolean"},
            "field_validation_passed": {"type": "boolean"},
            "critic_clearance_passed": {"type": "boolean"},
            "evidence_fresh_until": {"type": ["string", "null"]},
            "high_risk_eligible": {"type": "boolean"},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
        },
    ),
    "outcome_evidence": _object_schema(
        "outcome_evidence",
        "Paideia Kibo V2 Outcome Evidence",
        (
            "evidence_id",
            "pattern_id",
            "pattern_version",
            "task_id",
            "run_id",
            "environment_fingerprint",
            "task_difficulty",
            "started_at",
            "observed_at",
            "outcome_latency_seconds",
            "technical_score",
            "safety_score",
            "user_utility_score",
            "binary_success",
            "baseline_ref",
            "verifier_type",
            "verifier_id",
            "provenance",
            "action_receipt_refs",
            "artifact_hashes",
            "confidence",
            "status",
        ),
        {
            "evidence_id": {"type": "string", "minLength": 1},
            "pattern_id": {"type": "string", "minLength": 1},
            "pattern_version": {"type": "string", "minLength": 1},
            "task_id": {"type": "string", "minLength": 1},
            "run_id": {"type": "string", "minLength": 1},
            "environment_fingerprint": {"type": "string"},
            "task_difficulty": {"type": "number", "minimum": 0, "maximum": 1},
            "started_at": {"type": "string"},
            "observed_at": {"type": "string"},
            "outcome_latency_seconds": {"type": ["number", "null"], "minimum": 0},
            "technical_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "safety_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "user_utility_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "binary_success": {"type": ["boolean", "null"]},
            "baseline_ref": {"type": ["string", "null"]},
            "verifier_type": {"type": "string"},
            "verifier_id": {"type": ["string", "null"]},
            "provenance": {"type": "array", "items": _evidence_source_schema()},
            "action_receipt_refs": {"type": "array", "items": {"type": "string"}},
            "artifact_hashes": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "status": {"enum": ["pending", "verified", "contested", "invalidated", "expired"]},
        },
    ),
    "attribution_report": _object_schema(
        "attribution_report",
        "Paideia Kibo V2 Outcome Attribution Report",
        (
            "report_id",
            "outcome_evidence_id",
            "pattern_contribution",
            "llm_contribution",
            "tool_contribution",
            "human_contribution",
            "environment_contribution",
            "attribution_confidence",
            "confounders",
            "comparison_baseline",
            "step_credits",
        ),
        {
            "report_id": {"type": "string", "minLength": 1},
            "outcome_evidence_id": {"type": "string", "minLength": 1},
            "pattern_contribution": {"type": "number", "minimum": 0, "maximum": 1},
            "llm_contribution": {"type": "number", "minimum": 0, "maximum": 1},
            "tool_contribution": {"type": "number", "minimum": 0, "maximum": 1},
            "human_contribution": {"type": "number", "minimum": 0, "maximum": 1},
            "environment_contribution": {"type": "number", "minimum": 0, "maximum": 1},
            "attribution_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "confounders": {"type": "array", "items": {"type": "string"}},
            "comparison_baseline": {"type": ["string", "null"]},
            "step_credits": {"type": "array", "items": _step_credit_schema()},
        },
    ),
    "pattern_revision": _object_schema(
        "pattern_revision",
        "Paideia Kibo V2 Pattern Revision Proposal",
        (
            "revision_id",
            "pattern_id",
            "from_pattern_version",
            "proposed_pattern_version",
            "revision_reasons",
            "proposed_changes",
            "evidence_refs",
            "requires_behavioral_exam",
            "requires_shadow_validation",
            "status",
        ),
        {
            "revision_id": {"type": "string", "minLength": 1},
            "pattern_id": {"type": "string", "minLength": 1},
            "from_pattern_version": {"type": "string", "minLength": 1},
            "proposed_pattern_version": {"type": "string", "minLength": 1},
            "revision_reasons": {"type": "array", "items": {"type": "string"}},
            "proposed_changes": {"type": "array", "items": {"type": "object"}},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
            "requires_behavioral_exam": {"type": "boolean"},
            "requires_shadow_validation": {"type": "boolean"},
            "status": {"enum": ["draft", "quarantined", "testing", "accepted", "rejected", "rolled_back"]},
        },
    ),
    "token_usage_receipt": _object_schema(
        "token_usage_receipt",
        "Paideia Kibo V2 Token Usage Receipt",
        (
            "receipt_id",
            "run_id",
            "provider",
            "model",
            "call_purpose",
            "input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "estimated",
            "estimation_method",
            "monetary_cost",
            "latency_ms",
            "created_at",
        ),
        {
            "receipt_id": {"type": "string", "minLength": 1},
            "run_id": {"type": "string", "minLength": 1},
            "provider": {"type": "string"},
            "model": {"type": "string"},
            "call_purpose": {"type": "string"},
            "input_tokens": {"type": ["integer", "null"], "minimum": 0},
            "output_tokens": {"type": ["integer", "null"], "minimum": 0},
            "cached_input_tokens": {"type": ["integer", "null"], "minimum": 0},
            "estimated": {"type": "boolean"},
            "estimation_method": {"type": ["string", "null"]},
            "monetary_cost": {"type": ["number", "null"], "minimum": 0},
            "latency_ms": {"type": ["integer", "null"], "minimum": 0},
            "created_at": {"type": "string"},
        },
    ),
}


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "null":
        return value is None
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    return True


def _validate_json_schema(value: Any, schema: dict[str, Any], path: str) -> None:
    expected_types = schema.get("type")
    if expected_types is not None:
        allowed = [expected_types] if isinstance(expected_types, str) else list(expected_types)
        if not any(_matches_type(value, expected_type) for expected_type in allowed):
            raise ValueError(f"{path}: expected {allowed}, got {type(value).__name__}")
        if value is None:
            return
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: unsupported value {value!r}")
    if isinstance(value, str):
        if "minLength" in schema and len(value) < int(schema["minLength"]):
            raise ValueError(f"{path}: string shorter than minLength")
        if "maxLength" in schema and len(value) > int(schema["maxLength"]):
            raise ValueError(f"{path}: string longer than maxLength")
        if "pattern" in schema and re.search(str(schema["pattern"]), value) is None:
            raise ValueError(f"{path}: string does not match pattern")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{path}: number below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"{path}: number above maximum")
    if isinstance(value, dict):
        required = tuple(schema.get("required") or ())
        for field_name in required:
            if field_name not in value:
                raise ValueError(f"Missing required field {path}.{field_name}")
        properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
        additional = schema.get("additionalProperties", True)
        if additional is False:
            extra_fields = sorted(set(value) - set(properties))
            if extra_fields:
                raise ValueError(f"{path}: unexpected fields {extra_fields}")
        for field_name, field_value in value.items():
            if field_name in properties:
                _validate_json_schema(field_value, properties[field_name], f"{path}.{field_name}")
            elif isinstance(additional, dict):
                _validate_json_schema(field_value, additional, f"{path}.{field_name}")
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for index, item in enumerate(value):
            _validate_json_schema(item, schema["items"], f"{path}[{index}]")


def validate_contract_payload(artifact: dict[str, Any], *, contract_name: str) -> None:
    _validate_json_schema(artifact, get_schema(contract_name), "$")


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def contract_hash(name: str) -> str:
    if name not in SCHEMA_DEFINITIONS:
        raise KeyError(f"Unknown contract schema: {name}")
    return hashlib.sha256(canonical_json(SCHEMA_DEFINITIONS[name]).encode("utf-8")).hexdigest()


def contract_hashes() -> dict[str, str]:
    return {name: contract_hash(name) for name in CONTRACT_NAMES}


def get_schema(name: str) -> dict[str, Any]:
    if name not in SCHEMA_DEFINITIONS:
        raise KeyError(f"Unknown contract schema: {name}")
    return json.loads(canonical_json(SCHEMA_DEFINITIONS[name]))


def schema_registry() -> dict[str, Any]:
    return {
        "schema": "paideia-kibo-v2-schema-registry/v1",
        "contracts_release": CONTRACTS_RELEASE,
        "schema_ids": dict(SCHEMA_IDS),
        "contract_hashes": contract_hashes(),
    }


def validate_contract_header(artifact: dict[str, Any], *, contract_name: str) -> None:
    expected_schema = SCHEMA_IDS[contract_name]
    if artifact.get("schema") != expected_schema:
        raise ValueError(f"Unsupported schema for {contract_name}: {artifact.get('schema')}")
    schema_version = str(artifact.get("schema_version") or "")
    if not schema_version.startswith("2."):
        raise ValueError(f"Unsupported major schema_version for {contract_name}: {schema_version}")
    expected_hash = contract_hash(contract_name)
    if artifact.get("contract_hash") != expected_hash:
        raise ValueError(f"Contract hash mismatch for {contract_name}")
    validate_contract_payload(artifact, contract_name=contract_name)
