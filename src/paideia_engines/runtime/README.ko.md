# 런타임 엔진

[English](README.md)

런타임 엔진은 학습 업데이트를 직접 만들지 않고, 작업 실행 증거를 추적 가능한 형태로 기록합니다.

## 책임

- Runtime run ID
- Trace record
- Artifact manifest
- Persistent evidence bundle
- Acceptance checklist
- 재실행 가능한 trace
- Artifact file 존재, size, byte hash, manifest hash 검증

## 공개 API

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
  --runtime-output .paideia-runs\engines\08_runtime.json `
  --store-dir .paideia-runs\runtime `
  --artifact-base-dir examples `
  --output .paideia-runs\runtime-evidence-bundle.json

python -m paideia_engines.cli validate-runtime-evidence `
  --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json `
  --output .paideia-runs\runtime-evidence-validation.json
```

## 안전 경계

런타임 결과는 downstream memory promotion 전에 반드시 review가 필요합니다. Persistent evidence bundle은 선언된 artifact를 local bundle 안으로 복사하고, 복사된 bytes와 manifest hash record를 함께 검증합니다. artifact를 업로드하거나 promotion decision을 만들지 않습니다.
