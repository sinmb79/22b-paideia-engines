import json
from pathlib import Path

from paideia_engines.contracts import validate_engine_contract_registry
from paideia_engines.data_acquisition import (
    certify_adapters,
    diagnose_acquired_source_manifest,
    diagnose_source_fixture_pack,
)
from paideia_engines.evaluation import validate_benchmark_pack
from paideia_engines.orchestration.config_runner import EXECUTION_TRACE, run_config_file, run_engine_smoke
from paideia_engines.runtime import persist_runtime_evidence, validate_runtime_evidence_bundle
from paideia_engines.stress import diagnose_stress_scenario_pack


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_evidence(tmp_path: Path) -> tuple[Path, Path, Path]:
    result_path = tmp_path / "result.json"
    output_dir = tmp_path / "engines"
    reports_dir = tmp_path / "reports"

    result = run_config_file(
        ROOT / "examples" / "configured_suite.json",
        output_path=result_path,
        output_dir=output_dir,
    )
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


def _issue_codes(report: dict[str, object]) -> set[str]:
    return {str(issue["code"]) for issue in report["issues"]}


def test_benchmark_pack_passes_release_ready_evidence(tmp_path):
    result_path, output_dir, reports_dir = _build_evidence(tmp_path)

    report = validate_benchmark_pack(
        ROOT / "examples" / "benchmark_packs" / "core_engine_benchmark_pack.json",
        result=result_path,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )

    assert report["schema"] == "paideia-benchmark-report/v1"
    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["checks"]["golden_engine_schemas_match"] is True
    assert report["checks"]["mutation_expectations_declared"] is True
    assert report["checks"]["thresholds_met"] is True
    assert report["measurements"]["contract_validation"]["count"] == 12
    assert report["measurements"]["runtime_evidence_validation"]["count"] == 1


def test_benchmark_pack_golden_schema_order_matches_trace_schema_v2():
    pack = _load_json(ROOT / "examples" / "benchmark_packs" / "core_engine_benchmark_pack.json")

    assert list(pack["golden_engine_schemas"]) == list(EXECUTION_TRACE)


def test_benchmark_pack_blocks_stale_golden_schema_order(tmp_path):
    result_path, output_dir, reports_dir = _build_evidence(tmp_path)
    pack_path = tmp_path / "benchmark-pack.json"
    pack = _load_json(ROOT / "examples" / "benchmark_packs" / "core_engine_benchmark_pack.json")
    schemas = pack["golden_engine_schemas"]
    stale_order = [
        "data_acquisition",
        "acquisition_validation",
        "curriculum_mapping",
        "cultivation",
        "assessment",
        "stress",
        "promotion",
        "governance",
        "runtime",
        "verification",
    ]
    pack["golden_engine_schemas"] = {engine_name: schemas[engine_name] for engine_name in stale_order}
    _write_json(pack_path, pack)

    report = validate_benchmark_pack(
        pack_path,
        result=result_path,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )

    assert report["status"] == "blocked"
    assert report["checks"]["golden_engine_schemas_match"] is False
    assert "golden_engine_schemas_mismatch" in _issue_codes(report)


def test_benchmark_pack_blocks_tampered_suite_outputs(tmp_path):
    result_path, output_dir, reports_dir = _build_evidence(tmp_path)
    stress_path = output_dir / "06_stress.json"
    stress_payload = _load_json(stress_path)
    stress_payload["promotion_decision"] = {"status": "promoted"}
    _write_json(stress_path, stress_payload)

    report = validate_benchmark_pack(
        ROOT / "examples" / "benchmark_packs" / "core_engine_benchmark_pack.json",
        result=result_path,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )

    assert report["status"] == "blocked"
    assert "configured_suite_validation_blocked" in _issue_codes(report)
    assert "stress_promotion_decision_present" in report["suite_output_validation"]["issue_codes"]
    assert report["checks"]["configured_suite_validation_passed"] is False


def test_benchmark_pack_blocks_unmet_thresholds(tmp_path):
    result_path, output_dir, reports_dir = _build_evidence(tmp_path)
    pack_path = tmp_path / "benchmark-pack.json"
    pack = _load_json(ROOT / "examples" / "benchmark_packs" / "core_engine_benchmark_pack.json")
    pack["thresholds"]["min_stress_scenarios"] = 999
    _write_json(pack_path, pack)

    report = validate_benchmark_pack(
        pack_path,
        result=result_path,
        output_dir=output_dir,
        reports_dir=reports_dir,
    )

    assert report["status"] == "blocked"
    assert "benchmark_threshold_not_met" in _issue_codes(report)
    assert report["checks"]["thresholds_met"] is False
    assert report["measurements"]["stress_pack_diagnostics"]["count"] < 999
