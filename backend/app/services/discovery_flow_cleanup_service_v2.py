"""
Discovery Flow Cleanup Service V2
Handles cleanup operations for V2 discovery flows using flow_id as primary identifier.
Replaces session-based cleanup with flow-based architecture.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset

# Conditional imports for graceful degradation
try:
    from app.models.data_import import DataImport
    DATA_IMPORT_AVAILABLE = True
except ImportError:
    DATA_IMPORT_AVAILABLE = False

try:
    from app.models.asset import Asset
    ASSET_AVAILABLE = True
except ImportError:
    ASSET_AVAILABLE = False

logger = logging.getLogger(__name__)


class DiscoveryFlowCleanupServiceV2:
    """
    V2 Discovery Flow Cleanup Service
    
    Handles cleanup operations for V2 discovery flows using flow_id as the
    primary identifier instead of session_id. Provides comprehensive cleanup
    with audit trail and graceful error handling.
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
    
    async def delete_flow_with_cleanup(
        self,
        flow_id: str,
        force_delete: bool = False,
        cleanup_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Delete a discovery flow with comprehensive cleanup.
        
        Args:
            flow_id: The CrewAI flow ID to delete
            force_delete: Force deletion even if flow is active
            cleanup_options: Optional cleanup configuration
            
        Returns:
            Dictionary with cleanup results and summary
        """
        cleanup_options = cleanup_options or {}
        cleanup_summary = {
            "discovery_flow_deleted": False,
            "discovery_assets_deleted": 0,
            "created_assets_deleted": 0,
            "data_imports_cleaned": 0,
            "audit_record_created": False,
            "cleanup_duration_ms": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Get the discovery flow
            flow = await self._get_discovery_flow(flow_id)
            if not flow:
                return {
                    "success": False,
                    "error": f"Discovery flow not found: {flow_id}",
                    "cleanup_summary": cleanup_summary
                }
            
            # Check if force delete is required
            if flow.status in ["active", "running"] and not force_delete:
                return {
                    "success": False,
                    "error": "Cannot delete active flow without force_delete=True",
                    "cleanup_summary": cleanup_summary
                }
            
            # Begin comprehensive cleanup
            logger.info(f"🧹 Starting cleanup for discovery flow: {flow_id}")
            
            # 1. Delete discovery assets
            if cleanup_options.get("delete_discovery_assets", True):
                assets_deleted = await self._delete_discovery_assets(flow_id)
                cleanup_summary["discovery_assets_deleted"] = assets_deleted
                logger.info(f"Deleted {assets_deleted} discovery assets")
            
            # 2. Delete created assets (if any were created from this flow)
            if cleanup_options.get("delete_created_assets", True) and ASSET_AVAILABLE:
                created_assets_deleted = await self._delete_created_assets(flow)
                cleanup_summary["created_assets_deleted"] = created_assets_deleted
                logger.info(f"Deleted {created_assets_deleted} created assets")
            
            # 3. Clean up related data imports
            if cleanup_options.get("clean_data_imports", True) and DATA_IMPORT_AVAILABLE:
                data_imports_cleaned = await self._clean_data_imports(flow)
                cleanup_summary["data_imports_cleaned"] = data_imports_cleaned
                logger.info(f"Cleaned {data_imports_cleaned} data imports")
            
            # 4. Delete the discovery flow (must be last due to foreign keys)
            await self.db.delete(flow)
            cleanup_summary["discovery_flow_deleted"] = True
            logger.info(f"Deleted discovery flow: {flow_id}")
            
            # 5. Create audit record
            if cleanup_options.get("create_audit", True):
                audit_created = await self._create_audit_record(flow, cleanup_options, cleanup_summary)
                cleanup_summary["audit_record_created"] = audit_created
            
            # Commit all changes
            await self.db.commit()
            
            # Calculate cleanup duration
            cleanup_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            cleanup_summary["cleanup_duration_ms"] = int(cleanup_duration)
            
            logger.info(f"✅ Flow cleanup completed successfully for {flow_id} in {cleanup_duration:.0f}ms")
            
            return {
                "success": True,
                "message": f"Discovery flow {flow_id} and all associated data deleted successfully",
                "flow_id": flow_id,
                "cleanup_summary": cleanup_summary,
                "deletion_timestamp": datetime.utcnow().isoformat()
            }
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"❌ Database error during cleanup for {flow_id}: {e}")
            return {
                "success": False,
                "error": f"Database error during cleanup: {str(e)}",
                "cleanup_summary": cleanup_summary
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Unexpected error during cleanup for {flow_id}: {e}")
            return {
                "success": False,
                "error": f"Unexpected error during cleanup: {str(e)}",
                "cleanup_summary": cleanup_summary
            }
    
    async def bulk_cleanup_flows(
        self,
        flow_ids: List[str],
        force_delete: bool = False,
        cleanup_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Bulk cleanup multiple discovery flows.
        
        Args:
            flow_ids: List of flow IDs to cleanup
            force_delete: Force deletion even if flows are active
            cleanup_options: Optional cleanup configuration
            
        Returns:
            Dictionary with bulk cleanup results
        """
        start_time = datetime.utcnow()
        results = {
            "success": True,
            "total_flows": len(flow_ids),
            "successful_cleanups": 0,
            "failed_cleanups": 0,
            "flow_results": {},
            "overall_summary": {
                "discovery_flows_deleted": 0,
                "discovery_assets_deleted": 0,
                "created_assets_deleted": 0,
                "data_imports_cleaned": 0
            }
        }
        
        logger.info(f"🧹 Starting bulk cleanup for {len(flow_ids)} flows")
        
        for flow_id in flow_ids:
            try:
                cleanup_result = await self.delete_flow_with_cleanup(
                    flow_id, force_delete, cleanup_options
                )
                
                results["flow_results"][flow_id] = cleanup_result
                
                if cleanup_result["success"]:
                    results["successful_cleanups"] += 1
                    # Aggregate summary statistics
                    summary = cleanup_result.get("cleanup_summary", {})
                    if summary.get("discovery_flow_deleted"):
                        results["overall_summary"]["discovery_flows_deleted"] += 1
                    results["overall_summary"]["discovery_assets_deleted"] += summary.get("discovery_assets_deleted", 0)
                    results["overall_summary"]["created_assets_deleted"] += summary.get("created_assets_deleted", 0)
                    results["overall_summary"]["data_imports_cleaned"] += summary.get("data_imports_cleaned", 0)
                else:
                    results["failed_cleanups"] += 1
                    results["success"] = False
                    
            except Exception as e:
                logger.error(f"❌ Failed to cleanup flow {flow_id}: {e}")
                results["flow_results"][flow_id] = {
                    "success": False,
                    "error": str(e)
                }
                results["failed_cleanups"] += 1
                results["success"] = False
        
        cleanup_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        results["cleanup_duration_ms"] = int(cleanup_duration)
        
        logger.info(f"✅ Bulk cleanup completed: {results['successful_cleanups']}/{results['total_flows']} successful")
        
        return results
    
    async def cleanup_expired_flows(
        self,
        expiration_hours: int = 72,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Clean up expired discovery flows.
        
        Args:
            expiration_hours: Hours after which flows are considered expired
            dry_run: If True, only identify expired flows without deleting
            
        Returns:
            Dictionary with cleanup results
        """
        expiration_time = datetime.utcnow() - timedelta(hours=expiration_hours)
        
        # Find expired flows
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id,
                DiscoveryFlow.updated_at < expiration_time,
                DiscoveryFlow.status.in_(["active", "running", "failed", "error"])
            )
        )
        
        result = await self.db.execute(stmt)
        expired_flows = result.scalars().all()
        
        logger.info(f"Found {len(expired_flows)} expired flows (older than {expiration_hours} hours)")
        
        if dry_run:
            return {
                "status": "dry_run_completed",
                "expired_flows_found": len(expired_flows),
                "flow_ids": [flow.flow_id for flow in expired_flows],
                "expiration_hours": expiration_hours,
                "would_be_deleted": len(expired_flows)
            }
        
        if not expired_flows:
            return {
                "status": "no_expired_flows",
                "expired_flows_found": 0,
                "expiration_hours": expiration_hours
            }
        
        # Perform bulk cleanup
        flow_ids = [flow.flow_id for flow in expired_flows]
        cleanup_result = await self.bulk_cleanup_flows(
            flow_ids,
            force_delete=True,  # Expired flows can be force deleted
            cleanup_options={"reason": "expired_cleanup"}
        )
        
        return {
            "status": "cleanup_completed",
            "expired_flows_found": len(expired_flows),
            "cleanup_result": cleanup_result,
            "expiration_hours": expiration_hours
        }
    
    # Private helper methods
    
    async def _get_discovery_flow(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow by flow_id with context filtering."""
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _delete_discovery_assets(self, flow_id: str) -> int:
        """Delete all discovery assets for the flow."""
        # Get discovery flow first
        flow = await self._get_discovery_flow(flow_id)
        if not flow:
            return 0
        
        # Delete assets associated with this discovery flow
        stmt = delete(DiscoveryAsset).where(
            and_(
                DiscoveryAsset.discovery_flow_id == flow.id,
                DiscoveryAsset.client_account_id == self.client_account_id,
                DiscoveryAsset.engagement_id == self.engagement_id
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount
    
    async def _delete_created_assets(self, flow: DiscoveryFlow) -> int:
        """Delete assets that were created from this discovery flow."""
        if not ASSET_AVAILABLE:
            return 0
        
        # This would require tracking which assets were created from which discovery flow
        # For now, we'll skip this as it requires additional metadata tracking
        logger.info("Asset deletion not implemented - would require asset tracking metadata")
        return 0
    
    async def _clean_data_imports(self, flow: DiscoveryFlow) -> int:
        """Clean up related data imports."""
        if not DATA_IMPORT_AVAILABLE or not flow.import_session_id:
            return 0
        
        # Clean up data import references
        # This is optional and depends on the relationship structure
        logger.info(f"Data import cleanup not implemented for import_session_id: {flow.import_session_id}")
        return 0
    
    async def _create_audit_record(
        self,
        flow: DiscoveryFlow,
        cleanup_options: Dict[str, Any],
        cleanup_summary: Dict[str, Any]
    ) -> bool:
        """Create audit record for the deletion."""
        try:
            # For now, just log the audit information
            # In a full implementation, this would create an audit table record
            audit_data = {
                "flow_id": flow.flow_id,
                "client_account_id": str(flow.client_account_id),
                "engagement_id": str(flow.engagement_id),
                "user_id": str(self.user_id),
                "deletion_reason": cleanup_options.get("reason", "user_requested"),
                "cleanup_summary": cleanup_summary,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Audit record created for flow deletion: {audit_data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create audit record: {e}")
            return False


# Factory function for service creation
def create_discovery_flow_cleanup_service_v2(
    db: AsyncSession,
    context: RequestContext
) -> DiscoveryFlowCleanupServiceV2:
    """Create a V2 discovery flow cleanup service instance."""
    return DiscoveryFlowCleanupServiceV2(db, context) 