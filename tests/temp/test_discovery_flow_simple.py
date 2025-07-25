#!/usr/bin/env python3
"""
Simple test to verify Discovery Flow execution after repository fixes
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_discovery_flow():
    """Test Discovery Flow execution with simple data"""
    try:
        # Mock CMDB data
        mock_data = [
            {
                "hostname": "web-server-01",
                "type": "Server",
                "os": "Linux",
                "application": "WebApp",
                "environment": "Production"
            },
            {
                "hostname": "db-server-01",
                "type": "Database",
                "os": "Linux",
                "application": "MySQL",
                "environment": "Production"
            }
        ]

        # Mock metadata
        metadata = {
            "client_account_id": "11111111-1111-1111-1111-111111111111",
            "engagement_id": "22222222-2222-2222-2222-222222222222",
            "user_id": "347d1ecd-04f6-4e3a-86ca-d35703512301",
            "source": "test_upload",
            "filename": "test_data.csv"
        }

        # Try to import data import handler
        try:
            from app.api.v1.endpoints.data_import.handlers.import_storage_handler import _trigger_discovery_flow
            handler_available = True
            logger.info("✅ Data import handler available")
        except ImportError as e:
            logger.error(f"❌ Data import handler not available: {e}")
            handler_available = False

        if not handler_available:
            logger.info("❌ Cannot test Discovery Flow without data import handler")
            return False

        # Try to create discovery flow
        try:
            from app.core.database import AsyncSessionLocal
            from app.core.context import RequestContext

            # Create session and context
            async with AsyncSessionLocal() as db:
                context = RequestContext(
                    client_account_id=metadata["client_account_id"],
                    engagement_id=metadata["engagement_id"],
                    user_id=metadata["user_id"]
                )

                logger.info("🚀 Creating Discovery Flow with test data...")

                # Create Discovery Flow directly
                flow_id = await _trigger_discovery_flow(
                    data_import_id="test-data-import-123",
                    client_account_id=metadata["client_account_id"],
                    engagement_id=metadata["engagement_id"],
                    user_id=metadata["user_id"],
                    file_data=mock_data,
                    context=context
                )

                if flow_id:
                    logger.info(f"✅ Discovery Flow created successfully: {flow_id}")

                    # Check flow status
                    from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
                    flow_repo = DiscoveryFlowRepository(
                        db,
                        metadata["client_account_id"],
                        metadata["engagement_id"],
                        user_id=metadata["user_id"]
                    )

                    flow = await flow_repo.get_by_flow_id(flow_id)
                    if flow:
                        logger.info(f"✅ Flow found in database: {flow.status}")
                        logger.info(f"📊 Flow details: {flow.flow_id}, Status: {flow.status}, Phase: {flow.get_next_phase()}")
                        return True
                    else:
                        logger.error(f"❌ Flow not found in database: {flow_id}")
                        return False
                else:
                    logger.error(f"❌ Failed to create Discovery Flow. Flow ID: {flow_id}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error creating Discovery Flow: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_discovery_flow())
    if success:
        print("🎉 Discovery Flow test PASSED")
    else:
        print("💥 Discovery Flow test FAILED")
