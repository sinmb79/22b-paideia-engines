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
```

## Non-Goals

- HWP/PDF textbook parsing
- Digital textbook viewer scraping
- EBSi exam-page crawling
- AI-Hub download automation
- External upload of training corpora
