from paideia_engines.orchestration import PaideiaEngineSuite


def test_orchestration_runs_end_to_end_growth_cycle():
    suite = PaideiaEngineSuite()

    cycle = suite.run_growth_cycle(
        learner_id="agent:analyst",
        role="research analyst",
        objectives=["evidence-first answers"],
        task="prepare evidence summary",
    )

    assert cycle["schema"] == "paideia-growth-cycle/v1"
    assert cycle["blueprint"]["schema"] == "paideia-cultivation-blueprint/v1"
    assert cycle["assessment"]["passed"] is True
    assert cycle["governance_review"]["decision"] == "allowed"
    assert cycle["runtime_run"]["status"] == "completed_needs_review"
    assert cycle["stress_rollout"]["status"] == "promotion_candidate"
    assert cycle["promotion_decision"]["status"] == "promoted"
