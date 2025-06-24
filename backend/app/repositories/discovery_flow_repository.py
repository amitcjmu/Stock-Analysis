"""
Discovery Flow Repository
Repository for new discovery flow tables following ContextAwareRepository pattern.
Follows the Multi-Flow Architecture Implementation Plan.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, desc, func
from sqlalchemy.orm import selectinload

from app.repositories.base_repository import ContextAwareRepository
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset


class DiscoveryFlowRepository(ContextAwareRepository):
    """
    Repository for new discovery flow tables
    Uses CrewAI Flow ID as single source of truth (no session_id confusion)
    """
    
    def __init__(self, db: AsyncSession, client_account_id: str, engagement_id: str = None):
        context = {
            'client_account_id': uuid.UUID(client_account_id) if client_account_id else uuid.UUID("11111111-1111-1111-1111-111111111111"),
            'engagement_id': uuid.UUID(engagement_id) if engagement_id else uuid.UUID("22222222-2222-2222-2222-222222222222")
        }
        super().__init__(db, context)
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id or client_account_id  # Fallback for compatibility
    
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
        
        flow = DiscoveryFlow(
            flow_id=uuid.UUID(flow_id) if len(flow_id) == 36 else uuid.uuid4(),  # Handle both UUID and string flow IDs
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
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id)
            )
        ).options(selectinload(DiscoveryFlow.assets))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_flow_id_global(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI Flow ID without tenant filtering (for duplicate checking)"""
        stmt = select(DiscoveryFlow).where(
            DiscoveryFlow.flow_id == flow_id
        ).options(selectinload(DiscoveryFlow.assets))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_import_session_id(self, import_session_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by import session ID (for backward compatibility)"""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.import_session_id == uuid.UUID(import_session_id),
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id)
            )
        ).options(selectinload(DiscoveryFlow.assets))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_phase_completion(
        self, 
        flow_id: str, 
        phase: str, 
        data: Dict[str, Any],
        crew_status: Dict[str, Any] = None,
        agent_insights: List[Dict[str, Any]] = None
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
            "data_cleansing": "data_cleansing_completed",
            "inventory": "inventory_completed",
            "dependencies": "dependencies_completed",
            "tech_debt": "tech_debt_completed"
        }
        
        if phase in phase_completion_map:
            update_values[phase_completion_map[phase]] = True
        
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
                update_values["crewai_state_data"] = state_data
        
        # Calculate progress percentage
        completed_phases = 0
        total_phases = 6
        for phase_field in phase_completion_map.values():
            if update_values.get(phase_field, False):
                completed_phases += 1
        
        # Check existing completion status
        existing_flow = await self.get_by_flow_id(flow_id)
        if existing_flow:
            if existing_flow.data_import_completed: completed_phases += 1
            if existing_flow.attribute_mapping_completed and phase != "attribute_mapping": completed_phases += 1
            if existing_flow.data_cleansing_completed and phase != "data_cleansing": completed_phases += 1
            if existing_flow.inventory_completed and phase != "inventory": completed_phases += 1
            if existing_flow.dependencies_completed and phase != "dependencies": completed_phases += 1
            if existing_flow.tech_debt_completed and phase != "tech_debt": completed_phases += 1
        
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
        
        # Prepare assessment handoff data
        assessment_package = {
            "assets": [asset.to_dict() for asset in flow.assets],
            "summary": {
                "total_assets": len(flow.assets),
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
        
        # Calculate quality metrics
        if flow.assets:
            total_confidence = sum(asset.confidence_score or 0.0 for asset in flow.assets)
            assessment_package["summary"]["quality_metrics"]["avg_confidence_score"] = total_confidence / len(flow.assets)
            # Remove avg_quality_score as it doesn't exist in DiscoveryAsset model
            del assessment_package["summary"]["quality_metrics"]["avg_quality_score"]
            
            # Asset type distribution
            asset_types = {}
            validation_status = {}
            for asset in flow.assets:
                asset_types[asset.asset_type] = asset_types.get(asset.asset_type, 0) + 1
                validation_status[asset.validation_status] = validation_status.get(asset.validation_status, 0) + 1
            
            assessment_package["summary"]["asset_types"] = asset_types
            assessment_package["summary"]["quality_metrics"]["validation_status_distribution"] = validation_status
        
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
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id),
                DiscoveryFlow.status.in_(["active", "running", "paused"])
            )
        ).options(selectinload(DiscoveryFlow.assets)).order_by(desc(DiscoveryFlow.created_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_completed_flows(self, limit: int = 10) -> List[DiscoveryFlow]:
        """Get completed discovery flows for the client/engagement"""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == uuid.UUID(self.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.engagement_id),
                DiscoveryFlow.status == "completed"
            )
        ).options(selectinload(DiscoveryFlow.assets)).order_by(desc(DiscoveryFlow.completed_at)).limit(limit)
        
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