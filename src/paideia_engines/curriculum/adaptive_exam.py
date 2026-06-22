from __future__ import annotations

import hashlib
from typing import Any

from .contracts import AdaptiveExam, CurriculumPlan, WeaknessRecord


ADAPTIVE_EXAM_GENERATION_SCHEMA = "paideia-adaptive-exam-generation-report/v1"


def generate_adaptive_exam(
    curriculum: CurriculumPlan,
    *,
    weakness: WeaknessRecord | None = None,
    recent_improvement: bool = False,
) -> AdaptiveExam:
    difficulty = _difficulty(weakness, recent_improvement=recent_improvement)
    question_count = _question_count(weakness, recent_improvement=recent_improvement)
    seeds = list(curriculum.learning_goals or curriculum.lesson_units or ("target_skill",))
    questions: list[str] = []
    for index in range(question_count):
        topic = seeds[index % len(seeds)]
        if difficulty == "maintenance":
            prompt = f"Maintenance check {index + 1}: apply {topic} and state the verification signal."
        elif difficulty == "advanced":
            prompt = f"Advanced transfer {index + 1}: solve a novel case requiring {topic} and one counterargument."
        elif difficulty == "remediation":
            prompt = f"Remediation {index + 1}: identify the prior failure trigger for {topic} and prevent it."
        else:
            prompt = f"Standard application {index + 1}: use {topic} with evidence and risk checks."
        questions.append(prompt)
    return AdaptiveExam(
        exam_id=_stable_id("adaptive-exam", curriculum.curriculum_id, difficulty, question_count),
        curriculum_id=curriculum.curriculum_id,
        difficulty=difficulty,
        questions=tuple(questions),
    )


def build_adaptive_exam_report(
    curriculum: CurriculumPlan,
    *,
    weakness: WeaknessRecord | None = None,
    recent_improvement: bool = False,
) -> dict[str, Any]:
    exam = generate_adaptive_exam(
        curriculum,
        weakness=weakness,
        recent_improvement=recent_improvement,
    )
    return {
        "schema": ADAPTIVE_EXAM_GENERATION_SCHEMA,
        "exam": exam.to_dict(),
        "policy": {
            "higher_severity_gets_more_questions": True,
            "repeated_failure_increases_difficulty": True,
            "recent_improvement_uses_maintenance_exam": recent_improvement,
        },
    }


def _difficulty(weakness: WeaknessRecord | None, *, recent_improvement: bool) -> str:
    if recent_improvement:
        return "maintenance"
    if weakness is None:
        return "standard"
    if weakness.recurrence_count >= 3:
        return "remediation"
    if weakness.severity >= 0.8:
        return "advanced"
    return "standard"


def _question_count(weakness: WeaknessRecord | None, *, recent_improvement: bool) -> int:
    if recent_improvement:
        return 3
    if weakness is None:
        return 4
    count = 3
    if weakness.severity >= 0.6:
        count += 1
    if weakness.severity >= 0.8:
        count += 1
    count += min(3, max(0, weakness.recurrence_count - 1))
    return count


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
