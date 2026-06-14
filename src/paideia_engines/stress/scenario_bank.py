"""Scenario bank primitives for stress rehearsal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class StressScenario:
    """A deterministic stress scenario mapped to curriculum standards."""

    scenario_id: str
    stressor_type: str
    prompt: str
    expected_signal: str
    standard_ids: list[str]
    traps: list[str] = field(default_factory=list)
    time_limit_seconds: int | None = None
    difficulty: str = "medium"

    def __post_init__(self) -> None:
        if not self.scenario_id:
            raise ValueError("scenario_id is required.")
        if not self.stressor_type:
            raise ValueError("stressor_type is required.")
        if not self.prompt:
            raise ValueError("prompt is required.")
        if not self.expected_signal:
            raise ValueError("expected_signal is required.")
        if not self.standard_ids:
            raise ValueError("standard_ids is required.")
        if self.time_limit_seconds is not None and self.time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds must be positive when provided.")

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "stressor_type": self.stressor_type,
            "prompt": self.prompt,
            "expected_signal": self.expected_signal,
            "standard_ids": list(self.standard_ids),
            "traps": list(self.traps),
            "time_limit_seconds": self.time_limit_seconds,
            "difficulty": self.difficulty,
        }


class StressScenarioBank:
    """Index and select stress scenarios without executing promotion decisions."""

    schema = "paideia-stress-scenario-bank/v1"

    def __init__(self, scenarios: Iterable[StressScenario]) -> None:
        self._scenarios: dict[str, StressScenario] = {}
        for scenario in scenarios:
            if scenario.scenario_id in self._scenarios:
                raise ValueError(f"Duplicate stress scenario_id: {scenario.scenario_id}")
            self._scenarios[scenario.scenario_id] = scenario

    def __len__(self) -> int:
        return len(self._scenarios)

    def get(self, scenario_id: str) -> StressScenario:
        try:
            return self._scenarios[scenario_id]
        except KeyError as exc:
            raise KeyError(f"Unknown stress scenario_id: {scenario_id}") from exc

    def select(
        self,
        *,
        standard_ids: Iterable[str] | None = None,
        stressor_types: Iterable[str] | None = None,
    ) -> list[StressScenario]:
        standard_filter = set(standard_ids or [])
        stressor_filter = set(stressor_types or [])

        selected: list[StressScenario] = []
        for scenario in self._scenarios.values():
            if standard_filter and not (standard_filter & set(scenario.standard_ids)):
                continue
            if stressor_filter and scenario.stressor_type not in stressor_filter:
                continue
            selected.append(scenario)
        return selected

    def build_plan(self, standard_id: str) -> dict[str, object]:
        scenarios = self.select(standard_ids=[standard_id])
        stressor_types = sorted({scenario.stressor_type for scenario in scenarios})

        return {
            "schema": "paideia-stress-plan/v1",
            "standard_id": standard_id,
            "scenario_count": len(scenarios),
            "stressor_types": stressor_types,
            "scenarios": [scenario.to_dict() for scenario in scenarios],
            "promotion_boundary": "stress emits candidate signals only; promotion decides memory admission",
        }


__all__ = ["StressScenario", "StressScenarioBank"]
