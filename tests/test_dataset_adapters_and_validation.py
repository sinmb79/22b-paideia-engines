import json

import pytest

from paideia_engines.assessment.item_bank import ItemBank
from paideia_engines.curriculum_mapping import CurriculumMappingEngine
from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_catalog import default_seed_catalog


def test_curriculum_mapping_loads_standards_from_public_json_adapter(tmp_path):
    payload = {
        "schema": "paideia-curriculum-standards-json/v1",
        "source_id": "ncic_curriculum_originals",
        "standards": [
            {
                "standard_id": "E-MATH-03-01",
                "school_level": "elementary",
                "grade": "3",
                "subject": "math",
                "domain": "numbers_and_operations",
                "achievement": "Add and subtract within 1000 using place value.",
            }
        ],
    }
    path = tmp_path / "standards.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    standards = CurriculumMappingEngine.load_standards_file(path)
    engine = CurriculumMappingEngine(standards)

    unit = engine.build_learning_unit(school_level="elementary", grade="3", subject="math")

    assert unit["standard_count"] == 1
    assert unit["standards"][0]["standard_id"] == "E-MATH-03-01"


def test_item_bank_loads_items_from_public_json_adapter(tmp_path):
    payload = {
        "schema": "paideia-assessment-items-json/v1",
        "source_id": "moe_csat_example_items",
        "items": [
            {
                "item_id": "math-3-001",
                "standard_id": "E-MATH-03-01",
                "gate_id": "unit_check",
                "item_type": "short_answer",
                "prompt": "What is 245 + 130?",
                "answer": "375",
                "distractors": ["365"],
                "explanation": "245 + 130 = 375.",
                "rubric": {"accuracy": 80, "explanation": 20},
            }
        ],
    }
    path = tmp_path / "items.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    bank = ItemBank.from_file(path)
    gate = bank.build_gate("unit_check", standard_ids=["E-MATH-03-01"])

    assert gate["item_count"] == 1
    assert gate["items"][0]["item_id"] == "math-3-001"


def test_acquisition_validation_blocks_restricted_full_content_without_license_note(tmp_path):
    source_path = tmp_path / "restricted.json"
    source_path.write_text('{"title": "metadata only is safer"}\n', encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "digital_textbook_viewer_content",
        "status": "acquired",
        "local_path": str(source_path),
        "hash": DataAcquisitionEngine.hash_path(source_path),
        "content_scope": "full_content",
        "license_note_path": None,
        "approved_by": "boss",
    }

    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)
    report = engine.validate_acquired_sources([acquired])

    assert report["schema"] == "paideia-acquisition-validation-report/v1"
    assert report["status"] == "blocked"
    assert report["summary"]["blocked"] == 1
    assert report["issues"][0]["code"] == "license_note_required"


def test_acquisition_validation_allows_restricted_metadata_only_manifest(tmp_path):
    source_path = tmp_path / "textbook_metadata.json"
    source_path.write_text('{"title": "Publisher textbook metadata"}\n', encoding="utf-8")
    manifest_path = tmp_path / "manifest.jsonl"

    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)
    acquired = engine.register_acquired_source(
        "publisher_textbook_purchase_or_license",
        local_path=source_path,
        approved_by="boss",
        content_scope="metadata_only",
        manifest_path=manifest_path,
    )

    report = engine.validate_manifest(manifest_path)

    assert acquired["content_scope"] == "metadata_only"
    assert report["status"] == "passed"
    assert report["summary"]["validated"] == 1
    assert report["validations"][0]["provider"] == "Textbook publishers / Education Copyright Support Center guidance"
    assert report["validations"][0]["source_url"] == "https://copyright.keris.or.kr/wft/fntLaw"
    assert report["issues"] == []


def test_acquisition_validation_detects_hash_mismatch(tmp_path):
    source_path = tmp_path / "source.jsonl"
    source_path.write_text('{"question": "1+1", "answer": "2"}\n', encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "moe_csat_example_items",
        "status": "acquired",
        "local_path": str(source_path),
        "hash": "sha256:not-the-current-hash",
        "content_scope": "public_content",
        "license_note_path": None,
        "approved_by": "boss",
    }

    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)
    report = engine.validate_acquired_sources([acquired])

    assert report["status"] == "blocked"
    assert any(issue["code"] == "hash_mismatch" for issue in report["issues"])


def test_acquisition_validation_requires_at_least_one_source(tmp_path):
    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)

    report = engine.validate_acquired_sources([])

    assert report["status"] == "review_required"
    assert report["summary"]["validated"] == 0
    assert report["issues"][0]["code"] == "no_sources_to_validate"


def test_acquisition_validation_blocks_non_acquired_manifest_status(tmp_path):
    source_path = tmp_path / "planned.jsonl"
    source_path.write_text('{"question": "not acquired yet"}\n', encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "moe_csat_example_items",
        "status": "planned",
        "local_path": str(source_path),
        "hash": DataAcquisitionEngine.hash_path(source_path),
        "content_scope": "public_content",
        "license_note_path": None,
        "approved_by": "boss",
    }

    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)
    report = engine.validate_acquired_sources([acquired])

    assert report["status"] == "blocked"
    assert any(issue["code"] == "status_not_acquired" for issue in report["issues"])


def test_acquisition_validation_blocks_public_reference_terms_source_without_note(tmp_path):
    source_path = tmp_path / "public-reference-exam.jsonl"
    source_path.write_text('{"question": "published public reference item"}\n', encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "ebsi_national_exam_archives",
        "status": "acquired",
        "local_path": str(source_path),
        "hash": DataAcquisitionEngine.hash_path(source_path),
        "content_scope": "full_content",
        "license_note_path": None,
        "approved_by": "boss",
    }

    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)
    report = engine.validate_acquired_sources([acquired])

    assert report["status"] == "blocked"
    assert any(issue["code"] == "license_note_required" for issue in report["issues"])


def test_item_bank_adapter_rejects_missing_required_fields(tmp_path):
    path = tmp_path / "bad_items.json"
    path.write_text(json.dumps({"items": [{"item_id": "broken"}]}), encoding="utf-8")

    with pytest.raises(ValueError, match="Missing assessment item fields"):
        ItemBank.from_file(path)
