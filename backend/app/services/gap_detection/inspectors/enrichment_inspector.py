"""
EnrichmentInspector - Inspects Asset enrichment tables for missing/incomplete data.

7 Enrichment Tables (as defined in architecture doc):
1. AssetResilience (resilience) - RTO, RPO, backup strategy
2. AssetComplianceFlags (compliance_flags) - Compliance scopes, data classification
3. AssetVulnerabilities (vulnerabilities) - CVE, severity, remediation
4. AssetTechDebt (tech_debt) - Technical debt score, modernization priority
5. AssetDependencies (dependencies) - Upstream/downstream dependencies
6. AssetPerformanceMetrics (performance_metrics) - CPU, memory utilization
7. AssetCostOptimization (cost_optimization) - Monthly cost, optimization potential

Performance: <20ms per asset (eager-loaded relationships, no DB queries)
Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gap_detection.schemas import EnrichmentGapReport, DataRequirements
from .base import BaseInspector

logger = logging.getLogger(__name__)

# Map enrichment table names to Asset relationship attributes
# NOTE: The actual relationship names are defined on the Asset model
ENRICHMENT_RELATIONSHIPS = {
    "resilience": "resilience",
    "compliance_flags": "compliance_flags",
    "vulnerabilities": "vulnerabilities",
    "tech_debt": "tech_debt",
    "dependencies": "dependencies",
    "performance_metrics": "performance_metrics",
    "cost_optimization": "cost_optimization",
}


class EnrichmentInspector(BaseInspector):
    """
    Inspects Asset enrichment tables for missing/incomplete data.

    Enrichment tables provide specialized data beyond basic Asset columns:
    - Resilience: Business continuity metrics
    - Compliance: Regulatory and security flags
    - Vulnerabilities: Security vulnerability tracking
    - Tech Debt: Technical debt and modernization needs
    - Dependencies: Inter-asset relationships
    - Performance: Resource utilization metrics
    - Cost: Cost optimization opportunities

    Performance: <20ms per asset (assumes relationships are eager-loaded)

    GPT-5 Recommendations Applied:
    - #1: Tenant scoping parameters included (not used for eager-loaded checks)
    - #3: Async method signature
    - #8: Completeness score clamped to [0.0, 1.0]
    """

    async def inspect(
        self,
        asset: Any,
        application: Optional[Any],
        requirements: DataRequirements,
        client_account_id: str,
        engagement_id: str,
        db: Optional[AsyncSession] = None,
    ) -> EnrichmentGapReport:
        """
        Check enrichment tables for missing or incomplete data.

        Assumes enrichment relationships are eager-loaded on the asset.
        If not eager-loaded, this will trigger lazy loading (slower).

        Scoring:
        - Missing table = 0.0 points
        - Incomplete table (some fields empty) = 0.5 points
        - Complete table = 1.0 points

        Args:
            asset: Asset SQLAlchemy model with relationships loaded
            application: Not used by enrichment inspector
            requirements: DataRequirements with required_enrichments list
            client_account_id: Tenant client account UUID (not used for eager-loaded checks)
            engagement_id: Engagement UUID (not used for eager-loaded checks)
            db: Optional AsyncSession (not used if relationships are eager-loaded)

        Returns:
            EnrichmentGapReport with:
            - missing_tables: Enrichment tables that don't exist
            - incomplete_tables: Tables that exist but have incomplete fields
            - completeness_score: [0.0-1.0] weighted score

        Raises:
            ValueError: If asset or requirements are None
        """
        if asset is None:
            raise ValueError("Asset cannot be None")
        if requirements is None:
            raise ValueError("DataRequirements cannot be None")

        missing_tables = []
        incomplete_tables: Dict[str, List[str]] = {}

        # Check each required enrichment table
        for table_name in requirements.required_enrichments:
            relationship_attr = ENRICHMENT_RELATIONSHIPS.get(table_name)

            if not relationship_attr:
                logger.warning(
                    f"Unknown enrichment table: {table_name}",
                    extra={
                        "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                        "table_name": table_name,
                    },
                )
                continue

            # Check if relationship exists on Asset model
            if not hasattr(asset, relationship_attr):
                logger.warning(
                    f"Asset model missing relationship: {relationship_attr}",
                    extra={
                        "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                        "relationship": relationship_attr,
                        "table_name": table_name,
                    },
                )
                missing_tables.append(table_name)
                continue

            # Get relationship (should be eager-loaded for performance)
            enrichment = getattr(asset, relationship_attr, None)

            if enrichment is None:
                # Table completely missing
                missing_tables.append(table_name)
            else:
                # Table exists, check for incomplete fields
                incomplete_fields = self._check_completeness(enrichment, table_name)
                if incomplete_fields:
                    incomplete_tables[table_name] = incomplete_fields

        # Calculate completeness score (GPT-5 Rec #8: Clamp to [0.0, 1.0])
        total_required = len(requirements.required_enrichments)

        if total_required == 0:
            score = 1.0
        else:
            # Missing table = 0 points
            # Incomplete table = 0.5 points
            # Complete table = 1 point
            complete_count = (
                total_required - len(missing_tables) - len(incomplete_tables)
            )
            partial_count = len(incomplete_tables)

            score = (complete_count + (partial_count * 0.5)) / total_required

        # JSON safety: Clamp (GPT-5 Rec #8)
        score = max(0.0, min(1.0, float(score)))

        logger.debug(
            "enrichment_inspector_completed",
            extra={
                "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                "asset_name": getattr(asset, "asset_name", None),
                "total_required": total_required,
                "missing_tables": len(missing_tables),
                "incomplete_tables": len(incomplete_tables),
                "completeness_score": score,
            },
        )

        return EnrichmentGapReport(
            missing_tables=missing_tables,
            incomplete_tables=incomplete_tables,
            completeness_score=score,
        )

    def _check_completeness(self, enrichment: Any, table_name: str) -> List[str]:
        """
        Check if enrichment table has required fields populated.

        This defines the "critical fields" for each enrichment type.
        Fields with None or empty values are considered incomplete.

        Args:
            enrichment: Enrichment table instance (e.g., AssetResilience)
            table_name: Name of enrichment table (for lookup)

        Returns:
            List of incomplete field names (empty list if fully complete)
        """
        incomplete_fields = []

        # Define critical fields per enrichment type
        # NOTE: These fields must exist on the respective SQLAlchemy models
        critical_fields_map = {
            "resilience": ["rto_minutes", "rpo_minutes"],
            "compliance_flags": ["compliance_scopes", "data_classification"],
            "vulnerabilities": ["cve_id", "severity"],
            "tech_debt": ["technical_debt_score", "modernization_priority"],
            "dependencies": ["dependency_type"],  # AssetDependency table
            "performance_metrics": [
                "cpu_utilization_percent",
                "memory_utilization_percent",
            ],
            "cost_optimization": ["monthly_cost_usd", "optimization_potential"],
        }

        critical_fields = critical_fields_map.get(table_name, [])

        for field in critical_fields:
            if not hasattr(enrichment, field):
                # Field doesn't exist on model - treat as incomplete
                incomplete_fields.append(field)
                continue

            value = getattr(enrichment, field, None)

            # Check for None, empty strings, empty lists, empty dicts
            if value is None:
                incomplete_fields.append(field)
            elif isinstance(value, str) and not value.strip():
                incomplete_fields.append(field)
            elif isinstance(value, (list, dict)) and len(value) == 0:
                incomplete_fields.append(field)
            # Value exists and is not empty - field is complete

        return incomplete_fields
