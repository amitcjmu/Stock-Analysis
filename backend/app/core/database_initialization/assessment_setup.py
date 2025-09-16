"""
Assessment table verification and standards setup.

This module handles verification of assessment flow tables and initialization
of assessment standards for engagements.
"""

import logging
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Engagement
from .base import ASSESSMENT_MODELS_AVAILABLE, EngagementArchitectureStandard

logger = logging.getLogger(__name__)


class AssessmentSetupService:
    """Manages assessment flow table verification and standards initialization"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_assessment_tables(self):
        """Verify assessment flow tables exist and are properly configured"""
        logger.info("Verifying assessment flow tables...")

        required_tables = [
            "assessment_flows",
            "engagement_architecture_standards",
            "application_architecture_overrides",
            "application_components",
            "tech_debt_analysis",
            "component_treatments",
            "sixr_decisions",
            "assessment_learning_feedback",
        ]

        missing_tables = []
        for table in required_tables:
            try:
                result = await self.db.execute(
                    text("SELECT to_regclass(:table_name)"), {"table_name": table}
                )
                if not result.scalar():
                    missing_tables.append(table)
            except Exception as e:
                logger.warning(f"Could not verify table {table}: {e}")
                missing_tables.append(table)

        if missing_tables:
            logger.warning(
                f"Missing assessment flow tables: {', '.join(missing_tables)}. "
                f"These tables have schema mismatches and will be addressed in future migration."
            )
            logger.info(
                "Continuing with initialization without assessment flow tables."
            )
        else:
            logger.info("All assessment flow tables verified successfully")

        return missing_tables

    async def ensure_engagement_assessment_standards(self):
        """Initialize assessment standards for existing engagements"""
        logger.info("Ensuring assessment standards for all engagements...")

        try:
            # Get all active engagements
            result = await self.db.execute(
                select(Engagement).where(Engagement.status == "active")
            )
            engagements = result.scalars().all()

            standards_initialized = 0
            if ASSESSMENT_MODELS_AVAILABLE and EngagementArchitectureStandard:
                # Import here to avoid circular imports
                from app.core.seed_data.assessment_standards import (
                    initialize_assessment_standards,
                )

                for engagement in engagements:
                    # Check if standards already exist
                    existing_standards = await self.db.execute(
                        select(EngagementArchitectureStandard).where(
                            EngagementArchitectureStandard.engagement_id
                            == engagement.id
                        )
                    )

                    if not existing_standards.first():
                        try:
                            await initialize_assessment_standards(
                                self.db, str(engagement.id)
                            )
                            standards_initialized += 1
                            logger.info(
                                f"Initialized assessment standards for engagement: {engagement.name}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to initialize standards for engagement {engagement.id}: {str(e)}"
                            )
                            continue
                    else:
                        logger.debug(
                            f"Standards already exist for engagement: {engagement.name}"
                        )
            else:
                logger.info(
                    "Assessment models not available yet, skipping standards initialization"
                )

            if standards_initialized > 0:
                logger.info(
                    f"Successfully initialized assessment standards for {standards_initialized} engagements"
                )
            else:
                logger.info("All engagements already have assessment standards")

            return standards_initialized

        except Exception as e:
            logger.error(f"Failed to ensure engagement assessment standards: {str(e)}")
            # Don't raise here - this shouldn't block the main initialization
            return 0

    async def audit_assessment_data_integrity(self):
        """Audit assessment data integrity"""
        issues = []

        if not ASSESSMENT_MODELS_AVAILABLE:
            issues.append("Assessment models not available")
            return issues

        try:
            # Check for engagements without standards
            result = await self.db.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM engagements e
                LEFT JOIN engagement_architecture_standards eas ON e.id = eas.engagement_id
                WHERE e.status = 'active' AND eas.engagement_id IS NULL
                """
                )
            )
            engagements_without_standards = result.scalar()

            if engagements_without_standards > 0:
                issues.append(
                    f"{engagements_without_standards} active engagements without assessment standards"
                )

            # Check for orphaned standards
            result = await self.db.execute(
                text(
                    """
                SELECT COUNT(*)
                FROM engagement_architecture_standards eas
                LEFT JOIN engagements e ON eas.engagement_id = e.id
                WHERE e.id IS NULL
                """
                )
            )
            orphaned_standards = result.scalar()

            if orphaned_standards > 0:
                issues.append(f"{orphaned_standards} orphaned assessment standards")

        except Exception as e:
            issues.append(f"Error checking assessment integrity: {str(e)}")

        if issues:
            logger.warning(f"Assessment integrity issues found: {', '.join(issues)}")
        else:
            logger.info("Assessment data integrity check passed")

        return issues

    async def cleanup_orphaned_assessment_data(self):
        """Clean up orphaned assessment data"""
        if not ASSESSMENT_MODELS_AVAILABLE:
            logger.info("Assessment models not available, skipping cleanup")
            return

        logger.info("Cleaning up orphaned assessment data...")

        try:
            # Remove orphaned standards
            result = await self.db.execute(
                text(
                    """
                DELETE FROM engagement_architecture_standards
                WHERE engagement_id NOT IN (SELECT id FROM engagements)
                """
                )
            )
            deleted_standards = result.rowcount

            if deleted_standards > 0:
                await self.db.commit()
                logger.info(
                    f"Removed {deleted_standards} orphaned assessment standards"
                )
            else:
                logger.info("No orphaned assessment standards found")

        except Exception as e:
            logger.error(f"Error cleaning up assessment data: {str(e)}")
            await self.db.rollback()
