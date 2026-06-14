import pytest

from paideia_engines.contracts import ReviewLabel
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

    reconsidered = engine.reconsider_quarantined(
        quarantined["experience_id"],
        review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
        notes="Fresh governance decision allows local-only promotion.",
        governance_decision="allowed",
    )

    assert reconsidered["status"] == "promoted"
    assert reconsidered["governance_decision"] == "allowed"


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
