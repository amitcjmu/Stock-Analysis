import asyncio
import os
import sys
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append("/app")


# No longer need settings, will get from environment
# from app.core.config import settings

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"
)


async def fix_null_asset_ids():
    """
    Connects to the database and assigns a new UUID to every asset
    that currently has a NULL id.
    """
    print("🚀 Starting script to fix NULL asset IDs...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        try:
            print("🔍 Finding assets with NULL IDs using raw SQL...")

            # Use raw SQL for maximum reliability
            raw_query = text("SELECT * FROM assets WHERE id IS NULL")
            result = await session.execute(raw_query)
            assets_to_fix = result.fetchall()

            if not assets_to_fix:
                print("✅ No assets with NULL IDs found. Database is clean.")
                return

            print(
                f"Found {len(assets_to_fix)} assets with NULL IDs. Proceeding to fix them..."
            )

            fixed_count = 0
            # Since we can't reliably map raw results to SQLAlchemy objects easily,
            # we'll use a raw UPDATE statement. We need a way to uniquely identify each row.
            # Hostname or created_at are candidates. Let's use hostname for this attempt.

            # First, fetch a unique identifier for each row that needs fixing
            rows_to_update_query = text(
                "SELECT hostname, created_at FROM assets WHERE id IS NULL"
            )
            rows_result = await session.execute(rows_to_update_query)
            rows_to_update = rows_result.fetchall()

            for row in rows_to_update:
                new_id = uuid.uuid4()
                hostname, created_at = row

                # Using a raw SQL UPDATE statement
                update_query = text(
                    "UPDATE assets SET id = :new_id "
                    "WHERE hostname = :hostname AND created_at = :created_at AND id IS NULL"
                )

                await session.execute(
                    update_query,
                    {"new_id": new_id, "hostname": hostname, "created_at": created_at},
                )
                print(f"✅ Assigned new UUID {new_id} to asset with hostname {hostname}")
                fixed_count += 1

            await session.commit()
            print(f"🎉 Successfully fixed {fixed_count} assets.")

        except Exception as e:
            print(f"❌ An error occurred: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    # This script must be run within the backend container's environment
    # Example: docker exec -it migration_backend python /app/scripts/fix_asset_ids.py
    asyncio.run(fix_null_asset_ids())
