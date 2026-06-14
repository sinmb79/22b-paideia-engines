# 런타임 엔진

[English](README.md)

런타임 엔진은 학습 업데이트를 만들지 않고 작업 실행 증거를 기록합니다.

## 책임

- Runtime run ID
- Trace record
- Artifact manifest
- Acceptance checklist
- 재실행 가능한 trace

## 공개 API

- `RuntimeEngine(engine_id="runtime")`
- `run_task(...)`
- `replay_trace(run_id)`
- `TaskRun`

## 안전 경계

런타임 결과는 downstream memory promotion 전에 검토가 필요합니다.
