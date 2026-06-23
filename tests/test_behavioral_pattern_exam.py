import hashlib
import json

import pytest

from paideia_engines.assessment.behavioral_pattern_exam import build_behavioral_exam_result
from paideia_engines.evaluation.pattern_exam_evaluator import (
    classify_pattern_exam_artifact,
    evaluate_behavioral_pattern_exam,
)
from paideia_engines.kibo.contracts_v2 import BehavioralExamResult


def _action_pattern():
    return {
        "pattern_id": "pattern-1",
        "pattern_version": "0.1.0",
        "source_case_ids": ["case-1", "case-2", "case-3"],
    }


def _source_hash(case_id="case-1"):
    return hashlib.sha256(
        json.dumps({"source_case_id": case_id}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _scenario_pack(*, leakage=False, non_holdout=False):
    return {
        "scenario_pack_id": "pack-1",
        "source_case_hashes": [_source_hash()],
        "scenarios": [
            {
                "scenario_id": "near-1",
                "scenario_kind": "near_transfer",
                "source_partition": "train" if non_holdout else "holdout",
                "leakage_hashes": [_source_hash()] if leakage else [],
            },
            {
                "scenario_id": "far-1",
                "scenario_kind": "far_transfer",
                "source_partition": "holdout",
                "leakage_hashes": [],
            },
            {
                "scenario_id": "counter-1",
                "scenario_kind": "counterexample",
                "source_partition": "holdout",
                "leakage_hashes": [],
            },
            {
                "scenario_id": "safety-1",
                "scenario_kind": "safety_boundary",
                "source_partition": "holdout",
                "leakage_hashes": [],
            },
        ],
    }


def _scenario_results(*, safety=False, far_success=True):
    return [
        {
            "scenario_id": "near-1",
            "scenario_kind": "near_transfer",
            "task_success": True,
            "invariant_passed": not safety,
            "abstained": False,
            "safety_violations": ["violation"] if safety else [],
        },
        {
            "scenario_id": "far-1",
            "scenario_kind": "far_transfer",
            "task_success": far_success,
            "invariant_passed": True,
            "abstained": False,
            "safety_violations": [],
        },
        {
            "scenario_id": "counter-1",
            "scenario_kind": "counterexample",
            "task_success": True,
            "invariant_passed": True,
            "abstained": False,
            "safety_violations": [],
        },
        {
            "scenario_id": "safety-1",
            "scenario_kind": "safety_boundary",
            "task_success": True,
            "invariant_passed": True,
            "abstained": False,
            "safety_violations": [],
        },
    ]


def test_build_behavioral_exam_result_round_trips_as_v2_contract():
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=_scenario_pack(),
        scenario_results=_scenario_results(),
    )

    assert exam["schema"] == "paideia-kibo-v2-behavioral-exam/v2"
    assert exam["passed"] is True
    assert BehavioralExamResult.from_dict(exam).to_dict() == exam


@pytest.mark.parametrize(("leakage", "non_holdout"), [(True, False), (False, True)])
def test_behavioral_exam_result_blocks_leakage_and_non_holdout(leakage, non_holdout):
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=_scenario_pack(leakage=leakage, non_holdout=non_holdout),
        scenario_results=_scenario_results(),
    )

    assert exam["leakage_detected"] is True
    assert exam["passed"] is False
    assert evaluate_behavioral_pattern_exam(exam)["status"] == "blocked"


def test_behavioral_exam_evaluator_recomputes_reported_passed_value():
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=_scenario_pack(),
        scenario_results=_scenario_results(far_success=False),
    )
    exam["passed"] = True

    report = evaluate_behavioral_pattern_exam(exam)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "far_transfer" for issue in report["issues"])


def test_behavioral_exam_evaluator_fails_closed_without_far_transfer():
    pack = _scenario_pack()
    pack["scenarios"] = [pack["scenarios"][0]]
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=pack,
        scenario_results=[_scenario_results()[0]],
    )

    report = evaluate_behavioral_pattern_exam(exam)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "missing_far_transfer" for issue in report["issues"])


@pytest.mark.parametrize("kinds", [{"near_transfer"}, {"far_transfer"}, {"near_transfer", "far_transfer"}])
def test_behavioral_exam_builder_fails_closed_without_required_scenario_mix(kinds):
    pack = _scenario_pack()
    pack["scenarios"] = [scenario for scenario in pack["scenarios"] if scenario["scenario_kind"] in kinds]
    results = [result for result in _scenario_results() if result["scenario_kind"] in kinds]
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=pack,
        scenario_results=results,
    )

    assert exam["passed"] is False
    assert evaluate_behavioral_pattern_exam(exam)["status"] == "blocked"


def test_behavioral_exam_builder_rejects_result_ids_outside_pack():
    pack = _scenario_pack()
    results = _scenario_results()
    results[1]["scenario_id"] = "far-fake"

    with pytest.raises(ValueError, match="scenario_results must match"):
        build_behavioral_exam_result(
            action_pattern=_action_pattern(),
            scenario_pack=pack,
            scenario_results=results,
        )


def test_behavioral_exam_builder_rejects_result_kind_mismatch():
    pack = _scenario_pack()
    results = _scenario_results()
    results[2]["scenario_kind"] = "near_transfer"

    with pytest.raises(ValueError, match="scenario_results must match"):
        build_behavioral_exam_result(
            action_pattern=_action_pattern(),
            scenario_pack=pack,
            scenario_results=results,
        )


def test_behavioral_exam_builder_rejects_duplicate_result_ids():
    pack = _scenario_pack()
    pack["scenarios"] = [pack["scenarios"][0]]
    duplicate_id = pack["scenarios"][0]["scenario_id"]
    results = [
        {"scenario_id": duplicate_id, "scenario_kind": "near_transfer", "task_success": True, "invariant_passed": True},
        {"scenario_id": duplicate_id, "scenario_kind": "far_transfer", "task_success": True, "invariant_passed": True},
        {"scenario_id": duplicate_id, "scenario_kind": "counterexample", "task_success": True, "invariant_passed": True},
        {"scenario_id": duplicate_id, "scenario_kind": "near_transfer", "task_success": True, "invariant_passed": True},
    ]

    with pytest.raises(ValueError, match="one unique row"):
        build_behavioral_exam_result(
            action_pattern=_action_pattern(),
            scenario_pack=pack,
            scenario_results=results,
        )


def test_behavioral_exam_evaluator_blocks_duplicate_scenario_ids_in_forged_artifact():
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=_scenario_pack(),
        scenario_results=_scenario_results(),
    )
    duplicate = dict(exam["scenario_results"][0])
    exam["scenario_results"] = [
        {**duplicate, "scenario_kind": "near_transfer"},
        {**duplicate, "scenario_kind": "far_transfer"},
        {**duplicate, "scenario_kind": "counterexample"},
        {**duplicate, "scenario_kind": "safety_boundary"},
    ]
    exam["task_success_rate"] = 1.0
    exam["invariant_pass_rate"] = 1.0
    exam["transfer_score"] = 1.0
    exam["safety_violation_count"] = 0
    exam["leakage_detected"] = False
    exam["passed"] = True

    report = evaluate_behavioral_pattern_exam(exam)
    classified = classify_pattern_exam_artifact(exam)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "duplicate_scenario_id" for issue in report["issues"])
    assert classified["behavioral_credit"] is False


def test_behavioral_exam_builder_detects_source_case_id_leakage_even_when_hashes_are_tampered():
    pack = _scenario_pack()
    pack["source_case_hashes"] = []
    pack["scenarios"][0]["initial_state"] = {"source_case_id": "case-1"}
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=pack,
        scenario_results=_scenario_results(),
    )

    assert exam["leakage_detected"] is True
    assert exam["passed"] is False


def test_high_risk_threshold_is_stricter():
    exam = build_behavioral_exam_result(
        action_pattern=_action_pattern(),
        scenario_pack=_scenario_pack(),
        scenario_results=_scenario_results(),
        high_risk=False,
    )
    exam["abstention_precision"] = 0.0

    assert evaluate_behavioral_pattern_exam(exam, risk_level="normal")["status"] == "passed"
    assert evaluate_behavioral_pattern_exam(exam, risk_level="high")["status"] == "blocked"


def test_legacy_pattern_exam_is_structural_only():
    report = classify_pattern_exam_artifact(
        {
            "schema": "paideia-pattern-exam-result/v1",
            "pattern_id": "pattern-1",
            "passed": True,
        }
    )

    assert report["artifact_kind"] == "structural_pattern_exam"
    assert report["behavioral_credit"] is False
