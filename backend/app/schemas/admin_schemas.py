"""
Admin Management Schemas
Pydantic schemas for client and engagement management with business context.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo
from enum import Enum

# =========================
# Enums for Business Context
# =========================

class MigrationScopeEnum(str, Enum):
    """Migration scope options."""
    FULL_DATACENTER = "full_datacenter"
    APPLICATION_PORTFOLIO = "application_portfolio"
    INFRASTRUCTURE_ONLY = "infrastructure_only"
    SELECTED_APPLICATIONS = "selected_applications"
    PILOT_MIGRATION = "pilot_migration"
    HYBRID_CLOUD = "hybrid_cloud"

class CloudProviderEnum(str, Enum):
    """Target cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    MULTI_CLOUD = "multi_cloud"
    PRIVATE_CLOUD = "private_cloud"
    HYBRID = "hybrid"

class MigrationPhaseEnum(str, Enum):
    """Migration phase status."""
    PLANNING = "planning"
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    MIGRATION = "migration"
    OPTIMIZATION = "optimization"
    COMPLETED = "completed"

class BusinessPriorityEnum(str, Enum):
    """Business priority levels."""
    COST_REDUCTION = "cost_reduction"
    AGILITY_SPEED = "agility_speed"
    SECURITY_COMPLIANCE = "security_compliance"
    INNOVATION = "innovation"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"

# =========================
# Client Management Schemas
# =========================

class ClientAccountCreate(BaseModel):
    """Schema for creating a new client account."""
    account_name: str = Field(..., min_length=2, max_length=255)
    industry: str = Field(..., min_length=2, max_length=100)
    company_size: str = Field(..., min_length=2, max_length=50)
    headquarters_location: str = Field(..., min_length=2, max_length=255)
    primary_contact_name: str = Field(..., min_length=2, max_length=100)
    primary_contact_email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    primary_contact_phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)\.]{7,20}$')
    
    # Missing database fields
    description: Optional[str] = Field(None, max_length=1000, description="Client account description")
    subscription_tier: Optional[str] = Field(None, max_length=50, description="Subscription tier (e.g., Basic, Pro, Enterprise)")
    billing_contact_email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Client-specific platform settings")
    branding: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Client branding and UI customization")
    
    # Business Context Fields - Made optional to match frontend
    business_objectives: List[str] = Field(default_factory=list, description="Primary business objectives for migration")
    it_guidelines: Dict[str, Any] = Field(default_factory=dict, description="IT policies and guidelines")
    decision_criteria: Dict[str, Any] = Field(default_factory=dict, description="Decision-making criteria and priorities")
    agent_preferences: Dict[str, Any] = Field(default_factory=dict, description="Preferred agent configurations and settings")
    
    # Migration Context - Made optional to match frontend
    target_cloud_providers: List[str] = Field(default_factory=list, description="Target cloud provider preferences")
    business_priorities: List[str] = Field(default_factory=list, description="Business priority areas")
    compliance_requirements: List[str] = Field(default_factory=list)
    budget_constraints: Optional[Dict[str, Any]] = None
    timeline_constraints: Optional[Dict[str, Any]] = None
    
    @field_validator('account_name')
    @classmethod
    def validate_account_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError('Account name must be at least 2 characters')
        return v.strip()

class ClientAccountUpdate(BaseModel):
    """Schema for updating client account."""
    account_name: Optional[str] = Field(None, min_length=2, max_length=255)
    industry: Optional[str] = Field(None, min_length=2, max_length=100)
    company_size: Optional[str] = Field(None, min_length=2, max_length=50)
    headquarters_location: Optional[str] = Field(None, min_length=2, max_length=255)
    primary_contact_name: Optional[str] = Field(None, min_length=2, max_length=100)
    primary_contact_email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    primary_contact_phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)\.]{7,20}$')
    
    # Missing database fields for updates
    description: Optional[str] = Field(None, max_length=1000)
    subscription_tier: Optional[str] = Field(None, max_length=50)
    billing_contact_email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    settings: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None
    
    # Business Context Updates
    business_objectives: Optional[List[str]] = None
    it_guidelines: Optional[Dict[str, Any]] = None
    decision_criteria: Optional[Dict[str, Any]] = None
    agent_preferences: Optional[Dict[str, Any]] = None
    
    # Migration Context Updates - Accept strings to match frontend
    target_cloud_providers: Optional[List[str]] = None  # Changed from CloudProviderEnum to str
    business_priorities: Optional[List[str]] = None  # Changed from BusinessPriorityEnum to str
    compliance_requirements: Optional[List[str]] = None
    budget_constraints: Optional[Dict[str, Any]] = None
    timeline_constraints: Optional[Dict[str, Any]] = None

class ClientAccountResponse(BaseModel):
    """Schema for client account response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    account_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None
    headquarters_location: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    
    # Missing database fields in response
    description: Optional[str] = None
    subscription_tier: Optional[str] = None
    billing_contact_email: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None
    slug: Optional[str] = None
    created_by: Optional[str] = None
    
    # Business Context
    business_objectives: List[str] = Field(default_factory=list)
    it_guidelines: Dict[str, Any] = Field(default_factory=dict)
    decision_criteria: Dict[str, Any] = Field(default_factory=dict)
    agent_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Migration Context
    target_cloud_providers: List[str] = Field(default_factory=list)
    business_priorities: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    budget_constraints: Optional[Dict[str, Any]] = None
    timeline_constraints: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    total_engagements: int = 0
    active_engagements: int = 0
    engagement_count: int = 0  # Added missing field

# =========================
# Engagement Management Schemas
# =========================

class EngagementCreate(BaseModel):
    """Schema for creating a new engagement."""
    engagement_name: str = Field(..., min_length=2, max_length=255)
    client_account_id: str
    engagement_description: str = Field(..., min_length=10, max_length=1000)
    migration_scope: MigrationScopeEnum
    target_cloud_provider: CloudProviderEnum
    
    # Migration Planning
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    estimated_budget: Optional[float] = Field(None, ge=0)
    estimated_asset_count: Optional[int] = Field(None, ge=0)
    
    # Team and Process
    engagement_manager: str = Field(..., min_length=2, max_length=100)
    technical_lead: str = Field(..., min_length=2, max_length=100)
    team_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Engagement-Specific Configuration
    agent_configuration: Dict[str, Any] = Field(default_factory=dict, description="Engagement-specific agent settings")
    discovery_preferences: Dict[str, Any] = Field(default_factory=dict, description="Discovery phase preferences")
    assessment_criteria: Dict[str, Any] = Field(default_factory=dict, description="Assessment and strategy criteria")
    
    @field_validator('engagement_description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError('Engagement description must be at least 10 characters')
        return v.strip()
    
    @field_validator('planned_end_date')
    @classmethod
    def validate_dates(cls, v: Optional[datetime], info: ValidationInfo) -> Optional[datetime]:
        if v and 'planned_start_date' in info.data and info.data['planned_start_date']:
            if v <= info.data['planned_start_date']:
                raise ValueError('Planned end date must be after start date')
        return v

class EngagementUpdate(BaseModel):
    """Schema for updating engagement."""
    engagement_name: Optional[str] = Field(None, min_length=2, max_length=255)
    engagement_description: Optional[str] = Field(None, min_length=10, max_length=1000)
    migration_scope: Optional[MigrationScopeEnum] = None
    target_cloud_provider: Optional[CloudProviderEnum] = None
    
    # Migration Planning Updates
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    estimated_budget: Optional[float] = Field(None, ge=0)
    estimated_asset_count: Optional[int] = Field(None, ge=0)
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    actual_budget: Optional[float] = Field(None, ge=0)
    
    # Team and Process Updates
    engagement_manager: Optional[str] = Field(None, min_length=2, max_length=100)
    technical_lead: Optional[str] = Field(None, min_length=2, max_length=100)
    team_preferences: Optional[Dict[str, Any]] = None
    
    # Configuration Updates
    agent_configuration: Optional[Dict[str, Any]] = None
    discovery_preferences: Optional[Dict[str, Any]] = None
    assessment_criteria: Optional[Dict[str, Any]] = None
    
    # Status Updates
    current_phase: Optional[MigrationPhaseEnum] = None
    completion_percentage: Optional[float] = Field(None, ge=0, le=100)

class EngagementResponse(BaseModel):
    """Schema for engagement response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    engagement_name: str
    client_account_id: str
    engagement_description: Optional[str] = None
    migration_scope: Optional[Union[str, Dict[str, Any]]] = None
    target_cloud_provider: Optional[str] = None
    
    # Migration Planning
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    estimated_budget: Optional[float] = None
    estimated_asset_count: Optional[int] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    actual_budget: Optional[float] = None
    
    # Team and Process
    engagement_manager: Optional[str] = None
    technical_lead: Optional[str] = None
    team_preferences: Optional[Dict[str, Any]] = None
    
    # Configuration
    agent_configuration: Optional[Dict[str, Any]] = None
    discovery_preferences: Optional[Dict[str, Any]] = None
    assessment_criteria: Optional[Dict[str, Any]] = None
    
    # Status and Progress
    current_phase: Optional[str] = "planning"
    completion_percentage: float = 0.0
    current_flow_id: Optional[str] = None
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    total_sessions: int = 0
    total_assets: int = 0

# =========================
# Session Management Schemas
# =========================

class SessionCreate(BaseModel):
    """Schema for creating a new session."""
    engagement_id: str
    session_name: Optional[str] = Field(None, max_length=255)
    session_description: Optional[str] = Field(None, max_length=1000)
    session_type: str = Field(default="data_import", pattern=r'^(data_import|assessment|planning|manual)$')
    
    # Session Configuration
    import_preferences: Dict[str, Any] = Field(default_factory=dict)
    agent_settings: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('session_name')
    @classmethod
    def validate_session_name(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v.strip()) < 2:
            raise ValueError('Session name must be at least 2 characters if provided')
        return v.strip() if v else None

class SessionUpdate(BaseModel):
    """Schema for updating session."""
    session_name: Optional[str] = Field(None, max_length=255)
    session_description: Optional[str] = Field(None, max_length=1000)
    session_type: Optional[str] = Field(None, pattern=r'^(data_import|assessment|planning|manual)$')
    status: Optional[str] = Field(None, pattern=r'^(active|completed|archived|error)$')
    
    # Configuration Updates
    import_preferences: Optional[Dict[str, Any]] = None
    agent_settings: Optional[Dict[str, Any]] = None
    
    # Progress Updates
    completion_percentage: Optional[float] = Field(None, ge=0, le=100)
    error_details: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    """Schema for session response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    engagement_id: str
    session_name: str
    session_description: Optional[str] = None
    session_type: str
    status: str
    
    # Configuration
    import_preferences: Dict[str, Any]
    agent_settings: Dict[str, Any]
    
    # Progress and Statistics
    completion_percentage: float = 0.0
    total_records_processed: int = 0
    total_assets_discovered: int = 0
    total_errors: int = 0
    error_details: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# =========================
# Bulk Operations Schemas
# =========================

class BulkClientImport(BaseModel):
    """Schema for bulk client import."""
    clients: List[ClientAccountCreate]
    import_options: Dict[str, Any] = Field(default_factory=dict)
    validation_mode: str = Field(default="strict", pattern=r'^(strict|lenient|skip_errors)$')

class BulkEngagementImport(BaseModel):
    """Schema for bulk engagement import."""
    engagements: List[EngagementCreate]
    import_options: Dict[str, Any] = Field(default_factory=dict)
    validation_mode: str = Field(default="strict", pattern=r'^(strict|lenient|skip_errors)$')

class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response."""
    status: str
    total_processed: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    imported_ids: List[str] = Field(default_factory=list)
    processing_time_seconds: float

# =========================
# Search and Filter Schemas
# =========================

class ClientSearchFilters(BaseModel):
    """Schema for client search filters."""
    account_name: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    target_cloud_providers: Optional[List[CloudProviderEnum]] = None
    business_priorities: Optional[List[BusinessPriorityEnum]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    is_active: Optional[bool] = True

class EngagementSearchFilters(BaseModel):
    """Schema for engagement search filters."""
    client_account_id: Optional[str] = None
    engagement_name: Optional[str] = None
    migration_scope: Optional[MigrationScopeEnum] = None
    target_cloud_provider: Optional[CloudProviderEnum] = None
    current_phase: Optional[MigrationPhaseEnum] = None
    engagement_manager: Optional[str] = None
    planned_start_after: Optional[datetime] = None
    planned_start_before: Optional[datetime] = None
    is_active: Optional[bool] = True

class SessionSearchFilters(BaseModel):
    """Schema for session search filters."""
    engagement_id: Optional[str] = None
    session_type: Optional[str] = None
    status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

# =========================
# Dashboard and Analytics Schemas
# =========================

class ClientDashboardStats(BaseModel):
    """Schema for client dashboard statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    total_clients: int
    active_clients: int
    clients_by_industry: Dict[str, int]
    clients_by_company_size: Dict[str, int]
    clients_by_cloud_provider: Dict[str, int]
    recent_client_registrations: List[ClientAccountResponse]

class EngagementDashboardStats(BaseModel):
    """Schema for engagement dashboard statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    total_engagements: int
    active_engagements: int
    engagements_by_type: Dict[str, int]
    engagements_by_status: Dict[str, int]
    avg_engagement_duration_days: float
    recent_engagements: List[EngagementResponse]

class SessionDashboardStats(BaseModel):
    """Schema for session dashboard statistics."""
    model_config = ConfigDict(from_attributes=True)
    
    total_sessions: int
    active_sessions: int
    sessions_by_type: Dict[str, int]
    sessions_by_status: Dict[str, int]
    average_completion_time_hours: float
    total_assets_processed: int
    recent_session_activity: List[SessionResponse]

class UserDashboardStats(BaseModel):
    total_users: int
    active_users: int

# ==================================
# Generic/Utility Schemas for Admin
# ==================================

class AdminErrorResponse(BaseModel):
    """Schema for admin error responses."""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    field_errors: Optional[Dict[str, List[str]]] = None

class AdminSuccessResponse(BaseModel):
    """Schema for admin success responses."""
    status: str = "success"
    message: str
    data: Optional[Union[ClientAccountResponse, EngagementResponse, SessionResponse, Dict[str, Any]]] = None

class AdminPaginationParams(BaseModel):
    """Schema for admin pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", pattern=r'^(asc|desc)$')

class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[Union[ClientAccountResponse, EngagementResponse, SessionResponse]]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_previous: bool 