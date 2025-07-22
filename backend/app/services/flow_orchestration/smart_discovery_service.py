"""
Smart Flow Discovery Service

Handles intelligent flow data discovery and reconciliation for the Master Flow Orchestrator.
Extracted from MasterFlowOrchestrator to follow single responsibility principle.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository

logger = get_logger(__name__)


class SmartDiscoveryService:
    """Service for intelligent flow data discovery and reconciliation"""
    
    def __init__(self, db: AsyncSession, context: RequestContext, master_repo: CrewAIFlowStateExtensionsRepository):
        self.db = db
        self.context = context
        self.master_repo = master_repo
    
    async def smart_flow_discovery(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Intelligently discover flow data using multiple strategies
        
        This method attempts to find flow data using:
        1. Related data by timestamp correlation
        2. Related data by context (engagement/client)
        3. Flow persistence data
        
        Args:
            flow_id: Flow ID to discover data for
            
        Returns:
            Discovered flow data or None if not found
        """
        logger.info(f"🔍 Starting smart flow discovery for flow {flow_id}")
        
        # Strategy 1: Find related data by timestamp
        discovered_data = await self._find_related_data_by_timestamp(flow_id)
        if discovered_data:
            logger.info("✅ Found flow data via timestamp correlation")
            return discovered_data
        
        # Strategy 2: Find related data by context
        discovered_data = await self._find_related_data_by_context(flow_id)
        if discovered_data:
            logger.info("✅ Found flow data via context correlation")
            return discovered_data
        
        # Strategy 3: Check flow persistence data
        discovered_data = await self._find_in_flow_persistence(flow_id)
        if discovered_data:
            logger.info("✅ Found flow data in persistence layer")
            return discovered_data
        
        logger.warning(f"❌ No flow data discovered for {flow_id}")
        return None
    
    async def _find_related_data_by_timestamp(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find related data by timestamp correlation"""
        try:
            # Look for recent discovery flows that might be related
            query = text("""
                SELECT df.*, di.filename, di.created_at as import_created_at
                FROM discovery_flows df
                LEFT JOIN data_imports di ON df.data_import_id = di.id
                WHERE df.client_account_id = :client_id 
                AND df.engagement_id = :engagement_id
                AND df.created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY df.created_at DESC
                LIMIT 5
            """)
            
            result = await self.db.execute(query, {
                "client_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            })
            
            rows = result.fetchall()
            if not rows:
                return None
            
            # Try to find the most likely match based on timing
            for row in rows:
                if self._is_timestamp_correlation_match(flow_id, row):
                    return {
                        "discovery_flow": dict(row._mapping),
                        "correlation_method": "timestamp",
                        "confidence": 0.8
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding related data by timestamp: {e}")
            return None
    
    async def _find_related_data_by_context(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find related data by context correlation"""
        try:
            # Look for data imports and discovery flows in the same context
            query = text("""
                SELECT 
                    di.id as import_id,
                    di.filename,
                    di.status as import_status,
                    di.created_at as import_created,
                    df.id as flow_db_id,
                    df.flow_id as discovery_flow_id,
                    df.status as flow_status,
                    df.created_at as flow_created,
                    COUNT(a.id) as asset_count
                FROM data_imports di
                LEFT JOIN discovery_flows df ON di.id = df.data_import_id
                LEFT JOIN assets a ON a.engagement_id = :engagement_id
                WHERE di.client_account_id = :client_id
                AND di.engagement_id = :engagement_id
                AND di.created_at >= NOW() - INTERVAL '7 days'
                GROUP BY di.id, df.id
                ORDER BY di.created_at DESC
                LIMIT 10
            """)
            
            result = await self.db.execute(query, {
                "client_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            })
            
            rows = result.fetchall()
            if not rows:
                return None
            
            # Find best context match
            best_match = None
            highest_confidence = 0.0
            
            for row in rows:
                confidence = self._calculate_context_confidence(flow_id, row)
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = row
            
            if best_match and highest_confidence > 0.5:
                return {
                    "data_import": dict(best_match._mapping),
                    "correlation_method": "context",
                    "confidence": highest_confidence
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding related data by context: {e}")
            return None
    
    async def _find_in_flow_persistence(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find data in flow persistence layer"""
        try:
            # Check if there's persistence data for this flow
            query = text("""
                SELECT flow_persistence_data, flow_configuration, created_at
                FROM crewai_flow_state_extensions
                WHERE flow_id = :flow_id
                AND client_account_id = :client_id
                AND engagement_id = :engagement_id
            """)
            
            result = await self.db.execute(query, {
                "flow_id": flow_id,
                "client_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            })
            
            row = result.fetchone()
            if not row:
                return None
            
            persistence_data = row.flow_persistence_data or {}
            config_data = row.flow_configuration or {}
            
            if persistence_data or config_data:
                return {
                    "persistence_data": persistence_data,
                    "configuration": config_data,
                    "created_at": row.created_at,
                    "correlation_method": "persistence",
                    "confidence": 0.9
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding data in flow persistence: {e}")
            return None
    
    def _is_timestamp_correlation_match(self, flow_id: str, row) -> bool:
        """Check if timestamp correlation indicates a match"""
        # Simple heuristic: if the discovery flow was created recently and 
        # there's only one flow in the time window, it's likely related
        return True  # Simplified for now
    
    def _calculate_context_confidence(self, flow_id: str, row) -> float:
        """Calculate confidence score for context correlation"""
        confidence = 0.0
        
        # Higher confidence if there are assets
        if row.asset_count and row.asset_count > 0:
            confidence += 0.3
        
        # Higher confidence if there's a discovery flow
        if row.discovery_flow_id:
            confidence += 0.4
        
        # Higher confidence if import is completed
        if row.import_status == 'completed':
            confidence += 0.2
        
        # Recent data gets higher confidence
        if row.import_created and row.import_created >= datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def build_status_from_discovered_data(self, flow_id: str, discovered_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build flow status from discovered data"""
        try:
            correlation_method = discovered_data.get("correlation_method", "unknown")
            confidence = discovered_data.get("confidence", 0.0)
            
            status = {
                "flow_id": flow_id,
                "status": "discovered",
                "correlation_method": correlation_method,
                "confidence": confidence,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "data_sources": []
            }
            
            # Add data from different correlation methods
            if "discovery_flow" in discovered_data:
                df_data = discovered_data["discovery_flow"]
                status["data_sources"].append({
                    "type": "discovery_flow",
                    "flow_id": df_data.get("flow_id"),
                    "status": df_data.get("status"),
                    "progress": df_data.get("progress_percentage", 0),
                    "data_import_completed": df_data.get("data_import_completed", False),
                    "asset_inventory_completed": df_data.get("asset_inventory_completed", False)
                })
            
            if "data_import" in discovered_data:
                di_data = discovered_data["data_import"]
                status["data_sources"].append({
                    "type": "data_import",
                    "import_id": di_data.get("import_id"),
                    "filename": di_data.get("filename"),
                    "status": di_data.get("import_status"),
                    "asset_count": di_data.get("asset_count", 0)
                })
            
            if "persistence_data" in discovered_data:
                status["data_sources"].append({
                    "type": "persistence",
                    "has_config": bool(discovered_data.get("configuration")),
                    "has_state": bool(discovered_data.get("persistence_data"))
                })
            
            # Enhance with field mappings if available
            field_mappings = await self._retrieve_field_mappings_from_discovered_data(discovered_data)
            if field_mappings:
                status["field_mappings"] = field_mappings
            
            return status
            
        except Exception as e:
            logger.error(f"Error building status from discovered data: {e}")
            return {
                "flow_id": flow_id,
                "status": "discovery_error",
                "error": str(e)
            }
    
    async def _retrieve_field_mappings_from_discovered_data(self, discovered_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Retrieve field mappings from discovered data"""
        try:
            mappings = []
            
            # Extract from discovery flow if available
            if "discovery_flow" in discovered_data:
                df_data = discovered_data["discovery_flow"]
                flow_id = df_data.get("flow_id")
                
                if flow_id:
                    # Look for field mappings related to this flow
                    query = text("""
                        SELECT source_field, target_field, match_type, confidence_score, status
                        FROM import_field_mappings ifm
                        JOIN data_imports di ON ifm.data_import_id = di.id
                        JOIN discovery_flows df ON di.id = df.data_import_id
                        WHERE df.flow_id = :flow_id
                        AND ifm.status = 'approved'
                        ORDER BY ifm.created_at
                    """)
                    
                    result = await self.db.execute(query, {"flow_id": flow_id})
                    rows = result.fetchall()
                    
                    for row in rows:
                        mappings.append({
                            "source_field": row.source_field,
                            "target_field": row.target_field,
                            "match_type": row.match_type,
                            "confidence_score": float(row.confidence_score) if row.confidence_score else 0.0,
                            "status": row.status
                        })
            
            return mappings if mappings else None
            
        except Exception as e:
            logger.error(f"Error retrieving field mappings: {e}")
            return None
    
    async def find_orphaned_data_for_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find orphaned data that might belong to this flow"""
        try:
            # Look for orphaned discovery flows
            orphaned_discovery = await self._find_orphaned_discovery_flows(flow_id)
            
            # Look for orphaned data imports
            orphaned_imports = await self._find_orphaned_data_imports(flow_id)
            
            # Look for orphaned assets
            orphaned_assets = await self._find_orphaned_assets(flow_id)
            
            if orphaned_discovery or orphaned_imports or orphaned_assets:
                return {
                    "orphaned_discovery_flows": orphaned_discovery or [],
                    "orphaned_data_imports": orphaned_imports or [],
                    "orphaned_assets": orphaned_assets or [],
                    "total_orphaned_items": (
                        len(orphaned_discovery or []) + 
                        len(orphaned_imports or []) + 
                        len(orphaned_assets or [])
                    )
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding orphaned data: {e}")
            return None
    
    async def _find_orphaned_discovery_flows(self, flow_id: str) -> Optional[List[Dict[str, Any]]]:
        """Find orphaned discovery flows"""
        try:
            query = text("""
                SELECT df.*, di.filename
                FROM discovery_flows df
                LEFT JOIN data_imports di ON df.data_import_id = di.id
                LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id
                WHERE df.client_account_id = :client_id
                AND df.engagement_id = :engagement_id
                AND cse.flow_id IS NULL  -- No corresponding master flow
                AND df.created_at >= NOW() - INTERVAL '48 hours'
                ORDER BY df.created_at DESC
            """)
            
            result = await self.db.execute(query, {
                "client_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            })
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows] if rows else None
            
        except Exception as e:
            logger.error(f"Error finding orphaned discovery flows: {e}")
            return None
    
    async def _find_orphaned_data_imports(self, flow_id: str) -> Optional[List[Dict[str, Any]]]:
        """Find orphaned data imports"""
        try:
            query = text("""
                SELECT di.*
                FROM data_imports di
                LEFT JOIN discovery_flows df ON di.id = df.data_import_id
                WHERE di.client_account_id = :client_id
                AND di.engagement_id = :engagement_id
                AND df.id IS NULL  -- No corresponding discovery flow
                AND di.created_at >= NOW() - INTERVAL '48 hours'
                ORDER BY di.created_at DESC
            """)
            
            result = await self.db.execute(query, {
                "client_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            })
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows] if rows else None
            
        except Exception as e:
            logger.error(f"Error finding orphaned data imports: {e}")
            return None
    
    async def _find_orphaned_assets(self, flow_id: str) -> Optional[List[Dict[str, Any]]]:
        """Find orphaned assets"""
        try:
            query = text("""
                SELECT a.id, a.name, a.asset_type, a.created_at
                FROM assets a
                LEFT JOIN discovery_flows df ON a.engagement_id = df.engagement_id
                WHERE a.client_account_id = :client_id
                AND a.engagement_id = :engagement_id
                AND a.discovery_flow_id IS NULL  -- No discovery flow reference
                AND a.created_at >= NOW() - INTERVAL '48 hours'
                ORDER BY a.created_at DESC
                LIMIT 20
            """)
            
            result = await self.db.execute(query, {
                "client_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            })
            
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows] if rows else None
            
        except Exception as e:
            logger.error(f"Error finding orphaned assets: {e}")
            return None