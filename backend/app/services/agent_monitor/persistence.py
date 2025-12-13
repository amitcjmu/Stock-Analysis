"""
Database persistence for Agent Monitoring Service.
Handles async database writes, queue management, and data persistence.
"""

import asyncio
import logging
import threading
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
from app.models.agent_task_history import AgentTaskHistory
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class PersistenceMixin:
    """Mixin for database persistence operations."""

    def _start_db_writer(self):
        """Start background thread for database writes."""
        if not self._db_write_active:
            self._db_write_active = True
            self._db_write_thread = threading.Thread(
                target=self._db_writer_loop, daemon=True
            )
            self._db_write_thread.start()
            logger.info("Database writer thread started")

    def _stop_db_writer(self):
        """Stop the database writer thread."""
        if not self._db_write_active:
            return

        logger.info("Stopping database writer thread...")
        self._db_write_active = False
        if self._db_write_thread:
            # The thread will do a final flush in its loop's finally block
            # Give it enough time to complete the final write
            self._db_write_thread.join(timeout=10)
            if self._db_write_thread.is_alive():
                logger.warning("Database writer thread did not stop in time.")

        self._db_write_thread = None
        logger.info("Database writer thread stopped")

    def _db_writer_loop(self):
        """Background loop for processing database writes with dedicated event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._db_writer_async_loop())
        finally:
            logger.info("Flushing remaining DB queue before stopping writer loop...")
            try:
                loop.run_until_complete(self._flush_db_queue())
            except Exception as e:
                logger.error(f"Error flushing DB queue during shutdown: {e}")
            loop.close()

    async def _db_writer_async_loop(self):
        """The async part of the writer loop, runs within the dedicated event loop."""
        while self._db_write_active:
            try:
                await asyncio.sleep(2)
                await self._flush_db_queue()
            except Exception as e:
                logger.error(f"Error in database writer async loop: {e}")

    async def _flush_db_queue(self):
        """Flush all pending database writes asynchronously."""
        items_to_write: List[Tuple[str, Dict[str, Any]]] = []

        with self._lock:
            if self._db_write_queue:
                items_to_write = self._db_write_queue[:]
                self._db_write_queue.clear()

        if not items_to_write:
            return

        # Process items in batch using AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                for operation, data in items_to_write:
                    try:
                        if operation == "create_task":
                            await self._persist_task_start(db, data)
                        elif operation == "update_task":
                            await self._persist_task_update(db, data)
                        elif operation == "complete_task":
                            await self._persist_task_completion(db, data)
                        elif operation == "discover_pattern":
                            await self._persist_pattern_discovery(db, data)
                    except Exception as e:
                        logger.error(f"Error persisting {operation}: {e}")

                await db.commit()
            except Exception as e:
                logger.error(f"Error in database flush: {e}")
                await db.rollback()

    def _queue_db_write(self, operation: str, data: Dict[str, Any]):
        """Queue a database write operation."""
        with self._lock:
            self._db_write_queue.append((operation, data))

    async def _persist_task_start(self, db: AsyncSession, data: Dict[str, Any]):
        """Persist task start to database.

        Bug #1168 Defense-in-Depth: Validates flow_id against crewai_flow_state_extensions.
        ROOT CAUSE FIX: recommendation_executor.py now correctly uses master_flow.flow_id.
        This validation is a SAFETY NET to prevent FK violations if a developer accidentally
        passes a child flow ID instead of master flow ID in the future.

        Per Qodo Bot review: Instead of setting to None, we resolve child flow ID to master
        flow ID by checking child flow tables (Discovery only - Assessment and Collection flows removed).
        """
        flow_id = data.get("flow_id")
        master_flow_id = flow_id  # Start with provided ID, may be resolved

        # Bug #1168 Fix: Validate flow_id exists in master flow table
        if flow_id:
            try:
                from uuid import UUID as PyUUID

                flow_uuid = (
                    PyUUID(str(flow_id)) if isinstance(flow_id, str) else flow_id
                )
                stmt = select(CrewAIFlowStateExtensions.flow_id).where(
                    CrewAIFlowStateExtensions.flow_id == flow_uuid
                )
                result = await db.execute(stmt)
                exists = result.scalar_one_or_none()

                if not exists:
                    # Per Qodo Bot: Resolve child flow ID to master flow ID
                    logger.warning(
                        f"Bug #1168: flow_id {flow_id} not found in master table. "
                        f"Attempting to resolve from child flow tables..."
                    )
                    master_flow_id = await self._resolve_to_master_flow_id(
                        db, flow_uuid
                    )
                    if master_flow_id:
                        logger.info(
                            f"Bug #1168: Resolved child flow {flow_id} to master flow {master_flow_id}"
                        )
                    else:
                        logger.warning(
                            f"Bug #1168: Could not resolve flow_id {flow_id}. Setting to None."
                        )
            except Exception as e:
                logger.warning(
                    f"Bug #1168: Error validating flow_id {flow_id}: {e}. Setting to None."
                )
                master_flow_id = None

        task_history = AgentTaskHistory(
            flow_id=master_flow_id,  # Use resolved master flow ID
            agent_name=data["agent_name"],
            agent_type=data.get("agent_type", "individual"),
            task_id=data["task_id"],
            task_name=data.get("task_name", data["task_id"]),
            task_description=data.get("description"),
            started_at=data["started_at"],
            status=data["status"],
            client_account_id=data.get("client_account_id"),
            engagement_id=data.get("engagement_id"),
        )
        db.add(task_history)

    async def _resolve_to_master_flow_id(
        self, db: AsyncSession, child_flow_uuid: Any
    ) -> Optional[Any]:
        """Resolve a child flow ID to its master flow ID.

        Per Qodo Bot review: Instead of nullifying, attempt to resolve child→master.
        Checks Discovery flow table (Assessment and Collection flows removed).

        Args:
            db: Database session
            child_flow_uuid: UUID of the child flow

        Returns:
            The master_flow_id if found, None otherwise
        """
        # Check DiscoveryFlow (only remaining child flow type)
        stmt = select(DiscoveryFlow.master_flow_id).where(
            DiscoveryFlow.id == child_flow_uuid
        )
        result = await db.execute(stmt)
        master_id = result.scalar_one_or_none()
        if master_id:
            return master_id

        return None

    async def _persist_task_update(self, db: AsyncSession, data: Dict[str, Any]):
        """Update task in database."""
        stmt = select(AgentTaskHistory).where(
            AgentTaskHistory.task_id == data["task_id"],
            AgentTaskHistory.agent_name == data.get("agent_name", ""),
        )
        result = await db.execute(stmt)
        task_history = result.scalar_one_or_none()

        if task_history:
            task_history.status = data["status"]
            if data.get("error_message"):
                task_history.error_message = data["error_message"]
            if data.get("result_preview"):
                task_history.result_preview = data["result_preview"]
            if data.get("llm_calls_count"):
                task_history.llm_calls_count = data["llm_calls_count"]
            if data.get("thinking_phases_count"):
                task_history.thinking_phases_count = data["thinking_phases_count"]
            if data.get("token_usage"):
                task_history.token_usage = data["token_usage"]
            if data.get("confidence_score"):
                task_history.confidence_score = Decimal(str(data["confidence_score"]))

    async def _persist_task_completion(self, db: AsyncSession, data: Dict[str, Any]):
        """Persist task completion to database."""
        stmt = select(AgentTaskHistory).where(
            AgentTaskHistory.task_id == data["task_id"],
            AgentTaskHistory.agent_name == data.get("agent_name", ""),
        )
        result = await db.execute(stmt)
        task_history = result.scalar_one_or_none()

        if task_history:
            task_history.completed_at = data["completed_at"]
            task_history.status = data["status"]
            task_history.success = data.get("success", data["status"] == "completed")
            task_history.duration_seconds = Decimal(str(data.get("duration", 0)))

            if data.get("result_preview"):
                task_history.result_preview = data["result_preview"]
            if data.get("error_message"):
                task_history.error_message = data["error_message"]
            if data.get("llm_calls_count"):
                task_history.llm_calls_count = data["llm_calls_count"]
            if data.get("thinking_phases_count"):
                task_history.thinking_phases_count = data["thinking_phases_count"]
            if data.get("token_usage"):
                task_history.token_usage = data["token_usage"]
            if data.get("memory_usage_mb"):
                task_history.memory_usage_mb = Decimal(str(data["memory_usage_mb"]))

    async def _persist_pattern_discovery(self, db: AsyncSession, data: Dict[str, Any]):
        """Persist discovered pattern to database."""
        # Check if pattern already exists
        stmt = select(AgentDiscoveredPatterns).where(
            AgentDiscoveredPatterns.pattern_id == data["pattern_id"],
            AgentDiscoveredPatterns.client_account_id == data.get("client_account_id"),
            AgentDiscoveredPatterns.engagement_id == data.get("engagement_id"),
        )
        result = await db.execute(stmt)
        existing_pattern = result.scalar_one_or_none()

        if existing_pattern:
            # Update existing pattern
            existing_pattern.evidence_count += 1
            existing_pattern.confidence_score = Decimal(
                str(data.get("confidence_score", 0.5))
            )
            existing_pattern.last_used_at = datetime.utcnow()
            if data.get("evidence_data"):
                existing_pattern.add_evidence(data["evidence_data"])
        else:
            # Create new pattern
            pattern = AgentDiscoveredPatterns(
                pattern_id=data["pattern_id"],
                pattern_type=data.get("pattern_type", "general"),
                pattern_name=data.get("pattern_name", data["pattern_id"]),
                pattern_description=data.get("pattern_description"),
                discovered_by_agent=data["agent_name"],
                task_id=data.get("task_id"),
                confidence_score=Decimal(str(data.get("confidence_score", 0.5))),
                pattern_data=data.get("pattern_data", {}),
                execution_context=data.get("execution_context", {}),
                client_account_id=data.get("client_account_id"),
                engagement_id=data.get("engagement_id"),
            )
            db.add(pattern)

    def start_task_with_context(
        self,
        task_id: str,
        agent_name: str,
        description: str,
        flow_id: Optional[str] = None,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        agent_type: str = "individual",
    ):
        """Start task with full context for database persistence."""
        task_exec = self.start_task(task_id, agent_name, description)

        # Queue database write
        self._queue_db_write(
            "create_task",
            {
                "task_id": task_id,
                "agent_name": agent_name,
                "agent_type": agent_type,
                "task_name": task_id,
                "description": description,
                "started_at": task_exec.start_time,
                "status": task_exec.status.value,
                "flow_id": flow_id,
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )

        return task_exec

    def complete_task_with_metrics(
        self,
        task_id: str,
        result: Optional[str] = None,
        confidence_score: Optional[float] = None,
        token_usage: Optional[Dict[str, int]] = None,
        memory_usage_mb: Optional[float] = None,
    ):
        """Complete task with additional metrics for database."""
        task = None
        with self._lock:
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]

        if not task:
            return

        # Complete the task
        self.complete_task(task_id, result)

        # Queue database write with metrics
        self._queue_db_write(
            "complete_task",
            {
                "task_id": task_id,
                "agent_name": task.agent_name,
                "completed_at": task.end_time,
                "status": "completed",
                "success": True,
                "duration": task.duration,
                "result_preview": result[:200] if result else None,
                "llm_calls_count": len(task.llm_calls),
                "thinking_phases_count": len(task.thinking_phases),
                "token_usage": token_usage,
                "confidence_score": confidence_score,
                "memory_usage_mb": memory_usage_mb,
            },
        )

    def discover_pattern(
        self,
        agent_name: str,
        pattern_id: str,
        pattern_data: Dict[str, Any],
        task_id: Optional[str] = None,
        confidence_score: float = 0.5,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Record a pattern discovered by an agent."""
        self._queue_db_write(
            "discover_pattern",
            {
                "pattern_id": pattern_id,
                "pattern_type": pattern_data.get("type", "general"),
                "pattern_name": pattern_data.get("name", pattern_id),
                "pattern_description": pattern_data.get("description"),
                "agent_name": agent_name,
                "task_id": task_id,
                "confidence_score": confidence_score,
                "pattern_data": pattern_data,
                "execution_context": pattern_data.get("context", {}),
                "evidence_data": pattern_data.get("evidence"),
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )
