#!/usr/bin/env python3
"""
Migrate Local Feedback Data to Railway PostgreSQL
Exports local feedback data and imports it to Railway database
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def export_local_feedback():
    """Export feedback from local database."""
    logger.info("📤 Exporting local feedback data...")

    try:
        # Connect to local database
        from app.core.database import AsyncSessionLocal
        from app.models.feedback import Feedback
        from sqlalchemy import select

        feedback_data = []

        async with AsyncSessionLocal() as session:
            # Get all feedback
            result = await session.execute(select(Feedback))
            feedback_items = result.scalars().all()

            for item in feedback_items:
                feedback_dict = {
                    "feedback_type": item.feedback_type,
                    "page": item.page,
                    "rating": item.rating,
                    "comment": item.comment,
                    "category": item.category,
                    "breadcrumb": item.breadcrumb,
                    "user_timestamp": item.user_timestamp,
                    "status": item.status or "new",
                    "created_at": (
                        item.created_at.isoformat() if item.created_at else None
                    ),
                    "filename": item.filename,
                    "original_analysis": item.original_analysis,
                    "user_corrections": item.user_corrections,
                    "asset_type_override": item.asset_type_override,
                }
                feedback_data.append(feedback_dict)

        # Save to JSON file
        export_file = "local_feedback_export.json"
        with open(export_file, "w") as f:
            json.dump(feedback_data, f, indent=2, default=str)

        logger.info(f"✅ Exported {len(feedback_data)} feedback items to {export_file}")
        return export_file, feedback_data

    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        return None, []


async def import_to_railway(feedback_data):
    """Import feedback data to Railway database."""
    logger.info("📥 Importing feedback data to Railway...")

    try:
        # Set Railway DATABASE_URL
        railway_db_url = input("Enter Railway DATABASE_URL: ")
        if not railway_db_url:
            logger.error("❌ No DATABASE_URL provided")
            return False

        # Temporarily set the DATABASE_URL
        original_db_url = os.getenv("DATABASE_URL")
        os.environ["DATABASE_URL"] = railway_db_url

        # Import with Railway connection
        import uuid

        from app.core.database import AsyncSessionLocal
        from app.models.feedback import Feedback

        imported_count = 0

        async with AsyncSessionLocal() as session:
            for item_data in feedback_data:
                # Skip items that don't have required fields
                if not item_data.get("feedback_type"):
                    continue

                feedback_entry = Feedback(
                    id=uuid.uuid4(),
                    feedback_type=item_data["feedback_type"],
                    page=item_data.get("page"),
                    rating=item_data.get("rating"),
                    comment=item_data.get("comment"),
                    category=item_data.get("category"),
                    breadcrumb=item_data.get("breadcrumb"),
                    user_timestamp=item_data.get("user_timestamp"),
                    status=item_data.get("status", "new"),
                    filename=item_data.get("filename"),
                    original_analysis=item_data.get("original_analysis"),
                    user_corrections=item_data.get("user_corrections"),
                    asset_type_override=item_data.get("asset_type_override"),
                )

                session.add(feedback_entry)
                imported_count += 1

            await session.commit()

        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url

        logger.info(f"✅ Imported {imported_count} feedback items to Railway")
        return True

    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False


async def main():
    """Main migration process."""
    logger.info("🚀 Starting Feedback Migration to Railway...")
    logger.info("=" * 60)

    # Step 1: Export local data
    export_file, feedback_data = await export_local_feedback()
    if not feedback_data:
        logger.error("💥 No data to migrate!")
        return False

    # Step 2: Ask user if they want to import to Railway
    print(f"\n📋 Found {len(feedback_data)} feedback items to migrate.")
    print("📄 Export saved to:", export_file)

    migrate_choice = input("\nDo you want to import this data to Railway? (y/n): ")
    if migrate_choice.lower() != "y":
        logger.info("✅ Export completed. You can manually import later.")
        return True

    # Step 3: Import to Railway
    success = await import_to_railway(feedback_data)

    if success:
        logger.info("=" * 60)
        logger.info("🎉 Migration completed successfully!")
        logger.info("✅ Local feedback data migrated to Railway")
        logger.info("🗄️ Railway database ready for production use")
    else:
        logger.error("💥 Migration failed!")

    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
