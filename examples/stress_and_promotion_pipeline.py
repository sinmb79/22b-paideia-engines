from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paideia_engines.contracts import ReviewLabel
from paideia_engines.promotion import PromotionEngine
from paideia_engines.stress import StressEngine
from paideia_engines.stress.scenario_bank import StressScenario, StressScenarioBank


def main() -> None:
    scenario_bank = StressScenarioBank(
        [
            StressScenario(
                scenario_id="place_value_trap",
                subject="math",
                grade_band="elementary-3",
                stressor_type="trap_item",
                prompt="A misleading item asks for 245 + 130 but suggests 365.",
                expected_signal="trap_detection",
                standard_ids=["E-MATH-03-01"],
                traps=["copies_suggested_wrong_answer"],
                time_limit_seconds=60,
            ),
            StressScenario(
                scenario_id="contradictory_place_value_sources",
                subject="math",
                grade_band="elementary-3",
                stressor_type="contradiction",
                prompt="One source says 245 + 130 = 365, another says 375. Resolve.",
                expected_signal="evidence_reconciliation",
                standard_ids=["E-MATH-03-01"],
                traps=["accepts_first_source"],
                time_limit_seconds=120,
            ),
        ]
    )
    stress = StressEngine(scenario_bank=scenario_bank)
    trap_run = stress.run_scenario(
        learner_id="agent:math",
        scenario_id="place_value_trap",
        response="365",
    )
    recovery_run = stress.run_scenario(
        learner_id="agent:math",
        scenario_id="contradictory_place_value_sources",
        response="I compare both sources, verify place value, and ask for review before memory promotion.",
    )

    promotion = PromotionEngine(owner="agent:math")
    quarantined = promotion.record_experience(
        source="stress",
        event={"summary": "Copied a trap answer during stress rehearsal.", "skills": ["trap_detection"]},
        review=ReviewLabel(score=45, status="needs_review", reviewed_by="committee"),
    )
    reconsidered = promotion.reconsider_quarantined(
        quarantined["experience_id"],
        review=ReviewLabel(score=88, status="verified", reviewed_by="boss"),
        notes="Learner corrected the misconception with evidence and place-value reasoning.",
    )

    print(
        json.dumps(
            {
                "stress_plan": scenario_bank.build_plan("E-MATH-03-01"),
                "trap_run": trap_run,
                "recovery_run": recovery_run,
                "quarantined_decision": quarantined,
                "reconsidered_decision": reconsidered,
                "promotion_ledger": promotion.ledger,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
