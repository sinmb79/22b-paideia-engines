from paideia_engines.curriculum_mapping import CurriculumMappingEngine


SAMPLE_STANDARDS = [
    {
        "standard_id": "E-MATH-03-01",
        "school_level": "elementary",
        "grade": "3",
        "subject": "math",
        "domain": "numbers_and_operations",
        "achievement": "Add and subtract within 1000 using place value.",
    },
    {
        "standard_id": "E-MATH-03-02",
        "school_level": "elementary",
        "grade": "3",
        "subject": "math",
        "domain": "fractions",
        "achievement": "Understand fractions as equal parts of a whole.",
    },
    {
        "standard_id": "M-SCI-01-01",
        "school_level": "middle",
        "grade": "1",
        "subject": "science",
        "domain": "matter",
        "achievement": "Classify substances by observable properties.",
    },
]


def test_curriculum_mapping_builds_grade_subject_learning_unit():
    engine = CurriculumMappingEngine(SAMPLE_STANDARDS)

    unit = engine.build_learning_unit(
        school_level="elementary",
        grade="3",
        subject="math",
    )

    assert unit["schema"] == "paideia-curriculum-learning-unit/v1"
    assert unit["unit_id"] == "elementary-grade-3-math"
    assert unit["standard_count"] == 2
    assert unit["engine_handoffs"] == ["cultivation", "assessment", "stress", "promotion"]
    assert {item["standard_id"] for item in unit["standards"]} == {"E-MATH-03-01", "E-MATH-03-02"}


def test_curriculum_mapping_reports_coverage_for_dataset_sources():
    engine = CurriculumMappingEngine(SAMPLE_STANDARDS)

    report = engine.coverage_report(
        [
            {
                "source_id": "aihub_math_problem_solving",
                "school_levels": ["elementary"],
                "subjects": ["math"],
                "grades": ["3"],
            },
            {
                "source_id": "ncic_curriculum_originals",
                "school_levels": ["middle"],
                "subjects": ["science"],
                "grades": ["1"],
            },
        ]
    )

    assert report["schema"] == "paideia-curriculum-coverage/v1"
    assert report["covered_standard_count"] == 3
    assert report["missing_standard_count"] == 0
    assert report["coverage_by_source"]["aihub_math_problem_solving"] == ["E-MATH-03-01", "E-MATH-03-02"]


def test_curriculum_mapping_marks_missing_standards_when_dataset_has_no_matching_grade():
    engine = CurriculumMappingEngine(SAMPLE_STANDARDS)

    report = engine.coverage_report(
        [
            {
                "source_id": "wrong_grade_math",
                "school_levels": ["elementary"],
                "subjects": ["math"],
                "grades": ["4"],
            }
        ]
    )

    assert report["covered_standard_count"] == 0
    assert report["missing_standard_count"] == 3
    assert "E-MATH-03-01" in report["missing_standard_ids"]
