#!/usr/bin/env python
"""Simple test to verify schema."""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        # Count tables
        result = await session.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
        count = result.scalar()
        print(f"Total tables: {count}")
        
        # Check asset table columns
        result = await session.execute(text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'assets'"))
        asset_cols = result.scalar()
        print(f"Asset table columns: {asset_cols}")
        
        # Check critical fields
        result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'assets' AND column_name IN ('flow_id', 'name', 'six_r_strategy')"))
        fields = result.fetchall()
        print(f"Critical asset fields found: {[f[0] for f in fields]}")

if __name__ == "__main__":
    asyncio.run(main())