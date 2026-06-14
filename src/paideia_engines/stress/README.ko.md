# 스트레스 엔진

[English](README.md)

스트레스 엔진은 승급 경계를 보존하면서 회복력 시나리오를 실행합니다.

## 책임

- Stress rollout
- 교육과정 기반 scenario bank
- 과목별 scenario pack
- 함정 위험 flag
- 승급 후보 신호

## 공개 API

- `StressEngine(scenario_bank=None)`
- `run_rollout(...)`
- `run_scenario(...)`
- `StressScenario`
- `StressScenarioBank`
- `StressScenarioBank.from_file(path)`
- `diagnose_stress_scenario_pack(path)`

## 안전 경계

스트레스는 후보 신호를 만들 수 있습니다. 승급 결정을 직접 쓰지 않습니다. `StressScenarioBank.from_file(...)`은 기본적으로 strict diagnostics를 실행하며 unknown field, invalid type, subject/grade metadata 누락, `promotion_decision`, `ledger_version`, `experience_id` record를 거부합니다.
