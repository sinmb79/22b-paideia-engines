"""Orchestration layer for composing independent Paideia engines."""

from __future__ import annotations

from typing import Any

from paideia_engines.assessment import AssessmentEngine
from paideia_engines.contracts import ReviewLabel
from paideia_engines.cultivation import CultivationEngine
from paideia_engines.governance import GovernanceEngine
from paideia_engines.promotion import PromotionEngine
from paideia_engines.runtime import RuntimeEngine
from paideia_engines.stress import StressEngine


class PaideiaEngineSuite:
    """Compose the engines without hiding their independent APIs."""

    schema = "paideia-growth-cycle/v1"

    def __init__(
        self,
        *,
        cultivation: CultivationEngine | None = None,
        assessment: AssessmentEngine | None = None,
        stress: StressEngine | None = None,
        governance: GovernanceEngine | None = None,
        runtime: RuntimeEngine | None = None,
    ) -> None:
        self.cultivation = cultivation or CultivationEngine()
        self.assessment = assessment or AssessmentEngine()
        self.stress = stress or StressEngine()
        self.governance = governance or GovernanceEngine()
        self.runtime = runtime or RuntimeEngine()

    def run_growth_cycle(
        self,
        *,
        learner_id: str,
        role: str,
        objectives: list[str],
        task: str,
    ) -> dict[str, Any]:
        blueprint = self.cultivation.create_blueprint(
            learner_id=learner_id,
            role=role,
            objectives=objectives,
        )
        board = self.governance.create_board(program_id=f"{learner_id}:program")
        assessment = self.assessment.evaluate(
            gate_id="evidence_gate",
            submission={
                "answer": "This answer cites evidence, marks uncertainty, and includes verification checks.",
                "artifacts": ["trace.json"],
            },
        )
        governance_review = self.governance.review_action(
            action="run_local_task",
            context={"contains_private_assets": False},
        )
        runtime_run = self.runtime.run_task(
            agent_id=learner_id,
            task=task,
            tools=["read_file", "summarize", "write_report"],
        )
        stress_rollout = self.stress.run_rollout(
            learner_id=learner_id,
            scenario_id="conflicting_evidence",
            response="I will compare sources, mark uncertainty, verify the trace, and ask for review.",
        )

        promotion = PromotionEngine(owner=learner_id)
        promotion_decision = promotion.record_experience(
            source="growth_cycle",
            event={
                "summary": "Completed a local growth cycle with evidence, verification, stress rehearsal, and review gates.",
                "skills": ["evidence_review", "stress_rehearsal", "governance_check"],
            },
            review=ReviewLabel(score=92, status="verified", reviewed_by="boss_or_committee"),
        )

        return {
            "schema": self.schema,
            "learner_id": learner_id,
            "blueprint": blueprint,
            "governance_board": board,
            "assessment": assessment,
            "governance_review": governance_review,
            "runtime_run": runtime_run,
            "stress_rollout": stress_rollout,
            "promotion_decision": promotion_decision,
            "ledger": promotion.ledger,
        }


__all__ = ["PaideiaEngineSuite"]
