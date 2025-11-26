#!/usr/bin/env python3
"""
Diagnostic script to verify CanonicalApplication queries work correctly.
This simulates what the assessment data repository does.

Usage: Run from project root or backend directory
    python test_canonical_app_query.py
    OR
    python backend/scripts/test_canonical_app_query.py
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add backend to path (works from project root or backend dir)
backend_path = (
    Path(__file__).parent.parent
    if "scripts" in str(Path(__file__).parent)
    else Path(__file__).parent / "backend"
)
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, and_  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models.canonical_applications import CanonicalApplication  # noqa: E402

# Database connection (same as in backend)
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"


async def test_canonical_app_query():
    """Test querying CanonicalApplication table."""
    print("🔍 Testing CanonicalApplication query...")

    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Test query with tenant scoping (same as readiness_queries.py)
            client_account_id = UUID("11111111-1111-1111-1111-111111111111")
            engagement_id = UUID("22222222-2222-2222-2222-222222222222")

            query = select(CanonicalApplication).where(
                and_(
                    CanonicalApplication.client_account_id == client_account_id,
                    CanonicalApplication.engagement_id == engagement_id,
                )
            )

            result = await session.execute(query)
            applications = list(result.scalars().all())

            print(f"✅ SUCCESS: Found {len(applications)} canonical applications")

            # Print first few apps
            for i, app in enumerate(applications[:3]):
                print(f"  - App {i+1}: {app.canonical_name} (ID: {app.id})")

            if len(applications) > 3:
                print(f"  ... and {len(applications) - 3} more")

            return True

        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(test_canonical_app_query())
    sys.exit(0 if success else 1)
