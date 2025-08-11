"""
Flow Commands

Write operations for discovery flows.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.services.caching.redis_cache import get_redis_cache

from ..queries.flow_queries import FlowQueries

logger = logging.getLogger(__name__)


class FlowCommands:
    """Handles all flow write operations"""

    def __init__(
        self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_queries = FlowQueries(db, client_account_id, engagement_id)
        self.redis = get_redis_cache()

    def _ensure_uuid(self, flow_id: Any) -> uuid.UUID:
        """Ensure flow_id is a UUID object"""
        if isinstance(flow_id, uuid.UUID):
            return flow_id
        try:
            return uuid.UUID(str(flow_id))
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid UUID: {flow_id}, error: {e}")
            raise ValueError(f"Invalid UUID: {flow_id}. Must be a valid UUID.")

    async def _invalidate_flow_cache(self, flow: DiscoveryFlow):
        """Invalidate cached data for a discovery flow"""
        if not self.redis or not self.redis.enabled:
            return

        try:
            # Invalidate cache by master flow ID
            if flow.master_flow_id:
                cache_key = f"v1:flow:discovery:by_master:{flow.master_flow_id}"
                await self.redis.delete(cache_key)
                logger.debug(
                    f"Invalidated cache for master_flow_id: {flow.master_flow_id}"
                )
        except Exception as e:
            logger.warning(f"Failed to invalidate flow cache: {e}")

    async def create_discovery_flow(
        self,
        flow_id: str,
        master_flow_id: Optional[str] = None,
        flow_type: str = "primary",
        description: Optional[str] = None,
        initial_state_data: Optional[Dict[str, Any]] = None,
        data_import_id: Optional[str] = None,
        user_id: Optional[str] = None,
        raw_data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DiscoveryFlow:
        """Create new discovery flow using CrewAI Flow ID"""

        # Parse flow_id as UUID
        parsed_flow_id = self._ensure_uuid(flow_id)

        # Parse optional UUIDs
        master_uuid = self._ensure_uuid(master_flow_id) if master_flow_id else None

        # Prepare initial state data including raw_data and metadata
        state_data = initial_state_data or {}
        if raw_data:
            state_data["raw_data"] = raw_data
        if metadata:
            state_data["metadata"] = metadata

        # Add timeout to metadata (24 hours from creation)
        if "metadata" not in state_data:
            state_data["metadata"] = {}
        state_data["metadata"]["timeout_at"] = (
            datetime.utcnow() + timedelta(hours=24)
        ).isoformat()
        state_data["metadata"]["created_at"] = datetime.utcnow().isoformat()

        # Set status and current phase
        status = state_data.get("status", "initialized")
        current_phase = state_data.get("current_phase", "initialization")
        progress = state_data.get("progress_percentage", 0.0)

        # Create flow object
        flow = DiscoveryFlow(
            id=uuid.uuid4(),
            flow_id=parsed_flow_id,
            master_flow_id=master_uuid,
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            user_id=user_id or str(uuid.uuid4()),
            flow_name=description or f"Discovery Flow {str(parsed_flow_id)[:8]}",
            status=status,
            current_phase=current_phase,
            progress_percentage=progress,
            crewai_state_data=state_data,
            data_import_id=(
                self._ensure_uuid(data_import_id) if data_import_id else None
            ),
            learning_scope="engagement",
            memory_isolation_level="strict",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(flow)
        await self.db.commit()
        await self.db.refresh(flow)

        logger.info(
            f"✅ Created discovery flow: {flow.flow_id} with timeout at {state_data['metadata']['timeout_at']}"
        )
        return flow

    async def update_phase_completion(
        self,
        flow_id: str,
        phase: str,
        data: Optional[Dict[str, Any]] = None,
        completed: bool = False,
        agent_insights: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[DiscoveryFlow]:
        """Update phase completion status and data"""

        # Ensure flow_id is UUID
        flow_uuid = self._ensure_uuid(flow_id)

        # Map phase names to boolean fields
        phase_field_map = {
            "data_import": "data_import_completed",
            "field_mapping": "field_mapping_completed",
            "data_cleansing": "data_cleansing_completed",
            "asset_inventory": "asset_inventory_completed",
            "dependency_analysis": "dependency_analysis_completed",
            "tech_debt_assessment": "tech_debt_assessment_completed",
        }

        # Prepare update values
        update_values = {}

        # Update phase completion boolean
        if phase in phase_field_map and completed:
            update_values[phase_field_map[phase]] = True

        # Update current phase
        update_values["current_phase"] = phase
        update_values["updated_at"] = datetime.utcnow()

        # Update phase and agent state data
        if data or agent_insights:
            # Get existing flow to merge state data
            existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
            if existing_flow:
                state_data = existing_flow.crewai_state_data or {}

                # Update phase data
                if data:
                    state_data[phase] = data

                # Merge agent insights
                if agent_insights:
                    existing_insights = state_data.get("agent_insights", [])
                    existing_insights.extend(agent_insights)
                    state_data["agent_insights"] = existing_insights

                # Extract processing statistics to root level
                processing_fields = [
                    "records_processed",
                    "records_total",
                    "records_valid",
                    "records_failed",
                ]
                for field in processing_fields:
                    if data and field in data:
                        state_data[field] = data[field]

                update_values["crewai_state_data"] = state_data

        # Calculate progress
        progress = await self._calculate_progress(flow_id, phase, completed)
        update_values["progress_percentage"] = progress

        # Execute update
        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(**update_values)
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Invalidate cache after update
        updated_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if updated_flow:
            await self._invalidate_flow_cache(updated_flow)

        # 🔧 CC FIX: Check if all required phases are complete and auto-complete flow
        if updated_flow and completed:
            try:
                await self._check_and_complete_flow_if_ready(updated_flow)
            except Exception as completion_error:
                logger.error(
                    f"❌ Error during flow completion check for {flow_id}: {completion_error}"
                )
                # Don't fail the main operation if completion check fails

        return updated_flow

    async def update_flow_status(
        self, flow_id: str, status: str, progress_percentage: Optional[float] = None
    ) -> Optional[DiscoveryFlow]:
        """Update discovery flow status"""

        # Ensure flow_id is UUID
        flow_uuid = self._ensure_uuid(flow_id)

        # Get existing flow to merge state data
        existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not existing_flow:
            logger.error(f"Flow not found for status update: {flow_id}")
            return None

        # Get existing state data
        state_data = existing_flow.crewai_state_data or {}

        # Update status in state data
        state_data["status"] = status

        # Special handling for waiting_for_approval status
        if status == "waiting_for_approval":
            state_data["awaiting_user_approval"] = True
            # Also update current_phase to field_mapping
            update_values = {
                "status": status,
                "current_phase": "field_mapping",
                "crewai_state_data": state_data,
            }
        else:
            update_values = {"status": status, "crewai_state_data": state_data}

        # Update progress if provided
        if progress_percentage is not None:
            update_values["progress_percentage"] = progress_percentage

        # Always update timestamp
        update_values["updated_at"] = datetime.utcnow()

        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(**update_values)
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Invalidate cache after update
        updated_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if updated_flow:
            await self._invalidate_flow_cache(updated_flow)

        return updated_flow

    async def mark_flow_complete(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Mark flow as complete"""

        # Ensure flow_id is UUID
        flow_uuid = self._ensure_uuid(flow_id)

        # Get existing flow to update state data
        existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not existing_flow:
            return None

        # Update state data
        state_data = existing_flow.crewai_state_data or {}
        state_data["status"] = "complete"
        state_data["completed_at"] = datetime.utcnow().isoformat()

        # Calculate final readiness scores
        from app.services.crewai_flows.readiness_calculator import (
            calculate_readiness_scores,
        )

        readiness_scores = calculate_readiness_scores(state_data)
        state_data["readiness_scores"] = readiness_scores

        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(
                status="complete",
                progress_percentage=100.0,
                completed_at=datetime.utcnow(),
                assessment_ready=True,
                crewai_state_data=state_data,
                updated_at=datetime.utcnow(),
            )
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Invalidate cache after update
        updated_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if updated_flow:
            await self._invalidate_flow_cache(updated_flow)

        return updated_flow

    async def complete_discovery_flow(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """
        Complete discovery flow and prepare for assessment handoff.
        This method wraps mark_flow_complete with additional discovery-specific logic.
        """
        try:
            logger.info(f"🏁 Completing discovery flow: {flow_id}")

            # Use the existing mark_flow_complete method
            completed_flow = await self.mark_flow_complete(flow_id)

            if not completed_flow:
                logger.error(f"❌ Failed to complete flow {flow_id} - flow not found")
                return None

            # Update master flow state as well
            await self._update_master_flow_completion(flow_id)

            logger.info(f"✅ Discovery flow completed successfully: {flow_id}")
            return completed_flow

        except Exception as e:
            logger.error(f"❌ Failed to complete discovery flow {flow_id}: {e}")
            return None

    async def _check_and_complete_flow_if_ready(self, flow: DiscoveryFlow) -> bool:
        """
        Check if all required phases are complete and automatically complete the flow.

        Args:
            flow: The discovery flow to check

        Returns:
            True if flow was completed, False otherwise
        """
        try:
            # Define the required phases for completion (all 6 phases per spec)
            required_phases = {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed,
            }

            # Check if all required phases are complete
            all_phases_complete = all(required_phases.values())

            logger.info(
                f"🔍 Flow {flow.flow_id} phase completion status: {required_phases}, "
                f"all_complete={all_phases_complete}, current_status={flow.status}"
            )

            # Only complete if all phases are done and flow is not already complete
            if all_phases_complete and flow.status not in ["complete", "completed"]:
                logger.info(
                    f"🎯 Auto-completing flow {flow.flow_id} - all required phases complete"
                )
                # Use mark_flow_complete directly to avoid potential recursion
                await self.mark_flow_complete(str(flow.flow_id))
                # Update master flow state separately
                await self._update_master_flow_completion(str(flow.flow_id))
                return True

            return False

        except Exception as e:
            logger.error(
                f"❌ Error checking flow completion readiness for {flow.flow_id}: {e}"
            )
            return False

    async def _update_master_flow_completion(self, flow_id: str) -> bool:
        """
        Update the master flow state to completed status.

        Args:
            flow_id: The flow ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            # Create master repo with same context
            master_repo = CrewAIFlowStateExtensionsRepository(
                db=self.db,
                client_account_id=str(self.client_account_id),
                engagement_id=str(self.engagement_id),
                user_id="system",
            )

            # Update master flow status
            await master_repo.update_flow_status(
                flow_id=flow_id,
                status="completed",
                phase_data={
                    "completed_by": "discovery_flow_completion",
                    "completion_timestamp": datetime.utcnow().isoformat(),
                },
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "flow_completed",
                    "source": "discovery_flow_completion",
                    "message": "Discovery flow completed successfully - all phases finished",
                },
            )

            logger.info(f"✅ Master flow state updated to completed for: {flow_id}")
            return True

        except Exception as e:
            logger.warning(
                f"⚠️ Failed to update master flow completion for {flow_id}: {e}"
            )
            # Don't fail the whole operation if master flow update fails
            return False

    async def delete_flow(self, flow_id: str) -> bool:
        """Delete discovery flow"""
        try:
            # Ensure flow_id is UUID
            flow_uuid = self._ensure_uuid(flow_id)

            # Delete the flow
            stmt = delete(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            if result.rowcount > 0:
                logger.info(f"✅ Deleted discovery flow: {flow_id}")
                return True
            else:
                logger.warning(f"⚠️ No flow found to delete: {flow_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to delete flow {flow_id}: {e}")
            await self.db.rollback()
            return False

    async def _calculate_progress(
        self, flow_id: str, current_phase: str, phase_completed: bool
    ) -> float:
        """Calculate overall progress percentage"""

        # Get current flow state
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not flow:
            return 0.0

        # Phase weights
        phase_weights = {
            "data_import": 16.7,
            "field_mapping": 16.7,
            "data_cleansing": 16.6,
            "asset_inventory": 16.7,
            "dependency_analysis": 16.7,
            "tech_debt_assessment": 16.6,
        }

        # Calculate total progress
        total_progress = 0.0

        # Add progress for completed phases
        if flow.data_import_completed:
            total_progress += phase_weights["data_import"]
        if flow.field_mapping_completed:
            total_progress += phase_weights["field_mapping"]
        if flow.data_cleansing_completed:
            total_progress += phase_weights["data_cleansing"]
        if flow.asset_inventory_completed:
            total_progress += phase_weights["asset_inventory"]
        if flow.dependency_analysis_completed:
            total_progress += phase_weights["dependency_analysis"]
        if flow.tech_debt_assessment_completed:
            total_progress += phase_weights["tech_debt_assessment"]

        # If current phase is completed but not yet reflected in booleans
        if phase_completed and current_phase in phase_weights:
            phase_field_map = {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed,
            }

            if not phase_field_map.get(current_phase, False):
                total_progress += phase_weights[current_phase]

        return min(100.0, round(total_progress, 1))

    async def cleanup_stuck_flows(self, hours_threshold: int = 24) -> int:
        """Clean up flows that have been stuck for more than the threshold"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)

            # Find stuck flows
            stmt = (
                update(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.client_account_id == self.client_account_id,
                        DiscoveryFlow.engagement_id == self.engagement_id,
                        DiscoveryFlow.status.in_(["active", "initialized", "running"]),
                        DiscoveryFlow.progress_percentage == 0.0,
                        DiscoveryFlow.created_at < cutoff_time,
                    )
                )
                .values(
                    status="failed",
                    error_message=f"Flow timed out after {hours_threshold} hours with no progress",
                    error_phase="timeout",
                    error_details={
                        "reason": "no_progress",
                        "threshold_hours": hours_threshold,
                    },
                    updated_at=datetime.utcnow(),
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            count = result.rowcount
            if count > 0:
                logger.info(
                    f"🧹 Cleaned up {count} stuck flows older than {hours_threshold} hours"
                )

            return count

        except Exception as e:
            logger.error(f"❌ Failed to cleanup stuck flows: {e}")
            await self.db.rollback()
            return 0
