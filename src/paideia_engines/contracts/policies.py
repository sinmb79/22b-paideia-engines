from __future__ import annotations


def default_local_policy() -> dict[str, object]:
    return {
        "schema": "paideia-local-policy/v1",
        "data_boundary": "local-first",
        "external_uploads": "blocked_by_default",
        "protected_assets": [
            "boss_private_assets",
            "voice_models",
            "private_documents",
            "personal_images",
            "training_corpus",
        ],
        "review_required_for": [
            "external_upload",
            "private_asset_access",
            "memory_promotion",
            "credential_use",
            "destructive_filesystem_action",
        ],
    }
