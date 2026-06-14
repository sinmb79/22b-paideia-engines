import csv
import json

from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_acquisition.source_parsers import (
    build_public_exam_metadata_manifest,
    parse_aihub_math_items_json,
    parse_assessment_items_csv,
    parse_ncic_curriculum_csv,
)
from paideia_engines.data_catalog import default_seed_catalog


def test_ncic_curriculum_csv_parser_accepts_korean_headers(tmp_path):
    path = tmp_path / "ncic_standards.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["성취기준코드", "학교급", "학년", "교과", "영역", "성취기준"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "성취기준코드": "E-MATH-03-01",
                "학교급": "elementary",
                "학년": "3",
                "교과": "math",
                "영역": "numbers_and_operations",
                "성취기준": "Add and subtract within 1000 using place value.",
            }
        )

    standards = parse_ncic_curriculum_csv(path, standard_version="2022")

    assert len(standards) == 1
    assert standards[0].standard_id == "E-MATH-03-01"
    assert standards[0].source_id == "ncic_curriculum_originals"
    assert standards[0].standard_version == "2022"


def test_public_assessment_csv_parser_builds_item_bank_with_rubric(tmp_path):
    path = tmp_path / "public_items.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "item_id",
                "standard_id",
                "gate_id",
                "item_type",
                "prompt",
                "answer",
                "distractors",
                "explanation",
                "rubric",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "item_id": "math-public-001",
                "standard_id": "E-MATH-03-01",
                "gate_id": "unit_check",
                "item_type": "multiple_choice",
                "prompt": "What is 245 + 130?",
                "answer": "375",
                "distractors": "365|475",
                "explanation": "245 + 130 = 375.",
                "rubric": '{"accuracy": 80, "explanation": 20}',
            }
        )

    bank = parse_assessment_items_csv(path)
    gate = bank.build_gate("unit_check", standard_ids=["E-MATH-03-01"])

    assert gate["item_count"] == 1
    assert gate["items"][0]["item_id"] == "math-public-001"
    assert gate["items"][0]["distractors"] == ["365", "475"]
    assert gate["items"][0]["source_id"] == "moe_csat_example_items"


def test_aihub_math_json_parser_maps_problem_solution_payload(tmp_path):
    path = tmp_path / "aihub_math.json"
    path.write_text(
        json.dumps(
            {
                "data": [
                    {
                        "id": "aihub-math-001",
                        "curriculum_code": "E-MATH-03-01",
                        "question": "Show how to add 245 and 130.",
                        "answer": "375",
                        "wrong_answers": ["365"],
                        "solution": "Add hundreds, tens, and ones.",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    bank = parse_aihub_math_items_json(path)
    result = bank.build_gate("aihub_math_solution", standard_ids=["E-MATH-03-01"])

    assert result["item_count"] == 1
    assert result["items"][0]["item_type"] == "solution_process"
    assert result["items"][0]["license_tier"] == "login_or_agreement_required"


def test_ebsi_exam_metadata_manifest_tracks_metadata_only_and_validates(tmp_path):
    path = tmp_path / "ebsi_metadata.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["title", "year", "grade", "subject", "source_url"])
        writer.writeheader()
        writer.writerow(
            {
                "title": "High school public mock exam metadata",
                "year": "2026",
                "grade": "high3",
                "subject": "math",
                "source_url": "https://www.ebsi.co.kr/",
            }
        )

    records = build_public_exam_metadata_manifest(path, approved_by="boss")
    engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=tmp_path)
    report = engine.validate_acquired_sources(records)

    assert records[0]["source_id"] == "ebsi_national_exam_archives"
    assert records[0]["content_scope"] == "metadata_only"
    assert report["status"] == "passed"
