# Source-Specific Parsers

[한국어](source_parsers.ko.md)

Phase 8 adds local source-specific parsers. These parsers do not download, scrape, or unlock protected files. They only normalize already-acquired local files after acquisition validation.

## Supported Inputs

| Parser | Input | Output | Boundary |
| --- | --- | --- | --- |
| `ncic_csv` | NCIC/data.go.kr-style curriculum CSV exports | `CurriculumStandard` records | Public curriculum metadata and standards only |
| `public_assessment_csv` | Public or licensed assessment item CSV | `ItemBank` | No restricted page scraping |
| `aihub_json` | AI-Hub-like math problem JSON labels | `ItemBank` | Requires terms/license note through acquisition validation |
| `aihub_csv` | AI-Hub-like math problem CSV labels | `ItemBank` | Requires terms/license note through acquisition validation |
| `ebsi_metadata_csv` | Public exam metadata CSV | Metadata-only acquired-source records | Does not create assessment items from PDFs/HWP |

## Config Runner Keys

```json
{
  "curriculum": {
    "standards_path": "source_samples/ncic_curriculum_sample.csv",
    "parser": "ncic_csv"
  },
  "assessment": {
    "items_path": "source_samples/aihub_math_sample.json",
    "parser": "aihub_json"
  }
}
```

The file path must also appear in `data.acquired_sources` or `data.manifest_path` and pass hash/license validation before the parser runs.
When the Config Runner invokes a parser, it carries the validated `source_id`, `provider`, `source_url`, and `license_tier` into the normalized records so downstream engines can preserve attribution.

## Example

```powershell
python examples/source_specific_parsers.py
python -m paideia_engines.cli diagnose-source --manifest examples/source_fixture_pack.json --output .paideia-runs/source-diagnostics.json
```

## Diagnostics

Phase 9 adds parser diagnostics for public-safe fixture packs. A diagnostics report checks file existence, SHA-256 hash, supported parser, extension, required headers or JSON fields, parser completion, and minimum record count. The fixture pack stays metadata/sample-only and does not include restricted textbook or exam contents.

## Adding Official Export Samples

Use this order for every new parser fixture:

1. Add only a public-safe local fixture export or a synthetic mini export.
2. Register the fixture in an acquired-source manifest and run `diagnose-manifest`.
3. Register the fixture in `examples/source_fixture_pack.json` and run `diagnose-source`.
4. Run the parser only after manifest diagnostics and source fixture diagnostics pass.

Do not add original textbook PDFs/HWPs, exam PDFs/HWPs/audio/video, AI-Hub full corpora, private paths, or downloaded restricted source bundles to the public repository. Phase 14 will certify official adapter rows by linking parser fixtures to valid acquired-source manifests.

## Non-Goals

- HWP/PDF textbook parsing
- Digital textbook viewer scraping
- EBSi exam-page crawling
- AI-Hub download automation
- External upload of training corpora
