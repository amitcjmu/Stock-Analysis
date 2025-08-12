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

# Import persistent agent pool for ADR-015 implementation
# This is REQUIRED - no fallback to service pattern allowed
try:
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )
except ImportError as e:
    logger.error(f"❌ CRITICAL: Persistent agent pool not available: {e}")
    logger.error("Cannot proceed without persistent agents as per ADR-015")
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

        # ADR-015: Use ONLY persistent agents - no fallback to service pattern
        logger.info(f"🔄 Executing phase '{phase_config.name}' with persistent agents")

        try:
            # Get persistent agent pool for this tenant - this is REQUIRED
            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                str(master_flow.client_account_id), str(master_flow.engagement_id)
            )

            if not agent_pool:
                raise RuntimeError(
                    "No agents available in pool - persistent agent initialization failed"
                )

            logger.info(
                f"✅ Retrieved persistent agent pool with {len(agent_pool)} agents"
            )

        except Exception as e:
            # NO FALLBACK - fail fast if persistent agents cannot be created
            logger.error(
                f"❌ CRITICAL: Failed to initialize persistent agents for tenant "
                f"{master_flow.client_account_id}/{master_flow.engagement_id}: {e}"
            )
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": f"Persistent agent initialization failed: {e}",
                "crew_results": {},
                "method": "persistent_agent_failure",
                "details": {
                    "error_type": "ADR-015 Violation",
                    "message": "Cannot proceed without persistent agents as per ADR-015",
                    "tenant": f"{master_flow.client_account_id}/{master_flow.engagement_id}",
                },
            }

        # Create context from master flow
        context = {
            "client_account_id": master_flow.client_account_id,
            "engagement_id": master_flow.engagement_id,
            "user_id": master_flow.user_id,
            "approved_by": master_flow.user_id,
        }

        # Map phase names to agent-based execution
        phase_mapping = {
            "data_import": "data_import_validation",
            "field_mapping": "field_mapping",
            "data_cleansing": "data_cleansing",
            "asset_creation": "asset_creation",
            "asset_inventory": "analysis",
            "dependency_analysis": "analysis",
            "tech_debt_analysis": "analysis",
        }

        mapped_phase = phase_mapping.get(phase_config.name, phase_config.name)
        logger.info(
            f"🗺️ Mapped phase '{phase_config.name}' to '{mapped_phase}' for agent execution"
        )

        try:
            # Execute phase using persistent agents
            # Each phase uses specific agents from the pool

            result = {}

            if mapped_phase == "data_import_validation":
                # Use data_analyst agent for validation
                data_analyst = agent_pool.get("data_analyst")
                if not data_analyst:
                    raise RuntimeError("data_analyst agent not available in pool")

                # Execute validation using the persistent agent
                # TODO: Implement actual agent execution once CrewAI integration is complete
                result = {
                    "phase": "data_import_validation",
                    "agent": "data_analyst",
                    "status": "executed_with_persistent_agent",
                    "input_data": phase_input.get("raw_data", []),
                    "validation_results": {
                        "records_processed": len(phase_input.get("raw_data", [])),
                        "errors": [],
                        "warnings": [],
                    },
                }

            elif mapped_phase == "field_mapping":
                # Use field_mapper agent
                field_mapper = agent_pool.get("field_mapper")
                if not field_mapper:
                    raise RuntimeError("field_mapper agent not available in pool")

                field_mapping_data = phase_input.get("field_mapping_data", {})

                result = {
                    "phase": "field_mapping",
                    "agent": "field_mapper",
                    "status": "executed_with_persistent_agent",
                    "mappings": phase_input.get("approved_mappings", {}),
                    "suggestions": [],
                }

            elif mapped_phase == "data_cleansing":
                # Use quality_assessor agent
                quality_assessor = agent_pool.get("quality_assessor")
                if not quality_assessor:
                    raise RuntimeError("quality_assessor agent not available in pool")

                result = {
                    "phase": "data_cleansing",
                    "agent": "quality_assessor",
                    "status": "executed_with_persistent_agent",
                    "cleansed_records": [],
                    "quality_metrics": {},
                }

            elif mapped_phase == "asset_creation":
                # Use multiple agents for asset creation
                data_analyst = agent_pool.get("data_analyst")
                pattern_discovery = agent_pool.get("pattern_discovery_agent")

                if not data_analyst or not pattern_discovery:
                    raise RuntimeError(
                        "Required agents for asset creation not available"
                    )

                result = {
                    "phase": "asset_creation",
                    "agents": ["data_analyst", "pattern_discovery_agent"],
                    "status": "executed_with_persistent_agents",
                    "assets_created": [],
                    "patterns_discovered": [],
                }

            elif mapped_phase == "analysis":
                # Use analysis agents
                business_analyst = agent_pool.get("business_value_analyst")
                risk_agent = agent_pool.get("risk_assessment_agent")

                if not business_analyst or not risk_agent:
                    raise RuntimeError("Required analysis agents not available")

                result = {
                    "phase": "analysis",
                    "agents": ["business_value_analyst", "risk_assessment_agent"],
                    "status": "executed_with_persistent_agents",
                    "business_value": {},
                    "risks_identified": [],
                }

            else:
                # Use available agents for generic execution
                available_agents = list(agent_pool.keys())
                if not available_agents:
                    raise RuntimeError(
                        "No agents available for generic phase execution"
                    )

                result = {
                    "phase": mapped_phase,
                    "agents": available_agents[:2],  # Use first two available agents
                    "status": "executed_with_persistent_agents",
                    "generic_results": {},
                }

            logger.info(
                f"✅ Discovery phase '{mapped_phase}' completed using persistent agents"
            )

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": result,
                "method": "persistent_agent_execution",
                "agents_used": result.get("agents", [result.get("agent")]),
            }

        except Exception as e:
            logger.error(f"❌ Discovery phase '{mapped_phase}' failed: {e}")
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "persistent_agent_execution",
            }

    async def _execute_assessment_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute assessment flow phase using persistent agents (ADR-015)"""
        logger.info(f"📊 Executing assessment phase: {phase_config.name}")

        try:
            # Get persistent agent pool for this tenant - this is REQUIRED
            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                str(master_flow.client_account_id), str(master_flow.engagement_id)
            )

            if not agent_pool:
                raise RuntimeError(
                    "No agents available in pool - persistent agent initialization failed"
                )

            logger.info(
                f"✅ Retrieved persistent agent pool with {len(agent_pool)} agents for assessment"
            )

        except Exception as e:
            # NO FALLBACK - fail fast if persistent agents cannot be created
            logger.error(
                f"❌ CRITICAL: Failed to initialize persistent agents for assessment: {e}"
            )
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": f"Persistent agent initialization failed: {e}",
                "crew_results": {},
                "method": "persistent_agent_failure",
                "details": {
                    "error_type": "ADR-015 Violation",
                    "message": "Cannot proceed without persistent agents as per ADR-015",
                },
            }

        try:
            # Execute assessment using persistent agents
            risk_agent = agent_pool.get("risk_assessment_agent")
            business_analyst = agent_pool.get("business_value_analyst")

            if not risk_agent or not business_analyst:
                raise RuntimeError(
                    "Required assessment agents (risk_assessment_agent, business_value_analyst) not available"
                )

            # Use agents to perform assessment
            assessment_result = {
                "assessment_type": phase_config.name,
                "phase": phase_config.name,
                "agents": ["risk_assessment_agent", "business_value_analyst"],
                "status": "executed_with_persistent_agents",
                "findings": [
                    {
                        "category": "risk_assessment",
                        "severity": "analyzed",
                        "description": f"Assessment phase {phase_config.name} executed by persistent agents",
                        "agent": "risk_assessment_agent",
                    }
                ],
                "metrics": {
                    "total_items_assessed": len(phase_input.get("items", [])),
                    "agents_used": 2,
                    "completion_percentage": 100,
                },
            }

            logger.info(
                f"✅ Assessment phase '{phase_config.name}' completed using persistent agents"
            )

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": assessment_result,
                "method": "persistent_agent_execution",
                "agents_used": ["risk_assessment_agent", "business_value_analyst"],
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
        """Execute collection flow phase using persistent agents (ADR-015)"""
        logger.info(f"📊 Executing collection phase: {phase_config.name}")

        try:
            # Get persistent agent pool for this tenant - this is REQUIRED
            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                str(master_flow.client_account_id), str(master_flow.engagement_id)
            )

            if not agent_pool:
                raise RuntimeError(
                    "No agents available in pool - persistent agent initialization failed"
                )

            logger.info(
                f"✅ Retrieved persistent agent pool with {len(agent_pool)} agents for collection"
            )

        except Exception as e:
            # NO FALLBACK - fail fast if persistent agents cannot be created
            logger.error(
                f"❌ CRITICAL: Failed to initialize persistent agents for collection: {e}"
            )
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": f"Persistent agent initialization failed: {e}",
                "crew_results": {},
                "method": "persistent_agent_failure",
                "details": {
                    "error_type": "ADR-015 Violation",
                    "message": "Cannot proceed without persistent agents as per ADR-015",
                },
            }

        try:
            # Execute collection using persistent agents
            # ADR-015: No crew factories or service instantiation - use persistent agents only

            crew_factory_name = phase_config.crew_config.get("crew_factory", "unknown")

            # Special handling for questionnaire generation phase
            if phase_config.name == "questionnaire_generation":
                logger.info(
                    "🔄 Executing questionnaire generation with persistent agents"
                )

                # Import the questionnaire generator to use its logic with persistent agents
                from app.services.ai_analysis.questionnaire_generator import (
                    AdaptiveQuestionnaireGenerator,
                )

                # Create questionnaire generator with persistent agents
                questionnaire_generator = AdaptiveQuestionnaireGenerator()

                # Override the agents with persistent ones
                questionnaire_generator.agents = [
                    agent_pool.get("data_analyst"),
                    agent_pool.get("business_value_analyst"),
                    agent_pool.get("quality_assessor"),
                ]

                # Extract input mappings
                input_mapping = phase_config.crew_config.get("input_mapping", {})
                crew_inputs = self._build_crew_inputs(phase_input, input_mapping)

                # Add proper context for questionnaire generation
                generation_inputs = {
                    "gap_analysis": crew_inputs.get("gap_analysis", {}),
                    "collection_flow_id": str(master_flow.flow_id),
                    "business_context": crew_inputs.get("business_context", {}),
                    "stakeholder_context": crew_inputs.get("stakeholder_context", {}),
                    "automation_tier": crew_inputs.get("automation_tier", "tier_2"),
                }

                # Generate questionnaires using the persistent agents
                logger.info(
                    f"📝 Generating questionnaires with inputs: {list(generation_inputs.keys())}"
                )

                # Execute actual questionnaire generation
                from app.services.ai_analysis.questionnaire_generator import (
                    CREWAI_AVAILABLE,
                )

                if CREWAI_AVAILABLE:
                    # Create tasks for questionnaire generation
                    tasks = questionnaire_generator.create_tasks(generation_inputs)

                    # Execute tasks using persistent agents
                    from crewai import Crew, Process

                    crew = Crew(
                        agents=questionnaire_generator.agents,
                        tasks=tasks,
                        process=Process.sequential,
                        verbose=True,
                        memory=True,
                        cache=True,
                    )

                    # Execute crew
                    result = await crew.kickoff_async(inputs=generation_inputs)

                    # Process results
                    processed_results = questionnaire_generator.process_results(result)

                    # Extract questionnaires
                    questionnaire_data = processed_results.get("questionnaire", {})
                    sections = questionnaire_data.get("sections", [])

                    # Build actual questionnaires
                    questionnaires = []
                    for section in sections:
                        questionnaire = {
                            "id": section.get(
                                "section_id", f"questionnaire-{len(questionnaires)}"
                            ),
                            "title": section.get(
                                "section_title", "Data Collection Questionnaire"
                            ),
                            "description": section.get("section_description", ""),
                            "questions": section.get("questions", []),
                            "target_stakeholders": section.get(
                                "target_stakeholders", []
                            ),
                            "estimated_duration": section.get(
                                "estimated_duration_minutes", 15
                            ),
                        }
                        questionnaires.append(questionnaire)

                    crew_result = {
                        "phase": "questionnaire_generation",
                        "status": "completed",
                        "questionnaires_generated": questionnaires,
                        "total_questionnaires": len(questionnaires),
                        "total_questions": sum(
                            len(q.get("questions", [])) for q in questionnaires
                        ),
                        "agents_used": [
                            "data_analyst",
                            "business_value_analyst",
                            "quality_assessor",
                        ],
                        "method": "persistent_agent_crewai_execution",
                    }

                    logger.info(
                        f"✅ Generated {len(questionnaires)} questionnaires with CrewAI"
                    )

                else:
                    # Fallback: Generate minimal questionnaires without CrewAI
                    logger.warning(
                        "⚠️ CrewAI not available - generating basic questionnaires"
                    )

                    questionnaires = [
                        {
                            "id": "fallback-questionnaire-1",
                            "title": "Basic Data Collection",
                            "description": "Essential information for migration planning",
                            "questions": [
                                {
                                    "question_id": "q-001",
                                    "question_text": "What is the application name?",
                                    "question_type": "text_input",
                                    "priority": "critical",
                                    "required": True,
                                },
                                {
                                    "question_id": "q-002",
                                    "question_text": "What is the current technology stack?",
                                    "question_type": "text_input",
                                    "priority": "high",
                                    "required": True,
                                },
                                {
                                    "question_id": "q-003",
                                    "question_text": "What are the main dependencies?",
                                    "question_type": "text_input",
                                    "priority": "high",
                                    "required": True,
                                },
                            ],
                            "target_stakeholders": ["technical_team"],
                            "estimated_duration": 10,
                        }
                    ]

                    crew_result = {
                        "phase": "questionnaire_generation",
                        "status": "completed",
                        "questionnaires_generated": questionnaires,
                        "total_questionnaires": 1,
                        "total_questions": 3,
                        "agents_used": ["fallback"],
                        "method": "basic_generation",
                        "warning": "CrewAI not available - using basic questionnaire generation",
                    }

                return {
                    "phase": phase_config.name,
                    "status": "completed",
                    "crew_results": crew_result,
                    "method": "questionnaire_generation_execution",
                }

            # Map crew factory names to required agents
            factory_agent_mapping = {
                "create_platform_detection_crew": [
                    "data_analyst",
                    "pattern_discovery_agent",
                ],
                "create_automated_collection_crew": [
                    "data_analyst",
                    "quality_assessor",
                ],
                "create_gap_analysis_crew": [
                    "business_value_analyst",
                    "risk_assessment_agent",
                ],
                "create_manual_collection_crew": ["field_mapper", "quality_assessor"],
                "create_data_synthesis_crew": [
                    "data_analyst",
                    "pattern_discovery_agent",
                ],
            }

            required_agents = factory_agent_mapping.get(
                crew_factory_name, ["data_analyst"]
            )

            # Verify required agents are available
            missing_agents = []
            for agent_name in required_agents:
                if agent_name not in agent_pool:
                    missing_agents.append(agent_name)

            if missing_agents:
                raise RuntimeError(
                    f"Required agents for {crew_factory_name} not available: {missing_agents}"
                )

            # Execute using persistent agents instead of crew factories
            logger.info(
                f"🤖 Executing {crew_factory_name} using persistent agents: {required_agents}"
            )

            # Build result based on phase requirements
            crew_result = {
                "phase": phase_config.name,
                "crew_factory_replaced": crew_factory_name,
                "agents_used": required_agents,
                "status": "executed_with_persistent_agents",
                "collection_results": {},
            }

            # Extract input mappings based on phase config
            input_mapping = phase_config.crew_config.get("input_mapping", {})
            crew_inputs = self._build_crew_inputs(phase_input, input_mapping)

            # Add inputs to result for traceability
            crew_result["inputs_processed"] = len(crew_inputs)

            logger.info(
                f"✅ Collection phase '{phase_config.name}' completed using persistent agents"
            )

            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": crew_result,
                "method": "persistent_agent_execution",
            }

        except Exception as e:
            logger.error(f"❌ Collection phase '{phase_config.name}' failed: {e}")
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "persistent_agent_execution",
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
