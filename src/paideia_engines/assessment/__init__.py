"""Assessment engine for deterministic rubric evaluation."""

from __future__ import annotations

from typing import Any

from .item_bank import AssessmentItem, ItemBank


ALLOWED_RUBRIC_CRITERIA = {"accuracy", "explanation", "process", "clarity"}
EVIDENCE_KEYWORDS = ("evidence", "uncertainty", "verify", "verification", "source", "trace", "check")


class AssessmentEngine:
    """Score submissions against a fixed rubric and build learner transcripts."""

    schema = "paideia-assessment-result/v1"
    transcript_schema = "paideia-assessment-transcript/v1"

    def __init__(self, item_bank: ItemBank | None = None) -> None:
        self.item_bank = item_bank or ItemBank()

    def evaluate(self, gate_id: str, submission: dict[str, Any]) -> dict[str, Any]:
        if not gate_id:
            raise ValueError("gate_id is required.")
        if not isinstance(submission, dict):
            raise TypeError("submission must be a mapping.")

        answer = str(submission.get("answer", "")).strip().lower()
        artifacts = submission.get("artifacts") or []
        artifact_count = len(artifacts) if isinstance(artifacts, (list, tuple)) else 0

        score = self._score(answer, artifact_count)
        passed = score >= 80
        feedback = self._feedback(answer, score, passed, artifact_count)

        return {
            "schema": self.schema,
            "gate_id": gate_id,
            "score": score,
            "passed": passed,
            "feedback": feedback,
            "evidence_weight": 0.5,
            "artifact_count": artifact_count,
        }

    def build_transcript(
        self,
        learner_id: str,
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not learner_id:
            raise ValueError("learner_id is required.")
        if not isinstance(results, list):
            raise TypeError("results must be a list.")

        normalized_results: list[dict[str, Any]] = []
        for index, item in enumerate(results):
            if not isinstance(item, dict):
                raise TypeError(f"results[{index}] must be a mapping.")
            gate_id = str(item.get("gate_id", f"gate_{index}"))
            score = self._coerce_int(item.get("score"), default=0)
            passed = bool(item.get("passed") and score >= 80)
            normalized_results.append(
                {
                    "gate_id": gate_id,
                    "passed": passed,
                    "score": score,
                }
            )

        average_score = round(
            sum(item["score"] for item in normalized_results) / max(len(normalized_results), 1),
            2,
        )
        graduation_ready = all(item["passed"] for item in normalized_results) if normalized_results else False

        return {
            "schema": self.transcript_schema,
            "learner_id": learner_id,
            "results": normalized_results,
            "average_score": average_score,
            "graduation_ready": graduation_ready,
            "transcript_status": "pass" if graduation_ready else "continue_training",
        }

    def evaluate_item_response(self, item_id: str, response: dict[str, Any]) -> dict[str, Any]:
        item = self.item_bank.get(item_id)
        answer = str(response.get("answer", "")).strip()
        explanation = str(response.get("explanation", "")).strip()
        work = str(response.get("work", "")).strip()
        score_breakdown = self._score_item_response(
            item=item,
            answer=answer,
            explanation=explanation,
            work=work,
        )
        score = min(100, sum(score_breakdown.values()))
        passed = score >= 80
        return {
            "schema": "paideia-assessment-item-result/v1",
            "item_id": item.item_id,
            "standard_id": item.standard_id,
            "gate_id": item.gate_id,
            "item_type": item.item_type,
            "score": score,
            "score_breakdown": score_breakdown,
            "passed": passed,
            "feedback": self._item_feedback(item, passed, score_breakdown),
            "review_label": {
                "score": score,
                "status": "verified" if passed else "needs_review",
                "reviewed_by": "assessment_engine",
            },
        }

    def _score(self, answer: str, artifact_count: int) -> int:
        score = 35
        answer_words = [word for word in answer.replace(".", " ").split(" ") if word]
        score += min(20, len(set(answer_words)) * 2)

        keyword_hits = {keyword for keyword in EVIDENCE_KEYWORDS if keyword in answer}
        score += min(20, len(keyword_hits) * 4)

        score += min(25, artifact_count * 20)
        if "but" in answer or "however" in answer:
            score += 5
        if artifact_count == 0:
            score = min(score, 79)
        return max(0, min(100, score))

    def _score_item_response(
        self,
        *,
        item: AssessmentItem,
        answer: str,
        explanation: str,
        work: str,
    ) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        normalized_answer = answer.strip().lower()
        expected = item.answer.strip().lower()
        rubric = item.rubric or {"accuracy": 100}
        unknown_criteria = set(rubric) - ALLOWED_RUBRIC_CRITERIA
        if unknown_criteria:
            raise ValueError(f"Unknown rubric criteria: {sorted(unknown_criteria)}")

        for criterion, weight in rubric.items():
            criterion_weight = self._coerce_int(weight)
            if criterion == "accuracy":
                breakdown[criterion] = criterion_weight if normalized_answer == expected else 0
            elif criterion == "explanation":
                text = explanation.lower()
                breakdown[criterion] = criterion_weight if text and (expected in text or "place value" in text) else 0
            elif criterion == "process":
                text = f"{work} {explanation}".lower()
                has_process = bool(text.strip()) and (
                    expected in text or "+" in text or "place" in text or "step" in text
                )
                breakdown[criterion] = criterion_weight if has_process else 0
            elif criterion == "clarity":
                text = f"{work} {explanation}".strip()
                breakdown[criterion] = min(criterion_weight, max(0, len(text.split()) * 2))
            else:
                text = f"{answer} {explanation} {work}".strip()
                breakdown[criterion] = criterion_weight if text else 0
        return breakdown

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except Exception:
            return default

    def _feedback(self, answer: str, score: int, passed: bool, artifact_count: int) -> str:
        feedback = [
            "Evidence-first rubric review completed.",
        ]
        if "evidence" in answer:
            feedback.append("Strong evidence mention detected.")
        else:
            feedback.append("Evidence coverage is weak.")

        if "uncertainty" in answer:
            feedback.append("Uncertainty handling is present.")
        else:
            feedback.append("Please mark uncertainty where knowledge is incomplete.")

        if artifact_count:
            feedback.append(f"{artifact_count} artifact(s) provided for traceability.")
        feedback.append("PASS." if passed else "RETRY required.")

        return " ".join(feedback) + f" Score={score}."

    @staticmethod
    def _item_feedback(item: AssessmentItem, passed: bool, score_breakdown: dict[str, int]) -> str:
        status = "PASS" if passed else "REVIEW"
        parts = ", ".join(f"{key}={value}" for key, value in score_breakdown.items())
        return f"{status}: {item.item_id} scored by item-bank rubric ({parts})."


__all__ = ["AssessmentEngine", "AssessmentItem", "ItemBank"]
