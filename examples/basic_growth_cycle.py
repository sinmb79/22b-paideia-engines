from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from paideia_engines.orchestration import PaideiaEngineSuite


def main() -> None:
    suite = PaideiaEngineSuite()
    cycle = suite.run_growth_cycle(
        learner_id="agent:analyst",
        role="research analyst",
        objectives=["evidence-first answers", "safe memory use"],
        task="prepare evidence summary",
    )
    print(json.dumps(cycle, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
