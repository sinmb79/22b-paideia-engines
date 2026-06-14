from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_exposes_korean_language_choice():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    korean = (ROOT / "README.ko.md").read_text(encoding="utf-8")

    assert "[한국어](README.ko.md)" in readme
    assert "[English](README.md)" in korean
    assert "Paideia Engines" in readme
    assert "파이데이아 엔진" in korean


def test_architecture_docs_and_basic_example_exist():
    assert (ROOT / "docs" / "architecture.md").exists()
    assert (ROOT / "docs" / "architecture.ko.md").exists()
    assert (ROOT / "docs" / "data_acquisition.md").exists()
    assert (ROOT / "docs" / "data_acquisition.ko.md").exists()
    assert (ROOT / "docs" / "real_engine_development.md").exists()
    assert (ROOT / "docs" / "real_engine_development.ko.md").exists()
    assert (ROOT / "docs" / "master_development_plan.md").exists()
    assert (ROOT / "docs" / "master_development_plan.ko.md").exists()
    assert (ROOT / "examples" / "basic_growth_cycle.py").exists()
    assert (ROOT / "examples" / "data_and_curriculum_pipeline.py").exists()
    assert (ROOT / "examples" / "assessment_and_cultivation_pipeline.py").exists()
    assert (ROOT / "examples" / "stress_and_promotion_pipeline.py").exists()
