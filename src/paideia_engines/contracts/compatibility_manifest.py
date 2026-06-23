from __future__ import annotations

from typing import Any

from paideia_engines.kibo.schema_registry import CONTRACTS_RELEASE, contract_hashes


COMPATIBILITY_MANIFEST_SCHEMA = "paideia-cross-repo-compatibility/v1"
REPO_COMPATIBILITY_RANGES = {
    "paideia_agent": ">=0.x,<1.0",
    "paideia_engines": ">=0.x,<1.0",
    "genius_derivation": ">=0.x,<1.0",
}


def cross_repo_compatibility_manifest() -> dict[str, Any]:
    return {
        "schema": COMPATIBILITY_MANIFEST_SCHEMA,
        "contracts_release": CONTRACTS_RELEASE,
        **REPO_COMPATIBILITY_RANGES,
        "contract_hashes": contract_hashes(),
    }


def validate_cross_repo_compatibility_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if manifest.get("schema") != COMPATIBILITY_MANIFEST_SCHEMA:
        issues.append({"code": "schema", "message": "unsupported compatibility manifest schema"})
    if manifest.get("contracts_release") != CONTRACTS_RELEASE:
        issues.append({"code": "contracts_release", "message": "contracts release mismatch"})
    for repo_name, expected_range in REPO_COMPATIBILITY_RANGES.items():
        if manifest.get(repo_name) != expected_range:
            issues.append({"code": "repo_compatibility", "message": f"range mismatch for {repo_name}"})
    expected_hashes = contract_hashes()
    actual_hashes = manifest.get("contract_hashes") if isinstance(manifest.get("contract_hashes"), dict) else {}
    for name, expected_hash in expected_hashes.items():
        if actual_hashes.get(name) != expected_hash:
            issues.append({"code": "contract_hash", "message": f"hash mismatch for {name}"})
    return {
        "schema": "paideia-cross-repo-compatibility-validation/v1",
        "status": "passed" if not issues else "blocked",
        "issues": issues,
    }
