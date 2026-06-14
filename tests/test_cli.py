import json
import os
from pathlib import Path
import subprocess
import sys

from paideia_engines.data_acquisition import DataAcquisitionEngine


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


def test_cli_run_config_writes_json_output(tmp_path):
    config_path = tmp_path / "config.json"
    output_path = tmp_path / "result.json"
    config_path.write_text(json.dumps(_config(tmp_path), ensure_ascii=False), encoding="utf-8")

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
        check=True,
    )

    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-configured-suite-run/v1"
    assert payload["config_id"] == "cli-demo"
    assert "wrote" in completed.stdout.lower()


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
    assert payload["summary"]["total"] == 3
    assert "source_diagnostics" in completed.stdout


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
