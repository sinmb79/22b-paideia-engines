import json
from pathlib import Path

from paideia_engines.orchestration.config_runner import (
    load_config,
    run_config_file,
    run_configured_suite,
)


def _sample_config(tmp_path: Path) -> dict[str, object]:
    return {
        "config_id": "phase5-demo",
        "learner": {
            "learner_id": "agent:math",
            "role": "math tutor",
            "objectives": ["place value verification"],
            "task": "prepare local math evidence summary",
        },
        "data": {"storage_root": str(tmp_path / "data"), "engine": "assessment"},
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
