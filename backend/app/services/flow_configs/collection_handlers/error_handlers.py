"""
Collection Error and Recovery Handlers
ADCS: Error handling, rollback, and checkpoint handlers for collection flows

Provides handler functions for error handling, rollback operations, and checkpoint management.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    CollectionHandlerBase,
    clear_collected_data,
    clear_gaps,
    clear_questionnaire_responses,
)

logger = logging.getLogger(__name__)


class ErrorHandlers(CollectionHandlerBase):
    """Handlers for error handling and recovery operations"""

    async def collection_error_handler(
        self,
        db: AsyncSession,
        flow_id: str,
        error: Exception,
        error_context: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle errors in Collection flow"""
        try:
            logger.error(f"❌ Collection flow error for {flow_id}: {error}")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                logger.warning(f"Collection flow for master {flow_id} not found")
                return {"success": False, "error": "Collection flow not found"}

            # Update collection flow with error
            update_query = """
                UPDATE collection_flows
                SET status = :status,
                    error_message = :error_message,
                    error_details = :error_details::jsonb,
                    updated_at = :updated_at
                WHERE master_flow_id = :master_flow_id
            """

            await db.execute(
                update_query,
                {
                    "status": "failed",
                    "error_message": str(error),
                    "error_details": {
                        "error_type": type(error).__name__,
                        "error_context": error_context,
                        "failed_at": datetime.utcnow().isoformat(),
                        "phase": error_context.get("phase", "unknown"),
                        "operation": error_context.get("operation", "unknown"),
                    },
                    "updated_at": datetime.utcnow(),
                    "master_flow_id": flow_id,
                },
            )

            await db.commit()

            # Determine if error is recoverable
            recoverable_errors = ["ConnectionError", "TimeoutError", "RateLimitError"]
            is_recoverable = type(error).__name__ in recoverable_errors

            return {
                "success": True,
                "error_handled": True,
                "is_recoverable": is_recoverable,
                "recovery_strategy": (
                    "retry" if is_recoverable else "manual_intervention"
                ),
                "message": f"Error logged: {str(error)}",
            }

        except Exception as e:
            logger.error(f"❌ Error handler failed: {e}")
            return {"success": False, "error": f"Error handler failed: {str(e)}"}

    async def collection_rollback_handler(
        self,
        db: AsyncSession,
        flow_id: str,
        rollback_to_phase: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle rollback for Collection flow"""
        try:
            logger.info(
                f"⏪ Rolling back Collection flow {flow_id} to phase {rollback_to_phase}"
            )

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Define rollback actions by phase
            rollback_actions = {
                "platform_detection": ["clear_all_collected_data", "reset_adapters"],
                "automated_collection": ["clear_collected_data", "retain_platforms"],
                "gap_analysis": ["clear_gaps", "retain_collected_data"],
                "manual_collection": ["clear_responses", "retain_gaps"],
                "synthesis": ["clear_synthesis", "retain_all_raw_data"],
            }

            actions = rollback_actions.get(rollback_to_phase, [])

            # Execute rollback actions
            for action in actions:
                if action == "clear_all_collected_data":
                    await clear_collected_data(db, collection_flow["id"])
                elif action == "clear_collected_data":
                    await clear_collected_data(
                        db, collection_flow["id"], preserve_platforms=True
                    )
                elif action == "clear_gaps":
                    await clear_gaps(db, collection_flow["id"])
                elif action == "clear_responses":
                    await clear_questionnaire_responses(db, collection_flow["id"])

            # Update collection flow state
            update_query = """
                UPDATE collection_flows
                SET current_phase = :current_phase,
                    status = :status,
                    phase_state = phase_state || :rollback_info::jsonb,
                    updated_at = :updated_at
                WHERE master_flow_id = :master_flow_id
            """

            await db.execute(
                update_query,
                {
                    "current_phase": rollback_to_phase,
                    "status": "rolled_back",
                    "rollback_info": {
                        "rollback_at": datetime.utcnow().isoformat(),
                        "rollback_from": collection_flow.get("current_phase"),
                        "rollback_to": rollback_to_phase,
                        "actions_taken": actions,
                    },
                    "updated_at": datetime.utcnow(),
                    "master_flow_id": flow_id,
                },
            )

            await db.commit()

            return {
                "success": True,
                "rolled_back_to": rollback_to_phase,
                "actions_taken": actions,
                "message": f"Successfully rolled back to {rollback_to_phase}",
            }

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def collection_checkpoint_handler(
        self,
        db: AsyncSession,
        flow_id: str,
        checkpoint_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create checkpoint for Collection flow"""
        try:
            logger.info(f"💾 Creating checkpoint for Collection flow {flow_id}")

            # Get collection flow
            collection_flow = await self._get_collection_flow_by_master_id(db, flow_id)
            if not collection_flow:
                raise ValueError(f"Collection flow for master {flow_id} not found")

            # Update phase state with checkpoint
            update_query = """
                UPDATE collection_flows
                SET phase_state = phase_state || :checkpoint::jsonb,
                    updated_at = :updated_at
                WHERE master_flow_id = :master_flow_id
            """

            checkpoint_info = {
                "checkpoints": {
                    checkpoint_data.get("phase", "unknown"): {
                        "created_at": datetime.utcnow().isoformat(),
                        "data": checkpoint_data,
                        "phase_progress": checkpoint_data.get("progress", 0),
                        "can_resume": True,
                    }
                }
            }

            await db.execute(
                update_query,
                {
                    "checkpoint": checkpoint_info,
                    "updated_at": datetime.utcnow(),
                    "master_flow_id": flow_id,
                },
            )

            await db.commit()

            return {
                "success": True,
                "checkpoint_created": True,
                "phase": checkpoint_data.get("phase"),
                "message": "Checkpoint created successfully",
            }

        except Exception as e:
            logger.error(f"❌ Checkpoint creation failed: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}


# Create singleton instance for backward compatibility
error_handlers = ErrorHandlers()


# Export functions for backward compatibility
async def collection_error_handler(*args, **kwargs):
    return await error_handlers.collection_error_handler(*args, **kwargs)


async def collection_rollback_handler(*args, **kwargs):
    return await error_handlers.collection_rollback_handler(*args, **kwargs)


async def collection_checkpoint_handler(*args, **kwargs):
    return await error_handlers.collection_checkpoint_handler(*args, **kwargs)
