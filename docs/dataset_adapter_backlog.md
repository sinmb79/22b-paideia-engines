# Dataset Adapter Backlog

[한국어](dataset_adapter_backlog.ko.md)

The current repository ships metadata and examples, not full textbook or exam datasets. Dataset adapters must stay legal, manifest-driven, and local-first.

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
   - Guardrail: verify `09_verification.json` and no direct stress-to-promotion decision.

## Deferred

- Automatic textbook download.
- Scraping digital textbook viewer content.
- Uploading private training corpora to external services.
