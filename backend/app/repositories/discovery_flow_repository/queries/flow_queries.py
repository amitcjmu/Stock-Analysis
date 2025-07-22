"""
Flow Queries

Read operations for discovery flows.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class FlowQueries:
    """Handles all flow query operations"""
    
    def __init__(self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
    
    async def get_by_flow_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI Flow ID with context filtering"""
        try:
            # Convert flow_id to UUID
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None
            
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id: {e}")
            return None
    
    async def get_by_flow_id_global(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by ID without tenant filtering (for duplicate checking)
        
        SECURITY WARNING: This method bypasses tenant isolation and should only be used
        for system-level operations like duplicate checking. Never expose this to user-facing APIs.
        """
        # Log security audit trail
        logger.warning(f"🔒 SECURITY AUDIT: Global query attempted for flow_id={flow_id} by client={self.client_account_id}")
        
        try:
            # Convert flow_id to UUID
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None
            
            # SECURITY: First check if the flow belongs to the current client
            tenant_check = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id
                )
            )
            result = await self.db.execute(tenant_check)
            if result.scalar_one_or_none():
                # Flow belongs to current client, safe to return
                return result.scalar_one_or_none()
            
            # SECURITY: Only allow global query for system operations
            # In production, this should check for system/admin privileges
            logger.warning(f"🔒 SECURITY: Denying global query for flow {flow_id} - does not belong to client {self.client_account_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id_global: {e}")
            return None
    
    
    async def get_active_flows(self) -> List[DiscoveryFlow]:
        """Get all active discovery flows for the client/engagement"""
        # Include phase names that may have been incorrectly set as status
        valid_active_statuses = [
            "initialized", "active", "running", "paused",
            # Phase names that might have been set as status by mistake
            "data_import", "attribute_mapping", "field_mapping", 
            "data_cleansing", "inventory", "dependencies", "tech_debt"
        ]
        
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id,
                DiscoveryFlow.status.in_(valid_active_statuses)
            )
        ).order_by(desc(DiscoveryFlow.updated_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_incomplete_flows(self) -> List[DiscoveryFlow]:
        """Get incomplete flows that need attention"""
        # Check if ALL phases are completed
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id,
                DiscoveryFlow.status != "completed",
                # Check if any phase is not completed
                ~and_(
                    DiscoveryFlow.data_import_completed == True,
                    DiscoveryFlow.attribute_mapping_completed == True,
                    DiscoveryFlow.data_cleansing_completed == True,
                    DiscoveryFlow.inventory_completed == True,
                    DiscoveryFlow.dependencies_completed == True,
                    DiscoveryFlow.tech_debt_completed == True
                )
            )
        ).order_by(desc(DiscoveryFlow.updated_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_completed_flows(self, limit: int = 10) -> List[DiscoveryFlow]:
        """Get recently completed flows"""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id,
                DiscoveryFlow.status == "completed"
            )
        ).order_by(desc(DiscoveryFlow.completed_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_by_master_flow_id(self, master_flow_id: str) -> Optional[DiscoveryFlow]:
        """Get flow by master flow ID reference"""
        try:
            master_uuid = uuid.UUID(master_flow_id)
            
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.master_flow_id == master_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting flow by master flow ID: {e}")
            return None
    
    async def get_flows_by_type(self, flow_type: str) -> List[DiscoveryFlow]:
        """Get flows by type (primary, supplemental, assessment)"""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id,
                DiscoveryFlow.flow_type == flow_type
            )
        ).order_by(desc(DiscoveryFlow.created_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_flows_by_status(self, status: str) -> List[DiscoveryFlow]:
        """Get flows by status"""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id,
                DiscoveryFlow.status == status
            )
        ).order_by(desc(DiscoveryFlow.updated_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()