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


def test_configured_suite_runs_all_engines_and_writes_engine_outputs(tmp_path):
    result = run_configured_suite(_sample_config(tmp_path), output_dir=tmp_path / "outputs")

    assert result["schema"] == "paideia-configured-suite-run/v1"
    assert result["config_id"] == "phase5-demo"
    assert result["execution_trace"] == [
        "data_acquisition",
        "acquisition_validation",
        "curriculum_mapping",
        "cultivation",
        "assessment",
        "stress",
        "promotion",
        "governance",
        "runtime",
        "verification",
    ]
    assert result["outputs"]["runtime"]["schema"] == "paideia-runtime-run/v1"
    assert result["outputs"]["acquisition_validation"]["status"] == "passed"
    assert result["outputs"]["verification"]["checks"]["acquisition_validation_passed"] is True
    assert result["outputs"]["promotion"]["status"] == "promoted"
    assert result["outputs"]["verification"]["passed"] is True
    assert result["trace_metadata"]["output_count"] == len(result["output_paths"])

    for path in result["output_paths"].values():
        assert Path(path).exists()


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
