from paideia_engines.assessment import AssessmentEngine


def test_assessment_engine_scores_submission_with_rubric_feedback():
    engine = AssessmentEngine()

    result = engine.evaluate(
        gate_id="evidence_gate",
        submission={
            "answer": "The claim cites evidence, checks uncertainty, and proposes verification.",
            "artifacts": ["trace.json"],
        },
    )

    assert result["schema"] == "paideia-assessment-result/v1"
    assert result["gate_id"] == "evidence_gate"
    assert result["passed"] is True
    assert result["score"] >= 80
    assert "evidence" in result["feedback"].lower()


def test_assessment_transcript_does_not_make_promotion_decisions():
    engine = AssessmentEngine()

    transcript = engine.build_transcript(
        learner_id="agent:analyst",
        results=[
            {"gate_id": "evidence_gate", "passed": True, "score": 88},
            {"gate_id": "safety_gate", "passed": True, "score": 84},
        ],
    )

    assert transcript["schema"] == "paideia-assessment-transcript/v1"
    assert transcript["graduation_ready"] is True
    assert "promotion_decision" not in transcript
