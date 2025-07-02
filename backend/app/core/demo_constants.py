"""
Demo Data Constants for AI Force Migration Platform

These constants define the standard UUIDs used for demo data across the platform.
Using fixed UUIDs allows us to easily identify demo/mock data without database queries.
"""

# Demo Mode Constants - Standard UUIDs for identifying demo data
DEMO_USER_ID = '44444444-4444-4444-4444-444444444444'
DEMO_CLIENT_ID = '11111111-1111-1111-1111-111111111111'
DEMO_ENGAGEMENT_ID = '22222222-2222-2222-2222-222222222222'
DEMO_FLOW_ID = '33333333-3333-3333-3333-333333333333'

# Demo Data Identifiers
DEMO_USER_EMAIL = 'demo@democorp.com'
DEMO_CLIENT_NAME = 'Democorp'
DEMO_ENGAGEMENT_NAME = 'Cloud Migration 2024'
DEMO_FLOW_NAME = 'Demo Flow'

def is_demo_user_id(user_id: str) -> bool:
    """Check if a user ID is the demo user."""
    return str(user_id) == DEMO_USER_ID

def is_demo_client_id(client_id: str) -> bool:
    """Check if a client ID is the demo client."""
    return str(client_id) == DEMO_CLIENT_ID

def is_demo_engagement_id(engagement_id: str) -> bool:
    """Check if an engagement ID is the demo engagement."""
    return str(engagement_id) == DEMO_ENGAGEMENT_ID

def is_demo_flow_id(flow_id: str) -> bool:
    """Check if a flow ID is the demo flow."""
    return str(flow_id) == DEMO_FLOW_ID

def is_demo_data(entity_id: str) -> bool:
    """Check if any entity ID is demo data."""
    return (is_demo_user_id(entity_id) or 
            is_demo_client_id(entity_id) or 
            is_demo_engagement_id(entity_id) or 
            is_demo_flow_id(entity_id)) 