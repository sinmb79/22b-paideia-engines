# 오케스트레이션 엔진

[English](README.md)

오케스트레이션 엔진은 각 엔진의 계약을 숨기지 않고 독립 엔진들을 조합합니다.

## 책임

- `PaideiaEngineSuite` 성장 cycle 조합
- 설정 기반 suite runner
- CLI 친화적 JSON 입력/출력
- 엔진별 output path
- 설정 기반 suite verification summary
- 설정 기반 suite output validation

## 공개 API

- `PaideiaEngineSuite`
- `load_config(path)`
- `run_configured_suite(config, output_dir=None)`
- `run_config_file(config_path, output_path=None, output_dir=None)`
- `run_engine_smoke(engine="all")`
- `validate_configured_suite_outputs(output_dir)`
- `validate_configured_suite_result(result, output_dir=None)`

## 안전 경계

오케스트레이션은 산출물, trace metadata, validation report를 씁니다. Output validator는 이미 생성된 로컬 JSON만 읽으며, 엔진을 다시 실행하거나 각 엔진의 결정을 바꾸지 않습니다.
