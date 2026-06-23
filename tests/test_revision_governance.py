from paideia_engines.kibo import evaluate_pattern_revision_v2
from paideia_engines.kibo.contracts_v2 import BehavioralExamResult, PatternRevisionProposal, ScenarioResult


def _revision(*, status="quarantined", from_version="1.0.0", proposed_version="1.0.1", changes=True):
    return PatternRevisionProposal(
        revision_id="revision-1",
        pattern_id="pattern-1",
        from_pattern_version=from_version,
        proposed_pattern_version=proposed_version,
        revision_reasons=("negative_step_credit",),
        proposed_changes=(
            {"op": "quarantine_and_revise_action_node", "node_id": "inspect", "reason_codes": ["receipt_failed"]},
        )
        if changes
        else (),
        evidence_refs=("attr-1",),
        requires_behavioral_exam=True,
        requires_shadow_validation=True,
        status=status,
    ).to_dict()


def _behavioral_exam(*, pattern_version="1.0.1", passed=True, leakage=False):
    return BehavioralExamResult(
        exam_id="exam-1",
        pattern_id="pattern-1",
        pattern_version=pattern_version,
        scenario_pack_id="pack-1",
        scenario_results=(ScenarioResult("near-1", "near_transfer", True, True, False, (), "hash-trace"),),
        task_success_rate=1.0,
        invariant_pass_rate=1.0,
        transfer_score=1.0,
        abstention_precision=1.0,
        efficiency_score=1.0,
        safety_violation_count=0,
        leakage_detected=leakage,
        passed=passed,
        evidence_hashes=("hash-exam",),
    ).to_dict()


def _shadow(*, passed=True):
    return {
        "schema": "paideia-pattern-shadow-validation/v1",
        "revision_id": "revision-1",
        "pattern_id": "pattern-1",
        "pattern_version": "1.0.1",
        "passed": passed,
        "regression_detected": not passed,
    }


def test_quarantined_revision_can_enter_testing_but_not_promotion():
    report = evaluate_pattern_revision_v2(_revision())

    assert report["status"] == "passed"
    assert report["testing_allowed"] is True
    assert report["promotion_allowed"] is False


def test_accepted_revision_requires_behavioral_exam_and_shadow_validation():
    report = evaluate_pattern_revision_v2(_revision(status="accepted"))

    assert report["status"] == "blocked"
    assert report["promotion_allowed"] is False
    assert any(issue["code"] == "behavioral_exam_required" for issue in report["issues"])
    assert any(issue["code"] == "shadow_validation_required" for issue in report["issues"])


def test_accepted_revision_blocks_behavioral_version_mismatch():
    report = evaluate_pattern_revision_v2(
        _revision(status="accepted"),
        behavioral_exam=_behavioral_exam(pattern_version="1.0.0"),
        shadow_report=_shadow(),
    )

    assert report["status"] == "blocked"
    assert any(issue["code"] == "behavioral_version_mismatch" for issue in report["issues"])


def test_accepted_revision_allows_promotion_after_behavioral_and_shadow_pass():
    report = evaluate_pattern_revision_v2(
        _revision(status="accepted"),
        behavioral_exam=_behavioral_exam(),
        shadow_report=_shadow(),
    )

    assert report["status"] == "passed"
    assert report["promotion_allowed"] is True
    assert report["behavioral_exam_passed"] is True
    assert report["shadow_validation_passed"] is True


def test_accepted_revision_cannot_opt_out_of_required_validation_flags():
    revision = _revision(status="accepted")
    revision["requires_behavioral_exam"] = False
    revision["requires_shadow_validation"] = False
    report = evaluate_pattern_revision_v2(revision)

    assert report["status"] == "blocked"
    assert report["promotion_allowed"] is False
    assert any(issue["code"] == "behavioral_exam_required" for issue in report["issues"])
    assert any(issue["code"] == "shadow_validation_required" for issue in report["issues"])


def test_unrelated_shadow_report_cannot_satisfy_revision_gate():
    report = evaluate_pattern_revision_v2(
        _revision(status="accepted"),
        behavioral_exam=_behavioral_exam(),
        shadow_report={**_shadow(), "pattern_version": "9.9.9"},
    )

    assert report["status"] == "blocked"
    assert any(issue["code"] == "shadow_version_mismatch" for issue in report["issues"])


def test_revision_same_version_is_blocked():
    report = evaluate_pattern_revision_v2(_revision(from_version="1.0.0", proposed_version="1.0.0"))

    assert report["status"] == "blocked"
    assert any(issue["code"] == "version_lineage" for issue in report["issues"])


def test_revision_version_downgrade_is_blocked():
    report = evaluate_pattern_revision_v2(_revision(from_version="1.0.0", proposed_version="0.9.0"))

    assert report["status"] == "blocked"
    assert report["testing_allowed"] is False
    assert any(issue["code"] == "version_downgrade" for issue in report["issues"])


def test_non_draft_revision_requires_proposed_changes():
    report = evaluate_pattern_revision_v2(_revision(changes=False))

    assert report["status"] == "blocked"
    assert report["testing_allowed"] is False
    assert any(issue["code"] == "empty_revision" for issue in report["issues"])


def test_non_draft_revision_rejects_empty_change_objects():
    revision = _revision(changes=True)
    revision["proposed_changes"] = [{}]
    report = evaluate_pattern_revision_v2(revision)

    assert report["status"] == "blocked"
    assert report["testing_allowed"] is False
    assert any(issue["code"] == "invalid_change" for issue in report["issues"])
