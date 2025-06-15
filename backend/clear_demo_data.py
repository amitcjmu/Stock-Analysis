#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/app')

from app.core.database import AsyncSessionLocal
from app.models.client_account import User, ClientAccount, Engagement
from app.models.data_import_session import DataImportSession
from app.models.rbac import UserProfile
from sqlalchemy import delete

async def clear_demo_data():
    async with AsyncSessionLocal() as db:
        try:
            # Import additional models that might have foreign keys
            from app.models.rbac import UserRole, ClientAccess, EngagementAccess
            
            # Delete in proper dependency order
            await db.execute(delete(DataImportSession))
            await db.execute(delete(EngagementAccess))
            await db.execute(delete(ClientAccess))
            await db.execute(delete(UserRole))
            await db.execute(delete(UserProfile))
            await db.execute(delete(Engagement))
            await db.execute(delete(User))
            await db.execute(delete(ClientAccount))
            await db.commit()
            print('✓ Cleared existing demo data')
        except Exception as e:
            print(f'Error clearing data: {e}')
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(clear_demo_data()) 