#!/usr/bin/env python3
"""
Check client status and updated_at dates
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


async def check_client_status():
    """Check client status"""
    try:
        from datetime import datetime, timedelta

        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.models import ClientAccount

        async with AsyncSessionLocal() as db:
            # Get all clients
            result = await db.execute(select(ClientAccount))
            clients = result.scalars().all()

            print("=== CLIENT STATUS ===")
            print(f"Total clients: {len(clients)}")

            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            print(f"\n90 days ago: {ninety_days_ago}")

            for client in clients:
                print(f"\nClient: {client.name}")
                print(f"  ID: {client.id}")
                print(f"  Is Active: {client.is_active}")
                print(f"  Created: {client.created_at}")
                print(f"  Updated: {client.updated_at}")
                if client.updated_at:
                    print(
                        f"  Updated within 90 days: {client.updated_at > ninety_days_ago}"
                    )
                else:
                    print("  Updated within 90 days: False (never updated)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_client_status())
