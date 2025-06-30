"""
Discovery Flow Service
Service layer for new discovery flow tables.
Follows the Multi-Flow Architecture Implementation Plan.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.repositories.discovery_flow_repository import DiscoveryFlowRepository, DiscoveryAssetRepository
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset
from app.core.context import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DiscoveryFlowService:
    """
    Service layer for discovery flows using new database architecture.
    Integrates with CrewAI flows and maintains enterprise features.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        
        # Initialize repositories with multi-tenant context
        self.master_flow_repo = CrewAIFlowStateExtensionsRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id)
        )
        
        self.flow_repo = DiscoveryFlowRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id)
        )
        
        self.asset_repo = DiscoveryAssetRepository(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id)
        )
    
    async def create_discovery_flow(
        self,
        flow_id: str,  # CrewAI generated flow ID - single source of truth
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
        data_import_id: str = None,
        user_id: str = None
    ) -> DiscoveryFlow:
        """
        Create a new discovery flow and ensure corresponding crewai_flow_state_extensions record.
        
        Simple Architecture:
        1. Create discovery flow in discovery_flows table with flow_id = X
        2. Create crewai_flow_state_extensions record with same flow_id = X  
        3. Both tables linked by having the same flow_id value
        
        This ensures crewai_flow_state_extensions is populated for flow coordination.
        """
        try:
            logger.info(f"🚀 Creating discovery flow and extensions record: {flow_id}")
            
            # Validate input
            if not flow_id:
                raise ValueError("CrewAI Flow ID is required")
            
            if not raw_data:
                raise ValueError("Raw data is required for discovery flow")
            
            # Check if flow already exists (global check to handle duplicates)
            existing_flow = await self.flow_repo.get_by_flow_id_global(flow_id)
            if existing_flow:
                logger.info(f"✅ Discovery flow already exists globally, returning existing: {flow_id}")
                return existing_flow
            
            # Step 1: Create discovery flow in discovery_flows table
            logger.info(f"🔧 Creating discovery flow: {flow_id}")
            
            discovery_flow = await self.flow_repo.create_discovery_flow(
                flow_id=flow_id,
                import_session_id=data_import_id,
                user_id=user_id or str(self.context.user_id),
                raw_data=raw_data,
                metadata=metadata or {}
            )
            
            # Step 2: Create corresponding crewai_flow_state_extensions record with same flow_id
            logger.info(f"🔧 Creating crewai_flow_state_extensions record: {flow_id}")
            
            try:
                extensions_record = await self.master_flow_repo.create_master_flow(
                    flow_id=flow_id,  # Same flow_id as discovery flow
                    flow_type="discovery",
                    user_id=user_id or str(self.context.user_id),
                    flow_name=f"Discovery Flow {flow_id[:8]}",
                    flow_configuration={
                        "data_import_id": data_import_id,
                        "raw_data_count": len(raw_data),
                        "metadata": metadata or {}
                    },
                    initial_state={
                        "created_from": "discovery_flow_service",
                        "raw_data_sample": raw_data[:2] if raw_data else [],
                        "creation_timestamp": datetime.utcnow().isoformat()
                    }
                )
                logger.info(f"✅ Extensions record created: {extensions_record.flow_id}")
            except Exception as ext_error:
                logger.warning(f"⚠️ Failed to create extensions record (non-critical): {ext_error}")
                # Don't fail the whole operation if extensions creation fails
            
            logger.info(f"✅ Discovery flow created successfully: {flow_id}")
            logger.info(f"   Discovery flow: discovery_flows.flow_id = {flow_id}")
            logger.info(f"   Extensions: crewai_flow_state_extensions.flow_id = {flow_id}")
            
            return discovery_flow
            
        except Exception as e:
            logger.error(f"❌ Failed to create discovery flow: {e}")
            raise
    
    async def create_or_get_discovery_flow(
        self,
        flow_id: str,
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
        data_import_id: str = None,
        user_id: str = None
    ) -> DiscoveryFlow:
        """
        Create a new discovery flow or return existing one if it already exists.
        This is the preferred method for flow creation from CrewAI flows.
        """
        return await self.create_discovery_flow(
            flow_id=flow_id,
            raw_data=raw_data,
            metadata=metadata,
            data_import_id=data_import_id,
            user_id=user_id
        )
    
    async def get_flow_by_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI Flow ID (single source of truth)"""
        try:
            flow = await self.flow_repo.get_by_flow_id(flow_id)
            if flow:
                logger.info(f"✅ Discovery flow found: {flow_id}, next phase: {flow.get_next_phase()}")
            else:
                logger.warning(f"⚠️ Discovery flow not found: {flow_id}")
            
            return flow
            
        except Exception as e:
            logger.error(f"❌ Failed to get discovery flow {flow_id}: {e}")
            raise
    
    async def get_flow_by_import_session(self, import_session_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by import session ID (for backward compatibility)"""
        try:
            flow = await self.flow_repo.get_by_import_session_id(import_session_id)
            if flow:
                logger.info(f"✅ Discovery flow found by import session: {import_session_id} -> {flow.flow_id}")
            else:
                logger.warning(f"⚠️ Discovery flow not found for import session: {import_session_id}")
            
            return flow
            
        except Exception as e:
            logger.error(f"❌ Failed to get discovery flow by import session {import_session_id}: {e}")
            raise
    
    async def update_phase_completion(
        self,
        flow_id: str,
        phase: str,
        phase_data: Dict[str, Any],
        crew_status: Dict[str, Any] = None,
        agent_insights: List[Dict[str, Any]] = None
    ) -> DiscoveryFlow:
        """
        Update phase completion and store results.
        Integrates with CrewAI crew coordination.
        """
        try:
            logger.info(f"🔄 Updating phase completion: {flow_id}, phase: {phase}")
            
            # Validate phase
            valid_phases = ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]
            if phase not in valid_phases:
                raise ValueError(f"Invalid phase: {phase}. Valid phases: {valid_phases}")
            
            # Update phase completion
            flow = await self.flow_repo.update_phase_completion(
                flow_id=flow_id,
                phase=phase,
                data=phase_data,
                crew_status=crew_status,
                agent_insights=agent_insights
            )
            
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")
            
            # Create assets if this is the inventory phase
            if phase == "inventory" and phase_data.get("assets"):
                await self._create_assets_from_inventory(flow, phase_data["assets"])
            
            logger.info(f"✅ Phase completion updated: {flow_id}, phase: {phase}, progress: {flow.progress_percentage}%")
            return flow
            
        except Exception as e:
            logger.error(f"❌ Failed to update phase completion for {flow_id}: {e}")
            raise
    
    async def complete_discovery_flow(self, flow_id: str) -> DiscoveryFlow:
        """
        Complete discovery flow and prepare assessment handoff package.
        """
        try:
            logger.info(f"🏁 Completing discovery flow: {flow_id}")
            
            flow = await self.flow_repo.complete_discovery_flow(flow_id)
            
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")
            
            logger.info(f"✅ Discovery flow completed: {flow_id}, assets: {len(flow.assets)}")
            return flow
            
        except Exception as e:
            logger.error(f"❌ Failed to complete discovery flow {flow_id}: {e}")
            raise
    
    async def get_active_flows(self) -> List[DiscoveryFlow]:
        """Get all active discovery flows for the current client/engagement"""
        try:
            flows = await self.flow_repo.get_active_flows()
            logger.info(f"✅ Found {len(flows)} active discovery flows")
            return flows
            
        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            raise
    
    async def get_completed_flows(self, limit: int = 10) -> List[DiscoveryFlow]:
        """Get completed discovery flows for the current client/engagement"""
        try:
            flows = await self.flow_repo.get_completed_flows(limit)
            logger.info(f"✅ Found {len(flows)} completed discovery flows")
            return flows
            
        except Exception as e:
            logger.error(f"❌ Failed to get completed flows: {e}")
            raise
    
    async def get_flow_assets(self, flow_id: str) -> List[DiscoveryAsset]:
        """Get all assets for a discovery flow"""
        try:
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")
            
            assets = await self.asset_repo.get_assets_by_flow_id(flow.id)
            logger.info(f"✅ Found {len(assets)} assets for flow: {flow_id}")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to get assets for flow {flow_id}: {e}")
            raise
    
    async def get_assets_by_type(self, asset_type: str) -> List[DiscoveryAsset]:
        """Get assets by type for the current client/engagement"""
        try:
            assets = await self.asset_repo.get_assets_by_type(asset_type)
            logger.info(f"✅ Found {len(assets)} assets of type: {asset_type}")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to get assets by type {asset_type}: {e}")
            raise
    
    async def validate_asset(
        self,
        asset_id: uuid.UUID,
        validation_status: str,
        validation_results: Dict[str, Any] = None
    ) -> DiscoveryAsset:
        """Update asset validation status and results"""
        try:
            logger.info(f"🔍 Validating asset: {asset_id}, status: {validation_status}")
            
            valid_statuses = ["pending", "validated", "failed", "manual_review"]
            if validation_status not in valid_statuses:
                raise ValueError(f"Invalid validation status: {validation_status}")
            
            asset = await self.asset_repo.update_asset_validation(
                asset_id=asset_id,
                validation_status=validation_status,
                validation_results=validation_results
            )
            
            if not asset:
                raise ValueError(f"Asset not found: {asset_id}")
            
            logger.info(f"✅ Asset validation updated: {asset_id}")
            return asset
            
        except Exception as e:
            logger.error(f"❌ Failed to validate asset {asset_id}: {e}")
            raise
    
    async def delete_flow(self, flow_id: str) -> bool:
        """Delete discovery flow and all associated assets"""
        try:
            logger.info(f"🗑️ Deleting discovery flow: {flow_id}")
            
            deleted = await self.flow_repo.delete_flow(flow_id)
            
            if deleted:
                logger.info(f"✅ Discovery flow deleted: {flow_id}")
            else:
                logger.warning(f"⚠️ Discovery flow not found for deletion: {flow_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Failed to delete discovery flow {flow_id}: {e}")
            raise
    
    async def get_flow_summary(self, flow_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of the discovery flow"""
        try:
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Discovery flow not found: {flow_id}")
            
            assets = await self.get_flow_assets(flow_id)
            
            # Calculate summary statistics
            asset_type_counts = {}
            validation_status_counts = {}
            total_quality_score = 0.0
            total_confidence_score = 0.0
            
            for asset in assets:
                # Asset type distribution
                asset_type_counts[asset.asset_type] = asset_type_counts.get(asset.asset_type, 0) + 1
                
                # Validation status distribution
                validation_status_counts[asset.validation_status] = validation_status_counts.get(asset.validation_status, 0) + 1
                
                # Quality metrics
                total_quality_score += asset.quality_score or 0.0
                total_confidence_score += asset.confidence_score or 0.0
            
            avg_quality_score = total_quality_score / len(assets) if assets else 0.0
            avg_confidence_score = total_confidence_score / len(assets) if assets else 0.0
            
            # Phase completion status
            phase_completion = {
                "data_import": flow.data_import_completed,
                "attribute_mapping": flow.attribute_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "inventory": flow.inventory_completed,
                "dependencies": flow.dependencies_completed,
                "tech_debt": flow.tech_debt_completed
            }
            
            completed_phases = sum(1 for completed in phase_completion.values() if completed)
            
            summary = {
                "flow_id": flow.flow_id,
                "status": flow.status,
                "current_phase": flow.get_next_phase(),
                "progress_percentage": flow.progress_percentage,
                "phase_completion": phase_completion,
                "completed_phases": completed_phases,
                "total_phases": 6,
                "assets": {
                    "total_count": len(assets),
                    "type_distribution": asset_type_counts,
                    "validation_status_distribution": validation_status_counts,
                    "avg_quality_score": avg_quality_score,
                    "avg_confidence_score": avg_confidence_score
                },
                "timestamps": {
                    "created_at": flow.created_at.isoformat() if flow.created_at else None,
                    "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
                    "completed_at": flow.completed_at.isoformat() if flow.completed_at else None
                },
                "assessment_ready": flow.assessment_ready,
                "crewai_state": flow.crewai_state_data or {}
            }
            
            logger.info(f"✅ Flow summary generated: {flow_id}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to generate flow summary for {flow_id}: {e}")
            raise
    
    async def _create_assets_from_inventory(
        self,
        flow: DiscoveryFlow,
        asset_data_list: List[Dict[str, Any]]
    ) -> List[DiscoveryAsset]:
        """Create discovery assets from inventory phase results"""
        try:
            logger.info(f"📦 Creating {len(asset_data_list)} assets from inventory for flow: {flow.flow_id}")
            
            assets = await self.asset_repo.create_assets_from_discovery(
                discovery_flow_id=flow.id,
                asset_data_list=asset_data_list,
                discovered_in_phase="inventory"
            )
            
            logger.info(f"✅ Created {len(assets)} assets from inventory")
            return assets
            
        except Exception as e:
            logger.error(f"❌ Failed to create assets from inventory: {e}")
            raise


class DiscoveryFlowIntegrationService:
    """
    Integration service for bridging CrewAI flows with new database architecture.
    Handles the transition from existing unified flow to new tables.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.discovery_service = DiscoveryFlowService(db, context)
    
    async def create_flow_from_crewai(
        self,
        crewai_flow_id: str,
        crewai_state: Dict[str, Any],
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> DiscoveryFlow:
        """
        Create discovery flow from CrewAI flow initialization.
        Bridges CrewAI flow state with new database architecture.
        """
        try:
            logger.info(f"🔗 Creating discovery flow from CrewAI: {crewai_flow_id}")
            
            # Extract data import ID if available (for linking to import session)
            data_import_id = None
            if metadata and "data_import_id" in metadata:
                data_import_id = metadata["data_import_id"]
            elif metadata and "import_session_id" in metadata:
                # Backward compatibility - use import_session_id as data_import_id
                data_import_id = metadata["import_session_id"]
            elif crewai_state and "session_id" in crewai_state:
                # Backward compatibility - use session_id as data_import_id
                data_import_id = crewai_state["session_id"]
            
            # Create discovery flow using CrewAI Flow ID as single source of truth
            flow = await self.discovery_service.create_discovery_flow(
                flow_id=crewai_flow_id,
                raw_data=raw_data,
                metadata=metadata,
                data_import_id=data_import_id,
                user_id=str(self.context.user_id)
            )
            
            # Store CrewAI flow state for persistence integration
            if crewai_state:
                # Update flow with CrewAI state information
                await self.discovery_service.flow_repo.update_phase_completion(
                    flow_id=crewai_flow_id,
                    phase="data_import",
                    data={"crewai_state": crewai_state},
                    crew_status=crewai_state.get("crew_status", {}),
                    agent_insights=crewai_state.get("agent_insights", [])
                )
            
            logger.info(f"✅ Discovery flow created from CrewAI: {crewai_flow_id}")
            return flow
            
        except Exception as e:
            logger.error(f"❌ Failed to create flow from CrewAI {crewai_flow_id}: {e}")
            raise
    
    async def sync_crewai_state(
        self,
        flow_id: str,
        crewai_state: Dict[str, Any],
        phase: str = None
    ) -> DiscoveryFlow:
        """
        Sync CrewAI flow state with discovery flow database.
        Maintains hybrid persistence as described in the implementation plan.
        """
        try:
            logger.info(f"🔄 Syncing CrewAI state for flow: {flow_id}")
            
            current_phase = phase or crewai_state.get("current_phase", "data_import")
            
            # Extract phase-specific data from CrewAI state
            phase_data = {}
            if "field_mappings" in crewai_state:
                phase_data["field_mappings"] = crewai_state["field_mappings"]
            if "cleaned_data" in crewai_state:
                phase_data["cleaned_data"] = crewai_state["cleaned_data"]
            if "asset_inventory" in crewai_state:
                phase_data["asset_inventory"] = crewai_state["asset_inventory"]
            if "dependencies" in crewai_state:
                phase_data["dependencies"] = crewai_state["dependencies"]
            if "technical_debt" in crewai_state:
                phase_data["technical_debt"] = crewai_state["technical_debt"]
            
            # Update discovery flow with CrewAI state
            flow = await self.discovery_service.update_phase_completion(
                flow_id=flow_id,
                phase=current_phase,
                phase_data=phase_data,
                crew_status=crewai_state.get("crew_status", {}),
                agent_insights=crewai_state.get("agent_insights", [])
            )
            
            logger.info(f"✅ CrewAI state synced for flow: {flow_id}")
            return flow
            
        except Exception as e:
            logger.error(f"❌ Failed to sync CrewAI state for {flow_id}: {e}")
            raise 