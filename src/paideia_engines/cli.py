"""Command line interface for Paideia Engines."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from paideia_engines.data_acquisition.source_diagnostics import diagnose_source_fixture_pack
from paideia_engines.orchestration.config_runner import run_config_file, run_engine_smoke, write_json


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

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_parser", "main"]
