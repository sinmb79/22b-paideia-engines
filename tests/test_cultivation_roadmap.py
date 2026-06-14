from paideia_engines.assessment.item_bank import AssessmentItem, ItemBank
from paideia_engines.cultivation import CultivationEngine


def test_cultivation_engine_builds_roadmap_from_learning_unit_and_sources():
    engine = CultivationEngine()
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
            },
            {
                "source_id": "digital_textbook_viewer_content",
                "decision": "blocked",
                "license_tier": "restricted_publisher_license",
            },
        ]
    }

    roadmap = engine.build_learning_roadmap(
        learning_unit=learning_unit,
        data_plan=data_plan,
    )

    assert roadmap["schema"] == "paideia-cultivation-roadmap/v1"
    assert roadmap["unit_id"] == "elementary-grade-3-math"
    assert roadmap["licensed_source_count"] == 1
    assert roadmap["blocked_source_count"] == 1
    assert roadmap["stages"][0]["stage"] == "foundation"
    assert roadmap["assessment_gates"][0]["gate_id"] == "unit_check"


def test_cultivation_roadmap_embeds_assessment_gates_from_item_bank():
    engine = CultivationEngine()
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
    bank = ItemBank(
        [
            AssessmentItem(
                item_id="math-3-001",
                standard_id="E-MATH-03-01",
                gate_id="unit_check",
                item_type="short_answer",
                prompt="What is 245 + 130?",
                answer="375",
                distractors=[],
                explanation="245 + 130 = 375.",
                rubric={"accuracy": 80, "explanation": 20},
            )
        ]
    )

    roadmap = engine.build_learning_roadmap(
        learning_unit=learning_unit,
        data_plan={"sources": []},
        item_bank=bank,
    )

    assert roadmap["assessment_gates"][0]["item_count"] == 1
    assert roadmap["assessment_gates"][0]["items"][0]["item_id"] == "math-3-001"
