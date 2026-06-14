"""Release-candidate validation for public Paideia engine builds."""

from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib
from typing import Any


RELEASE_CANDIDATE_VALIDATION_SCHEMA = "paideia-release-candidate-validation/v1"

TEXT_SUFFIXES = {".csv", ".json", ".jsonl", ".md", ".py", ".toml", ".txt"}
SCAN_DIRS = ["data", "docs", "examples", "src", "tests"]
EXCLUDED_SCAN_PARTS = {
    ".git",
    ".mypy_cache",
    ".paideia-data",
    ".paideia-runs",
    ".paideia-smoke",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}
FORBIDDEN_PUBLIC_SUFFIXES = {".hwp", ".hwpx", ".mp3", ".mp4", ".mov", ".pdf", ".wav", ".zip"}
SENSITIVE_PATTERN = re.compile(
    r"([O]PENAI_API_KEY|[A]NTHROPIC_API_KEY|[G]ITHUB_TOKEN|github[_]pat_|gh[p]_|\bsk-[A-Za-z0-9]{16,}|"
    r"[B]EGIN (RSA|OPENSSH|PRIVATE) KEY|passw[o]rd\s*=|secr[e]t\s*=)"
)
PERSONAL_PATH_PATTERN = re.compile(r"([A-Za-z]:\\[U]sers\\|/[U]sers/|/[Hh]ome/)")
PUBLIC_SAFE_CONTENT_SCOPES = {"metadata_only", "public_content", "sample_content"}

REQUIRED_RELEASE_COMMANDS = [
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


def validate_release_candidate(repo_root: str | Path = ".") -> dict[str, Any]:
    """Validate release-candidate metadata, docs, links, encoding, and public-safety gates."""

    root = Path(repo_root).resolve()
    issues: list[dict[str, Any]] = []
    checks: dict[str, bool] = {
        "pyproject_present": False,
        "project_metadata_present": False,
        "console_script_declared": False,
        "package_source_present": False,
        "release_checklist_present": False,
        "release_commands_declared": False,
        "markdown_links_resolve": False,
        "utf8_text_files_readable": False,
        "replacement_characters_absent": False,
        "sensitive_patterns_absent": False,
        "personal_paths_absent": False,
        "forbidden_public_assets_absent": False,
        "manifest_public_paths_safe": False,
        "generated_paths_ignored": False,
    }

    text_cache: dict[Path, str | None] = {}
    pyproject = root / "pyproject.toml"
    checks["pyproject_present"] = pyproject.exists()
    if not checks["pyproject_present"]:
        issues.append(_issue("error", "pyproject_missing", "pyproject.toml is required.", path=str(pyproject)))
    pyproject_data = _read_toml(pyproject, issues, text_cache)
    project = pyproject_data.get("project", {}) if isinstance(pyproject_data.get("project"), dict) else {}
    checks["project_metadata_present"] = (
        project.get("name") == "paideia-engines"
        and bool(project.get("version"))
        and bool(project.get("requires-python"))
    )
    if not checks["project_metadata_present"]:
        issues.append(_issue("error", "project_metadata_missing", "Required pyproject project metadata is missing."))
    scripts = project.get("scripts", {}) if isinstance(project.get("scripts"), dict) else {}
    checks["console_script_declared"] = scripts.get("paideia-engines") == "paideia_engines.cli:main"
    if not checks["console_script_declared"]:
        issues.append(_issue("error", "console_script_missing", "Console script entrypoint is missing."))

    package_path = root / "src" / "paideia_engines"
    checks["package_source_present"] = (package_path / "__init__.py").exists() and (package_path / "cli.py").exists()
    if not checks["package_source_present"]:
        issues.append(_issue("error", "package_source_missing", "Package source or CLI module is missing.", path=str(package_path)))

    checklist = root / "docs" / "release_checklist.md"
    checks["release_checklist_present"] = checklist.exists()
    if not checks["release_checklist_present"]:
        issues.append(_issue("error", "release_checklist_missing", "Release checklist is required.", path=str(checklist)))
    checklist_text = _read_text(checklist, issues, text_cache)
    checklist_commands = _release_command_lines(checklist_text)
    missing_commands = [command for command in REQUIRED_RELEASE_COMMANDS if not _has_release_command(checklist_commands, command)]
    checks["release_commands_declared"] = not missing_commands
    if missing_commands:
        issues.append(
            _issue(
                "error",
                "release_commands_missing",
                "Release checklist is missing required validation commands.",
                missing=missing_commands,
            )
        )

    markdown_issues = _validate_markdown_links(root, issues, text_cache)
    checks["markdown_links_resolve"] = not markdown_issues
    issues.extend(markdown_issues)

    text_files = _iter_text_files(root)
    encoding_failures = _validate_utf8(text_files, issues, text_cache)
    checks["utf8_text_files_readable"] = not encoding_failures

    replacement_issues = _scan_replacement_characters(text_files, issues, text_cache)
    checks["replacement_characters_absent"] = not replacement_issues
    issues.extend(replacement_issues)

    sensitive_issues = _scan_sensitive_patterns(text_files, issues, text_cache)
    checks["sensitive_patterns_absent"] = not sensitive_issues
    issues.extend(sensitive_issues)

    personal_path_issues = _scan_personal_paths(text_files, issues, text_cache)
    checks["personal_paths_absent"] = not personal_path_issues
    issues.extend(personal_path_issues)

    forbidden = _find_forbidden_assets(root)
    checks["forbidden_public_assets_absent"] = not forbidden
    if forbidden:
        issues.append(
            _issue(
                "error",
                "forbidden_public_assets_present",
                "Public repository paths contain forbidden asset file types.",
                files=forbidden,
            )
        )

    manifest_issues = _validate_public_manifest_paths(root, issues, text_cache)
    checks["manifest_public_paths_safe"] = not manifest_issues
    issues.extend(manifest_issues)

    gitignore_text = _read_text(root / ".gitignore", issues, text_cache)
    gitignore_patterns = _gitignore_pattern_lines(gitignore_text)
    checks["generated_paths_ignored"] = all(
        pattern in gitignore_patterns
        for pattern in ["build/", "dist/", "*.egg-info/", ".paideia-runs/", ".paideia-data/"]
    )
    if not checks["generated_paths_ignored"]:
        issues.append(_issue("error", "generated_paths_not_ignored", "Generated build/run paths must be ignored."))

    return _build_report(root=root, checks=checks, issues=issues)


def _validate_markdown_links(
    root: Path,
    shared_issues: list[dict[str, Any]],
    text_cache: dict[Path, str | None],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    markdown_files = [path for path in root.rglob("*.md") if _is_scannable(path, root)]

    for path in sorted({item.resolve() for item in markdown_files if item.exists()}):
        text = _read_text(path, shared_issues, text_cache)
        for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (path.parent / target_path).resolve()
            if not _is_relative_to(resolved, root):
                issues.append(
                    _issue(
                        "error",
                        "markdown_link_outside_repo",
                        "Markdown link points outside the repository.",
                        file=str(path),
                        target=target,
                    )
                )
            elif not resolved.exists():
                issues.append(
                    _issue(
                        "error",
                        "markdown_link_missing",
                        "Markdown link target does not exist.",
                        file=str(path),
                        target=target,
                        resolved=str(resolved),
                    )
                )
    return issues


def _validate_utf8(
    paths: list[Path],
    shared_issues: list[dict[str, Any]],
    text_cache: dict[Path, str | None],
) -> list[Path]:
    failures: list[Path] = []
    for path in paths:
        _read_text(path, shared_issues, text_cache)
        if text_cache.get(path.resolve()) is None:
            failures.append(path)
    return failures


def _scan_replacement_characters(
    paths: list[Path],
    shared_issues: list[dict[str, Any]],
    text_cache: dict[Path, str | None],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for path in paths:
        text = _read_text(path, shared_issues, text_cache)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "\ufffd" in line:
                issues.append(
                    _issue(
                        "error",
                        "replacement_character_present",
                        "Text file contains the Unicode replacement character.",
                        file=str(path),
                        line=line_number,
                    )
                )
    return issues


def _scan_sensitive_patterns(
    paths: list[Path],
    shared_issues: list[dict[str, Any]],
    text_cache: dict[Path, str | None],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for path in paths:
        text = _read_text(path, shared_issues, text_cache)
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = SENSITIVE_PATTERN.search(line)
            if match:
                issues.append(
                    _issue(
                        "error",
                        "sensitive_pattern_present",
                        "Potential credential or secret pattern found.",
                        file=str(path),
                        line=line_number,
                        pattern=match.group(1),
                    )
                )
    return issues


def _scan_personal_paths(
    paths: list[Path],
    shared_issues: list[dict[str, Any]],
    text_cache: dict[Path, str | None],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for path in paths:
        text = _read_text(path, shared_issues, text_cache)
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = PERSONAL_PATH_PATTERN.search(line)
            if match:
                issues.append(
                    _issue(
                        "error",
                        "personal_path_present",
                        "Public text contains a local personal filesystem path.",
                        file=str(path),
                        line=line_number,
                        pattern=match.group(1),
                    )
                )
    return issues


def _validate_public_manifest_paths(
    root: Path,
    shared_issues: list[dict[str, Any]],
    text_cache: dict[Path, str | None],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for manifest in _iter_jsonl_files(root):
        text = _read_text(manifest, shared_issues, text_cache)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(
                    _issue(
                        "error",
                        "manifest_jsonl_invalid",
                        "Public acquired-source manifest line is not valid JSON.",
                        file=str(manifest),
                        line=line_number,
                        error=str(exc),
                    )
                )
                continue
            if not isinstance(record, dict):
                issues.append(
                    _issue(
                        "error",
                        "manifest_record_not_mapping",
                        "Public acquired-source manifest line must contain a JSON object.",
                        file=str(manifest),
                        line=line_number,
                    )
                )
                continue
            if "local_path" not in record:
                continue
            local_path = str(record.get("local_path", ""))
            if _is_absolute_or_personal_path(local_path):
                issues.append(
                    _issue(
                        "error",
                        "manifest_private_local_path",
                        "Public acquired-source manifest must not contain private absolute local paths.",
                        file=str(manifest),
                        line=line_number,
                        local_path=local_path,
                    )
                )
            content_scope = str(record.get("content_scope", ""))
            if content_scope and content_scope not in PUBLIC_SAFE_CONTENT_SCOPES:
                issues.append(
                    _issue(
                        "error",
                        "manifest_restricted_content_scope",
                        "Public acquired-source manifest contains a restricted content scope.",
                        file=str(manifest),
                        line=line_number,
                        content_scope=content_scope,
                    )
                )
    return issues


def _find_forbidden_assets(root: Path) -> list[str]:
    files = []
    for folder_name in SCAN_DIRS:
        folder = root / folder_name
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in FORBIDDEN_PUBLIC_SUFFIXES:
                files.append(str(path.relative_to(root)))
    return sorted(files)


def _iter_jsonl_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for folder_name in SCAN_DIRS:
        folder = root / folder_name
        if folder.exists():
            paths.extend(path for path in folder.rglob("*.jsonl") if _is_scannable(path, root))
    return sorted({path.resolve() for path in paths if path.is_file()})


def _iter_text_files(root: Path) -> list[Path]:
    paths = [root / "README.md", root / "README.ko.md", root / "pyproject.toml", root / ".gitignore"]
    for folder_name in SCAN_DIRS:
        folder = root / folder_name
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and _is_scannable(path, root):
                paths.append(path)
    return sorted({path.resolve() for path in paths if path.exists()})


def _read_toml(path: Path, issues: list[dict[str, Any]], text_cache: dict[Path, str | None]) -> dict[str, Any]:
    text = _read_text(path, issues, text_cache)
    if not text:
        return {}
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        issues.append(
            _issue(
                "error",
                "pyproject_toml_invalid",
                "pyproject.toml must be valid TOML.",
                file=str(path),
                error=str(exc),
            )
        )
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_text(path: Path, issues: list[dict[str, Any]], text_cache: dict[Path, str | None]) -> str:
    resolved = path.resolve()
    if resolved in text_cache:
        return text_cache[resolved] or ""
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        issues.append(
            _issue(
                "error",
                "utf8_decode_failed",
                "Text file must be readable as UTF-8.",
                file=str(path),
                error=str(exc),
            )
        )
        text_cache[resolved] = None
        return ""
    text_cache[resolved] = text
    return text


def _release_command_lines(text: str) -> set[str]:
    return {line.strip() for line in text.splitlines() if line.strip().startswith("python ")}


def _has_release_command(command_lines: set[str], required_command: str) -> bool:
    return any(line == required_command or line.startswith(f"{required_command} ") for line in command_lines)


def _gitignore_pattern_lines(text: str) -> set[str]:
    return {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def _is_scannable(path: Path, root: Path) -> bool:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return False
    return not any(part in EXCLUDED_SCAN_PARTS or part.endswith(".egg-info") for part in parts)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _is_absolute_or_personal_path(value: str) -> bool:
    if not value:
        return False
    normalized = value.replace("/", "\\")
    return (
        bool(re.match(r"^[A-Za-z]:\\", normalized))
        or value.startswith("/")
        or PERSONAL_PATH_PATTERN.search(value) is not None
    )


def _build_report(root: Path, checks: dict[str, bool], issues: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for value in checks.values() if value is not True)
    return {
        "schema": RELEASE_CANDIDATE_VALIDATION_SCHEMA,
        "status": _status_from_issues(issues),
        "repo_root": str(root),
        "summary": {
            "total": len(checks),
            "passed": len(checks) - failed,
            "failed": failed,
            "blocked": sum(1 for issue in issues if issue["severity"] == "error"),
            "review_required": sum(1 for issue in issues if issue["severity"] == "warning"),
        },
        "checks": checks,
        "issues": issues,
    }


def _issue(severity: str, code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {
        "severity": severity,
        "category": extra.pop("category", _category_for_code(code)),
        "code": code,
        "message": message,
        **extra,
    }


def _category_for_code(code: str) -> str:
    if code.startswith("markdown_"):
        return "documentation"
    if code.startswith("utf8_") or code.startswith("replacement_"):
        return "encoding"
    if code.startswith("sensitive_") or code.startswith("personal_"):
        return "secrets"
    if code.startswith("forbidden_") or code.startswith("manifest_"):
        return "public_assets"
    if code.startswith("release_"):
        return "release_process"
    if code.startswith(("pyproject_", "project_", "console_", "package_", "generated_")):
        return "packaging"
    return "release_candidate"


def _status_from_issues(issues: list[dict[str, Any]]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "blocked"
    if any(issue["severity"] == "warning" for issue in issues):
        return "review_required"
    return "passed"


__all__ = [
    "RELEASE_CANDIDATE_VALIDATION_SCHEMA",
    "validate_release_candidate",
]
