from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_acquisition.source_parsers import (
    build_public_exam_metadata_manifest,
    parse_aihub_math_items_json,
    parse_ncic_curriculum_csv,
)
from paideia_engines.data_catalog import default_seed_catalog


def main() -> None:
    samples = ROOT / "examples" / "source_samples"
    standards = parse_ncic_curriculum_csv(samples / "ncic_curriculum_sample.csv", standard_version="2022")
    item_bank = parse_aihub_math_items_json(samples / "aihub_math_sample.json")
    exam_manifest = build_public_exam_metadata_manifest(
        samples / "ebsi_exam_metadata_sample.csv",
        approved_by="example",
    )
    acquisition = DataAcquisitionEngine(default_seed_catalog(), storage_root=ROOT / ".paideia-data")
    validation = acquisition.validate_acquired_sources(exam_manifest)

    print(
        json.dumps(
            {
                "standards": [standard.to_dict() for standard in standards],
                "item_gate": item_bank.build_gate("aihub_math_solution"),
                "exam_metadata_validation": validation,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
