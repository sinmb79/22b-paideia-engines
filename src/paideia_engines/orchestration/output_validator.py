"""Validation for configured-suite per-engine JSON outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paideia_engines.orchestration.config_runner import EXECUTION_TRACE


VALIDATION_SCHEMA = "paideia-configured-suite-output-validation/v1"
SUITE_SCHEMA = "paideia-configured-suite-run/v1"

_ENGINE_SCHEMA_BY_NAME = {
    "data_acquisition": "paideia-data-acquisition-plan/v1",
    "acquisition_validation": "paideia-acquisition-validation-report/v1",
    "curriculum_mapping": "paideia-curriculum-learning-unit/v1",
    "cultivation": "paideia-cultivation-roadmap/v1",
    "assessment": "paideia-assessment-item-result/v1",
    "stress": "paideia-stress-scenario-run/v1",
    "promotion": "paideia-promotion-decision/v1",
    "governance": "paideia-governance-review/v1",
    "runtime": "paideia-runtime-run/v1",
    "verification": "paideia-configured-suite-verification/v1",
}
EXPECTED_ENGINE_SCHEMAS = {engine_name: _ENGINE_SCHEMA_BY_NAME[engine_name] for engine_name in EXECUTION_TRACE}

PROMOTION_LEAK_KEYS = {"promotion_decision", "ledger_version", "experience_id"}


def validate_configured_suite_outputs(output_dir: str | Path) -> dict[str, Any]:
    """Validate already-written per-engine output files without rerunning engines."""

    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {
        "required_files_present": False,
        "json_outputs_parse": False,
        "engine_schemas_match": False,
        "acquisition_validation_passed": False,
        "assessment_passed": False,
        "verification_passed": False,
        "verification_checks_all_true": False,
        "stress_no_promotion_decision": False,
        "stress_signal_candidate_only": False,
        "promotion_recorded": False,
        "governance_allowed": False,
        "governance_local_first": False,
        "runtime_review_required": False,
        "runtime_replayable": False,
    }
    base = Path(output_dir).resolve()
    outputs, files = _load_engine_outputs(base, issues)
    checks["required_files_present"] = all(file["exists"] for file in files.values())
    checks["json_outputs_parse"] = checks["required_files_present"] and len(outputs) == len(EXECUTION_TRACE)
    _validate_release_outputs(outputs, checks, issues)

    return _build_report(
        checks=checks,
        issues=issues,
        output_dir=str(base),
        files=files,
    )


def validate_configured_suite_result(
    result: str | Path | dict[str, Any],
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a configured-suite result and its per-engine output files."""

    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {
        "result_schema_matches": False,
        "execution_trace_matches": False,
        "output_count_matches": False,
        "all_engine_outputs_present_in_result": False,
        "all_engine_output_paths_present": False,
        "all_engine_output_files_exist": False,
        "engine_output_filenames_match": False,
        "engine_output_files_match_result": False,
        "engine_schemas_match": False,
        "acquisition_validation_passed": False,
        "assessment_passed": False,
        "verification_passed": False,
        "verification_checks_all_true": False,
        "stress_no_promotion_decision": False,
        "stress_signal_candidate_only": False,
        "promotion_recorded": False,
        "governance_allowed": False,
        "governance_local_first": False,
        "runtime_review_required": False,
        "runtime_replayable": False,
    }
    result_payload, result_path = _load_result_payload(result, issues)

    if result_payload is None:
        return _build_report(checks=checks, issues=issues, result_path=result_path)

    checks["result_schema_matches"] = result_payload.get("schema") == SUITE_SCHEMA
    if not checks["result_schema_matches"]:
        issues.append(
            _issue(
                "error",
                "configured_suite_schema_mismatch",
                f"Expected result schema {SUITE_SCHEMA}.",
                actual=result_payload.get("schema"),
            )
        )

    checks["execution_trace_matches"] = result_payload.get("execution_trace") == list(EXECUTION_TRACE)
    if not checks["execution_trace_matches"]:
        issues.append(_issue("error", "execution_trace_mismatch", "Configured suite execution trace changed."))

    trace_metadata = result_payload.get("trace_metadata", {})
    if not isinstance(trace_metadata, dict):
        trace_metadata = {}
    checks["output_count_matches"] = trace_metadata.get("output_count") == len(EXECUTION_TRACE)
    if not checks["output_count_matches"]:
        issues.append(
            _issue(
                "error",
                "output_count_mismatch",
                "Configured suite did not record one output per engine.",
                expected=len(EXECUTION_TRACE),
                actual=trace_metadata.get("output_count"),
            )
        )

    result_outputs = result_payload.get("outputs", {})
    if not isinstance(result_outputs, dict):
        result_outputs = {}
    checks["all_engine_outputs_present_in_result"] = all(name in result_outputs for name in EXECUTION_TRACE)
    if not checks["all_engine_outputs_present_in_result"]:
        issues.append(
            _issue(
                "error",
                "result_engine_output_missing",
                "Configured suite result is missing one or more engine outputs.",
                missing=[name for name in EXECUTION_TRACE if name not in result_outputs],
            )
        )

    output_paths = result_payload.get("output_paths", {})
    if not isinstance(output_paths, dict):
        output_paths = {}
    checks["all_engine_output_paths_present"] = all(name in output_paths for name in EXECUTION_TRACE)
    if not checks["all_engine_output_paths_present"]:
        issues.append(
            _issue(
                "error",
                "result_output_path_missing",
                "Configured suite result is missing one or more per-engine output paths.",
                missing=[name for name in EXECUTION_TRACE if name not in output_paths],
            )
        )

    resolved_output_dir = _resolve_output_dir(result_payload, output_dir, issues)
    file_outputs: dict[str, dict[str, Any]] = {}
    files: dict[str, dict[str, Any]] = {}
    if resolved_output_dir is not None:
        file_outputs, files = _load_engine_outputs(resolved_output_dir, issues)
        checks["all_engine_output_files_exist"] = all(file["exists"] for file in files.values())
        checks["engine_output_filenames_match"] = _output_paths_match_expected_files(
            output_paths,
            resolved_output_dir,
            issues,
        )
        checks["engine_output_files_match_result"] = _engine_outputs_match_result(
            file_outputs,
            result_outputs,
            issues,
        )

    outputs_for_release_checks = dict(result_outputs)
    outputs_for_release_checks.update(file_outputs)
    _validate_release_outputs(outputs_for_release_checks, checks, issues)

    return _build_report(
        checks=checks,
        issues=issues,
        result_path=result_path,
        output_dir=str(resolved_output_dir) if resolved_output_dir is not None else None,
        files=files,
    )


def _expected_filename(engine_name: str) -> str:
    index = EXECUTION_TRACE.index(engine_name) + 1
    return f"{index:02d}_{engine_name}.json"


def _load_result_payload(
    result: str | Path | dict[str, Any],
    issues: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(result, dict):
        return result, None

    path = Path(result).resolve()
    if not path.exists():
        issues.append(_issue("error", "result_file_missing", "Configured suite result file does not exist.", path=str(path)))
        return None, str(path)
    payload = _read_json_object(path, issues, missing_code="result_file_missing", parse_code="result_json_invalid")
    return payload, str(path)


def _resolve_output_dir(
    result: dict[str, Any],
    output_dir: str | Path | None,
    issues: list[dict[str, Any]],
) -> Path | None:
    if output_dir is not None:
        return Path(output_dir).resolve()

    trace_metadata = result.get("trace_metadata", {})
    if isinstance(trace_metadata, dict) and trace_metadata.get("output_dir"):
        return Path(str(trace_metadata["output_dir"])).resolve()

    output_paths = result.get("output_paths", {})
    if isinstance(output_paths, dict) and output_paths:
        parents = {Path(str(path)).resolve().parent for path in output_paths.values()}
        if len(parents) == 1:
            return parents.pop()

    issues.append(
        _issue(
            "error",
            "output_dir_unavailable",
            "Validation requires an output directory or configured suite output paths.",
        )
    )
    return None


def _load_engine_outputs(
    output_dir: Path,
    issues: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    outputs: dict[str, dict[str, Any]] = {}
    files: dict[str, dict[str, Any]] = {}

    for engine_name in EXECUTION_TRACE:
        expected_name = _expected_filename(engine_name)
        path = output_dir / expected_name
        exists = path.exists()
        files[engine_name] = {
            "path": str(path),
            "expected_filename": expected_name,
            "exists": exists,
        }
        if not exists:
            issues.append(
                _issue(
                    "error",
                    "missing_engine_output_file",
                    "Required per-engine output file is missing.",
                    engine=engine_name,
                    path=str(path),
                )
            )
            continue
        payload = _read_json_object(
            path,
            issues,
            missing_code="missing_engine_output_file",
            parse_code="engine_output_json_invalid",
            engine=engine_name,
        )
        if payload is not None:
            outputs[engine_name] = payload

    return outputs, files


def _read_json_object(
    path: Path,
    issues: list[dict[str, Any]],
    *,
    missing_code: str,
    parse_code: str,
    engine: str | None = None,
) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(_issue("error", missing_code, "JSON file does not exist.", path=str(path), engine=engine))
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            _issue(
                "error",
                parse_code,
                "JSON file could not be parsed.",
                path=str(path),
                engine=engine,
                error=str(exc),
            )
        )
        return None
    if not isinstance(payload, dict):
        issues.append(
            _issue(
                "error",
                parse_code,
                "JSON file must contain an object.",
                path=str(path),
                engine=engine,
                actual_type=type(payload).__name__,
            )
        )
        return None
    return payload


def _output_paths_match_expected_files(
    output_paths: dict[str, Any],
    output_dir: Path,
    issues: list[dict[str, Any]],
) -> bool:
    matched = True
    for engine_name in EXECUTION_TRACE:
        expected_path = output_dir / _expected_filename(engine_name)
        actual_raw = output_paths.get(engine_name)
        actual_path = Path(str(actual_raw)).resolve() if actual_raw not in (None, "") else None
        if actual_path != expected_path.resolve():
            matched = False
            issues.append(
                _issue(
                    "error",
                    "engine_output_path_mismatch",
                    "Configured suite output path does not match the expected numbered engine file.",
                    engine=engine_name,
                    expected=str(expected_path.resolve()),
                    actual=str(actual_path) if actual_path is not None else None,
                )
            )
    return matched


def _engine_outputs_match_result(
    file_outputs: dict[str, dict[str, Any]],
    result_outputs: dict[str, Any],
    issues: list[dict[str, Any]],
) -> bool:
    matched = True
    for engine_name in EXECUTION_TRACE:
        if engine_name not in file_outputs or engine_name not in result_outputs:
            matched = False
            continue
        if file_outputs[engine_name] != result_outputs[engine_name]:
            matched = False
            issues.append(
                _issue(
                    "error",
                    "engine_output_mismatch",
                    "Per-engine output file differs from the configured suite result payload.",
                    engine=engine_name,
                )
            )
    return matched


def _validate_release_outputs(
    outputs: dict[str, Any],
    checks: dict[str, bool],
    issues: list[dict[str, Any]],
) -> None:
    checks["engine_schemas_match"] = _engine_schemas_match(outputs, issues)

    acquisition = _engine_output(outputs, "acquisition_validation")
    checks["acquisition_validation_passed"] = acquisition.get("status") == "passed"
    if not checks["acquisition_validation_passed"]:
        issues.append(
            _issue(
                "error",
                "acquisition_validation_failed",
                "Acquisition validation must pass before release-quality suite output is trusted.",
                actual=acquisition.get("status"),
            )
        )

    assessment = _engine_output(outputs, "assessment")
    checks["assessment_passed"] = assessment.get("passed") is True
    if not checks["assessment_passed"]:
        issues.append(
            _issue("error", "assessment_failed", "Assessment output did not pass.", actual=assessment.get("passed"))
        )

    verification = _engine_output(outputs, "verification")
    checks["verification_passed"] = verification.get("passed") is True
    if not checks["verification_passed"]:
        issues.append(
            _issue(
                "error",
                "configured_verification_failed",
                "Configured suite verification did not pass.",
                actual=verification.get("passed"),
            )
        )
    verification_checks = verification.get("checks")
    checks["verification_checks_all_true"] = (
        isinstance(verification_checks, dict)
        and bool(verification_checks)
        and all(value is True for value in verification_checks.values())
    )
    if not checks["verification_checks_all_true"]:
        issues.append(
            _issue(
                "error",
                "configured_verification_check_failed",
                "One or more configured-suite verification checks failed.",
            )
        )

    stress = _engine_output(outputs, "stress")
    leaks = _promotion_leaks(stress)
    checks["stress_no_promotion_decision"] = not leaks
    if leaks:
        issues.append(
            _issue(
                "error",
                "stress_promotion_decision_present",
                "Stress output must only emit candidate signals, never promotion decisions.",
                leaks=leaks,
            )
        )
    promotion_signal = stress.get("promotion_signal")
    checks["stress_signal_candidate_only"] = (
        isinstance(promotion_signal, dict)
        and promotion_signal.get("status") == "candidate_only"
        and promotion_signal.get("requires_promotion_engine") is True
    )
    if not checks["stress_signal_candidate_only"]:
        issues.append(
            _issue(
                "error",
                "stress_signal_not_candidate_only",
                "Stress output must defer memory decisions to the promotion engine.",
            )
        )

    promotion = _engine_output(outputs, "promotion")
    checks["promotion_recorded"] = promotion.get("status") in {"promoted", "quarantined"}
    if not checks["promotion_recorded"]:
        issues.append(
            _issue("error", "promotion_not_recorded", "Promotion engine did not record a release-reviewable status.")
        )

    governance = _engine_output(outputs, "governance")
    checks["governance_allowed"] = governance.get("decision") == "allowed"
    if not checks["governance_allowed"]:
        issues.append(
            _issue("error", "governance_not_allowed", "Governance review must allow the configured local action.")
        )
    noted = governance.get("noted")
    checks["governance_local_first"] = (
        isinstance(noted, dict)
        and noted.get("private_asset") is False
        and noted.get("external_upload_risk") is False
    )
    if not checks["governance_local_first"]:
        issues.append(
            _issue(
                "error",
                "governance_local_first_violation",
                "Governance output indicates private asset or external upload risk.",
            )
        )

    runtime = _engine_output(outputs, "runtime")
    acceptance = runtime.get("acceptance_checklist")
    checks["runtime_review_required"] = isinstance(acceptance, dict) and acceptance.get("requires_review") is True
    if not checks["runtime_review_required"]:
        issues.append(
            _issue("error", "runtime_review_not_required", "Runtime output must require review before promotion.")
        )
    reproducibility = {}
    if isinstance(acceptance, dict):
        runtime_checks = acceptance.get("checks", {})
        if isinstance(runtime_checks, dict):
            reproducibility = runtime_checks.get("reproducibility", {})
    checks["runtime_replayable"] = (
        isinstance(reproducibility, dict) and reproducibility.get("replay_trace_available") is True
    )
    if not checks["runtime_replayable"]:
        issues.append(_issue("error", "runtime_not_replayable", "Runtime output must retain a replayable trace."))


def _engine_schemas_match(outputs: dict[str, Any], issues: list[dict[str, Any]]) -> bool:
    matched = True
    for engine_name, expected_schema in EXPECTED_ENGINE_SCHEMAS.items():
        output = outputs.get(engine_name)
        actual_schema = output.get("schema") if isinstance(output, dict) else None
        if actual_schema != expected_schema:
            matched = False
            issues.append(
                _issue(
                    "error",
                    "engine_schema_mismatch",
                    "Engine output schema does not match the expected contract.",
                    engine=engine_name,
                    expected=expected_schema,
                    actual=actual_schema,
                )
            )
    return matched


def _engine_output(outputs: dict[str, Any], engine_name: str) -> dict[str, Any]:
    output = outputs.get(engine_name, {})
    return output if isinstance(output, dict) else {}


def _promotion_leaks(payload: Any, path: str = "$") -> list[dict[str, str]]:
    leaks: list[dict[str, str]] = []
    if isinstance(payload, dict):
        if payload.get("schema") == "paideia-promotion-decision/v1":
            leaks.append({"path": path, "kind": "promotion_decision_schema"})
        for key, value in payload.items():
            child_path = f"{path}.{key}"
            if key in PROMOTION_LEAK_KEYS:
                leaks.append({"path": child_path, "kind": key})
            leaks.extend(_promotion_leaks(value, child_path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            leaks.extend(_promotion_leaks(value, f"{path}[{index}]"))
    return leaks


def _build_report(
    *,
    checks: dict[str, bool],
    issues: list[dict[str, Any]],
    result_path: str | None = None,
    output_dir: str | None = None,
    files: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    failed = sum(1 for value in checks.values() if value is not True)
    summary = {
        "total": len(checks),
        "passed": len(checks) - failed,
        "failed": failed,
        "blocked": sum(1 for issue in issues if issue["severity"] == "error"),
        "review_required": sum(1 for issue in issues if issue["severity"] == "warning"),
    }
    return {
        "schema": VALIDATION_SCHEMA,
        "status": _status_from_issues(issues),
        "result_path": result_path,
        "output_dir": output_dir,
        "summary": summary,
        "checks": checks,
        "files": files or {},
        "issues": issues,
    }


def _issue(severity: str, code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message": message, **extra}


def _status_from_issues(issues: list[dict[str, Any]]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "blocked"
    if any(issue["severity"] == "warning" for issue in issues):
        return "review_required"
    return "passed"


__all__ = [
    "EXPECTED_ENGINE_SCHEMAS",
    "VALIDATION_SCHEMA",
    "validate_configured_suite_outputs",
    "validate_configured_suite_result",
]
