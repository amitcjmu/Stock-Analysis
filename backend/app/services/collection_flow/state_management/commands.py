"""
Command operations for Collection Flow State Management
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)

from .base import CollectionPhase, CollectionPhaseUtils

logger = logging.getLogger(__name__)


class CollectionFlowCommandService:
    """Command service for Collection Flow operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Collection Flow Command Service.

        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)

    async def initialize_flow(
        self,
        flow_name: str,
        automation_tier: AutomationTier,
        master_flow_id: Optional[uuid.UUID] = None,
        discovery_flow_id: Optional[uuid.UUID] = None,
        collection_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Initialize a new Collection Flow.

        Args:
            flow_name: Name of the collection flow
            automation_tier: Automation tier (tier_1, tier_2, tier_3, tier_4)
            master_flow_id: Optional master flow ID
            discovery_flow_id: Optional discovery flow ID
            collection_config: Optional collection configuration
            metadata: Optional metadata

        Returns:
            Created CollectionFlow instance
        """
        try:
            # Generate unique flow ID
            flow_id = uuid.uuid4()

            # Initialize phase state - start at gap_analysis by default per v4 plan
            phase_state = {
                "current_phase": CollectionPhase.GAP_ANALYSIS.value,
                "phase_history": [
                    {
                        "phase": CollectionPhase.GAP_ANALYSIS.value,
                        "started_at": datetime.utcnow().isoformat(),
                        "status": "active",
                        "metadata": {
                            "started_directly": True,
                            "reason": "Default collection flow starts at gap analysis phase (v4 plan)",
                        },
                    }
                ],
                "phase_metadata": {
                    "gap_analysis": {
                        "started_directly": True,
                        "skip_platform_detection": True,
                        "skip_automated_collection": True,
                    }
                },
            }

            # Create the collection flow
            collection_flow = CollectionFlow(
                id=uuid.uuid4(),
                flow_id=flow_id,
                flow_name=flow_name,
                client_account_id=uuid.UUID(self.client_account_id),
                engagement_id=uuid.UUID(self.engagement_id),
                user_id=uuid.UUID(str(self.context.user_id)),
                automation_tier=automation_tier,
                status=CollectionFlowStatus.GAP_ANALYSIS,
                current_phase=CollectionPhase.GAP_ANALYSIS.value,
                phase_state=phase_state,
                collection_config=collection_config or {},
                metadata=metadata or {},
                master_flow_id=master_flow_id,
                discovery_flow_id=discovery_flow_id,
            )

            self.db.add(collection_flow)
            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.info(
                f"Initialized Collection Flow {flow_id} with tier {automation_tier}"
            )
            return collection_flow

        except Exception as e:
            logger.error(f"Failed to initialize Collection Flow: {str(e)}")
            await self.db.rollback()
            raise

    async def transition_phase(
        self,
        flow_id: uuid.UUID,
        new_phase: CollectionPhase,
        phase_metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Transition Collection Flow to a new phase.

        Args:
            flow_id: Flow ID
            new_phase: New phase to transition to
            phase_metadata: Optional metadata for the phase

        Returns:
            Updated CollectionFlow instance
        """
        try:
            # Get the collection flow
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            collection_flow = result.scalar_one_or_none()

            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")

            # Validate phase transition
            if not CollectionPhaseUtils.is_valid_transition(
                collection_flow.current_phase, new_phase.value
            ):
                raise ValueError(
                    f"Invalid phase transition from {collection_flow.current_phase} to {new_phase.value}"
                )

            # Update phase state
            phase_state = collection_flow.phase_state or {}
            phase_state["current_phase"] = new_phase.value

            # Update phase history
            if "phase_history" not in phase_state:
                phase_state["phase_history"] = []

            # Complete previous phase
            if phase_state["phase_history"]:
                phase_state["phase_history"][-1][
                    "completed_at"
                ] = datetime.utcnow().isoformat()
                phase_state["phase_history"][-1]["status"] = "completed"

            # Add new phase
            phase_state["phase_history"].append(
                {
                    "phase": new_phase.value,
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "active",
                    "metadata": phase_metadata or {},
                }
            )

            # Update phase metadata
            if phase_metadata:
                if "phase_metadata" not in phase_state:
                    phase_state["phase_metadata"] = {}
                phase_state["phase_metadata"][new_phase.value] = phase_metadata

            # Update the collection flow
            collection_flow.current_phase = new_phase.value
            collection_flow.phase_state = phase_state
            collection_flow.status = CollectionPhaseUtils.map_phase_to_status(new_phase)
            collection_flow.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.info(
                f"Transitioned Collection Flow {flow_id} to phase {new_phase.value}"
            )
            return collection_flow

        except Exception as e:
            logger.error(
                f"Failed to transition phase for Collection Flow {flow_id}: {str(e)}"
            )
            await self.db.rollback()
            raise

    async def update_progress(
        self,
        flow_id: uuid.UUID,
        progress_percentage: float,
        quality_score: Optional[float] = None,
        confidence_score: Optional[float] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Update Collection Flow progress and scores.

        Args:
            flow_id: Flow ID
            progress_percentage: Progress percentage (0-100)
            quality_score: Optional quality score
            confidence_score: Optional confidence score
            metadata_updates: Optional metadata updates

        Returns:
            Updated CollectionFlow instance
        """
        try:
            # Get the collection flow
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            collection_flow = result.scalar_one_or_none()

            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")

            # Update progress and scores
            collection_flow.progress_percentage = min(
                100.0, max(0.0, progress_percentage)
            )

            if quality_score is not None:
                collection_flow.collection_quality_score = quality_score

            if confidence_score is not None:
                collection_flow.confidence_score = confidence_score

            # Update metadata
            if metadata_updates:
                metadata = collection_flow.metadata or {}
                metadata.update(metadata_updates)
                collection_flow.metadata = metadata

            collection_flow.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.info(
                f"Updated progress for Collection Flow {flow_id}: {progress_percentage}%"
            )
            return collection_flow

        except Exception as e:
            logger.error(
                f"Failed to update progress for Collection Flow {flow_id}: {str(e)}"
            )
            await self.db.rollback()
            raise

    async def fail_flow(
        self,
        flow_id: uuid.UUID,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Mark Collection Flow as failed.

        Args:
            flow_id: Flow ID
            error_message: Error message
            error_details: Optional error details

        Returns:
            Updated CollectionFlow instance
        """
        try:
            # Get the collection flow
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            collection_flow = result.scalar_one_or_none()

            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")

            # Update flow status
            collection_flow.status = CollectionFlowStatus.FAILED
            collection_flow.error_message = error_message
            collection_flow.error_details = error_details or {}
            collection_flow.updated_at = datetime.utcnow()

            # Update phase state
            phase_state = collection_flow.phase_state or {}
            if "phase_history" in phase_state and phase_state["phase_history"]:
                phase_state["phase_history"][-1]["status"] = "failed"
                phase_state["phase_history"][-1][
                    "completed_at"
                ] = datetime.utcnow().isoformat()
                phase_state["phase_history"][-1]["error"] = error_message
            collection_flow.phase_state = phase_state

            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.error(f"Collection Flow {flow_id} failed: {error_message}")
            return collection_flow

        except Exception as e:
            logger.error(
                f"Failed to mark Collection Flow {flow_id} as failed: {str(e)}"
            )
            await self.db.rollback()
            raise
