import json
from pathlib import Path

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


def test_runtime_evidence_validation_blocks_tampered_bundled_artifact(tmp_path):
    run = _runtime_run(tmp_path)
    bundle = persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=tmp_path)
    bundled_artifact = Path(bundle["artifacts"][0]["bundle_path"])
    bundled_artifact.write_text('{"tampered": true}\n', encoding="utf-8")

    report = validate_runtime_evidence_bundle(bundle["bundle_path"])

    assert report["status"] == "blocked"
    assert "artifact_hash_mismatch" in _issue_codes(report)
    assert report["checks"]["artifact_file_hashes_match"] is False


def test_runtime_evidence_validation_blocks_promotion_leak(tmp_path):
    run = _runtime_run(tmp_path)
    run["promotion_decision"] = {"status": "promoted"}
    bundle = persist_runtime_evidence(run, tmp_path / "store", artifact_base_dir=tmp_path)

    report = validate_runtime_evidence_bundle(bundle["bundle_path"])

    assert report["status"] == "blocked"
    assert "runtime_evidence_promotion_leak" in _issue_codes(report)
