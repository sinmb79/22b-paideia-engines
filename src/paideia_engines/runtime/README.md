# Runtime Engine

[한국어](README.ko.md)

The Runtime Engine records task execution evidence without making learning updates.

## Owns

- Runtime run IDs
- Trace records
- Artifact manifests
- Acceptance checklists
- Replayable traces

## Public API

- `RuntimeEngine(engine_id="runtime")`
- `run_task(...)`
- `replay_trace(run_id)`
- `TaskRun`

## Safety Boundary

Runtime results require review before downstream memory promotion.
