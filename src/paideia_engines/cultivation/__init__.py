"""Cultivation engine for deterministic learner blueprint construction."""

from __future__ import annotations

from typing import Any, Iterable


class CultivationEngine:
    """Build deterministic cultivation blueprints for a learner.

    The implementation is intentionally lightweight and deterministic to keep tests
    and callers stable across executions.
    """

    schema = "paideia-cultivation-blueprint/v1"
    _default_stages = ("foundation", "practice", "assessment", "integration")

    def __init__(self, *, curriculum_density: str = "standard") -> None:
        if curriculum_density not in {"standard", "minimal", "extended"}:
            raise ValueError("curriculum_density must be standard, minimal, or extended.")
        self._curriculum_density = curriculum_density

    def create_blueprint(
        self,
        learner_id: str,
        role: str,
        objectives: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        if not learner_id:
            raise ValueError("learner_id is required.")
        if not role:
            raise ValueError("role is required.")

        normalized_objectives = self._normalize_objectives(objectives)

        return {
            "schema": self.schema,
            "learner_id": learner_id,
            "role": role,
            "curriculum": self._build_curriculum(role, normalized_objectives),
            "handoffs": ["assessment", "promotion"],
            "objectives": normalized_objectives,
            "metadata": {
                "curriculum_density": self._curriculum_density,
            },
        }

    def _normalize_objectives(self, objectives: Iterable[str] | None) -> list[str]:
        if objectives is None:
            return []
        cleaned: list[str] = []
        for objective in objectives:
            text = str(objective).strip()
            if text:
                cleaned.append(text)
        return cleaned

    def _build_curriculum(self, role: str, objectives: list[str]) -> list[dict[str, Any]]:
        objectives = list(objectives)
        primary_focus = objectives[0:2] or [f"{role} workflow fundamentals"]

        curriculum: list[dict[str, Any]] = []
        curriculum.append(
            {
                "stage": self._default_stages[0],
                "goal": "Establish conceptual foundations.",
                "objectives": primary_focus,
                "duration": "weeks_1_to_2",
            }
        )
        curriculum.append(
            {
                "stage": self._default_stages[1],
                "goal": "Practice workflows with deterministic evidence habits.",
                "objectives": ["evidence_checking", "uncertainty_awareness"],
                "duration": "weeks_3_to_4",
            }
        )
        curriculum.append(
            {
                "stage": self._default_stages[2],
                "goal": "Evaluate output quality before any promotion decision.",
                "objectives": ["self_audit", "rubric_validation"],
                "duration": "weeks_5_to_6",
            }
        )
        curriculum.append(
            {
                "stage": self._default_stages[3],
                "goal": "Stabilize habits for long-term growth.",
                "objectives": ["memory_integration", "reflection_loop"],
                "duration": "weeks_7_to_8",
            }
        )
        return curriculum

