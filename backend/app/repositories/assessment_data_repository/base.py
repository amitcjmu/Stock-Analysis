"""
Assessment Data Repository - Base Class

Core repository class with initialization and helper methods.
Per ADR-024: All queries MUST include client_account_id and engagement_id scoping.
"""

from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.canonical_applications import CanonicalApplication
from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset

from .readiness_queries import ReadinessQueriesMixin
from .complexity_queries import ComplexityQueriesMixin
from .dependency_queries import DependencyQueriesMixin
from .risk_queries import RiskQueriesMixin
from .recommendation_queries import RecommendationQueriesMixin
from .architecture_minimums_queries import ArchitectureMinimumsQueriesMixin  # ADR-039

logger = get_logger(__name__)


class AssessmentDataRepository(
    ReadinessQueriesMixin,
    ComplexityQueriesMixin,
    DependencyQueriesMixin,
    RiskQueriesMixin,
    RecommendationQueriesMixin,
    ArchitectureMinimumsQueriesMixin,  # ADR-039: Compliance validation queries
):
    """
    Tenant-scoped repository for assessment phase data access.

    Provides data fetch methods for each assessment phase, ensuring all queries
    are properly scoped by client_account_id and engagement_id for enterprise
    multi-tenant security.

    CRITICAL: All queries MUST include both client_account_id AND engagement_id
    in WHERE clauses per ADR-024 security requirements.
    """

    def __init__(self, db: AsyncSession, client_account_id: UUID, engagement_id: UUID):
        """
        Initialize assessment data repository with tenant context.

        Args:
            db: Async database session
            client_account_id: Client account UUID for multi-tenant scoping
            engagement_id: Engagement UUID for project isolation

        Raises:
            ValueError: If required identifiers are missing
        """
        if not client_account_id or not engagement_id:
            raise ValueError(
                "SECURITY: client_account_id and engagement_id are required "
                "for multi-tenant data access"
            )

        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        logger.debug(
            f"Initialized AssessmentDataRepository - "
            f"client={client_account_id}, engagement={engagement_id}"
        )

    # === SERIALIZATION METHODS ===

    def _serialize_application(
        self, app: CanonicalApplication, assets: List[Asset] = None
    ) -> Dict[str, Any]:
        """Serialize canonical application with comprehensive asset data.

        Args:
            app: CanonicalApplication model
            assets: List of Asset models associated with this application

        Returns:
            Dictionary with comprehensive application and asset data for agent analysis
        """
        base_data = {
            "id": str(app.id),
            "name": app.canonical_name,
            "business_criticality": app.business_criticality,
            "description": app.description,
            "technology_stack": app.technology_stack or {},
            "application_type": app.application_type,
            "confidence_score": app.confidence_score,
            "is_verified": app.is_verified,
        }

        # Add comprehensive asset data if available
        if assets:
            serialized_assets = []
            for asset in assets:
                asset_data = {
                    "id": str(asset.id),
                    "name": asset.name or asset.asset_name,
                    "asset_type": asset.asset_type,
                    "operating_system": asset.operating_system,
                    "os_version": asset.os_version,
                    "cpu_cores": asset.cpu_cores,
                    "memory_gb": asset.memory_gb,
                    "storage_gb": asset.storage_gb,
                    "environment": asset.environment,
                    "location": asset.location,
                    "datacenter": asset.datacenter,
                    "hostname": asset.hostname,
                    "ip_address": asset.ip_address,
                    "business_owner": asset.business_owner,
                    "technical_owner": asset.technical_owner,
                    "department": asset.department,
                    "criticality": asset.criticality,
                    "migration_complexity": asset.migration_complexity,
                    "six_r_strategy": asset.six_r_strategy,
                    # JSON/JSONB fields with rich metadata
                    "custom_attributes": asset.custom_attributes or {},
                    "dependencies": asset.dependencies or {},
                    "related_assets": asset.related_assets or {},
                    "technology_stack": asset.technology_stack,
                    "phase_context": asset.phase_context or {},
                }
                serialized_assets.append(asset_data)

            base_data["assets"] = serialized_assets

            # Aggregate key insights across assets for quick reference
            operating_systems = list(
                {a.operating_system for a in assets if a.operating_system}
            )
            base_data["operating_systems"] = operating_systems
            base_data["total_assets"] = len(assets)
            base_data["environments"] = list(
                {a.environment for a in assets if a.environment}
            )

        return base_data

    def _serialize_server(self, srv: Asset) -> Dict[str, Any]:
        """Serialize server asset to dictionary.

        Args:
            srv: Asset model with asset_type='server'

        Returns:
            Dictionary with server infrastructure details
        """
        return {
            "id": str(srv.id),
            "name": srv.name or srv.asset_name,
            "hostname": srv.hostname,
            "ip_address": srv.ip_address,
            "operating_system": srv.operating_system,
            "os_version": srv.os_version,
            "cpu_cores": srv.cpu_cores,
            "memory_gb": srv.memory_gb,
            "storage_gb": srv.storage_gb,
            "environment": srv.environment,
            "asset_type": srv.asset_type,
        }

    # === HELPER METHODS ===

    def _extract_phase_results(
        self, flow: AssessmentFlow, phase_name: str
    ) -> Dict[str, Any]:
        """Extract results for a specific phase from flow state."""
        if not flow or not flow.phase_results:
            return {}

        phase_data = flow.phase_results.get(phase_name, {})
        return phase_data if isinstance(phase_data, dict) else {}

    def _extract_business_constraints(self, flow: AssessmentFlow) -> Dict[str, Any]:
        """Extract business constraints from flow metadata."""
        if not flow or not flow.flow_metadata:
            return {"objectives": [], "timeline": {}, "budget": {}}

        metadata = flow.flow_metadata
        return {
            "objectives": metadata.get("business_objectives", []),
            "timeline": metadata.get("timeline_constraints", {}),
            "budget": metadata.get("budget_constraints", {}),
        }

    # === EMPTY DATA METHODS (GRACEFUL DEGRADATION) ===

    def _empty_readiness_data(self) -> Dict[str, Any]:
        """Return empty readiness data structure."""
        return {
            "applications": [],
            "discovery_results": {},
            "collected_inventory": {"by_type": [], "total_items": 0},
            "infrastructure_count": 0,
            "engagement_id": str(self.engagement_id),
            "client_account_id": str(self.client_account_id),
        }

    def _empty_complexity_data(self) -> Dict[str, Any]:
        """Return empty complexity data structure."""
        return {
            "applications": [],
            "inventory_by_type": {},
            "complexity_indicators": {},
            "total_applications": 0,
            "engagement_id": str(self.engagement_id),
        }

    def _empty_dependency_data(self) -> Dict[str, Any]:
        """Return empty dependency data structure."""
        return {
            "applications": [],
            "infrastructure": [],
            "dependency_graph": {
                "nodes": {"applications": [], "servers": []},
                "edges": [],
            },
            "collected_inventory": {"by_type": [], "total_items": 0},
            "engagement_id": str(self.engagement_id),
        }

    def _empty_risk_data(self) -> Dict[str, Any]:
        """Return empty risk data structure."""
        return {
            "readiness_results": {},
            "complexity_results": {},
            "dependency_results": {},
            "applications": [],
            "business_impact_data": {},
            "engagement_id": str(self.engagement_id),
        }

    def _empty_recommendation_data(self) -> Dict[str, Any]:
        """Return empty recommendation data structure."""
        return {
            "all_phase_results": {},
            "applications": [],
            "business_objectives": [],
            "timeline_constraints": {},
            "budget_constraints": {},
            "engagement_id": str(self.engagement_id),
        }
