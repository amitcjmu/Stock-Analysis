"""
Flow Execution Engine CrewAI Module

Handles CrewAI-specific execution logic for discovery and assessment flows.
"""

import asyncio
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry

logger = get_logger(__name__)

# Import these at module level to avoid reimport issues during execution
# This prevents SQLAlchemy metadata conflicts when models are imported multiple times
try:
    from app.core.database import AsyncSessionLocal
    from app.services.crewai_flow_service import CrewAIFlowService
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )
except ImportError as e:
    logger.warning(f"Optional imports for CrewAI execution not available: {e}")
    AsyncSessionLocal = None
    CrewAIFlowService = None
    TenantScopedAgentPool = None


class FlowCrewExecutor:
    """
    Handles execution of CrewAI flow phases for different flow types.
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry: FlowTypeRegistry,
        handler_registry: HandlerRegistry,
        validator_registry: ValidatorRegistry,
    ):
        """Initialize the CrewAI flow executor"""
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry

        logger.info(
            f"✅ Flow CrewAI Executor initialized for client {context.client_account_id}"
        )

    async def execute_crew_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a phase through CrewAI by delegating to the actual flow implementation"""
        logger.info(
            f"🔄 Executing CrewAI phase: {phase_config.name} for flow type: {master_flow.flow_type}"
        )

        try:
            # Delegate based on flow type
            if master_flow.flow_type == "discovery":
                return await self._execute_discovery_phase(
                    master_flow, phase_config, phase_input
                )
            elif master_flow.flow_type == "assessment":
                return await self._execute_assessment_phase(
                    master_flow, phase_config, phase_input
                )
            elif master_flow.flow_type == "collection":
                return await self._execute_collection_phase(
                    master_flow, phase_config, phase_input
                )
            else:
                # For other flow types, use placeholder until services are implemented
                logger.warning(
                    f"⚠️ Flow type '{master_flow.flow_type}' delegation not yet implemented"
                )

                return {
                    "phase": phase_config.name,
                    "status": "completed",
                    "crew_results": {
                        "message": f"{master_flow.flow_type} flow delegation pending implementation",
                        "flow_type": master_flow.flow_type,
                        "phase": phase_config.name,
                        "phase_input": phase_input,
                    },
                    "warning": f"{master_flow.flow_type} flow service not yet implemented",
                }

        except Exception as e:
            logger.error(f"❌ Failed to execute crew phase: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return error result but don't raise - let the orchestrator handle it
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "error_during_delegation",
            }

    async def _execute_discovery_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute discovery flow phase using persistent agents (ADR-015)"""
        # Imports moved to module level to prevent reimport issues

        # ADR-015: Use persistent agents instead of creating new ones
        logger.info(f"🔄 Using persistent agents for phase: {phase_config.name}")

        try:
            # Get persistent agent pool for this tenant
            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                master_flow.client_account_id, master_flow.engagement_id
            )

            logger.info(
                f"✅ Retrieved persistent agent pool with {len(agent_pool)} agents"
            )

        except Exception as e:
            logger.warning(
                f"⚠️ Failed to get persistent agents, falling back to service pattern: {e}"
            )
            # Fallback to original pattern if persistent agents fail
            async with AsyncSessionLocal() as db:
                crewai_service = CrewAIFlowService(db)

        # Create context from master flow
        context = {
            "client_account_id": master_flow.client_account_id,
            "engagement_id": master_flow.engagement_id,
            "user_id": master_flow.user_id,
            "approved_by": master_flow.user_id,
        }

        # Map phase names to CrewAI flow phases
        # Fix: Use actual phase names that match the valid discovery phases
        phase_mapping = {
            "data_import": "data_import_validation",  # Maps to execute_data_import_validation
            "field_mapping": "field_mapping",  # Maps to field mapping methods
            "data_cleansing": "data_cleansing",  # Maps to execute_data_cleansing
            "asset_creation": "asset_creation",  # Maps to create_discovery_assets
            "asset_inventory": "analysis",  # Maps to execute_analysis_phases
            "dependency_analysis": "analysis",  # Maps to execute_analysis_phases
            "tech_debt_analysis": "analysis",  # Maps to execute_analysis_phases
        }

        mapped_phase = phase_mapping.get(phase_config.name, phase_config.name)
        logger.info(
            f"🗺️ Mapped phase '{phase_config.name}' to '{mapped_phase}' for discovery flow"
        )

        try:
            # Execute phase through CrewAI service
            if mapped_phase == "data_import_validation":
                result = await crewai_service.execute_data_import_validation(
                    flow_id=master_flow.flow_id,
                    raw_data=phase_input.get("raw_data", []),
                    **context,
                )
            elif mapped_phase == "field_mapping":
                # Handle field mapping with approval if needed
                field_mapping_data = phase_input.get("field_mapping_data", {})

                if phase_input.get("approved_mappings"):
                    # Apply approved mappings
                    result = await crewai_service.apply_field_mappings(
                        flow_id=master_flow.flow_id,
                        approved_mappings=phase_input["approved_mappings"],
                        **context,
                    )
                else:
                    # Generate mapping suggestions
                    result = await crewai_service.generate_field_mapping_suggestions(
                        flow_id=master_flow.flow_id,
                        validation_result=field_mapping_data,
                        **context,
                    )
            elif mapped_phase == "data_cleansing":
                result = await crewai_service.execute_data_cleansing(
                    flow_id=master_flow.flow_id,
                    field_mappings=phase_input.get("field_mappings", {}),
                    **context,
                )
            elif mapped_phase == "asset_creation":
                result = await crewai_service.create_discovery_assets(
                    flow_id=master_flow.flow_id,
                    cleaned_data=phase_input.get("cleaned_data", []),
                    **context,
                )
            elif mapped_phase == "analysis":
                result = await crewai_service.execute_analysis_phases(
                    flow_id=master_flow.flow_id,
                    assets=phase_input.get("assets", []),
                    **context,
                )
            else:
                # Generic execution
                result = await crewai_service.execute_flow_phase(
                    flow_id=master_flow.flow_id,
                    phase_name=mapped_phase,
                    phase_input=phase_input,
                    **context,
                )

            logger.info(f"✅ Discovery phase '{mapped_phase}' completed successfully")

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": result,
                "method": "crewai_discovery_delegation",
            }

        except Exception as e:
            logger.error(f"❌ Discovery phase '{mapped_phase}' failed: {e}")
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "crewai_discovery_delegation",
            }

    async def _execute_assessment_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute assessment flow phase"""
        logger.info(f"📊 Executing assessment phase: {phase_config.name}")

        try:
            # Assessment flow logic would go here
            # For now, return a placeholder implementation

            # Simulate assessment processing
            await asyncio.sleep(0.1)  # Simulate processing time

            assessment_result = {
                "assessment_type": "placeholder",
                "phase": phase_config.name,
                "input_processed": len(phase_input),
                "findings": [
                    {
                        "category": "configuration",
                        "severity": "medium",
                        "description": f"Assessment phase {phase_config.name} executed",
                        "recommendations": ["Review assessment implementation"],
                    }
                ],
                "metrics": {
                    "total_items_assessed": len(phase_input.get("items", [])),
                    "issues_found": 1,
                    "completion_percentage": 100,
                },
            }

            logger.info(
                f"✅ Assessment phase '{phase_config.name}' completed (placeholder)"
            )

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": assessment_result,
                "method": "assessment_placeholder",
                "note": "Assessment flow implementation pending",
            }

        except Exception as e:
            logger.error(f"❌ Assessment phase '{phase_config.name}' failed: {e}")
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "assessment_placeholder",
            }

    async def _execute_collection_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute collection flow phase"""
        logger.info(f"📊 Executing collection phase: {phase_config.name}")

        try:
            # Get CrewAI service
            from app.services.crewai_flow_service import CrewAIFlowService

            crewai_service = CrewAIFlowService()

            # Import the appropriate crew based on phase
            crew_factory_name = phase_config.crew_config.get("crew_factory")
            crew = None
            crew_result = {}

            # Extract input mappings based on phase config
            input_mapping = phase_config.crew_config.get("input_mapping", {})
            crew_inputs = self._build_crew_inputs(phase_input, input_mapping)

            logger.info(f"🤖 Creating crew using factory: {crew_factory_name}")

            if crew_factory_name == "create_platform_detection_crew":
                from app.services.crewai_flows.crews.collection import (
                    create_platform_detection_crew,
                )

                crew = create_platform_detection_crew(
                    crewai_service=crewai_service,
                    environment_config=crew_inputs.get("infrastructure_data", {}),
                    tier_assessment=crew_inputs.get("context", {}).get(
                        "automation_tier", "tier_2"
                    ),
                    discovery_scope=crew_inputs.get("context", {}).get(
                        "discovery_scope", "full"
                    ),
                    platform_hints=crew_inputs.get("context", {}).get(
                        "platform_hints", []
                    ),
                )
            elif crew_factory_name == "create_automated_collection_crew":
                from app.services.crewai_flows.crews.collection import (
                    create_automated_collection_crew,
                )

                crew = create_automated_collection_crew(
                    crewai_service=crewai_service,
                    platforms=crew_inputs.get("platforms", []),
                    tier_assessments=crew_inputs.get("context", {}).get(
                        "tier_assignments", {}
                    ),
                    adapter_recommendations=crew_inputs.get("adapter_configs", []),
                    available_adapters=["aws", "azure", "gcp", "vmware", "kubernetes"],
                )
            elif crew_factory_name == "create_gap_analysis_crew":
                from app.services.crewai_flows.crews.collection import (
                    create_gap_analysis_crew,
                )

                crew = create_gap_analysis_crew(
                    crewai_service=crewai_service,
                    collected_data=crew_inputs.get("collected_data", {}),
                    quality_assessment=crew_inputs.get("context", {}).get(
                        "quality_scores", {}
                    ),
                    sixr_requirements=crew_inputs.get("requirements", {}).get(
                        "sixr_requirements", {}
                    ),
                    custom_requirements=crew_inputs.get("requirements", {}).get(
                        "custom_requirements", []
                    ),
                )
            elif crew_factory_name == "create_manual_collection_crew":
                from app.services.crewai_flows.crews.collection import (
                    create_manual_collection_crew,
                )

                crew = create_manual_collection_crew(
                    crewai_service=crewai_service,
                    data_gaps=crew_inputs.get("gaps", {}).get("data_gaps", []),
                    gap_categories=crew_inputs.get("gaps", {}).get(
                        "gap_categories", {}
                    ),
                    existing_data=crew_inputs.get("context", {}).get(
                        "existing_data", {}
                    ),
                    questionnaire_templates=crew_inputs.get("templates", {}),
                )
            elif crew_factory_name == "create_data_synthesis_crew":
                from app.services.crewai_flows.crews.collection import (
                    create_data_synthesis_crew,
                )

                crew = create_data_synthesis_crew(
                    crewai_service=crewai_service,
                    all_collected_data=crew_inputs.get("data_sources", {}),
                    validation_rules=crew_inputs.get("validation_rules", {}),
                    quality_assessments=crew_inputs.get("context", {}).get(
                        "quality_scores", {}
                    ),
                    synthesis_config=crew_inputs.get("context", {}),
                )
            else:
                logger.error(f"Unknown collection crew factory: {crew_factory_name}")
                return {
                    "phase": phase_config.name,
                    "status": "failed",
                    "error": f"Unknown crew factory: {crew_factory_name}",
                    "crew_results": {},
                    "method": "collection_crew_execution",
                }

            # Execute the crew
            if crew:
                logger.info(f"🚀 Executing {phase_config.name} crew with kickoff()")

                # Get execution config
                exec_config = phase_config.crew_config.get("execution_config", {})
                timeout = exec_config.get("timeout_seconds", 300)

                # Execute crew with timeout
                try:
                    crew_task = asyncio.create_task(
                        asyncio.to_thread(crew.kickoff, inputs=crew_inputs)
                    )
                    crew_result = await asyncio.wait_for(crew_task, timeout=timeout)

                    logger.info(
                        f"✅ Collection crew execution completed for phase '{phase_config.name}'"
                    )

                    # Process crew results based on output mapping
                    output_mapping = phase_config.crew_config.get("output_mapping", {})
                    processed_results = self._process_crew_output(
                        crew_result, output_mapping
                    )

                except asyncio.TimeoutError:
                    logger.error(
                        f"⏱️ Collection crew execution timed out after {timeout} seconds"
                    )
                    return {
                        "phase": phase_config.name,
                        "status": "failed",
                        "error": f"Crew execution timed out after {timeout} seconds",
                        "crew_results": {},
                        "method": "collection_crew_execution",
                    }

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": processed_results if crew else {},
                "method": "collection_crew_execution",
            }

        except Exception as e:
            logger.error(f"❌ Collection phase '{phase_config.name}' failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "collection_crew_execution",
            }

    def _build_crew_inputs(
        self, phase_input: Dict[str, Any], input_mapping: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build crew inputs based on input mapping configuration"""
        crew_inputs = {}

        for key, value in input_mapping.items():
            if isinstance(value, str):
                # Simple mapping from phase_input
                if value.startswith("state."):
                    field = value.replace("state.", "")
                    crew_inputs[key] = phase_input.get(field, {})
                else:
                    crew_inputs[key] = phase_input.get(value, {})
            elif isinstance(value, dict):
                # Nested mapping
                crew_inputs[key] = {}
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, str):
                        if sub_value.startswith("state."):
                            field = sub_value.replace("state.", "")
                            crew_inputs[key][sub_key] = phase_input.get(field, {})
                        else:
                            crew_inputs[key][sub_key] = phase_input.get(sub_value, {})
                    else:
                        crew_inputs[key][sub_key] = sub_value
            else:
                crew_inputs[key] = value

        return crew_inputs

    def _process_crew_output(
        self, crew_result: Any, output_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process crew output based on output mapping configuration"""
        processed = {}

        # If crew_result is a string or simple type, wrap it
        if not isinstance(crew_result, dict):
            crew_result = {"result": crew_result}

        for key, value in output_mapping.items():
            if value.startswith("crew_results."):
                field = value.replace("crew_results.", "")
                if hasattr(crew_result, field):
                    processed[key] = getattr(crew_result, field)
                elif isinstance(crew_result, dict) and field in crew_result:
                    processed[key] = crew_result[field]
                else:
                    processed[key] = None
            else:
                processed[key] = crew_result.get(value, None)

        # Include raw result as well
        processed["raw_result"] = crew_result

        return processed
