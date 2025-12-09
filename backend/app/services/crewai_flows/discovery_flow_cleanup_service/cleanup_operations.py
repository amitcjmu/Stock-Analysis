"""
Discovery Flow Cleanup Service - Cleanup Operations Module
⚠️ LEGACY COMPATIBILITY LAYER - MIGRATING TO V2 ARCHITECTURE

Handles the main deletion and cleanup operations for discovery flows.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal

# Legacy imports for backward compatibility
from app.models.asset import Asset
from app.models.data_import.core import DataImport as DataImportSession

# V2 Discovery Flow imports (target architecture)
from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery_flow_service import DiscoveryFlowService

# Optional dependency model import
try:
    from app.models.asset import AssetDependency as Dependency

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


class CleanupOperationsMixin:
    """
    Mixin for cleanup operations
    Handles deletion of flows and all associated data
    """

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

                # 7. Save audit record with defensive handling
                if AUDIT_AVAILABLE and audit_data:
                    from app.utils.flow_deletion_utils import (
                        safely_create_deletion_audit,
                    )

                    audit_record = FlowDeletionAudit(**audit_data)
                    audit_id = await safely_create_deletion_audit(
                        db_session, audit_record, flow_id, "v2_flow_cleanup"
                    )
                    cleanup_summary["audit_record_created"] = audit_id is not None
                    if not audit_id:
                        cleanup_summary["audit_skipped_reason"] = "table_not_found"

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
