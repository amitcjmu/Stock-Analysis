"""
Architecture Commands - Architecture standards and overrides management
"""

import logging
from datetime import datetime
from typing import List

from sqlalchemy import and_, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import (
    ApplicationArchitectureOverride,
    EngagementArchitectureStandard,
)
from app.models.assessment_flow_state import (
    ApplicationArchitectureOverride as ApplicationArchitectureOverrideState,
)
from app.models.assessment_flow_state import (
    ArchitectureRequirement,
)

logger = logging.getLogger(__name__)


class ArchitectureCommands:
    """Commands for architecture standards and overrides management"""

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id

    async def save_architecture_standards(
        self, engagement_id: str, standards: List[ArchitectureRequirement]
    ):
        """Save or update engagement architecture standards"""

        for standard in standards:
            # Fix: Map Pydantic fields to database columns and provide required fields
            stmt = insert(EngagementArchitectureStandard).values(
                engagement_id=engagement_id,
                client_account_id=self.client_account_id,  # Required NOT NULL field
                requirement_type=standard.requirement_type,
                standard_name=standard.description,  # Use description as unique standard_name
                description=standard.description,
                is_mandatory=standard.mandatory,  # Map mandatory -> is_mandatory
                supported_versions=standard.supported_versions,
                requirement_details=standard.requirement_details,
                # Provide required NOT NULL fields with sensible defaults
                minimum_requirements={},
                preferred_patterns={},
                constraints={},
                compliance_level="standard",
                priority=5,
                business_impact="medium",
                score_metadata={},
                updated_at=datetime.utcnow(),
            )

            # Unique constraint is (engagement_id, requirement_type, standard_name)
            stmt = stmt.on_conflict_do_update(
                index_elements=["engagement_id", "requirement_type", "standard_name"],
                set_=dict(
                    description=stmt.excluded.description,
                    is_mandatory=stmt.excluded.is_mandatory,  # Map mandatory -> is_mandatory
                    supported_versions=stmt.excluded.supported_versions,
                    requirement_details=stmt.excluded.requirement_details,
                    updated_at=stmt.excluded.updated_at,
                ),
            )

            await self.db.execute(stmt)

        await self.db.commit()
        logger.info(
            f"Saved {len(standards)} architecture standards for engagement {engagement_id}"
        )

    async def save_application_overrides(
        self,
        flow_id: str,
        app_id: str,
        overrides: List[ApplicationArchitectureOverrideState],
    ):
        """Save application architecture overrides"""

        # Delete existing overrides for this app in this flow
        await self.db.execute(
            delete(ApplicationArchitectureOverride).where(
                and_(
                    ApplicationArchitectureOverride.assessment_flow_id == flow_id,
                    ApplicationArchitectureOverride.application_id == app_id,
                )
            )
        )

        # Insert new overrides
        for override in overrides:
            override_record = ApplicationArchitectureOverride(
                assessment_flow_id=flow_id,
                application_id=app_id,
                standard_id=override.standard_id,
                override_type=override.override_type.value,
                override_details=override.override_details,
                rationale=override.rationale,
                approved_by=override.approved_by,
            )
            self.db.add(override_record)

        await self.db.commit()
