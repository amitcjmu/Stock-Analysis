"""
Demo Data Schemas
Pydantic models for demo API request/response data structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Base demo schemas
class DemoAssetBase(BaseModel):
    """Base schema for demo assets."""
    name: str = Field(..., description="Asset name")
    asset_type: str = Field(..., description="Type of asset")
    hostname: Optional[str] = Field(None, description="Hostname")
    ip_address: Optional[str] = Field(None, description="IP address")
    operating_system: Optional[str] = Field(None, description="Operating system")
    os_version: Optional[str] = Field(None, description="OS version")
    cpu_cores: Optional[int] = Field(None, description="Number of CPU cores")
    memory_gb: Optional[float] = Field(None, description="Memory in GB")
    storage_gb: Optional[float] = Field(None, description="Storage in GB")
    environment: Optional[str] = Field(None, description="Environment (prod/dev/test)")
    business_criticality: Optional[str] = Field(None, description="Business criticality level")
    location: Optional[str] = Field(None, description="Physical location")
    cost_center: Optional[str] = Field(None, description="Cost center")
    owner: Optional[str] = Field(None, description="Asset owner")
    description: Optional[str] = Field(None, description="Asset description")

class DemoAssetCreate(DemoAssetBase):
    """Schema for creating demo assets."""
    pass

class DemoAssetUpdate(BaseModel):
    """Schema for updating demo assets."""
    name: Optional[str] = None
    asset_type: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    operating_system: Optional[str] = None
    os_version: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    storage_gb: Optional[float] = None
    environment: Optional[str] = None
    business_criticality: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None

class DemoAssetResponse(DemoAssetBase):
    """Schema for demo asset responses."""
    id: Union[str, UUID] = Field(..., description="Asset ID")
    is_mock: bool = Field(True, description="Indicates this is mock data")
    discovery_date: Optional[datetime] = Field(None, description="Discovery date")
    discovery_method: Optional[str] = Field(None, description="Discovery method")
    discovery_source: Optional[str] = Field(None, description="Discovery source")
    last_seen: Optional[datetime] = Field(None, description="Last seen date")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    
    @field_validator('id')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Analysis schemas
class DemoAnalysisResponse(BaseModel):
    """Schema for demo 6R analysis responses."""
    id: str = Field(..., description="Analysis ID")
    asset_id: Optional[str] = Field(None, description="Associated asset ID")
    recommended_strategy: Optional[str] = Field(None, description="Recommended 6R strategy")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)")
    risk_level: Optional[str] = Field(None, description="Risk level")
    complexity: Optional[str] = Field(None, description="Migration complexity")
    effort_estimate: Optional[str] = Field(None, description="Effort estimate")
    cost_estimate: Optional[float] = Field(None, description="Cost estimate")
    rationale: Optional[str] = Field(None, description="Analysis rationale")
    alternatives: Optional[List[str]] = Field(None, description="Alternative strategies")
    considerations: Optional[List[str]] = Field(None, description="Key considerations")
    name: Optional[str] = Field(None, description="Analysis name")
    status: Optional[str] = Field(None, description="Analysis status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    @field_validator('id', 'asset_id', mode='before')
    @classmethod
    def convert_to_str(cls, v):
        if v is None:
            return v
        return str(v)
    
    class Config:
        from_attributes = True

# Wave schemas
class DemoWaveResponse(BaseModel):
    """Schema for demo migration wave responses."""
    id: Union[str, UUID] = Field(..., description="Wave ID")
    wave_number: int = Field(..., description="Wave number")
    name: str = Field(..., description="Wave name")
    description: Optional[str] = Field(None, description="Wave description")
    planned_start_date: Optional[datetime] = Field(None, description="Planned start date")
    planned_end_date: Optional[datetime] = Field(None, description="Planned end date")
    status: Optional[str] = Field(None, description="Wave status")
    asset_count: Optional[int] = Field(None, description="Number of assets in wave")
    estimated_effort: Optional[str] = Field(None, description="Estimated effort")
    dependencies: Optional[List[str]] = Field(None, description="Wave dependencies")
    is_mock: bool = Field(True, description="Indicates this is mock data")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    @field_validator('id')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Tag schemas
class DemoTagResponse(BaseModel):
    """Schema for demo tag responses."""
    id: Union[str, UUID] = Field(..., description="Tag ID")
    name: str = Field(..., description="Tag name")
    category: Optional[str] = Field(None, description="Tag category")
    description: Optional[str] = Field(None, description="Tag description")
    color: Optional[str] = Field(None, description="Tag color")
    is_mock: bool = Field(True, description="Indicates this is mock data")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    @field_validator('id')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Summary schemas
class DemoSummaryResponse(BaseModel):
    """Schema for demo assets summary response."""
    total_assets: int = Field(..., description="Total number of assets")
    asset_types: Dict[str, int] = Field(..., description="Asset type distribution")
    environments: Dict[str, int] = Field(..., description="Environment distribution")
    business_criticality: Dict[str, int] = Field(..., description="Business criticality distribution")
    total_resources: Dict[str, float] = Field(..., description="Total resource summary")

# Engagement schemas
class DemoEngagementResponse(BaseModel):
    """Schema for demo engagement information response."""
    client_name: str = Field(..., description="Client name")
    engagement_name: str = Field(..., description="Engagement name")
    engagement_type: str = Field(..., description="Engagement type")
    start_date: str = Field(..., description="Start date")
    estimated_end_date: str = Field(..., description="Estimated end date")
    project_manager: str = Field(..., description="Project manager")
    technical_lead: str = Field(..., description="Technical lead")
    total_assets_discovered: int = Field(..., description="Total assets discovered")
    assessment_phase: str = Field(..., description="Current assessment phase")
    next_milestone: str = Field(..., description="Next milestone")
    confidence_level: str = Field(..., description="Confidence level")

# Search and AI schemas
class DemoAssetSearchRequest(BaseModel):
    """Schema for demo asset search requests."""
    query_text: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(10, le=50, description="Maximum number of results")
    asset_type: Optional[str] = Field(None, description="Filter by asset type")
    environment: Optional[str] = Field(None, description="Filter by environment")

class DemoSimilarAssetsRequest(BaseModel):
    """Schema for finding similar demo assets."""
    asset_id: str = Field(..., description="Reference asset ID")
    limit: int = Field(5, le=20, description="Maximum number of similar assets")
    similarity_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")

class DemoAutoTagRequest(BaseModel):
    """Schema for auto-tagging demo assets."""
    asset_id: str = Field(..., description="Asset ID to tag")
    confidence_threshold: Optional[float] = Field(0.8, ge=0.0, le=1.0, description="Tag confidence threshold")
    max_tags: Optional[int] = Field(5, ge=1, le=10, description="Maximum number of tags to apply")

# Batch operation schemas
class DemoBatchAssetCreate(BaseModel):
    """Schema for batch creating demo assets."""
    assets: List[DemoAssetCreate] = Field(..., description="List of assets to create")
    
class DemoBatchAssetResponse(BaseModel):
    """Schema for batch asset creation response."""
    created_count: int = Field(..., description="Number of assets created")
    failed_count: int = Field(..., description="Number of failed creations")
    created_assets: List[DemoAssetResponse] = Field(..., description="Successfully created assets")
    errors: List[str] = Field(..., description="Error messages for failed creations")

# Filter schemas
class DemoAssetFilters(BaseModel):
    """Schema for demo asset filtering options."""
    asset_type: Optional[str] = None
    environment: Optional[str] = None
    business_criticality: Optional[str] = None
    operating_system: Optional[str] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    owner: Optional[str] = None
    min_cpu_cores: Optional[int] = None
    max_cpu_cores: Optional[int] = None
    min_memory_gb: Optional[float] = None
    max_memory_gb: Optional[float] = None
    min_storage_gb: Optional[float] = None
    max_storage_gb: Optional[float] = None

class DemoAssetListRequest(BaseModel):
    """Schema for demo asset list requests with filtering."""
    limit: int = Field(100, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    filters: Optional[DemoAssetFilters] = Field(None, description="Asset filters")
    sort_by: Optional[str] = Field("name", description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order (asc/desc)")

# Statistics schemas
class DemoAssetStats(BaseModel):
    """Schema for demo asset statistics."""
    total_assets: int
    total_cpu_cores: int
    total_memory_gb: float
    total_storage_gb: float
    avg_cpu_per_asset: float
    avg_memory_per_asset: float
    avg_storage_per_asset: float
    asset_type_distribution: Dict[str, int]
    environment_distribution: Dict[str, int]
    criticality_distribution: Dict[str, int]
    os_distribution: Dict[str, int]
    location_distribution: Dict[str, int]

class DemoHealthResponse(BaseModel):
    """Schema for demo API health check response."""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    timestamp: str = Field(..., description="Response timestamp")
    data_counts: Optional[Dict[str, int]] = Field(None, description="Data counts by type")
    version: Optional[str] = Field(None, description="API version") 