# 릴리스 체크리스트

[English](release_checklist.md)

PR을 ready로 바꾸거나 GitHub release를 만들기 전에 이 체크리스트를 실행합니다.

## 필수 명령

```powershell
python -m pytest tests -q
python examples\basic_growth_cycle.py
python examples\data_and_curriculum_pipeline.py
python examples\assessment_and_cultivation_pipeline.py
python examples\stress_and_promotion_pipeline.py
python examples\governance_and_runtime_pipeline.py
python examples\source_specific_parsers.py
python examples\downstream_single_engine_recipe.py
python examples\downstream_suite_recipe.py
python -m paideia_engines.cli validate-contracts --repo-root . --output .paideia-runs\contract-validation.json
python -m paideia_engines.cli certify-adapters --fixtures examples\source_fixture_pack.json --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\adapter-certification.json
python -m paideia_engines.cli diagnose-source --manifest examples\source_fixture_pack.json --output .paideia-runs\source-diagnostics.json
python -m paideia_engines.cli diagnose-manifest --manifest examples\acquired_sources_manifest.jsonl --output .paideia-runs\manifest-diagnostics.json
python -m paideia_engines.cli diagnose-stress-pack --pack examples\stress_packs\core_subject_stress_pack.json --output .paideia-runs\stress-pack-diagnostics.json
python -m paideia_engines.cli run-config --config examples\configured_suite.json --output .paideia-runs\result.json --output-dir .paideia-runs\engines
python -m paideia_engines.cli validate-suite-output --output-dir .paideia-runs\engines --result .paideia-runs\result.json --output .paideia-runs\suite-output-validation.json
python -m paideia_engines.cli persist-runtime-evidence --runtime-output .paideia-runs\engines\09_runtime.json --store-dir .paideia-runs\runtime --artifact-base-dir examples --output .paideia-runs\runtime-evidence-bundle.json
python -m paideia_engines.cli validate-runtime-evidence --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json --output .paideia-runs\runtime-evidence-validation.json
python -m paideia_engines.cli replay-runtime-evidence --bundle .paideia-runs\runtime\runtime_phase5-run-0001\evidence-bundle.json --output .paideia-runs\runtime-evidence-replay.json
python -m paideia_engines.cli smoke --engine all --output .paideia-runs\smoke.json
python -m paideia_engines.cli validate-benchmarks --pack examples\benchmark_packs\core_engine_benchmark_pack.json --result .paideia-runs\result.json --output-dir .paideia-runs\engines --reports-dir .paideia-runs --output .paideia-runs\benchmark-validation.json
python -m paideia_engines.cli validate-release-candidate --repo-root . --output .paideia-runs\release-candidate-validation.json
python -m compileall src
rg -n "([O]PENAI_API_KEY|[A]NTHROPIC_API_KEY|[G]ITHUB_TOKEN|github[_]pat_|gh[p]_|\bsk-[A-Za-z0-9]{16,}|[B]EGIN (RSA|OPENSSH|PRIVATE) KEY|passw[o]rd\s*=|secr[e]t\s*=)" README.md README.ko.md docs src tests data examples -g "!**/__pycache__/**"
git status --short --branch
gh pr view 1 --json number,title,url,isDraft,headRefName,baseRefName,state,commits
```

## 필수 수동 확인

- README에서 한국어 문서와 엔진 문서로 이동할 수 있어야 합니다.
- 엔진 계약 검증이 통과해야 하며, 모든 엔진은 공개 API, schema, 문서, 예제, 안전 경계 항목을 가져야 합니다.
- Adapter certification이 통과해야 하며, 모든 parser fixture는 valid acquired-source manifest record와 연결되어야 합니다.
- 모든 엔진 패키지에 영문/한국어 README가 있어야 합니다.
- `.paideia-runs/`, `.paideia-data/`, `.paideia-smoke/`, 로컬 생성 산출물이 staged 상태가 아니어야 합니다.
- 공개 seed data는 metadata만 포함하고 제한 교과서 본문을 포함하지 않아야 합니다.
- 공개 release validation에는 `--allow-local-only-full-content`를 사용하지 않습니다.
- Acquired-source manifest는 `examples/`, `data/`, `docs/`, `src/`, `tests/` 안의 AI-Hub corpus, 시험지 PDF/HWP/audio/video, 교과서 원본을 가리키지 않아야 합니다.
- Acquired-source manifest에는 local user-profile folder를 가리키는 private absolute path가 없어야 합니다.
- Stress pack에는 `promotion_decision`, `ledger_version`, `experience_id` record가 없어야 합니다.
- Runtime evidence bundle은 복사된 artifact file의 존재, size, hash, replay trace를 검증해야 합니다.
- Benchmark validation은 golden schema, mutation expectation, release evidence threshold를 통과해야 합니다.
- Release candidate validation은 link, UTF-8, replacement character, sensitive pattern, 개인 로컬 경로, acquired-source manifest, generated path, packaging metadata check를 통과해야 합니다.
- Downstream reuse example은 single-engine import와 configured-suite composition이 모두 동작함을 보여야 합니다.
- PR 본문에 검증 명령과 현재 draft/ready 상태가 적혀 있어야 합니다.

## 릴리스 판단

명령 결과와 [공개 자산 감사](public_asset_audit.ko.md)가 모두 깨끗할 때만 PR을 ready로 바꿀 수 있습니다.
