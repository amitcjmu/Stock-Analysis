"""
Delete Handler

Handles flow deletion operations.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from ..validators.permission_validator import PermissionValidator

logger = logging.getLogger(__name__)


class DeleteHandler:
    """Handles flow deletion operations"""
    
    def __init__(self, db: AsyncSession, flow_repo: DiscoveryFlowRepository, permission_validator: PermissionValidator):
        """Initialize with database session, flow repository, and permission validator"""
        self.db = db
        self.flow_repo = flow_repo
        self.permission_validator = permission_validator
    
    async def delete_flow(self, flow_id: str, force_delete: bool = False) -> Dict[str, Any]:
        """Delete a discovery flow and cleanup related data"""
        try:
            logger.info(f"🗑️ Deleting flow: {flow_id}, force: {force_delete}")
            
            # Get flow to check permissions
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            if not flow:
                return {
                    "status": "error",
                    "message": f"Flow {flow_id} not found",
                    "deleted": False
                }
            
            # Validate delete permission
            allowed, error_msg = self.permission_validator.validate_delete_permission(flow, force_delete)
            if not allowed:
                return {
                    "status": "error",
                    "message": error_msg,
                    "deleted": False
                }
            
            # Delete the flow
            deleted = await self.flow_repo.delete_flow(flow_id)
            
            if deleted:
                cleanup_summary = {
                    "flow_records_deleted": 1,
                    "status": "completed",
                    "cleanup_time": datetime.now().isoformat()
                }
                
                result = {
                    "flow_id": flow_id,
                    "deleted": True,
                    "cleanup_summary": cleanup_summary,
                    "message": "Flow and related data deleted successfully"
                }
                
                logger.info(f"✅ Flow deleted: {flow_id}")
                return result
            else:
                return {
                    "flow_id": flow_id,
                    "deleted": False,
                    "message": "Failed to delete flow"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to delete flow: {e}")
            return {
                "status": "error",
                "message": f"Failed to delete flow: {str(e)}",
                "deleted": False
            }