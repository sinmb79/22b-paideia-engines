# Data Acquisition Engine

[한국어](README.ko.md)

The Data Acquisition Engine plans education data use without bypassing source licenses.

## Owns

- Source license decisions
- Engine-specific acquisition plans
- Restricted textbook blocking
- Acquired source hashes and JSONL manifests

## Public API

- `DataAcquisitionEngine(records, storage_root)`
- `evaluate_source(source_id)`
- `build_engine_plan(engine_name)`
- `register_acquired_source(...)`

## Safety Boundary

This engine records metadata and local acquisition evidence. It does not download restricted textbooks automatically.
