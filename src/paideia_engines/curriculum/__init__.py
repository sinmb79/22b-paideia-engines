"""Closed-loop curriculum feedback helpers for Paideia pattern remediation."""

from .adaptive_exam import build_adaptive_exam_report, generate_adaptive_exam
from .contracts import (
    ADAPTIVE_EXAM_SCHEMA,
    CURRICULUM_PLAN_SCHEMA,
    WEAKNESS_RECORD_SCHEMA,
    AdaptiveExam,
    CurriculumPlan,
    WeaknessRecord,
)
from .curriculum_generator import build_curriculum_generation_report, generate_curriculum_plan
from .weakness_detector import (
    apply_curriculum_completion,
    build_weakness_detection_report,
    detect_weaknesses,
    weakness_blocks_direct_reuse,
    weakness_mapping_for_error,
)

__all__ = [
    "ADAPTIVE_EXAM_SCHEMA",
    "CURRICULUM_PLAN_SCHEMA",
    "WEAKNESS_RECORD_SCHEMA",
    "AdaptiveExam",
    "CurriculumPlan",
    "WeaknessRecord",
    "apply_curriculum_completion",
    "build_adaptive_exam_report",
    "build_curriculum_generation_report",
    "build_weakness_detection_report",
    "detect_weaknesses",
    "generate_adaptive_exam",
    "generate_curriculum_plan",
    "weakness_blocks_direct_reuse",
    "weakness_mapping_for_error",
]
