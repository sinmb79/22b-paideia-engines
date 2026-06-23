def test_pr1_cross_repo_contracts_have_canonical_v2_registry():
    from paideia_engines.kibo import schema_registry

    registry = schema_registry()

    assert registry["schema"] == "paideia-kibo-v2-schema-registry/v1"
    assert registry["contracts_release"].startswith("2.")
    assert "action_pattern" in registry["contract_hashes"]
