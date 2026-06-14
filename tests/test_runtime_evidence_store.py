import json
from pathlib import Path

import pytest

from paideia_engines.runtime import (
    RuntimeEngine,
    persist_runtime_evidence,
    replay_runtime_evidence_bundle,
    validate_runtime_evidence_bundle,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _issue_codes(report: dict[str, object]) -> set[str]:
    return {str(issue["code"]) for issue in report["issues"]}


def _runtime_run(tmp_path: Path) -> dict[str, object]:
    artifact_path = tmp_path / "artifacts" / "evidence.json"
    _write_json(
        artifact_path,
        {
            "schema": "test-artifact/v1",
            "summary": "local evidence",
            "contains_private_data": False,
        },
    )
    return RuntimeEngine(engine_id="runtime:persistent").run_task(
        agent_id="agent:runtime",
        task="prepare persistent evidence",
        tools=["read_file", "write_report"],
        artifacts=[{"path": "artifacts/evidence.json", "kind": "evidence"}],
    )


def _runtime_run_with_artifact_path(tmp_path: Path, artifact_path: str) -> dict[str, object]:
    artifact_file = Path(artifact_path)
    artifact_file.parent.mkdir(parents=True, exist_ok=True)
    artifact_file.write_text(
        json.dumps({"schema": "test-artifact/v1", "summary": "local evidence", "contains_private_data": False}),
        encoding="utf-8",
    )
    return RuntimeEngine(engine_id="runtime:persistent").run_task(
        agent_id="agent:runtime",
        task="prepare persistent evidence",
        tools=["read_file", "write_report"],
        artifacts=[{"path": artifact_path, "kind": "evidence"}],
    )


def test_runtime_evidence_store_persists_validates_and_replays_after_source_artifact_is_removed(tmp_path):
    run = _runtime_run(tmp_path)

    bundle = persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=tmp_path)
    source_path = tmp_path / "artifacts" / "evidence.json"
    source_path.unlink()

    report = validate_runtime_evidence_bundle(bundle["bundle_path"])
    replay = replay_runtime_evidence_bundle(bundle["bundle_path"])

    assert bundle["schema"] == "paideia-runtime-evidence-bundle/v1"
    assert bundle["artifacts"][0]["source_exists"] is True
    assert bundle["artifacts"][0]["bundled_exists"] is True
    assert report["schema"] == "paideia-runtime-evidence-validation/v1"
    assert report["status"] == "passed"
    assert report["summary"]["artifact_count"] == 1
    assert replay["schema"] == "paideia-runtime-evidence-replay/v1"
    assert replay["status"] == "passed"
    assert replay["run_id"] == run["run_id"]
    assert replay["trace_length"] == len(run["trace"])


def test_runtime_evidence_store_rejects_absolute_artifact_paths_without_artifact_base(tmp_path):
    absolute_artifact = tmp_path / "outside-store" / "evidence.json"
    absolute_artifact.parent.mkdir(parents=True, exist_ok=True)
    absolute_artifact.write_text('{"schema": "test-artifact/v1", "summary": "outside"}', encoding="utf-8")
    run = _runtime_run_with_artifact_path(tmp_path, str(absolute_artifact))

    with pytest.raises(ValueError, match="artifact_base_dir"):
        persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=None)


def test_runtime_evidence_store_rejects_relative_parent_artifact_without_artifact_base(tmp_path):
    run = RuntimeEngine(engine_id="runtime:persistent").run_task(
        agent_id="agent:runtime",
        task="prepare persistent evidence",
        tools=["read_file", "write_report"],
        artifacts=[{"path": "../outside.json", "kind": "evidence"}],
    )

    with pytest.raises(ValueError, match="parent directory"):
        persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=None)


def test_runtime_evidence_store_accepts_absolute_artifact_path_within_base_dir(tmp_path):
    artifact_base_dir = tmp_path / "artifacts"
    absolute_artifact = artifact_base_dir / "trusted" / "evidence.json"
    run = _runtime_run_with_artifact_path(tmp_path, str(absolute_artifact))

    bundle = persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=artifact_base_dir)

    assert bundle["schema"] == "paideia-runtime-evidence-bundle/v1"
    assert bundle["artifacts"][0]["source_exists"] is True


def test_runtime_evidence_store_rejects_relative_artifact_path_that_escapes_artifact_base(tmp_path):
    artifact_base_dir = tmp_path / "artifacts"
    escaped_artifact = artifact_base_dir / "inner" / "evidence.json"
    run = _runtime_run_with_artifact_path(tmp_path, str(escaped_artifact))
    artifact = escaped_artifact.parent.parent / "../secrets" / "evidence.json"

    run["artifact_manifest"]["artifacts"][0]["path"] = str(artifact)

    with pytest.raises(ValueError, match="artifact_base_dir"):
        persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=artifact_base_dir)


def test_runtime_evidence_store_rejects_symlink_artifacts(tmp_path):
    artifact_base_dir = tmp_path / "artifacts"
    target = artifact_base_dir / "real-evidence.json"
    artifact_base_dir.mkdir(parents=True, exist_ok=True)
    target.write_text('{"schema": "test-artifact/v1", "summary": "real"}', encoding="utf-8")
    symlink_artifact = artifact_base_dir / "link.json"
    try:
        symlink_artifact.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable in this environment: {exc}")

    run = RuntimeEngine(engine_id="runtime:persistent").run_task(
        agent_id="agent:runtime",
        task="prepare persistent evidence",
        tools=["read_file", "write_report"],
        artifacts=[{"path": str(symlink_artifact), "kind": "evidence"}],
    )

    with pytest.raises(ValueError, match="symlink"):
        persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=artifact_base_dir)


def test_runtime_evidence_store_rejects_sensitive_artifact_filenames(tmp_path):
    artifact_base_dir = tmp_path / "artifacts"
    sensitive_names = [".env", "id_rsa", "credentials.txt", "session_token.txt", "secret.key"]
    run_template = RuntimeEngine(engine_id="runtime:persistent")

    for sensitive_name in sensitive_names:
        artifact_path = artifact_base_dir / sensitive_name
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text('{"schema":"test-artifact/v1", "summary":"sensitive"}', encoding="utf-8")
        run = run_template.run_task(
            agent_id="agent:runtime",
            task="prepare persistent evidence",
            tools=["read_file", "write_report"],
            artifacts=[{"path": str(artifact_path), "kind": "evidence"}],
        )

        with pytest.raises(ValueError, match="sensitive"):
            persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=artifact_base_dir)


def test_runtime_evidence_validation_blocks_tampered_bundled_artifact(tmp_path):
    run = _runtime_run(tmp_path)
    bundle = persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=tmp_path)
    bundled_artifact = Path(bundle["artifacts"][0]["bundle_path"])
    bundled_artifact.write_text('{"tampered": true}\n', encoding="utf-8")

    report = validate_runtime_evidence_bundle(bundle["bundle_path"])

    assert report["status"] == "blocked"
    assert "artifact_hash_mismatch" in _issue_codes(report)
    assert report["checks"]["artifact_file_hashes_match"] is False


def test_runtime_evidence_validation_blocks_tampered_manifest_hash(tmp_path):
    run = _runtime_run(tmp_path)
    bundle = persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=tmp_path)
    manifest_path = Path(bundle["files"]["artifact_manifest"]["path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"][0]["content_hash"] = "sha256:" + "0" * 64
    _write_json(manifest_path, manifest)
    bundle_path = Path(bundle["bundle_path"])
    bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    bundle_payload["files"]["artifact_manifest"]["size_bytes"] = manifest_path.stat().st_size
    bundle_payload["files"]["artifact_manifest"]["sha256"] = _sha256_file(manifest_path)
    _write_json(bundle_path, bundle_payload)

    report = validate_runtime_evidence_bundle(bundle_path)

    assert report["status"] == "blocked"
    assert "artifact_manifest_hash_mismatch" in _issue_codes(report)
    assert report["checks"]["artifact_manifest_hashes_match"] is False


def test_runtime_evidence_validation_blocks_promotion_leak(tmp_path):
    run = _runtime_run(tmp_path)
    run["promotion_decision"] = {"status": "promoted"}
    bundle = persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=tmp_path)

    report = validate_runtime_evidence_bundle(bundle["bundle_path"])

    assert report["status"] == "blocked"
    assert "runtime_evidence_promotion_leak" in _issue_codes(report)


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()
