#!/usr/bin/env python3
"""
Test user update functionality
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


async def test_user_update():
    """Test user update functionality"""
    try:
        import uuid

        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.models import User

        async with AsyncSessionLocal() as db:
            # Get a user to test with
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()

            if not user:
                print("❌ No users found in database")
                return

            print(f"=== TESTING USER UPDATE ===")
            print(f"User: {user.email}")
            print(f"Current default_client_id: {user.default_client_id}")
            print(f"Current default_engagement_id: {user.default_engagement_id}")

            # Get valid client and engagement IDs
            from app.models import ClientAccount, Engagement

            # Get a valid client
            client_result = await db.execute(select(ClientAccount).limit(1))
            client = client_result.scalar_one_or_none()

            # Get a valid engagement
            engagement_result = await db.execute(select(Engagement).limit(1))
            engagement = engagement_result.scalar_one_or_none()

            if not client or not engagement:
                print("❌ No clients or engagements found in database")
                return

            print(f"\nUsing client: {client.name} ({client.id})")
            print(f"Using engagement: {engagement.name} ({engagement.id})")

            # Try to update the user
            user.default_client_id = client.id
            user.default_engagement_id = engagement.id

            await db.commit()
            await db.refresh(user)

            print(f"\n✅ Update successful!")
            print(f"New default_client_id: {user.default_client_id}")
            print(f"New default_engagement_id: {user.default_engagement_id}")

            # Reset to original values
            user.default_client_id = None
            user.default_engagement_id = None
            await db.commit()

            print(f"\n✅ Reset successful!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_user_update())
