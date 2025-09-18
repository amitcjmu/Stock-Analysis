"""
Verification operations for demo data seeding.
Handles verification of created data.
"""

from typing import Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Asset,
    CanonicalApplication,
    DiscoveryFlow,
    CrewAIFlowStateExtensions,
)
from .base import BaseDemoSeeder


class DataVerifier(BaseDemoSeeder):
    """Manages verification of seeded demo data"""

    async def verify_seed_data(self, db: AsyncSession) -> Dict[str, int]:
        """Verify that all seed data was created correctly"""
        print("🔍 Verifying seed data...")

        verification_results = {}

        # Count master flows
        result = await db.execute(
            select(func.count(CrewAIFlowStateExtensions.id)).where(
                CrewAIFlowStateExtensions.client_account_id == self.demo_client_id,
                CrewAIFlowStateExtensions.engagement_id == self.demo_engagement_id,
            )
        )
        verification_results["master_flows"] = result.scalar()

        # Count discovery flows
        result = await db.execute(
            select(func.count(DiscoveryFlow.id)).where(
                DiscoveryFlow.client_account_id == self.demo_client_id,
                DiscoveryFlow.engagement_id == self.demo_engagement_id,
            )
        )
        verification_results["discovery_flows"] = result.scalar()

        # Count assets
        result = await db.execute(
            select(func.count(Asset.id)).where(
                Asset.client_account_id == self.demo_client_id,
                Asset.engagement_id == self.demo_engagement_id,
            )
        )
        verification_results["assets"] = result.scalar()

        # Count canonical applications
        result = await db.execute(
            select(func.count(CanonicalApplication.id)).where(
                CanonicalApplication.client_account_id == self.demo_client_id,
                CanonicalApplication.engagement_id == self.demo_engagement_id,
            )
        )
        verification_results["canonical_applications"] = result.scalar()

        print("📊 Verification Results:")
        for entity, count in verification_results.items():
            print(f"  - {entity}: {count}")

        return verification_results
