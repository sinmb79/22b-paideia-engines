import json
from pathlib import Path

from paideia_engines.data_acquisition.source_diagnostics import (
    diagnose_source_file,
    diagnose_source_fixture_pack,
)


ROOT = Path(__file__).resolve().parents[1]


def test_diagnose_source_file_reports_passed_ncic_fixture():
    path = ROOT / "examples" / "source_samples" / "ncic_curriculum_sample.csv"

    report = diagnose_source_file(
        path,
        parser="ncic_csv",
        source_id="ncic_curriculum_originals",
        expected_min_records=1,
    )

    assert report["schema"] == "paideia-source-parser-diagnostics/v1"
    assert report["status"] == "passed"
    assert report["parser"] == "ncic_csv"
    assert report["file"]["exists"] is True
    assert report["file"]["sha256"].startswith("sha256:")
    assert report["input"]["row_count"] == 1
    assert report["output"]["record_count"] == 1
    assert report["checks"]["hash_matches_manifest"] is True
    assert report["checks"]["parser_completed"] is True
    assert report["issues"] == []


def test_diagnose_source_file_blocks_missing_required_csv_headers(tmp_path):
    path = tmp_path / "bad_ncic.csv"
    path.write_text("standard_id,grade\nE-MATH-03-01,3\n", encoding="utf-8")

    report = diagnose_source_file(
        path,
        parser="ncic_csv",
        source_id="ncic_curriculum_originals",
        expected_min_records=1,
    )

    assert report["status"] == "blocked"
    assert report["checks"]["required_fields_present"] is False
    assert any(issue["code"] == "missing_required_header" for issue in report["issues"])
    assert any(issue["code"] == "parser_error" for issue in report["issues"])
    assert all(issue["parser"] == "ncic_csv" for issue in report["issues"])
    assert all(issue["source_id"] == "ncic_curriculum_originals" for issue in report["issues"])


def test_diagnose_source_fixture_pack_summarizes_example_pack():
    manifest_path = ROOT / "examples" / "source_fixture_pack.json"

    report = diagnose_source_fixture_pack(manifest_path)

    assert report["schema"] == "paideia-source-fixture-pack-diagnostics/v1"
    assert report["status"] == "passed"
    assert report["summary"] == {"total": 3, "passed": 3, "review_required": 0, "blocked": 0}
    assert {fixture["fixture_id"] for fixture in report["fixtures"]} == {
        "ncic-curriculum-sample",
        "aihub-math-sample",
        "ebsi-exam-metadata-sample",
    }
    assert all(fixture["checks"]["hash_matches_manifest"] is True for fixture in report["fixtures"])


def test_fixture_pack_manifest_paths_are_relative_and_public_samples_only():
    manifest_path = ROOT / "examples" / "source_fixture_pack.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["schema"] == "paideia-source-fixture-pack/v1"
    for fixture in payload["fixtures"]:
        assert not Path(fixture["path"]).is_absolute()
        assert fixture["content_scope"] in {"public_sample", "metadata_only"}
        assert fixture["sha256"].startswith("sha256:")
        assert fixture["provider"]
        assert fixture["source_url"].startswith("https://")
        assert "not copied" in fixture["origin_note"].lower() or "no exam text" in fixture["origin_note"].lower()
