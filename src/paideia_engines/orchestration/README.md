# Orchestration Engine

[한국어](README.ko.md)

The Orchestration Engine composes independent engines without hiding their contracts.

## Owns

- `PaideiaEngineSuite` growth cycle composition
- Config-driven suite runner
- CLI-friendly JSON input and output
- Per-engine output paths
- Configured-suite verification summary
- Configured-suite output validation

## Public API

- `PaideiaEngineSuite`
- `load_config(path)`
- `run_configured_suite(config, output_dir=None)`
- `run_config_file(config_path, output_path=None, output_dir=None)`
- `run_engine_smoke(engine="all")`
- `validate_configured_suite_outputs(output_dir)`
- `validate_configured_suite_result(result, output_dir=None)`

## Safety Boundary

Orchestration writes outputs, trace metadata, and validation reports. The output validator reads existing local JSON only; it does not rerun engines or rewrite engine decisions.
