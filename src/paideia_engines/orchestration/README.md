# Orchestration Engine

[한국어](README.ko.md)

The Orchestration Engine composes independent engines without hiding their contracts.

## Owns

- `PaideiaEngineSuite` growth cycle composition
- Config-driven suite runner
- CLI-friendly JSON input and output
- Per-engine output paths
- Configured-suite verification summary

## Public API

- `PaideiaEngineSuite`
- `run_configured_suite(config, output_dir=None)`
- `run_config_file(config_path, output_path=None, output_dir=None)`
- `run_engine_smoke(engine="all")`

## Safety Boundary

Orchestration writes outputs and trace metadata. It does not rewrite engine decisions.
