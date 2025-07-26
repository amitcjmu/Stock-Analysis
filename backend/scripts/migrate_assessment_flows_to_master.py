#!/usr/bin/env python3
"""
Migration script to register existing assessment flows with the master flow system.
This ensures all assessment flows are tracked in the crewai_flow_state_extensions table.
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.assessment_flow import AssessmentFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def migrate_assessment_flows():
    """Register existing assessment flows with master flow system"""

    async with AsyncSessionLocal() as db:
        try:
            # Count total assessment flows
            count_result = await db.execute(select(func.count(AssessmentFlow.id)))
            total_flows = count_result.scalar() or 0
            logger.info(f"Found {total_flows} assessment flows to check")

            if total_flows == 0:
                logger.info("No assessment flows found. Migration complete.")
                return

            # Get all assessment flows
            result = await db.execute(
                select(AssessmentFlow).order_by(AssessmentFlow.created_at)
            )
            assessment_flows = result.scalars().all()

            migrated_count = 0
            already_registered = 0
            failed_count = 0

            for flow in assessment_flows:
                flow_id = str(flow.id)

                # Check if already registered in master flow system
                master_check = await db.execute(
                    select(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.flow_id == flow.id
                    )
                )
                existing_master = master_check.scalar_one_or_none()

                if existing_master:
                    logger.info(
                        f"Assessment flow {flow_id} already registered in master flow system"
                    )
                    already_registered += 1
                    continue

                # Register with master flow system
                try:
                    extensions_repo = CrewAIFlowStateExtensionsRepository(
                        db,
                        str(flow.client_account_id),
                        str(flow.engagement_id),
                        user_id="migration-script",
                    )

                    # Calculate progress from flow state
                    progress = flow.progress or 0

                    # Determine flow status
                    flow_status = flow.status or "initialized"
                    if flow.completed_at:
                        flow_status = "completed"

                    await extensions_repo.create_master_flow(
                        flow_id=flow_id,
                        flow_type="assessment",
                        user_id="migration-script",
                        flow_name=f"Assessment Flow - {len(flow.selected_application_ids or [])} Applications (Migrated)",
                        flow_configuration={
                            "selected_applications": flow.selected_application_ids
                            or [],
                            "assessment_type": "sixr_analysis",
                            "migrated": True,
                            "original_created_at": (
                                flow.created_at.isoformat() if flow.created_at else None
                            ),
                            "engagement_id": str(flow.engagement_id),
                            "architecture_captured": flow.architecture_captured,
                            "progress": progress,
                        },
                        initial_state={
                            "phase": flow.current_phase or "initialization",
                            "status": flow_status,
                            "progress": progress,
                            "applications_count": len(
                                flow.selected_application_ids or []
                            ),
                            "migrated_at": datetime.utcnow().isoformat(),
                        },
                    )

                    # Update the master flow with current status
                    await extensions_repo.update_flow_status(
                        flow_id=flow_id,
                        status=flow_status,
                        phase_data={
                            "current_phase": flow.current_phase,
                            "next_phase": flow.next_phase,
                            "progress": progress,
                            "pause_points": flow.pause_points or [],
                            "apps_ready_for_planning": flow.apps_ready_for_planning
                            or [],
                        },
                    )

                    logger.info(
                        f"✅ Migrated assessment flow {flow_id} to master flow system"
                    )
                    migrated_count += 1

                except Exception as e:
                    logger.error(f"❌ Failed to migrate assessment flow {flow_id}: {e}")
                    failed_count += 1
                    continue

            # Commit all changes
            await db.commit()

            # Summary
            logger.info("\n" + "=" * 50)
            logger.info("MIGRATION SUMMARY")
            logger.info("=" * 50)
            logger.info(f"Total assessment flows: {total_flows}")
            logger.info(f"Already registered: {already_registered}")
            logger.info(f"Successfully migrated: {migrated_count}")
            logger.info(f"Failed to migrate: {failed_count}")
            logger.info("=" * 50)

            if failed_count > 0:
                logger.warning(
                    f"\n⚠️  {failed_count} flows failed to migrate. Check logs for details."
                )
            else:
                logger.info("\n✅ All assessment flows successfully migrated!")

        except Exception as e:
            logger.error(f"Migration failed with error: {e}")
            await db.rollback()
            raise


async def verify_migration():
    """Verify that all assessment flows are registered in master flow system"""

    async with AsyncSessionLocal() as db:
        # Count assessment flows
        assessment_count = await db.execute(select(func.count(AssessmentFlow.id)))
        total_assessment = assessment_count.scalar() or 0

        # Count master flows of type 'assessment'
        master_count = await db.execute(
            select(func.count(CrewAIFlowStateExtensions.id)).where(
                CrewAIFlowStateExtensions.flow_type == "assessment"
            )
        )
        total_master = master_count.scalar() or 0

        logger.info("\n" + "=" * 50)
        logger.info("VERIFICATION RESULTS")
        logger.info("=" * 50)
        logger.info(f"Total assessment flows: {total_assessment}")
        logger.info(f"Total master flow records (assessment): {total_master}")

        if total_assessment == total_master:
            logger.info("✅ All assessment flows are registered in master flow system!")
        else:
            logger.warning(
                f"⚠️  Mismatch: {total_assessment - total_master} assessment flows not registered"
            )
        logger.info("=" * 50)


async def main():
    """Main migration function"""
    logger.info("Starting assessment flow migration to master flow system...")

    try:
        # Run migration
        await migrate_assessment_flows()

        # Verify results
        await verify_migration()

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Import func here to avoid import errors
    from sqlalchemy import func

    asyncio.run(main())
