# Evaluation Engine

[한국어](README.ko.md)

The Evaluation Engine validates benchmark packs against release evidence from the reusable Paideia engine suite.

## Owns

- Benchmark pack schema validation
- Golden engine output schema checks
- Required mutation and tamper expectation checks
- Evidence report validation for contracts, adapters, source fixtures, manifests, stress packs, smoke tests, and configured-suite outputs
- Release-readiness thresholds

## Public API

- `validate_benchmark_pack(pack_path, result, output_dir, reports_dir=None)`

## CLI

```powershell
python -m paideia_engines.cli validate-benchmarks `
  --pack examples\benchmark_packs\core_engine_benchmark_pack.json `
  --result .paideia-runs\result.json `
  --output-dir .paideia-runs\engines `
  --reports-dir .paideia-runs `
  --output .paideia-runs\benchmark-validation.json
```

## Safety Boundary

Evaluation reads local JSON evidence only. It does not rerun engines, download datasets, upload artifacts, or write promoted memory.
