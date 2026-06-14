import pytest

from paideia_engines.contracts import ReviewLabel
from paideia_engines.governance import GovernanceEngine
from paideia_engines.promotion import PromotionEngine


def test_promotion_engine_versions_ledger_after_each_decision():
    engine = PromotionEngine(owner="agent:math")

    first = engine.record_experience(
        source="assessment",
        event={"summary": "Passed place-value item.", "skills": ["place_value"]},
        review=ReviewLabel(score=91, status="verified", reviewed_by="boss"),
    )
    second = engine.record_experience(
        source="stress",
        event={"summary": "Copied trap answer.", "skills": ["trap_detection"]},
        review=ReviewLabel(score=45, status="needs_review", reviewed_by="committee"),
    )

    assert first["ledger_version"] == 1
    assert second["ledger_version"] == 2
    assert engine.ledger["version"] == 2
    assert [entry["version"] for entry in engine.ledger["history"]] == [1, 2]


def test_promotion_ledger_accessor_returns_snapshot_not_internal_store():
    engine = PromotionEngine(owner="agent:math")
    engine.record_experience(
        source="assessment",
        event={"summary": "Passed place-value item.", "skills": ["place_value"]},
        review=ReviewLabel(score=91, status="verified", reviewed_by="boss"),
    )

    ledger = engine.ledger
    ledger["promoted_experiences"][0]["review_status"] = "tampered"

    assert engine.ledger["promoted_experiences"][0]["review_status"] == "active"


def test_promotion_events_accessor_returns_snapshot_not_internal_store():
    engine = PromotionEngine(owner="agent:math")
    engine.record_experience(
        source="assessment",
        event={"summary": "Passed place-value item.", "skills": ["place_value"]},
        review=ReviewLabel(score=91, status="verified", reviewed_by="boss"),
    )

    events = engine.events
    events[0]["event_type"] = "tampered"

    assert engine.events[0]["event_type"] == "experience.recorded"


@pytest.mark.parametrize("attribute", ["ledger", "events", "owner", "minimum_score"])
def test_promotion_trust_boundary_accessors_are_read_only(attribute):
    engine = PromotionEngine(owner="agent:math")

    with pytest.raises(AttributeError):
        setattr(engine, attribute, {})


def test_promotion_owner_and_minimum_score_are_fixed_trust_config():
    engine = PromotionEngine(owner="agent:math", minimum_score=90)
    decision = engine.record_experience(
        source="assessment",
        event={"summary": "Strong but below stricter threshold.", "skills": ["place_value"]},
        review=ReviewLabel(score=85, status="verified", reviewed_by="boss"),
    )

    assert engine.owner == "agent:math"
    assert engine.minimum_score == 90
    assert engine.ledger["owner"] == "agent:math"
    assert decision["status"] == "quarantined"
    assert decision["owner"] == "agent:math"


def test_minimum_score_gate_applies_to_quarantine_reconsideration():
    engine = PromotionEngine(owner="agent:math", minimum_score=90)
    quarantined = engine.record_experience(
        source="stress",
        event={"summary": "Initially weak stress response.", "skills": ["stress_rehearsal"]},
        review=ReviewLabel(score=62, status="needs_review", reviewed_by="committee"),
    )

    reconsidered = engine.reconsider_quarantined(
        quarantined["experience_id"],
        review=ReviewLabel(score=88, status="verified", reviewed_by="boss"),
        notes="Still below the fixed stricter gate.",
    )

    assert reconsidered["status"] == "quarantined"
    assert reconsidered["reason"] == "reconsideration_failed_verified_quality_gate"
    assert engine.minimum_score == 90


def test_minimum_score_gate_applies_to_promoted_supersession():
    engine = PromotionEngine(owner="agent:math", minimum_score=90)
    promoted = engine.record_experience(
        source="assessment",
        event={"summary": "Old method for place value.", "skills": ["place_value"]},
        review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
    )

    with pytest.raises(ValueError, match="verified high-quality review"):
        engine.supersede_promoted(
            promoted["experience_id"],
            event={"summary": "Replacement is below the fixed stricter gate.", "skills": ["place_value"]},
            review=ReviewLabel(score=88, status="verified", reviewed_by="boss"),
            reason="below stricter fixed gate",
        )

    assert engine.minimum_score == 90
    assert len(engine.ledger["promoted_experiences"]) == 1


def test_record_experience_returns_snapshot_not_ledger_alias():
    engine = PromotionEngine(owner="agent:math")

    decision = engine.record_experience(
        source="assessment",
        event={"summary": "Passed place-value item.", "skills": ["place_value"]},
        review=ReviewLabel(score=91, status="verified", reviewed_by="boss"),
    )
    decision["review"]["score"] = 1

    assert engine.ledger["promoted_experiences"][0]["decision"]["review"]["score"] == 91


def test_reconsider_quarantined_returns_snapshot_not_ledger_alias():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="stress",
        event={"summary": "Initially weak stress response.", "skills": ["stress_rehearsal"]},
        review=ReviewLabel(score=62, status="needs_review", reviewed_by="committee"),
    )

    reconsidered = engine.reconsider_quarantined(
        quarantined["experience_id"],
        review=ReviewLabel(score=88, status="verified", reviewed_by="boss"),
        notes="Learner corrected the misconception with evidence.",
    )
    reconsidered["review"]["score"] = 1

    assert engine.ledger["promoted_experiences"][0]["decision"]["review"]["score"] == 88


def test_governance_reconsideration_returns_snapshot_not_ledger_alias():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )
    governance = GovernanceEngine()
    quarantine_ref = quarantined["quarantine_ref"]
    governance.record_approval(
        approval_type="boss_approval",
        subject_id=quarantined["experience_id"],
        approved_by="boss",
        scope={
            "action": "memory_promotion",
            "source_id": quarantined["experience_id"],
            "allowed_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    allowed_review = governance.review_action(
        "memory_promotion",
        context={
            "source_id": quarantined["experience_id"],
            "intended_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )

    reconsidered = engine.reconsider_quarantined(
        quarantined["experience_id"],
        review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
        notes="Fresh governance decision allows local-only promotion.",
        governance_review=allowed_review,
        governance_approval_ledger=governance.approval_ledger,
    )
    reconsidered["governance_review"]["policy_evaluation"]["context"]["source_id"] = "tampered"

    assert (
        engine.ledger["promoted_experiences"][0]["decision"]["governance_review"]["policy_evaluation"]["context"][
            "source_id"
        ]
        == quarantined["experience_id"]
    )


def test_supersede_promoted_returns_snapshot_not_ledger_alias():
    engine = PromotionEngine(owner="agent:math")
    promoted = engine.record_experience(
        source="assessment",
        event={"summary": "Old method for place value.", "skills": ["place_value"]},
        review=ReviewLabel(score=90, status="verified", reviewed_by="boss"),
    )

    replacement = engine.supersede_promoted(
        promoted["experience_id"],
        event={"summary": "Improved method with clearer verification.", "skills": ["place_value", "verification"]},
        review=ReviewLabel(score=95, status="verified", reviewed_by="boss"),
        reason="clearer verified method",
    )
    replacement["review"]["score"] = 1

    assert engine.ledger["promoted_experiences"][1]["decision"]["review"]["score"] == 95


def test_route_active_memory_returns_snapshot_not_ledger_alias():
    engine = PromotionEngine(owner="agent:math")
    engine.record_experience(
        source="assessment",
        event={"summary": "Passed place-value item.", "skills": ["place_value"]},
        review=ReviewLabel(score=91, status="verified", reviewed_by="boss"),
    )

    route = engine.route_active_memory("place value")
    route["selected"][0]["event"]["summary"] = "tampered"

    assert engine.ledger["promoted_experiences"][0]["event"]["summary"] == "Passed place-value item."


def test_promotion_engine_preserves_custom_quarantine_reason():
    engine = PromotionEngine(owner="agent:math")

    decision = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by local-first governance.", "skills": ["governance"]},
        review=ReviewLabel(score=91, status="needs_review", reviewed_by="governance"),
        quarantine_reason="governance_blocked_promotion",
    )

    assert decision["status"] == "quarantined"
    assert decision["reason"] == "governance_blocked_promotion"
    assert decision["requires_boss_review"] is True
    assert engine.ledger["quarantined_experiences"][0]["decision"]["reason"] == "governance_blocked_promotion"


def test_quarantine_reason_forces_quarantine_even_with_verified_review():
    engine = PromotionEngine(owner="agent:math")

    decision = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )

    assert decision["status"] == "quarantined"
    assert decision["reason"] == "governance_blocked_promotion"
    assert decision["requires_boss_review"] is True
    assert decision["quarantine_ref"].startswith("quarantine-ref-")
    assert engine.ledger["promoted_experiences"] == []


def test_governance_blocked_quarantine_requires_allowed_governance_for_reconsideration():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )

    with pytest.raises(ValueError, match="fresh allowed governance decision"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="Quality issue resolved, but governance is still blocked.",
        )

    with pytest.raises(ValueError, match="governance review payload"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="A forged string is not a governance review.",
            governance_decision="allowed",
    )

    governance = GovernanceEngine()
    quarantine_ref = quarantined["quarantine_ref"]
    governance.record_approval(
        approval_type="boss_approval",
        subject_id=quarantined["experience_id"],
        approved_by="boss",
        scope={
            "action": "memory_promotion",
            "source_id": quarantined["experience_id"],
            "allowed_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    allowed_review = governance.review_action(
        "memory_promotion",
        context={
            "source_id": quarantined["experience_id"],
            "intended_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    reconsidered = engine.reconsider_quarantined(
        quarantined["experience_id"],
        review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
        notes="Fresh governance decision allows local-only promotion.",
        governance_review=allowed_review,
        governance_approval_ledger=governance.approval_ledger,
    )

    assert reconsidered["status"] == "promoted"
    assert reconsidered["governance_review"]["decision"] == "allowed"
    assert reconsidered["governance_review"]["policy_evaluation"]["missing_approvals"] == []


def test_governance_blocked_quarantine_rejects_wrong_governance_review_scope():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )
    governance = GovernanceEngine()
    quarantine_ref = quarantined["quarantine_ref"]
    governance.record_approval(
        approval_type="boss_approval",
        subject_id="other-experience",
        approved_by="boss",
        scope={
            "action": "memory_promotion",
            "source_id": "other-experience",
            "allowed_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    wrong_scope_review = governance.review_action(
        "memory_promotion",
        context={
            "source_id": "other-experience",
            "intended_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )

    with pytest.raises(ValueError, match="fresh allowed governance decision"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="Review belongs to a different quarantined record.",
            governance_review=wrong_scope_review,
            governance_approval_ledger=governance.approval_ledger,
        )


def test_governance_blocked_quarantine_rejects_governance_review_with_wrong_approval_subject():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )
    governance = GovernanceEngine()
    quarantine_ref = quarantined["quarantine_ref"]
    governance.record_approval(
        approval_type="boss_approval",
        subject_id="other-experience",
        approved_by="boss",
        scope={
            "action": "memory_promotion",
            "source_id": quarantined["experience_id"],
            "allowed_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    wrong_subject_review = governance.review_action(
        "memory_promotion",
        context={
            "source_id": quarantined["experience_id"],
            "intended_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )

    with pytest.raises(ValueError, match="fresh allowed governance decision"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="Review has an approval for a different subject.",
            governance_review=wrong_subject_review,
            governance_approval_ledger=governance.approval_ledger,
        )


def test_governance_blocked_quarantine_rejects_governance_review_with_wrong_approval_scope():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )
    governance = GovernanceEngine()
    quarantine_ref = quarantined["quarantine_ref"]
    governance.record_approval(
        approval_type="boss_approval",
        subject_id=quarantined["experience_id"],
        approved_by="boss",
        scope={
            "action": "memory_promotion",
            "source_id": quarantined["experience_id"],
            "allowed_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    wrong_scope_review = governance.review_action(
        "memory_promotion",
        context={
            "source_id": quarantined["experience_id"],
            "intended_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    wrong_scope_review["policy_evaluation"]["approval_records"][0]["scope"] = {
        "action": "private_asset_access",
        "source_id": quarantined["experience_id"],
        "allowed_use": "active_memory",
        "quarantine_ref": quarantine_ref,
    }

    with pytest.raises(ValueError, match="fresh allowed governance decision"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="Approval scope does not authorize memory promotion.",
            governance_review=wrong_scope_review,
            governance_approval_ledger=governance.approval_ledger,
        )


def test_governance_blocked_quarantine_rejects_governance_review_missing_quarantine_ref():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )
    governance = GovernanceEngine()
    governance.record_approval(
        approval_type="boss_approval",
        subject_id=quarantined["experience_id"],
        approved_by="boss",
        scope={
            "action": "memory_promotion",
            "source_id": quarantined["experience_id"],
            "allowed_use": "active_memory",
        },
    )
    missing_ref_review = governance.review_action(
        "memory_promotion",
        context={"source_id": quarantined["experience_id"], "intended_use": "active_memory"},
    )
    missing_ref_review["timestamp"] = "9999-01-01T00:00:00Z"

    with pytest.raises(ValueError, match="fresh allowed governance decision"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="Review omits the quarantine ref.",
            governance_review=missing_ref_review,
            governance_approval_ledger=governance.approval_ledger,
        )


def test_governance_blocked_quarantine_rejects_forged_governance_review_without_ledger():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )
    forged_review = {
        "schema": "paideia-governance-review/v1",
        "action": "memory_promotion",
        "decision": "allowed",
        "timestamp": "9999-01-01T00:00:00Z",
        "policy_evaluation": {
            "decision": "allowed_with_approval",
            "missing_approvals": [],
            "override_allowed": True,
            "context": {
                "action": "memory_promotion",
                "source_id": quarantined["experience_id"],
                "intended_use": "active_memory",
                "quarantine_ref": quarantined["quarantine_ref"],
            },
            "approval_records": [
                {
                    "schema": "paideia-governance-approval/v1",
                    "approval_type": "boss_approval",
                    "subject_id": quarantined["experience_id"],
                    "approved_by": "boss",
                    "scope": {
                        "action": "memory_promotion",
                        "source_id": quarantined["experience_id"],
                        "allowed_use": "active_memory",
                        "quarantine_ref": quarantined["quarantine_ref"],
                    },
                    "status": "active",
                }
            ],
        },
    }

    with pytest.raises(ValueError, match="fresh allowed governance decision"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="Forged approval record is not present in a governance ledger.",
            governance_review=forged_review,
        )


def test_governance_blocked_quarantine_rejects_governance_review_older_than_quarantine():
    engine = PromotionEngine(owner="agent:math")
    quarantined = engine.record_experience(
        source="governance",
        event={"summary": "Blocked by governance.", "skills": ["governance"], "blocked_by": "governance"},
        review=ReviewLabel(score=100, status="verified", reviewed_by="committee"),
        quarantine_reason="governance_blocked_promotion",
    )
    governance = GovernanceEngine()
    quarantine_ref = quarantined["quarantine_ref"]
    governance.record_approval(
        approval_type="boss_approval",
        subject_id=quarantined["experience_id"],
        approved_by="boss",
        scope={
            "action": "memory_promotion",
            "source_id": quarantined["experience_id"],
            "allowed_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    stale_review = governance.review_action(
        "memory_promotion",
        context={
            "source_id": quarantined["experience_id"],
            "intended_use": "active_memory",
            "quarantine_ref": quarantine_ref,
        },
    )
    stale_review["timestamp"] = "1970-01-01T00:00:00Z"

    with pytest.raises(ValueError, match="fresh allowed governance decision"):
        engine.reconsider_quarantined(
            quarantined["experience_id"],
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
            notes="Review timestamp predates the quarantine.",
            governance_review=stale_review,
            governance_approval_ledger=governance.approval_ledger,
        )


def test_promotion_engine_reconsiders_quarantined_experience_after_review():
    engine = PromotionEngine(owner="agent:math")

    quarantined = engine.record_experience(
        source="stress",
        event={"summary": "Initially weak stress response.", "skills": ["stress_rehearsal"]},
        review=ReviewLabel(score=62, status="needs_review", reviewed_by="committee"),
    )
    reconsidered = engine.reconsider_quarantined(
        quarantined["experience_id"],
        review=ReviewLabel(score=88, status="verified", reviewed_by="boss"),
        notes="Learner corrected the misconception with evidence.",
    )

    assert reconsidered["status"] == "promoted"
    assert reconsidered["supersedes"] == quarantined["experience_id"]
    assert reconsidered["ledger_version"] == 2
    assert engine.ledger["quarantined_experiences"][0]["review_status"] == "superseded"
    assert engine.ledger["promoted_experiences"][0]["source"] == "quarantine_reconsideration"


def test_promotion_engine_can_supersede_promoted_experience_without_deleting_history():
    engine = PromotionEngine(owner="agent:math")
    promoted = engine.record_experience(
        source="assessment",
        event={"summary": "Old method for place value.", "skills": ["place_value"]},
        review=ReviewLabel(score=90, status="verified", reviewed_by="boss"),
    )

    replacement = engine.supersede_promoted(
        promoted["experience_id"],
        event={"summary": "Improved method with clearer verification.", "skills": ["place_value", "verification"]},
        review=ReviewLabel(score=95, status="verified", reviewed_by="boss"),
        reason="clearer verified method",
    )

    assert replacement["status"] == "promoted"
    assert replacement["supersedes"] == promoted["experience_id"]
    assert engine.ledger["promoted_experiences"][0]["review_status"] == "superseded"
    assert len(engine.ledger["promoted_experiences"]) == 2
    assert len(engine.ledger["history"]) == 2


def test_promotion_engine_routes_only_active_supersession_memory():
    engine = PromotionEngine(owner="agent:math")
    promoted = engine.record_experience(
        source="assessment",
        event={"summary": "Old method for place value.", "skills": ["place_value"]},
        review=ReviewLabel(score=90, status="verified", reviewed_by="boss"),
    )
    engine.supersede_promoted(
        promoted["experience_id"],
        event={"summary": "Improved method with verification.", "skills": ["place_value", "verification"]},
        review=ReviewLabel(score=95, status="verified", reviewed_by="boss"),
        reason="clearer verified method",
    )

    route = engine.route_active_memory("place value")

    assert route["matched"] == 1
    assert route["selected"][0]["event"]["summary"] == "Improved method with verification."
