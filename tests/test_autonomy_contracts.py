import pytest

from paideia_engines.autonomy import (
    ActionPattern,
    ActionReceipt,
    ActionStep,
    AutonomyEnvelope,
    BehavioralExamResult,
    CapabilityContract,
    CognitiveBudget,
    DeploymentStatus,
    Observation,
    OutcomeEvidence,
    SideEffectClass,
    StateFact,
    StepCredit,
    WeaknessRecord,
    WorldState,
)


def _envelope():
    return AutonomyEnvelope(
        envelope_id="env-1",
        allowed_capabilities=("cap.inspect",),
        prohibited_capabilities=("cap.actuate",),
        allowed_side_effect_classes=(SideEffectClass.READ_ONLY.value,),
        max_operation_duration_ms=1000,
        required_health_signals=("camera.ok",),
        abort_conditions=({"op": "eq", "fact": "zone.status", "value": "restricted"},),
        human_approval_scopes=("consequential",),
        offline_policy="degrade",
    )


def _budget():
    return CognitiveBudget(
        max_cycle_ms=1000,
        max_local_model_tokens=128,
        max_remote_model_tokens=0,
        max_energy_units=None,
        max_memory_mb=64,
        network_allowed=False,
        remote_calls_allowed=0,
    )


def _receipt():
    return ActionReceipt(
        receipt_id="receipt-1",
        decision_cycle_id="cycle-1",
        action_pattern_id="ap-1",
        step_id="inspect",
        capability_id="cap.inspect",
        requested_at="2026-06-23T00:00:00Z",
        completed_at="2026-06-23T00:00:01Z",
        status="succeeded",
        input_digest="sha256:input",
        output_ref="out.json",
        output_digest="sha256:output",
        observed_side_effects=("read_only",),
        error_code=None,
        rollback_status=None,
    )


def _pattern():
    return ActionPattern(
        action_pattern_id="ap-1",
        version="v1",
        source_pattern_id="pattern-1",
        source_kibo_ids=("kibo-1",),
        owner="Boss",
        domain="warehouse_robotics",
        task_family="inspection",
        required_observations=("camera.frame",),
        required_capabilities=("cap.inspect",),
        preconditions=({"op": "gte", "fact": "battery.percent", "value": 30},),
        invariants=(),
        postconditions=({"op": "exists", "fact": "inspection.report"},),
        steps=(
            ActionStep(
                step_id="inspect",
                kind="capability",
                capability_id="cap.inspect",
                input_bindings=({"source": "world_state", "target": "zone_id"},),
                guard=None,
                success_condition={"op": "exists", "fact": "inspection.report"},
                timeout_ms=300,
                max_attempts=1,
                on_success=None,
                on_failure=None,
                fallback_step_id=None,
                approval_scope=None,
            ),
        ),
        start_step_id="inspect",
        max_total_duration_ms=1000,
        cognitive_budget=_budget(),
        autonomy_envelope=_envelope(),
        learning_status="exam_validated",
        deployment_status=DeploymentStatus.COMPILED.value,
        evidence_refs=("exam-1",),
        content_digest="sha256:pattern",
    )


def test_autonomy_contracts_round_trip_core_action_pattern():
    payload = _pattern().to_dict()

    restored = ActionPattern.from_dict(payload)

    assert restored.to_dict() == payload
    assert payload["learning_status"] == "exam_validated"
    assert payload["deployment_status"] == "compiled"
    assert payload["cognitive_budget"]["network_allowed"] is False


def test_capability_contract_blocks_unknown_side_effect_class():
    with pytest.raises(ValueError, match="Unsupported side_effect_class"):
        CapabilityContract(
            capability_id="cap.shell",
            version="v1",
            input_schema_ref="input/v1",
            output_schema_ref="output/v1",
            side_effect_class="arbitrary_shell",
            required_permissions=(),
            idempotent=False,
            reversible=False,
            timeout_ms=100,
            simulator_adapter="sim.shell",
            runtime_adapter=None,
            safe_fallback_capability_id=None,
        )


def test_action_pattern_blocks_unknown_deployment_status():
    payload = _pattern().to_dict()
    payload["deployment_status"] = "online_promoted"

    with pytest.raises(ValueError, match="Unsupported deployment_status"):
        ActionPattern.from_dict(payload)


def test_behavioral_exam_result_round_trips_receipts():
    result = BehavioralExamResult(
        exam_id="exam-1",
        action_pattern_id="ap-1",
        scenario_id="scenario-1",
        exam_kind="stale_sensor",
        score=0.72,
        passed=True,
        receipts=(_receipt(),),
        outcome_evidence_id="outcome-1",
        safety_violations=(),
        trace_digest="sha256:trace",
        replay_digest="sha256:trace",
    )

    payload = result.to_dict()

    assert BehavioralExamResult.from_dict(payload).to_dict() == payload
    assert payload["receipts"][0]["schema"] == "paideia-edge-action-receipt/v1"


def test_observation_world_state_and_outcome_contracts_serialize():
    obs = Observation(
        observation_id="obs-1",
        source_id="camera-1",
        schema_ref="camera/v1",
        observed_at="2026-06-23T00:00:00Z",
        received_at="2026-06-23T00:00:01Z",
        payload_ref="blob://obs-1",
        payload_digest="sha256:obs",
        confidence=0.95,
        freshness_ms=20,
        health_status="ok",
        provenance=("simulator",),
    )
    state = WorldState(
        state_id="state-1",
        created_at="2026-06-23T00:00:01Z",
        facts=(StateFact("battery.percent", 88, 0.9, ("obs-1",), None),),
        environment_tags=("simulated",),
        sensor_health=("camera:ok",),
        state_digest="sha256:state",
    )
    outcome = OutcomeEvidence(
        outcome_id="outcome-1",
        decision_cycle_id="cycle-1",
        pattern_id="pattern-1",
        action_pattern_id="ap-1",
        immediate_score=0.8,
        delayed_score=None,
        success=True,
        safety_violations=(),
        error_type=None,
        environment_tags=("simulated",),
        confounders=(),
        evidence_refs=("receipt-1",),
        attribution_confidence=0.7,
    )
    credit = StepCredit("outcome-1", "inspect", 0.6, 0.7, ("goal_completed",))
    weakness = WeaknessRecord(
        "weakness-1",
        "Boss",
        "warehouse_robotics",
        "freshness_detection",
        "freshness_gap",
        ("outcome-1",),
        0.81,
        1,
        "open",
    )

    assert Observation.from_dict(obs.to_dict()).to_dict() == obs.to_dict()
    assert WorldState.from_dict(state.to_dict()).to_dict() == state.to_dict()
    assert outcome.to_dict()["schema"] == "paideia-edge-outcome-evidence/v1"
    assert credit.to_dict()["contribution_score"] == 0.6
    assert weakness.to_dict()["severity"] == 0.81
