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
- personal data
- generated caches
- private images
- local absolute paths to personal folders
- generated run outputs

## Current Public Data Boundary

`data/catalog/seed_sources.json` and `data/curriculum/sample_standards.json` contain metadata and small synthetic/sample standards only. Restricted textbook contents must be acquired outside the repository with a license or explicit permission.

## Audit Command

```powershell
rg -n "<release-sensitive-patterns>" README.md README.ko.md docs src tests data examples -g "!**/__pycache__/**"
```

No matches are expected before release.
