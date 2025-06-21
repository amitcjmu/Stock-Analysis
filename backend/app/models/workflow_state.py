"""
Enhanced Database model for persisting unified discovery flow state.
Supports the new UnifiedDiscoveryFlowState with proper multi-tenancy.
"""
import uuid
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from typing import List

class WorkflowState(Base):
    """
    Enhanced model for persisting unified discovery flow state.
    Supports comprehensive state tracking with multi-tenant isolation.
    """
    __tablename__ = 'workflow_states'

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Flow identification (unified approach)
    flow_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    session_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    engagement_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    user_id = Column(String, nullable=False)

    # Workflow metadata
    workflow_type = Column(String, default="unified_discovery", nullable=False, index=True)
    current_phase = Column(String, nullable=False, index=True)
    status = Column(String, default="running", nullable=False, index=True)  # running, completed, failed, paused
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # Phase completion tracking
    phase_completion = Column(JSON, nullable=False, default={})
    crew_status = Column(JSON, nullable=False, default={})
    
    # Comprehensive state data
    state_data = Column(JSON, nullable=False)
    
    # Results storage
    field_mappings = Column(JSON, nullable=True)
    cleaned_data = Column(JSON, nullable=True)
    asset_inventory = Column(JSON, nullable=True)
    dependencies = Column(JSON, nullable=True)
    technical_debt = Column(JSON, nullable=True)
    
    # Quality and metrics
    data_quality_metrics = Column(JSON, nullable=True)
    agent_insights = Column(JSON, nullable=True)
    success_criteria = Column(JSON, nullable=True)
    
    # Error tracking
    errors = Column(JSON, nullable=False, default=[])
    warnings = Column(JSON, nullable=False, default=[])
    workflow_log = Column(JSON, nullable=False, default=[])
    
    # Final results
    discovery_summary = Column(JSON, nullable=True)
    assessment_flow_package = Column(JSON, nullable=True)
    
    # Database integration tracking
    database_assets_created = Column(JSON, nullable=False, default=[])
    database_integration_status = Column(String, default="pending", nullable=False)
    
    # Enterprise features
    learning_scope = Column(String, default="engagement", nullable=False)
    memory_isolation_level = Column(String, default="strict", nullable=False)
    shared_memory_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<WorkflowState(id={self.id}, flow_id={self.flow_id}, session_id={self.session_id}, status='{self.status}', phase='{self.current_phase}')>"

class UnifiedFlowStateRepository:
    """
    Repository for managing unified discovery flow state persistence.
    Provides proper multi-tenant data access patterns.
    """
    
    def __init__(self, db_session, client_account_id: str, engagement_id: str):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
    
    async def create_flow_state(self, flow_state) -> WorkflowState:
        """Create a new workflow state record"""
        db_state = WorkflowState(
            flow_id=flow_state.flow_id,
            session_id=flow_state.session_id,
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            user_id=flow_state.user_id,
            workflow_type="unified_discovery",
            current_phase=flow_state.current_phase,
            status=flow_state.status,
            progress_percentage=flow_state.progress_percentage,
            phase_completion=flow_state.phase_completion,
            crew_status=flow_state.crew_status,
            state_data=flow_state.dict(),
            field_mappings=flow_state.field_mappings,
            cleaned_data=flow_state.cleaned_data,
            asset_inventory=flow_state.asset_inventory,
            dependencies=flow_state.dependencies,
            technical_debt=flow_state.technical_debt,
            data_quality_metrics=flow_state.data_quality_metrics,
            agent_insights=flow_state.agent_insights,
            success_criteria=flow_state.success_criteria,
            errors=flow_state.errors,
            warnings=flow_state.warnings,
            workflow_log=flow_state.workflow_log,
            discovery_summary=flow_state.discovery_summary,
            assessment_flow_package=flow_state.assessment_flow_package,
            database_assets_created=flow_state.database_assets_created,
            database_integration_status=flow_state.database_integration_status,
            learning_scope=flow_state.learning_scope,
            memory_isolation_level=flow_state.memory_isolation_level,
            shared_memory_id=flow_state.shared_memory_id,
            started_at=flow_state.started_at
        )
        
        self.db.add(db_state)
        await self.db.commit()
        await self.db.refresh(db_state)
        
        return db_state
    
    async def update_flow_state(self, session_id: str, flow_state) -> WorkflowState:
        """Update an existing workflow state record"""
        from sqlalchemy import select, update
        
        # Build update values
        update_values = {
            WorkflowState.current_phase: flow_state.current_phase,
            WorkflowState.status: flow_state.status,
            WorkflowState.progress_percentage: flow_state.progress_percentage,
            WorkflowState.phase_completion: flow_state.phase_completion,
            WorkflowState.crew_status: flow_state.crew_status,
            WorkflowState.state_data: flow_state.dict(),
            WorkflowState.field_mappings: flow_state.field_mappings,
            WorkflowState.cleaned_data: flow_state.cleaned_data,
            WorkflowState.asset_inventory: flow_state.asset_inventory,
            WorkflowState.dependencies: flow_state.dependencies,
            WorkflowState.technical_debt: flow_state.technical_debt,
            WorkflowState.data_quality_metrics: flow_state.data_quality_metrics,
            WorkflowState.agent_insights: flow_state.agent_insights,
            WorkflowState.success_criteria: flow_state.success_criteria,
            WorkflowState.errors: flow_state.errors,
            WorkflowState.warnings: flow_state.warnings,
            WorkflowState.workflow_log: flow_state.workflow_log,
            WorkflowState.discovery_summary: flow_state.discovery_summary,
            WorkflowState.assessment_flow_package: flow_state.assessment_flow_package,
            WorkflowState.database_assets_created: flow_state.database_assets_created,
            WorkflowState.database_integration_status: flow_state.database_integration_status,
            WorkflowState.completed_at: flow_state.completed_at
        }
        
        # Execute update with multi-tenant filtering
        stmt = update(WorkflowState).where(
            WorkflowState.session_id == session_id,
            WorkflowState.client_account_id == self.client_account_id,
            WorkflowState.engagement_id == self.engagement_id
        ).values(**update_values)
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated record
        result = await self.db.execute(
            select(WorkflowState).where(
                WorkflowState.session_id == session_id,
                WorkflowState.client_account_id == self.client_account_id,
                WorkflowState.engagement_id == self.engagement_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_flow_state(self, session_id: str) -> WorkflowState:
        """Get workflow state by session ID with multi-tenant filtering"""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(WorkflowState).where(
                WorkflowState.session_id == session_id,
                WorkflowState.client_account_id == self.client_account_id,
                WorkflowState.engagement_id == self.engagement_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_flows(self) -> List[WorkflowState]:
        """Get all active flows for the current client/engagement"""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(WorkflowState).where(
                WorkflowState.client_account_id == self.client_account_id,
                WorkflowState.engagement_id == self.engagement_id,
                WorkflowState.status.in_(["running", "paused"])
            ).order_by(WorkflowState.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_completed_flows(self, limit: int = 10) -> List[WorkflowState]:
        """Get recently completed flows for the current client/engagement"""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(WorkflowState).where(
                WorkflowState.client_account_id == self.client_account_id,
                WorkflowState.engagement_id == self.engagement_id,
                WorkflowState.status.in_(["completed", "failed"])
            ).order_by(WorkflowState.completed_at.desc()).limit(limit)
        )
        return result.scalars().all()
    
    async def delete_flow_state(self, session_id: str) -> bool:
        """Delete a workflow state record with multi-tenant filtering"""
        from sqlalchemy import delete
        
        stmt = delete(WorkflowState).where(
            WorkflowState.session_id == session_id,
            WorkflowState.client_account_id == self.client_account_id,
            WorkflowState.engagement_id == self.engagement_id
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0 