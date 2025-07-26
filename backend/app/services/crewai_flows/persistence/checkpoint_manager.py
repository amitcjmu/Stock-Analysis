"""
Checkpoint Manager for Flow State
Saves flow state at major steps to allow resuming from checkpoints
"""

import base64
import json
import logging
import pickle  # nosec B403 - Used only for backward compatibility
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class FlowCheckpoint:
    """Represents a flow checkpoint"""

    def __init__(
        self,
        flow_id: str,
        phase: str,
        checkpoint_id: str,
        state_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.flow_id = flow_id
        self.phase = phase
        self.checkpoint_id = checkpoint_id
        self.state_data = state_data
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()


class CheckpointManager:
    """
    Manages flow checkpoints for recovery and resumption
    """

    def __init__(self):
        self.checkpoints: Dict[str, List[FlowCheckpoint]] = {}
        self.max_checkpoints_per_flow = 10
        self.checkpoint_phases = [
            "data_import_validation",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "tech_debt_assessment",
        ]

    async def create_checkpoint(
        self,
        flow_id: str,
        phase: str,
        state: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a checkpoint for the current flow state

        Args:
            flow_id: The flow ID
            phase: Current phase name
            state: Flow state object
            metadata: Additional metadata to store

        Returns:
            checkpoint_id: Unique identifier for the checkpoint
        """
        try:
            # Generate checkpoint ID
            checkpoint_id = f"{flow_id}_{phase}_{datetime.utcnow().timestamp()}"

            # Serialize state data
            state_data = await self._serialize_state(state)

            # Create checkpoint
            checkpoint = FlowCheckpoint(
                flow_id=flow_id,
                phase=phase,
                checkpoint_id=checkpoint_id,
                state_data=state_data,
                metadata=metadata,
            )

            # Store checkpoint
            await self._store_checkpoint(checkpoint)

            # Cleanup old checkpoints
            await self._cleanup_old_checkpoints(flow_id)

            logger.info(
                f"✅ Created checkpoint {checkpoint_id} for flow {flow_id} at phase {phase}"
            )

            return checkpoint_id

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            raise

    async def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore flow state from a checkpoint

        Args:
            checkpoint_id: The checkpoint ID to restore

        Returns:
            Restored state data or None if not found
        """
        try:
            checkpoint = await self._load_checkpoint(checkpoint_id)

            if not checkpoint:
                logger.warning(f"Checkpoint {checkpoint_id} not found")
                return None

            # Deserialize state
            state_data = await self._deserialize_state(checkpoint.state_data)

            logger.info(f"✅ Restored checkpoint {checkpoint_id}")

            return {
                "flow_id": checkpoint.flow_id,
                "phase": checkpoint.phase,
                "state": state_data,
                "metadata": checkpoint.metadata,
                "created_at": checkpoint.created_at,
            }

        except Exception as e:
            logger.error(f"Failed to restore checkpoint: {e}")
            return None

    async def get_latest_checkpoint(
        self, flow_id: str, phase: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest checkpoint for a flow

        Args:
            flow_id: The flow ID
            phase: Optional phase filter

        Returns:
            Latest checkpoint data or None
        """
        try:
            checkpoints = await self._get_flow_checkpoints(flow_id)

            if phase:
                checkpoints = [cp for cp in checkpoints if cp.phase == phase]

            if not checkpoints:
                return None

            # Sort by creation time and get latest
            latest = max(checkpoints, key=lambda cp: cp.created_at)

            return await self.restore_checkpoint(latest.checkpoint_id)

        except Exception as e:
            logger.error(f"Failed to get latest checkpoint: {e}")
            return None

    async def list_checkpoints(self, flow_id: str) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a flow

        Args:
            flow_id: The flow ID

        Returns:
            List of checkpoint summaries
        """
        try:
            checkpoints = await self._get_flow_checkpoints(flow_id)

            return [
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "phase": cp.phase,
                    "created_at": cp.created_at.isoformat(),
                    "metadata": cp.metadata,
                }
                for cp in sorted(
                    checkpoints, key=lambda cp: cp.created_at, reverse=True
                )
            ]

        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a specific checkpoint

        Args:
            checkpoint_id: The checkpoint ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            async with AsyncSessionLocal():
                # For now, using in-memory storage
                # In production, this would delete from database
                for flow_id, checkpoints in self.checkpoints.items():
                    self.checkpoints[flow_id] = [
                        cp for cp in checkpoints if cp.checkpoint_id != checkpoint_id
                    ]

            logger.info(f"✅ Deleted checkpoint {checkpoint_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False

    async def cleanup_flow_checkpoints(self, flow_id: str) -> int:
        """
        Clean up all checkpoints for a flow

        Args:
            flow_id: The flow ID

        Returns:
            Number of checkpoints deleted
        """
        try:
            if flow_id in self.checkpoints:
                count = len(self.checkpoints[flow_id])
                del self.checkpoints[flow_id]
                logger.info(f"✅ Cleaned up {count} checkpoints for flow {flow_id}")
                return count
            return 0

        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")
            return 0

    async def _serialize_state(self, state: Any) -> Dict[str, Any]:
        """Serialize flow state for storage"""
        try:
            # Get state attributes
            state_dict = {}

            # Common attributes to serialize
            attributes = [
                "flow_id",
                "status",
                "current_phase",
                "progress_percentage",
                "phase_completion",
                "raw_data",
                "field_mappings",
                "cleaned_data",
                "asset_inventory",
                "app_server_dependencies",
                "app_app_dependencies",
                "technical_debt_assessment",
                "agent_insights",
                "errors",
                "client_account_id",
                "engagement_id",
                "user_id",
            ]

            for attr in attributes:
                if hasattr(state, attr):
                    value = getattr(state, attr)
                    # Handle complex objects
                    if isinstance(
                        value, (list, dict, str, int, float, bool, type(None))
                    ):
                        state_dict[attr] = value
                    else:
                        # Serialize complex objects as JSON
                        try:
                            # Try JSON first for safety
                            json_data = json.dumps(value, default=str)
                            state_dict[attr] = {
                                "_serialized": True,
                                "format": "json",
                                "data": json_data,
                            }
                        except Exception:
                            # Fall back to string representation
                            try:
                                state_dict[attr] = {
                                    "_serialized": True,
                                    "format": "str",
                                    "data": str(value),
                                }
                            except Exception:
                                # Skip if can't serialize
                                logger.warning(f"Could not serialize attribute: {attr}")

            return state_dict

        except Exception as e:
            logger.error(f"Failed to serialize state: {e}")
            raise

    async def _deserialize_state(self, state_data: Dict[str, Any]) -> Any:
        """Deserialize flow state from storage"""
        try:
            # Create a simple namespace to hold state
            from types import SimpleNamespace

            state = SimpleNamespace()

            for key, value in state_data.items():
                if isinstance(value, dict) and value.get("_serialized"):
                    # Deserialize complex object
                    try:
                        format_type = value.get(
                            "format", "pickle"
                        )  # Default to pickle for backward compatibility

                        if format_type == "json":
                            # New JSON format
                            deserialized = json.loads(value["data"])
                            setattr(state, key, deserialized)
                        elif format_type == "str":
                            # String representation
                            setattr(state, key, value["data"])
                        else:
                            # Legacy pickle format - only for backward compatibility
                            deserialized = pickle.loads(
                                base64.b64decode(value["data"])
                            )  # nosec B301
                            setattr(state, key, deserialized)
                    except Exception:
                        logger.warning(f"Could not deserialize attribute: {key}")
                        setattr(state, key, None)
                else:
                    setattr(state, key, value)

            return state

        except Exception as e:
            logger.error(f"Failed to deserialize state: {e}")
            raise

    async def _store_checkpoint(self, checkpoint: FlowCheckpoint):
        """Store checkpoint in persistence layer"""
        # For now, using in-memory storage
        # In production, this would store in database
        if checkpoint.flow_id not in self.checkpoints:
            self.checkpoints[checkpoint.flow_id] = []

        self.checkpoints[checkpoint.flow_id].append(checkpoint)

    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[FlowCheckpoint]:
        """Load checkpoint from persistence layer"""
        for flow_id, checkpoints in self.checkpoints.items():
            for cp in checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    return cp
        return None

    async def _get_flow_checkpoints(self, flow_id: str) -> List[FlowCheckpoint]:
        """Get all checkpoints for a flow"""
        return self.checkpoints.get(flow_id, [])

    async def _cleanup_old_checkpoints(self, flow_id: str):
        """Clean up old checkpoints to maintain storage limits"""
        if flow_id not in self.checkpoints:
            return

        checkpoints = self.checkpoints[flow_id]

        if len(checkpoints) > self.max_checkpoints_per_flow:
            # Sort by creation time and keep only recent ones
            sorted_checkpoints = sorted(
                checkpoints, key=lambda cp: cp.created_at, reverse=True
            )

            self.checkpoints[flow_id] = sorted_checkpoints[
                : self.max_checkpoints_per_flow
            ]

            removed = len(checkpoints) - self.max_checkpoints_per_flow
            logger.info(f"Cleaned up {removed} old checkpoints for flow {flow_id}")

    def should_checkpoint(self, phase: str) -> bool:
        """Determine if a checkpoint should be created for this phase"""
        return phase in self.checkpoint_phases

    async def create_phase_checkpoint(
        self, flow_id: str, phase: str, state: Any, phase_result: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a checkpoint specifically for phase completion

        Args:
            flow_id: The flow ID
            phase: Phase that was completed
            state: Current flow state
            phase_result: Result from the phase execution

        Returns:
            checkpoint_id or None
        """
        if not self.should_checkpoint(phase):
            return None

        metadata = {
            "phase_result": phase_result,
            "phase_completed": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return await self.create_checkpoint(
            flow_id=flow_id, phase=phase, state=state, metadata=metadata
        )


# Global instance
checkpoint_manager = CheckpointManager()
