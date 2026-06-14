"""Official adapter certification diagnostics for public-safe fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paideia_engines.data_acquisition.manifest_diagnostics import diagnose_acquired_source_manifest
from paideia_engines.data_acquisition.source_diagnostics import diagnose_source_fixture_pack


ADAPTER_CERTIFICATION_MATRIX_SCHEMA = "paideia-adapter-certification-matrix/v1"
ADAPTER_CERTIFICATION_REPORT_SCHEMA = "paideia-adapter-certification-report/v1"

ALLOWED_OFFICIAL_FORMAT_FAMILIES = {
    "ncic_data_go_kr_curriculum_csv",
    "public_assessment_csv",
    "aihub_math_json",
    "ebsi_exam_metadata_csv",
}

PARSER_SOURCE_MAP = {
    "ncic_csv": {"ncic_curriculum_originals"},
    "data_go_kr_csv": {"ncic_curriculum_originals"},
    "public_assessment_csv": {"moe_csat_example_items"},
    "aihub_json": {"aihub_math_problem_solving"},
    "aihub_csv": {"aihub_math_problem_solving"},
    "ebsi_metadata_csv": {"ebsi_national_exam_archives"},
}

PARSER_RECORD_SCHEMA_MAP = {
    "ncic_csv": "paideia-curriculum-standard/v1",
    "data_go_kr_csv": "paideia-curriculum-standard/v1",
    "public_assessment_csv": "paideia-assessment-item/v1",
    "aihub_json": "paideia-assessment-item/v1",
    "aihub_csv": "paideia-assessment-item/v1",
    "ebsi_metadata_csv": "paideia-acquired-source/v1",
}

PUBLIC_SAFE_SAMPLE_KINDS = {"synthetic", "metadata_only", "public_official_export_sample", "user_created_mini_export"}
NON_OPEN_PUBLIC_SAMPLE_KINDS = {"synthetic", "metadata_only", "user_created_mini_export"}


def certify_adapter_matrix(matrix_path: str | Path) -> dict[str, Any]:
    """Validate a parser adapter certification matrix and its linked evidence."""

    path = Path(matrix_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Adapter certification matrix must be a JSON object.")
    return _certify_payload(payload, path)


def certify_adapters(fixtures_path: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    """Infer and certify an adapter matrix from fixture and acquired-source manifests."""

    fixture_path = Path(fixtures_path)
    acquired_path = Path(manifest_path)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixtures = payload.get("fixtures", [])
    if not isinstance(fixtures, list):
        raise TypeError("Source fixture pack requires a fixtures list.")
    certifications = []
    for index, fixture in enumerate(fixtures, start=1):
        if not isinstance(fixture, dict):
            raise TypeError(f"fixtures[{index}] must be a mapping.")
        parser = str(fixture.get("parser", ""))
        fixture_id = str(fixture.get("fixture_id", f"fixture-{index}"))
        certifications.append(
            {
                "certification_id": fixture.get("certification_id", fixture_id),
                "adapter_id": fixture.get("adapter_id", fixture_id),
                "parser": parser,
                "source_id": fixture.get("source_id"),
                "fixture_id": fixture_id,
                "record_schema": fixture.get("record_schema", PARSER_RECORD_SCHEMA_MAP.get(parser, "")),
                "official_format_family": fixture.get("official_format_family", ""),
                "sample_kind": fixture.get("sample_kind", ""),
                "origin_note": fixture.get("origin_note", ""),
                "license_tier": fixture.get("license_tier", ""),
                "content_scope": fixture.get("content_scope", ""),
                "expected_min_records": fixture.get("expected_min_records", 1),
            }
        )
    matrix_payload = {
        "schema": ADAPTER_CERTIFICATION_MATRIX_SCHEMA,
        "matrix_id": f"{payload.get('pack_id', fixture_path.stem)}-certification",
        "fixture_pack_path": str(fixture_path.resolve()),
        "acquired_manifest_path": str(acquired_path.resolve()),
        "certifications": certifications,
    }
    return _certify_payload(matrix_payload, fixture_path)


def _certify_payload(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    """Validate a loaded adapter certification matrix payload."""

    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {
        "matrix_schema_matches": payload.get("schema") == ADAPTER_CERTIFICATION_MATRIX_SCHEMA,
        "certifications_present": False,
        "certification_ids_unique": False,
        "fixture_pack_diagnostics_passed": False,
        "acquired_manifest_diagnostics_passed": False,
        "fixture_links_resolve": False,
        "manifest_links_resolve": False,
        "parser_source_pairs_allowed": False,
        "record_schemas_match": False,
        "format_families_supported": False,
        "public_safe_sample_policy": False,
    }
    if not checks["matrix_schema_matches"]:
        issues.append(
            _issue(
                "error",
                "matrix_schema_mismatch",
                "Adapter certification matrix schema is invalid.",
                expected=ADAPTER_CERTIFICATION_MATRIX_SCHEMA,
                actual=payload.get("schema"),
            )
        )

    certifications = payload.get("certifications", [])
    if not isinstance(certifications, list):
        issues.append(_issue("error", "certifications_not_list", "certifications must be a list."))
        certifications = []
    checks["certifications_present"] = bool(certifications)
    if not certifications:
        issues.append(_issue("error", "certifications_missing", "At least one adapter certification is required."))

    ids = [str(item.get("certification_id", "")) for item in certifications if isinstance(item, dict)]
    checks["certification_ids_unique"] = len(ids) == len(set(ids))
    if not checks["certification_ids_unique"]:
        issues.append(_issue("error", "duplicate_certification_id", "Certification ids must be unique."))

    fixture_pack_path = _resolve_relative(path, str(payload.get("fixture_pack_path", "")))
    acquired_manifest_path = _resolve_relative(path, str(payload.get("acquired_manifest_path", "")))
    fixture_pack_report = diagnose_source_fixture_pack(fixture_pack_path) if fixture_pack_path.exists() else None
    manifest_report = (
        diagnose_acquired_source_manifest(acquired_manifest_path, repo_root=_repo_root())
        if acquired_manifest_path.exists()
        else None
    )

    checks["fixture_pack_diagnostics_passed"] = bool(fixture_pack_report and fixture_pack_report["status"] == "passed")
    checks["acquired_manifest_diagnostics_passed"] = bool(manifest_report and manifest_report["status"] == "passed")
    if not checks["fixture_pack_diagnostics_passed"]:
        issues.append(
            _issue(
                "error",
                "fixture_pack_diagnostics_not_passed",
                "Source fixture pack diagnostics must pass before adapter certification.",
                path=str(fixture_pack_path),
                status=fixture_pack_report.get("status") if fixture_pack_report else "missing",
            )
        )
    if not checks["acquired_manifest_diagnostics_passed"]:
        issues.append(
            _issue(
                "error",
                "acquired_manifest_diagnostics_not_passed",
                "Acquired-source manifest diagnostics must pass before adapter certification.",
                path=str(acquired_manifest_path),
                status=manifest_report.get("status") if manifest_report else "missing",
            )
        )

    fixture_index = _fixture_index(fixture_pack_report)
    manifest_index = _manifest_index(acquired_manifest_path)
    row_results = []
    for index, raw in enumerate(certifications, start=1):
        if not isinstance(raw, dict):
            issues.append(
                _issue(
                    "error",
                    "certification_not_mapping",
                    "Each adapter certification must be a JSON object.",
                    row_number=index,
                    actual_type=type(raw).__name__,
                )
            )
            continue
        row_result = _validate_row(
            raw,
            row_number=index,
            fixture_index=fixture_index,
            manifest_index=manifest_index,
            manifest_dir=acquired_manifest_path.parent,
            issues=issues,
        )
        row_results.append(row_result)

    row_checks = {
        "fixture_links_resolve": all(row.get("fixture_linked") for row in row_results) if row_results else False,
        "manifest_links_resolve": all(row.get("manifest_linked") for row in row_results) if row_results else False,
        "parser_source_pairs_allowed": all(row.get("parser_source_allowed") for row in row_results) if row_results else False,
        "record_schemas_match": all(row.get("record_schema_matched") for row in row_results) if row_results else False,
        "format_families_supported": all(row.get("format_family_supported") for row in row_results) if row_results else False,
        "public_safe_sample_policy": all(row.get("public_safe_sample") for row in row_results) if row_results else False,
    }
    checks.update(row_checks)

    certified_count = sum(1 for row in row_results if row.get("status") == "certified")
    checks_failed = sum(1 for passed in checks.values() if not passed)
    status = _status_from_issues(issues)
    return {
        "schema": ADAPTER_CERTIFICATION_REPORT_SCHEMA,
        "status": status,
        "matrix_path": str(path.resolve()),
        "fixture_pack_path": str(fixture_pack_path.resolve()),
        "acquired_manifest_path": str(acquired_manifest_path.resolve()),
        "summary": {
            "total": len(checks),
            "passed": len(checks) - checks_failed,
            "failed": checks_failed,
            "blocked": sum(1 for issue in issues if issue["severity"] == "error"),
            "review_required": sum(1 for issue in issues if issue["severity"] == "warning"),
            "certification_count": len(row_results),
            "certified": certified_count,
        },
        "checks": checks,
        "certifications": row_results,
        "issues": issues,
        "fixture_pack_report": _report_summary(fixture_pack_report),
        "acquired_manifest_report": _report_summary(manifest_report),
    }


def _validate_row(
    row: dict[str, Any],
    *,
    row_number: int,
    fixture_index: dict[str, dict[str, Any]],
    manifest_index: dict[tuple[str, str], dict[str, Any]],
    manifest_dir: Path,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    certification_id = str(row.get("certification_id", f"row-{row_number}"))
    adapter_id = str(row.get("adapter_id", certification_id))
    parser = str(row.get("parser", "")).strip()
    source_id = str(row.get("source_id", "")).strip()
    fixture_id = str(row.get("fixture_id", "")).strip()
    expected_schema = str(row.get("record_schema", "")).strip()
    format_family = str(row.get("official_format_family", "")).strip()
    sample_kind = str(row.get("sample_kind", "")).strip()
    origin_note = str(row.get("origin_note", "")).strip()

    fixture = fixture_index.get(fixture_id)
    fixture_linked = fixture is not None and fixture.get("status") == "passed"
    if not fixture_linked:
        issues.append(
            _issue(
                "error",
                "fixture_not_certifiable",
                "Certification row must link to a passing fixture diagnostic.",
                certification_id=certification_id,
                fixture_id=fixture_id,
            )
        )

    parser_source_allowed = source_id in PARSER_SOURCE_MAP.get(parser, set())
    if not parser_source_allowed:
        issues.append(
            _issue(
                "error",
                "parser_source_pair_not_allowed",
                "Parser/source_id pair is not in the certification allowlist.",
                certification_id=certification_id,
                parser=parser,
                source_id=source_id,
            )
        )

    actual_schema = PARSER_RECORD_SCHEMA_MAP.get(parser)
    record_schema_matched = bool(actual_schema and expected_schema == actual_schema)
    if fixture is not None:
        record_schema_matched = record_schema_matched and fixture.get("output", {}).get("record_schema") == expected_schema
    if not record_schema_matched:
        issues.append(
            _issue(
                "error",
                "record_schema_mismatch",
                "Certification record_schema must match parser output schema.",
                certification_id=certification_id,
                parser=parser,
                expected=actual_schema,
                actual=expected_schema,
                diagnostic_actual=fixture.get("output", {}).get("record_schema") if fixture else None,
            )
        )

    format_family_supported = format_family in ALLOWED_OFFICIAL_FORMAT_FAMILIES
    if not format_family_supported:
        issues.append(
            _issue(
                "error",
                "unsupported_official_format_family",
                "Certification row uses an unsupported official format family.",
                certification_id=certification_id,
                official_format_family=format_family,
            )
        )

    sample_kind_allowed = sample_kind in PUBLIC_SAFE_SAMPLE_KINDS
    if not sample_kind_allowed:
        issues.append(
            _issue(
                "error",
                "unsupported_sample_kind",
                "sample_kind must describe a public-safe fixture sample.",
                certification_id=certification_id,
                sample_kind=sample_kind,
            )
        )
    origin_note_safe = "not copied" in origin_note.lower() or "metadata" in origin_note.lower()
    if not origin_note_safe:
        issues.append(
            _issue(
                "error",
                "origin_note_not_public_safe",
                "origin_note must explain why the fixture is public-safe.",
                certification_id=certification_id,
            )
        )

    manifest_record = _linked_manifest_record(row, fixture, manifest_index, manifest_dir)
    manifest_linked = manifest_record is not None
    if not manifest_linked:
        issues.append(
            _issue(
                "error",
                "manifest_record_not_linked",
                "Certification row must link to a matching acquired-source manifest record by source_id, local_path, and hash.",
                certification_id=certification_id,
                fixture_id=fixture_id,
                source_id=source_id,
            )
        )

    public_safe_sample = bool(sample_kind_allowed and origin_note_safe and fixture_linked and manifest_linked)
    if manifest_record is not None:
        license_tier = str(manifest_record.get("license_tier", row.get("license_tier", ""))).strip()
        content_scope = str(manifest_record.get("content_scope", "")).strip().lower()
        if license_tier != "open_public" and sample_kind not in NON_OPEN_PUBLIC_SAMPLE_KINDS:
            public_safe_sample = False
            issues.append(
                _issue(
                    "error",
                    "non_open_fixture_requires_synthetic_or_metadata_sample",
                    "Non-open fixture certifications must use synthetic, user-created, or metadata-only samples.",
                    certification_id=certification_id,
                    license_tier=license_tier,
                    sample_kind=sample_kind,
                )
            )
        if license_tier != "open_public" and content_scope != "metadata_only":
            public_safe_sample = False
            issues.append(
                _issue(
                    "error",
                    "non_open_manifest_record_not_metadata_only",
                    "Non-open public certification records must be metadata_only in the acquired-source manifest.",
                    certification_id=certification_id,
                    license_tier=license_tier,
                    content_scope=content_scope,
                )
            )

    row_passed = (
        fixture_linked
        and manifest_linked
        and parser_source_allowed
        and record_schema_matched
        and format_family_supported
        and public_safe_sample
    )
    return {
        "adapter_id": adapter_id,
        "certification_id": certification_id,
        "certification_status": "certified" if row_passed else "blocked",
        "status": "certified" if row_passed else "blocked",
        "parser": parser,
        "source_id": source_id,
        "fixture_id": fixture_id,
        "fixture_path": fixture.get("file", {}).get("path") if fixture else None,
        "fixture_sha256": fixture.get("file", {}).get("sha256") if fixture else None,
        "manifest_local_path": manifest_record.get("local_path") if manifest_record else None,
        "manifest_hash": manifest_record.get("hash") if manifest_record else None,
        "content_scope": manifest_record.get("content_scope") if manifest_record else row.get("content_scope"),
        "expected_min_records": row.get("expected_min_records"),
        "official_format_family": format_family,
        "sample_kind": sample_kind,
        "record_schema": expected_schema,
        "fixture_linked": fixture_linked,
        "manifest_linked": manifest_linked,
        "parser_source_allowed": parser_source_allowed,
        "record_schema_matched": record_schema_matched,
        "format_family_supported": format_family_supported,
        "public_safe_sample": public_safe_sample,
    }


def _fixture_index(fixture_pack_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not fixture_pack_report:
        return {}
    return {str(item.get("fixture_id", "")): item for item in fixture_pack_report.get("fixtures", [])}


def _manifest_index(manifest_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not manifest_path.exists():
        return {}
    records: dict[tuple[str, str], dict[str, Any]] = {}
    with manifest_path.open("r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                continue
            records[
                (
                    str(payload.get("source_id", "")).strip(),
                    str(_resolve_relative(manifest_path, str(payload.get("local_path", ""))).resolve()),
                )
            ] = payload
    return records


def _linked_manifest_record(
    row: dict[str, Any],
    fixture: dict[str, Any] | None,
    manifest_index: dict[tuple[str, str], dict[str, Any]],
    manifest_dir: Path,
) -> dict[str, Any] | None:
    if not fixture:
        return None
    source_id = str(row.get("source_id", "")).strip()
    fixture_path = Path(str(fixture.get("file", {}).get("path", ""))).resolve()
    record = manifest_index.get((source_id, str(fixture_path)))
    if record is None:
        local_path = str(row.get("manifest_local_path", "")).strip()
        if local_path:
            record = manifest_index.get((source_id, str((manifest_dir / local_path).resolve())))
    if record is None:
        return None
    if str(record.get("hash", "")).strip() != str(fixture.get("file", {}).get("sha256", "")).strip():
        return None
    return record


def _resolve_relative(base_path: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return base_path.parent / path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _report_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "schema": report.get("schema"),
        "status": report.get("status"),
        "summary": report.get("summary"),
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
    "ADAPTER_CERTIFICATION_MATRIX_SCHEMA",
    "ADAPTER_CERTIFICATION_REPORT_SCHEMA",
    "certify_adapters",
    "certify_adapter_matrix",
]
