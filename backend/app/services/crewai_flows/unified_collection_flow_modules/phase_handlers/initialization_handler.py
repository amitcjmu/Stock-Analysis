"""
Initialization Phase Handler

Handles the initialization phase of the collection flow.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import update

from app.models.collection_flow import (CollectionFlow, CollectionFlowError,
                                        CollectionFlowState,
                                        CollectionFlowStatus, CollectionPhase,
                                        CollectionStatus)
from app.services.crewai_flows.handlers.enhanced_error_handler import \
    enhanced_error_handler

logger = logging.getLogger(__name__)


class InitializationHandler:
    """Handles initialization phase of collection flow"""

    def __init__(self, flow_context, state_manager, services, unified_flow_management):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.unified_flow_management = unified_flow_management

    async def initialize_collection(
        self, state: CollectionFlowState, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initialize the collection flow"""
        try:
            logger.info("🔄 Starting Collection Flow initialization")

            # Update state
            state.status = CollectionStatus.INITIALIZING
            state.current_phase = CollectionPhase.INITIALIZATION
            state.updated_at = datetime.utcnow()

            # Initialize flow in database
            await self.services.state_service.initialize_collection_flow(
                flow_id=state.flow_id,
                automation_tier=state.automation_tier.value,
                configuration={
                    "client_requirements": config.get("client_requirements", {}),
                    "environment_config": config.get("environment_config", {}),
                    "master_flow_id": config.get("master_flow_id"),
                    "discovery_flow_id": config.get("discovery_flow_id"),
                },
            )

            # Persist initial state
            await self.state_manager.save_state(state.to_dict())

            # Log initialization
            await self.services.audit_logging.log_flow_event(
                flow_id=state.flow_id,
                event_type="flow_initialized",
                event_data={
                    "automation_tier": state.automation_tier.value,
                    "environment_config": config.get("environment_config", {}),
                },
            )

            # Update phase
            state.current_phase = CollectionPhase.PLATFORM_DETECTION
            state.next_phase = CollectionPhase.AUTOMATED_COLLECTION
            state.progress = 5.0

            # Update database status to prevent blocking
            if self.flow_context.db_session:
                try:
                    stmt = (
                        update(CollectionFlow)
                        .where(CollectionFlow.id == uuid.UUID(state.flow_id))
                        .values(
                            status=CollectionFlowStatus.PLATFORM_DETECTION.value,
                            current_phase=CollectionPhase.PLATFORM_DETECTION.value,
                            progress_percentage=5.0,
                            updated_at=datetime.utcnow(),
                        )
                    )
                    await self.flow_context.db_session.execute(stmt)
                    await self.flow_context.db_session.commit()
                    logger.info(
                        f"✅ Updated flow {state.flow_id} status from INITIALIZED to PLATFORM_DETECTION"
                    )
                except Exception as e:
                    logger.error(f"Failed to update flow status in database: {e}")
                    # Continue even if database update fails

            return {
                "phase": "initialization",
                "status": "completed",
                "next_phase": "platform_detection",
                "flow_id": state.flow_id,
            }

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            state.add_error("initialization", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Initialization failed: {e}")
