"""
Migration script to add timeout tracking to discovery flows
"""

import asyncio
import logging

from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_timeout_column():
    """Add timeout_at column to discovery_flows table"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if column already exists
            check_query = text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'discovery_flows'
                AND column_name = 'timeout_at'
            """
            )

            result = await db.execute(check_query)
            exists = result.scalar()

            if not exists:
                logger.info("Adding timeout_at column to discovery_flows table...")

                # Add the column
                add_column_query = text(
                    """
                    ALTER TABLE discovery_flows
                    ADD COLUMN timeout_at TIMESTAMP WITH TIME ZONE
                """
                )

                await db.execute(add_column_query)
                await db.commit()

                logger.info("✅ Added timeout_at column")

                # Update existing flows with default timeout (24 hours from creation)
                update_query = text(
                    """
                    UPDATE discovery_flows
                    SET timeout_at = created_at + INTERVAL '24 hours'
                    WHERE timeout_at IS NULL
                """
                )

                result = await db.execute(update_query)
                await db.commit()

                logger.info(f"✅ Updated {result.rowcount} flows with default timeout")
            else:
                logger.info("✅ timeout_at column already exists")

        except Exception as e:
            logger.error(f"❌ Error adding timeout column: {e}")
            await db.rollback()
            raise


async def add_stuck_detection_index():
    """Add index for efficient stuck flow detection"""
    async with AsyncSessionLocal() as db:
        try:
            # Create index for stuck flow queries
            index_query = text(
                """
                CREATE INDEX IF NOT EXISTS idx_discovery_flows_stuck_detection
                ON discovery_flows (status, progress_percentage, created_at)
                WHERE status IN ('active', 'initialized', 'running')
                AND progress_percentage = 0.0
            """
            )

            await db.execute(index_query)
            await db.commit()

            logger.info("✅ Created stuck flow detection index")

        except Exception as e:
            logger.error(f"❌ Error creating index: {e}")
            await db.rollback()


async def update_flow_health_metrics():
    """Update flow health metrics in existing flows"""
    async with AsyncSessionLocal() as db:
        try:
            # Add health check timestamp to state data
            update_query = text(
                """
                UPDATE discovery_flows
                SET crewai_state_data =
                    CASE
                        WHEN crewai_state_data IS NULL THEN
                            jsonb_build_object('metadata', jsonb_build_object(
                                'health_check_at', to_jsonb(now()),
                                'created_at', to_jsonb(created_at)
                            ))
                        WHEN crewai_state_data->'metadata' IS NULL THEN
                            crewai_state_data || jsonb_build_object('metadata', jsonb_build_object(
                                'health_check_at', to_jsonb(now()),
                                'created_at', to_jsonb(created_at)
                            ))
                        ELSE
                            jsonb_set(
                                crewai_state_data,
                                '{metadata,health_check_at}',
                                to_jsonb(now())
                            )
                    END
                WHERE status IN ('active', 'initialized', 'running')
            """
            )

            result = await db.execute(update_query)
            await db.commit()

            logger.info(f"✅ Updated health metrics for {result.rowcount} active flows")

        except Exception as e:
            logger.error(f"❌ Error updating health metrics: {e}")
            await db.rollback()


async def main():
    """Run all migrations"""
    logger.info("🚀 Starting flow health migrations...")

    # Add timeout column
    await add_timeout_column()

    # Add performance index
    await add_stuck_detection_index()

    # Update health metrics
    await update_flow_health_metrics()

    logger.info("\n✅ All migrations completed!")


if __name__ == "__main__":
    asyncio.run(main())
