"""
Collection Flow Lifecycle Handlers
ADCS: Flow initialization and finalization handlers

Provides handler functions for flow initialization and finalization operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import CollectionHandlerBase

logger = logging.getLogger(__name__)


class LifecycleHandlers(CollectionHandlerBase):
    """Handlers for collection flow lifecycle management"""

    async def collection_initialization(
        self,
        flow_id: str,
        flow_type: str,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Initialize Collection flow configuration - following async flow state pattern"""
        try:
            logger.info(f"🚀 Initializing Collection flow {flow_id}")

            # Extract configuration
            config = configuration or {}
            state = initial_state or {}

            # Set up collection-specific initialization (no DB operations)
            initialization_result = {
                "initialized": True,
                "flow_id": flow_id,
                "initialization_time": datetime.utcnow().isoformat(),
                "collection_config": {
                    "automation_tier": state.get("automation_tier", "tier_2"),
                    "parallel_collection": config.get("parallel_collection", True),
                    "quality_threshold": config.get("quality_threshold", 0.8),
                    "gap_analysis_enabled": config.get("gap_analysis_enabled", True),
                    "adaptive_questionnaires": config.get(
                        "adaptive_questionnaires", True
                    ),
                    "max_collection_attempts": config.get("max_collection_attempts", 3),
                },
                "platform_detection": {
                    "auto_discovery": config.get("auto_discovery", True),
                    "credential_validation": config.get("credential_validation", True),
                    "tier_assessment": config.get("tier_assessment", True),
                },
                "adapter_settings": {
                    "timeout_seconds": config.get("adapter_timeout", 300),
                    "retry_attempts": config.get("retry_attempts", 3),
                    "batch_size": config.get("batch_size", 100),
                },
                "monitoring": {
                    "metrics_enabled": True,
                    "log_level": config.get("log_level", "INFO"),
                    "alerts_enabled": config.get("alerts_enabled", True),
                },
            }

            # Add initial state data if provided
            if state:
                initialization_result["initial_state"] = state

            # Initialize statistics tracking (in-memory only)
            initialization_result["statistics"] = {
                "platforms_detected": 0,
                "data_collected": 0,
                "gaps_identified": 0,
                "questionnaires_generated": 0,
                "start_time": datetime.utcnow().isoformat(),
            }

            # Start CrewAI flow execution in background
            try:
                from .background_handlers import start_crewai_collection_flow_background

                await start_crewai_collection_flow_background(flow_id, state, context)
                initialization_result["crewai_execution"] = "started"
                logger.info(
                    f"✅ Collection flow {flow_id} initialized successfully with CrewAI execution started"
                )
            except Exception as crewai_error:
                logger.error(
                    f"⚠️ Collection flow {flow_id} initialized but CrewAI execution failed to start: {crewai_error}"
                )
                initialization_result["crewai_execution"] = "failed"
                initialization_result["crewai_error"] = str(crewai_error)

            return initialization_result

        except Exception as e:
            logger.error(f"❌ Collection initialization failed: {e}")
            return {
                "initialized": False,
                "flow_id": flow_id,
                "error": str(e),
                "initialization_time": datetime.utcnow().isoformat(),
            }

    async def collection_finalization(
        self,
        db: AsyncSession,
        flow_id: str,
        final_state: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Finalize Collection flow and update records"""
        try:
            logger.info(f"🏁 Finalizing Collection flow {flow_id}")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Calculate final metrics
            crew_results = final_state.get("crew_results", {})
            quality_report = crew_results.get("quality_report", {})

            # Update collection flow
            update_query = """
                UPDATE collection_flows
                SET status = :status,
                    completed_at = :completed_at,
                    collection_quality_score = :quality_score,
                    confidence_score = :confidence_score,
                    metadata = metadata || :metadata::jsonb,
                    updated_at = :updated_at
                WHERE master_flow_id = :master_flow_id
            """

            await db.execute(
                update_query,
                {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "quality_score": quality_report.get("overall_quality", 0.0),
                    "confidence_score": crew_results.get("sixr_readiness_score", 0.0),
                    "metadata": {
                        "completion_time": datetime.utcnow().isoformat(),
                        "total_resources_collected": quality_report.get(
                            "total_resources", 0
                        ),
                        "platforms_collected": len(crew_results.get("final_data", {})),
                        "collection_summary": crew_results.get("summary", {}),
                    },
                    "updated_at": datetime.utcnow(),
                    "master_flow_id": flow_id,
                },
            )

            # Update master flow
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            master_flow_query = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            result = await db.execute(master_flow_query)
            master_flow = result.scalar_one_or_none()

            if master_flow:
                master_flow.collection_quality_score = quality_report.get(
                    "overall_quality", 0.0
                )
                master_flow.data_collection_metadata["completed_at"] = (
                    datetime.utcnow().isoformat()
                )
                master_flow.data_collection_metadata["final_metrics"] = {
                    "quality_score": quality_report.get("overall_quality", 0.0),
                    "sixr_readiness": crew_results.get("sixr_readiness_score", 0.0),
                    "total_resources": quality_report.get("total_resources", 0),
                }

            await db.commit()

            return {
                "success": True,
                "message": "Collection flow finalized successfully",
                "final_metrics": {
                    "quality_score": quality_report.get("overall_quality", 0.0),
                    "sixr_readiness": crew_results.get("sixr_readiness_score", 0.0),
                    "total_resources": quality_report.get("total_resources", 0),
                    "completion_time": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"❌ Collection finalization failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}


# Create singleton instance for backward compatibility
lifecycle_handlers = LifecycleHandlers()


# Export functions for backward compatibility
async def collection_initialization(*args, **kwargs):
    return await lifecycle_handlers.collection_initialization(*args, **kwargs)


async def collection_finalization(*args, **kwargs):
    return await lifecycle_handlers.collection_finalization(*args, **kwargs)
