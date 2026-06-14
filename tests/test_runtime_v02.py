from paideia_engines.runtime import RuntimeEngine


def test_runtime_engine_records_artifact_manifest_and_replayable_trace():
    engine = RuntimeEngine(engine_id="runtime:test")

    run = engine.run_task(
        agent_id="agent:analyst",
        task="prepare evidence summary",
        tools=["read_file", "summarize"],
        artifacts=[
            {"path": "reports/evidence.json", "kind": "evidence"},
            {"path": "traces/runtime.json", "kind": "trace"},
        ],
    )

    assert run["schema"] == "paideia-runtime-run/v1"
    assert run["run_id"] == "runtime_test-run-0001"
    assert run["artifact_manifest"]["schema"] == "paideia-runtime-artifact-manifest/v1"
    assert run["artifact_manifest"]["artifact_count"] == 2
    assert run["artifact_manifest"]["artifacts"][0]["content_hash"].startswith("sha256:")
    assert run["acceptance_checklist"]["checks"]["reproducibility"]["artifact_manifest_retained"] is True
    assert run["acceptance_checklist"]["checks"]["reproducibility"]["replay_trace_available"] is True
    assert "promotion_decision" not in run


def test_runtime_engine_replays_previous_trace_by_run_id():
    engine = RuntimeEngine(engine_id="runtime:test")
    run = engine.run_task(
        agent_id="agent:analyst",
        task="prepare evidence summary",
        tools=["read_file"],
        artifacts=[{"path": "reports/evidence.json", "kind": "evidence"}],
    )

    replay = engine.replay_trace(run["run_id"])

    assert replay["schema"] == "paideia-runtime-replay/v1"
    assert replay["run_id"] == run["run_id"]
    assert replay["replayable"] is True
    assert replay["trace_length"] == len(run["trace"])
    assert replay["artifact_manifest"]["artifact_count"] == 1


def test_runtime_engine_blocks_unknown_replay_id():
    engine = RuntimeEngine()

    try:
        engine.replay_trace("missing-run")
    except KeyError as exc:
        assert "Unknown runtime run_id" in str(exc)
    else:
        raise AssertionError("Expected KeyError for missing run_id.")
