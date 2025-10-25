#!/usr/bin/env python3
"""
Seed script for collection_question_rules table.
Creates baseline questions for Collection Flow adaptive questionnaire.

Usage:
    python seed_collection_question_rules.py [--engagement-id ENGAGEMENT_ID]

Asset Types:
    - Application
    - Server
    - Database
    - Network
    - Storage
"""

import argparse
import asyncio
import os
import sys
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.collection_flow.collection_question_rules import (  # noqa: E402
    CollectionQuestionRules,
)
from scripts.seed_data import QUESTION_TEMPLATES  # noqa: E402


# Templates are imported from seed_data.collection_question_templates


async def seed_question_rules(engagement_id: UUID, client_account_id: UUID) -> bool:
    """
    Seed collection_question_rules table with baseline questions.

    Args:
        engagement_id: Engagement UUID to associate questions with
        client_account_id: Client account UUID

    Returns:
        True if successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                # Check if questions already exist for this engagement
                result = await session.execute(
                    select(CollectionQuestionRules).where(
                        CollectionQuestionRules.engagement_id == engagement_id,
                        CollectionQuestionRules.client_account_id == client_account_id,
                    )
                )
                existing_questions = result.scalars().all()

                if existing_questions:
                    print(
                        f"⚠️  Found {len(existing_questions)} existing questions "
                        f"for engagement {engagement_id}"
                    )
                    response = input("Do you want to delete and recreate? (yes/no): ")
                    if response.lower() != "yes":
                        print("❌ Seeding cancelled")
                        return False

                    # Delete existing questions
                    for question in existing_questions:
                        await session.delete(question)
                    print(f"🗑️  Deleted {len(existing_questions)} existing questions")

                # Create new questions
                total_created = 0
                for asset_type, questions in QUESTION_TEMPLATES.items():
                    print(f"\n📝 Creating questions for {asset_type}...")

                    for idx, question_data in enumerate(questions, start=1):
                        # Generate question_id from question_text
                        question_text = question_data["question_text"]
                        # Create a simple slug-style ID
                        question_id = (
                            question_text.lower()
                            .replace("?", "")
                            .replace("'", "")
                            .replace("/", "_")
                            .replace(" ", "_")
                            .strip("_")
                        )
                        # Add asset type prefix and index for uniqueness
                        question_id = f"{asset_type.lower()}_{idx:02d}_{question_id}"

                        question = CollectionQuestionRules(
                            engagement_id=engagement_id,
                            client_account_id=client_account_id,
                            asset_type=asset_type,
                            question_id=question_id,
                            **question_data,
                        )
                        session.add(question)
                        total_created += 1

                    print(f"   ✅ Created {len(questions)} questions for {asset_type}")

                await session.commit()
                print(f"\n✅ Successfully seeded {total_created} question rules!")

                # Print summary
                print("\n" + "=" * 60)
                print("📊 SEEDING SUMMARY")
                print("=" * 60)
                for asset_type, questions in QUESTION_TEMPLATES.items():
                    print(f"  {asset_type}: {len(questions)} questions")
                print(f"  TOTAL: {total_created} questions")
                print("=" * 60)

                return True

    except Exception as e:
        print(f"❌ Error seeding question rules: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main entry point for seeding script."""
    parser = argparse.ArgumentParser(
        description="Seed collection_question_rules table with baseline questions"
    )
    parser.add_argument(
        "--engagement-id",
        type=str,
        default="22222222-2222-2222-2222-222222222222",
        help="Engagement UUID (default: 22222222-2222-2222-2222-222222222222 - Demo Cloud Migration Project)",
    )
    parser.add_argument(
        "--client-account-id",
        type=str,
        default="11111111-1111-1111-1111-111111111111",
        help="Client account UUID (default: 11111111-1111-1111-1111-111111111111 - Demo Corporation)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🌱 COLLECTION QUESTION RULES SEEDING SCRIPT")
    print("=" * 60)

    # Detect environment
    env = (
        "PRODUCTION"
        if (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("DATABASE_URL"))
        else "LOCAL"
    )
    print(f"\n📍 Environment: {env}")
    print(f"🎯 Engagement ID: {args.engagement_id}")
    print(f"🏢 Client Account ID: {args.client_account_id}")

    # Production safety check
    if env == "PRODUCTION":
        print("\n⚠️  WARNING: Running in PRODUCTION environment!")
        print("⏳ Starting in 5 seconds... Press Ctrl+C to cancel")
        try:
            for i in range(5, 0, -1):
                print(f"   {i}...")
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n❌ Seeding cancelled by user")
            sys.exit(1)

    # Convert engagement_id and client_account_id to UUIDs
    try:
        engagement_uuid = UUID(args.engagement_id)
        client_account_uuid = UUID(args.client_account_id)
    except ValueError as e:
        print(f"❌ Invalid UUID format: {e}")
        sys.exit(1)

    # Run seeding
    success = await seed_question_rules(
        engagement_id=engagement_uuid,
        client_account_id=client_account_uuid,
    )

    if success:
        print("\n✅ Seeding completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Seeding failed!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
