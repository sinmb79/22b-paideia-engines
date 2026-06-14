from paideia_engines.stress import StressEngine
from paideia_engines.stress.scenario_bank import StressScenario, StressScenarioBank


def test_stress_scenario_bank_builds_domain_scenarios():
    bank = StressScenarioBank(
        [
            StressScenario(
                scenario_id="math_misconception_place_value",
                subject="math",
                grade_band="elementary-3",
                stressor_type="misconception",
                prompt="A learner says 245 + 130 = 365 because only tens changed.",
                expected_signal="misconception_repair",
                standard_ids=["E-MATH-03-01"],
                traps=["ignores_hundreds_place"],
                time_limit_seconds=90,
            ),
            StressScenario(
                scenario_id="math_time_pressure",
                subject="math",
                grade_band="elementary-3",
                stressor_type="time_pressure",
                prompt="Solve and explain 245 + 130 under a short time limit.",
                expected_signal="robust_under_time_pressure",
                standard_ids=["E-MATH-03-01"],
                traps=[],
                time_limit_seconds=20,
            ),
        ]
    )

    selected = bank.select(standard_ids=["E-MATH-03-01"], stressor_types=["misconception"])

    assert len(selected) == 1
    assert selected[0].scenario_id == "math_misconception_place_value"
    assert bank.build_plan("E-MATH-03-01")["scenario_count"] == 2


def test_stress_engine_runs_scenario_bank_without_promotion_decision():
    bank = StressScenarioBank(
        [
            StressScenario(
                scenario_id="contradictory_evidence_math",
                subject="math",
                grade_band="elementary-3",
                stressor_type="contradiction",
                prompt="One source says 245 + 130 = 365, another says 375. Resolve.",
                expected_signal="evidence_reconciliation",
                standard_ids=["E-MATH-03-01"],
                traps=["accepts_first_source"],
                time_limit_seconds=120,
            )
        ]
    )
    engine = StressEngine(scenario_bank=bank)

    result = engine.run_scenario(
        learner_id="agent:math",
        scenario_id="contradictory_evidence_math",
        response="I compare both sources, verify place value, and ask for review before memory promotion.",
    )

    assert result["schema"] == "paideia-stress-scenario-run/v1"
    assert result["scenario_id"] == "contradictory_evidence_math"
    assert result["stressor_type"] == "contradiction"
    assert result["status"] == "promotion_candidate"
    assert result["promotion_signal"]["status"] == "candidate_only"
    assert "promotion_decision" not in result


def test_stress_engine_flags_trap_failure_for_review():
    bank = StressScenarioBank(
        [
            StressScenario(
                scenario_id="trap_item_math",
                subject="math",
                grade_band="elementary-3",
                stressor_type="trap_item",
                prompt="A misleading item asks for 245 + 130 but suggests 365.",
                expected_signal="trap_detection",
                standard_ids=["E-MATH-03-01"],
                traps=["copies_suggested_wrong_answer"],
                time_limit_seconds=60,
            )
        ]
    )
    engine = StressEngine(scenario_bank=bank)

    result = engine.run_scenario(
        learner_id="agent:math",
        scenario_id="trap_item_math",
        response="365",
    )

    assert result["status"] == "needs_review"
    assert "trap_risk" in result["flags"]
    assert result["promotion_signal"]["status"] == "blocked_pending_review"
