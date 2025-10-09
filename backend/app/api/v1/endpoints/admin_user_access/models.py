"""
Request and Response models for Admin User Access Management
"""

from pydantic import BaseModel


class ClientAccessResponse(BaseModel):
    id: str
    client_account_id: str
    client_name: str
    access_level: str
    is_active: bool
    granted_at: str


class EngagementAccessResponse(BaseModel):
    id: str
    engagement_id: str
    engagement_name: str
    client_account_id: str
    client_name: str
    access_level: str
    is_active: bool
    granted_at: str


class GrantClientAccessRequest(BaseModel):
    user_id: str
    client_account_id: str
    access_level: str


class GrantEngagementAccessRequest(BaseModel):
    user_id: str
    engagement_id: str
    access_level: str


class RecentActivityResponse(BaseModel):
    id: str
    user_name: str
    action_type: str
    resource_type: str
    resource_id: str
    result: str
    reason: str
    created_at: str
