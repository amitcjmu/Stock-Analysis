"""
Pydantic schemas for discovery-related data structures.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

class CMDBData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    data: List[Dict[str, Any]]

class FieldMapping(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_field: str
    target_field: str
    confidence: float

class DiscoveredAsset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_name: str
    asset_type: str
    details: Dict[str, Any] 