from paideia_engines.governance import GovernanceEngine


def test_governance_policy_evaluator_blocks_restricted_source_without_approval():
    engine = GovernanceEngine()

    evaluation = engine.evaluate_policy(
        action="use_dataset",
        context={
            "source_id": "textbook:math-grade-3",
            "license_tier": "manual_license_required",
            "intended_use": "local_training",
        },
    )

    assert evaluation["schema"] == "paideia-policy-evaluation/v1"
    assert evaluation["decision"] == "blocked"
    assert "manual_license_required" in evaluation["matched_rules"]
    assert "license_approval" in evaluation["required_approvals"]
    assert evaluation["approval_records"] == []


def test_governance_license_approval_allows_local_restricted_source_use():
    engine = GovernanceEngine()
    approval = engine.record_approval(
        approval_type="license_approval",
        subject_id="textbook:math-grade-3",
        approved_by="boss",
        scope={"source_id": "textbook:math-grade-3", "allowed_use": "local_training"},
        notes="Local-only use after license review.",
    )

    evaluation = engine.evaluate_policy(
        action="use_dataset",
        context={
            "source_id": "textbook:math-grade-3",
            "license_tier": "manual_license_required",
            "intended_use": "local_training",
        },
    )

    assert approval["schema"] == "paideia-governance-approval/v1"
    assert evaluation["decision"] == "allowed_with_approval"
    assert evaluation["approval_records"][0]["approval_id"] == approval["approval_id"]
    assert engine.approval_ledger["version"] == 1


def test_governance_external_upload_remains_blocked_even_with_boss_approval():
    engine = GovernanceEngine()
    engine.record_approval(
        approval_type="boss_approval",
        subject_id="external_upload",
        approved_by="boss",
        scope={"action": "external_upload"},
        notes="Approval record should not override the hard upload ban.",
    )

    evaluation = engine.evaluate_policy(
        action="external_upload",
        context={"contains_private_assets": True, "target": "remote_service"},
    )

    assert evaluation["decision"] == "blocked"
    assert "external_upload_ban" in evaluation["matched_rules"]
    assert evaluation["override_allowed"] is False


def test_governance_risky_permission_requires_boss_approval():
    engine = GovernanceEngine()

    blocked = engine.evaluate_policy(action="credential_use", context={"tool": "api_client"})
    approval = engine.record_approval(
        approval_type="boss_approval",
        subject_id="credential_use",
        approved_by="boss",
        scope={"action": "credential_use"},
        notes="Allow local test credential use for this run.",
    )
    allowed = engine.evaluate_policy(action="credential_use", context={"tool": "api_client"})

    assert blocked["decision"] == "blocked"
    assert "risky_permission" in blocked["matched_rules"]
    assert "boss_approval" in blocked["missing_approvals"]
    assert allowed["decision"] == "allowed_with_approval"
    assert allowed["approval_records"][0]["approval_id"] == approval["approval_id"]


def test_governance_records_committee_decision_trail():
    engine = GovernanceEngine()

    decision = engine.record_committee_decision(
        committee="oversight_committee",
        subject_id="memory:promotion:exp-1",
        decision="approved_for_local_memory",
        reviewers=["boss", "education_lead"],
        rationale="Verified high-quality experience and local-only memory scope.",
    )

    assert decision["schema"] == "paideia-committee-decision/v1"
    assert decision["decision_id"].startswith("governance-decision-")
    assert decision["ledger_version"] == 1
    assert engine.decision_ledger["decisions"][0]["rationale"].startswith("Verified")
