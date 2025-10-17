"""
Discovery to Collection Bridge Service

This service manages the transition from Discovery flow outputs (completed inventory)
to Collection flow inputs (gap analysis and questionnaire generation).
"""

import logging
from typing import Dict, List, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
    AutomationTier,
)
from app.models.asset import Asset
from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class DiscoveryToCollectionBridge:
    """Manages state transfer from Discovery to Collection flows"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def validate_discovery_flow(self, discovery_flow_id: UUID) -> DiscoveryFlow:
        """Validate that Discovery flow is complete and ready for transition"""
        result = await self.db.execute(
            select(DiscoveryFlow).where(
                DiscoveryFlow.id == discovery_flow_id,
                DiscoveryFlow.engagement_id == self.context.engagement_id,
                DiscoveryFlow.status == "completed",
            )
        )
        discovery_flow = result.scalar_one_or_none()

        if not discovery_flow:
            raise ValueError(
                f"Discovery flow {discovery_flow_id} not found or not completed"
            )

        return discovery_flow

    async def extract_application_data(
        self, selected_app_ids: List[UUID]
    ) -> List[Dict[str, Any]]:
        """Extract application data from inventory for selected applications"""
        result = await self.db.execute(
            select(Asset).where(
                Asset.id.in_(selected_app_ids),
                Asset.engagement_id == self.context.engagement_id,
            )
        )
        applications = result.scalars().all()

        app_data = []
        for app in applications:
            # Get associated assets for each application
            asset_result = await self.db.execute(
                select(Asset).where(
                    Asset.application_id == app.id,
                    Asset.engagement_id == self.context.engagement_id,
                )
            )
            assets = asset_result.scalars().all()

            app_data.append(
                {
                    "id": str(app.id),
                    "name": app.name,
                    "business_criticality": app.business_criticality,
                    "technology_stack": app.technology_stack,
                    "architecture_pattern": app.architecture_pattern,
                    "integration_dependencies": app.integration_dependencies,
                    "data_characteristics": app.data_characteristics,
                    "discovery_snapshot": {
                        "discovered_at": app.created_at.isoformat(),
                        "asset_count": len(assets),
                        "completeness_score": self._calculate_completeness(app),
                    },
                    "assets": [
                        {
                            "id": str(asset.id),
                            "name": asset.name,
                            "type": asset.asset_type,
                            "operating_system": asset.operating_system,
                            "specifications": asset.specifications,
                        }
                        for asset in assets[:10]  # Limit for metadata size
                    ],
                }
            )

        return app_data

    async def determine_tier_from_discovery(self, discovery_flow: DiscoveryFlow) -> str:
        """Determine automation tier based on Discovery results"""
        metadata = discovery_flow.metadata or {}

        # Check platform capabilities detected during Discovery
        platforms_detected = metadata.get("platforms_detected", [])
        api_access = metadata.get("api_access_available", False)
        credential_types = metadata.get("credential_types", [])

        # Tier determination logic based on Discovery findings
        if api_access and "aws" in platforms_detected:
            return AutomationTier.TIER_4.value  # Fully automated
        elif api_access and any(p in platforms_detected for p in ["azure", "gcp"]):
            return AutomationTier.TIER_3.value  # API-integrated
        elif credential_types:
            return AutomationTier.TIER_2.value  # Script-assisted
        else:
            return AutomationTier.TIER_1.value  # Manual/template-based

    async def create_collection_flow(
        self,
        discovery_flow_id: UUID,
        applications: List[Dict[str, Any]],
        automation_tier: str,
        start_phase: str = "gap_analysis",
    ) -> CollectionFlow:
        """
        Create Collection flow with Discovery context.
        Uses CollectionFlowRepository to ensure MFO registration (ADR-006).
        """
        from app.repositories.collection_flow_repository import CollectionFlowRepository
        from uuid import uuid4

        flow_id = uuid4()

        # Use repository pattern to ensure MFO registration (ADR-006)
        collection_repo = CollectionFlowRepository(
            db=self.db,
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
        )

        # Create flow with MFO registration
        collection_flow = await collection_repo.create(
            flow_name=f"Collection from Discovery - {len(applications)} apps",
            automation_tier=automation_tier,
            flow_metadata={
                "discovery_flow_id": str(discovery_flow_id),
                "created_from": "discovery_bridge",
                "application_count": len(applications),
            },
            collection_config={
                "discovery_flow_id": str(discovery_flow_id),
                "application_count": len(applications),
                "start_phase": start_phase,
                "applications": applications,
            },
            flow_id=flow_id,
            user_id=self.context.user_id,
            discovery_flow_id=discovery_flow_id,
            current_phase=start_phase,
        )

        logger.info(
            f"✅ Collection flow {collection_flow.id} registered with MFO "
            f"(master_flow_id: {collection_flow.flow_id})"
        )

        return collection_flow

    async def trigger_gap_analysis(
        self, collection_flow: CollectionFlow, app_data: List[Dict[str, Any]]
    ) -> None:
        """Trigger immediate gap analysis for selected applications"""
        # This will be handled by the CrewAI flow phases
        # Here we just update the flow state to indicate gap analysis should start
        collection_flow.status = (
            CollectionFlowStatus.RUNNING.value
        )  # Per ADR-012: Flow is now actively running
        collection_flow.current_phase = CollectionPhase.GAP_ANALYSIS.value
        collection_flow.phase_state = {
            "gap_analysis": {
                "status": "pending",
                "applications_to_analyze": [app["id"] for app in app_data],
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        }
        await self.db.commit()

    def _calculate_completeness(self, app: Asset) -> float:
        """Calculate completeness score for an application based on available attributes"""
        # List of critical attributes for 6R decision
        critical_attributes = [
            "name",
            "business_criticality",
            "technology_stack",
            "architecture_pattern",
            "integration_dependencies",
            "data_characteristics",
            "user_load_patterns",
            "compliance_requirements",
            "security_requirements",
            "performance_baseline",
        ]

        # Count how many attributes are populated
        populated = 0
        for attr in critical_attributes:
            value = getattr(app, attr, None)
            if value is not None and value != "" and value != {}:
                populated += 1

        return (populated / len(critical_attributes)) * 100

    async def create_collection_from_discovery(
        self,
        discovery_flow_id: UUID,
        selected_app_ids: List[UUID],
        context: RequestContext,
    ) -> CollectionFlow:
        """Main method to create Collection flow from Discovery results"""
        # 1. Validate Discovery flow is complete
        discovery_flow = await self.validate_discovery_flow(discovery_flow_id)

        # 2. Extract application data from inventory
        app_data = await self.extract_application_data(selected_app_ids)

        # 3. Determine automation tier from Discovery results
        tier = await self.determine_tier_from_discovery(discovery_flow)

        # 4. Create Collection flow with context
        collection_flow = await self.create_collection_flow(
            discovery_flow_id=discovery_flow_id,
            applications=app_data,
            automation_tier=tier,
            start_phase="gap_analysis",
        )

        # 5. Trigger immediate gap analysis
        await self.trigger_gap_analysis(collection_flow, app_data)

        logger.info(
            f"Created Collection flow {collection_flow.id} from Discovery flow "
            f"{discovery_flow_id} with {len(app_data)} applications"
        )

        return collection_flow


class CriticalAttributesFramework:
    """Defines and validates the 22 critical attributes for 6R decisions"""

    INFRASTRUCTURE_ATTRIBUTES = [
        "operating_system_version",
        "cpu_memory_storage_specs",
        "network_configuration",
        "virtualization_platform",
        "performance_baseline",
        "availability_requirements",
    ]

    APPLICATION_ATTRIBUTES = [
        "technology_stack",
        "architecture_pattern",
        "integration_dependencies",
        "data_volume_characteristics",
        "user_load_patterns",
        "business_logic_complexity",
        "configuration_complexity",
        "security_compliance_requirements",
    ]

    BUSINESS_CONTEXT_ATTRIBUTES = [
        "business_criticality_score",
        "change_tolerance",
        "compliance_constraints",
        "stakeholder_impact",
    ]

    TECHNICAL_DEBT_ATTRIBUTES = [
        "code_quality_metrics",
        "security_vulnerabilities",
        "eol_technology_assessment",
        "documentation_quality",
    ]

    async def analyze_gaps(
        self, app_data: Dict[str, Any], db: AsyncSession
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze which critical attributes are missing"""
        gaps = {"critical": [], "important": [], "optional": []}

        # Check infrastructure attributes
        for attr in self.INFRASTRUCTURE_ATTRIBUTES:
            if not self._has_attribute(app_data, attr):
                gaps["critical"].append(self._create_gap(attr, "infrastructure"))

        # Check application attributes
        for attr in self.APPLICATION_ATTRIBUTES:
            if not self._has_attribute(app_data, attr):
                severity = (
                    "critical"
                    if attr in ["technology_stack", "architecture_pattern"]
                    else "important"
                )
                gaps[severity].append(self._create_gap(attr, "application"))

        # Check business context attributes
        for attr in self.BUSINESS_CONTEXT_ATTRIBUTES:
            if not self._has_attribute(app_data, attr):
                gaps["important"].append(self._create_gap(attr, "business_context"))

        # Check technical debt attributes
        for attr in self.TECHNICAL_DEBT_ATTRIBUTES:
            if not self._has_attribute(app_data, attr):
                gaps["optional"].append(self._create_gap(attr, "technical_debt"))

        return gaps

    def _has_attribute(self, app_data: Dict[str, Any], attr: str) -> bool:
        """Check if an attribute exists and has meaningful data"""
        value = app_data.get(attr)
        return value is not None and value != "" and value != {} and value != []

    def _create_gap(self, attr: str, category: str) -> Dict[str, Any]:
        """Create a gap record for a missing attribute"""
        return {
            "attribute_name": attr,
            "attribute_category": category,
            "description": f"Missing {attr.replace('_', ' ').title()}",
            "business_impact": self._assess_business_impact(attr),
            "collection_difficulty": self._assess_collection_difficulty(attr),
        }

    def _assess_business_impact(self, attr: str) -> str:
        """Assess the business impact of a missing attribute"""
        high_impact = [
            "business_criticality_score",
            "technology_stack",
            "architecture_pattern",
            "security_compliance_requirements",
        ]
        medium_impact = [
            "integration_dependencies",
            "performance_baseline",
            "user_load_patterns",
        ]

        if attr in high_impact:
            return "high"
        elif attr in medium_impact:
            return "medium"
        else:
            return "low"

    def _assess_collection_difficulty(self, attr: str) -> str:
        """Assess how difficult it is to collect this attribute"""
        easy = ["operating_system_version", "cpu_memory_storage_specs"]
        medium = [
            "technology_stack",
            "architecture_pattern",
            "integration_dependencies",
        ]
        hard = ["business_logic_complexity", "change_tolerance", "stakeholder_impact"]

        if attr in easy:
            return "easy"
        elif attr in medium:
            return "medium"
        elif attr in hard:
            return "hard"
        else:
            return "medium"
