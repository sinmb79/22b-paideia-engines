from paideia_engines.assessment import AssessmentEngine


def test_assessment_engine_scores_submission_with_rubric_feedback():
    engine = AssessmentEngine()

    result = engine.evaluate(
        gate_id="evidence_gate",
        submission={
            "answer": "The claim cites evidence, checks uncertainty, and proposes verification.",
            "artifacts": [
                {
                    "path": "trace.json",
                    "verified": True,
                    "content_hash": "sha256:" + "b" * 64,
                    "evidence_ref": "runtime:trace",
                }
            ],
        },
    )

    assert result["schema"] == "paideia-assessment-result/v1"
    assert result["gate_id"] == "evidence_gate"
    assert result["passed"] is True
    assert result["score"] >= 80
    assert result["verified_artifact_count"] == 1
    assert "evidence" in result["feedback"].lower()


def test_keyword_stuffing_does_not_pass_assessment_without_artifacts():
    engine = AssessmentEngine()

    result = engine.evaluate(
        gate_id="evidence_gate",
        submission={
            "answer": "evidence uncertainty verify source trace check " * 5,
            "artifacts": [],
        },
    )

    assert result["passed"] is False
    assert result["score"] < 80


def test_keyword_stuffing_with_dummy_artifact_does_not_pass_assessment():
    engine = AssessmentEngine()

    result = engine.evaluate(
        gate_id="evidence_gate",
        submission={
            "answer": "evidence uncertainty verify source trace check " * 5,
            "artifacts": [{"path": "dummy.json"}],
        },
    )

    assert result["passed"] is False
    assert result["score"] < 80
    assert result["artifact_count"] == 1
    assert result["verified_artifact_count"] == 0


def test_keyword_stuffing_with_synthetic_hash_artifact_does_not_pass_assessment():
    engine = AssessmentEngine()

    result = engine.evaluate(
        gate_id="evidence_gate",
        submission={
            "answer": "evidence uncertainty verify source trace check " * 5,
            "artifacts": [
                {
                    "path": "dummy.json",
                    "verified": True,
                    "content_hash": "sha256:" + "0" * 64,
                    "evidence_ref": "runtime:trace",
                }
            ],
        },
    )

    assert result["passed"] is False
    assert result["verified_artifact_count"] == 0


def test_verified_artifact_can_support_assessment_pass():
    engine = AssessmentEngine()

    result = engine.evaluate(
        gate_id="evidence_gate",
        submission={
            "answer": "The claim cites evidence, checks uncertainty, and proposes verification.",
            "artifacts": [
                {
                    "path": "trace.json",
                    "verified": True,
                    "content_hash": "sha256:" + "a" * 64,
                    "evidence_ref": "runtime:trace",
                }
            ],
        },
    )

    assert result["passed"] is True
    assert result["artifact_count"] == 1
    assert result["verified_artifact_count"] == 1


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
