"""
Discovery Flow State Manager
Handles persistence and retrieval of discovery flow state across phases
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.data_import_session import DataImportSession
from app.models.asset import Asset

logger = logging.getLogger(__name__)

class DiscoveryFlowStateManager:
    """Manages discovery flow state persistence across phases"""
    
    def __init__(self):
        self.active_flows: Dict[str, Dict[str, Any]] = {}
    
    async def initialize_flow_state(self, session_id: str, client_account_id: str, 
                                  engagement_id: str, user_id: str, 
                                  raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Initialize a new discovery flow state"""
        
        flow_state = {
            "session_id": session_id,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "user_id": user_id,
            "status": "running",
            "current_phase": "field_mapping",
            "progress_percentage": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            
            # Phase completion tracking
            "phase_completion": {
                "field_mapping": False,
                "data_cleansing": False,
                "inventory_building": False,
                "app_server_dependencies": False,
                "app_app_dependencies": False,
                "technical_debt": False
            },
            
            # Data flow between phases
            "raw_data": raw_data,
            "field_mappings": {},
            "cleaned_data": [],
            "asset_inventory": {
                "servers": [],
                "applications": [],
                "devices": []
            },
            "app_server_dependencies": {
                "hosting_relationships": [],
                "suggested_mappings": [],
                "confidence_scores": {}
            },
            "app_app_dependencies": {
                "communication_patterns": [],
                "application_clusters": [],
                "dependency_graph": {"nodes": [], "edges": []},
                "suggested_patterns": []
            },
            "technical_debt_assessment": {},
            
            # Crew status tracking
            "crew_status": {},
            "crew_results": {},
            
            # Database integration tracking
            "database_assets_created": [],
            "database_integration_status": "pending"
        }
        
        # Store in memory and database
        self.active_flows[session_id] = flow_state
        await self._persist_flow_state_to_database(session_id, flow_state)
        
        logger.info(f"✅ Flow state initialized for session: {session_id}")
        return flow_state
    
    async def update_phase_completion(self, session_id: str, phase: str, 
                                    results: Dict[str, Any]) -> Dict[str, Any]:
        """Update flow state when a phase completes"""
        
        if session_id not in self.active_flows:
            raise ValueError(f"Flow state not found for session: {session_id}")
        
        flow_state = self.active_flows[session_id]
        
        # Update phase completion
        flow_state["phase_completion"][phase] = True
        flow_state["crew_results"][phase] = results
        
        # Update phase-specific data
        if phase == "field_mapping":
            flow_state["field_mappings"] = results.get("field_mappings", {})
            flow_state["current_phase"] = "data_cleansing"
            flow_state["progress_percentage"] = 16.7
            
        elif phase == "data_cleansing":
            flow_state["cleaned_data"] = results.get("cleaned_data", [])
            flow_state["current_phase"] = "inventory_building"
            flow_state["progress_percentage"] = 33.3
            
        elif phase == "inventory_building":
            flow_state["asset_inventory"] = results.get("asset_inventory", {})
            flow_state["current_phase"] = "app_server_dependencies"
            flow_state["progress_percentage"] = 50.0
            
        elif phase == "app_server_dependencies":
            flow_state["app_server_dependencies"] = results.get("app_server_dependencies", {})
            flow_state["current_phase"] = "app_app_dependencies"
            flow_state["progress_percentage"] = 66.7
            
        elif phase == "app_app_dependencies":
            flow_state["app_app_dependencies"] = results.get("app_app_dependencies", {})
            flow_state["current_phase"] = "technical_debt"
            flow_state["progress_percentage"] = 83.3
            
        elif phase == "technical_debt":
            flow_state["technical_debt_assessment"] = results.get("technical_debt_assessment", {})
            flow_state["current_phase"] = "completed"
            flow_state["progress_percentage"] = 100.0
            flow_state["status"] = "completed"
            flow_state["completed_at"] = datetime.utcnow().isoformat()
        
        # Update timestamps
        flow_state["updated_at"] = datetime.utcnow().isoformat()
        
        # Persist updated state
        await self._persist_flow_state_to_database(session_id, flow_state)
        
        logger.info(f"✅ Phase {phase} completed for session: {session_id}")
        return flow_state
    
    async def get_flow_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current flow state"""
        
        # Try memory first
        if session_id in self.active_flows:
            return self.active_flows[session_id]
        
        # Try database
        flow_state = await self._load_flow_state_from_database(session_id)
        if flow_state:
            self.active_flows[session_id] = flow_state
            return flow_state
        
        return None
    
    async def persist_assets_to_database(self, session_id: str) -> Dict[str, Any]:
        """Persist processed assets to database"""
        
        flow_state = await self.get_flow_state(session_id)
        if not flow_state:
            raise ValueError(f"Flow state not found for session: {session_id}")
        
        asset_inventory = flow_state.get("asset_inventory", {})
        field_mappings = flow_state.get("field_mappings", {})
        
        created_asset_ids = []
        
        async with AsyncSessionLocal() as db_session:
            try:
                # Create assets from inventory
                for asset_type, assets in asset_inventory.items():
                    for asset_data in assets:
                        db_asset = Asset(
                            # Context
                            client_account_id=flow_state["client_account_id"],
                            engagement_id=flow_state["engagement_id"],
                            session_id=flow_state["session_id"],
                            
                            # Basic info
                            name=asset_data.get("name", f"Asset_{len(created_asset_ids) + 1}"),
                            hostname=asset_data.get("hostname"),
                            asset_type=asset_data.get("asset_type", "OTHER"),
                            
                            # Technical details
                            ip_address=asset_data.get("ip_address"),
                            operating_system=asset_data.get("operating_system"),
                            environment=asset_data.get("environment", "Unknown"),
                            cpu_cores=asset_data.get("cpu_cores"),
                            memory_gb=asset_data.get("memory_gb"),
                            storage_gb=asset_data.get("storage_gb"),
                            
                            # Business info
                            business_owner=asset_data.get("business_owner"),
                            department=asset_data.get("department"),
                            business_criticality=asset_data.get("business_criticality", "Medium"),
                            
                            # Migration info
                            six_r_strategy=asset_data.get("six_r_strategy", "rehost"),
                            migration_complexity=asset_data.get("migration_complexity", "Medium"),
                            sixr_ready=asset_data.get("sixr_ready", False),
                            
                            # Discovery metadata
                            discovery_method="crewai_discovery_flow",
                            discovery_source="discovery_flow_modular",
                            discovery_timestamp=datetime.utcnow(),
                            
                            # Import metadata
                            imported_by=flow_state["user_id"],
                            imported_at=datetime.utcnow(),
                            source_filename=f"discovery_flow_{session_id}",
                            raw_data=asset_data.get("raw_data", {}),
                            field_mappings_used=field_mappings,
                            
                            # Audit
                            created_at=datetime.utcnow(),
                            created_by=flow_state["user_id"]
                        )
                        
                        db_session.add(db_asset)
                        await db_session.flush()
                        created_asset_ids.append(str(db_asset.id))
                
                await db_session.commit()
                
                # Update flow state with created asset IDs
                flow_state["database_assets_created"] = created_asset_ids
                flow_state["database_integration_status"] = "completed"
                await self._persist_flow_state_to_database(session_id, flow_state)
                
                logger.info(f"✅ Created {len(created_asset_ids)} assets in database")
                
                return {
                    "status": "success",
                    "assets_created": len(created_asset_ids),
                    "asset_ids": created_asset_ids
                }
                
            except Exception as e:
                await db_session.rollback()
                logger.error(f"❌ Failed to persist assets: {e}")
                raise
    
    async def _persist_flow_state_to_database(self, session_id: str, flow_state: Dict[str, Any]):
        """Persist flow state to database session metadata"""
        
        async with AsyncSessionLocal() as db_session:
            try:
                # Update session with flow state
                stmt = update(DataImportSession).where(
                    DataImportSession.id == session_id
                ).values(
                    agent_insights=flow_state,
                    progress_percentage=int(flow_state.get("progress_percentage", 0)),
                    last_activity_at=datetime.utcnow()
                )
                
                await db_session.execute(stmt)
                await db_session.commit()
                
            except Exception as e:
                logger.error(f"Failed to persist flow state: {e}")
    
    async def _load_flow_state_from_database(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load flow state from database session metadata"""
        
        async with AsyncSessionLocal() as db_session:
            try:
                stmt = select(DataImportSession).where(
                    DataImportSession.id == session_id
                )
                result = await db_session.execute(stmt)
                session = result.scalar_one_or_none()
                
                if session and session.agent_insights:
                    return session.agent_insights
                
            except Exception as e:
                logger.error(f"Failed to load flow state: {e}")
        
        return None

# Global instance
flow_state_manager = DiscoveryFlowStateManager() 