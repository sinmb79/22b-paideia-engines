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
    ) -> dict[str, Any]:
        record = self.get_source(source_id)
        path = Path(local_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Acquired source path does not exist: {path}")
        if not approved_by.strip():
            raise ValueError("approved_by is required.")

        license_note = Path(license_note_path).resolve() if license_note_path else None
        needs_license_note = record.license_tier in {
            "restricted_publisher_license",
            "login_or_agreement_required",
            "public_reference_with_site_terms",
        }
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
            "engine_uses": list(record.engine_uses),
        }
        if manifest_path is not None:
            self.append_manifest(manifest_path, acquired)
        return acquired

    @staticmethod
    def hash_path(path: Path) -> str:
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


__all__ = ["DataAcquisitionEngine"]
