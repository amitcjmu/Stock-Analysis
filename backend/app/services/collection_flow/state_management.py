"""
Collection Flow State Management Service

This service manages the lifecycle and state transitions of Collection Flows,
including initialization, phase transitions, and status updates.
"""

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import AutomationTier, CollectionFlow, CollectionFlowStatus

logger = logging.getLogger(__name__)


class CollectionPhase(str, Enum):
    """Collection Flow phases"""
    INITIALIZATION = "initialization"
    PLATFORM_DETECTION = "platform_detection"
    AUTOMATED_COLLECTION = "automated_collection"
    GAP_ANALYSIS = "gap_analysis"
    MANUAL_COLLECTION = "manual_collection"
    FINALIZATION = "finalization"


class CollectionFlowStateService:
    """
    Service for managing Collection Flow state and lifecycle.
    
    This service handles:
    - Flow initialization and setup
    - Phase transitions and validation
    - State updates and persistence
    - Flow completion and finalization
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Collection Flow State Service.
        
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
        metadata: Optional[Dict[str, Any]] = None
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
            
            # Initialize phase state
            phase_state = {
                "current_phase": CollectionPhase.INITIALIZATION.value,
                "phase_history": [{
                    "phase": CollectionPhase.INITIALIZATION.value,
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "active"
                }],
                "phase_metadata": {}
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
                status=CollectionFlowStatus.INITIALIZED,
                current_phase=CollectionPhase.INITIALIZATION.value,
                phase_state=phase_state,
                collection_config=collection_config or {},
                metadata=metadata or {},
                master_flow_id=master_flow_id,
                discovery_flow_id=discovery_flow_id
            )
            
            self.db.add(collection_flow)
            await self.db.commit()
            await self.db.refresh(collection_flow)
            
            logger.info(f"Initialized Collection Flow {flow_id} with tier {automation_tier}")
            return collection_flow
            
        except Exception as e:
            logger.error(f"Failed to initialize Collection Flow: {str(e)}")
            await self.db.rollback()
            raise
    
    async def transition_phase(
        self,
        flow_id: uuid.UUID,
        new_phase: CollectionPhase,
        phase_metadata: Optional[Dict[str, Any]] = None
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
                    CollectionFlow.client_account_id == uuid.UUID(self.client_account_id)
                )
            )
            collection_flow = result.scalar_one_or_none()
            
            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")
            
            # Validate phase transition
            if not self._is_valid_transition(collection_flow.current_phase, new_phase.value):
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
                phase_state["phase_history"][-1]["completed_at"] = datetime.utcnow().isoformat()
                phase_state["phase_history"][-1]["status"] = "completed"
            
            # Add new phase
            phase_state["phase_history"].append({
                "phase": new_phase.value,
                "started_at": datetime.utcnow().isoformat(),
                "status": "active",
                "metadata": phase_metadata or {}
            })
            
            # Update phase metadata
            if phase_metadata:
                if "phase_metadata" not in phase_state:
                    phase_state["phase_metadata"] = {}
                phase_state["phase_metadata"][new_phase.value] = phase_metadata
            
            # Update the collection flow
            collection_flow.current_phase = new_phase.value
            collection_flow.phase_state = phase_state
            collection_flow.status = self._map_phase_to_status(new_phase)
            collection_flow.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(collection_flow)
            
            logger.info(f"Transitioned Collection Flow {flow_id} to phase {new_phase.value}")
            return collection_flow
            
        except Exception as e:
            logger.error(f"Failed to transition phase for Collection Flow {flow_id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def update_progress(
        self,
        flow_id: uuid.UUID,
        progress_percentage: float,
        quality_score: Optional[float] = None,
        confidence_score: Optional[float] = None,
        metadata_updates: Optional[Dict[str, Any]] = None
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
                    CollectionFlow.client_account_id == uuid.UUID(self.client_account_id)
                )
            )
            collection_flow = result.scalar_one_or_none()
            
            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")
            
            # Update progress and scores
            collection_flow.progress_percentage = min(100.0, max(0.0, progress_percentage))
            
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
            
            logger.info(f"Updated progress for Collection Flow {flow_id}: {progress_percentage}%")
            return collection_flow
            
        except Exception as e:
            logger.error(f"Failed to update progress for Collection Flow {flow_id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def fail_flow(
        self,
        flow_id: uuid.UUID,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
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
                    CollectionFlow.client_account_id == uuid.UUID(self.client_account_id)
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
                phase_state["phase_history"][-1]["completed_at"] = datetime.utcnow().isoformat()
                phase_state["phase_history"][-1]["error"] = error_message
            collection_flow.phase_state = phase_state
            
            await self.db.commit()
            await self.db.refresh(collection_flow)
            
            logger.error(f"Collection Flow {flow_id} failed: {error_message}")
            return collection_flow
            
        except Exception as e:
            logger.error(f"Failed to mark Collection Flow {flow_id} as failed: {str(e)}")
            await self.db.rollback()
            raise
    
    async def complete_flow(
        self,
        flow_id: uuid.UUID,
        final_quality_score: float,
        final_confidence_score: float,
        completion_metadata: Optional[Dict[str, Any]] = None
    ) -> CollectionFlow:
        """
        Mark Collection Flow as completed.
        
        Args:
            flow_id: Flow ID
            final_quality_score: Final quality score
            final_confidence_score: Final confidence score
            completion_metadata: Optional completion metadata
            
        Returns:
            Updated CollectionFlow instance
        """
        try:
            # Get the collection flow
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id == uuid.UUID(self.client_account_id)
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
                **(completion_metadata or {})
            }
            collection_flow.metadata = metadata
            
            # Update phase state
            phase_state = collection_flow.phase_state or {}
            if "phase_history" in phase_state and phase_state["phase_history"]:
                phase_state["phase_history"][-1]["status"] = "completed"
                phase_state["phase_history"][-1]["completed_at"] = datetime.utcnow().isoformat()
            collection_flow.phase_state = phase_state
            
            await self.db.commit()
            await self.db.refresh(collection_flow)
            
            logger.info(f"Completed Collection Flow {flow_id} with quality score {final_quality_score}")
            return collection_flow
            
        except Exception as e:
            logger.error(f"Failed to complete Collection Flow {flow_id}: {str(e)}")
            await self.db.rollback()
            raise
    
    async def get_flow_by_id(
        self,
        flow_id: uuid.UUID
    ) -> Optional[CollectionFlow]:
        """
        Get Collection Flow by ID.
        
        Args:
            flow_id: Flow ID
            
        Returns:
            CollectionFlow instance or None
        """
        try:
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id == uuid.UUID(self.client_account_id)
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get Collection Flow {flow_id}: {str(e)}")
            raise
    
    async def get_flows_by_status(
        self,
        status: CollectionFlowStatus,
        limit: int = 100
    ) -> List[CollectionFlow]:
        """
        Get Collection Flows by status.
        
        Args:
            status: Flow status
            limit: Maximum number of flows to return
            
        Returns:
            List of CollectionFlow instances
        """
        try:
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.status == status,
                    CollectionFlow.client_account_id == uuid.UUID(self.client_account_id)
                ).limit(limit)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get Collection Flows by status {status}: {str(e)}")
            raise
    
    def _is_valid_transition(self, current_phase: str, new_phase: str) -> bool:
        """
        Check if phase transition is valid.
        
        Args:
            current_phase: Current phase
            new_phase: New phase
            
        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid transitions
        valid_transitions = {
            CollectionPhase.INITIALIZATION.value: [
                CollectionPhase.PLATFORM_DETECTION.value
            ],
            CollectionPhase.PLATFORM_DETECTION.value: [
                CollectionPhase.AUTOMATED_COLLECTION.value,
                CollectionPhase.MANUAL_COLLECTION.value  # Skip to manual if no automation
            ],
            CollectionPhase.AUTOMATED_COLLECTION.value: [
                CollectionPhase.GAP_ANALYSIS.value,
                CollectionPhase.FINALIZATION.value  # Skip gap analysis if complete
            ],
            CollectionPhase.GAP_ANALYSIS.value: [
                CollectionPhase.MANUAL_COLLECTION.value,
                CollectionPhase.FINALIZATION.value  # Skip manual if no gaps
            ],
            CollectionPhase.MANUAL_COLLECTION.value: [
                CollectionPhase.FINALIZATION.value
            ],
            CollectionPhase.FINALIZATION.value: []  # Terminal phase
        }
        
        return new_phase in valid_transitions.get(current_phase, [])
    
    def _map_phase_to_status(self, phase: CollectionPhase) -> CollectionFlowStatus:
        """
        Map phase to Collection Flow status.
        
        Args:
            phase: Collection phase
            
        Returns:
            Corresponding CollectionFlowStatus
        """
        phase_status_map = {
            CollectionPhase.INITIALIZATION: CollectionFlowStatus.INITIALIZED,
            CollectionPhase.PLATFORM_DETECTION: CollectionFlowStatus.PLATFORM_DETECTION,
            CollectionPhase.AUTOMATED_COLLECTION: CollectionFlowStatus.AUTOMATED_COLLECTION,
            CollectionPhase.GAP_ANALYSIS: CollectionFlowStatus.GAP_ANALYSIS,
            CollectionPhase.MANUAL_COLLECTION: CollectionFlowStatus.MANUAL_COLLECTION,
            CollectionPhase.FINALIZATION: CollectionFlowStatus.COMPLETED
        }
        
        return phase_status_map.get(phase, CollectionFlowStatus.INITIALIZED)