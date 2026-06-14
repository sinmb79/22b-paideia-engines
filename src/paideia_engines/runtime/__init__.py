"""Runtime engine that executes a task in a trace-first, review-aware format."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any

from paideia_engines.runtime.evidence_store import (
    RuntimeEvidenceStore,
    persist_runtime_evidence,
    replay_runtime_evidence_bundle,
    validate_runtime_evidence_bundle,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TaskRun:
    agent_id: str
    task: str
    tools: list[str]

    def summarize(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task": self.task,
            "tools": list(self.tools),
        }


class RuntimeEngine:
    """Run tasks and return deterministic runtime telemetry."""

    schema = "paideia-runtime-engine/v1"

    def __init__(self, engine_id: str = "runtime") -> None:
        self.engine_id = engine_id
        self._counter = 0
        self._runs = []
        self._run_index: dict[str, dict[str, Any]] = {}

    def _next_run_id(self) -> str:
        self._counter += 1
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", self.engine_id).strip("_") or "runtime"
        return f"{normalized}-run-{self._counter:04d}"

    def _build_trace(self, run_id: str, task: str, tools: list[str]) -> list[dict[str, Any]]:
        normalized_tools = [str(tool) for tool in tools]
        return [
            {"step": 1, "action": "task.accepted", "run_id": run_id, "task": task},
            {
                "step": 2,
                "action": "trace_recorded",
                "run_id": run_id,
                "tool_count": len(normalized_tools),
                "tools": normalized_tools,
            },
            {"step": 3, "action": "artifact_manifest_recorded", "run_id": run_id},
            {"step": 4, "action": "evidence_gathered", "run_id": run_id},
            {"step": 5, "action": "task.completed", "run_id": run_id},
        ]

    @staticmethod
    def _artifact_hash(artifact: dict[str, Any]) -> str:
        encoded = json.dumps(artifact, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def _build_artifact_manifest(
        self,
        *,
        run_id: str,
        artifacts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        normalized_artifacts = []
        for index, artifact in enumerate(artifacts, start=1):
            normalized = {
                "artifact_id": f"{run_id}-artifact-{index:04d}",
                "path": str(artifact.get("path", "")),
                "kind": str(artifact.get("kind", "artifact")),
                "metadata": dict(artifact.get("metadata", {})),
            }
            normalized["content_hash"] = self._artifact_hash(normalized)
            normalized_artifacts.append(normalized)

        return {
            "schema": "paideia-runtime-artifact-manifest/v1",
            "run_id": run_id,
            "artifact_count": len(normalized_artifacts),
            "artifacts": normalized_artifacts,
            "timestamp": _utc_now(),
        }

    @staticmethod
    def _build_acceptance_checklist(task: str, tools: list[str], artifact_manifest: dict[str, Any]) -> dict[str, Any]:
        return {
            "requires_review": True,
            "checks": {
                "tooling": {
                    "configured": bool(tools),
                    "tool_count": len(tools),
                    "tool_names": list(tools),
                },
                "reproducibility": {
                    "trace_retained": True,
                    "artifact_manifest_retained": True,
                    "replay_trace_available": True,
                    "artifact_count": artifact_manifest["artifact_count"],
                    "acceptance_criteria": [
                        "review_required_for_memory_promotion",
                        "verify_source_evidence_before_marketing",
                        "retain_artifact_manifest",
                        "retain_replayable_trace",
                    ],
                },
                "task_quality": {"task_summary_non_empty": bool(task.strip())},
            },
            "notes": "runtime task requires human review before downstream memory promotion",
        }

    def run_task(
        self,
        agent_id: str,
        task: str,
        tools: list[str],
        artifacts: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        task = str(task)
        tools = list(tools)
        artifacts = list(artifacts or [])
        run_id = self._next_run_id()
        run = TaskRun(agent_id=agent_id, task=task, tools=tools)
        trace = self._build_trace(run_id=run_id, task=run.task, tools=run.tools)
        artifact_manifest = self._build_artifact_manifest(run_id=run_id, artifacts=artifacts)
        acceptance = self._build_acceptance_checklist(
            task=run.task,
            tools=run.tools,
            artifact_manifest=artifact_manifest,
        )
        result = {
            "schema": "paideia-runtime-run/v1",
            "engine_id": self.engine_id,
            "run_id": run_id,
            "status": "completed_needs_review",
            "agent_id": run.agent_id,
            "task": task,
            "tools": tools,
            "trace": trace,
            "artifact_manifest": artifact_manifest,
            "acceptance_checklist": acceptance,
            "timestamp": _utc_now(),
        }
        self._runs.append(result)
        self._run_index[run_id] = result
        return result

    def replay_trace(self, run_id: str) -> dict[str, Any]:
        if run_id not in self._run_index:
            raise KeyError(f"Unknown runtime run_id: {run_id}")

        run = self._run_index[run_id]
        return {
            "schema": "paideia-runtime-replay/v1",
            "engine_id": self.engine_id,
            "run_id": run_id,
            "replayable": True,
            "trace_length": len(run["trace"]),
            "trace": list(run["trace"]),
            "artifact_manifest": dict(run["artifact_manifest"]),
            "acceptance_checklist": dict(run["acceptance_checklist"]),
            "timestamp": _utc_now(),
        }


__all__ = [
    "RuntimeEngine",
    "RuntimeEvidenceStore",
    "TaskRun",
    "persist_runtime_evidence",
    "replay_runtime_evidence_bundle",
    "validate_runtime_evidence_bundle",
]
