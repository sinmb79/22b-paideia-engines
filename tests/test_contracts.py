from paideia_engines.contracts import (
    EngineEvent,
    PromotionDecision,
    QuarantineDecision,
    ReviewLabel,
    default_local_policy,
)


def test_engine_event_serializes_with_traceable_contract_fields():
    event = EngineEvent(
        engine="promotion",
        event_type="decision.created",
        subject_id="employment:alpha",
        decision={"status": "promoted"},
    )

    payload = event.to_dict()

    assert payload["schema"] == "paideia-engine-event/v1"
    assert payload["engine"] == "promotion"
    assert payload["event_type"] == "decision.created"
    assert payload["subject_id"] == "employment:alpha"
    assert payload["decision"]["status"] == "promoted"
    assert payload["created_at"].endswith("Z")


def test_review_label_controls_promotion_and_quarantine_decisions():
    verified = ReviewLabel(score=91, status="verified", reviewed_by="boss")
    weak = ReviewLabel(score=61, status="needs_review", reviewed_by="committee")

    promoted = PromotionDecision.from_review("exp-1", verified)
    quarantined = QuarantineDecision.from_review("exp-2", weak)

    assert promoted.status == "promoted"
    assert promoted.requires_boss_review is False
    assert quarantined.status == "quarantined"
    assert quarantined.requires_boss_review is True
    assert "do_not_promote" in quarantined.reason


def test_default_policy_is_local_first_and_blocks_external_uploads():
    policy = default_local_policy()

    assert policy["data_boundary"] == "local-first"
    assert policy["external_uploads"] == "blocked_by_default"
    assert "boss_private_assets" in policy["protected_assets"]
