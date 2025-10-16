"""
State Queries - State construction helper methods
"""

import logging
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import (
    ApplicationArchitectureOverride,
    EngagementArchitectureStandard,
)
from app.models.assessment_flow_state import (
    ApplicationArchitectureOverride as ApplicationArchitectureOverrideState,
)
from app.models.assessment_flow_state import ArchitectureRequirement

logger = logging.getLogger(__name__)


class StateQueries:
    """Helper queries for state construction"""

    def __init__(self, db: AsyncSession, client_account_id: int):
        self.db = db
        self.client_account_id = client_account_id

    async def get_architecture_standards(
        self, engagement_id: str
    ) -> List[ArchitectureRequirement]:
        """Get architecture standards for engagement"""

        result = await self.db.execute(
            select(EngagementArchitectureStandard).where(
                EngagementArchitectureStandard.engagement_id == engagement_id
            )
        )
        standards = result.scalars().all()

        return [
            ArchitectureRequirement(
                requirement_type=std.requirement_type,
                description=std.description,
                mandatory=std.is_mandatory,  # Fixed: Use is_mandatory from database
                supported_versions=std.supported_versions,
                requirement_details=std.requirement_details,
                created_at=std.created_at,
                updated_at=std.updated_at,
            )
            for std in standards
        ]

    async def get_application_overrides(
        self, flow_id: str
    ) -> Dict[str, List[ApplicationArchitectureOverrideState]]:
        """Get application architecture overrides grouped by app"""

        result = await self.db.execute(
            select(ApplicationArchitectureOverride).where(
                ApplicationArchitectureOverride.assessment_flow_id == flow_id
            )
        )
        overrides = result.scalars().all()

        grouped = {}
        for override in overrides:
            app_id = str(override.application_id)
            if app_id not in grouped:
                grouped[app_id] = []

            grouped[app_id].append(
                ApplicationArchitectureOverrideState(
                    application_id=override.application_id,
                    standard_id=override.standard_id,
                    override_type=override.override_type,
                    override_details=override.override_details,
                    rationale=override.rationale,
                    approved_by=override.approved_by,
                    created_at=override.created_at,
                )
            )

        return grouped

    async def get_application_components(
        self, flow_id: str
    ) -> Dict[str, List[Any]]:
        """Get application components grouped by app"""

        # Note: application_components table doesn't have assessment_flow_id column
        # Return empty dict for now - table structure needs migration
        return {}

    async def get_tech_debt_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Get tech debt analysis and scores grouped by app"""

        # Note: tech_debt_analysis table name is singular, not plural
        # And it doesn't have assessment_flow_id column
        # Return empty for now - table structure needs migration
        return {"analysis": {}, "scores": {}}

    async def get_sixr_decisions(self, flow_id: str) -> Dict[str, Any]:
        """Get 6R decisions for all applications"""

        # Note: sixr_decisions table doesn't have assessment_flow_id column
        # Return empty dict for now - table structure needs migration
        return {}
