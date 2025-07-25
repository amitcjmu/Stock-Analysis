import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path, essential for running in the container
sys.path.append("/app")

# Get the database URL directly from the environment variable the container uses
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ FATAL: DATABASE_URL environment variable is not set inside the container.")
    sys.exit(1)

# Ensure the URL is in the asyncpg format required by asyncio
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


async def get_asset_id_by_hostname(hostname: str):
    """
    Connects to the database using the application's environment configuration
    and retrieves the ID of an asset by its hostname.
    """
    print(f"🚀 Querying for asset with hostname: '{hostname}'")
    print(f"🔌 Using database connection URL from environment: {DATABASE_URL}")

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession)

    async with AsyncSessionLocal() as session:
        try:
            # Using a raw, parameterized SQL query for maximum clarity and reliability
            query = text("SELECT id FROM assets WHERE hostname = :hostname")
            result = await session.execute(query, {"hostname": hostname})

            # Use .scalar_one_or_none() to get a single value or None if not found
            asset_id = result.scalar_one_or_none()

            if asset_id is not None:
                print("--- RESULT ---")
                print(f"✅ Found Asset ID: {asset_id}")
                print(f"   (Type of ID: {type(asset_id)})")
                print("--------------")
            else:
                print("--- RESULT ---")
                print(f"⚠️ No asset found with hostname '{hostname}'.")
                print("--------------")

        except Exception as e:
            print(f"❌ An error occurred during the database query: {e}")
        finally:
            await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python /app/app/scripts/debug_get_asset_id.py <hostname>")
        sys.exit(1)

    hostname_to_find = sys.argv[1]
    asyncio.run(get_asset_id_by_hostname(hostname_to_find))
