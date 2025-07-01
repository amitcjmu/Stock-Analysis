"""
Permission Validator

Access control validation for flow operations.
"""

import logging
from typing import Optional
from uuid import UUID

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class PermissionValidator:
    """Handles permission validation for flow operations"""
    
    def __init__(self, context: RequestContext):
        """Initialize with request context"""
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
    
    def validate_flow_access(self, flow) -> bool:
        """
        Validate user has access to the flow.
        
        Checks:
        - Flow belongs to user's client account
        - Flow belongs to user's engagement
        - User created the flow or has appropriate permissions
        """
        try:
            # Check client account match
            if flow.client_account_id and self.client_account_id:
                if str(flow.client_account_id) != str(self.client_account_id):
                    logger.warning(f"Client account mismatch: flow={flow.client_account_id}, "
                                 f"context={self.client_account_id}")
                    return False
            
            # Check engagement match
            if flow.engagement_id and self.engagement_id:
                if str(flow.engagement_id) != str(self.engagement_id):
                    logger.warning(f"Engagement mismatch: flow={flow.engagement_id}, "
                                 f"context={self.engagement_id}")
                    return False
            
            # Check user access
            if flow.created_by and self.user_id:
                # User can always access flows they created
                if str(flow.created_by) == str(self.user_id):
                    return True
                
                # TODO: Check if user has permission through role/team
                # For now, allow access if client/engagement matches
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Permission validation error: {e}")
            return False
    
    def validate_flow_modification(self, flow) -> bool:
        """
        Validate user can modify the flow.
        
        More restrictive than read access - checks if user can update/delete.
        """
        try:
            # First check basic access
            if not self.validate_flow_access(flow):
                return False
            
            # Check if user created the flow
            if flow.created_by and self.user_id:
                if str(flow.created_by) == str(self.user_id):
                    return True
            
            # TODO: Check if user has admin/manager role
            # For now, allow modification if basic access is granted
            return True
            
        except Exception as e:
            logger.error(f"Modification permission validation error: {e}")
            return False
    
    def validate_delete_permission(self, flow, force_delete: bool = False) -> tuple[bool, Optional[str]]:
        """
        Validate user can delete the flow.
        
        Returns:
            Tuple of (allowed, error_message)
        """
        try:
            # Check basic modification permission
            if not self.validate_flow_modification(flow):
                return False, "Insufficient permissions to delete this flow"
            
            # Check flow status - prevent deletion of active flows unless forced
            if not force_delete:
                active_statuses = ["running", "active", "in_progress"]
                if flow.status in active_statuses:
                    return False, f"Cannot delete flow in {flow.status} status without force_delete=true"
            
            # Check if flow has dependent data
            if flow.discovery_assets_count and flow.discovery_assets_count > 0:
                if not force_delete:
                    return False, f"Flow has {flow.discovery_assets_count} assets. Use force_delete=true to delete."
            
            return True, None
            
        except Exception as e:
            logger.error(f"Delete permission validation error: {e}")
            return False, f"Permission validation error: {str(e)}"