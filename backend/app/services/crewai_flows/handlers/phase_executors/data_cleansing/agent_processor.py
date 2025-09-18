"""
Agent Processing Module

Handles CrewAI agent interactions and processing for data cleansing.
"""

import logging
import uuid
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AgentProcessor:
    """Handles agent-based data processing for data cleansing"""

    def __init__(self, state, service_registry=None):
        self.state = state
        self.service_registry = service_registry

    async def process_with_agent(
        self, raw_import_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process data with persistent multi-tenant agent"""
        logger.info("🧠 Starting data cleansing with persistent multi-tenant agent")

        if not raw_import_records:
            raise RuntimeError("No raw import records found for data cleansing")

        # Get the agent
        cleansing_agent = await self._get_cleansing_agent()
        logger.info("🔧 Retrieved agent: data_cleansing")

        # Process with agent
        try:
            result = await self._execute_agent_processing(
                cleansing_agent, raw_import_records
            )
            return self._handle_agent_result(result, raw_import_records)
        except Exception as agent_err:
            logger.error(f"❌ Agent processing failed: {agent_err}")
            # Return error result to let caller handle fallback
            return {
                "status": "error",
                "error": str(agent_err),
                "raw_records": raw_import_records,
            }

    async def _get_cleansing_agent(self):
        """Get the data cleansing agent from the tenant scoped pool"""
        from app.core.context import RequestContext
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        # BUILD RequestContext from state
        request_context = RequestContext(
            client_account_id=self.state.client_account_id,
            engagement_id=self.state.engagement_id,
            user_id=getattr(self.state, "user_id", None),
            flow_id=self.state.flow_id,
        )

        return await TenantScopedAgentPool.get_agent(
            context=request_context,
            agent_type="data_cleansing",
            service_registry=self.service_registry,
        )

    async def _execute_agent_processing(
        self, agent, raw_import_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute the agent processing with proper interface handling"""
        if hasattr(agent, "process"):
            logger.info(
                f"🤖 Using AI agent process method for {len(raw_import_records)} records"
            )

            # The process method is always async in our wrapper
            import asyncio

            if asyncio.iscoroutinefunction(agent.process):
                return await agent.process(raw_import_records)
            else:
                # Fallback for sync process method
                return await asyncio.to_thread(agent.process, raw_import_records)
        else:
            # Agent doesn't have process method
            logger.warning(
                "⚠️ Agent doesn't have process method, cannot process with agent"
            )
            raise RuntimeError("Agent missing process method")

    def _handle_agent_result(
        self, result: Any, raw_import_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle the result returned by the agent"""
        if isinstance(result, dict):
            if result.get("status") == "success":
                # Agent succeeded - use processed data
                cleaned_data = result.get("processed_data", raw_import_records)
                logger.info(
                    f"✅ Agent processed {len(cleaned_data)} records successfully"
                )

                # Log agent insights if available
                if "agent_output" in result:
                    logger.info(f"🧠 Agent insights: {result['agent_output'][:200]}...")

                return {
                    "status": "success",
                    "cleaned_data": cleaned_data,
                    "agent_result": result,
                }
            else:
                # Agent failed
                logger.warning(
                    f"⚠️ Agent failed: {result.get('error', 'Unknown error')}"
                )
                return {
                    "status": "error",
                    "error": result.get("error", "Unknown agent error"),
                    "raw_records": raw_import_records,
                }
        else:
            # Unexpected result format
            logger.warning("⚠️ Agent returned unexpected result format")
            return {
                "status": "error",
                "error": "Agent returned unexpected result format",
                "raw_records": raw_import_records,
            }

    def prepare_assets_for_analysis(
        self, raw_import_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform raw import records into structured assets for analysis"""
        from ..data_cleansing_utils import DataCleansingUtils

        assets = []

        for i, record in enumerate(raw_import_records):
            try:
                # Create structured asset from raw import record, preserving linkage
                asset = {
                    "id": str(uuid.uuid4()),  # Generate unique ID for asset processing
                    "raw_import_record_id": record.get(
                        "raw_import_record_id"
                    ),  # Preserve linkage
                    "name": record.get("name", record.get("hostname", f"asset_{i+1}")),
                    "asset_type": record.get(
                        "asset_type", record.get("type", "unknown")
                    ),
                    "technology_stack": record.get(
                        "technology_stack",
                        record.get("technology", record.get("software", "")),
                    ),
                    "environment": record.get(
                        "environment", record.get("env", "unknown")
                    ),
                    "business_criticality": record.get(
                        "business_criticality", record.get("criticality", "medium")
                    ),
                    # Performance metrics
                    "cpu_utilization_percent": DataCleansingUtils.safe_float_convert(
                        record.get("cpu_utilization_percent", record.get("cpu_usage"))
                    ),
                    "memory_utilization_percent": DataCleansingUtils.safe_float_convert(
                        record.get(
                            "memory_utilization_percent", record.get("memory_usage")
                        )
                    ),
                    "disk_utilization_percent": DataCleansingUtils.safe_float_convert(
                        record.get("disk_utilization_percent", record.get("disk_usage"))
                    ),
                    # Network and security
                    "network_exposure": record.get(
                        "network_exposure", record.get("exposure", "internal")
                    ),
                    "data_sensitivity": record.get(
                        "data_sensitivity", record.get("sensitivity", "standard")
                    ),
                    # Architecture context
                    "architecture_style": record.get(
                        "architecture_style", record.get("architecture", "unknown")
                    ),
                    "integration_complexity": record.get(
                        "integration_complexity", "medium"
                    ),
                    "data_volume": record.get(
                        "data_volume", record.get("storage_gb", "unknown")
                    ),
                    # Original raw import record for reference and linkage
                    "raw_import_record": record,
                    "enrichment_status": "basic",
                    "source": "discovery_flow",
                }

                assets.append(asset)

            except Exception as e:
                logger.warning(f"Failed to convert raw record {i} to asset: {e}")
                continue

        logger.info(
            f"✅ Prepared {len(assets)} assets for agentic analysis with preserved raw record linkage"
        )
        return assets
