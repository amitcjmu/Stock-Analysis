"""
Flow operations for demo data seeding.
Handles creation of discovery flows using Master Flow Orchestrator pattern.
"""

import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.master_flow_orchestrator.core import MasterFlowOrchestrator
from .base import BaseDemoSeeder


class FlowOperations(BaseDemoSeeder):
    """Manages demo flow creation using MFO pattern"""

    async def create_discovery_flows_with_mfo(self, db: AsyncSession) -> List[str]:
        """Create discovery flows using Master Flow Orchestrator pattern"""
        print("🔄 Creating discovery flows using MFO pattern...")

        # Create request context for MFO
        context = RequestContext(
            client_account_id=uuid.UUID(self.demo_client_id),
            engagement_id=uuid.UUID(self.demo_engagement_id),
            user_id=self.demo_user_id,
        )

        # Initialize MFO
        mfo = MasterFlowOrchestrator(db, context)

        flow_configurations = [
            {
                "name": "Complete Discovery Flow - Asset Inventory Ready",
                "config": {
                    "learning_scope": "engagement",
                    "memory_isolation_level": "strict",
                    "enable_asset_inventory": True,
                    "auto_transition": True,
                },
                "initial_state": {
                    "current_phase": "completed",
                    "progress_percentage": 100.0,
                    "phases_completed": [
                        "data_import",
                        "field_mapping",
                        "data_cleansing",
                        "asset_inventory",
                        "dependency_analysis",
                    ],
                },
            },
            {
                "name": "Active Discovery Flow - Asset Inventory Phase",
                "config": {
                    "learning_scope": "engagement",
                    "memory_isolation_level": "moderate",
                    "enable_asset_inventory": True,
                },
                "initial_state": {
                    "current_phase": "asset_inventory",
                    "progress_percentage": 60.0,
                    "phases_completed": [
                        "data_import",
                        "field_mapping",
                        "data_cleansing",
                    ],
                },
            },
            {
                "name": "New Discovery Flow - Field Mapping Phase",
                "config": {
                    "learning_scope": "client",
                    "memory_isolation_level": "open",
                },
                "initial_state": {
                    "current_phase": "field_mapping",
                    "progress_percentage": 30.0,
                    "phases_completed": ["data_import"],
                },
            },
        ]

        created_flow_ids = []

        for flow_config in flow_configurations:
            try:
                print(f"  Creating flow: {flow_config['name']}")

                # Use MFO to create flow with atomic transactions
                flow_id, result = await mfo.create_flow(
                    flow_type="discovery",
                    flow_name=flow_config["name"],
                    configuration=flow_config["config"],
                    initial_state=flow_config["initial_state"],
                    atomic=True,
                )

                created_flow_ids.append(flow_id)
                print(f"    ✅ Created flow: {flow_id}")

            except Exception as e:
                print(f"    ❌ Failed to create flow {flow_config['name']}: {e}")
                # Continue with next flow
                continue

        print(f"✅ Created {len(created_flow_ids)} discovery flows using MFO")
        return created_flow_ids
