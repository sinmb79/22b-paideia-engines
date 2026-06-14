"""Public engine contract registry for reusable Paideia engines."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CONTRACT_REGISTRY_SCHEMA = "paideia-engine-contract-registry/v1"
ENGINE_CONTRACT_SCHEMA = "paideia-engine-contract/v1"
CONTRACT_VALIDATION_SCHEMA = "paideia-engine-contract-validation/v1"

REQUIRED_ENGINE_NAMES = {
    "data_acquisition",
    "curriculum_mapping",
    "cultivation",
    "assessment",
    "stress",
    "promotion",
    "governance",
    "runtime",
    "orchestration",
}


@dataclass(frozen=True)
class EngineContract:
    """Stable public API and boundary record for one engine."""

    name: str
    package: str
    version: str
    status: str
    public_api: list[str]
    input_schemas: list[str]
    output_schemas: list[str]
    cli_commands: list[str]
    examples: list[str]
    docs: list[str]
    safety_boundaries: list[str]
    compatibility: str
    schema: str = ENGINE_CONTRACT_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def engine_contracts() -> list[EngineContract]:
    """Return the Phase 13 contract registry as typed records."""

    return [
        EngineContract(
            name="data_acquisition",
            package="paideia_engines.data_acquisition",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=[
                "DataAcquisitionEngine",
                "diagnose_acquired_source_manifest",
                "certify_adapters",
                "certify_adapter_matrix",
                "diagnose_source_file",
                "diagnose_source_fixture_pack",
                "parse_ncic_curriculum_csv",
                "parse_assessment_items_csv",
                "parse_aihub_math_items_json",
                "build_public_exam_metadata_manifest",
            ],
            input_schemas=[
                "paideia-source-fixture-pack/v1",
                "paideia-acquired-source/v1",
            ],
            output_schemas=[
                "paideia-data-acquisition-plan/v1",
                "paideia-acquisition-validation-report/v1",
                "paideia-acquired-source-manifest-diagnostics/v1",
                "paideia-source-fixture-pack-diagnostics/v1",
            ],
            cli_commands=["certify-adapters", "diagnose-source", "diagnose-manifest"],
            examples=[
                "examples/data_and_curriculum_pipeline.py",
                "examples/source_specific_parsers.py",
                "examples/source_fixture_pack.json",
                "examples/acquired_sources_manifest.jsonl",
                "examples/source_samples/public_assessment_sample.csv",
            ],
            docs=[
                "src/paideia_engines/data_acquisition/README.md",
                "src/paideia_engines/data_acquisition/README.ko.md",
                "docs/data_acquisition.md",
                "docs/source_parsers.md",
            ],
            safety_boundaries=[
                "local files only",
                "no automatic textbook or exam download",
                "restricted full-content records require license evidence",
                "public release blocks private paths and unsafe source records",
            ],
            compatibility="Additive changes are allowed before 1.0; breaking schema changes require a new /vN schema.",
        ),
        EngineContract(
            name="curriculum_mapping",
            package="paideia_engines.curriculum_mapping",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=["CurriculumMappingEngine", "CurriculumStandard"],
            input_schemas=["paideia-curriculum-standard/v1"],
            output_schemas=[
                "paideia-curriculum-learning-unit/v1",
                "paideia-curriculum-coverage/v1",
            ],
            cli_commands=[],
            examples=["examples/data_and_curriculum_pipeline.py"],
            docs=[
                "src/paideia_engines/curriculum_mapping/README.md",
                "src/paideia_engines/curriculum_mapping/README.ko.md",
            ],
            safety_boundaries=[
                "preserve source attribution",
                "do not infer license rights from curriculum metadata",
            ],
            compatibility="Learning-unit fields remain additive before 1.0.",
        ),
        EngineContract(
            name="cultivation",
            package="paideia_engines.cultivation",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=["CultivationEngine"],
            input_schemas=["paideia-curriculum-learning-unit/v1"],
            output_schemas=[
                "paideia-cultivation-blueprint/v1",
                "paideia-learning-roadmap/v1",
            ],
            cli_commands=["smoke"],
            examples=[
                "examples/basic_growth_cycle.py",
                "examples/assessment_and_cultivation_pipeline.py",
            ],
            docs=[
                "src/paideia_engines/cultivation/README.md",
                "src/paideia_engines/cultivation/README.ko.md",
            ],
            safety_boundaries=[
                "training plans link to validated sources",
                "roadmaps do not promote runtime memory",
            ],
            compatibility="Step names may expand, but schema names stay versioned.",
        ),
        EngineContract(
            name="assessment",
            package="paideia_engines.assessment",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=["AssessmentEngine", "AssessmentItem", "ItemBank"],
            input_schemas=["paideia-assessment-item/v1"],
            output_schemas=[
                "paideia-assessment-result/v1",
                "paideia-assessment-gate/v1",
            ],
            cli_commands=["smoke"],
            examples=[
                "examples/basic_growth_cycle.py",
                "examples/assessment_and_cultivation_pipeline.py",
            ],
            docs=[
                "src/paideia_engines/assessment/README.md",
                "src/paideia_engines/assessment/README.ko.md",
            ],
            safety_boundaries=[
                "deterministic scoring requires rubric evidence",
                "review labels are candidates until promotion review",
            ],
            compatibility="Rubric dimensions can be added without removing existing result fields.",
        ),
        EngineContract(
            name="stress",
            package="paideia_engines.stress",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=[
                "StressEngine",
                "StressScenario",
                "StressScenarioBank",
                "diagnose_stress_scenario_pack",
            ],
            input_schemas=["paideia-stress-scenario-pack/v1"],
            output_schemas=[
                "paideia-stress-rollout/v1",
                "paideia-stress-scenario-pack-diagnostics/v1",
            ],
            cli_commands=["diagnose-stress-pack", "smoke"],
            examples=[
                "examples/stress_and_promotion_pipeline.py",
                "examples/stress_packs/core_subject_stress_pack.json",
            ],
            docs=[
                "src/paideia_engines/stress/README.md",
                "src/paideia_engines/stress/README.ko.md",
            ],
            safety_boundaries=[
                "stress emits candidate-only signals",
                "stress packs cannot contain promotion decisions or ledger records",
            ],
            compatibility="Scenario packs require diagnostics pass before strict loading.",
        ),
        EngineContract(
            name="promotion",
            package="paideia_engines.promotion",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=["PromotionEngine", "PromotionLedger"],
            input_schemas=["paideia-review-label/v1"],
            output_schemas=[
                "paideia-promotion-decision/v1",
                "paideia-promotion-ledger/v1",
            ],
            cli_commands=["smoke"],
            examples=[
                "examples/basic_growth_cycle.py",
                "examples/stress_and_promotion_pipeline.py",
            ],
            docs=[
                "src/paideia_engines/promotion/README.md",
                "src/paideia_engines/promotion/README.ko.md",
            ],
            safety_boundaries=[
                "promote only verified high-quality reviews",
                "quarantined and superseded experiences remain traceable",
            ],
            compatibility="Ledger versions are append-only and never silently rewrite history.",
        ),
        EngineContract(
            name="governance",
            package="paideia_engines.governance",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=["GovernanceEngine"],
            input_schemas=["paideia-policy-check/v1"],
            output_schemas=[
                "paideia-governance-decision/v1",
                "paideia-committee-decision/v1",
            ],
            cli_commands=["smoke"],
            examples=["examples/governance_and_runtime_pipeline.py"],
            docs=[
                "src/paideia_engines/governance/README.md",
                "src/paideia_engines/governance/README.ko.md",
            ],
            safety_boundaries=[
                "external uploads blocked by default",
                "boss and license approvals stay explicit",
            ],
            compatibility="New policy checks must be additive and traceable.",
        ),
        EngineContract(
            name="runtime",
            package="paideia_engines.runtime",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=["RuntimeEngine"],
            input_schemas=["paideia-runtime-input/v1"],
            output_schemas=[
                "paideia-runtime-record/v1",
                "paideia-runtime-trace/v1",
                "paideia-artifact-manifest/v1",
            ],
            cli_commands=["smoke"],
            examples=["examples/governance_and_runtime_pipeline.py"],
            docs=[
                "src/paideia_engines/runtime/README.md",
                "src/paideia_engines/runtime/README.ko.md",
            ],
            safety_boundaries=[
                "runtime outputs require review before memory promotion",
                "artifact manifests are review evidence",
            ],
            compatibility="Persistent replay is planned before 1.0; current in-memory replay remains versioned.",
        ),
        EngineContract(
            name="orchestration",
            package="paideia_engines.orchestration",
            version="0.2",
            status="phase13_contract_frozen",
            public_api=[
                "PaideiaEngineSuite",
                "run_config_file",
                "run_engine_smoke",
                "validate_configured_suite_outputs",
                "validate_configured_suite_result",
            ],
            input_schemas=["paideia-configured-suite-config/v1"],
            output_schemas=[
                "paideia-configured-suite-run/v1",
                "paideia-cli-smoke/v1",
                "paideia-configured-suite-output-validation/v1",
            ],
            cli_commands=["run-config", "validate-suite-output", "smoke"],
            examples=[
                "examples/basic_growth_cycle.py",
                "examples/configured_suite.json",
            ],
            docs=[
                "src/paideia_engines/orchestration/README.md",
                "src/paideia_engines/orchestration/README.ko.md",
            ],
            safety_boundaries=[
                "composition must not hide engine-specific contracts",
                "suite output validation reads local JSON without rerunning engines",
            ],
            compatibility="Config fields are additive before 1.0; removed fields require a schema bump.",
        ),
    ]


def engine_contract_registry() -> dict[str, Any]:
    """Return the registry as a JSON-serializable mapping."""

    contracts = [contract.to_dict() for contract in engine_contracts()]
    return {
        "schema": CONTRACT_REGISTRY_SCHEMA,
        "version": "0.2",
        "phase": 13,
        "compatibility_policy": {
            "pre_1_0": "Additive public API and schema changes are allowed.",
            "breaking_change": "Breaking changes require a schema version bump and migration note.",
            "deprecation": "Deprecated public APIs require documentation before removal.",
        },
        "engines": contracts,
        "engine_count": len(contracts),
    }


def validate_engine_contract_registry(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Validate registry completeness against the local repository tree."""

    root = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    contracts = engine_contracts()
    issues: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    names = [contract.name for contract in contracts]
    _add_check(
        checks,
        issues,
        "required_engines_present",
        REQUIRED_ENGINE_NAMES <= set(names),
        expected=sorted(REQUIRED_ENGINE_NAMES),
        actual=sorted(names),
    )
    _add_check(
        checks,
        issues,
        "engine_names_unique",
        len(names) == len(set(names)),
        actual=sorted(names),
    )

    for contract in contracts:
        package_path = root / "src" / Path(*contract.package.split("."))
        _add_check(
            checks,
            issues,
            "package_exists",
            package_path.exists(),
            engine=contract.name,
            path=str(package_path),
        )
        _add_check(
            checks,
            issues,
            "public_api_declared",
            bool(contract.public_api),
            engine=contract.name,
        )
        _add_check(
            checks,
            issues,
            "output_schemas_declared",
            bool(contract.output_schemas),
            engine=contract.name,
        )
        _add_check(
            checks,
            issues,
            "safety_boundaries_declared",
            bool(contract.safety_boundaries),
            engine=contract.name,
        )
        for doc_path in contract.docs:
            full_path = root / doc_path
            _add_check(
                checks,
                issues,
                "contract_doc_exists",
                full_path.exists(),
                engine=contract.name,
                path=doc_path,
            )
        for example_path in contract.examples:
            full_path = root / example_path
            _add_check(
                checks,
                issues,
                "contract_example_exists",
                full_path.exists(),
                engine=contract.name,
                path=example_path,
            )

    failed = sum(1 for check in checks if not check["passed"])
    passed = len(checks) - failed
    status = "blocked" if failed else "passed"
    return {
        "schema": CONTRACT_VALIDATION_SCHEMA,
        "status": status,
        "registry_schema": CONTRACT_REGISTRY_SCHEMA,
        "repo_root": str(root),
        "summary": {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
            "engine_count": len(contracts),
        },
        "checks": checks,
        "issues": issues,
    }


def _add_check(
    checks: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    code: str,
    passed: bool,
    **details: Any,
) -> None:
    check = {"code": code, "passed": bool(passed), **details}
    checks.append(check)
    if not passed:
        issues.append(
            {
                "severity": "error",
                "code": code,
                "message": f"Engine contract check failed: {code}",
                **details,
            }
        )


__all__ = [
    "CONTRACT_REGISTRY_SCHEMA",
    "CONTRACT_VALIDATION_SCHEMA",
    "ENGINE_CONTRACT_SCHEMA",
    "EngineContract",
    "engine_contract_registry",
    "engine_contracts",
    "validate_engine_contract_registry",
]
