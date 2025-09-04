#!/usr/bin/env python3
"""
Script to mark a collection flow as completed for testing the transition to assessment.
This bypasses the normal flow progression for testing purposes only.
"""

import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import after path modification to avoid E402
from sqlalchemy import update  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models.collection_flow import CollectionFlow  # noqa: E402
from app.core.config import settings  # noqa: E402


async def mark_flow_completed(flow_id: str):
    """Mark a collection flow as completed with all phases done."""

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True,
    )

    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        try:
            # Update the flow
            stmt = (
                update(CollectionFlow)
                .where(CollectionFlow.id == UUID(flow_id))
                .values(
                    status="completed",
                    current_phase="finalization",
                    progress_percentage=100,
                    assessment_ready=True,
                    data_quality_score=85,
                    confidence_score=90,
                    flow_metadata={
                        "phases_completed": [
                            "platform_detection",
                            "automated_collection",
                            "gap_analysis",
                            "questionnaire_generation",
                            "manual_collection",
                            "data_validation",
                            "finalization",
                        ],
                        "applications_processed": 5,
                        "gaps_identified": 3,
                        "gaps_resolved": 3,
                        "ready_for_assessment": True,
                    },
                )
            )

            await session.execute(stmt)
            await session.commit()

            print(f"✅ Successfully marked flow {flow_id} as completed")
            print("   - Status: completed")
            print("   - Progress: 100%")
            print("   - Assessment Ready: True")
            print("   - Data Quality: 85%")
            print("   - Confidence: 90%")

        except Exception as e:
            print(f"❌ Error updating flow: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python complete_collection_flow.py <flow_id>")
        print(
            "Example: python complete_collection_flow.py 3245200f-3150-4076-92d4-98ff8f72d318"
        )
        sys.exit(1)

    flow_id = sys.argv[1]
    asyncio.run(mark_flow_completed(flow_id))
