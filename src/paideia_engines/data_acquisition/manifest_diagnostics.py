"""Diagnostics for acquired-source manifest files."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_catalog import default_seed_catalog


MANIFEST_DIAGNOSTICS_SCHEMA = "paideia-acquired-source-manifest-diagnostics/v1"
SUPPORTED_CONTENT_SCOPES = {"public_content", "metadata_only", "full_content"}
PUBLIC_RELEASE_ALLOWED_LICENSE_TIERS = {"open_public"}
PUBLIC_REPO_DIRS = {"examples", "data", "docs", "src", "tests"}
RESTRICTED_ORIGINAL_EXTENSIONS = {".hwp", ".hwpx", ".pdf", ".zip", ".mp3", ".wav", ".mp4", ".mov"}
EXAM_SOURCE_IDS = {"moe_csat_example_items", "ebsi_national_exam_archives"}
PERSONAL_PATH_PATTERN = re.compile(r"(^[A-Za-z]:\\Users\\|^/Users/|^/home/)", re.IGNORECASE)


def diagnose_acquired_source_manifest(
    manifest_path: str | Path,
    *,
    storage_root: str | Path | None = None,
    public_release: bool = True,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Inspect an acquired-source JSONL manifest and produce a release diagnostic report."""

    path = Path(manifest_path)
    resolved_path = path.resolve()
    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {
        "manifest_file_exists": resolved_path.exists(),
        "manifest_jsonl_parse": False,
        "records_present": False,
        "records_are_acquired_source_schema": False,
        "content_scopes_supported": False,
        "no_duplicate_records": False,
        "no_auto_download_requests": False,
        "no_personal_absolute_paths": False,
        "public_repo_paths_safe": False,
        "restricted_original_files_absent": False,
        "local_only_private_context_safe": False,
        "acquired_source_validation_passed": False,
        "public_release_safe": not public_release,
    }

    records, line_count = _load_manifest_records(resolved_path, issues)
    resolved_repo_root = Path(repo_root).resolve() if repo_root is not None else _default_repo_root()
    checks["manifest_jsonl_parse"] = checks["manifest_file_exists"] and not any(
        issue["code"] in {"manifest_file_missing", "manifest_jsonl_invalid", "manifest_record_not_mapping"}
        for issue in issues
    )
    checks["records_present"] = bool(records)
    if not checks["records_present"]:
        issues.append(_issue("warning", "manifest_has_no_records", "Manifest should contain at least one source."))

    checks["records_are_acquired_source_schema"] = _check_record_schemas(records, issues)
    checks["content_scopes_supported"] = _check_content_scopes(records, issues)
    checks["no_duplicate_records"] = _check_duplicate_records(records, issues)
    checks["no_auto_download_requests"] = _check_auto_download_requests(records, issues)
    checks["no_personal_absolute_paths"] = _check_personal_absolute_paths(records, issues, public_release=public_release)

    engine = DataAcquisitionEngine(
        default_seed_catalog(),
        storage_root=storage_root if storage_root is not None else resolved_path.parent,
    )
    checks["public_repo_paths_safe"] = _check_public_repo_path_leaks(
        engine,
        records,
        resolved_path.parent,
        resolved_repo_root,
        issues,
        public_release=public_release,
    )
    checks["restricted_original_files_absent"] = _check_restricted_original_files(
        records,
        resolved_path.parent,
        resolved_repo_root,
        issues,
        public_release=public_release,
    )
    checks["local_only_private_context_safe"] = _check_local_only_private_context(
        engine,
        records,
        resolved_path,
        resolved_repo_root,
        issues,
        public_release=public_release,
    )
    validation_report = engine.validate_acquired_sources(records, base_dir=resolved_path.parent)
    checks["acquired_source_validation_passed"] = validation_report["status"] == "passed"
    _append_validation_issues(validation_report, issues, records)

    if public_release:
        checks["public_release_safe"] = _check_public_release_safety(engine, records, issues)

    return _build_report(
        manifest_path=str(resolved_path),
        line_count=line_count,
        record_count=len(records),
        public_release=public_release,
        checks=checks,
        issues=issues,
        validation_report=validation_report,
    )


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_manifest_records(path: Path, issues: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    records: list[dict[str, Any]] = []
    line_count = 0
    if not path.exists():
        issues.append(_issue("error", "manifest_file_missing", "Manifest file does not exist.", path=str(path)))
        return records, line_count

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            line_count += 1
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                issues.append(
                    _issue(
                        "error",
                        "manifest_jsonl_invalid",
                        "Manifest line is not valid JSON.",
                        line_number=line_number,
                        error=str(exc),
                    )
                )
                continue
            if not isinstance(payload, dict):
                issues.append(
                    _issue(
                        "error",
                        "manifest_record_not_mapping",
                        "Manifest line must contain a JSON object.",
                        line_number=line_number,
                        actual_type=type(payload).__name__,
                    )
                )
                continue
            payload["_manifest_line_number"] = line_number
            records.append(payload)
    return records, line_count


def _check_record_schemas(records: list[dict[str, Any]], issues: list[dict[str, Any]]) -> bool:
    matched = True
    for record in records:
        if record.get("schema") != DataAcquisitionEngine.acquired_schema:
            matched = False
            issues.append(
                _issue(
                    "error",
                    "acquired_source_schema_mismatch",
                    "Manifest record must use the acquired-source schema.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=record.get("source_id"),
                    expected=DataAcquisitionEngine.acquired_schema,
                    actual=record.get("schema"),
                )
            )
    return matched


def _check_content_scopes(records: list[dict[str, Any]], issues: list[dict[str, Any]]) -> bool:
    supported = True
    for record in records:
        scope = str(record.get("content_scope", "public_content")).strip().lower()
        if scope not in SUPPORTED_CONTENT_SCOPES:
            supported = False
            issues.append(
                _issue(
                    "error",
                    "unsupported_content_scope",
                    "content_scope must be public_content, metadata_only, or full_content.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=record.get("source_id"),
                    actual=scope,
                )
            )
    return supported


def _check_duplicate_records(records: list[dict[str, Any]], issues: list[dict[str, Any]]) -> bool:
    seen: dict[tuple[str, str], int] = {}
    unique = True
    for record in records:
        key = (
            str(record.get("source_id", "")).strip(),
            str(record.get("local_path", "")).strip(),
        )
        if key in seen:
            unique = False
            issues.append(
                _issue(
                    "error",
                    "duplicate_acquired_source_record",
                    "Manifest contains duplicate source_id/local_path records.",
                    source_id=key[0],
                    local_path=key[1],
                    first_line_number=seen[key],
                    line_number=record.get("_manifest_line_number"),
                )
            )
        else:
            seen[key] = int(record.get("_manifest_line_number", 0))
    return unique


def _check_auto_download_requests(records: list[dict[str, Any]], issues: list[dict[str, Any]]) -> bool:
    clean = True
    for record in records:
        if record.get("auto_download") is True or record.get("download_url"):
            clean = False
            issues.append(
                _issue(
                    "error",
                    "auto_download_request_in_manifest",
                    "Acquired-source manifests must describe local evidence, not request downloads.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=record.get("source_id"),
                )
            )
    return clean


def _check_personal_absolute_paths(
    records: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    *,
    public_release: bool,
) -> bool:
    clean = True
    if not public_release:
        return clean
    for record in records:
        raw_path = str(record.get("local_path", "")).strip()
        if raw_path and PERSONAL_PATH_PATTERN.search(raw_path):
            clean = False
            issues.append(
                _issue(
                    "error",
                    "absolute_personal_path_in_public_manifest",
                    "Public manifests must not contain personal absolute paths.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=record.get("source_id"),
                    local_path=raw_path,
                )
            )
    return clean


def _check_public_repo_path_leaks(
    engine: DataAcquisitionEngine,
    records: list[dict[str, Any]],
    manifest_dir: Path,
    repo_root: Path,
    issues: list[dict[str, Any]],
    *,
    public_release: bool,
) -> bool:
    clean = True
    if not public_release:
        return clean
    for record in records:
        source_id = str(record.get("source_id", "")).strip()
        content_scope = str(record.get("content_scope", "public_content")).strip().lower()
        path = _resolved_record_path(record, manifest_dir)
        if path is None or not _is_under_public_repo_dir(path, repo_root):
            continue
        try:
            catalog_record = engine.get_source(source_id)
        except KeyError:
            continue
        if catalog_record.license_tier != "open_public" and content_scope != "metadata_only":
            clean = False
            issues.append(
                _issue(
                    "error",
                    "public_repo_path_leak",
                    "Non-open full-content source records must not point inside public repository paths.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=source_id,
                    local_path=str(path),
                    license_tier=catalog_record.license_tier,
                    content_scope=content_scope,
                )
            )
    return clean


def _check_restricted_original_files(
    records: list[dict[str, Any]],
    manifest_dir: Path,
    repo_root: Path,
    issues: list[dict[str, Any]],
    *,
    public_release: bool,
) -> bool:
    clean = True
    if not public_release:
        return clean
    for record in records:
        source_id = str(record.get("source_id", "")).strip()
        content_scope = str(record.get("content_scope", "public_content")).strip().lower()
        path = _resolved_record_path(record, manifest_dir)
        suffix = path.suffix.lower() if path is not None else Path(str(record.get("local_path", ""))).suffix.lower()
        if content_scope == "metadata_only" or suffix not in RESTRICTED_ORIGINAL_EXTENSIONS:
            continue
        if source_id in EXAM_SOURCE_IDS:
            clean = False
            issues.append(
                _issue(
                    "error",
                    "exam_full_content_in_public_release",
                    "Exam PDFs, HWP/HWPX files, archives, audio, or video must be metadata-only or synthetic samples in public releases.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=source_id,
                    local_path=str(path) if path is not None else str(record.get("local_path", "")),
                    extension=suffix,
                )
            )
        elif path is not None and _is_under_public_repo_dir(path, repo_root):
            clean = False
            issues.append(
                _issue(
                    "error",
                    "restricted_extension_in_repo",
                    "Original source files with restricted extensions must not be referenced from public repository paths.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=source_id,
                    local_path=str(path),
                    extension=suffix,
                )
            )
    return clean


def _check_local_only_private_context(
    engine: DataAcquisitionEngine,
    records: list[dict[str, Any]],
    manifest_path: Path,
    repo_root: Path,
    issues: list[dict[str, Any]],
    *,
    public_release: bool,
) -> bool:
    clean = True
    if public_release:
        return clean
    if not _is_under_repo(manifest_path, repo_root):
        return clean
    for record in records:
        source_id = str(record.get("source_id", "")).strip()
        content_scope = str(record.get("content_scope", "public_content")).strip().lower()
        try:
            catalog_record = engine.get_source(source_id)
        except KeyError:
            continue
        if catalog_record.license_tier != "open_public" and content_scope == "full_content":
            clean = False
            issues.append(
                _issue(
                    "error",
                    "local_only_full_content_manifest_in_repo",
                    "Local-only full-content manifests for non-open sources must live outside the public repository.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=source_id,
                    license_tier=catalog_record.license_tier,
                )
            )
    return clean


def _append_validation_issues(
    validation_report: dict[str, Any],
    issues: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> None:
    for issue in validation_report.get("issues", []):
        severity = "warning" if issue.get("code") == "no_sources_to_validate" else "error"
        source_id = issue.get("source_id")
        issues.append(
            _issue(
                severity,
                f"acquisition_validation_{issue.get('code', 'issue')}",
                str(issue.get("message", "Acquired-source validation issue.")),
                source_id=source_id,
                line_number=_line_number_for_source(records, str(source_id or "")),
            )
        )


def _check_public_release_safety(
    engine: DataAcquisitionEngine,
    records: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> bool:
    safe = True
    for record in records:
        source_id = str(record.get("source_id", "")).strip()
        content_scope = str(record.get("content_scope", "public_content")).strip().lower()
        try:
            catalog_record = engine.get_source(source_id)
        except KeyError:
            continue
        if (
            catalog_record.license_tier not in PUBLIC_RELEASE_ALLOWED_LICENSE_TIERS
            and content_scope != "metadata_only"
        ):
            safe = False
            issues.append(
                _issue(
                    "error",
                    "non_public_full_content_in_public_release",
                    "Public releases may not include full-content records for non-open sources.",
                    line_number=record.get("_manifest_line_number"),
                    source_id=source_id,
                    license_tier=catalog_record.license_tier,
                    content_scope=content_scope,
                )
            )
    return safe


def _line_number_for_source(records: list[dict[str, Any]], source_id: str) -> int | None:
    for record in records:
        if str(record.get("source_id", "")).strip() == source_id:
            line_number = record.get("_manifest_line_number")
            return int(line_number) if line_number is not None else None
    return None


def _resolved_record_path(record: dict[str, Any], manifest_dir: Path) -> Path | None:
    raw_path = str(record.get("local_path", "")).strip()
    if not raw_path:
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_dir / path
    return path.resolve()


def _is_under_public_repo_dir(path: Path, repo_root: Path) -> bool:
    if not _is_under_repo(path, repo_root):
        return False
    try:
        first_part = path.resolve().relative_to(repo_root.resolve()).parts[0]
    except (IndexError, ValueError):
        return False
    return first_part in PUBLIC_REPO_DIRS


def _is_under_repo(path: Path, repo_root: Path) -> bool:
    try:
        path.resolve().relative_to(repo_root.resolve())
        return True
    except ValueError:
        return False


def _build_report(
    *,
    manifest_path: str,
    line_count: int,
    record_count: int,
    public_release: bool,
    checks: dict[str, bool],
    issues: list[dict[str, Any]],
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    failed = sum(1 for value in checks.values() if value is not True)
    return {
        "schema": MANIFEST_DIAGNOSTICS_SCHEMA,
        "status": _status_from_issues(issues),
        "manifest_path": manifest_path,
        "public_release": public_release,
        "summary": {
            "total": len(checks),
            "passed": len(checks) - failed,
            "failed": failed,
            "blocked": sum(1 for issue in issues if issue["severity"] == "error"),
            "review_required": sum(1 for issue in issues if issue["severity"] == "warning"),
            "line_count": line_count,
            "record_count": record_count,
        },
        "checks": checks,
        "issues": issues,
        "validation_report": validation_report,
    }


def _issue(severity: str, code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"severity": severity, "code": code, "message": message, **extra}


def _status_from_issues(issues: list[dict[str, Any]]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "blocked"
    if any(issue["severity"] == "warning" for issue in issues):
        return "review_required"
    return "passed"


__all__ = ["MANIFEST_DIAGNOSTICS_SCHEMA", "diagnose_acquired_source_manifest"]
