# Dataset Adapter Backlog

[한국어](dataset_adapter_backlog.ko.md)

The current repository ships metadata and examples, not full textbook or exam datasets. Dataset adapters must stay legal, manifest-driven, and local-first.

## Implemented In Phase 7

- `DataAcquisitionEngine.validate_acquired_sources(...)`
- `DataAcquisitionEngine.validate_manifest(...)`
- `CurriculumMappingEngine.load_standards_file(...)`
- `ItemBank.from_file(...)`
- Configured-suite `acquisition_validation` output

The implemented adapters parse already-acquired local JSON files. They do not download textbooks, scrape exam archives, or copy restricted source files into the repository.

## Implemented In Phase 8

- `parse_ncic_curriculum_csv(...)`
- `parse_assessment_items_csv(...)`
- `parse_aihub_math_items_json(...)`
- `build_public_exam_metadata_manifest(...)`
- Config runner parser keys: `ncic_csv`, `data_go_kr_csv`, `public_assessment_csv`, `aihub_json`, `aihub_csv`

The Phase 8 parsers consume local CSV/JSON exports only. They intentionally do not parse HWP/PDF textbooks or crawl exam pages.

## Implemented In Phase 9

- `diagnose_source_file(...)`
- `diagnose_source_fixture_pack(...)`
- CLI command: `diagnose-source`
- Public-safe fixture manifest: `examples/source_fixture_pack.json`

The Phase 9 diagnostics layer verifies fixture file existence, hash, parser support, required headers or JSON fields, parser completion, and minimum record counts before a parser pack is treated as release-ready.

## Implemented In Phase 10

- `validate_configured_suite_outputs(...)`
- `validate_configured_suite_result(...)`
- CLI command: `validate-suite-output`
- Release-quality cross-checks for per-engine output files, expected schemas, acquisition validation, final verification, stress-to-promotion boundaries, governance, and runtime replayability

The Phase 10 validator reads existing local JSON outputs only. It does not rerun engines, download source data, or create promotion decisions.

## Implemented In Phase 11

- `diagnose_acquired_source_manifest(...)`
- CLI command: `diagnose-manifest`
- Public-safe example acquired-source manifest: `examples/acquired_sources_manifest.jsonl`
- JSONL parsing, acquired-source schema, duplicate record, content-scope, hash/license-note, auto-download, and public-release safety diagnostics

The Phase 11 diagnostics layer verifies acquired-source manifests before larger local textbook, exam, or AI-Hub corpora are wired into engines. It reads manifest records and local evidence only; it does not download, scrape, copy, or upload source content.

## Adapter Priorities

1. **Public curriculum standards importer**
   - Input: official public curriculum files or manually prepared JSON.
   - Output: `CurriculumStandard` mappings.
   - Guardrail: preserve provider attribution and source URL.

2. **Public assessment item importer**
   - Input: public example items or manually licensed item banks.
   - Output: `AssessmentItem` records.
   - Guardrail: no scraping restricted pages.

3. **Official format-specific parser hardening**
   - Input: real public-source CSV/JSON exports collected under a valid manifest.
   - Output: normalized engine records plus parser diagnostics.
   - Guardrail: keep HWP/PDF and restricted source parsing out of the public repo until explicit license evidence exists.

4. **Subject-specific stress fixture packs**
   - Input: public-safe scenarios mapped to grade, subject, and standard IDs.
   - Output: reusable stress banks for math, language, science, and evidence-review skills.
   - Guardrail: stress packs emit candidate signals only; promotion decisions stay in the promotion engine.

## Deferred

- Automatic textbook download.
- Scraping digital textbook viewer content.
- Uploading private training corpora to external services.
