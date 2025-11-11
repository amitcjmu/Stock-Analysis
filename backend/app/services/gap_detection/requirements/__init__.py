"""
Requirements module for context-aware gap detection.

Provides RequirementsEngine for aggregating requirements based on:
- Asset type (server, database, application, network, storage, container)
- 6R migration strategy (rehost, replatform, refactor, repurchase, retire, retain)
- Compliance scope (PCI-DSS, HIPAA, SOC2, GDPR, ISO27001)
- Criticality tier (tier_1_critical, tier_2_important, tier_3_standard)

Usage:
    from app.services.gap_detection.requirements import RequirementsEngine

    engine = RequirementsEngine()
    reqs = await engine.get_requirements(
        asset_type="application",
        six_r_strategy="refactor",
        compliance_scopes=["PCI-DSS"],
        criticality="tier_1_critical",
    )
"""

from .asset_type_matrix import ASSET_TYPE_REQUIREMENTS
from .compliance_matrix import COMPLIANCE_REQUIREMENTS
from .criticality_matrix import CRITICALITY_REQUIREMENTS
from .requirements_engine import RequirementsEngine
from .six_r_strategy_matrix import SIX_R_STRATEGY_REQUIREMENTS

__all__ = [
    "RequirementsEngine",
    "ASSET_TYPE_REQUIREMENTS",
    "SIX_R_STRATEGY_REQUIREMENTS",
    "COMPLIANCE_REQUIREMENTS",
    "CRITICALITY_REQUIREMENTS",
]
