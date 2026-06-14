"""Assessment engine for deterministic rubric evaluation."""

from __future__ import annotations

from typing import Any


class AssessmentEngine:
    """Score submissions against a fixed rubric and build learner transcripts."""

    schema = "paideia-assessment-result/v1"
    transcript_schema = "paideia-assessment-transcript/v1"

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

    def _score(self, answer: str, artifact_count: int) -> int:
        score = 40
        answer_words = [word for word in answer.replace(".", " ").split(" ") if word]
        score += min(30, len(answer_words))

        for keyword in ("evidence", "uncertainty", "verify", "verification", "source", "trace", "check"):
            if keyword in answer:
                score += 7

        score += min(15, artifact_count * 5)
        if "but" in answer or "however" in answer:
            score += 5
        return max(0, min(100, score))

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

