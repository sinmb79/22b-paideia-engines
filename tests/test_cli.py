import json
import os
from pathlib import Path
import subprocess
import sys

from paideia_engines.contracts import validate_engine_contract_registry
from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_acquisition import (
    certify_adapters,
    diagnose_acquired_source_manifest,
    diagnose_source_fixture_pack,
)
from paideia_engines.orchestration.config_runner import run_config_file, run_engine_smoke
from paideia_engines.runtime import persist_runtime_evidence, validate_runtime_evidence_bundle
from paideia_engines.stress import diagnose_stress_scenario_pack


ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict[str, str]:
    env = dict(os.environ)
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _config(tmp_path: Path) -> dict[str, object]:
    return {
        "config_id": "cli-demo",
        "learner": {
            "learner_id": "agent:cli",
            "role": "local analyst",
            "objectives": ["traceable answers"],
            "task": "prepare local report",
        },
        "data": {"storage_root": str(tmp_path / "data"), "engine": "assessment"},
        "curriculum": {
            "school_level": "elementary",
            "grade": "3",
            "subject": "math",
            "standards": [
                {
                    "standard_id": "E-MATH-03-01",
                    "school_level": "elementary",
                    "grade": "3",
                    "subject": "math",
                    "domain": "numbers_and_operations",
                    "achievement": "Add and subtract within 1000 using place value.",
                }
            ],
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _build_benchmark_evidence(tmp_path: Path) -> tuple[Path, Path, Path]:
    result_path = tmp_path / "result.json"
    output_dir = tmp_path / "engines"
    reports_dir = tmp_path / "reports"
    result = run_config_file(ROOT / "examples" / "configured_suite.json", output_path=result_path, output_dir=output_dir)
    _write_json(reports_dir / "contract-validation.json", validate_engine_contract_registry(ROOT))
    _write_json(
        reports_dir / "adapter-certification.json",
        certify_adapters(
            ROOT / "examples" / "source_fixture_pack.json",
            ROOT / "examples" / "acquired_sources_manifest.jsonl",
        ),
    )
    _write_json(
        reports_dir / "source-diagnostics.json",
        diagnose_source_fixture_pack(ROOT / "examples" / "source_fixture_pack.json"),
    )
    _write_json(
        reports_dir / "manifest-diagnostics.json",
        diagnose_acquired_source_manifest(ROOT / "examples" / "acquired_sources_manifest.jsonl"),
    )
    _write_json(
        reports_dir / "stress-pack-diagnostics.json",
        diagnose_stress_scenario_pack(ROOT / "examples" / "stress_packs" / "core_subject_stress_pack.json"),
    )
    _write_json(reports_dir / "smoke.json", run_engine_smoke("all"))
    bundle = persist_runtime_evidence(
        result["outputs"]["runtime"],
        tmp_path / "runtime-store",
        artifact_base_dir=ROOT / "examples",
    )
    _write_json(
        reports_dir / "runtime-evidence-validation.json",
        validate_runtime_evidence_bundle(bundle["bundle_path"]),
    )
    return result_path, output_dir, reports_dir


def test_cli_run_config_writes_json_output(tmp_path):
    output_path = tmp_path / "result.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "run-config",
            "--config",
            str(ROOT / "examples" / "configured_suite.json"),
            "--output",
            str(output_path),
            "--output-dir",
            str(tmp_path / "outputs"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-configured-suite-run/v1"
    assert payload["config_id"] == "phase5-local-growth-demo"
    assert payload["outputs"]["verification"]["passed"] is True
    assert "wrote" in completed.stdout.lower()


def test_cli_run_config_returns_nonzero_when_verification_fails(tmp_path):
    config = _config(tmp_path)
    config["assessment"] = {
        "answer": "wrong",
        "explanation": "This answer does not solve the item.",
    }
    config_path = tmp_path / "config.json"
    output_path = tmp_path / "result.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "run-config",
            "--config",
            str(config_path),
            "--output",
            str(output_path),
            "--output-dir",
            str(tmp_path / "outputs"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["outputs"]["verification"]["passed"] is False
    assert payload["outputs"]["verification"]["checks"]["assessment_passed"] is False


def test_cli_smoke_runs_all_engines(tmp_path):
    output_path = tmp_path / "smoke.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "smoke",
            "--engine",
            "all",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-cli-smoke/v1"
    assert payload["summary"]["failed"] == 0
    assert {"cultivation", "assessment", "stress", "promotion", "governance", "runtime", "orchestration"} <= set(
        payload["results"]
    )


def test_cli_diagnose_source_fixture_pack_writes_report(tmp_path):
    output_path = tmp_path / "source-diagnostics.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "diagnose-source",
            "--manifest",
            str(ROOT / "examples" / "source_fixture_pack.json"),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-source-fixture-pack-diagnostics/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["total"] == 4
    assert "source_diagnostics" in completed.stdout


def test_cli_certify_adapters_writes_report(tmp_path):
    output_path = tmp_path / "adapter-certification.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "certify-adapters",
            "--fixtures",
            str(ROOT / "examples" / "source_fixture_pack.json"),
            "--manifest",
            str(ROOT / "examples" / "acquired_sources_manifest.jsonl"),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-adapter-certification-report/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["certification_count"] == 4
    assert payload["summary"]["certified"] == 4
    assert "adapter_certification" in completed.stdout


def test_cli_diagnose_manifest_writes_report(tmp_path):
    source_path = tmp_path / "public-items.jsonl"
    source_path.write_text('{"question": "1+1", "answer": "2"}\n', encoding="utf-8")
    manifest_path = tmp_path / "acquired_sources.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "paideia-acquired-source/v1",
                "source_id": "moe_csat_example_items",
                "status": "acquired",
                "local_path": str(source_path),
                "hash": DataAcquisitionEngine.hash_path(source_path),
                "content_scope": "public_content",
                "license_note_path": None,
                "approved_by": "boss",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "manifest-diagnostics.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "diagnose-manifest",
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-acquired-source-manifest-diagnostics/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["failed"] == 0
    assert "manifest_diagnostics" in completed.stdout


def test_cli_validate_suite_output_writes_report(tmp_path):
    result_path = tmp_path / "result.json"
    output_dir = tmp_path / "outputs"
    validation_path = tmp_path / "suite-output-validation.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "run-config",
            "--config",
            str(ROOT / "examples" / "configured_suite.json"),
            "--output",
            str(result_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "validate-suite-output",
            "--output-dir",
            str(output_dir),
            "--result",
            str(result_path),
            "--output",
            str(validation_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(validation_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-configured-suite-output-validation/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["failed"] == 0
    assert "suite_output_validation" in completed.stdout


def test_cli_diagnose_stress_pack_writes_report(tmp_path):
    output_path = tmp_path / "stress-pack-diagnostics.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "diagnose-stress-pack",
            "--pack",
            str(ROOT / "examples" / "stress_packs" / "core_subject_stress_pack.json"),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-stress-scenario-pack-diagnostics/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["scenario_count"] >= 6
    assert "stress_pack_diagnostics" in completed.stdout


def test_cli_validate_contracts_writes_report(tmp_path):
    output_path = tmp_path / "contract-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "validate-contracts",
            "--repo-root",
            str(ROOT),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-engine-contract-validation/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["engine_count"] == 10
    assert payload["summary"]["failed"] == 0
    assert "contract_validation" in completed.stdout


def test_cli_validate_benchmarks_writes_report(tmp_path):
    result_path, output_dir, reports_dir = _build_benchmark_evidence(tmp_path)
    output_path = tmp_path / "benchmark-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "validate-benchmarks",
            "--pack",
            str(ROOT / "examples" / "benchmark_packs" / "core_engine_benchmark_pack.json"),
            "--result",
            str(result_path),
            "--output-dir",
            str(output_dir),
            "--reports-dir",
            str(reports_dir),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-benchmark-report/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["failed"] == 0
    assert "benchmark_validation" in completed.stdout


def test_cli_persist_validate_and_replay_runtime_evidence(tmp_path):
    result_path = tmp_path / "result.json"
    output_dir = tmp_path / "engines"
    store_dir = tmp_path / "runtime-store"
    validation_path = tmp_path / "runtime-evidence-validation.json"
    replay_path = tmp_path / "runtime-evidence-replay.json"

    subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "run-config",
            "--config",
            str(ROOT / "examples" / "configured_suite.json"),
            "--output",
            str(result_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    persist_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "persist-runtime-evidence",
            "--runtime-output",
            str(output_dir / "09_runtime.json"),
            "--store-dir",
            str(store_dir),
            "--artifact-base-dir",
            str(ROOT / "examples"),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    persisted = json.loads(persist_completed.stdout)
    bundle_path = persisted["bundle_path"]
    validate_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "validate-runtime-evidence",
            "--bundle",
            bundle_path,
            "--output",
            str(validation_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    replay_completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "replay-runtime-evidence",
            "--bundle",
            bundle_path,
            "--output",
            str(replay_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    assert validation["schema"] == "paideia-runtime-evidence-validation/v1"
    assert validation["status"] == "passed"
    assert validation["summary"]["artifact_count"] == 1
    assert replay["schema"] == "paideia-runtime-evidence-replay/v1"
    assert replay["status"] == "passed"
    assert "runtime_evidence_validation" in validate_completed.stdout
    assert "runtime_evidence_replay" in replay_completed.stdout


def test_cli_validate_release_candidate_writes_report(tmp_path):
    output_path = tmp_path / "release-candidate-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "validate-release-candidate",
            "--repo-root",
            str(ROOT),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-release-candidate-validation/v1"
    assert payload["status"] == "passed"
    assert payload["summary"]["failed"] == 0
    assert "release_candidate_validation" in completed.stdout
