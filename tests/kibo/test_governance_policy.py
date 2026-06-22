from paideia_engines.kibo import ReuseDecision, TaskFingerprint, evaluate_kibo_governance


def test_governance_blocks_high_risk_direct_reuse():
    task = TaskFingerprint(
        task_id="task-1",
        owner="Boss",
        domain="investment_research",
        task_type="comparative_analysis",
        intent="assess_buy_opportunity",
        constraints=("current_data_required",),
        required_capabilities=("web_research", "valuation"),
        risk_level="high",
        freshness_required=True,
        expected_output_type="report",
        user_style_markers=("conclusion_first",),
    )
    decision = ReuseDecision(
        decision_id="reuse-1",
        task_id="task-1",
        selected_kibo_ids=("kibo-1",),
        similarity_score=0.9,
        confidence_score=0.8,
        risk_score=1.0,
        reuse_mode="direct_reuse",
        llm_required_parts=("fresh_external_data",),
        reason="test",
    )

    review = evaluate_kibo_governance(decision, task=task)

    assert review["decision"] == "blocked"
    assert "high_risk_direct_reuse_forbidden" in review["blocked_reasons"]
    assert review["runtime_policy"]["hidden_chain_of_thought_reuse"] is False
