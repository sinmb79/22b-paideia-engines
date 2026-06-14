from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paideia_engines.curriculum_mapping import CurriculumMappingEngine
from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_catalog import default_seed_catalog


def main() -> None:
    catalog = default_seed_catalog()
    acquisition = DataAcquisitionEngine(catalog, storage_root=ROOT / "data")
    assessment_plan = acquisition.build_engine_plan("assessment")

    standards = json.loads((ROOT / "data" / "curriculum" / "sample_standards.json").read_text(encoding="utf-8"))
    mapping = CurriculumMappingEngine(standards)
    learning_unit = mapping.build_learning_unit(
        school_level="elementary",
        grade="3",
        subject="math",
    )
    coverage = mapping.coverage_report(
        [
            {
                "source_id": "aihub_math_problem_solving",
                "school_levels": ["elementary"],
                "subjects": ["math"],
                "grades": ["3"],
            }
        ]
    )

    print(
        json.dumps(
            {
                "assessment_data_plan": assessment_plan,
                "learning_unit": learning_unit,
                "coverage": coverage,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
