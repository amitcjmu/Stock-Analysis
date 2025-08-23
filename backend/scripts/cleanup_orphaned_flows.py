"""
Cleanup Orphaned Discovery Flows

This script finds and deletes discovery flows that have no master_flow_id,
which means they're orphaned and can't be properly managed by the master flow system.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import and_, select, update

from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow
from app.models.flow_deletion_audit import FlowDeletionAudit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_orphaned_flows():
    """Find and delete all discovery flows with no master_flow_id"""

    async with AsyncSessionLocal() as db:
        try:
            # Find all orphaned discovery flows (no master_flow_id)
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.master_flow_id.is_(None),
                    DiscoveryFlow.status != "deleted",
                )
            )

            result = await db.execute(stmt)
            orphaned_flows = result.scalars().all()

            if not orphaned_flows:
                logger.info("No orphaned flows found.")
                return

            logger.info(f"Found {len(orphaned_flows)} orphaned discovery flows")

            # Log details of each orphaned flow
            for flow in orphaned_flows:
                logger.info(
                    f"  - Flow ID: {flow.flow_id}, Status: {flow.status}, "
                    f"Phase: {flow.current_phase}, Created: {flow.created_at}"
                )

            # Mark all orphaned flows as deleted
            update_stmt = (
                update(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.master_flow_id.is_(None),
                        DiscoveryFlow.status != "deleted",
                    )
                )
                .values(status="deleted", updated_at=datetime.utcnow())
            )

            result = await db.execute(update_stmt)
            flows_deleted = result.rowcount

            # Create audit record for the cleanup
            import uuid

            audit_flow_id = str(uuid.uuid4())  # Generate a valid UUID for the audit

            # Create audit record with defensive handling
            from app.utils.flow_deletion_utils import safely_create_deletion_audit

            audit_record = FlowDeletionAudit.create_audit_record(
                flow_id=audit_flow_id,
                client_account_id="11111111-1111-1111-1111-111111111111",  # Demo client ID
                engagement_id="22222222-2222-2222-2222-222222222222",  # Demo engagement ID
                user_id="SYSTEM_CLEANUP",
                deletion_type="system_cleanup",
                deletion_method="script",
                deleted_by="cleanup_orphaned_flows.py",
                deletion_reason="Cleaning up orphaned discovery flows with no master_flow_id",
                data_deleted={
                    "orphaned_flows_count": len(orphaned_flows),
                    "flow_ids": [str(f.flow_id) for f in orphaned_flows],
                },
                deletion_impact={
                    "flows_marked_deleted": flows_deleted,
                    "soft_delete": True,
                },
                cleanup_summary={"orphaned_flows_cleaned": flows_deleted},
                deletion_duration_ms=0,
            )

            # Safely create audit record (handles missing table scenario)
            audit_id = await safely_create_deletion_audit(
                db, audit_record, audit_flow_id, "orphaned_flow_cleanup"
            )
            await db.commit()

            logger.info(
                f"Successfully marked {flows_deleted} orphaned flows as deleted"
            )
            if audit_id:
                logger.info(f"Audit record created: {audit_id}")
            else:
                logger.warning(
                    "Audit record skipped - table not found (expected during initial migration)"
                )

            # Also check for any master flows that might be in inconsistent state
            logger.info("\nChecking for inconsistent master flows...")

            # Find master flows in 'cancelled' state that might need cleanup
            master_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_status == "cancelled"
            )

            master_result = await db.execute(master_stmt)
            cancelled_masters = master_result.scalars().all()

            if cancelled_masters:
                logger.info(f"Found {len(cancelled_masters)} cancelled master flows:")
                for master in cancelled_masters:
                    logger.info(
                        f"  - Master Flow ID: {master.flow_id}, Type: {master.flow_type}, "
                        f"Name: {master.flow_name}"
                    )

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            await db.rollback()
            raise


async def main():
    """Main entry point"""
    logger.info("Starting orphaned flow cleanup...")
    await cleanup_orphaned_flows()
    logger.info("Cleanup complete!")


if __name__ == "__main__":
    asyncio.run(main())
