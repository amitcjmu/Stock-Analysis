"""
Resource Skill Operations.

Provides CRUD operations for resource skills and skill gap analysis.
"""

import logging
import uuid
from typing import List

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.models.planning import ResourceSkill

logger = logging.getLogger(__name__)


class ResourceSkillOperationsMixin:
    """Mixin for resource skill operations."""

    # ===========================
    # Resource Skills Operations
    # ===========================

    async def create_resource_skill(
        self,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        wave_id: uuid.UUID,
        skill_name: str,
        required_hours: float,
        **kwargs,
    ) -> ResourceSkill:
        """
        Create resource skill requirement.

        Args:
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
            wave_id: Wave UUID
            skill_name: Skill name
            required_hours: Required hours for this skill
            **kwargs: Additional skill fields

        Returns:
            Created ResourceSkill instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            skill = ResourceSkill(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                wave_id=wave_id,
                skill_name=skill_name,
                required_hours=required_hours,
                **kwargs,
            )

            self.db.add(skill)
            await self.db.flush()

            logger.info(f"Created resource skill: {skill_name} for wave_id={wave_id}")

            return skill

        except SQLAlchemyError as e:
            logger.error(f"Failed to create resource skill: {e}")
            raise

    async def list_skills_by_wave(
        self,
        wave_id: uuid.UUID,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> List[ResourceSkill]:
        """
        Get all skill requirements for a wave.

        Args:
            wave_id: Wave UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

        Returns:
            List of ResourceSkill instances
        """
        try:
            stmt = select(ResourceSkill).where(
                and_(
                    ResourceSkill.wave_id == wave_id,
                    ResourceSkill.client_account_id == client_account_id,
                    ResourceSkill.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            skills = result.scalars().all()

            logger.debug(f"Retrieved {len(skills)} skills for wave_id: {wave_id}")

            return list(skills)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving skills for wave_id {wave_id}: {e}")
            return []

    async def list_skill_gaps_by_wave(
        self,
        wave_id: uuid.UUID,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> List[ResourceSkill]:
        """
        Get all skill gaps for a wave.

        Args:
            wave_id: Wave UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

        Returns:
            List of ResourceSkill instances with has_gap=True
        """
        try:
            stmt = select(ResourceSkill).where(
                and_(
                    ResourceSkill.wave_id == wave_id,
                    ResourceSkill.client_account_id == client_account_id,
                    ResourceSkill.engagement_id == engagement_id,
                    ResourceSkill.has_gap
                    == True,  # noqa: E712 - Per coding-agent-guide.md
                )
            )

            result = await self.db.execute(stmt)
            gaps = result.scalars().all()

            logger.debug(f"Retrieved {len(gaps)} skill gaps for wave_id: {wave_id}")

            return list(gaps)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving skill gaps for wave_id {wave_id}: {e}")
            return []
