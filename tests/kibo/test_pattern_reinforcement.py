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


def test_quarantined_pattern_stays_quarantined_after_success():
    pattern = _pattern(status="quarantined", exam_score=0.9, real_world_score=0.9, reinforcement_score=0.9)
    report = reinforce_pattern(
        pattern,
        outcomes=[
            RealWorldOutcome("outcome-1", pattern.pattern_id, "task-1", "now", "task", True, 1.0, None, 10, None, ())
        ],
        critic_reports=[CriticReport("critic-1", pattern.pattern_id, (), (), (), ("guard",), True)],
    )

    assert report["pattern"]["status"] == "quarantined"


def test_failed_exam_blocks_exam_validation_despite_high_score():
    pattern = _pattern(status="draft")
    report = reinforce_pattern(
        pattern,
        exam_results=[
            PatternExamResult("exam-1", pattern.pattern_id, "task-1", 0.95, False, ("mistake",), ())
        ],
        outcomes=[
            RealWorldOutcome("outcome-1", pattern.pattern_id, "task-1", "now", "task", True, 0.9, None, 9, None, ())
        ],
    )

    assert report["pattern"]["status"] == "draft"


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
    assert "high_risk_direct_reuse_forbidden" in review["blocked_reasons"]
    assert "validation_required_before_direct_reuse" in review["blocked_reasons"]


def test_governance_blocks_namespaced_validation_failure_for_direct_reuse():
    decision = ReuseDecision(
        decision_id="reuse-1",
        task_id="task-1",
        selected_kibo_ids=("kibo-1",),
        similarity_score=0.9,
        confidence_score=0.8,
        risk_score=0.1,
        reuse_mode="direct_reuse",
        llm_required_parts=("validation_failure:failure_memory",),
        reason="test",
    )

    review = evaluate_kibo_governance(decision)

    assert review["decision"] == "blocked"
    assert "validation_required_before_direct_reuse" in review["blocked_reasons"]


def test_mixed_case_high_risk_is_normalized():
    task = TaskFingerprint.from_dict(
        {
            "task_id": "task-1",
            "risk_level": "HIGH",
        }
    )

    assert task.risk_level == "high"


def test_reinforcement_requires_specific_remediated_weakness_ids():
    pattern = _pattern(
        status="field_validated",
        exam_score=0.95,
        real_world_score=0.95,
        reinforcement_score=0.9,
    )
    weakness = {
        "weakness_id": "weakness-code-inspection",
        "owner": "Boss",
        "domain": "software_agent_engineering",
        "skill_id": "code_inspection",
        "severity": 0.75,
        "recurrence_count": 1,
    }
    common = {
        "exam_results": [PatternExamResult("exam-1", pattern.pattern_id, "task-1", 0.95, True, (), ())],
        "outcomes": [
            RealWorldOutcome("outcome-1", pattern.pattern_id, "task-1", "now", "task", True, 0.95, None, 10, None, ())
        ],
        "critic_reports": [CriticReport("critic-1", pattern.pattern_id, (), (), (), ("guard",), True)],
        "weakness_records": [weakness],
    }

    unremediated = reinforce_pattern(pattern, curriculum_remediated=True, **common)
    remediated = reinforce_pattern(
        pattern,
        curriculum_remediated=True,
        remediated_weakness_ids=("weakness-code-inspection",),
        **common,
    )

    assert unremediated["pattern"]["status"] != "reinforced"
    assert unremediated["pattern"]["reinforcement_score"] <= 0.69
    assert remediated["pattern"]["status"] == "reinforced"
