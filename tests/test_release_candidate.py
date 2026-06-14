import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from paideia_engines.release_candidate import validate_release_candidate


ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_repo(tmp_path: Path, *, readme: str) -> Path:
    _write(
        tmp_path / "pyproject.toml",
        """
[project]
name = "paideia-engines"
version = "0.2.0"
requires-python = ">=3.11"

[project.scripts]
paideia-engines = "paideia_engines.cli:main"
""",
    )
    _write(tmp_path / ".gitignore", "build/\ndist/\n*.egg-info/\n.paideia-runs/\n.paideia-data/\n")
    _write(tmp_path / "README.md", readme)
    _write(tmp_path / "README.ko.md", "[English](README.md)\n")
    _write(tmp_path / "src" / "paideia_engines" / "__init__.py", "")
    _write(tmp_path / "src" / "paideia_engines" / "cli.py", "")
    _write(
        tmp_path / "docs" / "release_checklist.md",
        "\n".join(
            [
                "python -m pytest tests -q",
                "python -m compileall src",
                "python -m paideia_engines.cli validate-contracts",
                "python -m paideia_engines.cli certify-adapters",
                "python -m paideia_engines.cli diagnose-source",
                "python -m paideia_engines.cli diagnose-manifest",
                "python -m paideia_engines.cli diagnose-stress-pack",
                "python -m paideia_engines.cli run-config",
                "python -m paideia_engines.cli validate-suite-output",
                "python -m paideia_engines.cli persist-runtime-evidence",
                "python -m paideia_engines.cli validate-runtime-evidence",
                "python -m paideia_engines.cli replay-runtime-evidence",
                "python -m paideia_engines.cli smoke",
                "python -m paideia_engines.cli validate-benchmarks",
                "python -m paideia_engines.cli validate-release-candidate",
            ]
        ),
    )
    return tmp_path


def _issue_codes(report: dict[str, object]) -> set[str]:
    return {str(issue["code"]) for issue in report["issues"]}


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
    pytest.skip("No Python interpreter with pip is available for wheel install smoke.")


def test_release_candidate_validation_passes_current_repo():
    report = validate_release_candidate(ROOT)

    assert report["schema"] == "paideia-release-candidate-validation/v1"
    assert report["status"] == "passed"
    assert report["summary"]["failed"] == 0
    assert report["checks"]["markdown_links_resolve"] is True
    assert report["checks"]["replacement_characters_absent"] is True
    assert report["checks"]["sensitive_patterns_absent"] is True
    assert report["checks"]["personal_paths_absent"] is True
    assert report["checks"]["manifest_public_paths_safe"] is True


def test_release_candidate_validation_blocks_missing_markdown_links(tmp_path):
    repo = _minimal_repo(tmp_path, readme="[Missing](docs/missing.md)\n")

    report = validate_release_candidate(repo)

    assert report["status"] == "blocked"
    assert "markdown_link_missing" in _issue_codes(report)


def test_release_candidate_validation_blocks_sensitive_patterns(tmp_path):
    sensitive_name = "OPENAI" + "_API_KEY=placeholder"
    repo = _minimal_repo(tmp_path, readme=f"{sensitive_name}\n")

    report = validate_release_candidate(repo)

    assert report["status"] == "blocked"
    assert "sensitive_pattern_present" in _issue_codes(report)


def test_release_candidate_validation_blocks_personal_paths(tmp_path):
    personal_path = "C:" + "\\Users\\boss\\private-textbook.pdf"
    repo = _minimal_repo(tmp_path, readme=f"{personal_path}\n")

    report = validate_release_candidate(repo)

    assert report["status"] == "blocked"
    assert "personal_path_present" in _issue_codes(report)


def test_release_candidate_validation_blocks_manifest_private_paths(tmp_path):
    repo = _minimal_repo(tmp_path, readme="[Korean](README.ko.md)\n")
    private_path = "C:" + "\\Users\\boss\\licensed\\math.pdf"
    _write(
        repo / "examples" / "acquired_sources_manifest.jsonl",
        json.dumps(
            {
                "schema": "paideia-acquired-source/v1",
                "source_id": "private_textbook",
                "content_scope": "restricted_textbook",
                "local_path": private_path,
            },
            ensure_ascii=False,
        )
        + "\n",
    )

    report = validate_release_candidate(repo)

    assert report["status"] == "blocked"
    assert {"manifest_private_local_path", "manifest_restricted_content_scope"} <= _issue_codes(report)


def test_release_candidate_validation_blocks_invalid_manifest_jsonl(tmp_path):
    repo = _minimal_repo(tmp_path, readme="[Korean](README.ko.md)\n")
    _write(repo / "examples" / "acquired_sources_manifest.jsonl", '{"local_path": "sample.csv"\n')

    report = validate_release_candidate(repo)

    assert report["status"] == "blocked"
    assert "manifest_jsonl_invalid" in _issue_codes(report)


def test_release_candidate_validation_blocks_replacement_characters(tmp_path):
    repo = _minimal_repo(tmp_path, readme="Broken \ufffd text\n")

    report = validate_release_candidate(repo)

    assert report["status"] == "blocked"
    assert "replacement_character_present" in _issue_codes(report)


def test_cli_validate_release_candidate_returns_nonzero_when_blocked(tmp_path):
    repo = _minimal_repo(tmp_path / "repo", readme="[Missing](docs/missing.md)\n")
    output_path = tmp_path / "blocked-release-candidate.json"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "paideia_engines.cli",
            "validate-release-candidate",
            "--repo-root",
            str(repo),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert completed.returncode == 1
    assert payload["status"] == "blocked"
    assert "markdown_link_missing" in _issue_codes(payload)


def test_wheel_install_smoke_runs_cli_from_installed_package(tmp_path):
    python_cmd = _python_with_pip()
    wheel_dir = tmp_path / "dist"
    venv_dir = tmp_path / "venv"
    output_path = tmp_path / "installed-smoke-console.json"
    module_output_path = tmp_path / "installed-smoke-module.json"
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
        pytest.skip(f"Could not create wheel smoke venv: {exc.stderr}")

    scripts_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    venv_python = scripts_dir / ("python.exe" if os.name == "nt" else "python")
    console_script = scripts_dir / ("paideia-engines.exe" if os.name == "nt" else "paideia-engines")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheel), "--no-deps"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            str(console_script),
            "smoke",
            "--engine",
            "runtime",
            "--output",
            str(output_path),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "paideia_engines.cli",
            "smoke",
            "--engine",
            "runtime",
            "--output",
            str(module_output_path),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    module_payload = json.loads(module_output_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "paideia-cli-smoke/v1"
    assert payload["summary"]["failed"] == 0
    assert module_payload["schema"] == "paideia-cli-smoke/v1"
    assert module_payload["summary"]["failed"] == 0
