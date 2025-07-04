"""
Flow Commands

Write operations for discovery flows.
"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete, and_

from app.models.discovery_flow import DiscoveryFlow
from ..queries.flow_queries import FlowQueries

logger = logging.getLogger(__name__)


class FlowCommands:
    """Handles all flow write operations"""
    
    def __init__(self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_queries = FlowQueries(db, client_account_id, engagement_id)
    
    async def create_discovery_flow(
        self, 
        flow_id: str,
        master_flow_id: Optional[str] = None,
        flow_type: str = "primary",
        description: Optional[str] = None,
        initial_state_data: Optional[Dict[str, Any]] = None,
        data_import_id: Optional[str] = None,
        user_id: Optional[str] = None,
        raw_data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DiscoveryFlow:
        """Create new discovery flow using CrewAI Flow ID"""
        
        # Parse flow_id as UUID
        try:
            if isinstance(flow_id, uuid.UUID):
                parsed_flow_id = flow_id
            else:
                parsed_flow_id = uuid.UUID(flow_id)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid CrewAI Flow ID: {flow_id}, error: {e}")
            raise ValueError(f"Invalid CrewAI Flow ID: {flow_id}. Must be a valid UUID.")
        
        # Parse optional UUIDs
        master_uuid = uuid.UUID(master_flow_id) if master_flow_id else None
        
        # Prepare initial state data including raw_data and metadata
        state_data = initial_state_data or {}
        if raw_data:
            state_data['raw_data'] = raw_data
            state_data['records_total'] = len(raw_data)
        if metadata:
            state_data['metadata'] = metadata
        
        # Parse data_import_id if provided
        data_import_uuid = None
        if data_import_id:
            try:
                data_import_uuid = uuid.UUID(data_import_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid data_import_id: {data_import_id}")
        
        flow = DiscoveryFlow(
            flow_id=parsed_flow_id,
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            user_id=user_id or "system",  # Add user_id with fallback
            master_flow_id=master_uuid,
            flow_type=flow_type,
            flow_name=description or f"Discovery Flow {flow_id[:8]}",
            status="active",
            crewai_state_data=state_data,
            data_import_id=data_import_uuid,  # Store data_import_id
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(flow)
        await self.db.commit()
        await self.db.refresh(flow)
        
        logger.info(f"✅ Created discovery flow: {flow_id}")
        return flow
    
    async def update_phase_completion(
        self, 
        flow_id: str, 
        phase: str, 
        data: Optional[Dict[str, Any]] = None,
        crew_status: Optional[Dict[str, Any]] = None,
        completed: bool = True,
        agent_insights: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[DiscoveryFlow]:
        """Update phase completion and store results"""
        
        # Build update values
        update_values = {
            "updated_at": datetime.utcnow()
        }
        
        # Map phase to completion field
        phase_completion_map = {
            "data_import": "data_import_completed",
            "attribute_mapping": "attribute_mapping_completed",
            "field_mapping": "attribute_mapping_completed",  # Alias
            "data_cleansing": "data_cleansing_completed",
            "inventory": "inventory_completed",
            "dependencies": "dependencies_completed",
            "tech_debt": "tech_debt_completed"
        }
        
        if phase in phase_completion_map:
            update_values[phase_completion_map[phase]] = completed
        
        # Update state data
        if data or crew_status or agent_insights:
            # Get existing flow to merge data
            existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
            if existing_flow:
                state_data = existing_flow.crewai_state_data or {}
                
                if data:
                    state_data[phase] = data
                
                if crew_status:
                    state_data["crew_status"] = crew_status
                
                if agent_insights:
                    existing_insights = state_data.get("agent_insights", [])
                    existing_insights.extend(agent_insights)
                    state_data["agent_insights"] = existing_insights
                
                # Extract processing statistics to root level
                processing_fields = ['records_processed', 'records_total', 'records_valid', 'records_failed']
                for field in processing_fields:
                    if data and field in data:
                        state_data[field] = data[field]
                
                update_values["crewai_state_data"] = state_data
        
        # Calculate progress
        progress = await self._calculate_progress(flow_id, phase, completed)
        update_values["progress_percentage"] = progress
        
        # Execute update
        stmt = update(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == uuid.UUID(flow_id),
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id
            )
        ).values(**update_values)
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated flow
        return await self.flow_queries.get_by_flow_id(flow_id)
    
    async def complete_discovery_flow(self, flow_id: str) -> DiscoveryFlow:
        """Mark discovery flow as completed"""
        
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not flow:
            raise ValueError(f"Discovery flow not found: {flow_id}")
        
        # Create assessment package
        assessment_package = {
            "discovery_phases_completed": [
                phase for phase, completed in {
                    "data_import": flow.data_import_completed,
                    "attribute_mapping": flow.attribute_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "inventory": flow.inventory_completed,
                    "dependencies": flow.dependencies_completed,
                    "tech_debt": flow.tech_debt_completed
                }.items() if completed
            ],
            "ready_for_assessment": True,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Update flow
        update_values = {
            "status": "completed",
            "progress_percentage": 100.0,
            "assessment_ready": True,
            "assessment_package": assessment_package,
            "completed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        stmt = update(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == uuid.UUID(flow_id),
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id
            )
        ).values(**update_values)
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        return await self.flow_queries.get_by_flow_id(flow_id)
    
    async def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow and its related data"""
        try:
            # Delete the flow
            stmt = delete(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == uuid.UUID(flow_id),
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id
                )
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"✅ Deleted flow: {flow_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting flow: {e}")
            await self.db.rollback()
            return False
    
    async def update_master_flow_reference(self, flow_id: str, master_flow_id: str) -> bool:
        """Update the master flow reference for coordination"""
        try:
            stmt = update(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == uuid.UUID(flow_id),
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id
                )
            ).values(
                master_flow_id=uuid.UUID(master_flow_id),
                updated_at=datetime.utcnow()
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating master flow reference: {e}")
            await self.db.rollback()
            return False
    
    async def transition_to_assessment_phase(self, flow_id: str, assessment_flow_id: str) -> bool:
        """Transition flow to assessment phase"""
        try:
            # Get existing flow
            flow = await self.flow_queries.get_by_flow_id(flow_id)
            if not flow:
                return False
            
            # Update state data
            state_data = flow.crewai_state_data or {}
            state_data["assessment_transition"] = {
                "assessment_flow_id": assessment_flow_id,
                "transitioned_at": datetime.utcnow().isoformat(),
                "discovery_completed": True
            }
            
            # Update flow
            stmt = update(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == uuid.UUID(flow_id),
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id
                )
            ).values(
                assessment_ready=True,
                assessment_flow_id=uuid.UUID(assessment_flow_id),
                crewai_state_data=state_data,
                updated_at=datetime.utcnow()
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error transitioning to assessment: {e}")
            await self.db.rollback()
            return False
    
    async def _calculate_progress(self, flow_id: str, current_phase: str, completed: bool) -> float:
        """Calculate progress percentage based on phase completion"""
        # Get existing flow
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not flow:
            return 0.0
        
        # Count completed phases
        completed_count = 0
        total_phases = 6
        
        # Check each phase
        phases = {
            "data_import": flow.data_import_completed,
            "attribute_mapping": flow.attribute_mapping_completed,
            "data_cleansing": flow.data_cleansing_completed,
            "inventory": flow.inventory_completed,
            "dependencies": flow.dependencies_completed,
            "tech_debt": flow.tech_debt_completed
        }
        
        # Override current phase with new value
        if current_phase in phases or current_phase == "field_mapping":
            if current_phase == "field_mapping":
                phases["attribute_mapping"] = completed
            else:
                phases[current_phase] = completed
        
        # Count completed
        completed_count = sum(1 for is_completed in phases.values() if is_completed)
        
        return (completed_count / total_phases) * 100.0