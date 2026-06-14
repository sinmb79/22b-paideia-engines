"""Persistent runtime evidence bundles and artifact validation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import os


RUNTIME_EVIDENCE_BUNDLE_SCHEMA = "paideia-runtime-evidence-bundle/v1"
RUNTIME_EVIDENCE_VALIDATION_SCHEMA = "paideia-runtime-evidence-validation/v1"
RUNTIME_EVIDENCE_REPLAY_SCHEMA = "paideia-runtime-evidence-replay/v1"
RUNTIME_TRACE_SCHEMA = "paideia-runtime-trace/v1"
RUNTIME_ACCEPTANCE_SCHEMA = "paideia-runtime-acceptance-checklist/v1"

REQUIRED_BUNDLE_FILES = {
    "runtime_run": "paideia-runtime-run/v1",
    "trace": RUNTIME_TRACE_SCHEMA,
    "artifact_manifest": "paideia-runtime-artifact-manifest/v1",
    "acceptance_checklist": RUNTIME_ACCEPTANCE_SCHEMA,
}

PROMOTION_LEAK_KEYS = {"promotion_decision", "ledger_version", "experience_id"}
SENSITIVE_ARTIFACT_NAME_FRAGMENTS = (".env", "id_rsa", "credentials", "token", "secret")


def persist_runtime_evidence(
    run: dict[str, Any],
    store_dir: str | Path,
    *,
    artifact_base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Persist a runtime run as a replayable evidence bundle."""

    return RuntimeEvidenceStore(store_dir).persist_run(run, artifact_base_dir=artifact_base_dir)


def validate_runtime_evidence_bundle(bundle_path: str | Path) -> dict[str, Any]:
    """Validate a persisted runtime evidence bundle and its artifacts."""

    bundle_file = _resolve_bundle_path(bundle_path)
    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {
        "bundle_file_exists": bundle_file.exists(),
        "bundle_json_parse": False,
        "bundle_schema_matches": False,
        "required_bundle_files_present": False,
        "bundle_file_hashes_match": False,
        "runtime_run_schema_matches": False,
        "trace_schema_matches": False,
        "artifact_manifest_schema_matches": False,
        "acceptance_checklist_schema_matches": False,
        "acceptance_requires_review": False,
        "artifact_count_matches": False,
        "artifact_files_exist": False,
        "artifact_file_sizes_match": False,
        "artifact_file_hashes_match": False,
        "artifact_manifest_hashes_match": False,
        "replay_trace_available": False,
        "no_promotion_decision_leak": False,
    }
    if not checks["bundle_file_exists"]:
        issues.append(_issue("error", "bundle_file_missing", "Runtime evidence bundle file does not exist.", path=str(bundle_file)))
        return _build_report(bundle_file=bundle_file, bundle=None, checks=checks, issues=issues)

    bundle = _read_json_object(bundle_file, issues, parse_code="bundle_json_invalid")
    checks["bundle_json_parse"] = bundle is not None
    if bundle is None:
        return _build_report(bundle_file=bundle_file, bundle=None, checks=checks, issues=issues)

    checks["bundle_schema_matches"] = bundle.get("schema") == RUNTIME_EVIDENCE_BUNDLE_SCHEMA
    if not checks["bundle_schema_matches"]:
        issues.append(
            _issue(
                "error",
                "bundle_schema_mismatch",
                "Runtime evidence bundle schema is invalid.",
                expected=RUNTIME_EVIDENCE_BUNDLE_SCHEMA,
                actual=bundle.get("schema"),
            )
        )

    loaded_files = _load_bundle_files(bundle, issues)
    checks["required_bundle_files_present"] = set(REQUIRED_BUNDLE_FILES) <= set(loaded_files)
    checks["bundle_file_hashes_match"] = _bundle_file_hashes_match(bundle, loaded_files, issues)
    for name, expected_schema in REQUIRED_BUNDLE_FILES.items():
        payload = loaded_files.get(name)
        checks[f"{name}_schema_matches"] = bool(payload and payload.get("schema") == expected_schema)
        if not checks[f"{name}_schema_matches"]:
            issues.append(
                _issue(
                    "error",
                    "runtime_evidence_file_schema_mismatch",
                    "Runtime evidence file schema is invalid.",
                    file_key=name,
                    expected=expected_schema,
                    actual=payload.get("schema") if isinstance(payload, dict) else None,
                )
            )

    acceptance = _acceptance_payload(loaded_files.get("acceptance_checklist"))
    checks["acceptance_requires_review"] = acceptance.get("requires_review") is True
    if not checks["acceptance_requires_review"]:
        issues.append(_issue("error", "acceptance_review_not_required", "Runtime evidence must require review."))

    checks["artifact_count_matches"] = _artifact_count_matches(bundle, loaded_files.get("artifact_manifest"), issues)
    artifact_checks = _validate_artifacts(bundle, loaded_files.get("artifact_manifest"), issues)
    checks.update(artifact_checks)

    checks["replay_trace_available"] = _replay_trace_available(bundle, loaded_files, issues)
    leaks = _promotion_leaks({"bundle": bundle, "evidence_files": loaded_files})
    checks["no_promotion_decision_leak"] = not leaks
    if leaks:
        issues.append(
            _issue(
                "error",
                "runtime_evidence_promotion_leak",
                "Runtime evidence bundles must not contain promotion decisions or ledger records.",
                leaks=leaks,
            )
        )

    return _build_report(bundle_file=bundle_file, bundle=bundle, checks=checks, issues=issues)


def replay_runtime_evidence_bundle(bundle_path: str | Path) -> dict[str, Any]:
    """Replay persisted runtime evidence without an in-memory RuntimeEngine."""

    bundle_file = _resolve_bundle_path(bundle_path)
    issues: list[dict[str, Any]] = []
    bundle = _read_json_object(bundle_file, issues, parse_code="bundle_json_invalid") if bundle_file.exists() else None
    if bundle is None:
        return {
            "schema": RUNTIME_EVIDENCE_REPLAY_SCHEMA,
            "status": "blocked",
            "bundle_path": str(bundle_file),
            "run_id": None,
            "replayable": False,
            "trace_length": 0,
            "trace": [],
            "artifact_manifest": {},
            "acceptance_checklist": {},
            "artifacts": [],
            "issues": issues
            or [_issue("error", "bundle_file_missing", "Runtime evidence bundle file does not exist.", path=str(bundle_file))],
        }

    loaded_files = _load_bundle_files(bundle, issues)
    trace_payload = loaded_files.get("trace", {})
    acceptance_payload = _acceptance_payload(loaded_files.get("acceptance_checklist"))
    trace = trace_payload.get("trace", [])
    replayable = not issues and isinstance(trace, list) and bool(trace)
    return {
        "schema": RUNTIME_EVIDENCE_REPLAY_SCHEMA,
        "status": "passed" if replayable else "blocked",
        "bundle_path": str(bundle_file),
        "run_id": bundle.get("run_id"),
        "replayable": replayable,
        "trace_length": len(trace) if isinstance(trace, list) else 0,
        "trace": trace if isinstance(trace, list) else [],
        "artifact_manifest": loaded_files.get("artifact_manifest", {}),
        "acceptance_checklist": acceptance_payload,
        "artifacts": bundle.get("artifacts", []),
        "issues": issues,
    }


class RuntimeEvidenceStore:
    """Write and validate runtime evidence bundles on disk."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def persist_run(
        self,
        run: dict[str, Any],
        *,
        artifact_base_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        if not isinstance(run, dict):
            raise TypeError("runtime run must be a mapping.")
        run_id = str(run.get("run_id", "")).strip()
        if not run_id:
            raise ValueError("runtime run requires run_id.")

        run_dir = self.root / _safe_name(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        trace_payload = {
            "schema": RUNTIME_TRACE_SCHEMA,
            "run_id": run_id,
            "trace_length": len(run.get("trace", [])) if isinstance(run.get("trace"), list) else 0,
            "trace": list(run.get("trace", [])) if isinstance(run.get("trace"), list) else [],
            "timestamp": _utc_now(),
        }
        artifact_manifest = dict(run.get("artifact_manifest", {}))
        acceptance_payload = {
            "schema": RUNTIME_ACCEPTANCE_SCHEMA,
            "run_id": run_id,
            "acceptance_checklist": dict(run.get("acceptance_checklist", {})),
            "timestamp": _utc_now(),
        }

        written = {
            "runtime_run": _write_json(run_dir / "runtime-run.json", run),
            "trace": _write_json(run_dir / "trace.json", trace_payload),
            "artifact_manifest": _write_json(run_dir / "artifact-manifest.json", artifact_manifest),
            "acceptance_checklist": _write_json(run_dir / "acceptance-checklist.json", acceptance_payload),
        }
        artifact_evidence = _build_artifact_evidence(
            artifact_manifest,
            artifact_base_dir=Path(artifact_base_dir).resolve() if artifact_base_dir is not None else None,
            bundle_artifact_dir=run_dir / "artifacts",
        )
        bundle = {
            "schema": RUNTIME_EVIDENCE_BUNDLE_SCHEMA,
            "status": "recorded",
            "run_id": run_id,
            "engine_id": run.get("engine_id"),
            "store_root": str(self.root),
            "run_dir": str(run_dir),
            "artifact_base_dir": str(Path(artifact_base_dir).resolve()) if artifact_base_dir is not None else None,
            "files": {name: _file_record(path) for name, path in written.items()},
            "artifacts": artifact_evidence,
            "replay": {
                "replayable": True,
                "trace_length": trace_payload["trace_length"],
                "trace_path": str(written["trace"]),
            },
            "timestamp": _utc_now(),
        }
        bundle_path = run_dir / "evidence-bundle.json"
        _write_json(bundle_path, bundle)
        bundle["bundle_path"] = str(bundle_path.resolve())
        _write_json(bundle_path, bundle)
        return bundle

    def load_bundle(self, run_id: str) -> dict[str, Any]:
        return _read_json_object(self.root / _safe_name(run_id) / "evidence-bundle.json", [])


def _resolve_bundle_path(bundle_path: str | Path) -> Path:
    path = Path(bundle_path).resolve()
    if path.is_dir():
        return path / "evidence-bundle.json"
    return path


def _build_artifact_evidence(
    artifact_manifest: dict[str, Any],
    *,
    artifact_base_dir: Path | None,
    bundle_artifact_dir: Path,
) -> list[dict[str, Any]]:
    artifacts = artifact_manifest.get("artifacts", [])
    if not isinstance(artifacts, list):
        return []
    evidence = []
    bundle_artifact_dir.mkdir(parents=True, exist_ok=True)
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, dict):
            continue
        raw_path = str(artifact.get("path", "")).strip()
        resolved = _resolve_artifact_path(raw_path, artifact_base_dir)
        exists = resolved.exists() and resolved.is_file()
        bundled_path = None
        bundled_exists = False
        size_bytes = None
        content_hash = None
        if exists:
            bundled_path = bundle_artifact_dir / _artifact_bundle_name(index, artifact, resolved)
            _copy_file(resolved, bundled_path)
            bundled_exists = bundled_path.exists() and bundled_path.is_file()
            size_bytes = bundled_path.stat().st_size if bundled_exists else None
            content_hash = _sha256_file(bundled_path) if bundled_exists else None
        evidence.append(
            {
                "artifact_id": artifact.get("artifact_id"),
                "kind": artifact.get("kind"),
                "path": raw_path,
                "source_path": raw_path,
                "resolved_source_path": str(resolved),
                "bundle_path": str(bundled_path.resolve()) if bundled_path is not None else None,
                "source_exists": exists,
                "bundled_exists": bundled_exists,
                "exists": bundled_exists,
                "size_bytes": size_bytes,
                "content_hash": content_hash,
                "manifest_content_hash": artifact.get("content_hash"),
            }
        )
    return evidence


def _resolve_artifact_path(raw_path: str, artifact_base_dir: Path | None) -> Path:
    path = Path(raw_path)
    _reject_parent_directory_refs(path)
    if artifact_base_dir is not None:
        return _resolve_artifact_path_with_base(path, artifact_base_dir)
    if path.is_absolute():
        raise ValueError("Absolute artifact paths require artifact_base_dir for safe persistence.")
    candidate = Path.cwd() / path
    return _ensure_artifact_path_is_safe(candidate, artifact_base_dir=None)


def _resolve_artifact_path_with_base(path: Path, artifact_base_dir: Path) -> Path:
    if path.is_absolute():
        candidate = path
    else:
        candidate = artifact_base_dir / path
    return _ensure_artifact_path_is_safe(candidate, artifact_base_dir=artifact_base_dir)


def _ensure_artifact_path_is_safe(path: Path, artifact_base_dir: Path | None) -> Path:
    if _contains_sensitive_artifact_name(path):
        raise ValueError(f"Artifact filename contains sensitive token: {path.name}")
    if _path_contains_symlink(path):
        raise ValueError(f"Artifact path must not use symlinks: {path}")
    resolved = path.resolve()
    if artifact_base_dir is not None and not _is_within_artifact_base(resolved, artifact_base_dir):
        raise ValueError(f"Artifact path must stay within artifact_base_dir: {resolved}")
    return resolved


def _reject_parent_directory_refs(path: Path) -> None:
    if any(part == ".." for part in path.parts):
        raise ValueError(
            f"Artifact path must not contain parent directory references or escape artifact_base_dir: {path}"
        )


def _is_within_artifact_base(candidate: Path, artifact_base_dir: Path) -> bool:
    candidate_path = os.path.normpath(str(candidate)).casefold()
    base_path = os.path.normpath(str(artifact_base_dir)).casefold()
    return candidate_path == base_path or candidate_path.startswith(f"{base_path}{os.sep}")


def _contains_sensitive_artifact_name(path: Path) -> bool:
    filename = path.name.lower()
    return any(fragment in filename for fragment in SENSITIVE_ARTIFACT_NAME_FRAGMENTS)


def _path_contains_symlink(path: Path) -> bool:
    current = path
    while True:
        if current.is_symlink():
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def _load_bundle_files(bundle: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    files = bundle.get("files", {})
    if not isinstance(files, dict):
        issues.append(_issue("error", "bundle_files_missing", "Runtime evidence bundle requires a files mapping."))
        return loaded
    for name in REQUIRED_BUNDLE_FILES:
        record = files.get(name)
        path = Path(str(record.get("path", ""))).resolve() if isinstance(record, dict) else None
        if path is None or not path.exists():
            issues.append(
                _issue(
                    "error",
                    "runtime_evidence_file_missing",
                    "Required runtime evidence file is missing.",
                    file_key=name,
                    path=str(path) if path is not None else None,
                )
            )
            continue
        payload = _read_json_object(path, issues, parse_code="runtime_evidence_file_json_invalid", file_key=name)
        if payload is not None:
            loaded[name] = payload
    return loaded


def _bundle_file_hashes_match(
    bundle: dict[str, Any],
    loaded_files: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> bool:
    files = bundle.get("files", {})
    if not isinstance(files, dict):
        return False
    matched = True
    for name in REQUIRED_BUNDLE_FILES:
        if name not in loaded_files:
            matched = False
            continue
        record = files.get(name)
        path = Path(str(record.get("path", ""))).resolve() if isinstance(record, dict) else None
        expected_hash = record.get("sha256") if isinstance(record, dict) else None
        expected_size = record.get("size_bytes") if isinstance(record, dict) else None
        actual_hash = _sha256_file(path) if path and path.exists() else None
        actual_size = path.stat().st_size if path and path.exists() else None
        if actual_hash != expected_hash or actual_size != expected_size:
            matched = False
            issues.append(
                _issue(
                    "error",
                    "runtime_evidence_file_hash_mismatch",
                    "Runtime evidence file hash or size does not match the persisted bundle record.",
                    file_key=name,
                    expected_hash=expected_hash,
                    actual_hash=actual_hash,
                    expected_size=expected_size,
                    actual_size=actual_size,
                )
            )
    return matched


def _artifact_count_matches(
    bundle: dict[str, Any],
    manifest: dict[str, Any] | None,
    issues: list[dict[str, Any]],
) -> bool:
    artifacts = bundle.get("artifacts", [])
    manifest_count = manifest.get("artifact_count") if isinstance(manifest, dict) else None
    matched = isinstance(artifacts, list) and manifest_count == len(artifacts)
    if not matched:
        issues.append(
            _issue(
                "error",
                "artifact_count_mismatch",
                "Persisted artifact evidence count must match the artifact manifest.",
                expected=manifest_count,
                actual=len(artifacts) if isinstance(artifacts, list) else None,
            )
        )
    return matched


def _validate_artifacts(
    bundle: dict[str, Any],
    manifest: dict[str, Any] | None,
    issues: list[dict[str, Any]],
) -> dict[str, bool]:
    artifacts = bundle.get("artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        issues.append(_issue("error", "artifact_evidence_missing", "Runtime evidence bundle requires artifact evidence."))
        return {
            "artifact_files_exist": False,
            "artifact_file_sizes_match": False,
            "artifact_file_hashes_match": False,
            "artifact_manifest_hashes_match": False,
        }
    manifest_artifacts: dict[str, dict[str, Any]] = {}
    if isinstance(manifest, dict) and isinstance(manifest.get("artifacts"), list):
        for item in manifest["artifacts"]:
            if isinstance(item, dict):
                manifest_artifacts[str(item.get("artifact_id"))] = item
    files_exist = True
    sizes_match = True
    hashes_match = True
    manifest_hashes_match = True
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            files_exist = sizes_match = hashes_match = manifest_hashes_match = False
            continue
        manifest_artifact = manifest_artifacts.get(str(artifact.get("artifact_id")))
        if manifest_artifact is None:
            manifest_hashes_match = False
            issues.append(
                _issue(
                    "error",
                    "artifact_manifest_record_missing",
                    "Runtime artifact evidence must map to an artifact manifest record.",
                    artifact_id=artifact.get("artifact_id"),
                )
            )
        elif manifest_artifact.get("content_hash") != artifact.get("manifest_content_hash"):
            manifest_hashes_match = False
            issues.append(
                _issue(
                    "error",
                    "artifact_manifest_hash_mismatch",
                    "Runtime artifact manifest hash changed after evidence persistence.",
                    artifact_id=artifact.get("artifact_id"),
                    expected=artifact.get("manifest_content_hash"),
                    actual=manifest_artifact.get("content_hash"),
                )
            )
        artifact_path = artifact.get("bundle_path") or artifact.get("resolved_path") or artifact.get("resolved_source_path")
        path = Path(str(artifact_path or "")).resolve()
        exists = path.exists() and path.is_file()
        if not exists:
            files_exist = False
            issues.append(
                _issue(
                    "error",
                    "artifact_file_missing",
                    "Runtime artifact file is missing.",
                    artifact_id=artifact.get("artifact_id"),
                    path=str(path),
                )
            )
            continue
        actual_size = path.stat().st_size
        actual_hash = _sha256_file(path)
        if actual_size != artifact.get("size_bytes"):
            sizes_match = False
            issues.append(
                _issue(
                    "error",
                    "artifact_size_mismatch",
                    "Runtime artifact file size changed after evidence persistence.",
                    artifact_id=artifact.get("artifact_id"),
                    expected=artifact.get("size_bytes"),
                    actual=actual_size,
                )
            )
        if actual_hash != artifact.get("content_hash"):
            hashes_match = False
            issues.append(
                _issue(
                    "error",
                    "artifact_hash_mismatch",
                    "Runtime artifact file hash changed after evidence persistence.",
                    artifact_id=artifact.get("artifact_id"),
                    expected=artifact.get("content_hash"),
                    actual=actual_hash,
                )
            )
    return {
        "artifact_files_exist": files_exist,
        "artifact_file_sizes_match": sizes_match,
        "artifact_file_hashes_match": hashes_match,
        "artifact_manifest_hashes_match": manifest_hashes_match,
    }


def _replay_trace_available(
    bundle: dict[str, Any],
    loaded_files: dict[str, dict[str, Any]],
    issues: list[dict[str, Any]],
) -> bool:
    trace_payload = loaded_files.get("trace", {})
    runtime_payload = loaded_files.get("runtime_run", {})
    trace = trace_payload.get("trace")
    runtime_trace = runtime_payload.get("trace")
    replay = bundle.get("replay", {})
    trace_length = len(trace) if isinstance(trace, list) else None
    expected_length = replay.get("trace_length") if isinstance(replay, dict) else None
    available = (
        isinstance(trace, list)
        and bool(trace)
        and isinstance(runtime_trace, list)
        and trace == runtime_trace
        and trace_length == expected_length
    )
    if not available:
        issues.append(
            _issue(
                "error",
                "runtime_replay_trace_unavailable",
                "Persisted trace must match the runtime run and bundle replay metadata.",
                expected_length=expected_length,
                actual_length=trace_length,
            )
        )
    return available


def _acceptance_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    acceptance = payload.get("acceptance_checklist", {})
    return acceptance if isinstance(acceptance, dict) else {}


def _read_json_object(path: Path, issues: list[dict[str, Any]], *, parse_code: str = "json_invalid", **extra: Any) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(_issue("error", parse_code, "JSON file could not be parsed.", path=str(path), error=str(exc), **extra))
        return None
    if not isinstance(payload, dict):
        issues.append(
            _issue(
                "error",
                parse_code,
                "JSON file must contain an object.",
                path=str(path),
                actual_type=type(payload).__name__,
                **extra,
            )
        )
        return None
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(path)
    return path.resolve()


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".tmp")
    with source.open("rb") as reader, temp_path.open("wb") as writer:
        for chunk in iter(lambda: reader.read(1024 * 1024), b""):
            writer.write(chunk)
    temp_path.replace(destination)


def _artifact_bundle_name(index: int, artifact: dict[str, Any], source: Path) -> str:
    artifact_id = str(artifact.get("artifact_id") or f"artifact-{index:04d}")
    stem = _safe_name(artifact_id)
    suffix = source.suffix if source.suffix else ".artifact"
    return f"{index:04d}_{stem}{suffix}"


def _file_record(path: Path) -> dict[str, Any]:
    path = path.resolve()
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


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


def _safe_name(raw: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", raw).strip("_") or "runtime-run"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_report(
    *,
    bundle_file: Path,
    bundle: dict[str, Any] | None,
    checks: dict[str, bool],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = sum(1 for value in checks.values() if value is not True)
    artifacts = bundle.get("artifacts", []) if isinstance(bundle, dict) else []
    return {
        "schema": RUNTIME_EVIDENCE_VALIDATION_SCHEMA,
        "status": _status_from_issues(issues),
        "bundle_path": str(bundle_file),
        "run_id": bundle.get("run_id") if isinstance(bundle, dict) else None,
        "summary": {
            "total": len(checks),
            "passed": len(checks) - failed,
            "failed": failed,
            "blocked": sum(1 for issue in issues if issue["severity"] == "error"),
            "review_required": sum(1 for issue in issues if issue["severity"] == "warning"),
            "artifact_count": len(artifacts) if isinstance(artifacts, list) else 0,
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
    "RUNTIME_EVIDENCE_BUNDLE_SCHEMA",
    "RUNTIME_EVIDENCE_REPLAY_SCHEMA",
    "RUNTIME_EVIDENCE_VALIDATION_SCHEMA",
    "RuntimeEvidenceStore",
    "persist_runtime_evidence",
    "replay_runtime_evidence_bundle",
    "validate_runtime_evidence_bundle",
]
