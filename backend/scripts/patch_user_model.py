#!/usr/bin/env python3
"""
Add is_admin column to users table
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


async def add_is_admin_column():
    """Add is_admin column to users table"""
    try:
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Check if column already exists
            result = await db.execute(
                text(
                    """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'is_admin'
            """
                )
            )
            exists = result.scalar()

            if not exists:
                print("Adding is_admin column to users table...")
                await db.execute(
                    text(
                        """
                    ALTER TABLE users
                    ADD COLUMN is_admin BOOLEAN DEFAULT false
                """
                    )
                )
                await db.commit()
                print("✅ Added is_admin column")
            else:
                print("✅ is_admin column already exists")

            # Update chocka@gmail.com to have is_admin = true
            await db.execute(
                text(
                    """
                UPDATE users
                SET is_admin = true
                WHERE email = 'chocka@gmail.com'
            """
                )
            )
            await db.commit()
            print("✅ Updated chocka@gmail.com to have is_admin = true")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(add_is_admin_column())
