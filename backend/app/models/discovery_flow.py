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
    
    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String, nullable=False)
    
    # Data import integration
    import_session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    data_import_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Flow metadata
    flow_name = Column(String(255), nullable=False)
    flow_description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='active', index=True)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    
    # Phase completion tracking (6 phases)
    data_import_completed = Column(Boolean, nullable=False, default=False)
    attribute_mapping_completed = Column(Boolean, nullable=False, default=False)
    data_cleansing_completed = Column(Boolean, nullable=False, default=False)
    inventory_completed = Column(Boolean, nullable=False, default=False)
    dependencies_completed = Column(Boolean, nullable=False, default=False)
    tech_debt_completed = Column(Boolean, nullable=False, default=False)
    
    # CrewAI integration
    crewai_persistence_id = Column(UUID(as_uuid=True), nullable=True)
    crewai_state_data = Column(JSONB, nullable=False, default={})
    
    # Agent learning and memory
    learning_scope = Column(String(50), nullable=False, default='engagement')
    memory_isolation_level = Column(String(20), nullable=False, default='strict')
    
    # Assessment handoff preparation
    assessment_ready = Column(Boolean, nullable=False, default=False)
    assessment_package = Column(JSONB, nullable=True)
    
    # Demo mode support
    is_mock = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    assets = relationship("DiscoveryAsset", back_populates="discovery_flow", cascade="all, delete-orphan")
    crewai_extensions = relationship("CrewAIFlowStateExtensions", back_populates="discovery_flow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DiscoveryFlow(flow_id={self.flow_id}, name='{self.flow_name}', status='{self.status}')>"

    def calculate_progress(self) -> float:
        """Calculate progress percentage based on completed phases"""
        phases = [
            self.data_import_completed,
            self.attribute_mapping_completed,
            self.data_cleansing_completed,
            self.inventory_completed,
            self.dependencies_completed,
            self.tech_debt_completed
        ]
        completed_count = sum(1 for phase in phases if phase)
        return round((completed_count / len(phases)) * 100, 1)

    def update_progress(self):
        """Update progress percentage based on phase completion"""
        self.progress_percentage = self.calculate_progress()

    def get_next_phase(self) -> Optional[str]:
        """Get the next phase that needs to be completed"""
        phases = [
            ('data_import', self.data_import_completed),
            ('attribute_mapping', self.attribute_mapping_completed),
            ('data_cleansing', self.data_cleansing_completed),
            ('inventory', self.inventory_completed),
            ('dependencies', self.dependencies_completed),
            ('tech_debt', self.tech_debt_completed)
        ]
        
        for phase_name, completed in phases:
            if not completed:
                return phase_name
        return None

    def is_complete(self) -> bool:
        """Check if all phases are completed"""
        return all([
            self.data_import_completed,
            self.attribute_mapping_completed,
            self.data_cleansing_completed,
            self.inventory_completed,
            self.dependencies_completed,
            self.tech_debt_completed
        ])

    def prepare_assessment_package(self) -> Dict[str, Any]:
        """Prepare data package for assessment flow handoff"""
        return {
            "flow_id": str(self.flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "discovery_summary": {
                "total_assets": len(self.assets),
                "asset_types": list(set(asset.asset_type for asset in self.assets if asset.asset_type)),
                "migration_ready_count": sum(1 for asset in self.assets if asset.migration_ready),
                "phases_completed": self.calculate_progress()
            },
            "assets": [asset.to_dict() for asset in self.assets],
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "learning_scope": self.learning_scope,
            "memory_isolation_level": self.memory_isolation_level
        }

    def get_migration_readiness_score(self) -> float:
        """Calculate overall migration readiness score"""
        if not self.assets:
            return 0.0
        
        ready_assets = sum(1 for asset in self.assets if asset.migration_ready)
        return round((ready_assets / len(self.assets)) * 100, 1)

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