"""
Discovery Flow Cleanup Service - Impact Analysis Module
⚠️ LEGACY COMPATIBILITY LAYER - MIGRATING TO V2 ARCHITECTURE

Handles impact analysis and counting operations for cleanup planning.
"""

import logging
from typing import Any, Dict

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset as DiscoveryAsset
from app.models.data_import.core import DataImport as DataImportSession
from app.models.discovery_flow import DiscoveryFlow

# Optional dependency model import
try:
    from app.models.asset import AssetDependency as Dependency

    DEPENDENCY_MODEL_AVAILABLE = True
except ImportError:
    DEPENDENCY_MODEL_AVAILABLE = False
    Dependency = None

logger = logging.getLogger(__name__)


class ImpactAnalysisMixin:
    """
    Mixin for cleanup impact analysis
    Provides methods to analyze what will be deleted
    """

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
            # Use count() for better performance instead of len(all())
            stmt = select(func.count(DiscoveryAsset.id)).where(
                and_(
                    DiscoveryAsset.flow_id == flow_id,
                    DiscoveryAsset.client_account_id == self.client_account_id,
                    DiscoveryAsset.engagement_id == self.engagement_id,
                )
            )
            result = await db_session.execute(stmt)
            count_val = result.scalar_one()
            return int(count_val)
        except Exception:
            return 0

    async def _count_import_sessions(
        self, db_session: AsyncSession, flow_id: str
    ) -> int:
        """Count import sessions associated with the flow"""
        try:
            # Use count() for better performance instead of len(all())
            stmt = select(func.count(DataImportSession.id)).where(
                and_(
                    DataImportSession.flow_id == flow_id,
                    DataImportSession.client_account_id == self.client_account_id,
                    DataImportSession.engagement_id == self.engagement_id,
                )
            )
            result = await db_session.execute(stmt)
            count_val = result.scalar_one()
            return int(count_val)
        except Exception:
            return 0

    async def _count_dependencies(self, db_session: AsyncSession, flow_id: str) -> int:
        """Count dependencies associated with the flow"""
        if not DEPENDENCY_MODEL_AVAILABLE:
            return 0

        try:
            # Use count() for better performance instead of len(all())
            stmt = select(func.count(Dependency.id)).where(
                and_(
                    Dependency.session_id == flow_id,
                    Dependency.client_account_id == self.client_account_id,
                    Dependency.engagement_id == self.engagement_id,
                )
            )
            result = await db_session.execute(stmt)
            count_val = result.scalar_one()
            return int(count_val)
        except Exception:
            return 0
