from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paideia_engines.governance import GovernanceEngine
from paideia_engines.runtime import RuntimeEngine


def main() -> None:
    governance = GovernanceEngine()
    blocked_source = governance.evaluate_policy(
        action="use_dataset",
        context={
            "source_id": "textbook:math-grade-3",
            "license_tier": "manual_license_required",
            "intended_use": "local_training",
        },
    )
    approval = governance.record_approval(
        approval_type="license_approval",
        subject_id="textbook:math-grade-3",
        approved_by="boss",
        scope={"source_id": "textbook:math-grade-3", "allowed_use": "local_training"},
        notes="Local-only use after manual license review.",
    )
    approved_source = governance.evaluate_policy(
        action="use_dataset",
        context={
            "source_id": "textbook:math-grade-3",
            "license_tier": "manual_license_required",
            "intended_use": "local_training",
        },
    )
    committee_decision = governance.record_committee_decision(
        committee="oversight_committee",
        subject_id="runtime:agent:math",
        decision="approved_for_local_run",
        reviewers=["boss", "education_lead"],
        rationale="The run stays local and has a traceable artifact manifest.",
    )

    runtime = RuntimeEngine(engine_id="runtime:math")
    run = runtime.run_task(
        agent_id="agent:math",
        task="prepare local evidence summary",
        tools=["read_file", "summarize", "write_report"],
        artifacts=[
            {"path": "reports/math-evidence.json", "kind": "evidence"},
            {"path": "traces/math-runtime.json", "kind": "trace"},
        ],
    )
    replay = runtime.replay_trace(run["run_id"])

    print(
        json.dumps(
            {
                "blocked_source": blocked_source,
                "approval": approval,
                "approved_source": approved_source,
                "committee_decision": committee_decision,
                "runtime_run": run,
                "runtime_replay": replay,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
