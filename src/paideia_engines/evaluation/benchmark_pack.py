"""Release benchmark-pack validation for Paideia engine suites."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paideia_engines.orchestration.output_validator import (
    EXPECTED_ENGINE_SCHEMAS,
    validate_configured_suite_result,
)


BENCHMARK_PACK_SCHEMA = "paideia-benchmark-pack/v1"
BENCHMARK_REPORT_SCHEMA = "paideia-benchmark-report/v1"

REPORT_SPECS = {
    "contract_validation": {
        "schema": "paideia-engine-contract-validation/v1",
        "threshold_key": "min_contract_engines",
        "summary_key": "engine_count",
    },
    "adapter_certification": {
        "schema": "paideia-adapter-certification-report/v1",
        "threshold_key": "min_adapter_certifications",
        "summary_key": "certified",
    },
    "source_diagnostics": {
        "schema": "paideia-source-fixture-pack-diagnostics/v1",
        "threshold_key": "min_source_fixtures",
        "summary_key": "total",
    },
    "manifest_diagnostics": {
        "schema": "paideia-acquired-source-manifest-diagnostics/v1",
        "threshold_key": "min_manifest_records",
        "summary_key": "record_count",
    },
    "stress_pack_diagnostics": {
        "schema": "paideia-stress-scenario-pack-diagnostics/v1",
        "threshold_key": "min_stress_scenarios",
        "summary_key": "scenario_count",
    },
    "smoke": {
        "schema": "paideia-cli-smoke/v1",
        "threshold_key": "min_smoke_engines",
        "summary_key": "total",
    },
    "runtime_evidence_validation": {
        "schema": "paideia-runtime-evidence-validation/v1",
        "threshold_key": "min_runtime_artifacts",
        "summary_key": "artifact_count",
    },
}

REQUIRED_MUTATION_EXPECTATIONS = {
    "missing_engine_output_file",
    "engine_schema_mismatch",
    "stress_promotion_decision_present",
    "governance_local_first_violation",
    "runtime_not_replayable",
}


def validate_benchmark_pack(
    pack_path: str | Path,
    *,
    result: str | Path,
    output_dir: str | Path,
    reports_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Validate a benchmark pack against release evidence from the engine suite."""

    path = Path(pack_path).resolve()
    base_dir = Path(reports_dir).resolve() if reports_dir is not None else path.parent
    payload = _read_json(path)
    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {
        "pack_schema_matches": payload.get("schema") == BENCHMARK_PACK_SCHEMA,
        "benchmark_id_present": bool(str(payload.get("benchmark_id", "")).strip()),
        "golden_engine_schemas_match": False,
        "mutation_expectations_declared": False,
        "required_reports_present": False,
        "configured_suite_validation_passed": False,
        "suite_required_checks_passed": False,
        "contract_validation_passed": False,
        "adapter_certification_passed": False,
        "source_diagnostics_passed": False,
        "manifest_diagnostics_passed": False,
        "stress_pack_diagnostics_passed": False,
        "smoke_passed": False,
        "thresholds_met": False,
    }
    measurements: dict[str, Any] = {}

    if not checks["pack_schema_matches"]:
        issues.append(
            _issue(
                "error",
                "benchmark_pack_schema_mismatch",
                "Benchmark pack schema is invalid.",
                expected=BENCHMARK_PACK_SCHEMA,
                actual=payload.get("schema"),
            )
        )
    if not checks["benchmark_id_present"]:
        issues.append(_issue("error", "benchmark_id_missing", "Benchmark pack requires a benchmark_id."))

    golden_engine_schemas = payload.get("golden_engine_schemas", {})
    golden_schema_order_matches = (
        isinstance(golden_engine_schemas, dict)
        and list(golden_engine_schemas) == list(EXPECTED_ENGINE_SCHEMAS)
    )
    checks["golden_engine_schemas_match"] = (
        golden_engine_schemas == EXPECTED_ENGINE_SCHEMAS and golden_schema_order_matches
    )
    measurements["golden_engine_schema_count"] = (
        len(golden_engine_schemas) if isinstance(golden_engine_schemas, dict) else 0
    )
    measurements["golden_engine_schema_order"] = (
        list(golden_engine_schemas) if isinstance(golden_engine_schemas, dict) else []
    )
    if not checks["golden_engine_schemas_match"]:
        issues.append(
            _issue(
                "error",
                "golden_engine_schemas_mismatch",
                "Benchmark pack golden schemas must match the configured-suite engine schemas.",
                expected=EXPECTED_ENGINE_SCHEMAS,
                expected_order=list(EXPECTED_ENGINE_SCHEMAS),
                actual=golden_engine_schemas,
                actual_order=list(golden_engine_schemas) if isinstance(golden_engine_schemas, dict) else [],
            )
        )

    mutation_expectations = {str(item) for item in payload.get("required_mutation_expectations", [])}
    missing_mutation_expectations = sorted(REQUIRED_MUTATION_EXPECTATIONS - mutation_expectations)
    checks["mutation_expectations_declared"] = not missing_mutation_expectations
    measurements["mutation_expectation_count"] = len(mutation_expectations)
    if missing_mutation_expectations:
        issues.append(
            _issue(
                "error",
                "mutation_expectations_missing",
                "Benchmark pack must declare the required mutation/tamper expectations.",
                missing=missing_mutation_expectations,
            )
        )

    suite_report = validate_configured_suite_result(result, output_dir=output_dir)
    checks["configured_suite_validation_passed"] = suite_report.get("status") == "passed"
    measurements["suite_validation_status"] = suite_report.get("status")
    if not checks["configured_suite_validation_passed"]:
        issues.append(
            _issue(
                "error",
                "configured_suite_validation_blocked",
                "Configured-suite output validation must pass before benchmark release validation.",
                upstream_status=suite_report.get("status"),
                upstream_issue_codes=_issue_codes(suite_report),
            )
        )

    required_suite_checks = [str(item) for item in payload.get("required_suite_checks", [])]
    suite_checks = suite_report.get("checks", {})
    if not isinstance(suite_checks, dict):
        suite_checks = {}
    missing_or_failed_suite_checks = [
        check for check in required_suite_checks if suite_checks.get(check) is not True
    ]
    checks["suite_required_checks_passed"] = not missing_or_failed_suite_checks
    measurements["required_suite_check_count"] = len(required_suite_checks)
    if missing_or_failed_suite_checks:
        issues.append(
            _issue(
                "error",
                "suite_required_checks_failed",
                "One or more benchmark-required configured-suite checks failed.",
                failed=missing_or_failed_suite_checks,
            )
        )

    report_paths = payload.get("reports", {})
    if not isinstance(report_paths, dict):
        report_paths = {}
    reports = {
        name: _load_report(name, raw_path, base_dir, issues)
        for name, raw_path in report_paths.items()
        if name in REPORT_SPECS
    }
    missing_reports = sorted(set(REPORT_SPECS) - set(reports))
    checks["required_reports_present"] = not missing_reports and all(report is not None for report in reports.values())
    if missing_reports:
        issues.append(
            _issue(
                "error",
                "benchmark_report_missing",
                "Benchmark pack is missing one or more required report declarations.",
                missing=missing_reports,
            )
        )

    thresholds = payload.get("thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}

    threshold_failures = []
    for name, spec in REPORT_SPECS.items():
        report = reports.get(name)
        check_name = f"{name}_passed"
        passed, measurement, failure = _validate_required_report(name, spec, report, thresholds)
        checks[check_name] = passed
        measurements[name] = measurement
        if failure:
            threshold_failures.append(failure)
            issues.append(failure)

    min_engine_outputs = int(thresholds.get("min_engine_outputs", len(EXPECTED_ENGINE_SCHEMAS)))
    measurements["suite_engine_output_schema_count"] = len(EXPECTED_ENGINE_SCHEMAS)
    if len(EXPECTED_ENGINE_SCHEMAS) < min_engine_outputs:
        failure = _issue(
            "error",
            "benchmark_threshold_not_met",
            "Benchmark threshold for engine output schemas was not met.",
            threshold="min_engine_outputs",
            expected=min_engine_outputs,
            actual=len(EXPECTED_ENGINE_SCHEMAS),
        )
        threshold_failures.append(failure)
        issues.append(failure)

    checks["thresholds_met"] = not threshold_failures

    return _build_report(
        payload=payload,
        pack_path=path,
        reports_dir=base_dir,
        checks=checks,
        issues=issues,
        measurements=measurements,
        suite_report=suite_report,
        reports=reports,
    )


def _validate_required_report(
    name: str,
    spec: dict[str, str],
    report: dict[str, Any] | None,
    thresholds: dict[str, Any],
) -> tuple[bool, dict[str, Any], dict[str, Any] | None]:
    if report is None:
        return False, {"status": "missing"}, None

    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    status = report.get("status")
    expected_schema = spec["schema"]
    actual_schema = report.get("schema")
    summary_key = spec["summary_key"]
    threshold_key = spec["threshold_key"]
    actual_count = _summary_count(summary, summary_key)
    expected_count = int(thresholds.get(threshold_key, 0))
    failed = int(summary.get("failed", 0) or 0)
    measurement = {
        "schema": actual_schema,
        "status": status,
        "count_key": summary_key,
        "count": actual_count,
        "threshold_key": threshold_key,
        "threshold": expected_count,
        "failed": failed,
        "blocked": int(summary.get("blocked", 0) or 0),
    }

    if actual_schema != expected_schema:
        return (
            False,
            measurement,
            _issue(
                "error",
                "benchmark_report_schema_mismatch",
                "Required benchmark evidence report has the wrong schema.",
                report=name,
                expected=expected_schema,
                actual=actual_schema,
            ),
        )
    if status not in {None, "passed"}:
        return (
            False,
            measurement,
            _issue(
                "error",
                "benchmark_report_not_passed",
                "Required benchmark evidence report did not pass.",
                report=name,
                status=status,
            ),
        )
    if name == "smoke" and failed != 0:
        return (
            False,
            measurement,
            _issue(
                "error",
                "benchmark_smoke_failed",
                "Smoke report includes failed engine checks.",
                failed=failed,
            ),
        )
    if actual_count < expected_count:
        return (
            False,
            measurement,
            _issue(
                "error",
                "benchmark_threshold_not_met",
                "Required benchmark evidence count is below threshold.",
                report=name,
                threshold=threshold_key,
                expected=expected_count,
                actual=actual_count,
            ),
        )
    return True, measurement, None


def _summary_count(summary: dict[str, Any], key: str) -> int:
    value = summary.get(key)
    if value is None and key == "record_count":
        value = summary.get("line_count")
    return int(value or 0)


def _load_report(
    name: str,
    raw_path: Any,
    base_dir: Path,
    issues: list[dict[str, Any]],
) -> dict[str, Any] | None:
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = base_dir / path
    path = path.resolve()
    if not path.exists():
        issues.append(
            _issue(
                "error",
                "benchmark_report_file_missing",
                "Required benchmark evidence report file does not exist.",
                report=name,
                path=str(path),
            )
        )
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            _issue(
                "error",
                "benchmark_report_json_invalid",
                "Required benchmark evidence report is not valid JSON.",
                report=name,
                path=str(path),
                error=str(exc),
            )
        )
        return None
    if not isinstance(payload, dict):
        issues.append(
            _issue(
                "error",
                "benchmark_report_json_invalid",
                "Required benchmark evidence report must contain a JSON object.",
                report=name,
                path=str(path),
                actual_type=type(payload).__name__,
            )
        )
        return None
    payload["_path"] = str(path)
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Benchmark pack must be a JSON object.")
    return payload


def _issue_codes(report: dict[str, Any]) -> list[str]:
    issues = report.get("issues", [])
    if not isinstance(issues, list):
        return []
    return [str(issue.get("code", "")) for issue in issues if isinstance(issue, dict)]


def _build_report(
    *,
    payload: dict[str, Any],
    pack_path: Path,
    reports_dir: Path,
    checks: dict[str, bool],
    issues: list[dict[str, Any]],
    measurements: dict[str, Any],
    suite_report: dict[str, Any],
    reports: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    failed = sum(1 for value in checks.values() if value is not True)
    return {
        "schema": BENCHMARK_REPORT_SCHEMA,
        "status": _status_from_issues(issues),
        "benchmark_id": payload.get("benchmark_id"),
        "pack_path": str(pack_path),
        "reports_dir": str(reports_dir),
        "summary": {
            "total": len(checks),
            "passed": len(checks) - failed,
            "failed": failed,
            "blocked": sum(1 for issue in issues if issue["severity"] == "error"),
            "review_required": sum(1 for issue in issues if issue["severity"] == "warning"),
            "benchmark_count": len(payload.get("required_suite_checks", [])) + len(REPORT_SPECS),
        },
        "checks": checks,
        "measurements": measurements,
        "suite_output_validation": {
            "schema": suite_report.get("schema"),
            "status": suite_report.get("status"),
            "summary": suite_report.get("summary"),
            "issue_codes": _issue_codes(suite_report),
        },
        "evidence_reports": {
            name: {
                "schema": report.get("schema"),
                "status": report.get("status"),
                "summary": report.get("summary"),
                "path": report.get("_path"),
            }
            for name, report in reports.items()
            if isinstance(report, dict)
        },
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
    "BENCHMARK_PACK_SCHEMA",
    "BENCHMARK_REPORT_SCHEMA",
    "validate_benchmark_pack",
]
