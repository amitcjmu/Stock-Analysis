#!/usr/bin/env python3
"""
Script to update the flow phase to progress past field_mapping_approval
"""

import asyncio
import logging

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.core.security.secure_logging import mask_id

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flow ID to process
FLOW_ID = "582b87c4-0df1-4c2f-aa3b-e4b5a287d725"


async def update_flow_state():
    """Update flow state to continue processing"""
    async with AsyncSessionLocal() as db:
        try:
            # Update discovery_flows table
            update_discovery_query = text(
                """
                UPDATE discovery_flows
                SET current_phase = 'data_cleansing',
                    field_mapping_completed = true,
                    progress_percentage = 33.3,
                    phases_completed = COALESCE(phases_completed, '[]'::json)::jsonb
                                       || '["field_mapping_approval"]'::jsonb,
                    updated_at = NOW()
                WHERE flow_id = :flow_id
            """
            )

            await db.execute(update_discovery_query, {"flow_id": FLOW_ID})
            await db.commit()
            logger.info(
                f"✅ Updated discovery flow phase to data_cleansing "
                f"for flow {mask_id(FLOW_ID)}"  # nosec B106
            )

            # Update crewai_flow_state_extensions table
            update_state_query = text(
                """
                UPDATE crewai_flow_state_extensions
                SET flow_persistence_data = jsonb_set(
                    jsonb_set(
                        jsonb_set(
                            jsonb_set(
                                flow_persistence_data,
                                '{current_phase}',
                                '"data_cleansing"'::jsonb
                            ),
                            '{completion}',
                            '"processing"'::jsonb
                        ),
                        '{awaiting_user_approval}',
                        'false'::jsonb
                    ),
                    '{progress_percentage}',
                    '50.0'::jsonb
                ),
                flow_status = 'processing',
                updated_at = NOW()
                WHERE flow_id = :flow_id
            """
            )

            await db.execute(update_state_query, {"flow_id": FLOW_ID})
            await db.commit()
            logger.info(
                f"✅ Updated crewai flow state to continue processing for flow {mask_id(FLOW_ID)}"  # nosec B106
            )

            # Trigger flow resume by updating a timestamp
            trigger_query = text(
                """
                UPDATE crewai_flow_state_extensions
                SET flow_persistence_data = jsonb_set(
                    flow_persistence_data,
                    '{resumed_at}',
                    to_jsonb(NOW()::text)
                )
                WHERE flow_id = :flow_id
            """
            )

            await db.execute(trigger_query, {"flow_id": FLOW_ID})
            await db.commit()
            logger.info("✅ Triggered flow resume")

            logger.info(
                "🎉 Flow successfully updated to progress past field mapping approval!"
            )

        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(update_flow_state())
