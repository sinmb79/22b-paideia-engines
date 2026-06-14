# Paideia Engine Data Acquisition Plan

[한국어](data_acquisition.ko.md)

Paideia Engines need data before they can become serious training, assessment, stress, and promotion engines. The first task is not scraping. The first task is legal, traceable acquisition.

## Data Tiers

| Tier | Data | Status | Handling |
| --- | --- | --- | --- |
| 0 | National curriculum and achievement standards | Public | Use as the curriculum spine |
| 1 | AI-Hub education datasets | Login or agreement required | Download manually after terms review |
| 2 | Public exam and example-item archives | Source terms must be checked | Manifest by year, grade, subject, and URL |
| 3 | Publisher textbooks and digital textbooks | Restricted | Do not ingest without license or permission |

## Seed Sources

- NCIC: https://ncic.re.kr/
- data.go.kr NCIC curriculum originals: https://www.data.go.kr/data/15060742/fileData.do
- AI-Hub grade-level subject data: https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71855
- AI-Hub math problem solving data: https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71859
- MOE CSAT example items: https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=101085&lev=0&m=020402
- EBSi: https://www.ebsi.co.kr/
- Digital Textbook: https://dtbook.edunet.net/
- KERIS education copyright guidance: https://copyright.keris.or.kr/wft/fntLaw

## Repository Policy

This public repository stores source metadata, not copyrighted textbook contents. Large or restricted files should live in private local storage with a manifest entry and license note.

```text
data/
  catalog/
    seed_sources.json
    acquired_sources.jsonl
  raw/
  processed/
  licenses/
```

## Rule

No engine should train on a source unless the source has a manifest record with provider, URL, license tier, acquisition mode, and intended engine usage.

## Phase 7 Adapter Contract

The implemented adapter path is:

```text
legal local file -> acquired source manifest -> validation report -> engine adapter
```

- `validate_manifest(...)` and `validate_acquired_sources(...)` verify source id, local path, hash, approver, content scope, and license-note requirements.
- `CurriculumMappingEngine.load_standards_file(...)` imports already-acquired public curriculum JSON into `CurriculumStandard` records.
- `ItemBank.from_file(...)` imports already-acquired public or licensed item-bank JSON into `AssessmentItem` records.
- Configured suite runs now write `02_acquisition_validation.json` before curriculum mapping and `10_verification.json` at the end.

Restricted textbook or digital textbook content may pass only as `metadata_only` unless a license or terms-review note is present. Full-content ingestion without a valid note is blocked.

## Phase 8 Source Parsers

The source-specific parser layer currently supports local CSV/JSON exports:

- NCIC/data.go.kr-style curriculum CSV to `CurriculumStandard`.
- Public assessment item CSV to `ItemBank`.
- AI-Hub-like math problem JSON labels to `ItemBank`.
- Public exam metadata CSV to metadata-only acquired-source records.

The parser layer is downstream of acquisition validation. Parser files must be listed in `data.acquired_sources` or `data.manifest_path`, pass hash validation, and match the configured parser/source pair before use.

## Phase 9 Source Diagnostics

Source diagnostics validate public-safe fixture packs before release. They do not acquire new data; they inspect local sample files, compute hashes, check required fields, run the selected parser, and report record counts.

```powershell
python -m paideia_engines.cli diagnose-source --manifest examples/source_fixture_pack.json --output .paideia-runs/source-diagnostics.json
```

## Phase 11 Manifest Diagnostics

Acquired-source manifest diagnostics validate the JSONL manifest itself before a release or before wiring larger local corpora into engines. The report checks JSONL parsing, acquired-source schema, duplicate source/path records, supported content scopes, hash and license-note validation, auto-download requests, and whether non-open full-content records are safe for a public release.

```powershell
python -m paideia_engines.cli diagnose-manifest --manifest examples/acquired_sources_manifest.jsonl --output .paideia-runs/manifest-diagnostics.json
```

Use `--allow-local-only-full-content` only for private local runs after the Boss has approved local storage and license evidence. Do not use that option for a public GitHub release.
