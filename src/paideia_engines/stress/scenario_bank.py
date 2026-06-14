"""Scenario bank primitives for stress rehearsal."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable


STRESS_SCENARIO_PACK_SCHEMA = "paideia-stress-scenario-pack/v1"
STRESS_SCENARIO_PACK_DIAGNOSTICS_SCHEMA = "paideia-stress-scenario-pack-diagnostics/v1"
PROMOTION_LEAK_KEYS = {"promotion_decision", "ledger_version", "experience_id"}
ALLOWED_PACK_FIELDS = {
    "schema",
    "pack_id",
    "version",
    "description",
    "promotion_boundary",
    "content_scope",
    "subjects",
    "scenarios",
}
ALLOWED_SCENARIO_FIELDS = {
    "scenario_id",
    "subject",
    "grade_band",
    "stressor_type",
    "prompt",
    "expected_signal",
    "standard_ids",
    "traps",
    "time_limit_seconds",
    "difficulty",
}
ALLOWED_SUBJECTS = {"math", "language", "science", "evidence_review"}
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}


@dataclass(frozen=True)
class StressScenario:
    """A deterministic stress scenario mapped to curriculum standards."""

    scenario_id: str
    subject: str
    grade_band: str
    stressor_type: str
    prompt: str
    expected_signal: str
    standard_ids: list[str]
    traps: list[str] = field(default_factory=list)
    time_limit_seconds: int | None = None
    difficulty: str = "medium"

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id is required.")
        if self.subject not in ALLOWED_SUBJECTS:
            raise ValueError(f"subject must be one of: {', '.join(sorted(ALLOWED_SUBJECTS))}.")
        if not self.grade_band:
            raise ValueError("grade_band is required.")
        if not self.stressor_type:
            raise ValueError("stressor_type is required.")
        if not self.prompt:
            raise ValueError("prompt is required.")
        if not self.expected_signal:
            raise ValueError("expected_signal is required.")
        if not self.standard_ids:
            raise ValueError("standard_ids is required.")
        if self.time_limit_seconds is not None and self.time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds must be positive when provided.")
        if self.difficulty not in ALLOWED_DIFFICULTIES:
            raise ValueError(f"difficulty must be one of: {', '.join(sorted(ALLOWED_DIFFICULTIES))}.")

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "subject": self.subject,
            "grade_band": self.grade_band,
            "stressor_type": self.stressor_type,
            "prompt": self.prompt,
            "expected_signal": self.expected_signal,
            "standard_ids": list(self.standard_ids),
            "traps": list(self.traps),
            "time_limit_seconds": self.time_limit_seconds,
            "difficulty": self.difficulty,
        }


class StressScenarioBank:
    """Index and select stress scenarios without executing promotion decisions."""

    schema = "paideia-stress-scenario-bank/v1"

    def __init__(self, scenarios: Iterable[StressScenario]) -> None:
        self._scenarios: dict[str, StressScenario] = {}
        for scenario in scenarios:
            if scenario.scenario_id in self._scenarios:
                raise ValueError(f"Duplicate stress scenario_id: {scenario.scenario_id}")
            self._scenarios[scenario.scenario_id] = scenario

    @classmethod
    def from_file(cls, path: str | Path, *, strict: bool = True) -> "StressScenarioBank":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_mapping(payload, strict=strict)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any], *, strict: bool = True) -> "StressScenarioBank":
        if strict:
            report = diagnose_stress_scenario_pack(payload)
            if report["status"] != "passed":
                raise ValueError(f"Stress scenario pack diagnostics failed: {report['status']}")
        if payload.get("schema") != STRESS_SCENARIO_PACK_SCHEMA:
            raise ValueError(f"Stress scenario pack schema must be {STRESS_SCENARIO_PACK_SCHEMA}.")
        scenarios = payload.get("scenarios", [])
        if not isinstance(scenarios, list) or not scenarios:
            raise ValueError("Stress scenario pack requires at least one scenario.")
        return cls(_scenario_from_mapping(item) for item in scenarios)

    def __len__(self) -> int:
        return len(self._scenarios)

    def get(self, scenario_id: str) -> StressScenario:
        try:
            return self._scenarios[scenario_id]
        except KeyError as exc:
            raise KeyError(f"Unknown stress scenario_id: {scenario_id}") from exc

    def select(
        self,
        *,
        standard_ids: Iterable[str] | None = None,
        stressor_types: Iterable[str] | None = None,
    ) -> list[StressScenario]:
        standard_filter = set(standard_ids or [])
        stressor_filter = set(stressor_types or [])

        selected: list[StressScenario] = []
        for scenario in self._scenarios.values():
            if standard_filter and not (standard_filter & set(scenario.standard_ids)):
                continue
            if stressor_filter and scenario.stressor_type not in stressor_filter:
                continue
            selected.append(scenario)
        return selected

    def build_plan(self, standard_id: str) -> dict[str, object]:
        scenarios = self.select(standard_ids=[standard_id])
        stressor_types = sorted({scenario.stressor_type for scenario in scenarios})

        return {
            "schema": "paideia-stress-plan/v1",
            "standard_id": standard_id,
            "scenario_count": len(scenarios),
            "stressor_types": stressor_types,
            "scenarios": [scenario.to_dict() for scenario in scenarios],
            "promotion_boundary": "stress emits candidate signals only; promotion decides memory admission",
        }


def diagnose_stress_scenario_pack(path: str | Path) -> dict[str, Any]:
    """Validate a public-safe subject stress scenario pack."""

    pack_path = Path(path).resolve() if not isinstance(path, dict) else Path("<mapping>")
    issues: list[dict[str, Any]] = []
    checks = {
        "file_exists": pack_path.exists(),
        "json_object": False,
        "schema_matches": False,
        "scenarios_present": False,
        "scenario_ids_unique": False,
        "scenarios_valid": False,
        "curriculum_links_present": False,
        "subject_coverage_present": False,
        "promotion_boundary_clean": False,
    }
    payload: dict[str, Any] = {}
    scenarios: list[Any] = []

    if isinstance(path, dict):
        loaded = path
        checks["file_exists"] = True
    elif not pack_path.exists():
        issues.append(_issue("error", "stress_pack_missing", "Stress scenario pack file does not exist."))
        return _diagnostic_report(pack_path, payload, scenarios, checks, issues)
    else:
        try:
            loaded = json.loads(pack_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(_issue("error", "stress_pack_json_invalid", "Stress scenario pack JSON is invalid.", error=str(exc)))
            return _diagnostic_report(pack_path, payload, scenarios, checks, issues)

    if not isinstance(loaded, dict):
        issues.append(
            _issue(
                "error",
                "stress_pack_not_object",
                "Stress scenario pack must be a JSON object.",
                actual_type=type(loaded).__name__,
            )
        )
        return _diagnostic_report(pack_path, payload, scenarios, checks, issues)

    payload = loaded
    checks["json_object"] = True
    _check_allowed_fields(payload, ALLOWED_PACK_FIELDS, issues, path="$")
    checks["schema_matches"] = payload.get("schema") == STRESS_SCENARIO_PACK_SCHEMA
    if not checks["schema_matches"]:
        issues.append(
            _issue(
                "error",
                "stress_pack_schema_mismatch",
                "Stress scenario pack schema mismatch.",
                expected=STRESS_SCENARIO_PACK_SCHEMA,
                actual=payload.get("schema"),
            )
        )

    raw_scenarios = payload.get("scenarios", [])
    if isinstance(raw_scenarios, list):
        scenarios = raw_scenarios
    else:
        issues.append(_issue("error", "stress_pack_scenarios_not_list", "scenarios must be a list."))

    checks["scenarios_present"] = bool(scenarios)
    if not checks["scenarios_present"]:
        issues.append(_issue("error", "stress_pack_empty", "Stress scenario pack requires scenarios."))

    checks["scenario_ids_unique"] = _check_unique_scenario_ids(scenarios, issues)
    checks["scenarios_valid"] = _check_scenarios_valid(scenarios, issues)
    checks["curriculum_links_present"] = _check_curriculum_links(scenarios, issues)
    checks["subject_coverage_present"] = _check_subject_coverage(scenarios, issues)
    checks["promotion_boundary_clean"] = _check_promotion_boundary(payload, issues)

    return _diagnostic_report(pack_path, payload, scenarios, checks, issues)


def _scenario_from_mapping(payload: Any) -> StressScenario:
    if not isinstance(payload, dict):
        raise TypeError("Stress scenario must be a mapping.")
    _require_allowed_fields(payload, ALLOWED_SCENARIO_FIELDS, "stress scenario")
    _require_string(payload, "scenario_id")
    _require_string(payload, "subject")
    _require_string(payload, "grade_band")
    _require_string(payload, "stressor_type")
    _require_string(payload, "prompt")
    _require_string(payload, "expected_signal")
    standard_ids = _require_string_list(payload, "standard_ids")
    traps = _optional_string_list(payload, "traps")
    time_limit_seconds = payload.get("time_limit_seconds")
    if time_limit_seconds is not None and not isinstance(time_limit_seconds, int):
        raise TypeError("time_limit_seconds must be an integer when provided.")
    _require_string(payload, "difficulty", required=False)
    return StressScenario(
        scenario_id=payload["scenario_id"],
        subject=payload["subject"],
        grade_band=payload["grade_band"],
        stressor_type=payload["stressor_type"],
        prompt=payload["prompt"],
        expected_signal=payload["expected_signal"],
        standard_ids=standard_ids,
        traps=traps,
        time_limit_seconds=time_limit_seconds,
        difficulty=payload.get("difficulty", "medium"),
    )


def _check_unique_scenario_ids(scenarios: list[Any], issues: list[dict[str, Any]]) -> bool:
    seen: dict[str, int] = {}
    unique = True
    for index, item in enumerate(scenarios, start=1):
        scenario_id = str(item.get("scenario_id", "")) if isinstance(item, dict) else ""
        if scenario_id in seen:
            unique = False
            issues.append(
                _issue(
                    "error",
                    "duplicate_stress_scenario_id",
                    "Stress scenario ids must be unique.",
                    scenario_id=scenario_id,
                    first_index=seen[scenario_id],
                    index=index,
                )
            )
        else:
            seen[scenario_id] = index
    return unique


def _check_scenarios_valid(scenarios: list[Any], issues: list[dict[str, Any]]) -> bool:
    valid = True
    for index, item in enumerate(scenarios, start=1):
        try:
            _scenario_from_mapping(item)
        except Exception as exc:  # noqa: BLE001 - diagnostics report all schema defects.
            valid = False
            issues.append(
                _issue(
                    "error",
                    "invalid_stress_scenario",
                    str(exc),
                    index=index,
                    exception_type=type(exc).__name__,
                )
            )
    return valid


def _check_curriculum_links(scenarios: list[Any], issues: list[dict[str, Any]]) -> bool:
    linked = True
    for index, item in enumerate(scenarios, start=1):
        standard_ids = item.get("standard_ids", []) if isinstance(item, dict) else []
        if not isinstance(standard_ids, list) or not standard_ids:
            linked = False
            issues.append(
                _issue(
                    "error",
                    "stress_scenario_missing_standard_ids",
                    "Stress scenarios must link to at least one curriculum standard id.",
                    index=index,
                )
            )
    return linked


def _check_subject_coverage(scenarios: list[Any], issues: list[dict[str, Any]]) -> bool:
    covered_subjects = set()
    for item in scenarios:
        if not isinstance(item, dict):
            continue
        subject = item.get("subject")
        if isinstance(subject, str):
            covered_subjects.add(subject)
    required = {"math", "language", "science", "evidence_review"}
    missing = sorted(required - covered_subjects)
    if missing:
        issues.append(
            _issue(
                "warning",
                "stress_pack_subject_coverage_gap",
                "Stress pack should cover math, language, and science at minimum.",
                missing_subjects=missing,
                covered_subjects=sorted(covered_subjects),
            )
        )
        return False
    return True


def _check_allowed_fields(
    payload: Any,
    allowed_fields: set[str],
    issues: list[dict[str, Any]],
    *,
    path: str,
) -> bool:
    if not isinstance(payload, dict):
        return False
    unknown = sorted(set(payload) - allowed_fields)
    if unknown:
        issues.append(
            _issue(
                "error",
                "unknown_stress_pack_field",
                "Stress scenario packs must use the documented schema fields only.",
                path=path,
                fields=unknown,
            )
        )
        return False
    return True


def _require_allowed_fields(payload: dict[str, Any], allowed_fields: set[str], label: str) -> None:
    unknown = sorted(set(payload) - allowed_fields)
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {', '.join(unknown)}")


def _require_string(payload: dict[str, Any], field_name: str, *, required: bool = True) -> None:
    if field_name not in payload:
        if required:
            raise ValueError(f"{field_name} is required.")
        return
    if not isinstance(payload[field_name], str):
        raise TypeError(f"{field_name} must be a string.")
    if required and not payload[field_name].strip():
        raise ValueError(f"{field_name} is required.")


def _require_string_list(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload.get(field_name)
    if not isinstance(value, list) or not value:
        raise TypeError(f"{field_name} must be a non-empty list of strings.")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise TypeError(f"{field_name} must be a non-empty list of strings.")
    return list(value)


def _optional_string_list(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload.get(field_name, [])
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list of strings.")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise TypeError(f"{field_name} must be a list of strings.")
    return list(value)


def _check_promotion_boundary(payload: dict[str, Any], issues: list[dict[str, Any]]) -> bool:
    leaks = _promotion_leaks(payload)
    if leaks:
        issues.append(
            _issue(
                "error",
                "promotion_decision_leak",
                "Stress scenario packs must not contain promotion decisions or ledger records.",
                leaks=leaks,
            )
        )
        return False
    return True


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


def _diagnostic_report(
    pack_path: Path,
    payload: dict[str, Any],
    scenarios: list[Any],
    checks: dict[str, bool],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = sum(1 for value in checks.values() if value is not True)
    return {
        "schema": STRESS_SCENARIO_PACK_DIAGNOSTICS_SCHEMA,
        "status": _status_from_issues(issues),
        "pack_path": str(pack_path),
        "pack_id": payload.get("pack_id"),
        "summary": {
            "total": len(checks),
            "passed": len(checks) - failed,
            "failed": failed,
            "blocked": sum(1 for issue in issues if issue["severity"] == "error"),
            "review_required": sum(1 for issue in issues if issue["severity"] == "warning"),
            "scenario_count": len(scenarios),
        },
        "checks": checks,
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
    "STRESS_SCENARIO_PACK_DIAGNOSTICS_SCHEMA",
    "STRESS_SCENARIO_PACK_SCHEMA",
    "StressScenario",
    "StressScenarioBank",
    "diagnose_stress_scenario_pack",
]
