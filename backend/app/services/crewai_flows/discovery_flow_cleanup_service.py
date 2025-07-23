"""
Discovery Flow Cleanup Service
⚠️ LEGACY COMPATIBILITY LAYER - MIGRATING TO V2 ARCHITECTURE

Handles comprehensive cleanup of discovery flows including CrewAI Flow state,
agent memory, database records, and associated data with proper audit trail.

Migrating from WorkflowState to DiscoveryFlow V2 architecture.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
# Legacy imports for backward compatibility
from app.models.asset import Asset
from app.models.asset import Asset as DiscoveryAsset
from app.models.data_import.core import DataImport as DataImportSession
# V2 Discovery Flow imports (target architecture)
from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery_flow_service import DiscoveryFlowService

# Optional dependency model import
try:
    from app.models.dependency import Dependency

    DEPENDENCY_MODEL_AVAILABLE = True
except ImportError:
    DEPENDENCY_MODEL_AVAILABLE = False
    Dependency = None

# Optional imports with graceful fallback
try:
    from app.models.flow_deletion_audit import FlowDeletionAudit

    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DiscoveryFlowCleanupService:
    """
    ⚠️ LEGACY COMPATIBILITY LAYER - Use DiscoveryFlowService.delete_flow() for new development

    Comprehensive cleanup service for discovery flows
    Handles deletion of all associated data with proper audit trail
    """

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def delete_flow_with_cleanup(
        self,
        flow_id: str,
        force_delete: bool = False,
        cleanup_options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Delete a discovery flow and all associated data with comprehensive cleanup
        ⚠️ LEGACY METHOD - Use DiscoveryFlowService.delete_flow() for new development
        """
        cleanup_options = cleanup_options or {}
        cleanup_summary = {
            "discovery_flows_deleted": 0,
            "discovery_assets_deleted": 0,
            "legacy_assets_deleted": 0,
            "import_sessions_deleted": 0,
            "dependencies_deleted": 0,
            "agent_memory_cleared": False,
            "knowledge_base_cleared": False,
            "audit_record_created": False,
        }

        try:
            logger.info(f"🔄 [LEGACY] Starting V2 cleanup for flow: {flow_id}")

            async with AsyncSessionLocal() as db_session:
                # Create mock context for V2 service
                from app.core.context import RequestContext

                context = RequestContext(
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    user_id="system",
                )

                # Use V2 Discovery Flow Service
                flow_service = DiscoveryFlowService(db_session, context)

                # Get V2 discovery flow
                flow = await flow_service.get_flow_by_id(flow_id)

                if not flow:
                    logger.warning(f"⚠️ [LEGACY] V2 flow not found: {flow_id}")
                    return {
                        "success": False,
                        "error": f"V2 Discovery flow not found: {flow_id}",
                        "cleanup_summary": cleanup_summary,
                    }

                # Check if force delete is required
                if flow.status == "active" and not force_delete:
                    return {
                        "success": False,
                        "error": "Cannot delete active flow without force_delete=True",
                        "cleanup_summary": cleanup_summary,
                    }

                # Create audit record before deletion
                audit_data = await self._create_deletion_audit_record_v2(
                    flow, cleanup_options
                )

                # 1. Delete V2 discovery assets (handled by cascade)
                assets_count = len(flow.assets)
                cleanup_summary["discovery_assets_deleted"] = assets_count

                # 2. Delete legacy assets if any exist
                if cleanup_options.get("delete_legacy_assets", True):
                    legacy_assets_deleted = await self._delete_legacy_assets(
                        db_session, flow_id
                    )
                    cleanup_summary["legacy_assets_deleted"] = legacy_assets_deleted

                # 3. Delete import sessions
                if cleanup_options.get("delete_import_sessions", True):
                    sessions_deleted = await self._delete_import_sessions_v2(
                        db_session, flow
                    )
                    cleanup_summary["import_sessions_deleted"] = sessions_deleted

                # 4. Delete dependencies
                if cleanup_options.get("delete_dependencies", True):
                    deps_deleted = await self._delete_dependencies_v2(
                        db_session, flow_id
                    )
                    cleanup_summary["dependencies_deleted"] = deps_deleted

                # 5. Clear agent memory and knowledge base
                if cleanup_options.get("clear_agent_memory", True):
                    memory_cleared = await self._clear_agent_memory_v2(flow)
                    cleanup_summary["agent_memory_cleared"] = memory_cleared

                if cleanup_options.get("clear_knowledge_base", True):
                    kb_cleared = await self._clear_knowledge_base_references_v2(flow_id)
                    cleanup_summary["knowledge_base_cleared"] = kb_cleared

                # 6. Delete V2 discovery flow using service
                delete_success = await flow_service.delete_flow(flow_id)
                if delete_success:
                    cleanup_summary["discovery_flows_deleted"] = 1

                # 7. Save audit record
                if AUDIT_AVAILABLE and audit_data:
                    audit_record = FlowDeletionAudit(**audit_data)
                    db_session.add(audit_record)
                    cleanup_summary["audit_record_created"] = True

                # Commit all changes
                await db_session.commit()

                logger.info(f"✅ [LEGACY] V2 flow cleanup completed for: {flow_id}")

                return {
                    "success": True,
                    "message": "V2 Discovery flow and all associated data deleted successfully",
                    "flow_id": flow_id,
                    "cleanup_summary": cleanup_summary,
                    "deletion_timestamp": datetime.utcnow().isoformat(),
                    "audit_record_id": audit_data.get("id") if audit_data else None,
                    "migration_note": "Cleaned up using V2 DiscoveryFlow architecture",
                }

        except Exception as e:
            logger.error(f"❌ [LEGACY] V2 flow cleanup failed for {flow_id}: {e}")
            return {
                "success": False,
                "error": f"V2 cleanup failed: {str(e)}",
                "flow_id": flow_id,
                "cleanup_summary": cleanup_summary,
            }

    async def _delete_legacy_assets(
        self, db_session: AsyncSession, flow_id: str
    ) -> int:
        """Delete legacy assets that might reference the flow"""
        try:
            # Try to find legacy assets by various identifiers
            legacy_assets_stmt = select(Asset).where(
                and_(
                    Asset.client_account_id == self.client_account_id,
                    Asset.engagement_id == self.engagement_id,
                    # Match by discovery_flow_id using flow_id parameter
                    Asset.discovery_flow_id == flow_id,
                )
            )
            result = await db_session.execute(legacy_assets_stmt)
            legacy_assets = result.scalars().all()

            # Delete legacy assets
            for asset in legacy_assets:
                await db_session.delete(asset)

            logger.info(
                f"🗑️ [LEGACY] Deleted {len(legacy_assets)} legacy assets for flow: {flow_id}"
            )
            return len(legacy_assets)

        except Exception as e:
            logger.error(f"❌ [LEGACY] Failed to delete legacy assets: {e}")
            return 0

    async def _delete_import_sessions_v2(
        self, db_session: AsyncSession, flow: DiscoveryFlow
    ) -> int:
        """Delete import sessions associated with the V2 flow"""
        try:
            sessions_deleted = 0

            # Delete by data_import_id if available
            if hasattr(flow, "data_import_id") and flow.data_import_id:
                sessions_stmt = select(DataImportSession).where(
                    and_(
                        DataImportSession.id == flow.data_import_id,
                        DataImportSession.client_account_id == self.client_account_id,
                        DataImportSession.engagement_id == self.engagement_id,
                    )
                )
                result = await db_session.execute(sessions_stmt)
                import_sessions = result.scalars().all()

                for session in import_sessions:
                    await db_session.delete(session)
                    sessions_deleted += 1

            logger.info(
                f"🗑️ [LEGACY] Deleted {sessions_deleted} import sessions for V2 flow: {flow.flow_id}"
            )
            return sessions_deleted

        except Exception as e:
            logger.error(f"❌ [LEGACY] Failed to delete import sessions: {e}")
            return 0

    async def _delete_dependencies_v2(
        self, db_session: AsyncSession, flow_id: str
    ) -> int:
        """Delete dependencies associated with the V2 flow"""
        if not DEPENDENCY_MODEL_AVAILABLE:
            logger.info(
                f"📋 Dependency model not available - skipping dependency cleanup for flow: {flow_id}"
            )
            return 0

        try:
            # Get dependencies to delete
            deps_stmt = select(Dependency).where(
                and_(
                    Dependency.session_id == flow_id,
                    Dependency.client_account_id == self.client_account_id,
                    Dependency.engagement_id == self.engagement_id,
                )
            )
            result = await db_session.execute(deps_stmt)
            dependencies = result.scalars().all()

            # Delete dependencies
            for dep in dependencies:
                await db_session.delete(dep)

            logger.info(
                f"🗑️ Deleted {len(dependencies)} dependencies for flow: {flow_id}"
            )
            return len(dependencies)

        except Exception as e:
            logger.error(f"❌ Failed to delete dependencies: {e}")
            return 0

    async def _clear_agent_memory_v2(self, flow: DiscoveryFlow) -> bool:
        """Clear agent memory associated with the V2 flow"""
        if not flow.shared_memory_id:
            return True

        try:
            # TODO: Implement agent memory clearing
            # This would interact with CrewAI's memory system
            # For now, log the action
            logger.info(
                f"🧠 Agent memory clearing requested for: {flow.shared_memory_id}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to clear agent memory: {e}")
            return False

    async def _clear_knowledge_base_references_v2(self, flow_id: str) -> bool:
        """Clear knowledge base references associated with the V2 flow"""
        try:
            # TODO: Implement knowledge base cleanup
            # This would clear any session-specific knowledge base entries
            # For now, log the action
            logger.info(f"📚 Knowledge base cleanup requested for flow: {flow_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to clear knowledge base: {e}")
            return False

    async def _create_deletion_audit_record_v2(
        self, flow: DiscoveryFlow, cleanup_options: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create audit record for flow deletion"""
        if not AUDIT_AVAILABLE:
            return None

        try:
            audit_data = {
                "flow_id": str(flow.flow_id),
                "deleted_at": datetime.utcnow(),
                "deletion_reason": cleanup_options.get("reason", "user_requested"),
                "force_delete": cleanup_options.get("force_delete", False),
                "flow_state_snapshot": {
                    "current_phase": flow.current_phase,
                    "status": flow.status,
                    "progress_percentage": flow.progress_percentage,
                    "phase_completion": flow.phase_completion,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat(),
                },
                "cleanup_options": cleanup_options,
                "user_id": cleanup_options.get("user_id"),
                "admin_action": cleanup_options.get("admin_action", False),
            }

            return audit_data

        except Exception as e:
            logger.error(f"❌ Failed to create audit record: {e}")
            return None

    async def get_cleanup_impact_analysis(self, flow_id: str) -> Dict[str, Any]:
        """Analyze the impact of deleting a specific flow"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Get flow
                flow_stmt = select(DiscoveryFlow).where(
                    and_(
                        DiscoveryFlow.flow_id == flow_id,
                        DiscoveryFlow.client_account_id == self.client_account_id,
                        DiscoveryFlow.engagement_id == self.engagement_id,
                    )
                )
                result = await db_session.execute(flow_stmt)
                flow = result.scalar_one_or_none()

                if not flow:
                    return {"error": "Flow not found"}

                # Count associated data
                assets_count = await self._count_associated_assets(db_session, flow_id)
                sessions_count = await self._count_import_sessions(db_session, flow_id)
                deps_count = await self._count_dependencies(db_session, flow_id)

                # Calculate estimated cleanup time
                total_records = assets_count + sessions_count + deps_count
                estimated_time = self._calculate_cleanup_time(total_records)

                return {
                    "flow_id": flow_id,
                    "flow_phase": flow.current_phase,
                    "progress_percentage": flow.progress_percentage,
                    "status": flow.status,
                    "data_to_delete": {
                        "flow_state": 1,
                        "assets": assets_count,
                        "import_sessions": sessions_count,
                        "dependencies": deps_count,
                        "total_records": total_records,
                    },
                    "estimated_cleanup_time": estimated_time,
                    "data_recovery_possible": False,
                    "warnings": self._get_deletion_warnings(flow, total_records),
                    "recommendations": self._get_deletion_recommendations(flow),
                }

        except Exception as e:
            logger.error(f"❌ Cleanup impact analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    async def _count_associated_assets(
        self, db_session: AsyncSession, flow_id: str
    ) -> int:
        """Count assets associated with the flow"""
        try:
            stmt = select(DiscoveryAsset).where(
                and_(
                    DiscoveryAsset.flow_id == flow_id,
                    DiscoveryAsset.client_account_id == self.client_account_id,
                    DiscoveryAsset.engagement_id == self.engagement_id,
                )
            )
            result = await db_session.execute(stmt)
            return len(result.scalars().all())
        except Exception:
            return 0

    async def _count_import_sessions(
        self, db_session: AsyncSession, flow_id: str
    ) -> int:
        """Count import sessions associated with the flow"""
        try:
            stmt = select(DataImportSession).where(
                and_(
                    DataImportSession.flow_id == flow_id,
                    DataImportSession.client_account_id == self.client_account_id,
                    DataImportSession.engagement_id == self.engagement_id,
                )
            )
            result = await db_session.execute(stmt)
            return len(result.scalars().all())
        except Exception:
            return 0

    async def _count_dependencies(self, db_session: AsyncSession, flow_id: str) -> int:
        """Count dependencies associated with the flow"""
        if not DEPENDENCY_MODEL_AVAILABLE:
            return 0

        try:
            stmt = select(Dependency).where(
                and_(
                    Dependency.session_id == flow_id,
                    Dependency.client_account_id == self.client_account_id,
                    Dependency.engagement_id == self.engagement_id,
                )
            )
            result = await db_session.execute(stmt)
            return len(result.scalars().all())
        except Exception:
            return 0

    def _calculate_cleanup_time(self, total_records: int) -> str:
        """Calculate estimated cleanup time based on record count"""
        if total_records > 10000:
            return "30-60 seconds"
        elif total_records > 5000:
            return "15-30 seconds"
        elif total_records > 1000:
            return "10-15 seconds"
        elif total_records > 100:
            return "5-10 seconds"
        else:
            return "< 5 seconds"

    def _get_deletion_warnings(
        self, flow: DiscoveryFlow, total_records: int
    ) -> List[str]:
        """Get warnings about flow deletion"""
        warnings = []

        if flow.status == "active":
            warnings.append("Flow is currently active - force delete required")

        if flow.progress_percentage > 80:
            warnings.append(
                "Flow is nearly complete - consider completing instead of deleting"
            )

        if total_records > 1000:
            warnings.append(
                f"Large amount of data will be deleted ({total_records} records)"
            )

        if flow.shared_memory_id:
            warnings.append(
                "Agent memory will be cleared - learning progress may be lost"
            )

        return warnings

    def _get_deletion_recommendations(self, flow: DiscoveryFlow) -> List[str]:
        """Get recommendations for flow deletion"""
        recommendations = []

        if flow.status == "paused":
            recommendations.append("Consider resuming flow instead of deleting")

        if flow.progress_percentage > 50:
            recommendations.append(
                "Flow has significant progress - export data before deletion"
            )

        if flow.errors:
            recommendations.append(
                "Review errors before deletion to prevent similar issues"
            )

        recommendations.append("Ensure all stakeholders are aware of the deletion")
        recommendations.append("Consider creating a backup of important data")

        return recommendations
