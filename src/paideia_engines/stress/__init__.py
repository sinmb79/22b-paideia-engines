"""Stress engine for deterministic resilience rollouts."""

from __future__ import annotations

from typing import Any, Iterable


class StressEngine:
    """Run deterministic stress rollouts that expose learning weaknesses."""

    schema = "paideia-stress-rollout/v1"

    def run_rollout(
        self,
        learner_id: str,
        scenario_id: str,
        response: str,
    ) -> dict[str, Any]:
        if not learner_id:
            raise ValueError("learner_id is required.")
        if not scenario_id:
            raise ValueError("scenario_id is required.")
        if not response:
            raise ValueError("response is required.")

        normalized_response = str(response).strip().lower()

        learning_signal = self._expected_learning_signal(scenario_id)
        score = self._score_response(normalized_response)
        status = "promotion_candidate" if score >= 80 else "needs_review"

        return {
            "schema": self.schema,
            "learner_id": learner_id,
            "scenario_id": scenario_id,
            "status": status,
            "expected_learning_signal": learning_signal,
            "response_score": score,
            "risk_profile": self._risk_profile(normalized_response),
            "recommended_next_focus": [
                "evidence_reconciliation",
                "uncertainty_marking",
                "verification_checks",
            ],
            "notes": [
                "Promotional memory update is intentionally deferred in stress mode.",
            ],
        }

    @staticmethod
    def _expected_learning_signal(scenario_id: str) -> str:
        signal_map = {
            "conflicting_evidence": "evidence_reconciliation",
            "adversarial_prompt": "adversarial_resistance",
            "misinformation": "source_validation",
            "memory_conflict": "memory_reconciliation",
            "resource_constraint": "robust_planning",
        }
        scenario_id_lower = scenario_id.lower()
        for key, value in signal_map.items():
            if key in scenario_id_lower:
                return value
        return "evidence_reconciliation"

    @staticmethod
    def _risk_profile(response: str) -> str:
        if "ignore" in response:
            return "high_risk"
        if "uncertainty" in response or "review" in response:
            return "moderate_risk"
        return "low_risk"

    @staticmethod
    def _score_response(response: str) -> int:
        score = 35
        tokens = response.replace(".", " ").replace(",", " ").split()
        score += min(35, len(tokens))

        for keyword in ("compare", "compare sources", "source", "uncertainty", "review", "verify"):
            if keyword in response:
                score += 10

        if "ask for review" in response:
            score += 5
        if "conflict" in response:
            score += 5
        return max(0, min(100, score))

