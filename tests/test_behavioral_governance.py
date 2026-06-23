import pytest

from paideia_engines.kibo import evaluate_validation_profile_v2, validation_profile_reuse_ceiling_v2
from paideia_engines.kibo.contracts_v2 import PatternValidationProfile


def _profile(
    *,
    structural=True,
    behavioral=False,
    near=False,
    far=False,
    adversarial=False,
    shadow=False,
    field=False,
    critic=False,
    high_risk=False,
):
    return PatternValidationProfile(
        profile_id="validation-1",
        pattern_id="pattern-1",
        pattern_version="1.0.0",
        structural_exam_passed=structural,
        behavioral_exam_passed=behavioral,
        near_transfer_passed=near,
        far_transfer_passed=far,
        adversarial_exam_passed=adversarial,
        shadow_validation_passed=shadow,
        field_validation_passed=field,
        critic_clearance_passed=critic,
        evidence_fresh_until=None,
        high_risk_eligible=high_risk,
        evidence_refs=("exam-1",),
    ).to_dict()


def test_structural_profile_is_reference_only_without_behavioral_credit():
    report = evaluate_validation_profile_v2(_profile())

    assert report["status"] == "passed"
    assert report["reuse_ceiling"] == "reference_only"
    assert report["behavioral_credit"] is False


def test_behavioral_near_transfer_profile_allows_partial_reuse():
    report = evaluate_validation_profile_v2(_profile(behavioral=True, near=True))

    assert report["status"] == "passed"
    assert report["reuse_ceiling"] == "partial_reuse"
    assert report["behavioral_credit"] is True


def test_strong_profile_requires_field_far_adversarial_and_critic_evidence():
    payload = _profile(
        behavioral=True,
        near=True,
        far=True,
        adversarial=True,
        shadow=True,
        field=True,
        critic=True,
        high_risk=True,
    )
    profile = PatternValidationProfile.from_dict(payload)
    report = evaluate_validation_profile_v2(payload, risk_level="high")

    assert validation_profile_reuse_ceiling_v2(profile) == "strong_reuse"
    assert report["status"] == "passed"
    assert report["reuse_ceiling"] == "strong_reuse"
    assert report["high_risk_allowed"] is True


def test_strong_reuse_helper_requires_near_transfer_evidence():
    payload = _profile(
        behavioral=True,
        near=False,
        far=True,
        adversarial=True,
        shadow=True,
        field=True,
        critic=True,
        high_risk=True,
    )
    profile = PatternValidationProfile.from_dict(payload)

    assert validation_profile_reuse_ceiling_v2(profile) == "reference_only"


def test_high_risk_request_blocks_profiles_without_high_risk_eligibility():
    report = evaluate_validation_profile_v2(
        _profile(behavioral=True, near=True, far=True, adversarial=True, field=True, critic=True),
        risk_level="critical",
    )

    assert report["status"] == "blocked"
    assert report["reuse_ceiling"] == "partial_reuse"
    assert any(issue["code"] == "high_risk_eligibility" for issue in report["issues"])


def test_high_risk_eligibility_claim_requires_full_strong_evidence():
    report = evaluate_validation_profile_v2(_profile(high_risk=True), risk_level="critical")

    assert report["status"] == "blocked"
    assert report["reuse_ceiling"] == "reference_only"
    assert report["high_risk_allowed"] is False
    assert any(issue["code"] == "high_risk_evidence_required" for issue in report["issues"])


def test_field_validation_without_behavioral_validation_is_blocked():
    report = evaluate_validation_profile_v2(_profile(field=True, critic=True))

    assert report["status"] == "blocked"
    assert report["reuse_ceiling"] == "reference_only"
    assert any(issue["code"] == "field_without_behavioral" for issue in report["issues"])


def test_field_validation_without_shadow_validation_is_blocked():
    report = evaluate_validation_profile_v2(
        _profile(behavioral=True, near=True, far=True, adversarial=True, field=True, critic=True, high_risk=True),
        risk_level="critical",
    )

    assert report["status"] == "blocked"
    assert report["reuse_ceiling"] == "partial_reuse"
    assert report["high_risk_allowed"] is False
    assert any(issue["code"] == "field_without_shadow" for issue in report["issues"])


def test_behavioral_exam_passed_without_near_transfer_is_blocked():
    report = evaluate_validation_profile_v2(_profile(behavioral=True))

    assert report["status"] == "blocked"
    assert any(issue["code"] == "near_transfer" for issue in report["issues"])


def test_malformed_validation_profile_fails_closed():
    payload = _profile()
    payload["contract_hash"] = "0" * 64

    with pytest.raises(ValueError, match="Contract hash mismatch"):
        evaluate_validation_profile_v2(payload)
