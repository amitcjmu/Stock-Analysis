"""
GapAnalyzer requirements retrieval - Extracts context for RequirementsEngine.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any

from app.services.gap_detection.schemas import DataRequirements

logger = logging.getLogger(__name__)


class RequirementsMixin:
    """Mixin for getting context-aware requirements."""

    async def _get_requirements(self, asset: Any) -> DataRequirements:
        """
        Get context-aware requirements for the asset.

        Extracts context from asset attributes:
        - asset_type: From asset.asset_type
        - six_r_strategy: From asset.six_r_strategy (optional)
        - compliance_scopes: From asset.compliance_flags (optional)
        - criticality: From asset.criticality (optional)

        Args:
            asset: Asset SQLAlchemy model

        Returns:
            DataRequirements with context-aware requirements

        Performance:
            - RequirementsEngine uses LRU cache
            - First call: ~5-10ms (computation + cache storage)
            - Subsequent calls: <1ms (cache hit)
        """
        asset_type = getattr(asset, "asset_type", "other")
        six_r_strategy = getattr(asset, "six_r_strategy", None)
        criticality = getattr(asset, "criticality", None)

        # Extract compliance scopes from compliance_flags relationship
        compliance_scopes = None
        try:
            if hasattr(asset, "compliance_flags"):
                compliance_flags = getattr(asset, "compliance_flags", None)
                if compliance_flags is not None:
                    compliance_scopes = getattr(
                        compliance_flags, "compliance_scopes", None
                    )
        except Exception:
            # Relationship might not be loaded or doesn't exist - that's OK
            compliance_scopes = None

        requirements = await self.requirements_engine.get_requirements(
            asset_type=asset_type,
            six_r_strategy=six_r_strategy,
            compliance_scopes=compliance_scopes,
            criticality=criticality,
        )

        logger.debug(
            f"Generated requirements for asset {asset.id}",
            extra={
                "asset_id": str(asset.id),
                "asset_type": asset_type,
                "six_r_strategy": six_r_strategy,
                "compliance_scopes": compliance_scopes,
                "criticality": criticality,
                "required_columns_count": len(requirements.required_columns),
                "required_enrichments_count": len(requirements.required_enrichments),
                "completeness_threshold": requirements.completeness_threshold,
            },
        )

        return requirements
