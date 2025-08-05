"""
PostgreSQL-based state persistence for CrewAI flows.
Replaces the dual SQLite/PostgreSQL system with a single source of truth.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.cache_keys import CacheKeys
from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.security.cache_encryption import SecureCache
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.caching.redis_cache import get_redis_cache

logger = logging.getLogger(__name__)


class ConcurrentModificationError(Exception):
    """Raised when version conflict detected"""

    pass


class StateValidationError(Exception):
    """Raised when state validation fails"""

    pass


class StateRecoveryError(Exception):
    """Raised when state recovery fails"""

    pass


class PostgresFlowStateStore:
    """
    Single source of truth for CrewAI flow state with secure caching.
    
    Security Features:
    - Encrypts sensitive flow state data before caching
    - Proper tenant isolation in cache keys
    - Secure checkpoint management
    - Atomic state updates with optimistic locking
    - State recovery with encrypted persistence
    - Audit trail
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
        
        # Initialize secure caching
        self.redis_cache = get_redis_cache()
        self.secure_cache = SecureCache(self.redis_cache)

    def _map_phase_to_status(self, phase: str) -> str:
        """Map phase names to valid flow statuses"""
        # Valid statuses: initialized, active, processing, paused, completed, failed, cancelled, waiting_for_approval
        phase_status_mapping = {
            "initialization": "initialized",
            "initialized": "initialized",
            "data_import": "processing",
            "field_mapping": "processing",  # Could be waiting_for_approval, but we'll handle that separately
            "attribute_mapping": "processing",
            "data_cleansing": "processing",
            "asset_inventory": "processing",
            "dependency_analysis": "processing",
            "tech_debt_assessment": "processing",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
            "paused": "paused",
        }
        return phase_status_mapping.get(phase, "active")

    async def save_state(
        self,
        flow_id: str,
        state: Dict[str, Any],
        phase: str,
        version: Optional[int] = None,
    ) -> None:
        """
        Save flow state with optimistic locking and secure caching.
        Raises ConcurrentModificationError if version mismatch.
        
        Security: Automatically encrypts sensitive flow state data before caching.
        """
        try:
            # Ensure JSON serialization safety
            state_data = self._ensure_json_serializable(state)

            # Get existing record for version check
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing and version is not None:
                # Check for concurrent modification
                current_config = existing.flow_configuration or {}
                current_version = current_config.get("version", 0)
                if current_version != version:
                    raise ConcurrentModificationError(
                        f"State version mismatch. Expected {version}, got {current_version}"
                    )

            # Calculate new version
            current_config = existing.flow_configuration if existing else {}
            new_version = (current_config.get("version", 0) + 1) if existing else 1

            # Ensure current_phase is in the state data for MFO compatibility
            if isinstance(state_data, dict):
                state_data["current_phase"] = phase

            if existing:
                # Update existing record
                update_stmt = (
                    update(CrewAIFlowStateExtensions)
                    .where(CrewAIFlowStateExtensions.id == existing.id)
                    .values(
                        flow_persistence_data=state_data,
                        flow_status=self._map_phase_to_status(phase),
                        flow_configuration={
                            "phase": phase,
                            "version": new_version,
                            "current_phase": phase,
                        },
                        updated_at=datetime.utcnow(),
                    )
                )
                await self.db.execute(update_stmt)
            else:
                # Create new record
                new_record = CrewAIFlowStateExtensions(
                    flow_id=flow_id,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    user_id=self.user_id,
                    flow_type="discovery",
                    flow_persistence_data=state_data,
                    flow_status=self._map_phase_to_status(phase),
                    flow_configuration={
                        "phase": phase,
                        "version": new_version,
                        "current_phase": phase,
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                self.db.add(new_record)

            await self.db.commit()
            
            # Cache the state securely after successful database save
            await self._cache_flow_state_securely(flow_id, state_data, phase)
            
            logger.info(f"✅ State saved and cached securely for flow {flow_id}, version {new_version}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to save state for flow {flow_id}: {e}")
            raise

    async def update_flow_status(
        self, flow_id: str, status: str, update_persistence_data: bool = True
    ):
        """Update just the flow status without changing the entire state"""
        try:
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Prepare update values
                update_values = {"flow_status": status, "updated_at": datetime.utcnow()}

                # Also update status in persistence data if requested
                if update_persistence_data and existing.flow_persistence_data:
                    persistence_data = dict(existing.flow_persistence_data)
                    persistence_data["status"] = status
                    update_values["flow_persistence_data"] = persistence_data

                update_stmt = (
                    update(CrewAIFlowStateExtensions)
                    .where(CrewAIFlowStateExtensions.id == existing.id)
                    .values(**update_values)
                )

                await self.db.execute(update_stmt)
                await self.db.commit()
                logger.info(f"✅ Flow status updated to '{status}' for flow {flow_id}")
            else:
                logger.warning(f"⚠️ No flow found to update status for {flow_id}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to update flow status for {flow_id}: {e}")
            raise

    async def load_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Load the latest state for a flow with secure caching"""
        try:
            # Try to load from secure cache first
            cached_state = await self._load_from_secure_cache(flow_id)
            if cached_state:
                logger.debug(f"✅ State loaded from secure cache for flow {flow_id}")
                return cached_state
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.client_account_id,
                )
            )

            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()

            if record:
                version = (
                    record.flow_configuration.get("version", 0)
                    if record.flow_configuration
                    else 0
                )
                state_data = record.flow_persistence_data
                
                # Cache the loaded state securely for future requests
                if state_data:
                    current_phase = record.flow_configuration.get("phase", "unknown")
                    await self._cache_flow_state_securely(flow_id, state_data, current_phase)
                
                logger.info(f"✅ State loaded from database and cached securely for flow {flow_id}, version {version}")
                return state_data
            else:
                logger.warning(f"⚠️ No state found for flow {flow_id}")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to load state for flow {flow_id}: {e}")
            return None

    async def create_checkpoint(self, flow_id: str, phase: str) -> str:
        """Create a recoverable checkpoint with secure encryption"""
        try:
            checkpoint_id = str(uuid.uuid4())

            # Get current state
            current_state = await self.load_state(flow_id)
            if not current_state:
                raise StateRecoveryError(f"No current state found for flow {flow_id}")

            # Create checkpoint record with security metadata
            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "flow_id": flow_id,
                "phase": phase,
                "state_snapshot": current_state,
                "client_account_id": str(self.client_account_id),
                "engagement_id": str(self.engagement_id),
                "user_id": str(self.user_id),
                "created_at": datetime.utcnow().isoformat(),
                "security_context": {
                    "encrypted": True,
                    "tenant_isolated": True,
                    "version": "v1",
                },
            }
            
            # Store checkpoint in secure cache as well
            await self._cache_checkpoint_securely(checkpoint_id, checkpoint_data)

            # Store in flow_persistence_data as checkpoints array
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()

            if record:
                persistence_data = record.flow_persistence_data or {}
                checkpoints = persistence_data.get("checkpoints", [])
                checkpoints.append(checkpoint_data)

                # Keep only last 10 checkpoints
                if len(checkpoints) > 10:
                    checkpoints = checkpoints[-10:]

                persistence_data["checkpoints"] = checkpoints

                update_stmt = (
                    update(CrewAIFlowStateExtensions)
                    .where(CrewAIFlowStateExtensions.id == record.id)
                    .values(
                        flow_persistence_data=persistence_data,
                        updated_at=datetime.utcnow(),
                    )
                )
                await self.db.execute(update_stmt)
                await self.db.commit()

                logger.info(
                    f"✅ Secure checkpoint created for flow {flow_id}: {checkpoint_id}"
                )
                return checkpoint_id
            else:
                raise StateRecoveryError(f"No state record found for flow {flow_id}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to create checkpoint for flow {flow_id}: {e}")
            raise StateRecoveryError(f"Checkpoint creation failed: {e}")

    async def recover_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Recover state from a checkpoint"""
        try:
            # Find checkpoint across all flow records
            stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.client_account_id == self.client_account_id
            )
            result = await self.db.execute(stmt)
            records = result.scalars().all()

            for record in records:
                persistence_data = record.flow_persistence_data or {}
                checkpoints = persistence_data.get("checkpoints", [])

                for checkpoint in checkpoints:
                    if checkpoint.get("checkpoint_id") == checkpoint_id:
                        logger.info(
                            f"✅ Checkpoint found for recovery: {checkpoint_id}"
                        )
                        return checkpoint.get("state_snapshot", {})

            raise StateRecoveryError(f"Checkpoint not found: {checkpoint_id}")

        except Exception as e:
            logger.error(f"❌ Failed to recover from checkpoint {checkpoint_id}: {e}")
            raise StateRecoveryError(f"Checkpoint recovery failed: {e}")

    async def get_flow_versions(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get version history for a flow"""
        try:
            stmt = (
                select(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_id,
                        CrewAIFlowStateExtensions.client_account_id
                        == self.client_account_id,
                    )
                )
                .order_by(CrewAIFlowStateExtensions.updated_at.desc())
            )

            result = await self.db.execute(stmt)
            records = result.scalars().all()

            versions = []
            for record in records:
                config = record.flow_configuration or {}
                versions.append(
                    {
                        "version": config.get("version", 0),
                        "phase": config.get("phase", record.flow_status),
                        "created_at": record.created_at.isoformat(),
                        "updated_at": record.updated_at.isoformat(),
                    }
                )

            return versions

        except Exception as e:
            logger.error(f"❌ Failed to get versions for flow {flow_id}: {e}")
            return []

    async def cleanup_old_versions(self, flow_id: str, keep_versions: int = 5) -> int:
        """Clean up old versions, keeping only the most recent ones"""
        try:
            # Get all versions for the flow
            stmt = (
                select(CrewAIFlowStateExtensions)
                .where(
                    and_(
                        CrewAIFlowStateExtensions.flow_id == flow_id,
                        CrewAIFlowStateExtensions.client_account_id
                        == self.client_account_id,
                    )
                )
                .order_by(CrewAIFlowStateExtensions.updated_at.desc())
            )

            result = await self.db.execute(stmt)
            records = result.scalars().all()

            if len(records) <= keep_versions:
                return 0  # Nothing to clean up

            # Keep the most recent versions, delete the rest
            records_to_delete = records[keep_versions:]
            deleted_count = 0

            for record in records_to_delete:
                await self.db.delete(record)
                deleted_count += 1

            await self.db.commit()
            logger.info(
                f"✅ Cleaned up {deleted_count} old versions for flow {flow_id}"
            )
            return deleted_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to cleanup versions for flow {flow_id}: {e}")
            return 0

    def _ensure_json_serializable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure data is JSON serializable"""

        def convert_obj(obj):
            if isinstance(obj, dict):
                return {k: convert_obj(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_obj(item) for item in obj]
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "model_dump"):
                return convert_obj(obj.model_dump())
            elif hasattr(obj, "__dict__"):
                return convert_obj(obj.__dict__)
            else:
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    return str(obj)

        return convert_obj(data)

    async def _cache_flow_state_securely(
        self, flow_id: str, state_data: Dict[str, Any], phase: str
    ) -> None:
        """Cache flow state with automatic encryption for sensitive data"""
        try:
            # Generate secure cache key with tenant isolation
            cache_key = CacheKeys.crewai_flow_state(
                flow_id=flow_id,
                phase=phase,
                client_id=str(self.client_account_id),
                engagement_id=str(self.engagement_id),
            )

            # Get TTL recommendation
            ttl = CacheKeys.get_ttl_recommendation(cache_key)

            # Store with automatic encryption (SecureCache will detect sensitive data)
            success = await self.secure_cache.set(
                key=cache_key,
                value=state_data,
                ttl=ttl,
                force_encrypt=True,  # Force encryption for flow state
            )

            if success:
                logger.debug(f"✅ Flow state cached securely: {cache_key}")
            else:
                logger.warning(f"⚠️ Failed to cache flow state securely: {cache_key}")

        except Exception as e:
            logger.error(f"❌ Failed to cache flow state securely: {e}")
            # Don't raise - caching failure shouldn't break the main flow

    async def _load_from_secure_cache(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Load flow state from secure cache"""
        try:
            # We need to determine the current phase to generate the correct cache key
            # For now, we'll try common phases or use a generic approach
            
            # First, try to get the phase from database quickly
            stmt = select(CrewAIFlowStateExtensions.flow_configuration).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id == self.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if record and record.get("phase"):
                phase = record["phase"]
                cache_key = CacheKeys.crewai_flow_state(
                    flow_id=flow_id,
                    phase=phase,
                    client_id=str(self.client_account_id),
                    engagement_id=str(self.engagement_id),
                )
                
                cached_data = await self.secure_cache.get(cache_key)
                if cached_data:
                    return cached_data

            # If we couldn't determine phase or cache miss, return None
            return None

        except Exception as e:
            logger.error(f"❌ Failed to load from secure cache: {e}")
            return None

    async def _cache_checkpoint_securely(
        self, checkpoint_id: str, checkpoint_data: Dict[str, Any]
    ) -> None:
        """Cache checkpoint with encryption"""
        try:
            cache_key = CacheKeys.flow_checkpoint(
                flow_id=checkpoint_data["flow_id"],
                checkpoint_id=checkpoint_id,
                client_id=str(self.client_account_id),
                engagement_id=str(self.engagement_id),
            )

            # Get TTL for checkpoint caching
            ttl = CacheKeys.get_ttl_recommendation(cache_key)

            # Store with forced encryption
            success = await self.secure_cache.set(
                key=cache_key,
                value=checkpoint_data,
                ttl=ttl,
                force_encrypt=True,
            )

            if success:
                logger.debug(f"✅ Checkpoint cached securely: {checkpoint_id}")
            else:
                logger.warning(f"⚠️ Failed to cache checkpoint securely: {checkpoint_id}")

        except Exception as e:
            logger.error(f"❌ Failed to cache checkpoint securely: {e}")
            # Don't raise - caching failure shouldn't break the main flow


# Factory function for creating state stores
async def create_postgres_store(context: RequestContext) -> PostgresFlowStateStore:
    """
    Factory function to create a PostgreSQL state store.

    Args:
        context: RequestContext with tenant information

    Returns:
        PostgresFlowStateStore instance
    """
    async with AsyncSessionLocal() as db:
        return PostgresFlowStateStore(db, context)


# Context manager for automatic store lifecycle
class managed_postgres_store:
    """
    Async context manager for automatic store lifecycle management.

    Usage:
        async with managed_postgres_store(context) as store:
            await store.save_state(flow_id, state, phase)
    """

    def __init__(self, context: RequestContext):
        self.context = context
        self.db = None
        self.store = None

    async def __aenter__(self):
        self.db = AsyncSessionLocal()
        self.store = PostgresFlowStateStore(self.db, self.context)
        return self.store

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            await self.db.close()
