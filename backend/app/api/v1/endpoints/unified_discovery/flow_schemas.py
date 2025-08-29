"""
Flow Management Schemas for Unified Discovery

Request and response models for flow management endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FlowInitializationRequest(BaseModel):
    """Request model for flow initialization"""

    flow_name: Optional[str] = None
    raw_data: Optional[List[Dict[str, Any]]] = None
    configuration: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class FlowInitializationResponse(BaseModel):
    """Response model for flow initialization"""

    success: bool
    flow_id: str
    flow_name: str
    status: str
    message: str
    metadata: Dict[str, Any]
