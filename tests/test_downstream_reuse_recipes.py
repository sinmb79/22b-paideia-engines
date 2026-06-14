import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _python_with_pip() -> list[str]:
    candidates = []
    if os.environ.get("PAIDEIA_TEST_PYTHON_WITH_PIP"):
        candidates.append([os.environ["PAIDEIA_TEST_PYTHON_WITH_PIP"]])
    candidates.extend(
        [
            [sys.executable],
            ["py", "-3.11"],
            ["py", "-3.12"],
            ["python"],
        ]
    )
    for candidate in candidates:
        try:
            completed = subprocess.run(
                [*candidate, "-m", "pip", "--version"],
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError:
            continue
        if completed.returncode == 0:
            return candidate
    pytest.skip("No Python interpreter with pip is available for downstream installed-package smoke.")


@pytest.fixture(scope="module")
def installed_package(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    tmp_path = tmp_path_factory.mktemp("downstream-installed")
    python_cmd = _python_with_pip()
    wheel_dir = tmp_path / "dist"
    venv_dir = tmp_path / "venv"
    downstream_dir = tmp_path / "downstream-project"
    downstream_dir.mkdir()
    subprocess.run(
        [
            *python_cmd,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(wheel_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    wheel = next(wheel_dir.glob("paideia_engines-*.whl"))
    try:
        subprocess.run(
            [*python_cmd, "-m", "venv", str(venv_dir)],
            cwd=tmp_path,
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        pytest.skip(f"Could not create downstream smoke venv: {exc.stderr}")
    scripts_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    venv_python = scripts_dir / ("python.exe" if os.name == "nt" else "python")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheel), "--no-deps"],
        cwd=downstream_dir,
        text=True,
        capture_output=True,
        check=True,
    )
    return {
        "python": venv_python,
        "downstream_dir": downstream_dir,
    }


def _run_example(installed_package: dict[str, Path], relative_path: str) -> dict[str, object]:
    script_path = ROOT / relative_path
    completed = subprocess.run(
        [str(installed_package["python"]), str(script_path)],
        cwd=installed_package["downstream_dir"],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_downstream_single_engine_recipe_promotes_only_verified_memory(installed_package):
    payload = _run_example(installed_package, "examples/downstream_single_engine_recipe.py")

    assert payload["schema"] == "paideia-downstream-single-engine-recipe/v1"
    assert payload["engine"] == "promotion"
    assert payload["promoted_status"] == "promoted"
    assert payload["quarantined_status"] == "quarantined"
    assert payload["quarantined_policy"] == "excluded"
    assert payload["active_memory_matched"] == 1


def test_downstream_suite_recipe_composes_full_engine_trace(installed_package):
    payload = _run_example(installed_package, "examples/downstream_suite_recipe.py")

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
        "governance",
        "runtime",
        "promotion",
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
