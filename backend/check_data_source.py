#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('/app')
sys.path.append('/app/backend')

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_data_source():
    async with AsyncSessionLocal() as session:
        print('📊 Checking data sources...')
        
        # Check raw import records by session
        result = await session.execute(text("""
            SELECT data_import_id, COUNT(*), MIN(created_at), MAX(created_at), 
                   raw_data
            FROM raw_import_records 
            GROUP BY data_import_id, raw_data
            ORDER BY MIN(created_at) DESC 
            LIMIT 5
        """))
        
        print("📥 Raw Import Records:")
        for row in result:
            print(f'  Session {row[0]}: Record created {row[2]}')
            print(f'    Keys: {list(row[4].keys())}')
            print(f'    Sample: {row[4]}')
            print()
        
        # Check CMDB assets by source
        result = await session.execute(text("""
            SELECT discovery_source, COUNT(*), MIN(created_at), MAX(created_at) 
            FROM cmdb_assets 
            GROUP BY discovery_source 
            ORDER BY MIN(created_at) DESC
        """))
        
        print("💾 CMDB Assets by Source:")
        for row in result:
            print(f'  {row[0]}: {row[1]} assets from {row[2]} to {row[3]}')

asyncio.run(check_data_source()) 