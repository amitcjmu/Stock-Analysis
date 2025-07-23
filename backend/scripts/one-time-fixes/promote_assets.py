#!/usr/bin/env python3
"""
Manual Asset Promotion Script
Promotes discovery assets to main assets table for completed discovery flows
"""

import asyncio
import logging
import uuid

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.services.asset_creation_bridge_service import AssetCreationBridgeService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def promote_discovery_assets(flow_id: str):
    """Promote discovery assets to main assets table"""
    async with AsyncSessionLocal() as session:
        try:
            # Create context for demo client
            context = RequestContext(
                user_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
                client_account_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                engagement_id=uuid.UUID("22222222-2222-2222-2222-222222222222")
            )
            
            # Initialize asset creation bridge service
            bridge_service = AssetCreationBridgeService(session, context)
            
            # Create assets from discovery flow
            logger.info(f"🏗️ Starting asset promotion for flow: {flow_id}")
            result = await bridge_service.create_assets_from_discovery(
                discovery_flow_id=uuid.UUID(flow_id)
            )
            
            logger.info("✅ Asset promotion completed!")
            logger.info(f"📊 Results: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Asset promotion failed: {e}")
            raise

if __name__ == "__main__":
    flow_id = "e182c467-1189-4125-ad9a-5d406aeae437"
    result = asyncio.run(promote_discovery_assets(flow_id))
    print(f"Promotion result: {result}") 