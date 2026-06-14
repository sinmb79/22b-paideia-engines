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

## Adapter Priorities

1. **Public curriculum standards importer**
   - Input: official public curriculum files or manually prepared JSON.
   - Output: `CurriculumStandard` mappings.
   - Guardrail: preserve provider attribution and source URL.

2. **Public assessment item importer**
   - Input: public example items or manually licensed item banks.
   - Output: `AssessmentItem` records.
   - Guardrail: no scraping restricted pages.

3. **Acquired source manifest validator**
   - Input: `acquired_sources.jsonl`.
   - Output: validation report with hash, license note, approver, and missing fields.
   - Guardrail: fail closed when a restricted source lacks approval.

4. **Configured-suite output validator**
   - Input: per-engine JSON outputs.
   - Output: release-quality validation report.
   - Guardrail: verify `02_acquisition_validation.json`, `10_verification.json`, and no direct stress-to-promotion decision.

5. **Official format-specific parser hardening**
   - Input: real public-source CSV/JSON exports collected under a valid manifest.
   - Output: normalized engine records plus parser diagnostics.
   - Guardrail: keep HWP/PDF and restricted source parsing out of the public repo until explicit license evidence exists.

## Deferred

- Automatic textbook download.
- Scraping digital textbook viewer content.
- Uploading private training corpora to external services.
