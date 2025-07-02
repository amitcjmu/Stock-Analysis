"""
PostgreSQL-based state persistence for CrewAI flows.
Replaces the dual SQLite/PostgreSQL system with a single source of truth.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, func
from sqlalchemy.exc import SQLAlchemyError
import json
import uuid
import logging

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal

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
    Single source of truth for CrewAI flow state.
    Features:
    - Atomic state updates
    - Optimistic locking
    - State recovery
    - Audit trail
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.client_account_id = context.client_account_id
        self.engagement_id = context.engagement_id
        self.user_id = context.user_id
    
    async def save_state(
        self, 
        flow_id: str, 
        state: Dict[str, Any],
        phase: str,
        version: Optional[int] = None
    ) -> None:
        """
        Save flow state with optimistic locking.
        Raises ConcurrentModificationError if version mismatch.
        """
        try:
            # Ensure JSON serialization safety
            state_data = self._ensure_json_serializable(state)
            
            # Get existing record for version check
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id == self.client_account_id
                )
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing and version is not None:
                # Check for concurrent modification
                current_version = existing.state_version or 0
                if current_version != version:
                    raise ConcurrentModificationError(
                        f"State version mismatch. Expected {version}, got {current_version}"
                    )
            
            # Calculate new version
            new_version = (existing.state_version + 1) if existing else 1
            
            if existing:
                # Update existing record
                update_stmt = update(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.id == existing.id
                ).values(
                    flow_state_data=state_data,
                    current_phase=phase,
                    state_version=new_version,
                    updated_at=datetime.utcnow()
                )
                await self.db.execute(update_stmt)
            else:
                # Create new record
                new_record = CrewAIFlowStateExtensions(
                    flow_id=flow_id,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    user_id=self.user_id,
                    flow_state_data=state_data,
                    current_phase=phase,
                    state_version=new_version,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(new_record)
            
            await self.db.commit()
            logger.info(f"✅ State saved for flow {flow_id}, version {new_version}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"❌ Failed to save state for flow {flow_id}: {e}")
            raise
    
    async def load_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Load the latest state for a flow"""
        try:
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id == self.client_account_id
                )
            ).order_by(CrewAIFlowStateExtensions.state_version.desc())
            
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if record:
                logger.info(f"✅ State loaded for flow {flow_id}, version {record.state_version}")
                return record.flow_state_data
            else:
                logger.warning(f"⚠️ No state found for flow {flow_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to load state for flow {flow_id}: {e}")
            return None
    
    async def create_checkpoint(self, flow_id: str, phase: str) -> str:
        """Create a recoverable checkpoint"""
        try:
            checkpoint_id = str(uuid.uuid4())
            
            # Get current state
            current_state = await self.load_state(flow_id)
            if not current_state:
                raise StateRecoveryError(f"No current state found for flow {flow_id}")
            
            # Create checkpoint record
            checkpoint_data = {
                'checkpoint_id': checkpoint_id,
                'flow_id': flow_id,
                'phase': phase,
                'state_snapshot': current_state,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Store in flow_persistence_data as checkpoints array
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id == self.client_account_id
                )
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()
            
            if record:
                persistence_data = record.flow_persistence_data or {}
                checkpoints = persistence_data.get('checkpoints', [])
                checkpoints.append(checkpoint_data)
                
                # Keep only last 10 checkpoints
                if len(checkpoints) > 10:
                    checkpoints = checkpoints[-10:]
                
                persistence_data['checkpoints'] = checkpoints
                
                update_stmt = update(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.id == record.id
                ).values(
                    flow_persistence_data=persistence_data,
                    updated_at=datetime.utcnow()
                )
                await self.db.execute(update_stmt)
                await self.db.commit()
                
                logger.info(f"✅ Checkpoint created for flow {flow_id}: {checkpoint_id}")
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
                checkpoints = persistence_data.get('checkpoints', [])
                
                for checkpoint in checkpoints:
                    if checkpoint.get('checkpoint_id') == checkpoint_id:
                        logger.info(f"✅ Checkpoint found for recovery: {checkpoint_id}")
                        return checkpoint.get('state_snapshot', {})
            
            raise StateRecoveryError(f"Checkpoint not found: {checkpoint_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to recover from checkpoint {checkpoint_id}: {e}")
            raise StateRecoveryError(f"Checkpoint recovery failed: {e}")
    
    async def get_flow_versions(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get version history for a flow"""
        try:
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id == self.client_account_id
                )
            ).order_by(CrewAIFlowStateExtensions.state_version.desc())
            
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            
            versions = []
            for record in records:
                versions.append({
                    'version': record.state_version,
                    'phase': record.current_phase,
                    'created_at': record.created_at.isoformat(),
                    'updated_at': record.updated_at.isoformat()
                })
            
            return versions
            
        except Exception as e:
            logger.error(f"❌ Failed to get versions for flow {flow_id}: {e}")
            return []
    
    async def cleanup_old_versions(self, flow_id: str, keep_versions: int = 5) -> int:
        """Clean up old versions, keeping only the most recent ones"""
        try:
            # Get all versions for the flow
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id == self.client_account_id
                )
            ).order_by(CrewAIFlowStateExtensions.state_version.desc())
            
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
            logger.info(f"✅ Cleaned up {deleted_count} old versions for flow {flow_id}")
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
            elif hasattr(obj, 'model_dump'):
                return convert_obj(obj.model_dump())
            elif hasattr(obj, '__dict__'):
                return convert_obj(obj.__dict__)
            else:
                try:
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    return str(obj)
        
        return convert_obj(data)


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