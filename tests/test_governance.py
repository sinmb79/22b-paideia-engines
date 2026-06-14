from paideia_engines.governance import GovernanceEngine


def test_governance_engine_declares_committees_and_boss_review_gate():
    engine = GovernanceEngine()

    board = engine.create_board(program_id="paideia:demo")

    assert board["schema"] == "paideia-governance-board/v1"
    assert "education_committee" in board["committees"]
    assert "oversight_committee" in board["committees"]
    assert "memory_promotion" in board["boss_review_required_for"]


def test_governance_review_blocks_external_upload_by_default():
    engine = GovernanceEngine()

    review = engine.review_action(
        action="upload_training_data",
        context={"contains_private_assets": True},
    )

    assert review["schema"] == "paideia-governance-review/v1"
    assert review["decision"] == "blocked"
    assert review["requires_boss_review"] is True
