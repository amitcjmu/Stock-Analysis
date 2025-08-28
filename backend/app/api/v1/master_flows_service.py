"""
Master Flow Coordination Service
Business logic for master flow operations
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.secure_logging import safe_log_format
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.utils.flow_deletion_utils import safely_create_deletion_audit

logger = logging.getLogger(__name__)


class MasterFlowService:
    """Service for master flow operations"""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.asset_repo = AssetRepository(db, client_account_id)
        self.discovery_repo = DiscoveryFlowRepository(
            db, client_account_id, engagement_id, user_id
        )

    async def get_active_master_flows(
        self, flow_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all active master flows"""
        try:
            # Convert client_account_id string to UUID for database comparison
            try:
                client_uuid = uuid.UUID(self.client_account_id)
            except (ValueError, TypeError):
                logger.error("Invalid client_account_id format received")
                raise HTTPException(
                    status_code=400, detail="Invalid client account ID format"
                )

            # Build query conditions
            conditions = [
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
                CrewAIFlowStateExtensions.flow_status.notin_(
                    [
                        "completed",
                        "failed",
                        "error",
                        "deleted",
                        "cancelled",
                        "child_flows_deleted",
                    ]
                ),
            ]

            # Add flow type filter if provided
            if flow_type:
                conditions.append(CrewAIFlowStateExtensions.flow_type == flow_type)

            # Query for active master flows
            stmt = (
                select(CrewAIFlowStateExtensions)
                .where(and_(*conditions))
                .order_by(CrewAIFlowStateExtensions.created_at.desc())
            )

            result = await self.db.execute(stmt)
            master_flows = result.scalars().all()

            # Convert to response format
            active_flows = []
            for flow in master_flows:
                active_flows.append(
                    {
                        "master_flow_id": str(flow.flow_id),
                        "flow_type": flow.flow_type,
                        "flow_name": flow.flow_name,
                        "status": flow.flow_status,
                        "created_at": (
                            flow.created_at.isoformat() if flow.created_at else None
                        ),
                        "updated_at": (
                            flow.updated_at.isoformat() if flow.updated_at else None
                        ),
                        "configuration": flow.flow_configuration or {},
                    }
                )

            logger.info(
                f"Found {len(active_flows)} active master flows"
                + (
                    f" (filtered by flow_type: {flow_type})"
                    if flow_type
                    else " (all flow types)"
                )
            )
            return active_flows

        except Exception as e:
            logger.error(
                safe_log_format("Error retrieving active master flows: {e}", e=e)
            )
            raise

    async def transition_to_assessment_phase(
        self, discovery_flow_id: str, assessment_flow_id: str
    ) -> Dict[str, Any]:
        """Prepare discovery flow for assessment phase transition"""
        try:
            discovery_flow = await self.discovery_repo.get_by_id(discovery_flow_id)
            if not discovery_flow:
                raise HTTPException(status_code=404, detail="Discovery flow not found")

            # Store the assessment flow ID in discovery flow metadata
            discovery_flow.metadata = discovery_flow.metadata or {}
            discovery_flow.metadata["assessment_flow_id"] = assessment_flow_id
            await self.db.commit()

            # Get assets from this discovery flow
            assets = await self.asset_repo.get_by_discovery_flow(discovery_flow_id)

            # Mark assets as ready for assessment
            for asset in assets:
                asset.current_phase = "assessment"
                asset.assessment_flow_id = uuid.UUID(assessment_flow_id)
                asset.assessment_readiness = "ready"

            await self.db.commit()

            return {
                "success": True,
                "discovery_flow_id": discovery_flow_id,
                "assessment_flow_id": assessment_flow_id,
                "assets_marked": len(assets),
                "message": f"Marked {len(assets)} assets ready for assessment",
            }

        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise

    async def update_asset_phase(self, asset_id: str, new_phase: str) -> Dict[str, Any]:
        """Update an asset's phase progression"""
        try:
            asset = await self.asset_repo.get_by_id(asset_id)
            if not asset:
                raise HTTPException(status_code=404, detail="Asset not found")

            # Store previous phase
            previous_phase = asset.current_phase

            # Update phase
            asset.current_phase = new_phase

            # Track phase history
            phase_history = (
                asset.metadata.get("phase_history", []) if asset.metadata else []
            )
            phase_history.append(
                {
                    "from": previous_phase,
                    "to": new_phase,
                    "timestamp": str(datetime.utcnow()),
                    "user_id": self.user_id,
                }
            )

            if not asset.metadata:
                asset.metadata = {}
            asset.metadata["phase_history"] = phase_history

            await self.db.commit()

            return {
                "success": True,
                "asset_id": asset_id,
                "previous_phase": previous_phase,
                "new_phase": new_phase,
                "message": f"Asset phase updated from {previous_phase} to {new_phase}",
            }

        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            raise

    async def soft_delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Soft delete a master flow and its child flows"""
        try:
            # Get the master flow
            stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == uuid.UUID(flow_id),
                CrewAIFlowStateExtensions.client_account_id
                == uuid.UUID(self.client_account_id),
            )
            result = await self.db.execute(stmt)
            master_flow = result.scalar_one_or_none()

            if not master_flow:
                raise HTTPException(status_code=404, detail="Master flow not found")

            # Store the previous status
            previous_status = master_flow.flow_status

            # Mark master flow as deleted
            master_flow.flow_status = "deleted"
            master_flow.updated_at = datetime.utcnow()

            # Mark all child flows (discovery flows) as deleted
            child_flows_deleted = 0
            if master_flow.flow_type == "discovery":
                # Get all discovery flows with this master_flow_id
                discovery_flows = await self.discovery_repo.get_by_master_flow_id(
                    flow_id
                )

                if discovery_flows:
                    # Handle both single flow and list of flows
                    flows_to_delete = (
                        discovery_flows
                        if isinstance(discovery_flows, list)
                        else [discovery_flows]
                    )

                    for flow in flows_to_delete:
                        flow.status = "deleted"
                        flow.updated_at = datetime.utcnow()
                        child_flows_deleted += 1

            # Create deletion audit record
            from app.models.flow_deletion_audit import FlowDeletionAudit

            audit_record = FlowDeletionAudit(
                flow_id=uuid.UUID(flow_id),
                client_account_id=uuid.UUID(self.client_account_id),
                engagement_id=uuid.UUID(self.engagement_id),
                user_id=self.user_id,
                deletion_type="user_requested",
                deletion_reason=f"Soft deleted master flow and {child_flows_deleted} child flows",
                deletion_method="api",
                data_deleted={
                    "flow_type": master_flow.flow_type,
                    "child_flows": child_flows_deleted,
                },
                deletion_impact={
                    "master_flow_deleted": True,
                    "child_flows_deleted": child_flows_deleted,
                },
                cleanup_summary={"status": "soft_delete", "permanent": False},
            )

            audit_created = await safely_create_deletion_audit(
                db=self.db,
                audit_record=audit_record,
                flow_id=flow_id,
                operation_context="master_flow_soft_deletion",
            )

            await self.db.commit()

            return {
                "success": True,
                "flow_id": flow_id,
                "flow_type": master_flow.flow_type,
                "previous_status": previous_status,
                "child_flows_deleted": child_flows_deleted,
                "audit_id": audit_created if audit_created else None,
                "message": f"Master flow and {child_flows_deleted} child flows marked as deleted",
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(safe_log_format("Error soft deleting flow: {e}", e=e))
            raise
