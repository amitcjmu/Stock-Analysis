"""
Comprehensive Asset Inventory Model for Migration Assessment
Replaces persistence layer with proper database-backed asset management
"""

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class AssetInventory(Base):
    """
    Comprehensive asset inventory model for migration assessment.
    Stores all discovered attributes and workflow progress.
    """
    __tablename__ = "asset_inventory"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Multi-tenant support
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Core Asset Information
    asset_name = Column(String(255), nullable=True, index=True)
    hostname = Column(String(255), nullable=True, index=True)
    asset_type = Column(String(100), nullable=True, index=True)  # Application, Server, Database, etc.
    
    # Infrastructure Details
    ip_address = Column(String(45), nullable=True)
    operating_system = Column(String(255), nullable=True)
    os_version = Column(String(100), nullable=True)
    hardware_type = Column(String(100), nullable=True)
    
    # Migration Critical Attributes (20+ fields)
    environment = Column(String(50), nullable=True, index=True)  # Production, Development, Test
    business_owner = Column(String(255), nullable=True)
    technical_owner = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True, index=True)
    business_criticality = Column(String(50), nullable=True, index=True)  # Critical, High, Medium, Low
    
    # Application Specific
    application_id = Column(String(255), nullable=True, index=True)
    application_version = Column(String(100), nullable=True)
    programming_language = Column(String(100), nullable=True)
    framework = Column(String(100), nullable=True)
    database_type = Column(String(100), nullable=True)
    
    # Cloud Readiness Assessment
    cloud_readiness_score = Column(Float, nullable=True)
    modernization_complexity = Column(String(50), nullable=True)  # Low, Medium, High, Complex
    tech_debt_score = Column(Float, nullable=True)
    compliance_requirements = Column(Text, nullable=True)
    
    # Dependencies
    server_dependencies = Column(JSON, nullable=True)  # List of dependent servers
    application_dependencies = Column(JSON, nullable=True)  # List of dependent applications
    database_dependencies = Column(JSON, nullable=True)  # List of dependent databases
    network_dependencies = Column(JSON, nullable=True)  # Network requirements
    
    # Financial Information
    estimated_monthly_cost = Column(Float, nullable=True)
    license_cost = Column(Float, nullable=True)
    support_cost = Column(Float, nullable=True)
    
    # Security & Compliance
    security_classification = Column(String(50), nullable=True)
    compliance_frameworks = Column(JSON, nullable=True)  # List of compliance requirements
    vulnerability_score = Column(Float, nullable=True)
    
    # Migration Planning
    migration_priority = Column(String(50), nullable=True)  # High, Medium, Low
    migration_complexity = Column(String(50), nullable=True)  # Simple, Medium, Complex
    estimated_migration_effort = Column(String(100), nullable=True)  # Person-days
    migration_wave = Column(Integer, nullable=True)
    
    # 6R Strategy Assessment
    recommended_6r_strategy = Column(String(50), nullable=True)  # Rehost, Replatform, etc.
    strategy_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    strategy_rationale = Column(Text, nullable=True)
    
    # Workflow Status Tracking
    discovery_status = Column(String(50), default='discovered', index=True)  # discovered, mapped, cleaned, validated
    mapping_status = Column(String(50), default='pending', index=True)  # pending, in_progress, completed, failed
    cleanup_status = Column(String(50), default='pending', index=True)  # pending, in_progress, completed, failed
    assessment_readiness = Column(String(50), default='not_ready', index=True)  # not_ready, partial, ready
    
    # Data Quality Metrics
    completeness_score = Column(Float, nullable=True)  # Percentage of required fields filled
    quality_score = Column(Float, nullable=True)  # Overall data quality score
    missing_critical_fields = Column(JSON, nullable=True)  # List of missing required fields
    data_quality_issues = Column(JSON, nullable=True)  # List of identified issues
    
    # Agentic Analysis Results
    ai_analysis_result = Column(JSON, nullable=True)  # AI agent analysis results
    ai_recommendations = Column(JSON, nullable=True)  # AI recommendations for improvement
    ai_confidence_score = Column(Float, nullable=True)  # AI confidence in analysis
    last_ai_analysis = Column(DateTime, nullable=True)  # When AI last analyzed this asset
    
    # Audit Trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Source Information
    source_system = Column(String(100), nullable=True)  # CMDB, Discovery Tool, Manual
    source_file = Column(String(255), nullable=True)  # Original import file
    import_batch_id = Column(String(255), nullable=True, index=True)  # Batch import tracking
    
    # Custom Attributes (Organization-specific)
    custom_attributes = Column(JSON, nullable=True)  # Flexible custom field storage
    
    # Relationships
    client_account = relationship("ClientAccount", back_populates="assets")
    engagement = relationship("Engagement", back_populates="assets")

class AssetDependency(Base):
    """
    Asset dependency mapping for application-to-server relationships
    """
    __tablename__ = "asset_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source and target assets
    source_asset_id = Column(UUID(as_uuid=True), ForeignKey('asset_inventory.id'), nullable=False)
    target_asset_id = Column(UUID(as_uuid=True), ForeignKey('asset_inventory.id'), nullable=False)
    
    # Dependency details
    dependency_type = Column(String(100), nullable=False)  # database, service, network, etc.
    dependency_strength = Column(String(50), nullable=True)  # Critical, Important, Optional
    port_number = Column(Integer, nullable=True)
    protocol = Column(String(50), nullable=True)
    
    # Multi-tenant support
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    source_asset = relationship("AssetInventory", foreign_keys=[source_asset_id])
    target_asset = relationship("AssetInventory", foreign_keys=[target_asset_id])

class WorkflowProgress(Base):
    """
    Track workflow progress for assets through migration phases
    """
    __tablename__ = "workflow_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('asset_inventory.id'), nullable=False)
    
    # Workflow phases
    phase = Column(String(50), nullable=False)  # discovery, mapping, cleanup, assessment
    status = Column(String(50), nullable=False)  # pending, in_progress, completed, failed
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    
    # Details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    errors = Column(JSON, nullable=True)  # Any errors encountered
    
    # Multi-tenant support
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    asset = relationship("AssetInventory", back_populates="workflow_progress")

# Add workflow_progress relationship to AssetInventory
AssetInventory.workflow_progress = relationship("WorkflowProgress", back_populates="asset") 