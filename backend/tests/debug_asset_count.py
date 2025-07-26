import asyncio
import sys

# Add the backend directory to the Python path
sys.path.append("backend")


async def check_asset_count():
    try:
        from sqlalchemy import func, select

        from app.core.database import AsyncSessionLocal
        from app.models.asset import Asset

        print("🔍 Checking asset count in database...")

        async with AsyncSessionLocal() as session:
            # Get total count
            result = await session.execute(select(func.count(Asset.id)))
            total_count = result.scalar()
            print(f"📊 Total assets in database: {total_count}")

            # Get first 5 assets for verification
            result = await session.execute(select(Asset).limit(5))
            assets = result.scalars().all()

            print("📋 Sample assets:")
            for asset in assets:
                print(f"  - {asset.hostname} ({asset.asset_type})")

            # Check asset types
            result = await session.execute(
                select(Asset.asset_type, func.count(Asset.id)).group_by(
                    Asset.asset_type
                )
            )
            type_counts = result.all()

            print("📈 Asset type breakdown:")
            for asset_type, count in type_counts:
                print(f"  - {asset_type}: {count}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_asset_count())
