"""
Test database connection and check existing data.
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select, text

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.client_account import ClientAccount, User
from seeding.constants import DEMO_CLIENT_ID


async def test_connection():
    """Test database connection and check for existing data."""
    print("Testing database connection...")

    async with AsyncSessionLocal() as db:
        try:
            # Test basic connection
            result = await db.execute(text("SELECT 1"))
            print("✓ Database connection successful")

            # Check for existing client
            existing_client = await db.get(ClientAccount, DEMO_CLIENT_ID)
            if existing_client:
                print(f"⚠️  Demo client already exists: {existing_client.name}")
            else:
                print("✓ Demo client does not exist yet")

            # Count existing users
            user_count = await db.scalar(select(User).count())
            print(f"ℹ️  Current user count: {user_count}")

            # List tables
            result = await db.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
                )
            )
            tables = [row[0] for row in result]
            print(f"\nℹ️  Available tables ({len(tables)}):")
            for table in tables[:10]:  # Show first 10
                print(f"   - {table}")
            if len(tables) > 10:
                print(f"   ... and {len(tables) - 10} more")

        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(test_connection())
