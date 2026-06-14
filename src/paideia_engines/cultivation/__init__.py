"""Cultivation engine for deterministic learner blueprint construction."""

from __future__ import annotations

from typing import Any, Iterable

from paideia_engines.assessment.item_bank import ItemBank


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

    def build_learning_roadmap(
        self,
        *,
        learning_unit: dict[str, Any],
        data_plan: dict[str, Any],
        item_bank: ItemBank | None = None,
    ) -> dict[str, Any]:
        unit_id = str(learning_unit.get("unit_id", "")).strip()
        if not unit_id:
            raise ValueError("learning_unit.unit_id is required.")
        standards = list(learning_unit.get("standards", []))
        standard_ids = [str(item.get("standard_id")) for item in standards if item.get("standard_id")]
        sources = list(data_plan.get("sources", []))
        usable_sources = [source for source in sources if source.get("decision") != "blocked"]
        blocked_sources = [source for source in sources if source.get("decision") == "blocked"]
        assessment_gates = self._roadmap_assessment_gates(standard_ids, item_bank)

        return {
            "schema": "paideia-cultivation-roadmap/v1",
            "unit_id": unit_id,
            "school_level": learning_unit.get("school_level"),
            "grade": learning_unit.get("grade"),
            "subject": learning_unit.get("subject"),
            "standard_ids": standard_ids,
            "licensed_source_count": len(usable_sources),
            "blocked_source_count": len(blocked_sources),
            "source_policy": {
                "usable_source_ids": [source.get("source_id") for source in usable_sources],
                "blocked_source_ids": [source.get("source_id") for source in blocked_sources],
            },
            "stages": self._roadmap_stages(standards),
            "assessment_gates": assessment_gates,
            "engine_handoffs": ["assessment", "stress", "promotion", "governance"],
        }

    def _roadmap_stages(self, standards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        standard_ids = [str(item.get("standard_id")) for item in standards if item.get("standard_id")]
        return [
            {
                "stage": "foundation",
                "goal": "Introduce concepts and vocabulary linked to achievement standards.",
                "standard_ids": standard_ids,
            },
            {
                "stage": "guided_practice",
                "goal": "Practice with licensed or reviewed data sources.",
                "standard_ids": standard_ids,
            },
            {
                "stage": "assessment",
                "goal": "Run item-bank gates and capture review labels.",
                "standard_ids": standard_ids,
            },
            {
                "stage": "reflection",
                "goal": "Send reviewed experiences to promotion or quarantine.",
                "standard_ids": standard_ids,
            },
        ]

    def _roadmap_assessment_gates(
        self,
        standard_ids: list[str],
        item_bank: ItemBank | None,
    ) -> list[dict[str, Any]]:
        gate_ids = ["unit_check", "solution_process"]
        if item_bank is None:
            return [
                {
                    "schema": "paideia-assessment-gate/v1",
                    "gate_id": gate_id,
                    "standard_ids": standard_ids,
                    "item_count": 0,
                    "items": [],
                }
                for gate_id in gate_ids
            ]
        return [item_bank.build_gate(gate_id, standard_ids=standard_ids) for gate_id in gate_ids]


__all__ = ["CultivationEngine"]
