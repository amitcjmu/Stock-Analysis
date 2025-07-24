import asyncio
import os
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- Configuration ---
# The Client Account and Engagement ID that the frontend uses for the demo context.
# We need to assign these to the assets we want to see.
TARGET_CLIENT_ACCOUNT_ID = uuid.UUID("d838573d-f461-44e4-81b5-5af510ef83b7")
TARGET_ENGAGEMENT_ID = uuid.UUID("d1a93e23-719d-4dad-8bbf-b66ab9de2b94")

# The IDs of the two assets that are missing the engagement_id.
ASSET_IDS_TO_UPDATE = [
    uuid.UUID("bf765d50-0c08-475e-a2a4-23a5b513559e"),
    uuid.UUID("95be79c8-22f5-4cf7-a372-1671ad4a1c97"),
]

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# --- Main Logic ---
async def fix_asset_engagement_ids():
    print("--- 🔧 Attempting to fix asset engagement IDs ---")

    updated_count = 0

    try:
        async with SessionLocal() as session:
            async with session.begin():
                for asset_id in ASSET_IDS_TO_UPDATE:
                    print(f"Updating asset {asset_id}...")
                    stmt = text(
                        """
                        UPDATE assets
                        SET client_account_id = :client_id, engagement_id = :engagement_id
                        WHERE id = :asset_id
                    """
                    )
                    result = await session.execute(
                        stmt,
                        {
                            "client_id": TARGET_CLIENT_ACCOUNT_ID,
                            "engagement_id": TARGET_ENGAGEMENT_ID,
                            "asset_id": asset_id,
                        },
                    )
                    if result.rowcount > 0:
                        print(f"  ✅ Successfully updated asset {asset_id}")
                        updated_count += 1
                    else:
                        print(f"  ⚠️ Asset {asset_id} not found or not updated.")

            await session.commit()

        print(f"\\n🎉 Finished. Updated {updated_count} assets.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_asset_engagement_ids())
