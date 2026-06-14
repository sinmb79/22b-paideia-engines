from pathlib import Path

import pytest

from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_catalog import default_seed_catalog


def test_data_acquisition_engine_blocks_restricted_textbooks_without_license(tmp_path):
    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)

    decision = engine.evaluate_source("digital_textbook_viewer_content")

    assert decision["source_id"] == "digital_textbook_viewer_content"
    assert decision["decision"] == "blocked"
    assert decision["acquisition_mode"] == "manual_license_required"
    assert decision["auto_download"] is False
    assert "license" in decision["reason"].lower()


def test_data_acquisition_engine_builds_engine_specific_plan(tmp_path):
    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)

    plan = engine.build_engine_plan("assessment")

    assert plan["schema"] == "paideia-data-acquisition-plan/v1"
    assert plan["engine"] == "assessment"
    assert any(item["source_id"] == "aihub_math_problem_solving" for item in plan["sources"])
    assert any(item["decision"] == "blocked" for item in plan["sources"])
    assert plan["summary"]["total_sources"] >= 3


def test_register_acquired_source_records_hash_and_manifest(tmp_path):
    payload = tmp_path / "sample.jsonl"
    payload.write_text('{"question": "1+1", "answer": "2"}\n', encoding="utf-8")
    license_note = tmp_path / "license.md"
    license_note.write_text("Downloaded after AI-Hub terms review.", encoding="utf-8")
    manifest_path = tmp_path / "acquired_sources.jsonl"

    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)

    acquired = engine.register_acquired_source(
        "aihub_math_problem_solving",
        local_path=payload,
        license_note_path=license_note,
        approved_by="boss",
        manifest_path=manifest_path,
    )

    assert acquired["schema"] == "paideia-acquired-source/v1"
    assert acquired["source_id"] == "aihub_math_problem_solving"
    assert acquired["status"] == "acquired"
    assert acquired["hash"].startswith("sha256:")
    assert acquired["approved_by"] == "boss"
    assert manifest_path.read_text(encoding="utf-8").strip()


def test_register_restricted_source_requires_license_note(tmp_path):
    payload = tmp_path / "restricted.txt"
    payload.write_text("licensed textbook excerpt", encoding="utf-8")
    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)

    with pytest.raises(PermissionError):
        engine.register_acquired_source(
            "publisher_textbook_purchase_or_license",
            local_path=payload,
            approved_by="boss",
        )
