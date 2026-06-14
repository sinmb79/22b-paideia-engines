# Release Checklist

[한국어](release_checklist.ko.md)

Run this checklist before marking the PR ready or creating a GitHub release.

## Required Commands

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python examples\source_specific_parsers.py
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
python -m paideia_engines.cli diagnose-stress-pack --pack examples\stress_packs\core_subject_stress_pack.json --output .paideia-runs\stress-pack-diagnostics.json
python -m paideia_engines.cli run-config --config examples\configured_suite.json --output .paideia-runs\result.json --output-dir .paideia-runs\engines
python -m paideia_engines.cli validate-suite-output --output-dir .paideia-runs\engines --result .paideia-runs\result.json --output .paideia-runs\suite-output-validation.json
python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json
python -m compileall src
rg -n "<release-sensitive-patterns>" README.md README.ko.md docs src tests data examples -g "!**/__pycache__/**"
git status --short --branch
gh pr view 1 --json number,title,url,isDraft,headRefName,baseRefName,state,commits
```

## Required Manual Checks

- README links to Korean documentation and engine documentation.
- Per-engine README files exist in every engine package.
- `.paideia-runs/`, `.paideia-data/`, `.paideia-smoke/`, and local generated outputs are not staged.
- Public seed data contains metadata only, not restricted textbook contents.
- Public release validation does not use `--allow-local-only-full-content`.
- Acquired-source manifests do not point to AI-Hub corpora, exam PDFs/HWPs/audio/video, or textbook originals inside `examples/`, `data/`, `docs/`, `src/`, or `tests/`.
- Acquired-source manifests contain no private absolute paths such as `C:\Users\...`.
- Stress packs contain no `promotion_decision`, `ledger_version`, or `experience_id` records.
- PR body lists validation commands and current draft/ready status.

## Release Decision

The PR can become ready only when the command results and the [Public Asset Audit](public_asset_audit.md) are clean.
