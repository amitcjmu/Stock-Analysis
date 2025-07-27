#!/usr/bin/env python3
"""
Check engagements in the database
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Set database URL - use Docker network hostname
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"
)


async def check_engagements():
    """Check engagements in the database"""
    try:
        from sqlalchemy import select, text

        from app.core.database import AsyncSessionLocal
        from app.models import Engagement

        async with AsyncSessionLocal() as db:
            # Check Engagement table structure
            result = await db.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'engagements'"
                )
            )
            columns = result.fetchall()

            print("=== ENGAGEMENT TABLE COLUMNS ===")
            for col in columns[:10]:  # Show first 10 columns
                print(f"  {col[0]}: {col[1]}")

            # Count engagements
            result = await db.execute(text("SELECT COUNT(*) FROM engagements"))
            count = result.scalar()
            print(f"\n=== TOTAL ENGAGEMENTS: {count} ===")

            # Get all engagements
            result = await db.execute(select(Engagement))
            engagements = result.scalars().all()

            print("\n=== ENGAGEMENT DETAILS ===")
            for eng in engagements:
                print(f"\nEngagement: {eng.name}")
                print(f"  ID: {eng.id}")
                print(f"  Client ID: {eng.client_account_id}")
                print(f"  Status: {eng.status}")
                print(f"  Type: {eng.engagement_type}")
                print(f"  Is Active: {eng.is_active}")
                print(f"  Created: {eng.created_at}")

            # Check for demo engagement specifically
            print("\n=== CHECKING FOR DEMO ENGAGEMENT ===")
            result = await db.execute(
                select(Engagement).where(
                    Engagement.id == "22222222-2222-2222-2222-222222222222"
                )
            )
            demo_eng = result.scalar_one_or_none()
            if demo_eng:
                print(f"✅ Demo engagement found: {demo_eng.name}")
            else:
                print("❌ Demo engagement NOT found")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_engagements())
