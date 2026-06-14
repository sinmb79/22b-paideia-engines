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
    ]
    for relative_path in expected_docs:
        assert (ROOT / relative_path).exists(), f"Missing {relative_path}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    korean = (ROOT / "README.ko.md").read_text(encoding="utf-8")
    assert "[Engine documentation](docs/engines/README.md)" in readme
    assert "[Engine contract registry](docs/engine_contracts.md)" in readme
    assert "[Release checklist](docs/release_checklist.md)" in readme
    assert "[Source-specific parsers](docs/source_parsers.md)" in readme
    assert "[엔진 문서](docs/engines/README.ko.md)" in korean
    assert "[엔진 계약 레지스트리](docs/engine_contracts.ko.md)" in korean
    assert "[릴리스 체크리스트](docs/release_checklist.ko.md)" in korean
    assert "[출처별 파서](docs/source_parsers.ko.md)" in korean


def test_release_checklist_contains_required_validation_commands():
    checklist = (ROOT / "docs" / "release_checklist.md").read_text(encoding="utf-8")

    required_commands = [
        "python -m pytest tests -q",
        "python -m compileall src",
        "python -m paideia_engines.cli validate-contracts",
        "python -m paideia_engines.cli run-config",
        "python -m paideia_engines.cli validate-suite-output",
        "python -m paideia_engines.cli smoke",
        "python -m paideia_engines.cli diagnose-source",
        "python -m paideia_engines.cli diagnose-manifest",
        "python -m paideia_engines.cli diagnose-stress-pack",
        "rg -n",
    ]
    for command in required_commands:
        assert command in checklist
    assert "<release-sensitive-patterns>" not in checklist


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
