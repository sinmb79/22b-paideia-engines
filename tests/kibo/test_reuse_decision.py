from paideia_engines.kibo import KiboRecord, TaskFingerprint, decide_reuse, score_reuse_candidate


def _task(**overrides):
    data = {
        "task_id": "task-1",
        "owner": "Boss",
        "domain": "software_agent_engineering",
        "task_type": "implementation",
        "intent": "implement_requested_change",
        "constraints": ("tests_required",),
        "required_capabilities": ("code_inspection", "test_execution"),
        "risk_level": "low",
        "freshness_required": False,
        "expected_output_type": "code_change",
        "user_style_markers": (),
    }
    data.update(overrides)
    return TaskFingerprint(**data)


def _record(**overrides):
    data = {
        "kibo_id": "kibo-1",
        "source_run_id": "run-1",
        "owner": "Boss",
        "domain": "software_agent_engineering",
        "task_type": "implementation",
        "problem_signature": "Implement a CLI feature with tests.",
        "solution_steps": ("inspect", "patch", "pytest"),
        "reusable_logic": ("code_inspection", "test_execution"),
        "failure_modes": (),
        "required_inputs": ("code_inspection", "test_execution"),
        "output_template": "patch",
        "evidence_refs": ("reviewed-run",),
        "success_score": 94,
        "promotion_status": "promoted",
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
    }
    data.update(overrides)
    return KiboRecord(**data)


def test_same_domain_same_task_gets_direct_reuse_when_low_risk():
    decision = decide_reuse(_task(), [_record()])

    assert decision.reuse_mode == "direct_reuse"
    assert decision.selected_kibo_ids == ("kibo-1",)


def test_unreviewed_or_quarantined_records_do_not_influence_decision():
    decision = decide_reuse(_task(), [_record(promotion_status="quarantine")])

    assert decision.reuse_mode == "reject_and_solve_fresh"
    assert decision.selected_kibo_ids == ()


def test_different_domain_scores_lower():
    score = score_reuse_candidate(_task(domain="investment_research"), _record())

    assert score["reuse_score"] < 0.65
