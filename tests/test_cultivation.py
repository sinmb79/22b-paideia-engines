from paideia_engines.cultivation import CultivationEngine


def test_cultivation_engine_builds_reusable_training_blueprint():
    engine = CultivationEngine()

    blueprint = engine.create_blueprint(
        learner_id="agent:analyst",
        role="research analyst",
        objectives=["evidence-first answers", "safe memory use"],
    )

    assert blueprint["schema"] == "paideia-cultivation-blueprint/v1"
    assert blueprint["learner_id"] == "agent:analyst"
    assert blueprint["role"] == "research analyst"
    assert blueprint["curriculum"][0]["stage"] == "foundation"
    assert "assessment" in blueprint["handoffs"]
    assert "promotion" in blueprint["handoffs"]
