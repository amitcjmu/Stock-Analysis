"""
Discovery Flow Models - Phase 3: Database Integration
CrewAI Flow ID as single source of truth, eliminating session_id dependencies
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class DiscoveryFlow(Base):
    """
    Discovery Flow model with CrewAI Flow ID as single source of truth.
    Eliminates session_id in favor of flow_id for unified tracking.
    """
    __tablename__ = 'discovery_flows'

    # Primary identification - CrewAI Flow ID is the single source of truth
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    flow_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)  # CrewAI Flow ID
    
    # Master Flow Coordination (Phase 2)
    master_flow_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String, nullable=False)
    
    # Data import integration
    import_session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    data_import_id = Column(UUID(as_uuid=True), ForeignKey("data_imports.id"), nullable=True, index=True)
    
    # Flow metadata
    flow_name = Column(String(255), nullable=False)
    flow_description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    
    # Phase completion tracking - HYBRID APPROACH
    # Boolean flags (keep for backward compatibility)
    data_validation_completed = Column(Boolean, nullable=False, default=False)
    field_mapping_completed = Column(Boolean, nullable=False, default=False)  # was attribute_mapping_completed
    data_cleansing_completed = Column(Boolean, nullable=False, default=False)
    asset_inventory_completed = Column(Boolean, nullable=False, default=False)  # was inventory_completed
    dependency_analysis_completed = Column(Boolean, nullable=False, default=False)  # was dependencies_completed
    tech_debt_assessment_completed = Column(Boolean, nullable=False, default=False)  # was tech_debt_completed
    
    # JSON fields for CrewAI state management (V3 features)
    flow_type = Column(String(100), default='unified_discovery')
    current_phase = Column(String(100), nullable=True)
    phases_completed = Column(JSON, default=list)
    flow_state = Column(JSON, default=dict)
    crew_outputs = Column(JSON, default=dict)
    field_mappings = Column(JSON, nullable=True)
    discovered_assets = Column(JSON, nullable=True)
    dependencies = Column(JSON, nullable=True)
    tech_debt_analysis = Column(JSON, nullable=True)
    
    # CrewAI integration
    crewai_persistence_id = Column(UUID(as_uuid=True), nullable=True)
    crewai_state_data = Column(JSONB, nullable=False, default={})
    
    # Error handling (new fields)
    error_message = Column(Text, nullable=True)
    error_phase = Column(String(100), nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # Note: discovery_assets table was consolidated into main assets table
    # Use assets table with discovery_flow_id foreign key instead
    # Note: CrewAIFlowStateExtensions is now the master table, so no direct relationship needed
    data_import = relationship("DataImport", back_populates="discovery_flows")

    def __repr__(self):
        return f"<DiscoveryFlow(flow_id={self.flow_id}, name='{self.flow_name}', status='{self.status}')>"

    def calculate_progress(self) -> float:
        """Calculate progress percentage based on completed phases"""
        phases = [
            self.data_validation_completed,
            self.field_mapping_completed,
            self.data_cleansing_completed,
            self.asset_inventory_completed,
            self.dependency_analysis_completed,
            self.tech_debt_assessment_completed
        ]
        completed_count = sum(1 for phase in phases if phase)
        return round((completed_count / len(phases)) * 100, 1)

    def update_progress(self):
        """Update progress percentage based on phase completion"""
        self.progress_percentage = self.calculate_progress()

    def get_current_phase(self) -> str:
        """Get the current phase based on completion status"""
        # Use JSON field if available, otherwise calculate from booleans
        if self.current_phase:
            return self.current_phase
            
        phases = [
            ('data_validation', self.data_validation_completed),
            ('field_mapping', self.field_mapping_completed),
            ('data_cleansing', self.data_cleansing_completed),
            ('asset_inventory', self.asset_inventory_completed),
            ('dependency_analysis', self.dependency_analysis_completed),
            ('tech_debt_assessment', self.tech_debt_assessment_completed)
        ]
        
        # Find the last completed phase
        current_phase = "data_validation"  # Default starting phase
        for phase_name, completed in phases:
            if completed:
                current_phase = phase_name
            else:
                break
        
        return current_phase

    def get_next_phase(self) -> Optional[str]:
        """Get the next phase that needs to be completed"""
        phases = [
            ('data_validation', self.data_validation_completed),
            ('field_mapping', self.field_mapping_completed),
            ('data_cleansing', self.data_cleansing_completed),
            ('asset_inventory', self.asset_inventory_completed),
            ('dependency_analysis', self.dependency_analysis_completed),
            ('tech_debt_assessment', self.tech_debt_assessment_completed)
        ]
        
        for phase_name, completed in phases:
            if not completed:
                return phase_name
        return None

    def is_complete(self) -> bool:
        """Check if all phases are completed"""
        return all([
            self.data_validation_completed,
            self.field_mapping_completed,
            self.data_cleansing_completed,
            self.asset_inventory_completed,
            self.dependency_analysis_completed,
            self.tech_debt_assessment_completed
        ])

    def prepare_assessment_package(self) -> Dict[str, Any]:
        """Prepare data package for assessment flow handoff"""
        return {
            "flow_id": str(self.flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "discovery_summary": {
                "total_assets": 0,  # Will be calculated by repository
                "asset_types": [],  # Will be calculated by repository
                "migration_ready_count": 0,  # Will be calculated by repository
                "phases_completed": self.calculate_progress()
            },
            "assets": [],  # Will be populated by repository query
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "learning_scope": self.learning_scope,
            "memory_isolation_level": self.memory_isolation_level
        }

    def get_migration_readiness_score(self) -> float:
        """Calculate overall migration readiness score"""
        # Note: Now calculated by repository since assets are in main assets table
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        # Extract agent_insights from crewai_state_data
        agent_insights = []
        if self.crewai_state_data:
            agent_insights = self.crewai_state_data.get("agent_insights", [])
            # Also check for agent_insights in phase-specific data
            for phase_data in self.crewai_state_data.values():
                if isinstance(phase_data, dict) and "agent_insights" in phase_data:
                    phase_insights = phase_data["agent_insights"]
                    if isinstance(phase_insights, list):
                        agent_insights.extend(phase_insights)
        
        return {
            "id": str(self.id),
            "flow_id": str(self.flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "user_id": self.user_id,
            "import_session_id": str(self.import_session_id) if self.import_session_id else None,
            "data_import_id": str(self.data_import_id) if self.data_import_id else None,
            "flow_name": self.flow_name,
            "flow_description": self.flow_description,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "phases": {
                "data_import_completed": self.data_import_completed,
                "attribute_mapping_completed": self.attribute_mapping_completed,
                "data_cleansing_completed": self.data_cleansing_completed,
                "inventory_completed": self.inventory_completed,
                "dependencies_completed": self.dependencies_completed,
                "tech_debt_completed": self.tech_debt_completed
            },
            "crewai_persistence_id": str(self.crewai_persistence_id) if self.crewai_persistence_id else None,
            "learning_scope": self.learning_scope,
            "memory_isolation_level": self.memory_isolation_level,
            "assessment_ready": self.assessment_ready,
            "is_mock": self.is_mock,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "migration_readiness_score": self.get_migration_readiness_score(),
            "next_phase": self.get_next_phase(),
            "is_complete": self.is_complete(),
            "agent_insights": agent_insights  # Critical for agent-UI bridge functionality
        } 