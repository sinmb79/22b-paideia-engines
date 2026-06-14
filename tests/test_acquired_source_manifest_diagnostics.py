import json
from pathlib import Path

from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_acquisition.manifest_diagnostics import diagnose_acquired_source_manifest
from paideia_engines.data_catalog import default_seed_catalog


ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def test_manifest_diagnostics_passes_public_and_metadata_only_sources(tmp_path):
    public_path = tmp_path / "public-items.jsonl"
    public_path.write_text('{"question": "1+1", "answer": "2"}\n', encoding="utf-8")
    metadata_path = tmp_path / "textbook-metadata.json"
    metadata_path.write_text('{"title": "Licensed textbook metadata only"}\n', encoding="utf-8")
    manifest_path = tmp_path / "acquired_sources.jsonl"

    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)
    engine.register_acquired_source(
        "moe_csat_example_items",
        local_path=public_path,
        approved_by="boss",
        manifest_path=manifest_path,
    )
    engine.register_acquired_source(
        "publisher_textbook_purchase_or_license",
        local_path=metadata_path,
        approved_by="boss",
        content_scope="metadata_only",
        manifest_path=manifest_path,
    )

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)

    assert report["schema"] == "paideia-acquired-source-manifest-diagnostics/v1"
    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["checks"]["acquired_source_validation_passed"] is True
    assert report["checks"]["public_release_safe"] is True


def test_manifest_diagnostics_blocks_invalid_jsonl(tmp_path):
    manifest_path = tmp_path / "broken.jsonl"
    manifest_path.write_text('{"source_id": "moe_csat_example_items"}\nnot-json\n', encoding="utf-8")

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)

    assert report["status"] == "blocked"
    assert report["checks"]["manifest_jsonl_parse"] is False
    assert any(issue["code"] == "manifest_jsonl_invalid" for issue in report["issues"])


def test_manifest_diagnostics_blocks_duplicate_records(tmp_path):
    source_path = tmp_path / "public-items.jsonl"
    source_path.write_text('{"question": "1+1", "answer": "2"}\n', encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "moe_csat_example_items",
        "status": "acquired",
        "local_path": str(source_path),
        "hash": DataAcquisitionEngine.hash_path(source_path),
        "content_scope": "public_content",
        "license_note_path": None,
        "approved_by": "boss",
    }
    manifest_path = tmp_path / "duplicates.jsonl"
    _write_jsonl(manifest_path, [acquired, acquired])

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)

    assert report["status"] == "blocked"
    assert report["checks"]["no_duplicate_records"] is False
    assert any(issue["code"] == "duplicate_acquired_source_record" for issue in report["issues"])


def test_manifest_diagnostics_blocks_non_public_full_content_for_public_release(tmp_path):
    source_path = tmp_path / "aihub-full.json"
    source_path.write_text('{"data": [{"question": "licensed data"}]}\n', encoding="utf-8")
    note_path = tmp_path / "aihub-terms.md"
    note_path.write_text("Terms reviewed for local-only use.", encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "aihub_math_problem_solving",
        "status": "acquired",
        "local_path": str(source_path),
        "hash": DataAcquisitionEngine.hash_path(source_path),
        "content_scope": "full_content",
        "license_note_path": str(note_path),
        "approved_by": "boss",
    }
    manifest_path = tmp_path / "local-only.jsonl"
    _write_jsonl(manifest_path, [acquired])

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)

    assert report["status"] == "blocked"
    assert report["checks"]["acquired_source_validation_passed"] is True
    assert report["checks"]["public_release_safe"] is False
    assert any(issue["code"] == "non_public_full_content_in_public_release" for issue in report["issues"])


def test_manifest_diagnostics_blocks_non_open_full_content_inside_public_repo(tmp_path):
    repo_sample = ROOT / "examples" / "public_item_sample.jsonl"
    note_path = tmp_path / "aihub-terms.md"
    note_path.write_text("Terms reviewed for local-only use.", encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "aihub_math_problem_solving",
        "status": "acquired",
        "local_path": str(repo_sample),
        "hash": DataAcquisitionEngine.hash_path(repo_sample),
        "content_scope": "full_content",
        "license_note_path": str(note_path),
        "approved_by": "boss",
    }
    manifest_path = tmp_path / "repo-leak.jsonl"
    _write_jsonl(manifest_path, [acquired])

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "public_repo_path_leak" for issue in report["issues"])


def test_manifest_diagnostics_blocks_personal_absolute_path_in_public_manifest(tmp_path):
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "moe_csat_example_items",
        "status": "acquired",
        "local_path": r"C:\Users\sinmb\Downloads\exam.pdf",
        "hash": "sha256:not-checked-because-file-is-private",
        "content_scope": "metadata_only",
        "license_note_path": None,
        "approved_by": "boss",
    }
    manifest_path = tmp_path / "personal-path.jsonl"
    _write_jsonl(manifest_path, [acquired])

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "absolute_personal_path_in_public_manifest" for issue in report["issues"])


def test_manifest_diagnostics_blocks_exam_pdf_full_content_even_for_open_public_source(tmp_path):
    source_path = tmp_path / "moe-example-exam.pdf"
    source_path.write_text("fake pdf bytes for diagnostic test", encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "moe_csat_example_items",
        "status": "acquired",
        "local_path": str(source_path),
        "hash": DataAcquisitionEngine.hash_path(source_path),
        "content_scope": "full_content",
        "license_note_path": None,
        "approved_by": "boss",
    }
    manifest_path = tmp_path / "exam-pdf.jsonl"
    _write_jsonl(manifest_path, [acquired])

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "exam_full_content_in_public_release" for issue in report["issues"])


def test_manifest_diagnostics_preserves_line_number_for_validation_issues(tmp_path):
    source_path = tmp_path / "public-items.jsonl"
    source_path.write_text('{"question": "1+1", "answer": "2"}\n', encoding="utf-8")
    acquired = {
        "schema": "paideia-acquired-source/v1",
        "source_id": "moe_csat_example_items",
        "status": "acquired",
        "local_path": str(source_path),
        "hash": "sha256:wrong",
        "content_scope": "public_content",
        "license_note_path": None,
        "approved_by": "boss",
    }
    manifest_path = tmp_path / "hash-mismatch.jsonl"
    _write_jsonl(manifest_path, [acquired])

    report = diagnose_acquired_source_manifest(manifest_path, storage_root=tmp_path)
    issue = next(issue for issue in report["issues"] if issue["code"] == "acquisition_validation_hash_mismatch")

    assert issue["line_number"] == 1


def test_example_acquired_source_manifest_is_release_safe():
    report = diagnose_acquired_source_manifest(ROOT / "examples" / "acquired_sources_manifest.jsonl")

    assert report["status"] == "passed"
    assert report["summary"]["record_count"] == 4
