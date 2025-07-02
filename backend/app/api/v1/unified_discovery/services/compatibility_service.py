"""
Compatibility service for bridging v1/v3 API differences.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class CompatibilityService:
    """Service for handling API version compatibility."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
    
    async def transform_v1_to_v3(self, v1_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform v1 API data to v3 format."""
        
        # Basic transformation logic
        v3_data = v1_data.copy()
        
        # Add v3-specific fields
        if "flow_id" not in v3_data:
            v3_data["flow_id"] = v1_data.get("flow_id", "unknown")
        
        # Transform status format
        if "status" in v1_data:
            v3_data["execution_status"] = v1_data["status"]
        
        logger.debug(f"Transformed v1 data to v3 format")
        return v3_data
    
    async def transform_v3_to_v1(self, v3_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform v3 API data to v1 format for backward compatibility."""
        
        # Basic transformation logic
        v1_data = v3_data.copy()
        
        # Map v3 fields to v1 equivalents
        if "flow_id" in v3_data:
            v1_data["flow_id"] = v3_data["flow_id"]
        
        if "execution_status" in v3_data:
            v1_data["status"] = v3_data["execution_status"]
        
        logger.debug(f"Transformed v3 data to v1 format")
        return v1_data
    
    def get_safe_context(self) -> RequestContext:
        """Get context safely with fallback values."""
        
        if self.context and self.context.client_account_id:
            return self.context
        
        logger.warning("⚠️ No context available, using fallback values")
        return RequestContext(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            user_id="347d1ecd-04f6-4e3a-86ca-d35703512301"
        )