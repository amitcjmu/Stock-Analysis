"""
Structured Demo Data Seeding Module

This module provides a modularized approach to seeding demo data
while maintaining backward compatibility with the original script.

Usage:
    from seed_structured_demo_data import StructuredDemoSeeder
    seeder = StructuredDemoSeeder()
    await seeder.seed_all_data()
"""

from .base import BaseDemoSeeder
from .data_population import DataPopulator
from .flow_operations import FlowOperations
from .tenant_management import TenantManager
from .verification import DataVerifier

# Main seeder class that combines all operations


class StructuredDemoSeeder(TenantManager, FlowOperations, DataPopulator, DataVerifier):
    """
    Structured demo data seeder using MFO pattern.

    This class inherits from all specialized modules to provide
    a complete seeding solution while maintaining clean separation
    of concerns.
    """

    async def seed_all_data(self) -> bool:
        """Main method to seed all demo data using structured approach"""
        from app.core.database import AsyncSessionLocal

        print("=" * 60)
        print("🌱 STRUCTURED DEMO DATA SEEDING")
        print("=" * 60)
        print(
            "This script creates a structured solution that works across all environments"
        )
        print()

        try:
            async with AsyncSessionLocal() as db:
                # Step 1: Ensure demo tenant exists
                await self.ensure_demo_tenant_exists(db)

                # Step 2: Create discovery flows using MFO pattern
                flow_ids = await self.create_discovery_flows_with_mfo(db)

                # Step 3: Populate assets table with proper discovered_at timestamps
                await self.populate_assets_table(db, flow_ids)

                # Step 4: Populate canonical applications for Collection flow
                await self.populate_canonical_applications(db)

                # Step 5: Verify everything was created correctly
                await self.verify_seed_data(db)

                print()
                print("✅ STRUCTURED SEEDING COMPLETED SUCCESSFULLY!")
                print()
                print("🎯 Benefits of this structured approach:")
                print(
                    "  - Uses Master Flow Orchestrator pattern (no direct DiscoveryFlow creation)"
                )
                print("  - Proper multi-tenant scoping prevents data leakage")
                print("  - Discovered_at column properly populated")
                print("  - Both assets and canonical_applications tables populated")
                print("  - Idempotent operations (safe to run multiple times)")
                print("  - Works consistently across all environments")
                print()
                print("🔐 Demo Login Credentials:")
                print("  - Email: demo@demo-corp.com")
                print(f"  - Client ID: {self.demo_client_id}")
                print(f"  - Engagement ID: {self.demo_engagement_id}")
                print()

                return True

        except Exception as e:
            print(f"❌ Seeding failed: {e}")
            return False


# Maintain backward compatibility
__all__ = [
    "StructuredDemoSeeder",
    "BaseDemoSeeder",
    "TenantManager",
    "FlowOperations",
    "DataPopulator",
    "DataVerifier",
]
