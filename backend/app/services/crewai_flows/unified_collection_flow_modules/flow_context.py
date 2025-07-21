"""
Flow Context for Collection Flow

This module contains the FlowContext class used to manage flow execution context.
"""

from typing import Optional


class FlowContext:
    """Flow context container for Collection Flow execution."""
    
    def __init__(self, flow_id: str, client_account_id: str, engagement_id: str, 
                 user_id: Optional[str] = None, db_session=None):
        self.flow_id = flow_id
        self.client_account_id = client_account_id  
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.db_session = db_session