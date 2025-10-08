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

            # DEPRECATED: Per ADR-025, collection flows now use CollectionChildFlowService
            # This background handler is legacy and should not be called
            logger.error(
                f"❌ Legacy background handler called for {flow_id}. "
                "Collection flows now use CollectionChildFlowService pattern. "
                "This handler is no longer functional per ADR-025."
            )
            raise NotImplementedError(
                "UnifiedCollectionFlow removed per ADR-025. "
                "Use CollectionChildFlowService via Master Flow Orchestrator instead."
            )

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
