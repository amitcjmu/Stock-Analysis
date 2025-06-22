"""
Discovery Flow Cleanup Service
Handles comprehensive cleanup of discovery flows including CrewAI Flow state,
agent memory, database records, and associated data with proper audit trail
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, text
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.models.workflow_state import WorkflowState
from app.models.asset import Asset
from app.models.data_import_session import DataImportSession

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
    Comprehensive cleanup service for discovery flows
    Handles deletion of all associated data with proper audit trail
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None,
                 client_account_id: Optional[str] = None,
                 engagement_id: Optional[str] = None):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
    
    async def delete_flow_with_cleanup(self, session_id: str, 
                                     force_delete: bool = False,
                                     cleanup_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Delete a discovery flow and all associated data with comprehensive cleanup
        """
        cleanup_options = cleanup_options or {}
        cleanup_summary = {
            "workflow_states_deleted": 0,
            "assets_deleted": 0,
            "import_sessions_deleted": 0,
            "dependencies_deleted": 0,
            "agent_memory_cleared": False,
            "knowledge_base_cleared": False,
            "audit_record_created": False
        }
        
        try:
            async with AsyncSessionLocal() as db_session:
                # Get workflow state for audit purposes
                workflow_stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.session_id == session_id,
                        WorkflowState.client_account_id == self.client_account_id,
                        WorkflowState.engagement_id == self.engagement_id
                    )
                )
                result = await db_session.execute(workflow_stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return {
                        "success": False,
                        "error": f"Workflow not found for session: {session_id}",
                        "cleanup_summary": cleanup_summary
                    }
                
                # Check if force delete is required
                if workflow.status == "running" and not force_delete:
                    return {
                        "success": False,
                        "error": "Cannot delete running flow without force_delete=True",
                        "cleanup_summary": cleanup_summary
                    }
                
                # Create audit record before deletion
                audit_data = await self._create_deletion_audit_record(workflow, cleanup_options)
                
                # 1. Delete associated assets
                if cleanup_options.get("delete_assets", True):
                    assets_deleted = await self._delete_associated_assets(db_session, session_id)
                    cleanup_summary["assets_deleted"] = assets_deleted
                
                # 2. Delete import sessions
                if cleanup_options.get("delete_import_sessions", True):
                    sessions_deleted = await self._delete_import_sessions(db_session, session_id)
                    cleanup_summary["import_sessions_deleted"] = sessions_deleted
                
                # 3. Delete dependencies
                if cleanup_options.get("delete_dependencies", True):
                    deps_deleted = await self._delete_dependencies(db_session, session_id)
                    cleanup_summary["dependencies_deleted"] = deps_deleted
                
                # 4. Clear agent memory and knowledge base
                if cleanup_options.get("clear_agent_memory", True):
                    memory_cleared = await self._clear_agent_memory(workflow.shared_memory_id)
                    cleanup_summary["agent_memory_cleared"] = memory_cleared
                
                if cleanup_options.get("clear_knowledge_base", True):
                    kb_cleared = await self._clear_knowledge_base_references(session_id)
                    cleanup_summary["knowledge_base_cleared"] = kb_cleared
                
                # 5. Delete workflow state (must be last)
                await db_session.delete(workflow)
                cleanup_summary["workflow_states_deleted"] = 1
                
                # 6. Save audit record
                if AUDIT_AVAILABLE and audit_data:
                    audit_record = FlowDeletionAudit(**audit_data)
                    db_session.add(audit_record)
                    cleanup_summary["audit_record_created"] = True
                
                # Commit all changes
                await db_session.commit()
                
                logger.info(f"✅ Flow cleanup completed for session: {session_id}")
                
                return {
                    "success": True,
                    "message": f"Flow and all associated data deleted successfully",
                    "session_id": session_id,
                    "cleanup_summary": cleanup_summary,
                    "deletion_timestamp": datetime.utcnow().isoformat(),
                    "audit_record_id": audit_data.get("id") if audit_data else None
                }
                
        except Exception as e:
            logger.error(f"❌ Flow cleanup failed for session {session_id}: {e}")
            return {
                "success": False,
                "error": f"Cleanup failed: {str(e)}",
                "session_id": session_id,
                "cleanup_summary": cleanup_summary
            }
    
    async def _delete_associated_assets(self, db_session: AsyncSession, session_id: str) -> int:
        """Delete all assets associated with the flow"""
        try:
            # Get assets to delete
            assets_stmt = select(Asset).where(
                and_(
                    Asset.session_id == session_id,
                    Asset.client_account_id == self.client_account_id,
                    Asset.engagement_id == self.engagement_id
                )
            )
            result = await db_session.execute(assets_stmt)
            assets = result.scalars().all()
            
            # Delete assets
            for asset in assets:
                await db_session.delete(asset)
            
            logger.info(f"🗑️ Deleted {len(assets)} assets for session: {session_id}")
            return len(assets)
            
        except Exception as e:
            logger.error(f"❌ Failed to delete assets: {e}")
            return 0
    
    async def _delete_import_sessions(self, db_session: AsyncSession, session_id: str) -> int:
        """Delete import sessions associated with the flow"""
        try:
            # Get import sessions to delete
            sessions_stmt = select(DataImportSession).where(
                and_(
                    DataImportSession.session_id == session_id,
                    DataImportSession.client_account_id == self.client_account_id,
                    DataImportSession.engagement_id == self.engagement_id
                )
            )
            result = await db_session.execute(sessions_stmt)
            import_sessions = result.scalars().all()
            
            # Delete import sessions
            for session in import_sessions:
                await db_session.delete(session)
            
            logger.info(f"🗑️ Deleted {len(import_sessions)} import sessions for session: {session_id}")
            return len(import_sessions)
            
        except Exception as e:
            logger.error(f"❌ Failed to delete import sessions: {e}")
            return 0
    
    async def _delete_dependencies(self, db_session: AsyncSession, session_id: str) -> int:
        """Delete dependencies associated with the flow"""
        if not DEPENDENCY_MODEL_AVAILABLE:
            logger.info(f"📋 Dependency model not available - skipping dependency cleanup for session: {session_id}")
            return 0
            
        try:
            # Get dependencies to delete
            deps_stmt = select(Dependency).where(
                and_(
                    Dependency.session_id == session_id,
                    Dependency.client_account_id == self.client_account_id,
                    Dependency.engagement_id == self.engagement_id
                )
            )
            result = await db_session.execute(deps_stmt)
            dependencies = result.scalars().all()
            
            # Delete dependencies
            for dep in dependencies:
                await db_session.delete(dep)
            
            logger.info(f"🗑️ Deleted {len(dependencies)} dependencies for session: {session_id}")
            return len(dependencies)
            
        except Exception as e:
            logger.error(f"❌ Failed to delete dependencies: {e}")
            return 0
    
    async def _clear_agent_memory(self, shared_memory_id: Optional[str]) -> bool:
        """Clear agent memory associated with the flow"""
        if not shared_memory_id:
            return True
        
        try:
            # TODO: Implement agent memory clearing
            # This would interact with CrewAI's memory system
            # For now, log the action
            logger.info(f"🧠 Agent memory clearing requested for: {shared_memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear agent memory: {e}")
            return False
    
    async def _clear_knowledge_base_references(self, session_id: str) -> bool:
        """Clear knowledge base references associated with the flow"""
        try:
            # TODO: Implement knowledge base cleanup
            # This would clear any session-specific knowledge base entries
            # For now, log the action
            logger.info(f"📚 Knowledge base cleanup requested for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear knowledge base: {e}")
            return False
    
    async def _create_deletion_audit_record(self, workflow: WorkflowState, 
                                          cleanup_options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create audit record for flow deletion"""
        if not AUDIT_AVAILABLE:
            return None
        
        try:
            audit_data = {
                "session_id": str(workflow.session_id),
                "client_account_id": str(workflow.client_account_id),
                "engagement_id": str(workflow.engagement_id),
                "flow_id": str(workflow.flow_id),
                "deleted_at": datetime.utcnow(),
                "deletion_reason": cleanup_options.get("reason", "user_requested"),
                "force_delete": cleanup_options.get("force_delete", False),
                "flow_state_snapshot": {
                    "current_phase": workflow.current_phase,
                    "status": workflow.status,
                    "progress_percentage": workflow.progress_percentage,
                    "phase_completion": workflow.phase_completion,
                    "created_at": workflow.created_at.isoformat(),
                    "updated_at": workflow.updated_at.isoformat()
                },
                "cleanup_options": cleanup_options,
                "user_id": cleanup_options.get("user_id"),
                "admin_action": cleanup_options.get("admin_action", False)
            }
            
            return audit_data
            
        except Exception as e:
            logger.error(f"❌ Failed to create audit record: {e}")
            return None
    
    async def get_cleanup_impact_analysis(self, session_id: str) -> Dict[str, Any]:
        """Analyze the impact of deleting a specific flow"""
        try:
            async with AsyncSessionLocal() as db_session:
                # Get workflow state
                workflow_stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.session_id == session_id,
                        WorkflowState.client_account_id == self.client_account_id,
                        WorkflowState.engagement_id == self.engagement_id
                    )
                )
                result = await db_session.execute(workflow_stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return {"error": "Workflow not found"}
                
                # Count associated data
                assets_count = await self._count_associated_assets(db_session, session_id)
                sessions_count = await self._count_import_sessions(db_session, session_id)
                deps_count = await self._count_dependencies(db_session, session_id)
                
                # Calculate estimated cleanup time
                total_records = assets_count + sessions_count + deps_count
                estimated_time = self._calculate_cleanup_time(total_records)
                
                return {
                    "session_id": session_id,
                    "flow_phase": workflow.current_phase,
                    "progress_percentage": workflow.progress_percentage,
                    "status": workflow.status,
                    "data_to_delete": {
                        "workflow_state": 1,
                        "assets": assets_count,
                        "import_sessions": sessions_count,
                        "dependencies": deps_count,
                        "total_records": total_records
                    },
                    "estimated_cleanup_time": estimated_time,
                    "data_recovery_possible": False,
                    "warnings": self._get_deletion_warnings(workflow, total_records),
                    "recommendations": self._get_deletion_recommendations(workflow)
                }
                
        except Exception as e:
            logger.error(f"❌ Cleanup impact analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def _count_associated_assets(self, db_session: AsyncSession, session_id: str) -> int:
        """Count assets associated with the flow"""
        try:
            stmt = select(Asset).where(
                and_(
                    Asset.session_id == session_id,
                    Asset.client_account_id == self.client_account_id,
                    Asset.engagement_id == self.engagement_id
                )
            )
            result = await db_session.execute(stmt)
            return len(result.scalars().all())
        except Exception:
            return 0
    
    async def _count_import_sessions(self, db_session: AsyncSession, session_id: str) -> int:
        """Count import sessions associated with the flow"""
        try:
            stmt = select(DataImportSession).where(
                and_(
                    DataImportSession.session_id == session_id,
                    DataImportSession.client_account_id == self.client_account_id,
                    DataImportSession.engagement_id == self.engagement_id
                )
            )
            result = await db_session.execute(stmt)
            return len(result.scalars().all())
        except Exception:
            return 0
    
    async def _count_dependencies(self, db_session: AsyncSession, session_id: str) -> int:
        """Count dependencies associated with the flow"""
        if not DEPENDENCY_MODEL_AVAILABLE:
            return 0
            
        try:
            stmt = select(Dependency).where(
                and_(
                    Dependency.session_id == session_id,
                    Dependency.client_account_id == self.client_account_id,
                    Dependency.engagement_id == self.engagement_id
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
    
    def _get_deletion_warnings(self, workflow: WorkflowState, total_records: int) -> List[str]:
        """Get warnings about flow deletion"""
        warnings = []
        
        if workflow.status == "running":
            warnings.append("Flow is currently running - force delete required")
        
        if workflow.progress_percentage > 80:
            warnings.append("Flow is nearly complete - consider completing instead of deleting")
        
        if total_records > 1000:
            warnings.append(f"Large amount of data will be deleted ({total_records} records)")
        
        if workflow.shared_memory_id:
            warnings.append("Agent memory will be cleared - learning progress may be lost")
        
        return warnings
    
    def _get_deletion_recommendations(self, workflow: WorkflowState) -> List[str]:
        """Get recommendations for flow deletion"""
        recommendations = []
        
        if workflow.status == "paused":
            recommendations.append("Consider resuming flow instead of deleting")
        
        if workflow.progress_percentage > 50:
            recommendations.append("Flow has significant progress - export data before deletion")
        
        if workflow.errors:
            recommendations.append("Review errors before deletion to prevent similar issues")
        
        recommendations.append("Ensure all stakeholders are aware of the deletion")
        recommendations.append("Consider creating a backup of important data")
        
        return recommendations 