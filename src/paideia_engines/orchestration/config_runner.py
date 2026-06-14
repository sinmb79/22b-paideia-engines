"""Config-driven orchestration runner for Paideia engine suites."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paideia_engines.assessment import AssessmentEngine
from paideia_engines.assessment.item_bank import AssessmentItem, ItemBank
from paideia_engines.contracts import ReviewLabel
from paideia_engines.cultivation import CultivationEngine
from paideia_engines.curriculum_mapping import CurriculumMappingEngine
from paideia_engines.data_acquisition import DataAcquisitionEngine
from paideia_engines.data_acquisition.source_parsers import (
    parse_aihub_math_items_json,
    parse_assessment_items_csv,
    parse_ncic_curriculum_csv,
)
from paideia_engines.data_catalog import default_seed_catalog
from paideia_engines.governance import GovernanceEngine
from paideia_engines.promotion import PromotionEngine
from paideia_engines.runtime import RuntimeEngine
from paideia_engines.stress import StressEngine
from paideia_engines.stress.scenario_bank import StressScenario, StressScenarioBank


EXECUTION_TRACE = [
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

SMOKE_ENGINES = [
    "data_acquisition",
    "curriculum_mapping",
    "cultivation",
    "assessment",
    "stress",
    "promotion",
    "governance",
    "runtime",
    "orchestration",
]

CONFIGURED_SUITE_SCHEMA = "paideia-configured-suite/v1"
CONFIGURED_SUITE_RUN_SCHEMA = "paideia-configured-suite-run/v1"
CONFIGURED_SUITE_TRACE_SCHEMA = "paideia-configured-suite-trace/v2"
VALID_CONFIG_MODES = {"demo", "production"}
PRODUCTION_REQUIRED_FIELDS = {
    "data": ("engine",),
    "learner": ("learner_id", "role", "objectives", "task"),
    "curriculum": ("school_level", "grade", "subject"),
    "assessment": ("item_id", "items_path", "parser", "answer", "explanation"),
    "stress": ("scenario_id", "response"),
    "runtime": ("tools",),
    "governance": ("action", "context"),
}


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    return json.loads(config_path.read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> str:
    output_path = Path(path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return str(output_path)


def _default_standards() -> list[dict[str, Any]]:
    return [
        {
            "standard_id": "E-MATH-03-01",
            "school_level": "elementary",
            "grade": "3",
            "subject": "math",
            "domain": "numbers_and_operations",
            "achievement": "Add and subtract within 1000 using place value.",
        }
    ]


def _config_section(config: dict[str, Any], section: str) -> dict[str, Any]:
    value = config.get(section, {})
    if not isinstance(value, dict):
        raise TypeError(f"config.{section} must be a mapping.")
    return value


def _config_mode(config: dict[str, Any]) -> str:
    mode = str(config.get("mode", "demo")).strip().lower()
    if mode not in VALID_CONFIG_MODES:
        allowed = ", ".join(sorted(VALID_CONFIG_MODES))
        raise ValueError(f"config.mode must be one of: {allowed}.")
    return mode


def _is_missing_required_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def _validate_production_config(config: dict[str, Any]) -> None:
    if config.get("schema") != CONFIGURED_SUITE_SCHEMA:
        raise ValueError(f"production config requires schema {CONFIGURED_SUITE_SCHEMA}.")

    for section, fields in PRODUCTION_REQUIRED_FIELDS.items():
        section_config = _config_section(config, section)
        for field in fields:
            if field not in section_config or _is_missing_required_value(section_config[field]):
                raise ValueError(f"production config requires config.{section}.{field}.")

    data_config = _config_section(config, "data")
    if _is_missing_required_value(data_config.get("acquired_sources")) and _is_missing_required_value(
        data_config.get("manifest_path")
    ):
        raise ValueError("production config requires config.data.acquired_sources or config.data.manifest_path.")

    curriculum_config = _config_section(config, "curriculum")
    if _is_missing_required_value(curriculum_config.get("standards")) and _is_missing_required_value(
        curriculum_config.get("standards_path")
    ):
        raise ValueError("production config requires config.curriculum.standards or config.curriculum.standards_path.")

    governance_config = _config_section(config, "governance")
    if not isinstance(governance_config.get("context"), dict):
        raise TypeError("production config.governance.context must be a mapping.")


def _learner_config(config: dict[str, Any]) -> dict[str, Any]:
    learner = _config_section(config, "learner")
    return {
        "learner_id": str(learner.get("learner_id", "agent:demo")),
        "role": str(learner.get("role", "local analyst")),
        "objectives": [str(item) for item in learner.get("objectives", ["evidence-first answers"])],
        "task": str(learner.get("task", "prepare evidence summary")),
    }


def _resolve_config_path(path_value: Any, base_dir: str | Path | None) -> Path:
    path = Path(str(path_value))
    if base_dir is not None and not path.is_absolute():
        path = Path(base_dir) / path
    return path.resolve()


def _validated_adapter_record(
    path: Path,
    config_key: str,
    validation_report: dict[str, Any],
) -> dict[str, Any]:
    resolved = str(path.resolve())
    for validation in validation_report.get("validations", []):
        if not isinstance(validation, dict) or validation.get("status") != "passed":
            continue
        if str(Path(str(validation.get("local_path", ""))).resolve()) == resolved:
            return validation
    raise PermissionError(
        f"config.{config_key} must point to a path that passed acquired-source validation."
    )


def _require_parser_source(
    parser: str,
    validation: dict[str, Any],
    allowed_source_ids: set[str],
) -> None:
    source_id = str(validation.get("source_id", ""))
    if source_id not in allowed_source_ids:
        allowed = ", ".join(sorted(allowed_source_ids))
        raise PermissionError(f"parser {parser} requires one of: {allowed}.")


def _validation_metadata(validation: dict[str, Any], *keys: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for key in keys:
        value = validation.get(key)
        if value not in (None, ""):
            metadata[key] = str(value)
    return metadata


def _build_item_bank(
    config: dict[str, Any],
    standards: list[dict[str, Any]],
    *,
    config_base_dir: str | Path | None,
    acquisition_validation: dict[str, Any],
) -> ItemBank:
    assessment_config = _config_section(config, "assessment")
    items_path = assessment_config.get("items_path")
    if items_path:
        resolved_path = _resolve_config_path(items_path, config_base_dir)
        validation = _validated_adapter_record(
            resolved_path,
            "assessment.items_path",
            acquisition_validation,
        )
        parser = str(assessment_config.get("parser", "paideia_json"))
        if parser == "paideia_json":
            _require_parser_source(
                parser,
                validation,
                {"moe_csat_example_items", "aihub_math_problem_solving", "aihub_grade_subject_textbook_data"},
            )
            return ItemBank.from_file(resolved_path)
        if parser == "aihub_json":
            _require_parser_source(parser, validation, {"aihub_math_problem_solving"})
            return parse_aihub_math_items_json(
                resolved_path,
                **_validation_metadata(validation, "source_id", "provider", "source_url", "license_tier"),
            )
        if parser == "aihub_csv":
            _require_parser_source(parser, validation, {"aihub_math_problem_solving"})
            return parse_assessment_items_csv(
                resolved_path,
                **_validation_metadata(validation, "source_id", "provider", "source_url", "license_tier"),
            )
        if parser == "public_assessment_csv":
            _require_parser_source(parser, validation, {"moe_csat_example_items"})
            return parse_assessment_items_csv(
                resolved_path,
                **_validation_metadata(validation, "source_id", "provider", "source_url", "license_tier"),
            )
        raise ValueError(f"Unknown assessment parser: {parser}")

    configured_items = assessment_config.get("items")
    if isinstance(configured_items, list) and configured_items:
        return ItemBank([ItemBank._item_from_mapping(dict(item)) for item in configured_items])

    standard_id = str(standards[0].get("standard_id", "E-MATH-03-01")) if standards else "E-MATH-03-01"
    return ItemBank(
        [
            AssessmentItem(
                item_id="phase5-default-item",
                standard_id=standard_id,
                gate_id="unit_check",
                item_type="short_answer",
                prompt="What is 245 + 130?",
                answer="375",
                distractors=["365", "475"],
                explanation="245 + 130 = 375 by place value.",
                rubric={"accuracy": 80, "explanation": 20},
            )
        ]
    )


def _load_standards(
    curriculum_config: dict[str, Any],
    *,
    config_base_dir: str | Path | None,
    acquisition_validation: dict[str, Any],
) -> list[dict[str, Any]]:
    standards_path = curriculum_config.get("standards_path")
    if standards_path:
        resolved_path = _resolve_config_path(standards_path, config_base_dir)
        validation = _validated_adapter_record(
            resolved_path,
            "curriculum.standards_path",
            acquisition_validation,
        )
        parser = str(curriculum_config.get("parser", "paideia_json"))
        if parser == "paideia_json":
            _require_parser_source(
                parser,
                validation,
                {"ncic_curriculum_originals", "data_go_kr_ncic_curriculum"},
            )
            return [
                standard.to_dict()
                for standard in CurriculumMappingEngine.load_standards_file(resolved_path)
            ]
        if parser in {"ncic_csv", "data_go_kr_csv"}:
            _require_parser_source(
                parser,
                validation,
                {"ncic_curriculum_originals", "data_go_kr_ncic_curriculum"},
            )
            return [
                standard.to_dict()
                for standard in parse_ncic_curriculum_csv(
                    resolved_path,
                    **_validation_metadata(validation, "source_id", "provider", "source_url", "license_tier"),
                )
            ]
        raise ValueError(f"Unknown curriculum parser: {parser}")
    return list(curriculum_config.get("standards") or _default_standards())


def _validate_configured_sources(
    data_engine: DataAcquisitionEngine,
    data_config: dict[str, Any],
    *,
    config_base_dir: str | Path | None,
) -> dict[str, Any]:
    manifest_path = data_config.get("manifest_path")
    if manifest_path:
        return data_engine.validate_manifest(_resolve_config_path(manifest_path, config_base_dir))

    acquired_sources = data_config.get("acquired_sources", [])
    if acquired_sources is None:
        acquired_sources = []
    if not isinstance(acquired_sources, list):
        raise TypeError("config.data.acquired_sources must be a list.")
    normalized_sources: list[dict[str, Any]] = []
    for item in acquired_sources:
        if not isinstance(item, dict):
            raise TypeError("config.data.acquired_sources items must be mappings.")
        record = dict(item)
        if record.get("local_path"):
            record["local_path"] = str(_resolve_config_path(record["local_path"], config_base_dir))
        if record.get("license_note_path"):
            record["license_note_path"] = str(
                _resolve_config_path(record["license_note_path"], config_base_dir)
            )
        normalized_sources.append(record)
    return data_engine.validate_acquired_sources(normalized_sources)


def _build_stress_bank(config: dict[str, Any], standards: list[dict[str, Any]]) -> StressScenarioBank:
    stress_config = _config_section(config, "stress")
    configured_scenarios = stress_config.get("scenarios")
    if isinstance(configured_scenarios, list) and configured_scenarios:
        return StressScenarioBank([StressScenario(**dict(item)) for item in configured_scenarios])

    standard_id = str(standards[0].get("standard_id", "E-MATH-03-01")) if standards else "E-MATH-03-01"
    return StressScenarioBank(
        [
            StressScenario(
                scenario_id="phase5-contradictory-evidence",
                subject=str(standards[0].get("subject", "math")) if standards else "math",
                grade_band=f"{standards[0].get('school_level', 'elementary')}-{standards[0].get('grade', '3')}" if standards else "elementary-3",
                stressor_type="contradiction",
                prompt="One source says 245 + 130 = 365, another says 375. Resolve.",
                expected_signal="evidence_reconciliation",
                standard_ids=[standard_id],
                traps=["accepts_first_source"],
                time_limit_seconds=120,
            )
        ]
    )


def _write_engine_outputs(output_dir: str | Path | None, outputs: dict[str, Any]) -> dict[str, str]:
    if output_dir is None:
        return {}

    base = Path(output_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)
    output_paths: dict[str, str] = {}
    for index, engine_name in enumerate(EXECUTION_TRACE, start=1):
        path = base / f"{index:02d}_{engine_name}.json"
        output_paths[engine_name] = write_json(path, outputs[engine_name])
    return output_paths


def run_configured_suite(
    config: dict[str, Any],
    *,
    output_dir: str | Path | None = None,
    config_base_dir: str | Path | None = None,
) -> dict[str, Any]:
    mode = _config_mode(config)
    if mode == "production":
        _validate_production_config(config)

    learner = _learner_config(config)
    data_config = _config_section(config, "data")
    curriculum_config = _config_section(config, "curriculum")
    runtime_config = _config_section(config, "runtime")
    stress_config = _config_section(config, "stress")
    governance_config = _config_section(config, "governance")

    storage_root = data_config.get("storage_root", ".paideia-data")
    data_engine = DataAcquisitionEngine(default_seed_catalog(), storage_root=storage_root)
    data_plan = data_engine.build_engine_plan(str(data_config.get("engine", "assessment")))
    acquisition_validation = _validate_configured_sources(
        data_engine,
        data_config,
        config_base_dir=config_base_dir,
    )

    standards = _load_standards(
        curriculum_config,
        config_base_dir=config_base_dir,
        acquisition_validation=acquisition_validation,
    )
    curriculum = CurriculumMappingEngine(standards)
    learning_unit = curriculum.build_learning_unit(
        school_level=str(curriculum_config.get("school_level", "elementary")),
        grade=str(curriculum_config.get("grade", "3")),
        subject=str(curriculum_config.get("subject", "math")),
    )

    item_bank = _build_item_bank(
        config,
        standards,
        config_base_dir=config_base_dir,
        acquisition_validation=acquisition_validation,
    )
    cultivation = CultivationEngine()
    roadmap = cultivation.build_learning_roadmap(
        learning_unit=learning_unit,
        data_plan=data_plan,
        item_bank=item_bank,
    )

    assessment = AssessmentEngine(item_bank=item_bank)
    assessment_result = assessment.evaluate_item_response(
        str(_config_section(config, "assessment").get("item_id", "phase5-default-item")),
        response={
            "answer": str(_config_section(config, "assessment").get("answer", "375")),
            "explanation": str(
                _config_section(config, "assessment").get("explanation", "I used place value to verify 375.")
            ),
        },
    )

    stress_bank = _build_stress_bank(config, standards)
    stress = StressEngine(scenario_bank=stress_bank)
    scenario_id = str(stress_config.get("scenario_id", "phase5-contradictory-evidence"))
    stress_run = stress.run_scenario(
        learner_id=learner["learner_id"],
        scenario_id=scenario_id,
        response=str(
            stress_config.get(
                "response",
                "I compare both sources, verify place value, and ask for review before memory promotion.",
            )
        ),
    )

    governance = GovernanceEngine()
    governance_review = governance.review_action(
        str(governance_config.get("action", "run_local_task")),
        context=dict(governance_config.get("context", {"contains_private_assets": False})),
    )

    runtime = RuntimeEngine(engine_id=str(runtime_config.get("engine_id", "runtime:configured")))
    runtime_run = runtime.run_task(
        agent_id=learner["learner_id"],
        task=learner["task"],
        tools=[str(tool) for tool in runtime_config.get("tools", ["read_file", "summarize", "write_report"])],
        artifacts=[dict(item) for item in runtime_config.get("artifacts", [])],
    )

    promotion = PromotionEngine(owner=learner["learner_id"])
    review_label = assessment_result["review_label"]
    governance_allowed = governance_review["decision"] == "allowed"
    promotion_event = {
        "summary": "Configured suite run completed after assessment, stress, governance, and runtime evidence.",
        "skills": ["configuration", "orchestration", "trace_review"],
        "assessment_score": assessment_result["score"],
        "stress_status": stress_run["status"],
        "governance_decision": governance_review["decision"],
        "runtime_run_id": runtime_run["run_id"],
    }
    review_status = str(review_label["status"])
    review_notes = str(review_label.get("notes", ""))
    quarantine_reason = None
    if not governance_allowed:
        promotion_event["blocked_by"] = "governance"
        review_status = "needs_review"
        review_notes = "Governance blocked promotion."
        quarantine_reason = "governance_blocked_promotion"
    promotion_decision = promotion.record_experience(
        source="configured_suite",
        event=promotion_event,
        review=ReviewLabel(
            score=int(review_label["score"]),
            status=review_status,
            reviewed_by=str(review_label["reviewed_by"]),
            notes=review_notes,
        ),
        quarantine_reason=quarantine_reason,
    )
    promotion_decision["event"] = dict(promotion_event)

    verification = {
        "schema": "paideia-configured-suite-verification/v1",
        "checks": {
            "assessment_passed": bool(assessment_result["passed"]),
            "acquisition_validation_passed": acquisition_validation["status"] == "passed",
            "stress_no_promotion_decision": "promotion_decision" not in stress_run,
            "promotion_recorded": promotion_decision["status"] in {"promoted", "quarantined"},
            "promotion_governance_gate_enforced": governance_allowed
            or promotion_decision["status"] == "quarantined",
            "governance_allowed": governance_allowed,
            "runtime_review_required": runtime_run["acceptance_checklist"]["requires_review"] is True,
            "runtime_replayable": runtime_run["acceptance_checklist"]["checks"]["reproducibility"][
                "replay_trace_available"
            ]
            is True,
        },
    }
    verification["passed"] = all(verification["checks"].values())

    outputs: dict[str, Any] = {
        "data_acquisition": data_plan,
        "acquisition_validation": acquisition_validation,
        "curriculum_mapping": learning_unit,
        "cultivation": roadmap,
        "assessment": assessment_result,
        "stress": stress_run,
        "governance": governance_review,
        "runtime": runtime_run,
        "promotion": promotion_decision,
        "verification": verification,
    }
    output_paths = _write_engine_outputs(output_dir, outputs)

    return {
        "schema": CONFIGURED_SUITE_RUN_SCHEMA,
        "trace_schema": CONFIGURED_SUITE_TRACE_SCHEMA,
        "mode": mode,
        "config_id": str(config.get("config_id", "default")),
        "learner": learner,
        "execution_trace": list(EXECUTION_TRACE),
        "outputs": outputs,
        "output_paths": output_paths,
        "trace_metadata": {
            "output_dir": str(Path(output_dir).resolve()) if output_dir is not None else None,
            "output_count": len(output_paths),
            "runtime_run_id": runtime_run["run_id"],
            "promotion_ledger_version": promotion.ledger["version"],
        },
    }


def run_config_file(
    config_path: str | Path,
    *,
    output_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    resolved_config_path = Path(config_path).resolve()
    config = load_config(resolved_config_path)
    result = run_configured_suite(
        config,
        output_dir=output_dir,
        config_base_dir=resolved_config_path.parent,
    )
    if output_path is not None:
        result["result_path"] = str(Path(output_path).resolve())
        write_json(output_path, result)
    return result


def run_engine_smoke(engine: str = "all") -> dict[str, Any]:
    selected = list(SMOKE_ENGINES if engine == "all" else [engine])
    results: dict[str, Any] = {}

    for engine_name in selected:
        try:
            sample = _run_single_smoke(engine_name)
            results[engine_name] = {
                "status": "passed",
                "sample_schema": sample.get("schema"),
            }
        except Exception as exc:  # pragma: no cover - exercised when a smoke check fails.
            results[engine_name] = {
                "status": "failed",
                "error": str(exc),
            }

    passed = sum(1 for item in results.values() if item["status"] == "passed")
    failed = len(results) - passed
    return {
        "schema": "paideia-cli-smoke/v1",
        "engine": engine,
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
        },
    }


def _run_single_smoke(engine_name: str) -> dict[str, Any]:
    if engine_name == "data_acquisition":
        return DataAcquisitionEngine(default_seed_catalog(), storage_root=".paideia-smoke").build_engine_plan(
            "assessment"
        )
    if engine_name == "curriculum_mapping":
        return CurriculumMappingEngine(_default_standards()).build_learning_unit(
            school_level="elementary",
            grade="3",
            subject="math",
        )
    if engine_name == "cultivation":
        return CultivationEngine().create_blueprint("agent:smoke", "local analyst", ["traceable answers"])
    if engine_name == "assessment":
        return AssessmentEngine().evaluate(
            gate_id="smoke_gate",
            submission={"answer": "Evidence with uncertainty and verification.", "artifacts": ["trace.json"]},
        )
    if engine_name == "stress":
        return StressEngine().run_rollout(
            learner_id="agent:smoke",
            scenario_id="conflicting_evidence",
            response="I compare sources, mark uncertainty, verify, and ask for review.",
        )
    if engine_name == "promotion":
        return PromotionEngine(owner="agent:smoke").record_experience(
            source="smoke",
            event={"summary": "Verified smoke result.", "skills": ["verification"]},
            review=ReviewLabel(score=90, status="verified", reviewed_by="smoke"),
        )
    if engine_name == "governance":
        return GovernanceEngine().review_action("run_local_task", {"contains_private_assets": False})
    if engine_name == "runtime":
        return RuntimeEngine(engine_id="runtime:smoke").run_task(
            agent_id="agent:smoke",
            task="smoke runtime",
            tools=["read_file"],
            artifacts=[{"path": "trace.json", "kind": "trace"}],
        )
    if engine_name == "orchestration":
        from paideia_engines.orchestration import PaideiaEngineSuite

        return PaideiaEngineSuite().run_growth_cycle(
            learner_id="agent:smoke",
            role="local analyst",
            objectives=["traceable answers"],
            task="smoke orchestration",
        )
    raise ValueError(f"Unknown smoke engine: {engine_name}")


__all__ = [
    "EXECUTION_TRACE",
    "SMOKE_ENGINES",
    "load_config",
    "run_config_file",
    "run_configured_suite",
    "run_engine_smoke",
    "write_json",
]
