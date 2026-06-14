import json
from pathlib import Path

from paideia_engines.data_catalog import default_seed_catalog, filter_by_engine


ROOT = Path(__file__).resolve().parents[1]


def test_default_seed_catalog_separates_open_licensed_and_restricted_sources():
    catalog = default_seed_catalog()
    license_tiers = {record.license_tier for record in catalog}

    assert "open_public" in license_tiers
    assert "login_or_agreement_required" in license_tiers
    assert "restricted_publisher_license" in license_tiers
    assert all(record.source_url.startswith("https://") for record in catalog)


def test_data_catalog_maps_sources_to_engine_usage():
    catalog = default_seed_catalog()

    cultivation_sources = filter_by_engine(catalog, "cultivation")
    assessment_sources = filter_by_engine(catalog, "assessment")

    assert any("curriculum" in record.source_id for record in cultivation_sources)
    assert any("exam" in record.source_id or "math_problem" in record.source_id for record in assessment_sources)
    assert all("cultivation" in record.engine_uses for record in cultivation_sources)


def test_restricted_textbooks_are_not_marked_as_auto_downloadable():
    catalog = default_seed_catalog()
    restricted = [record for record in catalog if record.license_tier == "restricted_publisher_license"]

    assert restricted
    assert all(record.acquisition_mode == "manual_license_required" for record in restricted)
    assert all(record.auto_download is False for record in restricted)


def test_seed_sources_json_matches_code_catalog_ids():
    catalog_ids = {record.source_id for record in default_seed_catalog()}
    manifest = json.loads((ROOT / "data" / "catalog" / "seed_sources.json").read_text(encoding="utf-8"))
    manifest_ids = {record["source_id"] for record in manifest}

    assert manifest_ids == catalog_ids
