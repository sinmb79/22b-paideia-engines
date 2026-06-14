import json
from pathlib import Path

from paideia_engines.orchestration.config_runner import run_config_file
from paideia_engines.orchestration.output_validator import (
    validate_configured_suite_outputs,
    validate_configured_suite_result,
)


ROOT = Path(__file__).resolve().parents[1]


def _run_suite(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    result_path = tmp_path / "suite-result.json"
    result = run_config_file(
        ROOT / "examples" / "configured_suite.json",
        output_path=result_path,
        output_dir=tmp_path / "engine-outputs",
    )
    return result_path, result


def _load_json(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, object]) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _issue_codes(report: dict[str, object]) -> set[str]:
    return {str(issue["code"]) for issue in report["issues"]}


def test_configured_suite_output_validator_passes_release_ready_outputs(tmp_path):
    result_path, _result = _run_suite(tmp_path)

    report = validate_configured_suite_result(result_path)

    assert report["schema"] == "paideia-configured-suite-output-validation/v1"
    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["checks"]["execution_trace_matches"] is True
    assert report["checks"]["engine_output_files_match_result"] is True
    assert report["checks"]["verification_passed"] is True


def test_configured_suite_output_validator_can_validate_output_dir_without_result_json(tmp_path):
    _result_path, result = _run_suite(tmp_path)

    report = validate_configured_suite_outputs(Path(result["trace_metadata"]["output_dir"]))

    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["checks"]["required_files_present"] is True
    assert report["checks"]["engine_schemas_match"] is True


def test_configured_suite_output_validator_blocks_missing_engine_file(tmp_path):
    result_path, result = _run_suite(tmp_path)
    Path(result["output_paths"]["stress"]).unlink()

    report = validate_configured_suite_result(result_path)

    assert report["status"] == "blocked"
    assert "missing_engine_output_file" in _issue_codes(report)
    assert report["checks"]["all_engine_output_files_exist"] is False


def test_configured_suite_output_validator_blocks_tampered_stress_promotion_decision(tmp_path):
    result_path, result = _run_suite(tmp_path)
    stress_path = Path(result["output_paths"]["stress"])
    stress_payload = _load_json(stress_path)
    stress_payload["promotion_decision"] = {"status": "promoted"}
    _write_json(stress_path, stress_payload)

    report = validate_configured_suite_result(result_path)

    assert report["status"] == "blocked"
    assert "stress_promotion_decision_present" in _issue_codes(report)
    assert report["checks"]["stress_no_promotion_decision"] is False


def test_configured_suite_output_validator_blocks_failed_verification(tmp_path):
    result_path, result = _run_suite(tmp_path)
    payload = _load_json(result_path)
    verification = payload["outputs"]["verification"]
    verification["passed"] = False
    verification["checks"]["acquisition_validation_passed"] = False
    _write_json(result_path, payload)
    _write_json(result["output_paths"]["verification"], verification)

    report = validate_configured_suite_result(result_path)

    assert report["status"] == "blocked"
    assert "configured_verification_failed" in _issue_codes(report)
    assert report["checks"]["verification_passed"] is False
