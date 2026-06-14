from paideia_engines.assessment import AssessmentEngine
from paideia_engines.assessment.item_bank import AssessmentItem, ItemBank


def test_item_bank_groups_items_by_standard_and_gate():
    bank = ItemBank(
        [
            AssessmentItem(
                item_id="math-3-001",
                standard_id="E-MATH-03-01",
                gate_id="unit_check",
                item_type="multiple_choice",
                prompt="What is 245 + 130?",
                answer="375",
                distractors=["365", "475", "315"],
                explanation="Add hundreds, tens, and ones by place value.",
                rubric={"accuracy": 70, "explanation": 30},
            ),
            AssessmentItem(
                item_id="math-3-002",
                standard_id="E-MATH-03-01",
                gate_id="solution_process",
                item_type="solution_process",
                prompt="Show how to add 245 and 130.",
                answer="375",
                distractors=[],
                explanation="The work should show place-value grouping.",
                rubric={"accuracy": 50, "process": 40, "clarity": 10},
            ),
        ]
    )

    gate = bank.build_gate("unit_check", standard_ids=["E-MATH-03-01"])

    assert gate["schema"] == "paideia-assessment-gate/v1"
    assert gate["gate_id"] == "unit_check"
    assert gate["item_count"] == 1
    assert gate["items"][0]["item_id"] == "math-3-001"


def test_assessment_engine_evaluates_item_bank_submission_with_rubric():
    bank = ItemBank(
        [
            AssessmentItem(
                item_id="math-3-001",
                standard_id="E-MATH-03-01",
                gate_id="unit_check",
                item_type="short_answer",
                prompt="What is 245 + 130?",
                answer="375",
                distractors=["365"],
                explanation="245 + 130 = 375.",
                rubric={"accuracy": 80, "explanation": 20},
            )
        ]
    )
    engine = AssessmentEngine(item_bank=bank)

    result = engine.evaluate_item_response(
        "math-3-001",
        response={"answer": "375", "explanation": "I added 245 and 130 by place value."},
    )

    assert result["schema"] == "paideia-assessment-item-result/v1"
    assert result["passed"] is True
    assert result["score"] >= 90
    assert result["review_label"]["status"] == "verified"
    assert result["review_label"]["score"] == result["score"]


def test_assessment_engine_scores_solution_process_partially():
    bank = ItemBank(
        [
            AssessmentItem(
                item_id="math-3-002",
                standard_id="E-MATH-03-01",
                gate_id="solution_process",
                item_type="solution_process",
                prompt="Show how to add 245 and 130.",
                answer="375",
                distractors=[],
                explanation="Expected process: hundreds, tens, ones.",
                rubric={"accuracy": 50, "process": 40, "clarity": 10},
            )
        ]
    )
    engine = AssessmentEngine(item_bank=bank)

    result = engine.evaluate_item_response(
        "math-3-002",
        response={"answer": "375", "work": "245 + 130 = 375"},
    )

    assert result["passed"] is True
    assert result["score_breakdown"]["accuracy"] == 50
    assert result["score_breakdown"]["process"] > 0
    assert result["score_breakdown"]["clarity"] >= 0
