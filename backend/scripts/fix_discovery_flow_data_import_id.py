#!/usr/bin/env python3
"""
Fix missing data_import_id in discovery_flows table.
Maps import_session_id to data_import_id for existing flows.
"""

import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_data_import_ids():
    """Update discovery flows to set data_import_id from import_session_id"""

    async with AsyncSessionLocal() as db:
        try:
            # Find all discovery flows with import_session_id but no data_import_id
            result = await db.execute(
                select(DiscoveryFlow).where(
                    DiscoveryFlow.import_session_id.isnot(None),
                    DiscoveryFlow.data_import_id.is_(None),
                )
            )
            flows = result.scalars().all()

            logger.info(
                f"Found {len(flows)} flows with import_session_id but no data_import_id"
            )

            fixed_count = 0
            for flow in flows:
                logger.info(f"\nProcessing flow {flow.flow_id}")
                logger.info(f"  import_session_id: {flow.import_session_id}")

                # The import_session_id is actually the data_import_id
                # (based on how the data is stored in import_storage_handler.py)
                if flow.import_session_id:
                    flow.data_import_id = flow.import_session_id
                    logger.info(f"  Set data_import_id to: {flow.data_import_id}")
                    fixed_count += 1

            if fixed_count > 0:
                await db.commit()
                logger.info(
                    f"\n✅ Successfully updated {fixed_count} discovery flows with data_import_id"
                )
            else:
                logger.info("\n✅ No flows needed updating")

            # Verify the fix
            logger.info("\n🔍 Verifying the fix:")
            result = await db.execute(
                select(DiscoveryFlow)
                .where(DiscoveryFlow.data_import_id.isnot(None))
                .order_by(DiscoveryFlow.created_at.desc())
                .limit(5)
            )
            fixed_flows = result.scalars().all()

            for flow in fixed_flows:
                logger.info(f"\n  Flow {flow.flow_id}:")
                logger.info(f"    data_import_id: {flow.data_import_id}")
                logger.info(f"    import_session_id: {flow.import_session_id}")

        except Exception as e:
            logger.error(f"❌ Error fixing data_import_ids: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(fix_data_import_ids())
