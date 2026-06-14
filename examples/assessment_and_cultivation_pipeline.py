from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paideia_engines.assessment import AssessmentEngine
from paideia_engines.assessment.item_bank import AssessmentItem, ItemBank
from paideia_engines.cultivation import CultivationEngine


def main() -> None:
    learning_unit = {
        "unit_id": "elementary-grade-3-math",
        "school_level": "elementary",
        "grade": "3",
        "subject": "math",
        "standards": [
            {
                "standard_id": "E-MATH-03-01",
                "domain": "numbers_and_operations",
                "achievement": "Add and subtract within 1000 using place value.",
            }
        ],
    }
    data_plan = {
        "sources": [
            {
                "source_id": "aihub_math_problem_solving",
                "decision": "review_required",
                "license_tier": "login_or_agreement_required",
            }
        ]
    }
    bank = ItemBank(
        [
            AssessmentItem(
                item_id="math-3-001",
                standard_id="E-MATH-03-01",
                gate_id="unit_check",
                item_type="short_answer",
                prompt="What is 245 + 130?",
                answer="375",
                distractors=["365", "475"],
                explanation="245 + 130 = 375.",
                rubric={"accuracy": 80, "explanation": 20},
            )
        ]
    )
    cultivation = CultivationEngine()
    roadmap = cultivation.build_learning_roadmap(
        learning_unit=learning_unit,
        data_plan=data_plan,
        item_bank=bank,
    )
    assessment = AssessmentEngine(item_bank=bank)
    result = assessment.evaluate_item_response(
        "math-3-001",
        response={"answer": "375", "explanation": "I used place value to add 245 and 130."},
    )
    print(json.dumps({"roadmap": roadmap, "assessment_result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
