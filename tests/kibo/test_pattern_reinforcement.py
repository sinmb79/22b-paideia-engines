import pytest

from paideia_engines.kibo import (
    CriticReport,
    PatternCandidate,
    PatternExamResult,
    RealWorldOutcome,
    ReuseDecision,
    TaskFingerprint,
    evaluate_kibo_governance,
    reinforce_pattern,
)


def _pattern(**overrides):
    data = {
        "pattern_id": "pattern-1",
        "owner": "Boss",
        "domain": "software_agent_engineering",
        "task_family": "implementation",
        "abstract_strategy": ("inspect", "patch", "test"),
        "required_conditions": ("code_inspection", "test_execution"),
        "known_failure_modes": ("missing_tests",),
        "source_kibo_ids": ("kibo-1", "kibo-2"),
        "exam_score": None,
        "real_world_score": None,
        "reinforcement_score": 0.4,
        "status": "draft",
    }
    data.update(overrides)
    return PatternCandidate(**data)


def test_pattern_requires_source_kibo_ids():
    with pytest.raises(ValueError):
        _pattern(source_kibo_ids=())


def test_reinforcement_requires_real_world_success_for_reinforced_status():
    pattern = _pattern(status="exam_validated")
    report = reinforce_pattern(
        pattern,
        exam_results=[PatternExamResult("exam-1", pattern.pattern_id, "task-1", 0.95, True, (), ())],
        outcomes=[
            RealWorldOutcome(
                "outcome-1",
                pattern.pattern_id,
                "task-1",
                "2026-06-22T00:00:00Z",
                "task_outcome",
                False,
                0.1,
                None,
                2,
                "overgeneralization",
                (),
            )
        ],
        critic_reports=[CriticReport("critic-1", pattern.pattern_id, (), (), (), ("guard",), True)],
    )

    assert report["pattern"]["status"] != "reinforced"


def test_critical_failure_quarantines_pattern():
    pattern = _pattern(status="field_validated", exam_score=0.8, real_world_score=0.8)
    report = reinforce_pattern(
        pattern,
        outcomes=[
            RealWorldOutcome(
                "outcome-1",
                pattern.pattern_id,
                "task-1",
                "2026-06-22T00:00:00Z",
                "task_outcome",
                False,
                0.0,
                None,
                1,
                "domain_mismatch",
                (),
            )
        ],
    )

    assert report["pattern"]["status"] == "quarantined"


def test_governance_blocks_high_risk_pattern_without_critic_gate():
    task = TaskFingerprint(
        task_id="task-1",
        owner="Boss",
        domain="investment_research",
        task_type="comparative_analysis",
        intent="assess_buy_opportunity",
        constraints=(),
        required_capabilities=("valuation",),
        risk_level="high",
        freshness_required=False,
        expected_output_type="report",
        user_style_markers=(),
    )
    decision = ReuseDecision(
        decision_id="reuse-1",
        task_id="task-1",
        selected_kibo_ids=("kibo-1",),
        similarity_score=0.9,
        confidence_score=0.8,
        risk_score=1.0,
        reuse_mode="direct_reuse",
        llm_required_parts=("validation_failure:self_critic_gate",),
        reason="test",
        pattern_id="pattern-1",
        pattern_status="field_validated",
        exam_validated=True,
        field_validated=True,
        critic_required=True,
    )

    review = evaluate_kibo_governance(decision, task=task)

    assert review["decision"] == "blocked"
    assert "self_critic_gate_required" in review["blocked_reasons"]
