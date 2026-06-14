"""Curriculum mapping engine for grade, subject, and achievement standards."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class CurriculumStandard:
    standard_id: str
    school_level: str
    grade: str
    subject: str
    domain: str
    achievement: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "CurriculumStandard":
        required = ["standard_id", "school_level", "grade", "subject", "domain", "achievement"]
        missing = [key for key in required if not str(value.get(key, "")).strip()]
        if missing:
            raise ValueError(f"Missing curriculum standard fields: {', '.join(missing)}")
        return cls(
            standard_id=str(value["standard_id"]),
            school_level=str(value["school_level"]).lower(),
            grade=str(value["grade"]).lower(),
            subject=str(value["subject"]).lower(),
            domain=str(value["domain"]),
            achievement=str(value["achievement"]),
        )

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class CurriculumMappingEngine:
    """Build grade-subject units and coverage reports from achievement standards."""

    learning_unit_schema = "paideia-curriculum-learning-unit/v1"
    coverage_schema = "paideia-curriculum-coverage/v1"

    def __init__(self, standards: Iterable[dict[str, Any] | CurriculumStandard]) -> None:
        self.standards = [
            item if isinstance(item, CurriculumStandard) else CurriculumStandard.from_mapping(item)
            for item in standards
        ]

    def build_learning_unit(self, *, school_level: str, grade: str, subject: str) -> dict[str, Any]:
        normalized_level = school_level.lower()
        normalized_grade = grade.lower()
        normalized_subject = subject.lower()
        selected = [
            standard
            for standard in self.standards
            if standard.school_level == normalized_level
            and standard.grade == normalized_grade
            and standard.subject == normalized_subject
        ]
        domains = sorted({standard.domain for standard in selected})
        return {
            "schema": self.learning_unit_schema,
            "unit_id": f"{normalized_level}-grade-{normalized_grade}-{normalized_subject}",
            "school_level": normalized_level,
            "grade": normalized_grade,
            "subject": normalized_subject,
            "domains": domains,
            "standard_count": len(selected),
            "standards": [standard.to_dict() for standard in selected],
            "engine_handoffs": ["cultivation", "assessment", "stress", "promotion"],
        }

    def coverage_report(self, dataset_sources: Iterable[dict[str, Any]]) -> dict[str, Any]:
        coverage_by_source: dict[str, list[str]] = {}
        covered_ids: set[str] = set()

        for source in dataset_sources:
            source_id = str(source.get("source_id", "unknown_source"))
            matched = [
                standard.standard_id
                for standard in self.standards
                if self._source_matches_standard(source, standard)
            ]
            coverage_by_source[source_id] = matched
            covered_ids.update(matched)

        all_ids = {standard.standard_id for standard in self.standards}
        missing = sorted(all_ids - covered_ids)
        return {
            "schema": self.coverage_schema,
            "total_standard_count": len(all_ids),
            "covered_standard_count": len(covered_ids),
            "missing_standard_count": len(missing),
            "missing_standard_ids": missing,
            "coverage_by_source": coverage_by_source,
        }

    @staticmethod
    def _values(source: dict[str, Any], key: str) -> set[str]:
        value = source.get(key, [])
        if isinstance(value, str):
            return {value.lower()}
        return {str(item).lower() for item in value}

    def _source_matches_standard(self, source: dict[str, Any], standard: CurriculumStandard) -> bool:
        levels = self._values(source, "school_levels")
        subjects = self._values(source, "subjects")
        grades = self._values(source, "grades")
        level_match = "all" in levels or standard.school_level in levels
        subject_match = "all" in subjects or standard.subject in subjects
        grade_match = not grades or "all" in grades or standard.grade in grades
        return level_match and subject_match and grade_match


__all__ = ["CurriculumMappingEngine", "CurriculumStandard"]
