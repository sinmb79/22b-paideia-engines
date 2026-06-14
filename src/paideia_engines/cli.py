"""Command line interface for Paideia Engines."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from paideia_engines.contracts import validate_engine_contract_registry
from paideia_engines.data_acquisition.adapter_certification import certify_adapters
from paideia_engines.data_acquisition.manifest_diagnostics import diagnose_acquired_source_manifest
from paideia_engines.data_acquisition.source_diagnostics import diagnose_source_fixture_pack
from paideia_engines.evaluation import validate_benchmark_pack
from paideia_engines.orchestration.config_runner import run_config_file, run_engine_smoke, write_json
from paideia_engines.orchestration.output_validator import (
    validate_configured_suite_outputs,
    validate_configured_suite_result,
)
from paideia_engines.runtime import (
    persist_runtime_evidence,
    replay_runtime_evidence_bundle,
    validate_runtime_evidence_bundle,
)
from paideia_engines.stress import diagnose_stress_scenario_pack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paideia-engines")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_config = subcommands.add_parser("run-config", help="Run the configured Paideia engine suite.")
    run_config.add_argument("--config", required=True, help="Path to a suite config JSON file.")
    run_config.add_argument("--output", required=True, help="Path to write the full suite result JSON.")
    run_config.add_argument("--output-dir", required=True, help="Directory for per-engine output JSON files.")

    smoke = subcommands.add_parser("smoke", help="Run engine smoke checks.")
    smoke.add_argument("--engine", default="all", help="Engine name or 'all'.")
    smoke.add_argument("--output", required=True, help="Path to write the smoke result JSON.")

    diagnose_source = subcommands.add_parser(
        "diagnose-source",
        help="Run source parser diagnostics for a fixture-pack manifest.",
    )
    diagnose_source.add_argument("--manifest", required=True, help="Path to a source fixture-pack JSON file.")
    diagnose_source.add_argument("--output", required=True, help="Path to write the diagnostics report JSON.")

    certify_adapters_parser = subcommands.add_parser(
        "certify-adapters",
        help="Certify parser adapters by linking source fixtures to acquired-source manifest records.",
    )
    certify_adapters_parser.add_argument("--fixtures", required=True, help="Path to a source fixture-pack JSON file.")
    certify_adapters_parser.add_argument("--manifest", required=True, help="Path to an acquired-source JSONL manifest.")
    certify_adapters_parser.add_argument("--output", required=True, help="Path to write the certification report JSON.")

    diagnose_manifest = subcommands.add_parser(
        "diagnose-manifest",
        help="Run acquired-source manifest diagnostics.",
    )
    diagnose_manifest.add_argument("--manifest", required=True, help="Path to an acquired-source JSONL manifest.")
    diagnose_manifest.add_argument("--output", required=True, help="Path to write the diagnostics report JSON.")
    diagnose_manifest.add_argument(
        "--allow-local-only-full-content",
        action="store_true",
        help="Do not block non-open full-content records as public-release unsafe.",
    )

    diagnose_stress_pack = subcommands.add_parser(
        "diagnose-stress-pack",
        help="Run stress scenario pack diagnostics.",
    )
    diagnose_stress_pack.add_argument("--pack", required=True, help="Path to a stress scenario pack JSON file.")
    diagnose_stress_pack.add_argument("--output", required=True, help="Path to write the diagnostics report JSON.")

    validate_contracts = subcommands.add_parser(
        "validate-contracts",
        help="Validate the public engine contract registry against this repository.",
    )
    validate_contracts.add_argument("--repo-root", default=".", help="Repository root to validate.")
    validate_contracts.add_argument("--output", required=True, help="Path to write the contract validation report JSON.")

    validate_suite = subcommands.add_parser(
        "validate-suite-output",
        help="Validate configured-suite per-engine output JSON files.",
    )
    validate_suite.add_argument("--output-dir", required=True, help="Directory containing numbered engine outputs.")
    validate_suite.add_argument("--result", help="Optional full configured-suite result JSON for cross-checking.")
    validate_suite.add_argument("--output", required=True, help="Path to write the validation report JSON.")

    validate_benchmarks = subcommands.add_parser(
        "validate-benchmarks",
        help="Validate a benchmark pack against release evidence reports.",
    )
    validate_benchmarks.add_argument("--pack", required=True, help="Path to a benchmark pack JSON file.")
    validate_benchmarks.add_argument("--result", required=True, help="Configured-suite result JSON path.")
    validate_benchmarks.add_argument("--output-dir", required=True, help="Directory containing per-engine outputs.")
    validate_benchmarks.add_argument("--reports-dir", required=True, help="Directory containing evidence reports.")
    validate_benchmarks.add_argument("--output", required=True, help="Path to write the benchmark report JSON.")

    persist_runtime = subcommands.add_parser(
        "persist-runtime-evidence",
        help="Persist a runtime output JSON as a replayable evidence bundle.",
    )
    persist_runtime.add_argument("--runtime-output", required=True, help="Path to a runtime engine output JSON file.")
    persist_runtime.add_argument("--store-dir", required=True, help="Directory to store runtime evidence bundles.")
    persist_runtime.add_argument(
        "--artifact-base-dir",
        help="Base directory for relative artifact paths in the runtime output.",
    )
    persist_runtime.add_argument("--output", help="Optional path to write a copy of the bundle JSON.")

    validate_runtime = subcommands.add_parser(
        "validate-runtime-evidence",
        help="Validate a persisted runtime evidence bundle and its artifact files.",
    )
    validate_runtime.add_argument("--bundle", required=True, help="Path to an evidence-bundle JSON file or bundle dir.")
    validate_runtime.add_argument("--output", required=True, help="Path to write the validation report JSON.")

    replay_runtime = subcommands.add_parser(
        "replay-runtime-evidence",
        help="Replay a persisted runtime evidence bundle without an in-memory RuntimeEngine.",
    )
    replay_runtime.add_argument("--bundle", required=True, help="Path to an evidence-bundle JSON file or bundle dir.")
    replay_runtime.add_argument("--output", required=True, help="Path to write the replay JSON.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run-config":
        result = run_config_file(args.config, output_path=args.output, output_dir=args.output_dir)
        print(f"Wrote configured suite result to {result['result_path']}")
        return 0

    if args.command == "smoke":
        result = run_engine_smoke(args.engine)
        output_path = write_json(args.output, result)
        print(json.dumps({"wrote": output_path, "summary": result["summary"]}, ensure_ascii=False))
        return 0 if result["summary"]["failed"] == 0 else 1

    if args.command == "diagnose-source":
        result = diagnose_source_fixture_pack(args.manifest)
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "source_diagnostics": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "certify-adapters":
        result = certify_adapters(args.fixtures, args.manifest)
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "adapter_certification": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "diagnose-manifest":
        result = diagnose_acquired_source_manifest(
            args.manifest,
            public_release=not args.allow_local_only_full_content,
        )
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "manifest_diagnostics": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "diagnose-stress-pack":
        result = diagnose_stress_scenario_pack(args.pack)
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "stress_pack_diagnostics": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "validate-contracts":
        result = validate_engine_contract_registry(args.repo_root)
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "contract_validation": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "validate-suite-output":
        if args.result:
            result = validate_configured_suite_result(args.result, output_dir=args.output_dir)
        else:
            result = validate_configured_suite_outputs(args.output_dir)
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "suite_output_validation": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "validate-benchmarks":
        result = validate_benchmark_pack(
            args.pack,
            result=args.result,
            output_dir=args.output_dir,
            reports_dir=args.reports_dir,
        )
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "benchmark_validation": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "persist-runtime-evidence":
        with open(args.runtime_output, "r", encoding="utf-8") as file:
            runtime_output = json.load(file)
        result = persist_runtime_evidence(
            runtime_output,
            args.store_dir,
            artifact_base_dir=args.artifact_base_dir,
        )
        output_path = args.output
        if output_path:
            output_path = write_json(output_path, result)
        print(
            json.dumps(
                {
                    "bundle_path": result["bundle_path"],
                    "wrote": output_path or result["bundle_path"],
                    "runtime_evidence": {
                        "run_id": result["run_id"],
                        "artifact_count": len(result["artifacts"]),
                    },
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "validate-runtime-evidence":
        result = validate_runtime_evidence_bundle(args.bundle)
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "runtime_evidence_validation": result["summary"],
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    if args.command == "replay-runtime-evidence":
        result = replay_runtime_evidence_bundle(args.bundle)
        output_path = write_json(args.output, result)
        print(
            json.dumps(
                {
                    "wrote": output_path,
                    "runtime_evidence_replay": {
                        "run_id": result["run_id"],
                        "trace_length": result["trace_length"],
                    },
                    "status": result["status"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if result["status"] == "passed" else 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_parser", "main"]
