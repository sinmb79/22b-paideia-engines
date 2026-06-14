"""Diagnostics for local source parser fixture packs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from paideia_engines.assessment.item_bank import ItemBank
from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_acquisition.source_parsers import (
    build_public_exam_metadata_manifest,
    parse_aihub_math_items_json,
    parse_assessment_items_csv,
    parse_ncic_curriculum_csv,
)


DiagnosticIssue = dict[str, Any]


CSV_REQUIRED_HEADER_GROUPS = {
    "ncic_csv": {
        "standard_id": ["standard_id", "성취기준코드", "성취기준 ID", "성취기준ID", "코드"],
        "school_level": ["school_level", "학교급", "학교급별", "학교급명"],
        "grade": ["grade", "학년", "학년군", "대상학년"],
        "subject": ["subject", "과목", "교과", "교과목"],
        "domain": ["domain", "영역", "내용영역", "내용 영역"],
        "achievement": ["achievement", "성취기준", "성취기준 해설", "기준"],
    },
    "data_go_kr_csv": {
        "standard_id": ["standard_id", "성취기준코드", "성취기준 ID", "성취기준ID", "코드"],
        "school_level": ["school_level", "학교급", "학교급별", "학교급명"],
        "grade": ["grade", "학년", "학년군", "대상학년"],
        "subject": ["subject", "과목", "교과", "교과목"],
        "domain": ["domain", "영역", "내용영역", "내용 영역"],
        "achievement": ["achievement", "성취기준", "성취기준 해설", "기준"],
    },
    "public_assessment_csv": {
        "item_id": ["item_id", "문항ID", "id"],
        "standard_id": ["standard_id", "성취기준코드", "curriculum_code"],
        "prompt": ["prompt", "문항", "문제", "question"],
        "answer": ["answer", "정답"],
    },
    "aihub_csv": {
        "item_id": ["item_id", "문항ID", "id"],
        "standard_id": ["standard_id", "성취기준코드", "curriculum_code"],
        "prompt": ["prompt", "문항", "문제", "question"],
        "answer": ["answer", "정답"],
    },
    "ebsi_metadata_csv": {
        "title": ["title", "제목"],
        "source_url": ["source_url", "url", "URL"],
    },
}

JSON_REQUIRED_FIELD_GROUPS = {
    "aihub_json": {
        "standard_id": ["standard_id", "curriculum_code", "성취기준코드"],
        "prompt": ["prompt", "question", "문제", "문항"],
        "answer": ["answer", "정답"],
    }
}


def diagnose_source_file(
    path: str | Path,
    *,
    parser: str,
    source_id: str | None = None,
    provider: str | None = None,
    source_url: str | None = None,
    license_tier: str | None = None,
    expected_sha256: str | None = None,
    expected_min_records: int = 1,
    approved_by: str = "diagnostics",
) -> dict[str, Any]:
    """Inspect a local source file and run the selected parser with diagnostics."""

    source_path = Path(path)
    parser_name = parser.strip()
    definition = _parser_definition(parser_name)
    issues: list[DiagnosticIssue] = []
    checks = {
        "file_exists": source_path.exists(),
        "supported_parser": definition is not None,
        "supported_extension": False,
        "hash_matches_manifest": expected_sha256 is None,
        "required_fields_present": False,
        "parser_completed": False,
        "record_count_meets_expectation": False,
    }
    file_info: dict[str, Any] = {
        "path": str(source_path.resolve()),
        "exists": source_path.exists(),
        "size_bytes": source_path.stat().st_size if source_path.exists() else 0,
        "sha256": DataAcquisitionEngine.hash_path(source_path) if source_path.exists() else None,
    }
    input_info: dict[str, Any] = {"format": source_path.suffix.lower().lstrip(".") or "unknown"}
    output_info: dict[str, Any] = {"record_count": 0, "record_schema": None}

    if definition is None:
        issues.append(_issue("error", "unsupported_parser", f"Unsupported source parser: {parser_name}"))
        return _diagnostic_report(parser_name, source_id, file_info, input_info, output_info, checks, issues)

    checks["supported_extension"] = source_path.suffix.lower() in definition["extensions"]
    if not checks["file_exists"]:
        issues.append(_issue("error", "file_missing", "Source fixture file does not exist."))
        return _diagnostic_report(parser_name, source_id, file_info, input_info, output_info, checks, issues)
    if expected_sha256 is not None:
        checks["hash_matches_manifest"] = file_info["sha256"] == expected_sha256
        if not checks["hash_matches_manifest"]:
            issues.append(
                _issue(
                    "error",
                    "fixture_hash_mismatch",
                    "Fixture file hash does not match the manifest.",
                    expected=expected_sha256,
                    actual=file_info["sha256"],
                )
            )
    if not checks["supported_extension"]:
        allowed = ", ".join(sorted(definition["extensions"]))
        issues.append(_issue("error", "unsupported_extension", f"Expected one of: {allowed}."))
        return _diagnostic_report(parser_name, source_id, file_info, input_info, output_info, checks, issues)

    input_info.update(definition["inspect"](source_path, parser_name, issues))
    checks["required_fields_present"] = not any(
        issue["code"] in {"missing_required_header", "missing_required_json_field"}
        for issue in issues
    )

    try:
        parsed = definition["parse"](
            source_path,
            {
                key: value
                for key, value in {
                    "source_id": source_id,
                    "provider": provider,
                    "source_url": source_url,
                    "license_tier": license_tier,
                    "approved_by": approved_by,
                }.items()
                if value not in (None, "")
            },
        )
        checks["parser_completed"] = True
        output_info = _output_info(parsed, definition["record_schema"])
    except Exception as exc:  # noqa: BLE001 - diagnostics must report parser failures.
        issues.append(_issue("error", "parser_error", str(exc), exception_type=type(exc).__name__))

    checks["record_count_meets_expectation"] = output_info["record_count"] >= int(expected_min_records)
    if checks["parser_completed"] and not checks["record_count_meets_expectation"]:
        issues.append(
            _issue(
                "error",
                "record_count_below_expected",
                f"Expected at least {expected_min_records} records.",
                actual=output_info["record_count"],
            )
        )

    return _diagnostic_report(parser_name, source_id, file_info, input_info, output_info, checks, issues)


def diagnose_source_fixture_pack(manifest_path: str | Path) -> dict[str, Any]:
    """Run source parser diagnostics for every fixture in a local manifest."""

    path = Path(manifest_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    fixtures = payload.get("fixtures", [])
    if not isinstance(fixtures, list):
        raise TypeError("Source fixture pack requires a fixtures list.")

    results: list[dict[str, Any]] = []
    for index, fixture in enumerate(fixtures, start=1):
        if not isinstance(fixture, dict):
            raise TypeError(f"fixtures[{index}] must be a mapping.")
        fixture_path = Path(str(fixture.get("path", "")))
        if not fixture_path.is_absolute():
            fixture_path = path.parent / fixture_path
        diagnostic = diagnose_source_file(
            fixture_path,
            parser=str(fixture.get("parser", "")),
            source_id=_optional_str(fixture.get("source_id")),
            provider=_optional_str(fixture.get("provider")),
            source_url=_optional_str(fixture.get("source_url")),
            license_tier=_optional_str(fixture.get("license_tier")),
            expected_sha256=_optional_str(fixture.get("sha256")),
            expected_min_records=int(fixture.get("expected_min_records", 1)),
            approved_by=str(fixture.get("approved_by", "diagnostics")),
        )
        diagnostic["fixture_id"] = str(fixture.get("fixture_id", f"fixture-{index}"))
        diagnostic["content_scope"] = str(fixture.get("content_scope", "public_sample"))
        results.append(diagnostic)

    summary = {
        "total": len(results),
        "passed": sum(1 for item in results if item["status"] == "passed"),
        "review_required": sum(1 for item in results if item["status"] == "review_required"),
        "blocked": sum(1 for item in results if item["status"] == "blocked"),
    }
    status = "blocked" if summary["blocked"] else "review_required" if summary["review_required"] else "passed"
    return {
        "schema": "paideia-source-fixture-pack-diagnostics/v1",
        "pack_id": str(payload.get("pack_id", path.stem)),
        "manifest_path": str(path.resolve()),
        "status": status,
        "summary": summary,
        "fixtures": results,
    }


def _parser_definition(parser: str) -> dict[str, Any] | None:
    csv_extensions = {".csv"}
    definitions: dict[str, dict[str, Any]] = {
        "ncic_csv": {
            "extensions": csv_extensions,
            "inspect": _inspect_csv,
            "parse": lambda path, metadata: parse_ncic_curriculum_csv(
                path, **_parser_metadata(metadata, "source_id", "provider", "source_url", "license_tier")
            ),
            "record_schema": "paideia-curriculum-standard/v1",
        },
        "data_go_kr_csv": {
            "extensions": csv_extensions,
            "inspect": _inspect_csv,
            "parse": lambda path, metadata: parse_ncic_curriculum_csv(
                path, **_parser_metadata(metadata, "source_id", "provider", "source_url", "license_tier")
            ),
            "record_schema": "paideia-curriculum-standard/v1",
        },
        "public_assessment_csv": {
            "extensions": csv_extensions,
            "inspect": _inspect_csv,
            "parse": lambda path, metadata: parse_assessment_items_csv(
                path, **_parser_metadata(metadata, "source_id", "provider", "source_url", "license_tier")
            ),
            "record_schema": "paideia-assessment-item/v1",
        },
        "aihub_csv": {
            "extensions": csv_extensions,
            "inspect": _inspect_csv,
            "parse": lambda path, metadata: parse_assessment_items_csv(
                path, **_parser_metadata(metadata, "source_id", "provider", "source_url", "license_tier")
            ),
            "record_schema": "paideia-assessment-item/v1",
        },
        "aihub_json": {
            "extensions": {".json"},
            "inspect": _inspect_json,
            "parse": lambda path, metadata: parse_aihub_math_items_json(
                path, **_parser_metadata(metadata, "source_id", "provider", "source_url", "license_tier")
            ),
            "record_schema": "paideia-assessment-item/v1",
        },
        "ebsi_metadata_csv": {
            "extensions": csv_extensions,
            "inspect": _inspect_csv,
            "parse": lambda path, metadata: build_public_exam_metadata_manifest(
                path,
                approved_by=str(metadata.get("approved_by", "diagnostics")),
                **_parser_metadata(metadata, "source_id", "provider", "source_url"),
            ),
            "record_schema": "paideia-acquired-source/v1",
        },
    }
    return definitions.get(parser)


def _inspect_csv(path: Path, parser: str, issues: list[DiagnosticIssue]) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        headers = [str(header).strip() for header in (reader.fieldnames or [])]
        rows = list(reader)

    _check_required_groups(
        headers,
        CSV_REQUIRED_HEADER_GROUPS.get(parser, {}),
        issues,
        issue_code="missing_required_header",
    )
    return {
        "headers": headers,
        "row_count": len(rows),
        "missing_required_fields": [
            issue["field"]
            for issue in issues
            if issue["code"] == "missing_required_header"
        ],
    }


def _inspect_json(path: Path, parser: str, issues: list[DiagnosticIssue]) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_items = payload.get("data", payload.get("items", [])) if isinstance(payload, dict) else payload
    if not isinstance(raw_items, list):
        issues.append(_issue("error", "json_items_missing", "JSON payload requires a data or items list."))
        raw_items = []
    first_item = raw_items[0] if raw_items and isinstance(raw_items[0], dict) else {}
    _check_required_groups(
        list(first_item.keys()),
        JSON_REQUIRED_FIELD_GROUPS.get(parser, {}),
        issues,
        issue_code="missing_required_json_field",
    )
    return {
        "item_count": len(raw_items),
        "top_level_type": type(payload).__name__,
        "missing_required_fields": [
            issue["field"]
            for issue in issues
            if issue["code"] == "missing_required_json_field"
        ],
    }


def _check_required_groups(
    fields: list[str],
    required_groups: dict[str, list[str]],
    issues: list[DiagnosticIssue],
    *,
    issue_code: str,
) -> None:
    available = {field.strip() for field in fields}
    for canonical, aliases in required_groups.items():
        if not any(alias in available for alias in aliases):
            issues.append(
                _issue(
                    "error",
                    issue_code,
                    f"Missing required field group: {canonical}",
                    field=canonical,
                    aliases=aliases,
                )
            )


def _output_info(parsed: Any, record_schema: str) -> dict[str, Any]:
    if isinstance(parsed, ItemBank):
        count = len(parsed.items)
    elif isinstance(parsed, list):
        count = len(parsed)
    else:
        count = 1 if parsed is not None else 0
    return {"record_count": count, "record_schema": record_schema}


def _diagnostic_report(
    parser: str,
    source_id: str | None,
    file_info: dict[str, Any],
    input_info: dict[str, Any],
    output_info: dict[str, Any],
    checks: dict[str, bool],
    issues: list[DiagnosticIssue],
) -> dict[str, Any]:
    status = _status_from_issues(issues)
    enriched_issues = [
        {
            "parser": parser,
            "source_id": source_id,
            "path": file_info["path"],
            **issue,
        }
        for issue in issues
    ]
    return {
        "schema": "paideia-source-parser-diagnostics/v1",
        "status": status,
        "parser": parser,
        "source_id": source_id,
        "file": file_info,
        "input": input_info,
        "output": output_info,
        "checks": checks,
        "issues": enriched_issues,
    }


def _parser_metadata(metadata: dict[str, Any], *keys: str) -> dict[str, str]:
    return {
        key: str(metadata[key])
        for key in keys
        if metadata.get(key) not in (None, "")
    }


def _issue(severity: str, code: str, message: str, **extra: Any) -> DiagnosticIssue:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        **extra,
    }


def _status_from_issues(issues: list[DiagnosticIssue]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "blocked"
    if any(issue["severity"] == "warning" for issue in issues):
        return "review_required"
    return "passed"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["diagnose_source_file", "diagnose_source_fixture_pack"]
