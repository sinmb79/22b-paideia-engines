# Public Asset Audit

[한국어](public_asset_audit.ko.md)

This audit defines what may and may not be included in the public repository.

## Allowed

- Engine source code under `src/paideia_engines/`.
- Tests under `tests/`.
- Public metadata catalogs under `data/`.
- Sample curriculum standards and sample JSON configs.
- Documentation and release checklists.

## Forbidden

- private voice assets
- credentials
- restricted textbooks
- AI-Hub downloaded corpora
- exam PDFs, HWP/HWPX files, archives, audio, or video
- personal data
- generated caches
- private images
- local absolute paths to personal folders
- acquired-source manifests with private absolute paths
- generated run outputs

## Current Public Data Boundary

`data/catalog/seed_sources.json` and `data/curriculum/sample_standards.json` contain metadata and small synthetic/sample standards only. Restricted textbook contents must be acquired outside the repository with a license or explicit permission.

`examples/acquired_sources_manifest.jsonl` is a public-safe manifest example that points only to a small sample JSONL file. Real acquired-source manifests for textbooks, exam archives, AI-Hub downloads, or licensed corpora should stay outside the public repository unless they are metadata-only and contain no private absolute paths.

## Audit Command

```powershell
rg -n "<release-sensitive-patterns>" README.md README.ko.md docs src tests data examples -g "!**/__pycache__/**"
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
```

No matches are expected before release.
