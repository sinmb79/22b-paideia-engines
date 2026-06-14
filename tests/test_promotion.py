from paideia_engines.contracts import ReviewLabel
from paideia_engines.promotion import PromotionEngine


def test_promotion_engine_promotes_only_verified_high_quality_experience():
    engine = PromotionEngine(owner="agent:analyst")

    decision = engine.record_experience(
        source="runtime",
        event={"summary": "Solved task with evidence and verification.", "skills": ["evidence_review"]},
        review=ReviewLabel(score=92, status="verified", reviewed_by="boss"),
    )

    assert decision["status"] == "promoted"
    assert engine.ledger["promoted_experiences"][0]["source"] == "runtime"
    assert engine.ledger["quarantined_experiences"] == []


def test_promotion_engine_quarantines_unreviewed_or_low_quality_experience():
    engine = PromotionEngine(owner="agent:analyst")

    decision = engine.record_experience(
        source="stress",
        event={"summary": "Guessed without checking sources.", "skills": ["guessing"]},
        review=ReviewLabel(score=55, status="needs_review", reviewed_by="committee"),
    )

    assert decision["status"] == "quarantined"
    assert engine.ledger["promoted_experiences"] == []
    assert engine.ledger["quarantined_experiences"][0]["flags"] == ["needs_human_review", "do_not_promote"]


def test_promotion_engine_routes_active_memory_from_promoted_entries_only():
    engine = PromotionEngine(owner="agent:analyst")
    engine.record_experience(
        source="runtime",
        event={"summary": "Evidence-first financial analysis.", "skills": ["evidence_review"]},
        review=ReviewLabel(score=90, status="verified", reviewed_by="boss"),
    )
    engine.record_experience(
        source="runtime",
        event={"summary": "Unsafe external upload attempt.", "skills": ["upload"]},
        review=ReviewLabel(score=20, status="failed", reviewed_by="oversight"),
    )

    route = engine.route_active_memory("Need evidence review")

    assert route["schema"] == "paideia-active-memory-route/v1"
    assert len(route["selected"]) == 1
    assert route["selected"][0]["source"] == "runtime"
    assert route["quarantined_experiences"] == "excluded"
