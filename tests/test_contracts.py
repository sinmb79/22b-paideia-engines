from pathlib import Path

from paideia_engines.contracts import (
    EngineContract,
    EngineEvent,
    PromotionDecision,
    QuarantineDecision,
    ReviewLabel,
    default_local_policy,
    engine_contract_registry,
    engine_contracts,
    validate_engine_contract_registry,
)


ROOT = Path(__file__).resolve().parents[1]


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


def test_engine_contract_registry_lists_every_reusable_engine():
    registry = engine_contract_registry()
    contracts = engine_contracts()
    names = {contract.name for contract in contracts}

    assert registry["schema"] == "paideia-engine-contract-registry/v1"
    assert registry["phase"] == 13
    assert all(isinstance(contract, EngineContract) for contract in contracts)
    assert names == {
        "data_acquisition",
        "curriculum_mapping",
        "cultivation",
        "assessment",
        "stress",
        "promotion",
        "governance",
        "runtime",
        "orchestration",
        "evaluation",
    }
    for contract in contracts:
        assert contract.public_api
        assert contract.output_schemas
        assert contract.safety_boundaries
        assert contract.status in {"phase13_contract_frozen", "phase15_benchmark_gate"}


def test_engine_contract_registry_validation_passes_current_repo():
    report = validate_engine_contract_registry(ROOT)

    assert report["schema"] == "paideia-engine-contract-validation/v1"
    assert report["status"] == "passed"
    assert report["summary"]["engine_count"] == 10
    assert report["summary"]["failed"] == 0
    assert report["issues"] == []


def test_engine_contract_registry_validation_blocks_missing_repo_files(tmp_path):
    report = validate_engine_contract_registry(tmp_path)

    assert report["status"] == "blocked"
    assert report["summary"]["failed"] > 0
    assert any(issue["code"] == "package_exists" for issue in report["issues"])
