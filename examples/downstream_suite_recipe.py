from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from paideia_engines.orchestration import load_config, run_configured_suite


def build_recipe() -> dict[str, object]:
    """Compose the full engine suite inside another local project."""

    examples_dir = ROOT / "examples"
    config = load_config(examples_dir / "configured_suite.json")
    result = run_configured_suite(config, config_base_dir=examples_dir)
    outputs = result["outputs"]

    return {
        "schema": "paideia-downstream-suite-recipe/v1",
        "project_role": "external 22B local agent",
        "engine_mode": "configured_suite",
        "import_path": "paideia_engines.orchestration.run_configured_suite",
        "execution_trace": result["execution_trace"],
        "verification_passed": outputs["verification"]["passed"],
        "assessment_passed": outputs["assessment"]["passed"],
        "stress_signal": outputs["stress"]["promotion_signal"]["status"],
        "promotion_status": outputs["promotion"]["status"],
        "runtime_review_required": outputs["runtime"]["acceptance_checklist"]["requires_review"],
    }


def main() -> None:
    print(json.dumps(build_recipe(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
