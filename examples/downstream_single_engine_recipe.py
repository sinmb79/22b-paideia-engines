from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paideia_engines.contracts import ReviewLabel
from paideia_engines.promotion import PromotionEngine


def build_recipe() -> dict[str, object]:
    """Use one engine as a small memory promotion gate in another project."""

    promotion = PromotionEngine(owner="agent:downstream")
    promoted = promotion.record_experience(
        source="external_project:reporting",
        event={
            "summary": "Verified local report writing workflow with retained evidence.",
            "skills": ["reporting", "evidence_review", "local_first"],
        },
        review=ReviewLabel(score=91, status="verified", reviewed_by="boss"),
    )
    quarantined = promotion.record_experience(
        source="external_project:trial",
        event={
            "summary": "Draft workflow without enough evidence.",
            "skills": ["drafting"],
        },
        review=ReviewLabel(score=54, status="needs_review", reviewed_by="committee"),
    )
    route = promotion.route_active_memory("reporting evidence local_first")

    return {
        "schema": "paideia-downstream-single-engine-recipe/v1",
        "project_role": "external 22B local agent",
        "engine": "promotion",
        "import_path": "paideia_engines.promotion.PromotionEngine",
        "promoted_status": promoted["status"],
        "quarantined_status": quarantined["status"],
        "active_memory_matched": route["matched"],
        "quarantined_policy": route["quarantined_experiences"],
        "ledger_version": promotion.ledger["version"],
    }


def main() -> None:
    print(json.dumps(build_recipe(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
