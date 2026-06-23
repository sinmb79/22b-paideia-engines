"""Shared contracts used by every Paideia engine."""

from .models import EngineEvent, PromotionDecision, QuarantineDecision, ReviewLabel
from .policies import default_local_policy
from .registry import (
    EngineContract,
    engine_contract_registry,
    engine_contracts,
    validate_engine_contract_registry,
)
from .compatibility_manifest import (
    cross_repo_compatibility_manifest,
    validate_cross_repo_compatibility_manifest,
)

__all__ = [
    "EngineContract",
    "EngineEvent",
    "PromotionDecision",
    "QuarantineDecision",
    "ReviewLabel",
    "default_local_policy",
    "cross_repo_compatibility_manifest",
    "engine_contract_registry",
    "engine_contracts",
    "validate_cross_repo_compatibility_manifest",
    "validate_engine_contract_registry",
]
