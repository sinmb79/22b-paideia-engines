from paideia_engines.runtime import RuntimeEngine


def test_runtime_engine_returns_trace_and_acceptance_checklist():
    engine = RuntimeEngine()

    run = engine.run_task(
        agent_id="agent:analyst",
        task="prepare evidence summary",
        tools=["read_file", "summarize"],
    )

    assert run["schema"] == "paideia-runtime-run/v1"
    assert run["status"] == "completed_needs_review"
    assert run["trace"][0]["action"] == "task.accepted"
    assert run["acceptance_checklist"]["requires_review"] is True
    assert "promotion_decision" not in run
