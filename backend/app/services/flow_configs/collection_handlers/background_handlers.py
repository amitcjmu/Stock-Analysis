"""
Collection Background and Async Processing Handlers
ADCS: Background task management and async flow execution handlers

Provides handler functions for background processing and asynchronous CrewAI flow execution.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def start_crewai_collection_flow_background(
    flow_id: str,
    initial_state: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    **kwargs,
):
    """Start CrewAI collection flow execution in background"""

    async def run_collection_flow():
        try:
            logger.info(f"🚀 Starting CrewAI collection flow execution: {flow_id}")

            # Import required modules
            from app.core.context import RequestContext
            from app.services.crewai_flow_service import CrewAIFlowService
            from app.services.crewai_flows.unified_collection_flow import (
                create_unified_collection_flow,
            )

            # Extract context information
            if context and hasattr(context, "client_account_id"):
                # If context is a RequestContext object
                request_context = context
            else:
                # Create RequestContext from context dict or use defaults
                context_dict = context or {}
                request_context = RequestContext(
                    client_account_id=context_dict.get("client_account_id"),
                    engagement_id=context_dict.get("engagement_id"),
                    user_id=context_dict.get("user_id", "system"),
                    flow_id=flow_id,
                )

            # Create CrewAI service (it will handle its own database connections)
            crewai_service = CrewAIFlowService()

            # Prepare initial state data
            automation_tier = initial_state.get("automation_tier", "tier_2")
            collection_config = initial_state.get("collection_config", {})
            flow_metadata = initial_state.copy()
            flow_metadata["master_flow_id"] = flow_id

            # Create the UnifiedCollectionFlow instance
            collection_flow = create_unified_collection_flow(
                flow_id=flow_id,
                client_account_id=request_context.client_account_id,
                engagement_id=request_context.engagement_id,
                user_id=request_context.user_id or "system",
                automation_tier=automation_tier,
                collection_config=collection_config,
                metadata=flow_metadata,
                crewai_service=crewai_service,
                context=request_context,
            )

            # Execute the flow (this will run the CrewAI flow)
            await collection_flow.kickoff()

            logger.info(f"✅ CrewAI collection flow completed: {flow_id}")

        except Exception as e:
            logger.error(
                f"❌ CrewAI collection flow execution failed for {flow_id}: {e}"
            )
            # Note: We don't re-raise here as this is a background task

    # Start in background - don't await
    asyncio.create_task(run_collection_flow())
    logger.info(f"🔄 CrewAI collection flow {flow_id} started in background")


# Backward compatibility alias - the original function name
async def _start_crewai_collection_flow_background(*args, **kwargs):
    """Backward compatibility alias for start_crewai_collection_flow_background"""
    return await start_crewai_collection_flow_background(*args, **kwargs)
