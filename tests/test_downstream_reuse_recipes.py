import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict[str, str]:
    env = dict(os.environ)
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _run_example(relative_path: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, relative_path],
        cwd=ROOT,
        env=_env(),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_downstream_single_engine_recipe_promotes_only_verified_memory():
    payload = _run_example("examples/downstream_single_engine_recipe.py")

    assert payload["schema"] == "paideia-downstream-single-engine-recipe/v1"
    assert payload["engine"] == "promotion"
    assert payload["promoted_status"] == "promoted"
    assert payload["quarantined_status"] == "quarantined"
    assert payload["quarantined_policy"] == "excluded"
    assert payload["active_memory_matched"] == 1


def test_downstream_suite_recipe_composes_full_engine_trace():
    payload = _run_example("examples/downstream_suite_recipe.py")

    assert payload["schema"] == "paideia-downstream-suite-recipe/v1"
    assert payload["engine_mode"] == "configured_suite"
    assert payload["verification_passed"] is True
    assert payload["assessment_passed"] is True
    assert payload["stress_signal"] == "candidate_only"
    assert payload["promotion_status"] == "promoted"
    assert payload["runtime_review_required"] is True
    assert payload["execution_trace"] == [
        "data_acquisition",
        "acquisition_validation",
        "curriculum_mapping",
        "cultivation",
        "assessment",
        "stress",
        "promotion",
        "governance",
        "runtime",
        "verification",
    ]


def test_downstream_reuse_docs_are_bilingual_and_linked():
    english = (ROOT / "docs" / "downstream_reuse_recipes.md").read_text(encoding="utf-8")
    korean = (ROOT / "docs" / "downstream_reuse_recipes.ko.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_ko = (ROOT / "README.ko.md").read_text(encoding="utf-8")

    assert "[한국어](downstream_reuse_recipes.ko.md)" in english
    assert "[English](downstream_reuse_recipes.md)" in korean
    assert "[Downstream reuse recipes](docs/downstream_reuse_recipes.md)" in readme
    assert "[Downstream 재사용 레시피](docs/downstream_reuse_recipes.ko.md)" in readme_ko
