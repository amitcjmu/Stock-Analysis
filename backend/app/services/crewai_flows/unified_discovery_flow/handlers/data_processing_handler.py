"""
Data processing phase handler.
Handles data cleansing and asset creation phases of the unified discovery flow.
"""

import logging

from .communication_utils import CommunicationUtils
from .state_utils import StateUtils

logger = logging.getLogger(__name__)


class DataProcessingHandler:
    """Handles data processing phase operations."""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance."""
        self.flow = flow_instance
        self.logger = logger
        self.communication = CommunicationUtils(flow_instance)
        self.state_utils = StateUtils(flow_instance)

    async def execute_data_cleansing(self, mapping_application_result):
        """Execute data cleansing phase"""
        self.logger.info(
            f"🧹 [ECHO] Data cleansing phase triggered for flow {self.flow._flow_id}"
        )

        try:
            # Update flow status
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import (
                    PostgresFlowStateStore,
                )

                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(
                        self.flow._flow_id, "processing_data_cleansing"
                    )

            # Execute data cleansing using the executor pattern
            cleansing_result = await self.flow.data_cleansing_phase.execute(
                mapping_application_result  # Pass mapping result from previous phase
            )

            # Send agent insight
            await self.communication.send_phase_insight(
                phase="data_cleansing",
                title="Data Cleansing Completed",
                description="Data cleansing phase has been completed successfully",
                progress=70,
                data=cleansing_result,
            )

            # Update state with cleansed data
            self.flow.state.cleansed_data = cleansing_result.get("cleansed_data", {})

            return cleansing_result

        except Exception as e:
            self.logger.error(f"❌ Data cleansing phase failed: {e}")
            await self.communication.send_phase_error("data_cleansing", str(e))
            raise

    async def create_discovery_assets(self, data_cleansing_result):
        """Create discovery assets from cleansed data"""
        self.logger.info(
            f"📦 [ECHO] Creating discovery assets for flow {self.flow._flow_id}"
        )

        try:
            # Update flow status
            if hasattr(self.flow, "flow_bridge") and self.flow.flow_bridge:
                from app.core.database import AsyncSessionLocal
                from app.services.crewai_flows.persistence.postgres_store import (
                    PostgresFlowStateStore,
                )

                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.flow.context)
                    await store.update_flow_status(
                        self.flow._flow_id, "creating_discovery_assets"
                    )

            # Execute asset creation using the executor pattern
            asset_creation_result = await self.flow.asset_inventory_phase.execute(
                data_cleansing_result  # Pass cleansing result from previous phase
            )

            # Send agent insight
            await self.communication.send_phase_insight(
                phase="asset_creation",
                title="Discovery Assets Created",
                description="Discovery assets have been created from cleansed data",
                progress=80,
                data=asset_creation_result,
            )

            # Update state with created assets
            self.flow.state.discovery_assets = asset_creation_result.get(
                "discovery_assets", []
            )

            return asset_creation_result

        except Exception as e:
            self.logger.error(f"❌ Asset creation phase failed: {e}")
            await self.communication.send_phase_error("asset_creation", str(e))
            raise
