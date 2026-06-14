from paideia_engines.stress import StressEngine


def test_stress_engine_generates_rollout_without_promoting_memory():
    engine = StressEngine()

    rollout = engine.run_rollout(
        learner_id="agent:analyst",
        scenario_id="conflicting_evidence",
        response="I will compare sources, mark uncertainty, and ask for review.",
    )

    assert rollout["schema"] == "paideia-stress-rollout/v1"
    assert rollout["scenario_id"] == "conflicting_evidence"
    assert rollout["status"] == "promotion_candidate"
    assert rollout["expected_learning_signal"] == "evidence_reconciliation"
    assert "promotion_decision" not in rollout
