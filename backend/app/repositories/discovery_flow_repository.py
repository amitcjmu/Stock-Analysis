"""
Discovery Flow Repository
Repository for new discovery flow tables following ContextAwareRepository pattern.
Follows the Multi-Flow Architecture Implementation Plan.
"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, desc, func
from sqlalchemy.orm import selectinload

from app.repositories.base_repository import ContextAwareRepository
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset

logger = logging.getLogger(__name__)


class DiscoveryFlowRepository(ContextAwareRepository):
    """
    Repository for new discovery flow tables
    Uses CrewAI Flow ID as single source of truth (no session_id confusion)
    """
    
    def __init__(self, db: AsyncSession, client_account_id: str, engagement_id: str = None):
        # Handle None values and invalid UUIDs with proper fallbacks
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        
        # Safely convert client_account_id
        try:
            if client_account_id and client_account_id != "None":
                parsed_client_id = uuid.UUID(client_account_id)
            else:
                parsed_client_id = demo_client_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid client_account_id '{client_account_id}', using demo fallback")
            parsed_client_id = demo_client_id
            
        # Safely convert engagement_id
        try:
            if engagement_id and engagement_id != "None":
                parsed_engagement_id = uuid.UUID(engagement_id)
            else:
                parsed_engagement_id = demo_engagement_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid engagement_id '{engagement_id}', using demo fallback")
            parsed_engagement_id = demo_engagement_id
        
        context = {
            'client_account_id': parsed_client_id,
            'engagement_id': parsed_engagement_id
        }
        super().__init__(db, context)
        self.client_account_id = str(parsed_client_id)
        self.engagement_id = str(parsed_engagement_id)
    
    async def create_discovery_flow(
        self, 
        flow_id: str,  # CrewAI generated flow ID
        import_session_id: str = None,
        user_id: str = None,
        raw_data: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ) -> DiscoveryFlow:
        """Create new discovery flow using CrewAI Flow ID as single source of truth"""
        
        # Use demo constants as defaults
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        demo_user_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
        
        # ✅ CRITICAL FIX: Always use the provided CrewAI Flow ID, never generate a new one
        try:
            # Try to parse as UUID (handles both string UUIDs and UUID objects)
            if isinstance(flow_id, uuid.UUID):
                parsed_flow_id = flow_id
            else:
                parsed_flow_id = uuid.UUID(flow_id)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid CrewAI Flow ID provided: {flow_id}, error: {e}")
            raise ValueError(f"Invalid CrewAI Flow ID: {flow_id}. Must be a valid UUID.")
        
        flow = DiscoveryFlow(
            flow_id=parsed_flow_id,  # Always use the REAL CrewAI Flow ID
            client_account_id=uuid.UUID(self.client_account_id) if self.client_account_id else demo_client_id,
            engagement_id=uuid.UUID(self.engagement_id) if self.engagement_id else demo_engagement_id,
            user_id=str(uuid.UUID(user_id)) if user_id else str(demo_user_id),
            import_session_id=uuid.UUID(import_session_id) if import_session_id else None,
            flow_name=f"Discovery Flow {flow_id[:8]}",
            status="active",
            crewai_state_data=metadata or {}
        )
        
        self.db.add(flow)
        await self.db.commit()
        await self.db.refresh(flow)
        
        return flow
    
    async def get_by_flow_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI Flow ID (single source of truth)"""
        try:
            # Convert flow_id to UUID for database query
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None
            
            # Convert context UUIDs (should already be valid from __init__)
            try:
                client_uuid = uuid.UUID(self.client_account_id)
                engagement_uuid = uuid.UUID(self.engagement_id)
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid context UUID - client: {self.client_account_id}, engagement: {self.engagement_id}, error: {e}")
                return None
            
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == client_uuid,
                    DiscoveryFlow.engagement_id == engagement_uuid
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id: {e}")
            return None
    
    async def get_by_flow_id_global(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI Flow ID without tenant filtering (for duplicate checking)"""
        try:
            # Convert flow_id to UUID for database query
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None
            
            stmt = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_uuid
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id_global: {e}")
            return None
    
    async def get_by_import_session_id(self, import_session_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by import session ID (for backward compatibility)"""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.import_session_id == uuid.UUID(import_session_id),
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id)
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_phase_completion(
        self, 
        flow_id: str, 
        phase: str, 
        data: Dict[str, Any],
        crew_status: Dict[str, Any] = None,
        agent_insights: List[Dict[str, Any]] = None,
        completed: bool = True
    ) -> DiscoveryFlow:
        """Update phase completion and store results"""
        
        # Build update values based on phase
        update_values = {
            "updated_at": datetime.utcnow()
        }
        
        # Set phase completion flag
        phase_completion_map = {
            "data_import": "data_import_completed",
            "attribute_mapping": "attribute_mapping_completed",
            "field_mapping": "attribute_mapping_completed",  # Alias for frontend compatibility
            "data_cleansing": "data_cleansing_completed",
            "inventory": "inventory_completed",
            "dependencies": "dependencies_completed",
            "tech_debt": "tech_debt_completed"
        }
        
        if phase in phase_completion_map:
            update_values[phase_completion_map[phase]] = completed
        
        # Store phase-specific data in crewai_state_data
        if data:
            # Get existing flow to merge data
            existing_flow = await self.get_by_flow_id(flow_id)
            if existing_flow:
                state_data = existing_flow.crewai_state_data or {}
                state_data[phase] = data
                if crew_status:
                    state_data["crew_status"] = crew_status
                if agent_insights:
                    state_data["agent_insights"] = agent_insights
                
                # Extract processing statistics to root level for API responses
                processing_fields = ['records_processed', 'records_total', 'records_valid', 'records_failed']
                for field in processing_fields:
                    if field in data:
                        state_data[field] = data[field]
                
                update_values["crewai_state_data"] = state_data
                
                # Set CrewAI persistence ID if not already set (for validation compatibility)
                if not existing_flow.crewai_persistence_id and data.get("validation_compatible"):
                    import uuid as uuid_pkg
                    update_values["crewai_persistence_id"] = uuid_pkg.uuid4()
        
        # Calculate progress percentage
        completed_phases = 0
        total_phases = 6
        
        # Check existing completion status and account for current update
        existing_flow = await self.get_by_flow_id(flow_id)
        if existing_flow:
            # Count existing completed phases, but override with current update if applicable
            if phase == "data_import":
                if completed: completed_phases += 1
            elif existing_flow.data_import_completed:
                completed_phases += 1
                
            if phase == "attribute_mapping" or phase == "field_mapping":
                if completed: completed_phases += 1
            elif existing_flow.attribute_mapping_completed:
                completed_phases += 1
                
            if phase == "data_cleansing":
                if completed: completed_phases += 1
            elif existing_flow.data_cleansing_completed:
                completed_phases += 1
                
            if phase == "inventory":
                if completed: completed_phases += 1
            elif existing_flow.inventory_completed:
                completed_phases += 1
                
            if phase == "dependencies":
                if completed: completed_phases += 1
            elif existing_flow.dependencies_completed:
                completed_phases += 1
                
            if phase == "tech_debt":
                if completed: completed_phases += 1
            elif existing_flow.tech_debt_completed:
                completed_phases += 1
        
        progress_percentage = (completed_phases / total_phases) * 100
        update_values["progress_percentage"] = min(progress_percentage, 100.0)
        
        # Execute update with multi-tenant filtering
        stmt = update(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id)
            )
        ).values(**update_values)
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated flow
        return await self.get_by_flow_id(flow_id)
    
    async def complete_discovery_flow(self, flow_id: str) -> DiscoveryFlow:
        """Mark discovery flow as completed and prepare for assessment"""
        
        flow = await self.get_by_flow_id(flow_id)
        if not flow:
            raise ValueError(f"Discovery flow not found: {flow_id}")
        
        # Note: Assets are now in the main assets table with discovery_flow_id reference
        # For now, create a basic assessment package without assets data
        # In a full implementation, you would import AssetRepository and fetch assets by discovery_flow_id
        
        assessment_package = {
            "assets": [],  # Would need AssetRepository to fetch discovery assets
            "summary": {
                "total_assets": 0,  # Would be calculated from assets
                "asset_types": {},
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
                "quality_metrics": {
                    "avg_confidence_score": 0.0,
                    "validation_status_distribution": {}
                }
            },
            "ready_for_assessment": True,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Update flow status
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
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id)
            )
        ).values(**update_values)
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        return await self.get_by_flow_id(flow_id)
    
    async def get_active_flows(self) -> List[DiscoveryFlow]:
        """Get all active discovery flows for the client/engagement"""
        # Include phase names that may have been incorrectly set as status
        # This handles legacy data where phase names were used as status
        valid_active_statuses = [
            "initialized", "active", "running", "paused",
            # Phase names that might have been set as status by mistake
            "data_import", "attribute_mapping", "field_mapping", 
            "data_cleansing", "inventory", "dependencies", "tech_debt"
        ]
        
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id),
                DiscoveryFlow.status.in_(valid_active_statuses)
            )
        ).order_by(desc(DiscoveryFlow.created_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_incomplete_flows(self) -> List[DiscoveryFlow]:
        """
        Get all incomplete discovery flows that should block new uploads.
        This includes flows with status 'active', 'running', 'paused', and 'completed' flows that are not actually complete.
        """
        # Include phase names that may have been incorrectly set as status
        valid_statuses = [
            "initialized", "active", "running", "paused", "completed",
            # Phase names that might have been set as status by mistake
            "data_import", "attribute_mapping", "field_mapping",
            "data_cleansing", "inventory", "dependencies", "tech_debt"
        ]
        
        # First get all non-failed flows
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id),
                DiscoveryFlow.status.in_(valid_statuses)
            )
        ).order_by(desc(DiscoveryFlow.created_at))
        
        result = await self.db.execute(stmt)
        all_flows = result.scalars().all()
        
        # Filter to only truly incomplete flows
        incomplete_flows = []
        non_final_statuses = [
            "active", "running", "paused",
            # Phase names that might have been set as status
            "data_import", "attribute_mapping", "field_mapping",
            "data_cleansing", "inventory", "dependencies", "tech_debt"
        ]
        
        for flow in all_flows:
            # Include flows that are not complete OR have non-final status
            if not flow.is_complete() or flow.status in non_final_statuses:
                incomplete_flows.append(flow)
        
        return incomplete_flows
    
    async def get_completed_flows(self, limit: int = 10) -> List[DiscoveryFlow]:
        """Get completed discovery flows for the client/engagement"""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id),
                DiscoveryFlow.status == "completed"
            )
        ).order_by(desc(DiscoveryFlow.completed_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_flow(self, flow_id: str) -> bool:
        """Delete discovery flow and all associated assets"""
        stmt = delete(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id)
            )
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        return result.rowcount > 0
    
    # Master Flow Coordination Methods - Task 5.1.2
    
    async def get_by_master_flow_id(self, master_flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by master flow ID."""
        try:
            master_flow_uuid = uuid.UUID(master_flow_id)
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
            
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.master_flow_id == master_flow_uuid,
                    DiscoveryFlow.client_account_id == client_uuid,
                    DiscoveryFlow.engagement_id == engagement_uuid
                )
            )
            
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid UUID format - master_flow_id: {master_flow_id}, error: {e}")
            return None
    
    async def update_master_flow_reference(self, flow_id: str, master_flow_id: str) -> bool:
        """Update discovery flow with master flow reference."""
        try:
            flow_uuid = uuid.UUID(flow_id)
            master_flow_uuid = uuid.UUID(master_flow_id)
            
            stmt = update(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_uuid
            ).values(
                master_flow_id=master_flow_uuid,
                updated_at=datetime.utcnow()
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid UUID format in update_master_flow_reference: {e}")
            return False
    
    async def get_master_flow_coordination_summary(self) -> Dict[str, Any]:
        """Get summary of master flow coordination status."""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
            
            # Get discovery flows with master flow coordination
            stmt = select(
                func.count(DiscoveryFlow.id).label('total_flows'),
                func.count(DiscoveryFlow.master_flow_id).label('flows_with_master'),
                func.count(func.distinct(DiscoveryFlow.master_flow_id)).label('unique_master_flows')
            ).where(
                and_(
                    DiscoveryFlow.client_account_id == client_uuid,
                    DiscoveryFlow.engagement_id == engagement_uuid
                )
            )
            
            result = await self.db.execute(stmt)
            stats = result.first()
            
            # Get phase distribution
            phase_stmt = select(
                DiscoveryFlow.status,
                func.count(DiscoveryFlow.id).label('count')
            ).where(
                and_(
                    DiscoveryFlow.client_account_id == client_uuid,
                    DiscoveryFlow.engagement_id == engagement_uuid
                )
            ).group_by(DiscoveryFlow.status)
            
            phase_result = await self.db.execute(phase_stmt)
            phase_stats = {row.status: row.count for row in phase_result}
            
            return {
                'total_discovery_flows': stats.total_flows,
                'flows_with_master_coordination': stats.flows_with_master,
                'unique_master_flows': stats.unique_master_flows,
                'coordination_percentage': (stats.flows_with_master / stats.total_flows * 100) if stats.total_flows > 0 else 0,
                'phase_distribution': phase_stats
            }
            
        except Exception as e:
            logger.error(f"Error in get_master_flow_coordination_summary: {e}")
            return {
                'total_discovery_flows': 0,
                'flows_with_master_coordination': 0,
                'unique_master_flows': 0,
                'coordination_percentage': 0,
                'phase_distribution': {}
            }
    
    async def transition_to_assessment_phase(self, flow_id: str, assessment_flow_id: str) -> bool:
        """Prepare discovery flow for assessment phase transition."""
        try:
            flow = await self.get_by_flow_id(flow_id)
            if not flow:
                return False
            
            # Update status and add assessment transition data
            state_data = flow.crewai_state_data or {}
            state_data['assessment_transition'] = {
                'assessment_flow_id': assessment_flow_id,
                'transition_timestamp': datetime.utcnow().isoformat(),
                'discovery_completion_status': 'ready_for_assessment'
            }
            
            stmt = update(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == uuid.UUID(flow_id)
            ).values(
                status='transition_to_assessment',
                crewai_state_data=state_data,
                updated_at=datetime.utcnow()
            )
            
            await self.db.execute(stmt)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in transition_to_assessment_phase: {e}")
            return False


class DiscoveryAssetRepository(ContextAwareRepository):
    """
    Repository for discovery assets
    Created automatically from Discovery Flow results
    """
    
    def __init__(self, db: AsyncSession, client_account_id: str, engagement_id: str = None):
        context = {
            'client_account_id': uuid.UUID(client_account_id) if client_account_id else uuid.UUID("11111111-1111-1111-1111-111111111111"),
            'engagement_id': uuid.UUID(engagement_id) if engagement_id else uuid.UUID("22222222-2222-2222-2222-222222222222")
        }
        super().__init__(db, context)
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id or client_account_id
    
    async def create_assets_from_discovery(
        self, 
        discovery_flow_id: uuid.UUID, 
        asset_data_list: List[Dict[str, Any]],
        discovered_in_phase: str = "inventory"
    ) -> List[DiscoveryAsset]:
        """Create DiscoveryAsset records from flow results"""
        
        assets = []
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        
        for asset_data in asset_data_list:
            asset = DiscoveryAsset(
                discovery_flow_id=discovery_flow_id,
                client_account_id=uuid.UUID(self.client_account_id) if self.client_account_id else demo_client_id,
                engagement_id=uuid.UUID(self.engagement_id) if self.engagement_id else demo_engagement_id,
                asset_name=asset_data.get('name', 'Unknown'),
                asset_type=asset_data.get('type', 'unknown'),
                asset_subtype=asset_data.get('subtype'),
                asset_data=asset_data,
                discovered_in_phase=discovered_in_phase,
                discovery_method="crewai_discovery_flow",
                # quality_score field doesn't exist in DiscoveryAsset model
                confidence_score=asset_data.get('confidence_score', 0.0),
                validation_status="pending"
            )
            
            self.db.add(asset)
            assets.append(asset)
        
        await self.db.commit()
        
        # Refresh all assets
        for asset in assets:
            await self.db.refresh(asset)
        
        return assets
    
    async def get_assets_by_flow_id(self, discovery_flow_id: uuid.UUID) -> List[DiscoveryAsset]:
        """Get all assets for a discovery flow"""
        stmt = select(DiscoveryAsset).where(
            and_(
                DiscoveryAsset.discovery_flow_id == discovery_flow_id,
                DiscoveryAsset.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryAsset.engagement_id == uuid.UUID(self.engagement_id)
            )
        ).order_by(DiscoveryAsset.created_at)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_assets_by_type(self, asset_type: str) -> List[DiscoveryAsset]:
        """Get assets by type for the client/engagement"""
        stmt = select(DiscoveryAsset).where(
            and_(
                DiscoveryAsset.asset_type == asset_type,
                DiscoveryAsset.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryAsset.engagement_id == uuid.UUID(self.engagement_id)
            )
        ).order_by(DiscoveryAsset.asset_name)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_asset_validation(
        self, 
        asset_id: uuid.UUID, 
        validation_status: str,
        validation_results: Dict[str, Any] = None
    ) -> DiscoveryAsset:
        """Update asset validation status and results"""
        
        update_values = {
            "validation_status": validation_status,
            "updated_at": datetime.utcnow()
        }
        
        if validation_results:
            update_values["validation_results"] = validation_results
        
        stmt = update(DiscoveryAsset).where(
            and_(
                DiscoveryAsset.id == asset_id,
                DiscoveryAsset.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryAsset.engagement_id == uuid.UUID(self.engagement_id)
            )
        ).values(**update_values)
        
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated asset
        result = await self.db.execute(
            select(DiscoveryAsset).where(DiscoveryAsset.id == asset_id)
        )
        return result.scalar_one_or_none() 