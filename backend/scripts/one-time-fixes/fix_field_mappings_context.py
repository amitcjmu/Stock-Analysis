#!/usr/bin/env python
"""
Fix field mappings context issue by generating mappings for demo context
"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.core.database import get_db
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord


async def fix_field_mappings_context():
    async for db in get_db():
        try:
            # Get latest data import
            import_result = await db.execute(
                select(DataImport).order_by(DataImport.created_at.desc()).limit(1)
            )
            data_import = import_result.scalar_one_or_none()
            
            if not data_import:
                print("❌ No data import found")
                return
                
            print(f"Found data import: {data_import.id}")
            print(f"Current context - Client: {data_import.client_account_id}, Engagement: {data_import.engagement_id}")
            
            # Update to demo context
            demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
            demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
            
            # Update data import context
            data_import.client_account_id = demo_client_id
            data_import.engagement_id = demo_engagement_id
            
            # Update raw import records context
            await db.execute(
                update(RawImportRecord)
                .where(RawImportRecord.data_import_id == data_import.id)
                .values(
                    client_account_id=demo_client_id,
                    engagement_id=demo_engagement_id
                )
            )
            
            # Update field mappings context (if any exist)
            await db.execute(
                update(ImportFieldMapping)
                .where(ImportFieldMapping.data_import_id == data_import.id)
                .values(updated_at=datetime.utcnow())
            )
            
            await db.commit()
            print("✅ Updated data import to demo context")
            
            # Also update discovery flow context if needed
            from app.models.discovery_flow import DiscoveryFlow
            
            flow_result = await db.execute(
                select(DiscoveryFlow).order_by(DiscoveryFlow.created_at.desc()).limit(1)
            )
            flow = flow_result.scalar_one_or_none()
            
            if flow:
                print(f"\nFound flow: {flow.flow_id}")
                print(f"Current flow context - Client: {flow.client_account_id}, Engagement: {flow.engagement_id}")
                
                flow.client_account_id = demo_client_id
                flow.engagement_id = demo_engagement_id
                await db.commit()
                print("✅ Updated flow to demo context")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(fix_field_mappings_context())