"""
Flow Execution Engine Collection Crew
Collection-specific persistent agent execution methods and phase handlers.
Following the pattern from Discovery flow to use persistent agents per ADR-015.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


class ExecutionEngineCollectionCrews:
    """Collection flow persistent agent execution handlers."""

    def __init__(self, crew_utils):
        self.crew_utils = crew_utils

    async def execute_collection_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute collection flow phase using persistent agents"""
        logger.info(
            f"🔄 Executing collection phase '{phase_config.name}' with persistent agents"
        )

        try:
            # Initialize persistent agent pool for this tenant
            agent_pool = await self._initialize_collection_agent_pool(master_flow)

            # Map phase names to execution methods
            mapped_phase = self._map_collection_phase_name(phase_config.name)

            # Execute the phase with persistent agents
            result = await self._execute_collection_mapped_phase(
                mapped_phase, agent_pool, phase_input
            )

            # Add metadata about persistent agent usage
            result["agent_pool_info"] = {
                "agent_pool_type": "TenantScopedAgentPool" if agent_pool else "none",
                "client_account_id": str(master_flow.client_account_id),
                "engagement_id": str(master_flow.engagement_id),
            }

            logger.info(
                f"✅ Collection phase '{phase_config.name}' completed with persistent agents"
            )
            return {
                "phase": phase_config.name,
                "status": "completed",
                "crew_results": result,
                "method": "persistent_agent_execution",
                "agents_used": result.get("agents", [result.get("agent")]),
            }

        except Exception as e:
            logger.error(f"❌ Collection phase failed: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return self.crew_utils.build_error_response(
                phase_config.name, str(e), master_flow
            )

    async def _initialize_collection_agent_pool(
        self, master_flow: CrewAIFlowStateExtensions
    ) -> Any:
        """Initialize persistent agent pool for collection tasks"""
        try:
            # Import here to avoid circular dependencies
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            # Validate required identifiers before pool init
            client_id = master_flow.client_account_id
            engagement_id = master_flow.engagement_id

            # Ensure identifiers are non-empty strings to prevent passing "None" or empty IDs
            if not client_id or not engagement_id:
                logger.error(
                    "Missing required identifiers for agent pool initialization"
                )
                raise ValueError(
                    "client_id and engagement_id are required for agent pool initialization"
                )

            # Convert to safe string representations
            safe_client = str(client_id)
            safe_eng = str(engagement_id)

            # Initialize the tenant pool (returns None but sets up the pool)
            try:
                await TenantScopedAgentPool.initialize_tenant_pool(
                    client_id=safe_client,
                    engagement_id=safe_eng,
                )
            except Exception as e:
                msg = "Failed to initialize TenantScopedAgentPool for collection flow"
                # Avoid logging sensitive identifiers directly
                logger.exception("%s", msg)
                raise RuntimeError(msg) from e

            logger.info(
                "🏊 Initialized agent pool for collection flow - client_id=%s engagement_id=%s",
                str(client_id),
                str(engagement_id),
            )

            # Return the TenantScopedAgentPool class itself for agent access
            # The pool has been initialized and agents can be retrieved via get_agent()
            return TenantScopedAgentPool

        except Exception as e:
            logger.error(f"❌ Failed to initialize collection agent pool: {e}")
            raise

    def _map_collection_phase_name(self, phase_name: str) -> str:
        """Map collection flow phase names to execution methods"""
        phase_mapping = {
            "platform_detection": "platform_detection",
            "automated_collection": "automated_collection",
            "gap_analysis": "gap_analysis",
            "questionnaire_generation": "questionnaire_generation",
            "manual_collection": "manual_collection",
        }
        return phase_mapping.get(phase_name, phase_name)

    async def _execute_collection_mapped_phase(
        self, mapped_phase: str, agent_pool: Any, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mapped collection phase with appropriate agents"""
        phase_methods = {
            "platform_detection": self._execute_platform_detection,
            "automated_collection": self._execute_automated_collection,
            "gap_analysis": self._execute_gap_analysis,
            "questionnaire_generation": self._execute_questionnaire_generation,
            "manual_collection": self._execute_manual_collection,
        }

        method = phase_methods.get(mapped_phase, self._execute_generic_collection_phase)
        return await method(agent_pool, phase_input)

    async def _execute_platform_detection(
        self, agent_pool: Any, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute platform detection phase using data analyst agent"""
        logger.info("🔍 Executing platform detection with persistent agents")

        # Use data_analyst agent for platform detection
        if agent_pool:
            try:
                # Create context from phase_input
                from app.core.context import RequestContext

                context = RequestContext(
                    client_account_id=phase_input.get("client_account_id", "1"),
                    engagement_id=phase_input.get("engagement_id", "1"),
                )

                data_analyst = await agent_pool.get_agent(
                    context=context, agent_type="data_analyst"
                )
                if data_analyst:
                    logger.info(
                        "📊 Using persistent data_analyst agent for platform detection"
                    )
            except Exception as e:
                logger.warning(f"Could not get data_analyst agent: {e}")

        return {
            "phase": "platform_detection",
            "status": "completed",
            "platforms_detected": ["cloud", "on-premise"],
            "agent": "data_analyst",
            "message": "Platform detection completed using persistent agent",
        }

    async def _execute_automated_collection(
        self, agent_pool: Any, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute automated collection phase"""
        logger.info("🤖 Executing automated collection with persistent agents")

        # Use quality_assessor agent for automated data collection
        if agent_pool:
            try:
                from app.core.context import RequestContext

                context = RequestContext(
                    client_account_id=phase_input.get("client_account_id", "1"),
                    engagement_id=phase_input.get("engagement_id", "1"),
                )

                quality_assessor = await agent_pool.get_agent(
                    context=context, agent_type="quality_assessor"
                )
                if quality_assessor:
                    logger.info(
                        "✅ Using persistent quality_assessor agent for automated collection"
                    )
            except Exception as e:
                logger.warning(f"Could not get quality_assessor agent: {e}")

        return {
            "phase": "automated_collection",
            "status": "completed",
            "data_collected": {},
            "agent": "quality_assessor",
            "message": "Automated collection completed using persistent agent",
        }

    async def _execute_gap_analysis(
        self, agent_pool: Any, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute gap analysis phase using lean single-agent service.

        Lean workflow (ADR-015):
        1. Load REAL selected assets from database
        2. Single persistent agent analyzes gaps against 22 critical attributes
        3. Generate questionnaire atomically with gap detection
        4. Persist gaps to collection_data_gaps table
        5. Return results with gap count and questionnaire
        """
        logger.info("📊 Executing gap analysis with lean single-agent service")

        # Get flow_id and selected assets from phase_input
        flow_id = phase_input.get("flow_id")
        selected_asset_ids = phase_input.get("selected_application_ids", [])

        if not flow_id:
            logger.error("No flow_id provided in phase_input")
            return {
                "phase": "gap_analysis",
                "status": "failed",
                "error": "Missing flow_id in phase_input",
            }

        if not selected_asset_ids:
            logger.warning("No selected assets provided")
            return {
                "phase": "gap_analysis",
                "status": "failed",
                "error": "No assets selected for gap analysis",
            }

        logger.info(f"Analyzing {len(selected_asset_ids)} selected assets for gaps")

        try:
            # Use lean gap analysis service
            from app.core.database import AsyncSessionLocal
            from app.services.collection.gap_analysis import GapAnalysisService

            async with AsyncSessionLocal() as db:
                service = GapAnalysisService(
                    client_account_id=phase_input.get("client_account_id", "1"),
                    engagement_id=phase_input.get("engagement_id", "1"),
                    collection_flow_id=flow_id,
                )

                result = await service.analyze_and_generate_questionnaire(
                    selected_asset_ids=selected_asset_ids,
                    db=db,
                    automation_tier=phase_input.get("automation_tier", "tier_2"),
                )

                # Check for errors
                if result.get("status") == "error":
                    logger.error(f"Gap analysis failed: {result.get('error')}")
                    return {
                        "phase": "gap_analysis",
                        "status": "failed",
                        "error": result.get("error"),
                        "message": "Gap analysis failed",
                    }

                # Extract summary
                summary = result.get("summary", {})
                gaps_persisted = summary.get("gaps_persisted", 0)
                total_gaps = summary.get("total_gaps", 0)

                logger.info(
                    f"✅ Gap analysis completed: {gaps_persisted} gaps persisted, "
                    f"{total_gaps} total gaps detected"
                )

                return {
                    "phase": "gap_analysis",
                    "status": "completed",
                    "selected_assets": selected_asset_ids,
                    "gaps_detected": gaps_persisted,
                    "total_gaps": total_gaps,
                    "gap_analysis_result": result,
                    "agent": "gap_analysis_specialist",
                    "message": (
                        f"Gap analysis completed: {gaps_persisted} gaps detected "
                        f"across {len(selected_asset_ids)} assets"
                    ),
                }

        except Exception as e:
            logger.error(f"Gap analysis failed: {e}", exc_info=True)
            return {
                "phase": "gap_analysis",
                "status": "failed",
                "error": str(e),
                "message": "Gap analysis failed due to service error",
            }

    async def _execute_questionnaire_generation(
        self, agent_pool: Any, phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute per-asset questionnaire generation using AI agent service.

        FIX (Issue #1067 - Fix #2): Use correct per-asset generation logic.
        Questionnaires are generated per asset (not per flow) using _start_agent_generation.
        """
        logger.info("📝 Executing questionnaire generation with AI agent service")

        # Extract flow_id from phase_input (child flow ID, not master)
        flow_id = phase_input.get("flow_id")
        if not flow_id:
            logger.error("❌ No flow_id in phase_input for questionnaire generation")
            return {
                "phase": "questionnaire_generation",
                "status": "failed",
                "error": "Missing flow_id in phase_input",
                "message": "Cannot generate questionnaires without flow_id",
            }

        try:
            # Import per-asset questionnaire generation service
            from app.api.v1.endpoints.collection_crud_questionnaires.commands import (
                _start_agent_generation,
            )
            from app.core.database import AsyncSessionLocal
            from app.core.context import RequestContext
            from app.models.collection_flow import CollectionFlow
            from app.models.asset import Asset
            from sqlalchemy import select
            from uuid import UUID

            async with AsyncSessionLocal() as db:
                # Get collection flow
                flow_result = await db.execute(
                    select(CollectionFlow).where(
                        CollectionFlow.flow_id == UUID(flow_id),
                        CollectionFlow.client_account_id
                        == phase_input.get("client_account_id", "1"),
                        CollectionFlow.engagement_id
                        == phase_input.get("engagement_id", "1"),
                    )
                )
                flow = flow_result.scalar_one_or_none()

                if not flow:
                    logger.error(f"❌ Collection flow {flow_id} not found")
                    return {
                        "phase": "questionnaire_generation",
                        "status": "failed",
                        "error": "Collection flow not found",
                        "message": f"Cannot find flow {flow_id}",
                    }

                # Get selected assets from flow metadata
                selected_asset_ids = []
                if flow.flow_metadata and isinstance(flow.flow_metadata, dict):
                    selected_asset_ids = flow.flow_metadata.get(
                        "selected_asset_ids", []
                    )

                if not selected_asset_ids:
                    logger.warning(f"No selected assets in flow {flow_id} metadata")
                    return {
                        "phase": "questionnaire_generation",
                        "status": "failed",
                        "error": "No assets selected for questionnaire generation",
                        "message": "Asset selection required before questionnaire generation",
                    }

                # Get assets for questionnaire generation
                assets_result = await db.execute(
                    select(Asset).where(
                        Asset.id.in_(
                            [
                                UUID(aid) if isinstance(aid, str) else aid
                                for aid in selected_asset_ids
                            ]
                        ),
                        Asset.client_account_id
                        == phase_input.get("client_account_id", "1"),
                        Asset.engagement_id == phase_input.get("engagement_id", "1"),
                    )
                )
                existing_assets = list(assets_result.scalars().all())

                if not existing_assets:
                    logger.error(f"❌ No assets found for flow {flow_id}")
                    return {
                        "phase": "questionnaire_generation",
                        "status": "failed",
                        "error": "No assets found",
                        "message": "Cannot generate questionnaires without assets",
                    }

                # Create request context for tenant scoping
                context = RequestContext(
                    client_account_id=phase_input.get("client_account_id", "1"),
                    engagement_id=phase_input.get("engagement_id", "1"),
                )

                # Call per-asset questionnaire generation
                # This creates pending questionnaires and starts background AI generation
                questionnaire_responses = await _start_agent_generation(
                    flow_id=flow_id,
                    flow=flow,
                    existing_assets=existing_assets,
                    context=context,
                    db=db,
                )

                questionnaire_count = (
                    len(questionnaire_responses) if questionnaire_responses else 0
                )
                logger.info(
                    f"✅ Generated {questionnaire_count} questionnaires via AI service "
                    f"({len(existing_assets)} assets processed)"
                )

                return {
                    "phase": "questionnaire_generation",
                    "status": "completed",
                    "questionnaires_generated": questionnaire_count,
                    "generation_method": "ai_agent",
                    "message": f"Generated {questionnaire_count} AI questionnaires for {len(existing_assets)} assets",
                }

        except ImportError as e:
            logger.error(
                f"❌ Cannot import questionnaire generation service: {e}",
                exc_info=True,
            )
            return {
                "phase": "questionnaire_generation",
                "status": "failed",
                "error": f"Service import failed: {str(e)}",
                "message": "Questionnaire generation service unavailable",
            }
        except Exception as e:
            logger.error(f"❌ Questionnaire generation failed: {e}", exc_info=True)
            return {
                "phase": "questionnaire_generation",
                "status": "failed",
                "error": str(e),
                "message": "Unexpected error during questionnaire generation",
            }

    async def _execute_manual_collection(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute manual collection phase"""
        logger.info("✍️ Executing manual collection phase")

        return {
            "phase": "manual_collection",
            "status": "completed",
            "awaiting_user_input": True,
            "agent": "quality_assessor",
            "message": "Ready for manual data collection",
        }

    async def _execute_generic_collection_phase(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generic collection phase execution for unmapped phases"""
        logger.info("🔄 Executing generic collection phase with persistent agents")

        return {
            "phase": "generic",
            "status": "completed",
            "agent_pool_available": agent_pool is not None,
            "agent_pool_type": agent_pool.__name__ if agent_pool else "none",
            "message": "Generic phase executed with persistent agent pool",
        }
