"""
State Synchronizer for ADCS Cross-Flow Coordination

This service manages state synchronization across Collection, Discovery, and Assessment flows,
ensuring consistent state transitions and data coherence throughout the workflow.

Generated with CC for ADCS end-to-end integration.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
from app.models.discovery_flow import DiscoveryFlow
from app.monitoring.metrics import track_performance

logger = get_logger(__name__)

class SyncEventType(Enum):
    """Types of synchronization events"""
    FLOW_CREATED = "flow_created"
    FLOW_UPDATED = "flow_updated"
    FLOW_COMPLETED = "flow_completed"
    FLOW_FAILED = "flow_failed"
    ASSET_CREATED = "asset_created"
    ASSET_UPDATED = "asset_updated"
    ASSET_DELETED = "asset_deleted"
    PHASE_TRANSITION = "phase_transition"
    STATE_CONFLICT = "state_conflict"

class SyncPriority(Enum):
    """Priority levels for synchronization events"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class SyncEvent:
    """Represents a synchronization event"""
    id: UUID = field(default_factory=uuid4)
    event_type: SyncEventType = None
    priority: SyncPriority = SyncPriority.MEDIUM
    source_flow_id: UUID = None
    source_flow_type: str = None
    target_flow_ids: List[UUID] = field(default_factory=list)
    engagement_id: UUID = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    status: str = "pending"  # pending, processing, completed, failed

@dataclass
class FlowState:
    """Represents the current state of a flow"""
    flow_id: UUID
    flow_type: str
    status: str
    current_phase: str
    progress_percentage: float
    last_updated: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class SyncContext:
    """Context for synchronization operations"""
    engagement_id: UUID
    flows: Dict[str, FlowState] = field(default_factory=dict)
    assets_snapshot: Dict[UUID, Dict[str, Any]] = field(default_factory=dict)
    sync_history: List[SyncEvent] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)

class StateSynchronizer:
    """
    Manages state synchronization across ADCS workflow phases
    """
    
    def __init__(self):
        self.sync_queue: List[SyncEvent] = []
        self.processing_lock = asyncio.Lock()
        self.sync_contexts: Dict[UUID, SyncContext] = {}
        
        # Define sync rules for different flow combinations
        self.sync_rules = {
            "collection_to_discovery": {
                "triggers": ["flow_completed", "asset_created", "asset_updated"],
                "actions": ["propagate_assets", "update_confidence_scores", "trigger_enrichment"],
                "required_conditions": ["min_asset_count", "min_confidence"]
            },
            "discovery_to_assessment": {
                "triggers": ["flow_completed", "asset_updated", "phase_transition"],
                "actions": ["propagate_enriched_data", "trigger_analysis", "update_readiness"],
                "required_conditions": ["min_discovery_completion", "dependency_analysis_complete"]
            },
            "bidirectional_updates": {
                "triggers": ["asset_updated", "confidence_updated"],
                "actions": ["sync_asset_state", "update_cross_references"],
                "propagation_delay": 2  # seconds
            }
        }
        
    @track_performance("sync.state.full_sync")
    async def synchronize_engagement_state(
        self,
        engagement_id: UUID,
        force_full_sync: bool = False
    ) -> SyncContext:
        """
        Perform comprehensive state synchronization for an engagement
        """
        
        logger.info(
            "Starting engagement state synchronization",
            extra={
                "engagement_id": str(engagement_id),
                "force_full_sync": force_full_sync
            }
        )
        
        async with self.processing_lock:
            try:
                # Get or create sync context
                context = await self._get_or_create_sync_context(engagement_id)
                
                # Load current flow states
                await self._load_flow_states(context)
                
                # Load current asset states
                await self._load_asset_states(context)
                
                # Detect state conflicts
                conflicts = await self._detect_state_conflicts(context)
                context.conflicts = conflicts
                
                # Process pending sync events
                await self._process_sync_queue(context)
                
                # Apply synchronization rules
                await self._apply_sync_rules(context)
                
                # Resolve conflicts if any
                if conflicts:
                    await self._resolve_state_conflicts(context)
                    
                # Update context timestamp
                context.sync_history.append(SyncEvent(
                    event_type=SyncEventType.PHASE_TRANSITION,
                    priority=SyncPriority.MEDIUM,
                    engagement_id=engagement_id,
                    data={"sync_type": "full_engagement_sync"},
                    status="completed",
                    processed_at=datetime.utcnow()
                ))
                
                logger.info(
                    "Engagement state synchronization completed",
                    extra={
                        "engagement_id": str(engagement_id),
                        "conflicts_found": len(conflicts),
                        "flows_synced": len(context.flows)
                    }
                )
                
                return context
                
            except Exception as e:
                logger.error(
                    "Error during engagement state synchronization",
                    extra={
                        "engagement_id": str(engagement_id),
                        "error": str(e)
                    }
                )
                raise
                
    async def _get_or_create_sync_context(self, engagement_id: UUID) -> SyncContext:
        """Get or create synchronization context for engagement"""
        
        if engagement_id not in self.sync_contexts:
            self.sync_contexts[engagement_id] = SyncContext(engagement_id=engagement_id)
            
        return self.sync_contexts[engagement_id]
        
    async def _load_flow_states(self, context: SyncContext) -> None:
        """Load current states of all flows for the engagement"""
        
        async with AsyncSessionLocal() as session:
            # Load collection flow
            collection_result = await session.execute(
                select(CollectionFlow).where(CollectionFlow.engagement_id == context.engagement_id)
            )
            collection_flow = collection_result.scalar_one_or_none()
            
            if collection_flow:
                context.flows["collection"] = FlowState(
                    flow_id=collection_flow.id,
                    flow_type="collection",
                    status=collection_flow.status,
                    current_phase=collection_flow.current_phase or "pending",
                    progress_percentage=collection_flow.progress_percentage or 0.0,
                    last_updated=collection_flow.updated_at or collection_flow.created_at,
                    metadata=collection_flow.metadata or {}
                )
                
            # Load discovery flow
            discovery_result = await session.execute(
                select(DiscoveryFlow).where(DiscoveryFlow.engagement_id == context.engagement_id)
            )
            discovery_flow = discovery_result.scalar_one_or_none()
            
            if discovery_flow:
                context.flows["discovery"] = FlowState(
                    flow_id=discovery_flow.id,
                    flow_type="discovery",
                    status=discovery_flow.status,
                    current_phase=discovery_flow.current_phase or "pending",
                    progress_percentage=discovery_flow.progress_percentage or 0.0,
                    last_updated=discovery_flow.updated_at or discovery_flow.created_at,
                    metadata=discovery_flow.metadata or {}
                )
                
            # Load assessment flow
            assessment_result = await session.execute(
                select(AssessmentFlow).where(AssessmentFlow.engagement_id == context.engagement_id)
            )
            assessment_flow = assessment_result.scalar_one_or_none()
            
            if assessment_flow:
                context.flows["assessment"] = FlowState(
                    flow_id=assessment_flow.id,
                    flow_type="assessment",
                    status=assessment_flow.status,
                    current_phase=assessment_flow.current_phase or "pending",
                    progress_percentage=assessment_flow.progress_percentage or 0.0,
                    last_updated=assessment_flow.updated_at or assessment_flow.created_at,
                    metadata=assessment_flow.metadata or {}
                )
                
    async def _load_asset_states(self, context: SyncContext) -> None:
        """Load current asset states for the engagement"""
        
        async with AsyncSessionLocal() as session:
            assets_result = await session.execute(
                select(Asset)
                .where(Asset.engagement_id == context.engagement_id)
                .options(selectinload(Asset.dependencies))
            )
            assets = assets_result.scalars().all()
            
            for asset in assets:
                context.assets_snapshot[asset.id] = {
                    "name": asset.name,
                    "type": asset.type,
                    "status": asset.status,
                    "confidence_score": asset.confidence_score,
                    "business_criticality": asset.business_criticality,
                    "sixr_recommendation": asset.sixr_recommendation,
                    "technical_fit_score": asset.technical_fit_score,
                    "last_updated": asset.updated_at.isoformat() if asset.updated_at else None,
                    "dependency_count": len(asset.dependencies) if asset.dependencies else 0,
                    "metadata": asset.metadata or {}
                }
                
    async def _detect_state_conflicts(self, context: SyncContext) -> List[Dict[str, Any]]:
        """Detect state conflicts between flows"""
        
        conflicts = []
        
        # Check for flow status conflicts
        flow_statuses = {flow_type: flow.status for flow_type, flow in context.flows.items()}
        
        # Collection completed but discovery not started
        if (flow_statuses.get("collection") == "completed" and 
            "discovery" not in context.flows and 
            len(context.assets_snapshot) > 0):
            conflicts.append({
                "type": "missing_discovery_flow",
                "severity": "medium",
                "description": "Collection completed but discovery flow not initiated",
                "affected_flows": ["collection"],
                "recommended_action": "initiate_discovery_flow"
            })
            
        # Discovery completed but assessment not started
        if (flow_statuses.get("discovery") == "completed" and 
            "assessment" not in context.flows):
            conflicts.append({
                "type": "missing_assessment_flow",
                "severity": "medium", 
                "description": "Discovery completed but assessment flow not initiated",
                "affected_flows": ["discovery"],
                "recommended_action": "initiate_assessment_flow"
            })
            
        # Asset count mismatches
        collection_asset_count = context.flows.get("collection", {}).metadata.get("asset_count", 0)
        discovery_asset_count = context.flows.get("discovery", {}).metadata.get("asset_count", 0)
        actual_asset_count = len(context.assets_snapshot)
        
        if abs(collection_asset_count - actual_asset_count) > 2:
            conflicts.append({
                "type": "asset_count_mismatch",
                "severity": "high",
                "description": f"Collection reports {collection_asset_count} assets but {actual_asset_count} found",
                "affected_flows": ["collection"],
                "recommended_action": "sync_asset_counts"
            })
            
        # Progress percentage conflicts
        for flow_type, flow in context.flows.items():
            if flow.status == "completed" and flow.progress_percentage < 100.0:
                conflicts.append({
                    "type": "progress_status_mismatch",
                    "severity": "low",
                    "description": f"{flow_type} flow marked completed but progress is {flow.progress_percentage}%",
                    "affected_flows": [flow_type],
                    "recommended_action": "update_progress_percentage"
                })
                
        return conflicts
        
    async def _process_sync_queue(self, context: SyncContext) -> None:
        """Process pending synchronization events"""
        
        # Filter events for this engagement
        engagement_events = [
            event for event in self.sync_queue 
            if event.engagement_id == context.engagement_id and event.status == "pending"
        ]
        
        # Sort by priority and timestamp
        engagement_events.sort(key=lambda e: (e.priority.value, e.created_at))
        
        for event in engagement_events:
            try:
                await self._process_sync_event(context, event)
                event.status = "completed"
                event.processed_at = datetime.utcnow()
                
            except Exception as e:
                event.status = "failed"
                event.metadata["error"] = str(e)
                logger.error(
                    f"Failed to process sync event {event.id}",
                    extra={"engagement_id": str(context.engagement_id), "error": str(e)}
                )
                
        # Add processed events to context history
        context.sync_history.extend(engagement_events)
        
        # Remove processed events from queue
        self.sync_queue = [e for e in self.sync_queue if e not in engagement_events]
        
    async def _process_sync_event(self, context: SyncContext, event: SyncEvent) -> None:
        """Process a single synchronization event"""
        
        if event.event_type == SyncEventType.FLOW_COMPLETED:
            await self._handle_flow_completion(context, event)
            
        elif event.event_type == SyncEventType.ASSET_UPDATED:
            await self._handle_asset_update(context, event)
            
        elif event.event_type == SyncEventType.PHASE_TRANSITION:
            await self._handle_phase_transition(context, event)
            
    async def _handle_flow_completion(self, context: SyncContext, event: SyncEvent) -> None:
        """Handle flow completion events"""
        
        source_flow_type = event.source_flow_type
        
        if source_flow_type == "collection":
            # Collection completed - prepare for discovery
            await self._trigger_discovery_readiness_check(context)
            
        elif source_flow_type == "discovery":
            # Discovery completed - prepare for assessment
            await self._trigger_assessment_readiness_check(context)
            
    async def _handle_asset_update(self, context: SyncContext, event: SyncEvent) -> None:
        """Handle asset update events"""
        
        asset_id = event.data.get("asset_id")
        if asset_id:
            # Update asset snapshot
            async with AsyncSessionLocal() as session:
                asset_result = await session.execute(
                    select(Asset).where(Asset.id == UUID(asset_id))
                )
                asset = asset_result.scalar_one_or_none()
                
                if asset:
                    context.assets_snapshot[asset.id] = {
                        "name": asset.name,
                        "confidence_score": asset.confidence_score,
                        "last_updated": datetime.utcnow().isoformat(),
                        "metadata": asset.metadata or {}
                    }
                    
    async def _handle_phase_transition(self, context: SyncContext, event: SyncEvent) -> None:
        """Handle phase transition events"""
        
        # Update flow state in context
        flow_type = event.source_flow_type
        new_phase = event.data.get("new_phase")
        
        if flow_type in context.flows and new_phase:
            context.flows[flow_type].current_phase = new_phase
            context.flows[flow_type].last_updated = datetime.utcnow()
            
    async def _apply_sync_rules(self, context: SyncContext) -> None:
        """Apply synchronization rules based on current state"""
        
        # Collection to Discovery sync rules
        if ("collection" in context.flows and 
            context.flows["collection"].status == "completed" and
            "discovery" not in context.flows):
            await self._apply_collection_to_discovery_rules(context)
            
        # Discovery to Assessment sync rules  
        if ("discovery" in context.flows and
            context.flows["discovery"].status == "completed" and
            "assessment" not in context.flows):
            await self._apply_discovery_to_assessment_rules(context)
            
        # Bidirectional update rules
        await self._apply_bidirectional_sync_rules(context)
        
    async def _apply_collection_to_discovery_rules(self, context: SyncContext) -> None:
        """Apply collection to discovery synchronization rules"""
        
        collection_flow = context.flows["collection"]
        asset_count = len(context.assets_snapshot)
        
        # Check readiness conditions
        min_asset_count = self.sync_rules["collection_to_discovery"]["required_conditions"]
        
        if asset_count >= 1:  # At least 1 asset required
            # Create discovery flow initialization event
            init_event = SyncEvent(
                event_type=SyncEventType.FLOW_CREATED,
                priority=SyncPriority.HIGH,
                source_flow_id=collection_flow.flow_id,
                source_flow_type="collection",
                engagement_id=context.engagement_id,
                data={"target_flow_type": "discovery", "auto_initiated": True}
            )
            self.sync_queue.append(init_event)
            
    async def _apply_discovery_to_assessment_rules(self, context: SyncContext) -> None:
        """Apply discovery to assessment synchronization rules"""
        
        discovery_flow = context.flows["discovery"]
        
        # Check readiness conditions
        if discovery_flow.progress_percentage >= 80.0:  # At least 80% complete
            # Create assessment flow initialization event
            init_event = SyncEvent(
                event_type=SyncEventType.FLOW_CREATED,
                priority=SyncPriority.HIGH,
                source_flow_id=discovery_flow.flow_id,
                source_flow_type="discovery",
                engagement_id=context.engagement_id,
                data={"target_flow_type": "assessment", "auto_initiated": True}
            )
            self.sync_queue.append(init_event)
            
    async def _apply_bidirectional_sync_rules(self, context: SyncContext) -> None:
        """Apply bidirectional synchronization rules"""
        
        # Sync asset confidence scores across flows
        for asset_id, asset_data in context.assets_snapshot.items():
            confidence = asset_data.get("confidence_score", 0.0)
            
            # Update flow metadata with confidence metrics
            for flow_type, flow in context.flows.items():
                if "average_confidence" not in flow.metadata:
                    flow.metadata["average_confidence"] = confidence
                else:
                    # Update running average
                    current_avg = flow.metadata["average_confidence"]
                    flow.metadata["average_confidence"] = (current_avg + confidence) / 2
                    
    async def _resolve_state_conflicts(self, context: SyncContext) -> None:
        """Resolve detected state conflicts"""
        
        for conflict in context.conflicts:
            action = conflict.get("recommended_action")
            
            if action == "sync_asset_counts":
                await self._sync_asset_counts(context, conflict)
                
            elif action == "update_progress_percentage":
                await self._fix_progress_percentages(context, conflict)
                
            elif action == "initiate_discovery_flow":
                await self._auto_initiate_flow(context, "discovery")
                
            elif action == "initiate_assessment_flow":
                await self._auto_initiate_flow(context, "assessment")
                
    async def _sync_asset_counts(self, context: SyncContext, conflict: Dict[str, Any]) -> None:
        """Synchronize asset counts across flows"""
        
        actual_count = len(context.assets_snapshot)
        
        async with AsyncSessionLocal() as session:
            # Update collection flow metadata
            if "collection" in context.flows:
                collection_id = context.flows["collection"].flow_id
                await session.execute(
                    update(CollectionFlow)
                    .where(CollectionFlow.id == collection_id)
                    .values(metadata={"asset_count": actual_count})
                )
                
            await session.commit()
            
    async def _fix_progress_percentages(self, context: SyncContext, conflict: Dict[str, Any]) -> None:
        """Fix progress percentage mismatches"""
        
        affected_flows = conflict.get("affected_flows", [])
        
        async with AsyncSessionLocal() as session:
            for flow_type in affected_flows:
                if flow_type in context.flows:
                    flow = context.flows[flow_type]
                    if flow.status == "completed":
                        # Update progress to 100%
                        if flow_type == "collection":
                            await session.execute(
                                update(CollectionFlow)
                                .where(CollectionFlow.id == flow.flow_id)
                                .values(progress_percentage=100.0)
                            )
                        elif flow_type == "discovery":
                            await session.execute(
                                update(DiscoveryFlow)
                                .where(DiscoveryFlow.id == flow.flow_id)
                                .values(progress_percentage=100.0)
                            )
                        elif flow_type == "assessment":
                            await session.execute(
                                update(AssessmentFlow)
                                .where(AssessmentFlow.id == flow.flow_id)
                                .values(progress_percentage=100.0)
                            )
                            
            await session.commit()
            
    async def _auto_initiate_flow(self, context: SyncContext, flow_type: str) -> None:
        """Auto-initiate missing flows"""
        
        # This would integrate with the appropriate flow creation services
        logger.info(
            f"Auto-initiating {flow_type} flow",
            extra={"engagement_id": str(context.engagement_id)}
        )
        
    async def _trigger_discovery_readiness_check(self, context: SyncContext) -> None:
        """Trigger discovery readiness check"""
        
        # Check if discovery should be auto-initiated
        asset_count = len(context.assets_snapshot)
        if asset_count >= 1:
            await self._auto_initiate_flow(context, "discovery")
            
    async def _trigger_assessment_readiness_check(self, context: SyncContext) -> None:
        """Trigger assessment readiness check"""
        
        # Check if assessment should be auto-initiated
        discovery_flow = context.flows.get("discovery")
        if discovery_flow and discovery_flow.progress_percentage >= 80.0:
            await self._auto_initiate_flow(context, "assessment")
            
    @track_performance("sync.event.add")
    async def add_sync_event(
        self,
        event_type: SyncEventType,
        engagement_id: UUID,
        source_flow_id: UUID = None,
        source_flow_type: str = None,
        data: Dict[str, Any] = None,
        priority: SyncPriority = SyncPriority.MEDIUM
    ) -> UUID:
        """Add a synchronization event to the queue"""
        
        event = SyncEvent(
            event_type=event_type,
            priority=priority,
            source_flow_id=source_flow_id,
            source_flow_type=source_flow_type,
            engagement_id=engagement_id,
            data=data or {},
            status="pending"
        )
        
        self.sync_queue.append(event)
        
        logger.debug(
            "Added sync event to queue",
            extra={
                "event_id": str(event.id),
                "event_type": event_type.value,
                "engagement_id": str(engagement_id)
            }
        )
        
        return event.id
        
    @track_performance("sync.status.get")
    async def get_sync_status(self, engagement_id: UUID) -> Dict[str, Any]:
        """Get synchronization status for an engagement"""
        
        context = self.sync_contexts.get(engagement_id)
        
        if not context:
            return {
                "engagement_id": str(engagement_id),
                "sync_status": "not_initialized",
                "flows": {},
                "conflicts": [],
                "pending_events": 0
            }
            
        pending_events = len([
            e for e in self.sync_queue 
            if e.engagement_id == engagement_id and e.status == "pending"
        ])
        
        return {
            "engagement_id": str(engagement_id),
            "sync_status": "synchronized" if not context.conflicts else "conflicts_detected",
            "flows": {
                flow_type: {
                    "status": flow.status,
                    "current_phase": flow.current_phase,
                    "progress": flow.progress_percentage,
                    "last_updated": flow.last_updated.isoformat()
                }
                for flow_type, flow in context.flows.items()
            },
            "conflicts": context.conflicts,
            "pending_events": pending_events,
            "asset_count": len(context.assets_snapshot),
            "last_sync": max(
                [event.processed_at for event in context.sync_history if event.processed_at],
                default=datetime.utcnow()
            ).isoformat()
        }