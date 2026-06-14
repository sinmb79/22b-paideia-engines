import json
from pathlib import Path

import pytest

from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.orchestration.config_runner import (
    load_config,
    run_config_file,
    run_configured_suite,
)


def _sample_config(tmp_path: Path) -> dict[str, object]:
    acquired_path = tmp_path / "public-example-items.jsonl"
    acquired_path.write_text('{"question": "245 + 130", "answer": "375"}\n', encoding="utf-8")
    return {
        "config_id": "phase5-demo",
        "learner": {
            "learner_id": "agent:math",
            "role": "math tutor",
            "objectives": ["place value verification"],
            "task": "prepare local math evidence summary",
        },
        "data": {
            "storage_root": str(tmp_path / "data"),
            "engine": "assessment",
            "acquired_sources": [
                {
                    "schema": "paideia-acquired-source/v1",
                    "source_id": "moe_csat_example_items",
                    "status": "acquired",
                    "local_path": str(acquired_path),
                    "hash": DataAcquisitionEngine.hash_path(acquired_path),
                    "content_scope": "public_content",
                    "license_note_path": None,
                    "approved_by": "boss",
                }
            ],
        },
        "curriculum": {
            "school_level": "elementary",
            "grade": "3",
            "subject": "math",
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
        },
        "runtime": {
            "engine_id": "runtime:phase5",
            "tools": ["read_file", "summarize", "write_report"],
            "artifacts": [{"path": "reports/math-evidence.json", "kind": "evidence"}],
        },
    }


def _write_production_items(tmp_path: Path) -> Path:
    items_path = tmp_path / "production-items.json"
    items_path.write_text(
        json.dumps(
            {
                "schema": "paideia-assessment-items/v1",
                "items": [
                    {
                        "item_id": "math-3-prod",
                        "standard_id": "E-MATH-03-01",
                        "gate_id": "unit_check",
                        "item_type": "short_answer",
                        "prompt": "What is 245 + 130?",
                        "answer": "375",
                        "distractors": [],
                        "explanation": "245 + 130 = 375.",
                        "rubric": {"accuracy": 80, "explanation": 20},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return items_path


def _make_production_config(tmp_path: Path) -> dict[str, object]:
    items_path = _write_production_items(tmp_path)
    config = _sample_config(tmp_path)
    config["schema"] = "paideia-configured-suite/v1"
    config["mode"] = "production"
    config["data"]["acquired_sources"] = [
        {
            "schema": "paideia-acquired-source/v1",
            "source_id": "moe_csat_example_items",
            "status": "acquired",
            "local_path": str(items_path),
            "hash": DataAcquisitionEngine.hash_path(items_path),
            "content_scope": "public_content",
            "license_note_path": None,
            "approved_by": "boss",
        }
    ]
    config["assessment"] = {
        "items_path": str(items_path),
        "parser": "paideia_json",
        "item_id": "math-3-prod",
        "answer": "375",
        "explanation": "I used place value to verify 375.",
    }
    config["stress"] = {
        "scenario_id": "phase5-contradictory-evidence",
        "response": "I compare both sources, verify place value, and ask for review before memory promotion.",
    }
    config["governance"] = {
        "action": "run_local_task",
        "context": {"contains_private_assets": False},
    }
    return config


def test_configured_suite_runs_all_engines_and_writes_engine_outputs(tmp_path):
    result = run_configured_suite(_sample_config(tmp_path), output_dir=tmp_path / "outputs")

    assert result["schema"] == "paideia-configured-suite-run/v1"
    assert result["trace_schema"] == "paideia-configured-suite-trace/v2"
    assert result["config_id"] == "phase5-demo"
    assert result["execution_trace"] == [
        "data_acquisition",
        "acquisition_validation",
        "curriculum_mapping",
        "cultivation",
        "assessment",
        "stress",
        "governance",
        "runtime",
        "promotion",
        "verification",
    ]
    assert result["outputs"]["runtime"]["schema"] == "paideia-runtime-run/v1"
    assert result["outputs"]["acquisition_validation"]["status"] == "passed"
    assert result["outputs"]["verification"]["checks"]["acquisition_validation_passed"] is True
    assert result["outputs"]["promotion"]["status"] == "promoted"
    assert result["outputs"]["verification"]["passed"] is True
    assert result["trace_metadata"]["output_count"] == len(result["output_paths"])
    assert result["execution_trace"].index("promotion") > result["execution_trace"].index("governance")
    assert result["execution_trace"].index("promotion") > result["execution_trace"].index("runtime")
    assert result["outputs"]["promotion"]["event"]["runtime_run_id"] == result["outputs"]["runtime"]["run_id"]
    assert result["outputs"]["promotion"]["event"]["governance_decision"] == result["outputs"]["governance"]["decision"]

    for path in result["output_paths"].values():
        assert Path(path).exists()


def test_production_config_rejects_demo_defaults(tmp_path):
    config = _sample_config(tmp_path)
    config["schema"] = "paideia-configured-suite/v1"
    config["mode"] = "production"

    with pytest.raises(ValueError, match="config.assessment.item_id"):
        run_configured_suite(config, output_dir=tmp_path / "outputs")


def test_production_config_runs_when_required_values_are_explicit(tmp_path):
    config = _make_production_config(tmp_path)

    result = run_configured_suite(config, output_dir=tmp_path / "outputs")

    assert result["mode"] == "production"
    assert result["outputs"]["verification"]["passed"] is True


def test_production_config_rejects_missing_curriculum_standards(tmp_path):
    config = _make_production_config(tmp_path)
    config["curriculum"] = {
        "school_level": "elementary",
        "grade": "3",
        "subject": "math",
    }

    with pytest.raises(ValueError, match="config.curriculum.standards"):
        run_configured_suite(config, output_dir=tmp_path / "outputs")


def test_production_config_rejects_missing_governance(tmp_path):
    config = _make_production_config(tmp_path)
    config.pop("governance")

    with pytest.raises(ValueError, match="config.governance.action"):
        run_configured_suite(config, output_dir=tmp_path / "outputs")


def test_production_config_rejects_non_mapping_governance_context(tmp_path):
    config = _make_production_config(tmp_path)
    config["governance"]["context"] = "contains_private_assets=false"

    with pytest.raises(TypeError, match="config.governance.context"):
        run_configured_suite(config, output_dir=tmp_path / "outputs")


def test_config_runner_loads_json_file_and_writes_result(tmp_path):
    config_path = tmp_path / "suite-config.json"
    output_path = tmp_path / "suite-result.json"
    config_path.write_text(json.dumps(_sample_config(tmp_path), ensure_ascii=False), encoding="utf-8")

    loaded = load_config(config_path)
    result = run_config_file(config_path, output_path=output_path, output_dir=tmp_path / "engine-outputs")

    assert loaded["config_id"] == "phase5-demo"
    assert output_path.exists()
    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved["schema"] == "paideia-configured-suite-run/v1"
    assert saved["outputs"]["curriculum_mapping"]["standard_count"] == 1
    assert result["result_path"] == str(output_path.resolve())


def test_config_runner_uses_standards_and_item_adapter_files(tmp_path):
    standards_path = tmp_path / "standards.json"
    standards_path.write_text(
        json.dumps(
            {
                "schema": "paideia-curriculum-standards-json/v1",
                "source_id": "ncic_curriculum_originals",
                "standards": [
                    {
                        "standard_id": "E-MATH-03-07",
                        "school_level": "elementary",
                        "grade": "3",
                        "subject": "math",
                        "domain": "numbers_and_operations",
                        "achievement": "Solve addition problems with place-value reasoning.",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    items_path = tmp_path / "items.json"
    items_path.write_text(
        json.dumps(
            {
                "schema": "paideia-assessment-items-json/v1",
                "source_id": "moe_csat_example_items",
                "items": [
                    {
                        "item_id": "adapter-item-001",
                        "standard_id": "E-MATH-03-07",
                        "gate_id": "unit_check",
                        "item_type": "short_answer",
                        "prompt": "What is 245 + 130?",
                        "answer": "375",
                        "distractors": [],
                        "explanation": "245 + 130 = 375.",
                        "rubric": {"accuracy": 100},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    config = _sample_config(tmp_path)
    config["data"]["acquired_sources"].extend(
        [
            {
                "schema": "paideia-acquired-source/v1",
                "source_id": "ncic_curriculum_originals",
                "status": "acquired",
                "local_path": str(standards_path),
                "hash": DataAcquisitionEngine.hash_path(standards_path),
                "content_scope": "public_content",
                "license_note_path": None,
                "approved_by": "boss",
            },
            {
                "schema": "paideia-acquired-source/v1",
                "source_id": "moe_csat_example_items",
                "status": "acquired",
                "local_path": str(items_path),
                "hash": DataAcquisitionEngine.hash_path(items_path),
                "content_scope": "public_content",
                "license_note_path": None,
                "approved_by": "boss",
            },
        ]
    )
    config["curriculum"]["standards"] = []
    config["curriculum"]["standards_path"] = str(standards_path)
    config["assessment"] = {
        "items_path": str(items_path),
        "item_id": "adapter-item-001",
        "answer": "375",
        "explanation": "245 + 130 = 375.",
    }

    result = run_configured_suite(config, output_dir=tmp_path / "outputs")

    assert result["outputs"]["curriculum_mapping"]["standards"][0]["standard_id"] == "E-MATH-03-07"
    assert result["outputs"]["assessment"]["item_id"] == "adapter-item-001"
    assert result["outputs"]["verification"]["passed"] is True


def test_config_runner_rejects_unvalidated_adapter_file(tmp_path):
    standards_path = tmp_path / "unvalidated-standards.json"
    standards_path.write_text(
        json.dumps(
            {
                "standards": [
                    {
                        "standard_id": "E-MATH-03-09",
                        "school_level": "elementary",
                        "grade": "3",
                        "subject": "math",
                        "domain": "numbers_and_operations",
                        "achievement": "Use place value to solve problems.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    config = _sample_config(tmp_path)
    config["curriculum"]["standards"] = []
    config["curriculum"]["standards_path"] = str(standards_path)

    with pytest.raises(PermissionError, match="curriculum.standards_path"):
        run_configured_suite(config, output_dir=tmp_path / "outputs")


def test_config_runner_marks_empty_acquisition_validation_not_ready(tmp_path):
    config = _sample_config(tmp_path)
    config["data"]["acquired_sources"] = []

    result = run_configured_suite(config, output_dir=tmp_path / "outputs")

    assert result["outputs"]["acquisition_validation"]["status"] == "review_required"
    assert result["outputs"]["verification"]["checks"]["acquisition_validation_passed"] is False
    assert result["outputs"]["verification"]["passed"] is False


def test_config_file_resolves_relative_paths_from_config_location(tmp_path):
    config_dir = tmp_path / "suite"
    config_dir.mkdir()
    standards_path = config_dir / "standards.json"
    standards_path.write_text(
        json.dumps(
            {
                "schema": "paideia-curriculum-standards-json/v1",
                "source_id": "ncic_curriculum_originals",
                "standards": [
                    {
                        "standard_id": "E-MATH-03-08",
                        "school_level": "elementary",
                        "grade": "3",
                        "subject": "math",
                        "domain": "numbers_and_operations",
                        "achievement": "Use place value to verify addition results.",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    config = _sample_config(tmp_path)
    config["data"]["acquired_sources"] = [
        {
            "schema": "paideia-acquired-source/v1",
            "source_id": "ncic_curriculum_originals",
            "status": "acquired",
            "local_path": "standards.json",
            "hash": DataAcquisitionEngine.hash_path(standards_path),
            "content_scope": "public_content",
            "license_note_path": None,
            "approved_by": "boss",
        }
    ]
    config["curriculum"]["standards"] = []
    config["curriculum"]["standards_path"] = "standards.json"
    config_path = config_dir / "suite.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    result = run_config_file(config_path, output_dir=config_dir / "outputs")

    assert result["outputs"]["curriculum_mapping"]["standards"][0]["standard_id"] == "E-MATH-03-08"
    assert result["outputs"]["verification"]["passed"] is True


def test_config_runner_uses_ncic_csv_parser_after_acquisition_validation(tmp_path):
    standards_path = tmp_path / "ncic.csv"
    standards_path.write_text(
        "성취기준코드,학교급,학년,교과,영역,성취기준\n"
        "E-MATH-03-10,elementary,3,math,numbers_and_operations,Verify addition with place value.\n",
        encoding="utf-8",
    )
    config = _sample_config(tmp_path)
    config["data"]["acquired_sources"].append(
        {
            "schema": "paideia-acquired-source/v1",
            "source_id": "ncic_curriculum_originals",
            "status": "acquired",
            "local_path": str(standards_path),
            "hash": DataAcquisitionEngine.hash_path(standards_path),
            "content_scope": "public_content",
            "license_note_path": None,
            "approved_by": "boss",
        }
    )
    config["curriculum"]["standards"] = []
    config["curriculum"]["standards_path"] = str(standards_path)
    config["curriculum"]["parser"] = "ncic_csv"

    result = run_configured_suite(config, output_dir=tmp_path / "outputs")

    assert result["outputs"]["curriculum_mapping"]["standards"][0]["standard_id"] == "E-MATH-03-10"
    assert result["outputs"]["curriculum_mapping"]["standards"][0]["source_id"] == "ncic_curriculum_originals"


def test_config_runner_uses_aihub_json_parser_after_terms_note_validation(tmp_path):
    items_path = tmp_path / "aihub.json"
    items_path.write_text(
        json.dumps(
            {
                "data": [
                    {
                        "id": "aihub-math-777",
                        "curriculum_code": "E-MATH-03-01",
                        "question": "Show how to add 245 and 130.",
                        "answer": "375",
                        "solution": "Use place value.",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    note_path = tmp_path / "aihub_terms.md"
    note_path.write_text("Terms reviewed for local-only parser smoke.", encoding="utf-8")
    config = _sample_config(tmp_path)
    config["data"]["acquired_sources"].append(
        {
            "schema": "paideia-acquired-source/v1",
            "source_id": "aihub_math_problem_solving",
            "status": "acquired",
            "local_path": str(items_path),
            "hash": DataAcquisitionEngine.hash_path(items_path),
            "content_scope": "public_content",
            "license_note_path": str(note_path),
            "approved_by": "boss",
        }
    )
    config["assessment"] = {
        "items_path": str(items_path),
        "parser": "aihub_json",
        "item_id": "aihub-math-777",
        "answer": "375",
        "explanation": "Use place value.",
    }

    result = run_configured_suite(config, output_dir=tmp_path / "outputs")

    assert result["outputs"]["assessment"]["item_id"] == "aihub-math-777"
    assert result["outputs"]["assessment"]["item_type"] == "solution_process"
    assert result["outputs"]["verification"]["passed"] is True


def test_config_runner_rejects_wrong_source_parser_pairing(tmp_path):
    standards_path = tmp_path / "wrong-source.csv"
    standards_path.write_text(
        "성취기준코드,학교급,학년,교과,영역,성취기준\n"
        "E-MATH-03-11,elementary,3,math,numbers_and_operations,Verify addition.\n",
        encoding="utf-8",
    )
    config = _sample_config(tmp_path)
    config["data"]["acquired_sources"].append(
        {
            "schema": "paideia-acquired-source/v1",
            "source_id": "moe_csat_example_items",
            "status": "acquired",
            "local_path": str(standards_path),
            "hash": DataAcquisitionEngine.hash_path(standards_path),
            "content_scope": "public_content",
            "license_note_path": None,
            "approved_by": "boss",
        }
    )
    config["curriculum"]["standards"] = []
    config["curriculum"]["standards_path"] = str(standards_path)
    config["curriculum"]["parser"] = "ncic_csv"

    with pytest.raises(PermissionError, match="parser ncic_csv"):
        run_configured_suite(config, output_dir=tmp_path / "outputs")


def test_config_runner_preserves_validation_source_metadata_in_source_parser(tmp_path):
    standards_path = tmp_path / "data-go-kr-ncic.csv"
    standards_path.write_text(
        "성취기준코드,학교급,학년,교과,영역,성취기준\n"
        "E-MATH-03-12,elementary,3,math,numbers_and_operations,Verify addition with place value.\n",
        encoding="utf-8",
    )
    config = _sample_config(tmp_path)
    config["data"]["acquired_sources"].append(
        {
            "schema": "paideia-acquired-source/v1",
            "source_id": "data_go_kr_ncic_curriculum",
            "status": "acquired",
            "local_path": str(standards_path),
            "hash": DataAcquisitionEngine.hash_path(standards_path),
            "content_scope": "public_content",
            "license_note_path": None,
            "approved_by": "boss",
        }
    )
    config["curriculum"]["standards"] = []
    config["curriculum"]["standards_path"] = str(standards_path)
    config["curriculum"]["parser"] = "data_go_kr_csv"

    result = run_configured_suite(config, output_dir=tmp_path / "outputs")

    standard = result["outputs"]["curriculum_mapping"]["standards"][0]
    assert standard["source_id"] == "data_go_kr_ncic_curriculum"
    assert standard["provider"] == "Ministry of Education / data.go.kr"
    assert standard["source_url"] == "https://www.data.go.kr/data/15060742/fileData.do"
