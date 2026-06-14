# Runtime Engine

[한국어](README.ko.md)

The Runtime Engine records task execution evidence without making learning updates.

## Owns

- Runtime run IDs
- Trace records
- Artifact manifests
- Persistent evidence bundles
- Acceptance checklists
- Replayable traces
- Artifact file existence, size, byte hash, and manifest hash validation

## Public API

- `RuntimeEngine(engine_id="runtime")`
- `RuntimeEvidenceStore(root)`
- `run_task(...)`
- `replay_trace(run_id)`
- `persist_runtime_evidence(run, store_dir, artifact_base_dir=None)`
- `validate_runtime_evidence_bundle(bundle_path)`
- `replay_runtime_evidence_bundle(bundle_path)`
- `TaskRun`

## CLI

```powershell
python -m paideia_engines.cli persist-runtime-evidence `
  --runtime-output .paideia-runs\engines\09_runtime.json `
  --store-dir .paideia-runs\runtime `
  --artifact-base-dir examples `
  --output .paideia-runs\runtime-evidence-bundle.json

python -m paideia_engines.cli validate-runtime-evidence `
  --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json `
  --output .paideia-runs\runtime-evidence-validation.json
```

## Safety Boundary

Runtime results require review before downstream memory promotion. Persistent evidence bundles copy declared artifacts into the local bundle and validate copied bytes against persisted evidence plus manifest hash records; they do not upload artifacts or create promotion decisions.
