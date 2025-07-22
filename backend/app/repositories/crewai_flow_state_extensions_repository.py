"""
CrewAI Flow State Extensions Repository
Repository for managing master flow records in crewai_flow_state_extensions table.
This is the master table that coordinates all CrewAI flows (Discovery, Assessment, Planning, etc.)
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class CrewAIFlowStateExtensionsRepository(ContextAwareRepository):
    """
    Repository for master CrewAI flow state management.
    This is the central coordination table for all flow types.
    """
    
    def __init__(self, db: AsyncSession, client_account_id: str, engagement_id: str = None, user_id: Optional[str] = None):
        # Handle None values and invalid UUIDs with proper fallbacks
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        
        # Safely convert client_account_id
        try:
            if client_account_id and client_account_id != "None":
                # Handle if already a UUID object
                if isinstance(client_account_id, uuid.UUID):
                    parsed_client_id = client_account_id
                else:
                    parsed_client_id = uuid.UUID(str(client_account_id))
            else:
                parsed_client_id = demo_client_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid client_account_id '{client_account_id}', using demo fallback")
            parsed_client_id = demo_client_id
            
        # Safely convert engagement_id
        try:
            if engagement_id and engagement_id != "None":
                # Handle if already a UUID object
                if isinstance(engagement_id, uuid.UUID):
                    parsed_engagement_id = engagement_id
                else:
                    parsed_engagement_id = uuid.UUID(str(engagement_id))
            else:
                parsed_engagement_id = demo_engagement_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid engagement_id '{engagement_id}', using demo fallback")
            parsed_engagement_id = demo_engagement_id
        
        # Initialize parent with proper parameters
        super().__init__(
            db=db,
            model_class=CrewAIFlowStateExtensions,
            client_account_id=str(parsed_client_id),
            engagement_id=str(parsed_engagement_id)
        )
        self.client_account_id = str(parsed_client_id)
        self.engagement_id = str(parsed_engagement_id)
    
    async def create_master_flow(
        self,
        flow_id: str,  # CrewAI generated flow ID
        flow_type: str,  # 'discovery', 'assessment', 'planning', 'execution'
        user_id: str = None,
        flow_name: str = None,
        flow_configuration: Dict[str, Any] = None,
        initial_state: Dict[str, Any] = None,
        auto_commit: bool = True  # Allow controlling transaction behavior
    ) -> CrewAIFlowStateExtensions:
        """Create master flow record - this must be called before creating specific flow types"""
        
        # Use demo constants as defaults
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        demo_user_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
        
        # Validate and parse flow_id
        try:
            if isinstance(flow_id, uuid.UUID):
                parsed_flow_id = flow_id
            else:
                parsed_flow_id = uuid.UUID(flow_id)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid CrewAI Flow ID provided: {flow_id}, error: {e}")
            raise ValueError(f"Invalid CrewAI Flow ID: {flow_id}. Must be a valid UUID.")
        
        # Validate flow type
        valid_flow_types = ['discovery', 'assessment', 'collection', 'planning', 'execution', 'modernize', 'finops', 'observability', 'decommission']
        if flow_type not in valid_flow_types:
            raise ValueError(f"Invalid flow_type: {flow_type}. Must be one of: {valid_flow_types}")
        
        # Generate flow name if not provided
        if not flow_name:
            flow_name = f"{flow_type.title()} Flow {str(flow_id)[:8]}"
        
        # Safely handle user_id
        safe_user_id = user_id or "test-user"  # Don't try to convert to UUID
        
        master_flow = CrewAIFlowStateExtensions(
            flow_id=parsed_flow_id,  # This is the master flow ID that other tables reference
            client_account_id=uuid.UUID(self.client_account_id) if self.client_account_id else demo_client_id,
            engagement_id=uuid.UUID(self.engagement_id) if self.engagement_id else demo_engagement_id,
            user_id=safe_user_id,  # Store as string, not UUID
            flow_type=flow_type,
            flow_name=flow_name,
            flow_status="initialized",
            flow_configuration=flow_configuration or {},
            flow_persistence_data=initial_state or {},
            agent_collaboration_log=[],
            phase_execution_times={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(master_flow)
        
        # FIX: Allow controlling transaction behavior for atomic operations
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(master_flow)
            logger.info(f"✅ Master flow created with commit: flow_id={flow_id}, type={flow_type}")
        else:
            await self.db.flush()
            await self.db.refresh(master_flow)
            logger.info(f"✅ Master flow created with flush: flow_id={flow_id}, type={flow_type}")
        
        return master_flow
    
    async def get_by_flow_id(self, flow_id: str) -> Optional[CrewAIFlowStateExtensions]:
        """Get master flow by CrewAI Flow ID"""
        try:
            # Convert flow_id to UUID for database query
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None
            
            # Convert context UUIDs
            try:
                client_uuid = uuid.UUID(self.client_account_id)
                engagement_uuid = uuid.UUID(self.engagement_id)
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid context UUID - client: {self.client_account_id}, engagement: {self.engagement_id}, error: {e}")
                return None
            
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )
            )
            
            result = await self.db.execute(stmt)
            flow = result.scalar_one_or_none()
            
            # Ensure flow has a valid status (fix for NULL status issue)
            if flow and flow.flow_status is None:
                logger.warning(f"⚠️ Flow {flow_id} has NULL status, setting to 'processing'")
                flow.flow_status = "processing"
                await self.db.commit()
            
            return flow
            
        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id: {e}")
            return None
    
    async def get_by_flow_id_global(self, flow_id: str) -> Optional[CrewAIFlowStateExtensions]:
        """Get master flow by CrewAI Flow ID without tenant filtering (for duplicate checking)
        
        SECURITY WARNING: This method bypasses tenant isolation and should only be used
        for system-level operations like duplicate checking. Never expose this to user-facing APIs.
        """
        # Log security audit trail
        logger.warning(f"🔒 SECURITY AUDIT: Global query attempted for master flow_id={flow_id} by client={self.client_account_id}")
        
        try:
            # Convert flow_id to UUID for database query
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None
            
            # SECURITY: First check if the flow belongs to the current client
            tenant_check = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == uuid.UUID(self.client_account_id)
                )
            )
            result = await self.db.execute(tenant_check)
            flow = result.scalar_one_or_none()
            
            if flow:
                # Flow belongs to current client, safe to return
                # Ensure flow has a valid status (fix for NULL status issue)
                if flow.flow_status is None:
                    logger.warning(f"⚠️ Flow {flow_id} has NULL status, setting to 'processing'")
                    flow.flow_status = "processing"
                    await self.db.commit()
                return flow
            
            # SECURITY: Only allow global query for system operations
            # In production, this should check for system/admin privileges
            logger.warning(f"🔒 SECURITY: Denying global query for master flow {flow_id} - does not belong to client {self.client_account_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id_global: {e}")
            return None
    
    async def update_flow_status(
        self,
        flow_id: str,
        status: str,
        phase_data: Dict[str, Any] = None,
        collaboration_entry: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> CrewAIFlowStateExtensions:
        """Update master flow status and state"""
        
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid UUID format in update_flow_status: {e}")
            raise ValueError(f"Invalid UUID format: {e}")
        
        # Build update values
        update_values = {
            "flow_status": status,
            "updated_at": datetime.utcnow()
        }
        
        # Get existing flow to merge data
        existing_flow = await self.get_by_flow_id(flow_id)
        if existing_flow:
            # Update persistence data
            if phase_data:
                persistence_data = existing_flow.flow_persistence_data or {}
                persistence_data.update(phase_data)
                update_values["flow_persistence_data"] = persistence_data
            
            # Update collaboration log
            if collaboration_entry:
                collaboration_log = existing_flow.agent_collaboration_log or []
                collaboration_log.append(collaboration_entry)
                # Keep only last 100 entries to prevent bloat
                if len(collaboration_log) > 100:
                    collaboration_log = collaboration_log[-100:]
                update_values["agent_collaboration_log"] = collaboration_log
                
            # Update metadata (ADR-012 sync metadata)
            if metadata:
                flow_metadata = existing_flow.flow_metadata or {}
                flow_metadata.update(metadata)
                update_values["flow_metadata"] = flow_metadata
        
        # Execute update
        stmt = update(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.flow_id == flow_uuid,
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
                CrewAIFlowStateExtensions.engagement_id == engagement_uuid
            )
        ).values(**update_values)
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated flow
        return await self.get_by_flow_id(flow_id)
    
    async def get_flows_by_type(self, flow_type: str, limit: int = 10) -> List[CrewAIFlowStateExtensions]:
        """Get master flows by type for the current client/engagement"""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
            
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_type == flow_type,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )
            ).order_by(desc(CrewAIFlowStateExtensions.created_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"❌ Failed to get flows by type {flow_type}: {e}")
            return []
    
    async def get_active_flows(self, limit: int = 10) -> List[CrewAIFlowStateExtensions]:
        """Get all active master flows for the current client/engagement"""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
            
            active_statuses = ["initialized", "active", "processing", "paused"]
            
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    CrewAIFlowStateExtensions.flow_status.in_(active_statuses)
                )
            ).order_by(desc(CrewAIFlowStateExtensions.created_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            return []
    
    async def get_flows_by_engagement(
        self, 
        engagement_id: str, 
        flow_type: Optional[str] = None, 
        limit: int = 50
    ) -> List[CrewAIFlowStateExtensions]:
        """Get flows for a specific engagement"""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(engagement_id)
            
            # Build query conditions
            conditions = [
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
                CrewAIFlowStateExtensions.engagement_id == engagement_uuid
            ]
            
            # Add flow type filter if specified
            if flow_type:
                conditions.append(CrewAIFlowStateExtensions.flow_type == flow_type)
            
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(*conditions)
            ).order_by(desc(CrewAIFlowStateExtensions.created_at)).limit(limit)
            
            result = await self.db.execute(stmt)
            flows = result.scalars().all()
            
            logger.info(f"Retrieved {len(flows)} flows for engagement {engagement_id}")
            return flows
            
        except Exception as e:
            logger.error(f"❌ Failed to get flows by engagement {engagement_id}: {e}")
            return []
    
    async def delete_master_flow(self, flow_id: str) -> bool:
        """Delete master flow and all subordinate flows (cascade)"""
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
            
            stmt = delete(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"✅ Master flow deleted: {flow_id}")
            else:
                logger.warning(f"⚠️ Master flow not found for deletion: {flow_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Failed to delete master flow {flow_id}: {e}")
            return False
    
    async def get_master_flow_summary(self) -> Dict[str, Any]:
        """Get summary of master flow coordination status"""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
            
            # Get master flow statistics
            stmt = select(
                func.count(CrewAIFlowStateExtensions.id).label('total_master_flows'),
                func.count(func.distinct(CrewAIFlowStateExtensions.flow_type)).label('unique_flow_types')
            ).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )
            )
            
            result = await self.db.execute(stmt)
            stats = result.first()
            
            # Get flow type distribution
            type_stmt = select(
                CrewAIFlowStateExtensions.flow_type,
                func.count(CrewAIFlowStateExtensions.id).label('count')
            ).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )
            ).group_by(CrewAIFlowStateExtensions.flow_type)
            
            type_result = await self.db.execute(type_stmt)
            type_stats = {row.flow_type: row.count for row in type_result}
            
            # Get status distribution
            status_stmt = select(
                CrewAIFlowStateExtensions.flow_status,
                func.count(CrewAIFlowStateExtensions.id).label('count')
            ).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )
            ).group_by(CrewAIFlowStateExtensions.flow_status)
            
            status_result = await self.db.execute(status_stmt)
            status_stats = {row.flow_status: row.count for row in status_result}
            
            return {
                'total_master_flows': stats.total_master_flows,
                'unique_flow_types': stats.unique_flow_types,
                'flow_type_distribution': type_stats,
                'flow_status_distribution': status_stats,
                'master_coordination_health': 'healthy' if stats.total_master_flows > 0 else 'missing_master_flows'
            }
            
        except Exception as e:
            logger.error(f"Error in get_master_flow_summary: {e}")
            return {
                'total_master_flows': 0,
                'unique_flow_types': 0,
                'flow_type_distribution': {},
                'flow_status_distribution': {},
                'master_coordination_health': 'error'
            }