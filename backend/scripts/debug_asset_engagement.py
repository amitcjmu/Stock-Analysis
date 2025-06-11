import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

try:
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    print("✅ Async database connection configured.")
except Exception as e:
    print(f"❌ Failed to configure database connection: {e}")
    engine = None
    SessionLocal = None

async def inspect_assets():
    if not SessionLocal:
        print("❌ Cannot inspect assets, database session is not available.")
        return

    print("\n--- Inspecting Assets in Database ---")
    try:
        async with SessionLocal() as session:
            result = await session.execute(text("SELECT id, name, client_account_id, engagement_id FROM assets"))
            assets = result.fetchall()

            if not assets:
                print("No assets found in the database.")
                return

            print(f"Found {len(assets)} assets. Details:")
            for asset in assets:
                print(
                    f"  - ID: {asset.id}\n"
                    f"    Name: {asset.name}\n"
                    f"    Client Account ID: {asset.client_account_id}\n"
                    f"    Engagement ID: {asset.engagement_id}\n"
                )

    except Exception as e:
        print(f"❌ An error occurred while inspecting assets: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(inspect_assets()) 