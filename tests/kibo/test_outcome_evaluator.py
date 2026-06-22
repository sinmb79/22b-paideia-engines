from paideia_engines.kibo import KiboRecord, ReuseDecision
from paideia_engines.kibo.outcome_evaluator import apply_outcome, evaluate_kibo_outcome


def _decision():
    return ReuseDecision(
        decision_id="reuse-1",
        task_id="task-1",
        selected_kibo_ids=("kibo-1",),
        similarity_score=0.8,
        confidence_score=0.7,
        risk_score=0.2,
        reuse_mode="partial_reuse",
        llm_required_parts=("fresh_external_data",),
        reason="test",
    )


def _record():
    return KiboRecord(
        kibo_id="kibo-1",
        source_run_id="run-1",
        owner="Boss",
        domain="investment_research",
        task_type="comparative_analysis",
        problem_signature="Investment research.",
        solution_steps=("step",),
        reusable_logic=("valuation",),
        failure_modes=(),
        required_inputs=("valuation",),
        output_template="report",
        evidence_refs=("reviewed-run",),
        success_score=90,
        promotion_status="promoted",
        created_at="2026-06-01T00:00:00Z",
        updated_at="2026-06-01T00:00:00Z",
    )


def test_failed_outcome_requires_quarantine_and_updates_record():
    evaluation = evaluate_kibo_outcome(
        _decision(),
        validation_passed=False,
        quality_score=40,
        evidence_ref="failed-run",
    )
    updated = apply_outcome(_record(), evaluation)

    assert evaluation["outcome"] == "failure"
    assert evaluation["quarantine_required"] is True
    assert updated.promotion_status == "quarantine"
    assert "reuse_failed_validation" in updated.failure_modes
