#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('/app')
sys.path.append('/app/backend')

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_raw_data():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text('SELECT raw_data FROM raw_import_records LIMIT 3'))
        for i, row in enumerate(result):
            print(f'Record {i+1}:')
            print(f'Keys: {list(row[0].keys())}')
            for key, value in row[0].items():
                print(f'  {key}: {value}')
            print()

asyncio.run(check_raw_data()) 