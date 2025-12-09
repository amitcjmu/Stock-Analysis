"""
Flow completion operations for Collection Flow State Management
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus

logger = logging.getLogger(__name__)


class CollectionFlowCompletionService:
    """Service for Collection Flow completion operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Collection Flow Completion Service.

        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)

    async def complete_flow(
        self,
        flow_id: uuid.UUID,
        final_quality_score: float,
        final_confidence_score: float,
        completion_metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Mark Collection Flow as completed.

        Per ADR-028: Updates master flow phase transitions, not local phase_state.

        Args:
            flow_id: Flow ID
            final_quality_score: Final quality score
            final_confidence_score: Final confidence score
            completion_metadata: Optional completion metadata

        Returns:
            Updated CollectionFlow instance
        """
        try:
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

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
            collection_flow.status = CollectionFlowStatus.COMPLETED
            collection_flow.progress_percentage = 100.0
            collection_flow.collection_quality_score = final_quality_score
            collection_flow.confidence_score = final_confidence_score
            collection_flow.completed_at = datetime.utcnow()
            collection_flow.updated_at = datetime.utcnow()

            # Update metadata
            metadata = collection_flow.metadata or {}
            metadata["completion"] = {
                "completed_at": datetime.utcnow().isoformat(),
                "final_quality_score": final_quality_score,
                "final_confidence_score": final_confidence_score,
                **(completion_metadata or {}),
            }
            collection_flow.metadata = metadata

            # ADR-028: Mark current phase as completed in master flow
            if collection_flow.master_flow_id:
                master_flow_result = await self.db.execute(
                    select(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.flow_id
                        == collection_flow.master_flow_id
                    )
                )
                master_flow = master_flow_result.scalar_one_or_none()

                if master_flow:
                    # Complete current phase in master flow
                    if master_flow.phase_transitions:
                        last_transition = master_flow.phase_transitions[-1]
                        if last_transition.get("status") == "active":
                            last_transition["status"] = "completed"
                            last_transition["completed_at"] = (
                                datetime.utcnow().isoformat()
                            )

                    # Synchronize master flow status to completed
                    await self._sync_master_flow_completion(
                        collection_flow, final_quality_score, final_confidence_score
                    )

            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.info(
                f"Completed Collection Flow {flow_id} with quality score {final_quality_score}"
            )
            return collection_flow

        except Exception as e:
            logger.error(f"Failed to complete Collection Flow {flow_id}: {str(e)}")
            await self.db.rollback()
            raise

    async def _sync_master_flow_completion(
        self,
        collection_flow: CollectionFlow,
        final_quality_score: float,
        final_confidence_score: float,
    ) -> None:
        """
        Synchronize master flow completion status

        Args:
            collection_flow: The collection flow being completed
            final_quality_score: Final quality score
            final_confidence_score: Final confidence score
        """
        try:
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            master_flow_result = await self.db.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id
                    == str(collection_flow.master_flow_id),
                    CrewAIFlowStateExtensions.client_account_id
                    == collection_flow.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id
                    == collection_flow.engagement_id,
                )
            )
            master_flow = master_flow_result.scalar_one_or_none()

            if master_flow:
                master_flow.flow_status = "completed"
                master_flow.progress_percentage = 100.0
                master_flow.updated_at = datetime.utcnow()

                # Update master flow persistence data with completion info
                persistence_data = master_flow.flow_persistence_data or {}
                persistence_data.update(
                    {
                        "completion": {
                            "completed_at": datetime.utcnow().isoformat(),
                            "completed_by": "collection_flow_state_management",
                            "final_quality_score": final_quality_score,
                            "final_confidence_score": final_confidence_score,
                            "collection_flow_id": str(collection_flow.flow_id),
                        }
                    }
                )
                master_flow.flow_persistence_data = persistence_data

                logger.info(
                    f"Synchronized master flow {master_flow.flow_id} status to completed"
                )
            else:
                logger.warning(
                    f"Master flow {collection_flow.master_flow_id} not found for "
                    f"collection flow {collection_flow.flow_id}"
                )

        except Exception as sync_error:
            logger.error(
                f"Failed to synchronize master flow status for collection {collection_flow.flow_id}: {sync_error}"
            )
            # Don't fail the entire operation if master flow sync fails
            # but ensure we log it for monitoring
