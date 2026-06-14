import json
from pathlib import Path

from paideia_engines.data_acquisition import DataAcquisitionEngine, certify_adapters


ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def test_certify_adapters_passes_example_fixture_and_manifest_matrix():
    report = certify_adapters(
        ROOT / "examples" / "source_fixture_pack.json",
        ROOT / "examples" / "acquired_sources_manifest.jsonl",
    )

    assert report["schema"] == "paideia-adapter-certification-report/v1"
    assert report["status"] == "passed"
    assert report["summary"]["certification_count"] == 4
    assert report["summary"]["certified"] == 4
    assert report["checks"]["fixture_pack_diagnostics_passed"] is True
    assert report["checks"]["acquired_manifest_diagnostics_passed"] is True
    assert report["checks"]["manifest_links_resolve"] is True
    assert {row["certification_status"] for row in report["certifications"]} == {"certified"}
    assert {row["parser"] for row in report["certifications"]} == {
        "ncic_csv",
        "public_assessment_csv",
        "aihub_json",
        "ebsi_metadata_csv",
    }


def test_certify_adapters_blocks_manifest_hash_mismatch(tmp_path):
    source_path = ROOT / "examples" / "source_samples" / "public_assessment_sample.csv"
    fixture_pack = tmp_path / "fixture_pack.json"
    fixture_pack.write_text(
        json.dumps(
            {
                "schema": "paideia-source-fixture-pack/v1",
                "pack_id": "hash-mismatch-pack",
                "fixtures": [
                    {
                        "fixture_id": "public-assessment-sample",
                        "parser": "public_assessment_csv",
                        "path": str(source_path),
                        "source_id": "moe_csat_example_items",
                        "provider": "Ministry of Education",
                        "source_url": "https://www.moe.go.kr/",
                        "license_tier": "open_public",
                        "content_scope": "public_sample",
                        "official_format_family": "public_assessment_csv",
                        "sample_kind": "synthetic",
                        "record_schema": "paideia-assessment-item/v1",
                        "expected_min_records": 1,
                        "sha256": DataAcquisitionEngine.hash_path(source_path),
                        "origin_note": "Synthetic public assessment CSV fixture; not copied exam content.",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "acquired_sources.jsonl"
    _write_jsonl(
        manifest,
        [
            {
                "schema": "paideia-acquired-source/v1",
                "source_id": "moe_csat_example_items",
                "status": "acquired",
                "local_path": str(source_path),
                "hash": "sha256:wrong",
                "content_scope": "public_content",
                "license_note_path": None,
                "approved_by": "boss",
            }
        ],
    )

    report = certify_adapters(fixture_pack, manifest)

    assert report["status"] == "blocked"
    assert report["checks"]["acquired_manifest_diagnostics_passed"] is False
    assert any(issue["code"] == "manifest_record_not_linked" for issue in report["issues"])


def test_certify_adapters_blocks_unsupported_parser_source_pair(tmp_path):
    source_path = ROOT / "examples" / "source_samples" / "public_assessment_sample.csv"
    fixture_pack = tmp_path / "fixture_pack.json"
    fixture_pack.write_text(
        json.dumps(
            {
                "schema": "paideia-source-fixture-pack/v1",
                "pack_id": "unsupported-pair-pack",
                "fixtures": [
                    {
                        "fixture_id": "bad-public-assessment-source",
                        "parser": "public_assessment_csv",
                        "path": str(source_path),
                        "source_id": "ncic_curriculum_originals",
                        "provider": "National Curriculum Information Center",
                        "source_url": "https://ncic.re.kr/",
                        "license_tier": "open_public",
                        "content_scope": "public_sample",
                        "official_format_family": "public_assessment_csv",
                        "sample_kind": "synthetic",
                        "record_schema": "paideia-assessment-item/v1",
                        "expected_min_records": 1,
                        "sha256": DataAcquisitionEngine.hash_path(source_path),
                        "origin_note": "Synthetic fixture; not copied exam content.",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifest = tmp_path / "acquired_sources.jsonl"
    _write_jsonl(
        manifest,
        [
            {
                "schema": "paideia-acquired-source/v1",
                "source_id": "ncic_curriculum_originals",
                "status": "acquired",
                "local_path": str(source_path),
                "hash": DataAcquisitionEngine.hash_path(source_path),
                "content_scope": "public_content",
                "license_note_path": None,
                "approved_by": "boss",
            }
        ],
    )

    report = certify_adapters(fixture_pack, manifest)

    assert report["status"] == "blocked"
    assert report["checks"]["parser_source_pairs_allowed"] is False
    assert any(issue["code"] == "parser_source_pair_not_allowed" for issue in report["issues"])
