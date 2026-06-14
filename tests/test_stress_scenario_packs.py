import json
from pathlib import Path

import pytest

from paideia_engines.stress.scenario_bank import (
    StressScenarioBank,
    diagnose_stress_scenario_pack,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "examples" / "stress_packs" / "core_subject_stress_pack.json"


def test_subject_stress_pack_loads_curriculum_linked_scenarios():
    bank = StressScenarioBank.from_file(PACK_PATH)

    math_plan = bank.build_plan("E-MATH-03-01")
    language_plan = bank.build_plan("E-LANG-04-02")
    science_plan = bank.build_plan("M-SCI-01-01")

    assert len(bank) >= 6
    assert math_plan["scenario_count"] >= 2
    assert "misconception" in math_plan["stressor_types"]
    assert language_plan["scenario_count"] >= 1
    assert science_plan["scenario_count"] >= 1
    assert all("subject" in scenario for scenario in math_plan["scenarios"])
    assert all("grade_band" in scenario for scenario in math_plan["scenarios"])


def test_subject_stress_pack_diagnostics_passes_public_pack():
    report = diagnose_stress_scenario_pack(PACK_PATH)

    assert report["schema"] == "paideia-stress-scenario-pack-diagnostics/v1"
    assert report["status"] == "passed"
    assert report["checks"]["scenario_ids_unique"] is True
    assert report["checks"]["promotion_boundary_clean"] is True
    assert report["summary"]["scenario_count"] >= 6


def test_subject_stress_pack_diagnostics_blocks_promotion_decision_leak(tmp_path):
    payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    payload["scenarios"][0]["promotion_decision"] = {"status": "promoted"}
    pack_path = tmp_path / "leaky-pack.json"
    pack_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = diagnose_stress_scenario_pack(pack_path)

    assert report["status"] == "blocked"
    assert report["checks"]["promotion_boundary_clean"] is False
    assert any(issue["code"] == "promotion_decision_leak" for issue in report["issues"])


def test_stress_pack_loader_rejects_promotion_decision_leak(tmp_path):
    payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    payload["scenarios"][0]["ledger_version"] = 1
    pack_path = tmp_path / "loader-leak.json"
    pack_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="Stress scenario pack diagnostics failed"):
        StressScenarioBank.from_file(pack_path)


def test_stress_pack_diagnostics_blocks_missing_subject_and_grade(tmp_path):
    payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    payload["scenarios"][0].pop("subject")
    payload["scenarios"][1].pop("grade_band")
    pack_path = tmp_path / "missing-fields.json"
    pack_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = diagnose_stress_scenario_pack(pack_path)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "invalid_stress_scenario" for issue in report["issues"])


def test_stress_pack_diagnostics_blocks_wrong_types_and_unknown_fields(tmp_path):
    payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    payload["scenarios"][0]["scenario_id"] = 100
    payload["scenarios"][0]["standard_ids"] = "E-MATH-03-01"
    payload["scenarios"][0]["unexpected"] = "not allowed"
    pack_path = tmp_path / "wrong-types.json"
    pack_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = diagnose_stress_scenario_pack(pack_path)

    assert report["status"] == "blocked"
    assert any(issue["code"] == "invalid_stress_scenario" for issue in report["issues"])
