"""
Pydantic schemas for dependency data.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, UUID4
from datetime import datetime

class DependencyBase(BaseModel):
    """Base schema for dependency data."""
    dependency_type: str
    description: Optional[str] = None

class DependencyCreate(DependencyBase):
    """Schema for creating a new dependency."""
    source_id: UUID4
    target_id: UUID4
    is_app_to_app: bool

class DependencyResponse(DependencyBase):
    """Schema for dependency response."""
    id: UUID4
    asset_id: UUID4
    depends_on_asset_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationInfo(BaseModel):
    """Schema for application information."""
    id: UUID4
    name: str
    application_name: Optional[str]
    description: Optional[str]

class ServerInfo(BaseModel):
    """Schema for server information."""
    id: UUID4
    name: str
    hostname: Optional[str]
    description: Optional[str]

class DependencyGraphNode(BaseModel):
    """Schema for dependency graph node."""
    id: UUID4
    label: str

class DependencyGraphEdge(BaseModel):
    """Schema for dependency graph edge."""
    source: UUID4
    target: UUID4
    type: str
    description: Optional[str]

class DependencyGraph(BaseModel):
    """Schema for dependency graph."""
    nodes: List[DependencyGraphNode]
    edges: List[DependencyGraphEdge]

class AppServerMapping(BaseModel):
    """Schema for application-to-server mapping."""
    hosting_relationships: List[Dict[str, Any]]
    available_applications: List[ApplicationInfo]
    available_servers: List[ServerInfo]

class CrossApplicationMapping(BaseModel):
    """Schema for application-to-application mapping."""
    cross_app_dependencies: List[Dict[str, Any]]
    available_applications: List[ApplicationInfo]
    dependency_graph: DependencyGraph

class DependencyAnalysisResponse(BaseModel):
    """Schema for dependency analysis response."""
    app_server_mapping: AppServerMapping
    cross_application_mapping: CrossApplicationMapping 