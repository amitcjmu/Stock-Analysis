"""
Decommission Flow Pydantic Schemas

This package contains all request and response schemas for decommission flow API endpoints.
Follows the pattern established in assessment_flow schemas.
"""

from .requests import (
    DecommissionFlowCreateRequest,
    ResumeFlowRequest,
    UpdatePhaseRequest,
)
from .responses import (
    DecommissionFlowResponse,
    DecommissionFlowStatusResponse,
    DecommissionFlowListItem,
    EligibleSystemResponse,
)

__all__ = [
    # Request schemas
    "DecommissionFlowCreateRequest",
    "ResumeFlowRequest",
    "UpdatePhaseRequest",
    # Response schemas
    "DecommissionFlowResponse",
    "DecommissionFlowStatusResponse",
    "DecommissionFlowListItem",
    "EligibleSystemResponse",
]
