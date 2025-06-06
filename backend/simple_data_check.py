#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('/app')
sys.path.append('/app/backend')

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def simple_check():
    async with AsyncSessionLocal() as session:
        # Check raw records count
        result = await session.execute(text('SELECT COUNT(*) FROM raw_import_records'))
        raw_count = result.scalar()
        print(f'📥 Raw records: {raw_count}')
        
        # Check cmdb assets count
        result = await session.execute(text('SELECT COUNT(*) FROM cmdb_assets'))
        cmdb_count = result.scalar()
        print(f'💾 CMDB assets: {cmdb_count}')
        
        # Check asset types
        result = await session.execute(text('SELECT asset_type, COUNT(*) FROM cmdb_assets GROUP BY asset_type'))
        print('📊 Asset types:')
        for row in result:
            print(f'  {row[0]}: {row[1]}')

asyncio.run(simple_check()) 