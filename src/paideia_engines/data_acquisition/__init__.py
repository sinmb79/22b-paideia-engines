"""Data acquisition engine with license gates and manifest records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from paideia_engines.data_catalog import DatasetRecord


class DataAcquisitionEngine:
    """Plan and register education datasets without bypassing license rules."""

    plan_schema = "paideia-data-acquisition-plan/v1"
    acquired_schema = "paideia-acquired-source/v1"
    validation_schema = "paideia-acquisition-validation-report/v1"
    source_validation_schema = "paideia-acquired-source-validation/v1"
    license_note_required_tiers = {
        "restricted_publisher_license",
        "login_or_agreement_required",
        "public_reference_with_site_terms",
    }

    def __init__(self, records: Iterable[DatasetRecord], *, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.records = {record.source_id: record for record in records}

    def get_source(self, source_id: str) -> DatasetRecord:
        try:
            return self.records[source_id]
        except KeyError as exc:
            raise KeyError(f"Unknown data source: {source_id}") from exc

    def evaluate_source(self, source_id: str) -> dict[str, Any]:
        record = self.get_source(source_id)
        if record.license_tier == "restricted_publisher_license":
            decision = "blocked"
            reason = "Manual publisher license or written permission is required before acquisition."
        elif record.license_tier in {"login_or_agreement_required", "public_reference_with_site_terms"}:
            decision = "review_required"
            reason = "Terms, account access, or source-specific use conditions must be reviewed first."
        else:
            decision = "allowed"
            reason = "Official public source metadata is safe to reference; preserve provider attribution."

        return {
            "schema": "paideia-data-source-decision/v1",
            "source_id": record.source_id,
            "title": record.title,
            "provider": record.provider,
            "source_url": record.source_url,
            "license_tier": record.license_tier,
            "acquisition_mode": record.acquisition_mode,
            "auto_download": record.auto_download,
            "decision": decision,
            "reason": reason,
            "engine_uses": list(record.engine_uses),
        }

    def build_engine_plan(self, engine_name: str) -> dict[str, Any]:
        engine = engine_name.strip().lower()
        sources = [
            self.evaluate_source(record.source_id)
            for record in self.records.values()
            if engine in record.engine_uses
        ]
        return {
            "schema": self.plan_schema,
            "engine": engine,
            "storage_root": str(self.storage_root),
            "sources": sources,
            "summary": {
                "total_sources": len(sources),
                "allowed": sum(1 for item in sources if item["decision"] == "allowed"),
                "review_required": sum(1 for item in sources if item["decision"] == "review_required"),
                "blocked": sum(1 for item in sources if item["decision"] == "blocked"),
            },
        }

    def register_acquired_source(
        self,
        source_id: str,
        *,
        local_path: str | Path,
        approved_by: str,
        license_note_path: str | Path | None = None,
        manifest_path: str | Path | None = None,
        content_scope: str = "public_content",
    ) -> dict[str, Any]:
        record = self.get_source(source_id)
        path = Path(local_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Acquired source path does not exist: {path}")
        if not approved_by.strip():
            raise ValueError("approved_by is required.")

        license_note = Path(license_note_path).resolve() if license_note_path else None
        normalized_scope = content_scope.strip().lower() or "public_content"
        needs_license_note = (
            record.license_tier in self.license_note_required_tiers
            and normalized_scope != "metadata_only"
        )
        if needs_license_note and (license_note is None or not license_note.exists()):
            raise PermissionError(
                f"{source_id} requires a license or terms-review note before acquisition."
            )

        acquired = {
            "schema": self.acquired_schema,
            "source_id": record.source_id,
            "title": record.title,
            "provider": record.provider,
            "source_url": record.source_url,
            "license_tier": record.license_tier,
            "acquisition_mode": record.acquisition_mode,
            "status": "acquired",
            "local_path": str(path),
            "hash": self.hash_path(path),
            "license_note_path": str(license_note) if license_note else None,
            "approved_by": approved_by,
            "content_scope": normalized_scope,
            "engine_uses": list(record.engine_uses),
        }
        if manifest_path is not None:
            self.append_manifest(manifest_path, acquired)
        return acquired

    @staticmethod
    def load_manifest(manifest_path: str | Path) -> list[dict[str, Any]]:
        path = Path(manifest_path)
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    item = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL manifest line {line_number}: {path}") from exc
                if not isinstance(item, dict):
                    raise TypeError(f"Manifest line {line_number} must be a mapping.")
                records.append(item)
        return records

    def validate_manifest(self, manifest_path: str | Path) -> dict[str, Any]:
        path = Path(manifest_path)
        records = self.load_manifest(path)
        report = self.validate_acquired_sources(records, base_dir=path.parent)
        report["manifest_path"] = str(path.resolve())
        return report

    def validate_acquired_sources(
        self,
        records: Iterable[dict[str, Any]],
        *,
        base_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        records_list = list(records)
        if not records_list:
            return {
                "schema": self.validation_schema,
                "status": "review_required",
                "summary": {
                    "validated": 0,
                    "passed": 0,
                    "review_required": 1,
                    "blocked": 0,
                },
                "issues": [
                    self._issue(
                        "unknown_source",
                        "no_sources_to_validate",
                        "At least one acquired source is required for validation.",
                    )
                ],
                "validations": [],
            }

        validations = [
            self.validate_acquired_source(record, base_dir=base_dir)
            for record in records_list
        ]
        issues = [
            issue
            for validation in validations
            for issue in validation["issues"]
        ]
        blocked = sum(1 for validation in validations if validation["status"] == "blocked")
        review_required = sum(
            1 for validation in validations if validation["status"] == "review_required"
        )
        passed = sum(1 for validation in validations if validation["status"] == "passed")
        status = "blocked" if blocked else "review_required" if review_required else "passed"
        return {
            "schema": self.validation_schema,
            "status": status,
            "summary": {
                "validated": len(validations),
                "passed": passed,
                "review_required": review_required,
                "blocked": blocked,
            },
            "issues": issues,
            "validations": validations,
        }

    def validate_acquired_source(
        self,
        acquired: dict[str, Any],
        *,
        base_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        if not isinstance(acquired, dict):
            raise TypeError("acquired source must be a mapping.")

        source_id = str(acquired.get("source_id", "")).strip()
        issues: list[dict[str, Any]] = []
        record: DatasetRecord | None = None
        if source_id:
            try:
                record = self.get_source(source_id)
            except KeyError:
                issues.append(self._issue(source_id, "unknown_source", "Source id is not in the catalog."))
        else:
            issues.append(self._issue("unknown_source", "source_id_required", "source_id is required."))

        path = self._validate_local_path(acquired, source_id, issues, base_dir=base_dir)
        self._validate_status(acquired, source_id, issues)
        self._validate_hash(acquired, path, source_id, issues)
        self._validate_approval(acquired, source_id, issues)
        self._validate_license_note(acquired, record, source_id, issues, base_dir=base_dir)

        blocked_codes = {
            "unknown_source",
            "source_id_required",
            "status_not_acquired",
            "local_path_required",
            "local_path_missing",
            "hash_required",
            "hash_mismatch",
            "approved_by_required",
            "license_note_required",
            "license_note_missing",
        }
        status = "blocked" if any(issue["code"] in blocked_codes for issue in issues) else "passed"
        return {
            "schema": self.source_validation_schema,
            "source_id": source_id or "unknown_source",
            "status": status,
            "content_scope": str(acquired.get("content_scope", "public_content")).lower(),
            "local_path": str(path) if path is not None else str(acquired.get("local_path", "")),
            "provider": record.provider if record else None,
            "source_url": record.source_url if record else None,
            "license_tier": record.license_tier if record else None,
            "acquisition_mode": record.acquisition_mode if record else None,
            "engine_uses": list(record.engine_uses) if record else [],
            "issues": issues,
        }

    @staticmethod
    def hash_path(path: str | Path) -> str:
        path = Path(path)
        if path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            return f"sha256:{digest}"
        if path.is_dir():
            digest = hashlib.sha256()
            for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
                digest.update(str(file_path.relative_to(path)).replace("\\", "/").encode("utf-8"))
                digest.update(b"\0")
                digest.update(file_path.read_bytes())
                digest.update(b"\0")
            return f"sha256-tree:{digest.hexdigest()}"
        raise FileNotFoundError(path)

    @staticmethod
    def append_manifest(manifest_path: str | Path, acquired: dict[str, Any]) -> None:
        path = Path(manifest_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as file:
            file.write(json.dumps(acquired, ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def _issue(source_id: str, code: str, message: str) -> dict[str, str]:
        return {
            "source_id": source_id or "unknown_source",
            "code": code,
            "message": message,
        }

    def _validate_local_path(
        self,
        acquired: dict[str, Any],
        source_id: str,
        issues: list[dict[str, Any]],
        *,
        base_dir: str | Path | None = None,
    ) -> Path | None:
        raw_path = str(acquired.get("local_path", "")).strip()
        if not raw_path:
            issues.append(self._issue(source_id, "local_path_required", "local_path is required."))
            return None
        path = Path(raw_path)
        if base_dir is not None and not path.is_absolute():
            path = Path(base_dir) / path
        if not path.exists():
            issues.append(self._issue(source_id, "local_path_missing", "local_path does not exist."))
            return None
        return path.resolve()

    def _validate_status(
        self,
        acquired: dict[str, Any],
        source_id: str,
        issues: list[dict[str, Any]],
    ) -> None:
        status = str(acquired.get("status", "")).strip().lower()
        if status != "acquired":
            issues.append(self._issue(source_id, "status_not_acquired", "status must be acquired."))

    def _validate_hash(
        self,
        acquired: dict[str, Any],
        path: Path | None,
        source_id: str,
        issues: list[dict[str, Any]],
    ) -> None:
        expected_hash = str(acquired.get("hash", "")).strip()
        if not expected_hash:
            issues.append(self._issue(source_id, "hash_required", "hash is required."))
            return
        if path is None:
            return
        actual_hash = self.hash_path(path)
        if actual_hash != expected_hash:
            issues.append(self._issue(source_id, "hash_mismatch", "hash does not match local_path."))

    def _validate_approval(
        self,
        acquired: dict[str, Any],
        source_id: str,
        issues: list[dict[str, Any]],
    ) -> None:
        approved_by = str(acquired.get("approved_by", "")).strip()
        if not approved_by:
            issues.append(self._issue(source_id, "approved_by_required", "approved_by is required."))

    def _validate_license_note(
        self,
        acquired: dict[str, Any],
        record: DatasetRecord | None,
        source_id: str,
        issues: list[dict[str, Any]],
        *,
        base_dir: str | Path | None = None,
    ) -> None:
        if record is None:
            return
        content_scope = str(acquired.get("content_scope", "public_content")).lower()
        if record.license_tier not in self.license_note_required_tiers or content_scope == "metadata_only":
            return
        raw_note = str(acquired.get("license_note_path") or "").strip()
        if not raw_note:
            issues.append(
                self._issue(source_id, "license_note_required", "license_note_path is required.")
            )
            return
        note_path = Path(raw_note)
        if base_dir is not None and not note_path.is_absolute():
            note_path = Path(base_dir) / note_path
        if not note_path.exists():
            issues.append(self._issue(source_id, "license_note_missing", "license note path is missing."))


from paideia_engines.data_acquisition.source_diagnostics import (
    diagnose_source_file,
    diagnose_source_fixture_pack,
)
from paideia_engines.data_acquisition.manifest_diagnostics import diagnose_acquired_source_manifest
from paideia_engines.data_acquisition.adapter_certification import (
    certify_adapter_matrix,
    certify_adapters,
)


__all__ = [
    "DataAcquisitionEngine",
    "certify_adapter_matrix",
    "certify_adapters",
    "diagnose_acquired_source_manifest",
    "diagnose_source_file",
    "diagnose_source_fixture_pack",
]
