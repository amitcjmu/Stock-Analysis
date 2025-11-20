#!/usr/bin/env python3
"""
Test script for asset write-back with enhanced field mappings
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend')

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.services.flow_configs.collection_handlers.asset_handlers import asset_handlers

async def test_asset_writeback():
    # Database connection
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Test context
        context = {
            "client_account_id": "11111111-def0-def0-def0-111111111111",
            "engagement_id": "22222222-def0-def0-def0-222222222222",
            "batch_size": 300
        }

        collection_flow_id = UUID("f1b1ddcb-5830-4230-ae33-be61be7545dd")

        print("🧪 Testing asset write-back with enhanced field mappings...")
        print(f"Flow ID: {collection_flow_id}")
        print(f"Context: {context}")

        try:
            await asset_handlers.apply_resolved_gaps_to_assets(
                db, collection_flow_id, context
            )
            print("✅ Asset write-back completed successfully")
        except Exception as e:
            print(f"❌ Asset write-back failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_asset_writeback())
