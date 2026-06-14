"""Runtime engine that executes a task in a trace-first, review-aware format."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


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
        self._runs = []

    def _build_trace(self, task: str, tools: list[str]) -> list[dict[str, Any]]:
        normalized_tools = [str(tool) for tool in tools]
        return [
            {"step": 1, "action": "task.accepted", "task": task},
            {
                "step": 2,
                "action": "trace_recorded",
                "tool_count": len(normalized_tools),
                "tools": normalized_tools,
            },
            {"step": 3, "action": "evidence_gathered"},
            {"step": 4, "action": "task.completed"},
        ]

    @staticmethod
    def _build_acceptance_checklist(task: str, tools: list[str]) -> dict[str, Any]:
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
                    "acceptance_criteria": [
                        "review_required_for_memory_promotion",
                        "verify_source_evidence_before_marketing",
                    ],
                },
                "task_quality": {"task_summary_non_empty": bool(task.strip())},
            },
            "notes": "runtime task requires human review before downstream memory promotion",
        }

    def run_task(self, agent_id: str, task: str, tools: list[str]) -> dict[str, Any]:
        task = str(task)
        tools = list(tools)
        run = TaskRun(agent_id=agent_id, task=task, tools=tools)
        trace = self._build_trace(task=run.task, tools=run.tools)
        acceptance = self._build_acceptance_checklist(task=run.task, tools=run.tools)
        result = {
            "schema": "paideia-runtime-run/v1",
            "engine_id": self.engine_id,
            "status": "completed_needs_review",
            "agent_id": run.agent_id,
            "task": task,
            "tools": tools,
            "trace": trace,
            "acceptance_checklist": acceptance,
            "timestamp": _utc_now(),
        }
        self._runs.append(result)
        return result


__all__ = ["RuntimeEngine", "TaskRun"]
