from paideia_engines.curriculum import (
    WeaknessRecord,
    apply_curriculum_completion,
    build_adaptive_exam_report,
    build_curriculum_generation_report,
    detect_weaknesses,
    generate_adaptive_exam,
    generate_curriculum_plan,
)
from paideia_engines.kibo import (
    CriticReport,
    FailureMemory,
    PatternCandidate,
    PatternExamResult,
    RealWorldOutcome,
    ReuseDecision,
    TaskFingerprint,
    evaluate_kibo_governance,
    reinforce_pattern,
)


def _failure(**overrides):
    data = {
        "failure_id": "failure-1",
        "pattern_id": "pattern-1",
        "task_id": "task-1",
        "error_type": "macro_ignored",
        "severity": "high",
        "trigger_conditions": ("investment_research",),
        "missed_signals": ("yield_curve",),
        "prevention_rules": ("check_macro_regime",),
        "created_at": "2026-06-22T00:00:00Z",
    }
    data.update(overrides)
    return FailureMemory(**data)


def _pattern(**overrides):
    data = {
        "pattern_id": "pattern-1",
        "owner": "Boss",
        "domain": "investment_research",
        "task_family": "comparative_analysis",
        "abstract_strategy": ("valuation", "macro_regime_analysis", "risk_assessment"),
        "required_conditions": ("valuation", "macro_regime_analysis", "risk_assessment"),
        "known_failure_modes": ("macro_ignored",),
        "source_kibo_ids": ("kibo-1", "kibo-2"),
        "exam_score": 0.9,
        "real_world_score": 0.9,
        "reinforcement_score": 0.9,
        "status": "field_validated",
    }
    data.update(overrides)
    return PatternCandidate(**data)


def test_failure_memory_creates_weakness_record():
    weaknesses = detect_weaknesses([_failure()], owner="Boss", domain="investment_research")

    assert len(weaknesses) == 1
    assert weaknesses[0].skill_id == "macro_regime_analysis"
    assert weaknesses[0].weakness_type == "knowledge_gap"
    assert weaknesses[0].severity >= 0.75


def test_repeated_failures_increase_weakness_severity_and_recurrence():
    weaknesses = detect_weaknesses(
        [
            _failure(failure_id="failure-1"),
            _failure(failure_id="failure-2"),
            _failure(failure_id="failure-3"),
        ],
        domain="investment_research",
    )

    assert weaknesses[0].recurrence_count == 3
    assert weaknesses[0].severity >= 0.85


def test_existing_weakness_merge_does_not_duplicate_same_evidence():
    first = detect_weaknesses([_failure()], domain="investment_research")[0]
    merged = detect_weaknesses([_failure()], domain="investment_research", existing_weaknesses=[first])[0]

    assert merged.evidence_refs == first.evidence_refs
    assert merged.recurrence_count == 1


def test_weakness_generates_curriculum_plan_with_related_skills():
    weakness = detect_weaknesses([_failure()], domain="investment_research")[0]
    plan = generate_curriculum_plan(weakness, related_skills=("liquidity", "bond_market"))

    assert plan.weakness_id == weakness.weakness_id
    assert "macro_regime_analysis" in plan.learning_goals
    assert "liquidity" in plan.learning_goals
    assert plan.target_score >= 0.8


def test_curriculum_plan_generates_adaptive_exam():
    weakness = WeaknessRecord(
        "weakness-1",
        "Boss",
        "investment_research",
        "macro_regime_analysis",
        "knowledge_gap",
        ("failure-1",),
        0.82,
        2,
    )
    plan = generate_curriculum_plan(weakness)
    exam = generate_adaptive_exam(plan, weakness=weakness)

    assert exam.curriculum_id == plan.curriculum_id
    assert exam.difficulty == "remediation"
    assert len(exam.questions) >= 5


def test_exam_completion_reduces_or_increases_weakness():
    weakness = WeaknessRecord("w1", "Boss", "general", "risk_assessment", "risk_gap", ("f1",), 0.8, 2)

    passed = apply_curriculum_completion(weakness, passed=True, score=0.9, transfer_passed=True, retention_passed=True)
    failed = apply_curriculum_completion(weakness, passed=False, score=0.3)
    below_target = apply_curriculum_completion(weakness, passed=True, score=0.6, target_score=0.85)
    no_transfer = apply_curriculum_completion(weakness, passed=True, score=0.95, target_score=0.85)

    assert passed["updated_weakness"]["severity"] < weakness.severity
    assert failed["updated_weakness"]["severity"] > weakness.severity
    assert failed["updated_weakness"]["recurrence_count"] == 3
    assert below_target["effective_passed"] is False
    assert below_target["updated_weakness"]["severity"] > weakness.severity
    assert no_transfer["effective_passed"] is False
    assert no_transfer["action"] == "weakness_increased"


def test_exam_completion_rejects_non_finite_scores_fail_closed():
    weakness = WeaknessRecord("w1", "Boss", "general", "risk_assessment", "risk_gap", ("f1",), 0.8, 2)

    completion = apply_curriculum_completion(
        weakness,
        passed=True,
        score=float("nan"),
        target_score=0.85,
        transfer_passed=True,
        retention_passed=True,
    )

    assert completion["effective_passed"] is False
    assert completion["score"] == 0.0
    assert completion["action"] == "weakness_increased"
    assert completion["updated_weakness"]["severity"] > weakness.severity


def test_weakness_record_rejects_non_finite_severity_fail_closed():
    weakness = WeaknessRecord("w1", "Boss", "general", "risk_assessment", "risk_gap", ("f1",), float("nan"), 1)

    assert weakness.severity == 0.0


def test_high_severity_weakness_blocks_direct_reuse_governance():
    task = TaskFingerprint(
        "task-1",
        "Boss",
        "investment_research",
        "comparative_analysis",
        "assess",
        (),
        ("macro_regime_analysis",),
        "medium",
        False,
        "report",
        (),
    )
    decision = ReuseDecision(
        "reuse-1",
        "task-1",
        ("kibo-1",),
        0.9,
        0.9,
        0.1,
        "direct_reuse",
        (),
        "test",
        pattern_id="pattern-1",
        pattern_status="field_validated",
        exam_validated=True,
        field_validated=True,
    )
    weakness = WeaknessRecord(
        "weakness-1",
        "Boss",
        "investment_research",
        "macro_regime_analysis",
        "knowledge_gap",
        ("failure-1",),
        0.85,
        2,
    )

    review = evaluate_kibo_governance(decision, task=task, weakness_records=[weakness])

    assert review["decision"] == "blocked"
    assert "active_weakness_blocks_direct_reuse" in review["blocked_reasons"]
    assert "high_severity_weakness_requires_reexam" in review["blocked_reasons"]


def test_single_high_failure_weakness_blocks_direct_reuse_governance():
    task = TaskFingerprint(
        "task-1",
        "Boss",
        "investment_research",
        "comparative_analysis",
        "assess",
        (),
        ("macro_regime_analysis",),
        "medium",
        False,
        "report",
        (),
    )
    decision = ReuseDecision(
        "reuse-1",
        "task-1",
        ("kibo-1",),
        0.9,
        0.9,
        0.1,
        "direct_reuse",
        (),
        "test",
    )
    weakness = detect_weaknesses([_failure()], domain="investment_research")[0]

    review = evaluate_kibo_governance(decision, task=task, weakness_records=[weakness])

    assert weakness.severity == 0.75
    assert review["decision"] == "blocked"
    assert "active_weakness_blocks_direct_reuse" in review["blocked_reasons"]


def test_repeated_weakness_prevents_reinforcement_without_remediation():
    pattern = _pattern(status="field_validated")
    weakness = WeaknessRecord(
        "weakness-1",
        "Boss",
        "investment_research",
        "macro_regime_analysis",
        "knowledge_gap",
        ("failure-1",),
        0.7,
        3,
    )

    report = reinforce_pattern(
        pattern,
        exam_results=[PatternExamResult("exam-1", pattern.pattern_id, "task-1", 0.95, True, (), ())],
        outcomes=[
            RealWorldOutcome("outcome-1", pattern.pattern_id, "task-1", "now", "task", True, 0.95, None, 10, None, ())
        ],
        critic_reports=[CriticReport("critic-1", pattern.pattern_id, (), (), (), ("guard",), True)],
        weakness_records=[weakness],
    )

    assert report["pattern"]["status"] == "weakened"


def test_curriculum_reports_are_reviewable_json_payloads():
    weakness = detect_weaknesses([_failure()], domain="investment_research")[0]
    curriculum_report = build_curriculum_generation_report([weakness])
    exam_report = build_adaptive_exam_report(generate_curriculum_plan(weakness), weakness=weakness)

    assert curriculum_report["schema"] == "paideia-curriculum-generation-report/v1"
    assert curriculum_report["curriculum_count"] == 1
    assert exam_report["schema"] == "paideia-adaptive-exam-generation-report/v1"
