from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ENGINE_DOC_DIRS = [
    ROOT / "src" / "paideia_engines" / "data_acquisition",
    ROOT / "src" / "paideia_engines" / "curriculum_mapping",
    ROOT / "src" / "paideia_engines" / "cultivation",
    ROOT / "src" / "paideia_engines" / "assessment",
    ROOT / "src" / "paideia_engines" / "stress",
    ROOT / "src" / "paideia_engines" / "promotion",
    ROOT / "src" / "paideia_engines" / "governance",
    ROOT / "src" / "paideia_engines" / "runtime",
    ROOT / "src" / "paideia_engines" / "orchestration",
    ROOT / "src" / "paideia_engines" / "evaluation",
]


def test_every_engine_has_bilingual_readme():
    for engine_dir in ENGINE_DOC_DIRS:
        english = engine_dir / "README.md"
        korean = engine_dir / "README.ko.md"
        assert english.exists(), f"Missing {english}"
        assert korean.exists(), f"Missing {korean}"
        assert "[한국어](README.ko.md)" in english.read_text(encoding="utf-8")
        assert "[English](README.md)" in korean.read_text(encoding="utf-8")


def test_release_hardening_docs_exist_and_are_linked():
    expected_docs = [
        "docs/engines/README.md",
        "docs/engines/README.ko.md",
        "docs/engine_contracts.md",
        "docs/engine_contracts.ko.md",
        "docs/release_guide.md",
        "docs/release_guide.ko.md",
        "docs/release_checklist.md",
        "docs/release_checklist.ko.md",
        "docs/public_asset_audit.md",
        "docs/public_asset_audit.ko.md",
        "docs/dataset_adapter_backlog.md",
        "docs/dataset_adapter_backlog.ko.md",
        "docs/source_parsers.md",
        "docs/source_parsers.ko.md",
        "docs/example_data_index.md",
        "docs/example_data_index.ko.md",
        "docs/downstream_reuse_recipes.md",
        "docs/downstream_reuse_recipes.ko.md",
    ]
    for relative_path in expected_docs:
        assert (ROOT / relative_path).exists(), f"Missing {relative_path}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    korean = (ROOT / "README.ko.md").read_text(encoding="utf-8")
    assert "[Engine documentation](docs/engines/README.md)" in readme
    assert "[Engine contract registry](docs/engine_contracts.md)" in readme
    assert "[Release checklist](docs/release_checklist.md)" in readme
    assert "[Source-specific parsers](docs/source_parsers.md)" in readme
    assert "[Downstream reuse recipes](docs/downstream_reuse_recipes.md)" in readme
    assert "[엔진 문서](docs/engines/README.ko.md)" in korean
    assert "[엔진 계약 레지스트리](docs/engine_contracts.ko.md)" in korean
    assert "[릴리스 체크리스트](docs/release_checklist.ko.md)" in korean
    assert "[출처별 파서](docs/source_parsers.ko.md)" in korean
    assert "[Downstream 재사용 레시피](docs/downstream_reuse_recipes.ko.md)" in korean


def test_release_checklist_contains_required_validation_commands():
    checklist = (ROOT / "docs" / "release_checklist.md").read_text(encoding="utf-8")

    required_commands = [
        "python -m pytest tests -q",
        "python -m compileall src",
        "python -m paideia_engines.cli validate-contracts",
        "python -m paideia_engines.cli certify-adapters",
        "python -m paideia_engines.cli run-config",
        "python -m paideia_engines.cli validate-suite-output",
        "python -m paideia_engines.cli smoke",
        "python -m paideia_engines.cli diagnose-source",
        "python -m paideia_engines.cli diagnose-manifest",
        "python -m paideia_engines.cli diagnose-stress-pack",
        "python -m paideia_engines.cli persist-runtime-evidence",
        "python -m paideia_engines.cli validate-runtime-evidence",
        "python -m paideia_engines.cli replay-runtime-evidence",
        "python -m paideia_engines.cli validate-benchmarks",
        "python -m paideia_engines.cli validate-release-candidate",
        "python examples\\downstream_single_engine_recipe.py",
        "python examples\\downstream_suite_recipe.py",
        "rg -n",
    ]
    for command in required_commands:
        assert command in checklist
    assert "<release-sensitive-patterns>" not in checklist


def test_trust_boundary_docs_pin_promotion_and_artifact_gates():
    required_phrases = [
        "governance-blocked promotion quarantine",
        "verified artifact",
        "trace schema v2",
    ]
    documented_paths = [
        "docs/architecture.md",
        "docs/architecture.ko.md",
        "docs/release_checklist.md",
        "docs/release_checklist.ko.md",
        "docs/engine_contracts.md",
        "docs/engine_contracts.ko.md",
    ]

    for relative_path in documented_paths:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in text, f"{relative_path} must document {phrase!r}"


def test_engine_contracts_document_governance_quarantine_reconsideration_gate():
    for relative_path in ["docs/engine_contracts.md", "docs/engine_contracts.ko.md"]:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "force-quarantine" in text
        assert "fresh allowed governance decision" in text


def test_ci_workflow_runs_release_quality_gates():
    workflow = ROOT / ".github" / "workflows" / "ci.yml"

    assert workflow.exists(), "Missing GitHub Actions CI workflow."
    text = workflow.read_text(encoding="utf-8")
    for required in [
        "python-version",
        "setuptools",
        "wheel",
        "python -m compileall src",
        "python -m pytest tests -q",
        "paideia-engines validate-release-candidate",
    ]:
        assert required in text


def test_public_asset_audit_declares_forbidden_asset_classes():
    audit = (ROOT / "docs" / "public_asset_audit.md").read_text(encoding="utf-8")

    for forbidden in [
        "private voice assets",
        "credentials",
        "restricted textbooks",
        "AI-Hub downloaded corpora",
        "exam PDFs",
        "personal data",
        "generated caches",
    ]:
        assert forbidden in audit
