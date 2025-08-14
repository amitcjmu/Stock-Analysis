"""
CrewAI Flow State Extensions Repository
Repository for managing master flow records in crewai_flow_state_extensions table.
This is the master table that coordinates all CrewAI flows (Discovery, Assessment, Planning, etc.)
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class CrewAIFlowStateExtensionsRepository(ContextAwareRepository):
    """
    Repository for master CrewAI flow state management.
    This is the central coordination table for all flow types.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str = None,
        user_id: Optional[str] = None,
    ):
        # Handle None values and invalid UUIDs with proper fallbacks
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

        # Safely convert client_account_id
        try:
            if client_account_id and client_account_id != "None":
                # Handle if already a UUID object
                if isinstance(client_account_id, uuid.UUID):
                    parsed_client_id = client_account_id
                else:
                    parsed_client_id = uuid.UUID(str(client_account_id))
            else:
                parsed_client_id = demo_client_id
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid client_account_id '{client_account_id}', using demo fallback"
            )
            parsed_client_id = demo_client_id

        # Safely convert engagement_id
        try:
            if engagement_id and engagement_id != "None":
                # Handle if already a UUID object
                if isinstance(engagement_id, uuid.UUID):
                    parsed_engagement_id = engagement_id
                else:
                    parsed_engagement_id = uuid.UUID(str(engagement_id))
            else:
                parsed_engagement_id = demo_engagement_id
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid engagement_id '{engagement_id}', using demo fallback"
            )
            parsed_engagement_id = demo_engagement_id

        # Initialize parent with proper parameters
        super().__init__(
            db=db,
            model_class=CrewAIFlowStateExtensions,
            client_account_id=str(parsed_client_id),
            engagement_id=str(parsed_engagement_id),
        )
        self.client_account_id = str(parsed_client_id)
        self.engagement_id = str(parsed_engagement_id)

    async def create_master_flow(
        self,
        flow_id: str,  # CrewAI generated flow ID
        flow_type: str,  # 'discovery', 'assessment', 'planning', 'execution'
        user_id: str = None,
        flow_name: str = None,
        flow_configuration: Dict[str, Any] = None,
        initial_state: Dict[str, Any] = None,
        auto_commit: bool = True,  # Allow controlling transaction behavior
    ) -> CrewAIFlowStateExtensions:
        """Create master flow record - this must be called before creating specific flow types"""

        # Use demo constants as defaults
        demo_client_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        demo_engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        uuid.UUID("33333333-3333-3333-3333-333333333333")

        # Validate and parse flow_id
        try:
            if isinstance(flow_id, uuid.UUID):
                parsed_flow_id = flow_id
            else:
                parsed_flow_id = uuid.UUID(flow_id)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid CrewAI Flow ID provided: {flow_id}, error: {e}")
            raise ValueError(
                f"Invalid CrewAI Flow ID: {flow_id}. Must be a valid UUID."
            )

        # Validate flow type
        valid_flow_types = [
            "discovery",
            "assessment",
            "collection",
            "planning",
            "execution",
            "modernize",
            "finops",
            "observability",
            "decommission",
        ]
        if flow_type not in valid_flow_types:
            raise ValueError(
                f"Invalid flow_type: {flow_type}. Must be one of: {valid_flow_types}"
            )

        # Generate flow name if not provided
        if not flow_name:
            flow_name = f"{flow_type.title()} Flow {str(flow_id)[:8]}"

        # Safely handle user_id
        safe_user_id = user_id or "test-user"  # Don't try to convert to UUID

        master_flow = CrewAIFlowStateExtensions(
            flow_id=parsed_flow_id,  # This is the master flow ID that other tables reference
            client_account_id=(
                uuid.UUID(self.client_account_id)
                if self.client_account_id
                else demo_client_id
            ),
            engagement_id=(
                uuid.UUID(self.engagement_id)
                if self.engagement_id
                else demo_engagement_id
            ),
            user_id=safe_user_id,  # Store as string, not UUID
            flow_type=flow_type,
            flow_name=flow_name,
            flow_status="initialized",
            flow_configuration=flow_configuration or {},
            flow_persistence_data=initial_state or {},
            agent_collaboration_log=[],
            phase_execution_times={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(master_flow)

        # FIX: Allow controlling transaction behavior for atomic operations
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(master_flow)
            logger.info(
                f"✅ Master flow created with commit: flow_id={flow_id}, type={flow_type}"
            )
        else:
            await self.db.flush()
            await self.db.refresh(master_flow)
            logger.info(
                f"✅ Master flow created with flush: flow_id={flow_id}, type={flow_type}"
            )

        return master_flow

    async def get_by_flow_id(self, flow_id: str) -> Optional[CrewAIFlowStateExtensions]:
        """Get master flow by CrewAI Flow ID"""
        try:
            # Convert flow_id to UUID for database query
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None

            # Convert context UUIDs
            try:
                client_uuid = uuid.UUID(self.client_account_id)
                engagement_uuid = uuid.UUID(self.engagement_id)
            except (ValueError, TypeError) as e:
                logger.error(
                    f"❌ Invalid context UUID - client: {self.client_account_id}, "
                    f"engagement: {self.engagement_id}, error: {e}"
                )
                return None

            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )

            result = await self.db.execute(stmt)
            flow = result.scalar_one_or_none()

            # Ensure flow has a valid status (fix for NULL status issue)
            if flow and flow.flow_status is None:
                logger.warning(
                    f"⚠️ Flow {flow_id} has NULL status, setting to 'processing'"
                )
                flow.flow_status = "processing"
                await self.db.commit()

            return flow

        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id: {e}")
            return None

    async def get_by_flow_id_global(
        self, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        """Get master flow by CrewAI Flow ID without tenant filtering (for duplicate checking)

        SECURITY WARNING: This method bypasses tenant isolation and should only be used
        for system-level operations like duplicate checking. Never expose this to user-facing APIs.
        """
        # Log security audit trail
        logger.warning(
            f"🔒 SECURITY AUDIT: Global query attempted for master flow_id={flow_id} by client={self.client_account_id}"
        )

        try:
            # Convert flow_id to UUID for database query
            try:
                flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id UUID format: {flow_id}, error: {e}")
                return None

            # SECURITY: First check if the flow belongs to the current client
            tenant_check = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            result = await self.db.execute(tenant_check)
            flow = result.scalar_one_or_none()

            if flow:
                # Flow belongs to current client, safe to return
                # Ensure flow has a valid status (fix for NULL status issue)
                if flow.flow_status is None:
                    logger.warning(
                        f"⚠️ Flow {flow_id} has NULL status, setting to 'processing'"
                    )
                    flow.flow_status = "processing"
                    await self.db.commit()
                return flow

            # SECURITY: Only allow global query for system operations
            # In production, this should check for system/admin privileges
            logger.warning(
                f"🔒 SECURITY: Denying global query for master flow {flow_id} - "
                f"does not belong to client {self.client_account_id}"
            )
            return None

        except Exception as e:
            logger.error(f"❌ Database error in get_by_flow_id_global: {e}")
            return None

    def _ensure_json_serializable(
        self, obj: Any, _visited: Optional[set] = None, _depth: int = 0
    ) -> Any:
        """
        Recursively convert non-JSON serializable objects to serializable format.
        Handles UUID, datetime, and other common non-serializable types.

        This method is critical for preventing JSON serialization errors when storing
        phase_data, collaboration_entry, or metadata that may contain UUID objects
        from CrewAI flows or other sources.

        Common sources of UUID objects:
        - RequestContext fields (client_account_id, engagement_id)
        - Flow IDs from CrewAI
        - Database record IDs
        - Nested data structures from phase results

        Args:
            obj: Object to serialize
            _visited: Set of visited object IDs to prevent circular references
            _depth: Current recursion depth to prevent excessive nesting
        """
        # Initialize visited set on first call
        if _visited is None:
            _visited = set()

        # Prevent excessive recursion depth
        MAX_DEPTH = 50
        if _depth > MAX_DEPTH:
            logger.warning(
                f"Maximum serialization depth {MAX_DEPTH} reached, converting to string"
            )
            return str(obj)

        try:
            if isinstance(obj, dict):
                # Check for circular reference
                obj_id = id(obj)
                if obj_id in _visited:
                    return "<circular reference: dict>"
                _visited.add(obj_id)

                result = {}
                for key, value in obj.items():
                    result[key] = self._ensure_json_serializable(
                        value, _visited, _depth + 1
                    )
                _visited.discard(obj_id)
                return result

            elif isinstance(obj, list):
                # Check for circular reference
                obj_id = id(obj)
                if obj_id in _visited:
                    return "<circular reference: list>"
                _visited.add(obj_id)

                result = [
                    self._ensure_json_serializable(item, _visited, _depth + 1)
                    for item in obj
                ]
                _visited.discard(obj_id)
                return result

            elif isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, (str, int, float, bool, type(None))):
                # These types are already JSON serializable
                return obj
            elif hasattr(obj, "__dict__"):
                # Check for circular reference
                obj_id = id(obj)
                if obj_id in _visited:
                    return f"<circular reference: {type(obj).__name__}>"
                _visited.add(obj_id)

                # Handle custom objects by converting to dict
                logger.debug(f"Converting object of type {type(obj).__name__} to dict")
                result = self._ensure_json_serializable(
                    obj.__dict__, _visited, _depth + 1
                )
                _visited.discard(obj_id)
                return result
            else:
                # For any other type, convert to string
                logger.warning(
                    f"Converting unknown type {type(obj).__name__} to string: {obj}"
                )
                return str(obj)
        except Exception as e:
            logger.error(
                f"Error in _ensure_json_serializable for object {type(obj).__name__}: {e}"
            )
            # As a last resort, convert to string
            return str(obj)

    async def update_flow_status(
        self,
        flow_id: str,
        status: str,
        phase_data: Dict[str, Any] = None,
        collaboration_entry: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> CrewAIFlowStateExtensions:
        """Update master flow status and state"""

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid UUID format in update_flow_status: {e}")
            raise ValueError(f"Invalid UUID format: {e}")

        # Build update values
        update_values = {"flow_status": status, "updated_at": datetime.utcnow()}

        # Get existing flow to merge data
        existing_flow = await self.get_by_flow_id(flow_id)
        if existing_flow:
            # Update persistence data - ensure JSON serializable
            if phase_data:
                persistence_data = existing_flow.flow_persistence_data or {}
                # Ensure phase_data is JSON serializable before updating
                logger.debug(
                    f"🔍 Serializing phase_data for flow {flow_id} with keys: {list(phase_data.keys())}"
                )
                serializable_phase_data = self._ensure_json_serializable(phase_data)
                persistence_data.update(serializable_phase_data)
                update_values["flow_persistence_data"] = persistence_data
                logger.debug(
                    f"✅ Successfully serialized phase_data for flow {flow_id}"
                )

            # Update collaboration log - ensure JSON serializable
            if collaboration_entry:
                collaboration_log = existing_flow.agent_collaboration_log or []
                # Ensure collaboration_entry is JSON serializable
                serializable_entry = self._ensure_json_serializable(collaboration_entry)
                collaboration_log.append(serializable_entry)
                # Keep only last 100 entries to prevent bloat
                if len(collaboration_log) > 100:
                    collaboration_log = collaboration_log[-100:]
                update_values["agent_collaboration_log"] = collaboration_log

            # Update metadata (ADR-012 sync metadata) - ensure JSON serializable
            if metadata:
                flow_metadata = existing_flow.flow_metadata or {}
                # Ensure metadata is JSON serializable
                serializable_metadata = self._ensure_json_serializable(metadata)
                flow_metadata.update(serializable_metadata)
                update_values["flow_metadata"] = flow_metadata

        # Execute update
        stmt = (
            update(CrewAIFlowStateExtensions)
            .where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )
            .values(**update_values)
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Return updated flow
        return await self.get_by_flow_id(flow_id)

    async def get_flows_by_type(
        self, flow_type: str, limit: int = 10
    ) -> List[CrewAIFlowStateExtensions]:
        """Get master flows by type for the current client/engagement"""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            stmt = (
                select(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_type == flow_type,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .order_by(desc(CrewAIFlowStateExtensions.created_at))
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"❌ Failed to get flows by type {flow_type}: {e}")
            return []

    async def get_active_flows(
        self, limit: int = 10, flow_type: Optional[str] = None
    ) -> List[CrewAIFlowStateExtensions]:
        """Get all active master flows for the current client/engagement"""
        try:
            # Check if required context values are present
            if not self.client_account_id:
                logger.warning(
                    f"Missing required context for get_active_flows: "
                    f"client_account_id={self.client_account_id}"
                )
                return []

            client_uuid = uuid.UUID(self.client_account_id)

            active_statuses = [
                "initialized",
                "active",
                "processing",
                "paused",
                "waiting_for_approval",
            ]

            # Build query conditions
            conditions = [
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
                CrewAIFlowStateExtensions.flow_status.in_(active_statuses),
            ]

            # Only filter by engagement_id if it's provided
            if self.engagement_id:
                engagement_uuid = uuid.UUID(self.engagement_id)
                conditions.append(
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid
                )

            # Add flow type filter if specified
            if flow_type:
                conditions.append(CrewAIFlowStateExtensions.flow_type == flow_type)

            stmt = (
                select(CrewAIFlowStateExtensions)
                .where(and_(*conditions))
                .order_by(desc(CrewAIFlowStateExtensions.created_at))
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            flows = result.scalars().all()

            logger.info(
                f"Found {len(flows)} active flows (flow_type: {flow_type}, limit: {limit})"
            )
            return flows

        except Exception as e:
            logger.error(f"❌ Failed to get active flows: {e}")
            return []

    async def get_flows_by_engagement(
        self, engagement_id: str, flow_type: Optional[str] = None, limit: int = 50
    ) -> List[CrewAIFlowStateExtensions]:
        """Get flows for a specific engagement"""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(engagement_id)

            # Build query conditions
            conditions = [
                CrewAIFlowStateExtensions.client_account_id == client_uuid,
                CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
            ]

            # Add flow type filter if specified
            if flow_type:
                conditions.append(CrewAIFlowStateExtensions.flow_type == flow_type)

            stmt = (
                select(CrewAIFlowStateExtensions)
                .where(and_(*conditions))
                .order_by(desc(CrewAIFlowStateExtensions.created_at))
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            flows = result.scalars().all()

            logger.info(f"Retrieved {len(flows)} flows for engagement {engagement_id}")
            return flows

        except Exception as e:
            logger.error(f"❌ Failed to get flows by engagement {engagement_id}: {e}")
            return []

    async def delete_master_flow(self, flow_id: str) -> bool:
        """Delete master flow and all subordinate flows (cascade)"""
        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            stmt = delete(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid,
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"✅ Master flow deleted: {flow_id}")
            else:
                logger.warning(f"⚠️ Master flow not found for deletion: {flow_id}")

            return deleted

        except Exception as e:
            logger.error(f"❌ Failed to delete master flow {flow_id}: {e}")
            return False

    async def get_master_flow_by_id(
        self, flow_id: str
    ) -> Optional[CrewAIFlowStateExtensions]:
        """Get master flow by ID (with multi-tenant security)"""
        try:
            # Validate and parse flow_id
            if isinstance(flow_id, uuid.UUID):
                parsed_flow_id = flow_id
            else:
                parsed_flow_id = uuid.UUID(flow_id)

            query = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == parsed_flow_id,
                    (
                        CrewAIFlowStateExtensions.client_account_id
                        == uuid.UUID(self.client_account_id)
                        if self.client_account_id
                        else None
                    ),
                    (
                        CrewAIFlowStateExtensions.engagement_id
                        == uuid.UUID(self.engagement_id)
                        if self.engagement_id
                        else None
                    ),
                )
            )

            result = await self.db.execute(query)
            master_flow = result.scalar_one_or_none()

            if master_flow:
                logger.info(f"✅ Found master flow: {flow_id}")
            else:
                logger.warning(f"⚠️ Master flow not found: {flow_id}")

            return master_flow

        except Exception as e:
            logger.error(f"❌ Error getting master flow by ID: {e}")
            raise

    async def get_master_flow_summary(self) -> Dict[str, Any]:
        """Get summary of master flow coordination status"""
        try:
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get master flow statistics
            stmt = select(
                func.count(CrewAIFlowStateExtensions.id).label("total_master_flows"),
                func.count(func.distinct(CrewAIFlowStateExtensions.flow_type)).label(
                    "unique_flow_types"
                ),
            ).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == client_uuid,
                    CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                )
            )

            result = await self.db.execute(stmt)
            stats = result.first()

            # Get flow type distribution
            type_stmt = (
                select(
                    CrewAIFlowStateExtensions.flow_type,
                    func.count(CrewAIFlowStateExtensions.id).label("count"),
                )
                .where(
                    and_(
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .group_by(CrewAIFlowStateExtensions.flow_type)
            )

            type_result = await self.db.execute(type_stmt)
            type_stats = {row.flow_type: row.count for row in type_result}

            # Get status distribution
            status_stmt = (
                select(
                    CrewAIFlowStateExtensions.flow_status,
                    func.count(CrewAIFlowStateExtensions.id).label("count"),
                )
                .where(
                    and_(
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .group_by(CrewAIFlowStateExtensions.flow_status)
            )

            status_result = await self.db.execute(status_stmt)
            status_stats = {row.flow_status: row.count for row in status_result}

            return {
                "total_master_flows": stats.total_master_flows,
                "unique_flow_types": stats.unique_flow_types,
                "flow_type_distribution": type_stats,
                "flow_status_distribution": status_stats,
                "master_coordination_health": (
                    "healthy"
                    if stats.total_master_flows > 0
                    else "missing_master_flows"
                ),
            }

        except Exception as e:
            logger.error(f"Error in get_master_flow_summary: {e}")
            return {
                "total_master_flows": 0,
                "unique_flow_types": 0,
                "flow_type_distribution": {},
                "flow_status_distribution": {},
                "master_coordination_health": "error",
            }

    # Analytics methods for Master Flow State Enrichment
    def _is_enrichment_enabled(self) -> bool:
        """Check if master state enrichment is enabled via feature flag."""
        return os.getenv("MASTER_STATE_ENRICHMENT_ENABLED", "true").lower() == "true"

    async def add_phase_transition(
        self,
        flow_id: str,
        phase: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a phase transition entry to the master flow record.

        Appends to phase_transitions JSONB array, maintaining recent transitions.

        Args:
            flow_id: The flow ID
            phase: Phase name (e.g., 'initialization', 'discovery', 'analysis')
            status: Phase status (e.g., 'processing', 'completed', 'failed')
            metadata: Optional additional metadata about the transition
        """
        if not self._is_enrichment_enabled():
            logger.debug(
                f"Master state enrichment disabled, skipping phase transition for {flow_id}"
            )
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get existing flow
            existing_flow = await self.get_by_flow_id(flow_id)
            if not existing_flow:
                logger.warning(f"Flow {flow_id} not found for phase transition update")
                return

            # Prepare transition entry
            transition_entry = {
                "phase": phase,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": (
                    self._ensure_json_serializable(metadata) if metadata else {}
                ),
            }

            # Update phase transitions array
            phase_transitions = existing_flow.phase_transitions or []
            phase_transitions.append(self._ensure_json_serializable(transition_entry))

            # Keep only the last 50 transitions to prevent unbounded growth
            if len(phase_transitions) > 50:
                phase_transitions = phase_transitions[-50:]

            # Update the flow record
            stmt = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_uuid,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .values(
                    phase_transitions=phase_transitions, updated_at=datetime.utcnow()
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

            logger.debug(
                f"✅ Added phase transition for flow {flow_id}: {phase} -> {status}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to add phase transition for flow {flow_id}: {e}")
            await self.db.rollback()

    async def record_phase_execution_time(
        self, flow_id: str, phase: str, execution_time_ms: float
    ) -> None:
        """Record execution time for a phase in the master flow record.

        Updates phase_execution_times JSONB with timing data.

        Args:
            flow_id: The flow ID
            phase: Phase name
            execution_time_ms: Execution time in milliseconds
        """
        if not self._is_enrichment_enabled():
            logger.debug(
                f"Master state enrichment disabled, skipping execution time for {flow_id}"
            )
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get existing flow
            existing_flow = await self.get_by_flow_id(flow_id)
            if not existing_flow:
                logger.warning(f"Flow {flow_id} not found for execution time update")
                return

            # Update phase execution times
            phase_execution_times = existing_flow.phase_execution_times or {}
            phase_execution_times[phase] = {
                "execution_time_ms": float(execution_time_ms),
                "recorded_at": datetime.utcnow().isoformat(),
            }

            # Update the flow record
            stmt = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_uuid,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .values(
                    phase_execution_times=self._ensure_json_serializable(
                        phase_execution_times
                    ),
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

            logger.debug(
                f"✅ Recorded execution time for flow {flow_id}, phase {phase}: {execution_time_ms}ms"
            )

        except Exception as e:
            logger.error(f"❌ Failed to record execution time for flow {flow_id}: {e}")
            await self.db.rollback()

    async def append_agent_collaboration(
        self, flow_id: str, entry: Dict[str, Any]
    ) -> None:
        """Append agent collaboration entry to the master flow record.

        Appends to agent_collaboration_log JSONB array, capped at 100 entries.

        Args:
            flow_id: The flow ID
            entry: Collaboration entry with agent activity details
        """
        if not self._is_enrichment_enabled():
            logger.debug(
                f"Master state enrichment disabled, skipping collaboration log for {flow_id}"
            )
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get existing flow
            existing_flow = await self.get_by_flow_id(flow_id)
            if not existing_flow:
                logger.warning(f"Flow {flow_id} not found for collaboration log update")
                return

            # Prepare collaboration entry
            collaboration_entry = self._ensure_json_serializable(
                {**entry, "timestamp": datetime.utcnow().isoformat()}
            )

            # Update collaboration log
            collaboration_log = existing_flow.agent_collaboration_log or []
            collaboration_log.append(collaboration_entry)

            # Keep only the last 100 entries to prevent unbounded growth
            if len(collaboration_log) > 100:
                collaboration_log = collaboration_log[-100:]

            # Update the flow record
            stmt = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_uuid,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .values(
                    agent_collaboration_log=collaboration_log,
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

            logger.debug(f"✅ Added collaboration entry for flow {flow_id}")

        except Exception as e:
            logger.error(
                f"❌ Failed to append collaboration entry for flow {flow_id}: {e}"
            )
            await self.db.rollback()

    async def update_memory_usage_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        """Update memory usage metrics for the master flow record.

        Updates memory_usage_metrics JSONB field.

        Args:
            flow_id: The flow ID
            metrics: Memory usage metrics (memory_mb, peak_memory_mb, etc.)
        """
        if not self._is_enrichment_enabled():
            logger.debug(
                f"Master state enrichment disabled, skipping memory metrics for {flow_id}"
            )
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get existing flow
            existing_flow = await self.get_by_flow_id(flow_id)
            if not existing_flow:
                logger.warning(f"Flow {flow_id} not found for memory metrics update")
                return

            # Update memory usage metrics
            memory_metrics = existing_flow.memory_usage_metrics or {}
            memory_metrics.update(
                self._ensure_json_serializable(
                    {**metrics, "last_updated": datetime.utcnow().isoformat()}
                )
            )

            # Update the flow record
            stmt = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_uuid,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .values(
                    memory_usage_metrics=memory_metrics, updated_at=datetime.utcnow()
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

            logger.debug(f"✅ Updated memory metrics for flow {flow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to update memory metrics for flow {flow_id}: {e}")
            await self.db.rollback()

    async def update_agent_performance_metrics(
        self, flow_id: str, metrics: Dict[str, Any]
    ) -> None:
        """Update agent performance metrics for the master flow record.

        Updates agent_performance_metrics JSONB field.

        Args:
            flow_id: The flow ID
            metrics: Agent performance metrics (response_time_ms, success_rate, etc.)
        """
        if not self._is_enrichment_enabled():
            logger.debug(
                f"Master state enrichment disabled, skipping performance metrics for {flow_id}"
            )
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get existing flow
            existing_flow = await self.get_by_flow_id(flow_id)
            if not existing_flow:
                logger.warning(
                    f"Flow {flow_id} not found for performance metrics update"
                )
                return

            # Update agent performance metrics
            performance_metrics = existing_flow.agent_performance_metrics or {}
            performance_metrics.update(
                self._ensure_json_serializable(
                    {**metrics, "last_updated": datetime.utcnow().isoformat()}
                )
            )

            # Update the flow record
            stmt = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_uuid,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .values(
                    agent_performance_metrics=performance_metrics,
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

            logger.debug(f"✅ Updated performance metrics for flow {flow_id}")

        except Exception as e:
            logger.error(
                f"❌ Failed to update performance metrics for flow {flow_id}: {e}"
            )
            await self.db.rollback()

    async def add_error_entry(
        self,
        flow_id: str,
        phase: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add error entry to the master flow record.

        Appends to error_history JSONB array, capped at 100 entries.

        Args:
            flow_id: The flow ID
            phase: Phase where error occurred
            error: Error message or type
            details: Optional additional error details
        """
        if not self._is_enrichment_enabled():
            logger.debug(
                f"Master state enrichment disabled, skipping error entry for {flow_id}"
            )
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get existing flow
            existing_flow = await self.get_by_flow_id(flow_id)
            if not existing_flow:
                logger.warning(f"Flow {flow_id} not found for error entry update")
                return

            # Prepare error entry
            error_entry = self._ensure_json_serializable(
                {
                    "phase": phase,
                    "error": error,
                    "details": details or {},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Update error history
            error_history = existing_flow.error_history or []
            error_history.append(error_entry)

            # Keep only the last 100 entries to prevent unbounded growth
            if len(error_history) > 100:
                error_history = error_history[-100:]

            # Update the flow record
            stmt = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_uuid,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .values(error_history=error_history, updated_at=datetime.utcnow())
            )

            await self.db.execute(stmt)
            await self.db.commit()

            logger.debug(f"✅ Added error entry for flow {flow_id} in phase {phase}")

        except Exception as e:
            logger.error(f"❌ Failed to add error entry for flow {flow_id}: {e}")
            await self.db.rollback()

    async def increment_retry_count(self, flow_id: str) -> None:
        """Increment retry count for the master flow record.

        Updates retry_count JSONB field.

        Args:
            flow_id: The flow ID
        """
        if not self._is_enrichment_enabled():
            logger.debug(
                f"Master state enrichment disabled, skipping retry count for {flow_id}"
            )
            return

        try:
            flow_uuid = uuid.UUID(flow_id) if isinstance(flow_id, str) else flow_id
            client_uuid = uuid.UUID(self.client_account_id)
            engagement_uuid = uuid.UUID(self.engagement_id)

            # Get existing flow
            existing_flow = await self.get_by_flow_id(flow_id)
            if not existing_flow:
                logger.warning(f"Flow {flow_id} not found for retry count update")
                return

            # Update retry count
            retry_count = existing_flow.retry_count or {"total_retries": 0}
            if isinstance(retry_count, dict):
                retry_count["total_retries"] = retry_count.get("total_retries", 0) + 1
                retry_count["last_retry"] = datetime.utcnow().isoformat()
            else:
                # Handle legacy integer retry_count
                retry_count = {
                    "total_retries": (
                        int(retry_count) + 1
                        if isinstance(retry_count, (int, float))
                        else 1
                    ),
                    "last_retry": datetime.utcnow().isoformat(),
                }

            # Update the flow record
            stmt = (
                update(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_uuid,
                        CrewAIFlowStateExtensions.client_account_id == client_uuid,
                        CrewAIFlowStateExtensions.engagement_id == engagement_uuid,
                    )
                )
                .values(
                    retry_count=self._ensure_json_serializable(retry_count),
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

            logger.debug(
                f"✅ Incremented retry count for flow {flow_id}: {retry_count['total_retries']}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to increment retry count for flow {flow_id}: {e}")
            await self.db.rollback()
