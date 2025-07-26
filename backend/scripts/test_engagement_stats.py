#!/usr/bin/env python3
"""
Test engagement stats directly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Set database URL - use Docker network hostname
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"


async def test_engagement_stats():
    """Test engagement stats query directly"""
    try:
        from sqlalchemy import func, select

        from app.core.database import AsyncSessionLocal
        from app.models import Engagement

        async with AsyncSessionLocal() as db:
            # Test the exact query from the handler
            print("=== Testing Dashboard Stats Query ===")

            # Total engagements (only active ones)
            total_query = select(func.count()).where(Engagement.is_active is True)
            result = await db.execute(total_query)
            total_engagements = result.scalar_one()
            print(f"Total active engagements: {total_engagements}")

            # Let's also try without the where clause
            total_all_query = select(func.count()).select_from(Engagement)
            result = await db.execute(total_all_query)
            total_all = result.scalar_one()
            print(f"Total all engagements: {total_all}")

            # Check the actual SQL being generated
            print(f"\nSQL for active query: {total_query}")
            print(f"SQL for all query: {total_all_query}")

            # Try a simpler query
            print("\n=== Simple Query Test ===")
            result = await db.execute(select(func.count(Engagement.id)))
            simple_count = result.scalar_one()
            print(f"Simple count: {simple_count}")

            # Get all engagements with their is_active status
            print("\n=== All Engagements is_active Status ===")
            result = await db.execute(
                select(Engagement.id, Engagement.name, Engagement.is_active)
            )
            for row in result:
                print(f"  {row[1]}: is_active={row[2]}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_engagement_stats())
