# State Management Implementation Guide

**Last Updated: August 18, 2025**

## Overview

The AI Modernize Migration Platform implements a sophisticated state management system using the **Master-Child Table Pattern** with PostgreSQL as the single source of truth. This guide documents the flow state lifecycle, persistence patterns, transaction handling, and recovery mechanisms.

## Architecture Overview

### Master-Child Table Pattern

The platform uses a two-table architecture for managing flow state:

1. **Master Table**: `crewai_flow_state_extensions` - Central source of truth for all flows
2. **Child Tables**: Domain-specific tables (e.g., `discovery_flows`, `assessment_flows`)

This pattern provides:
- **Atomic Operations** - Single transaction across related data
- **Audit Trail** - Complete lifecycle tracking in master table
- **Domain Separation** - Specific data models for different flow types
- **Enterprise Resilience** - Graceful handling of state transitions

### State Management Components

```
┌─────────────────────┐
│   FlowStateManager  │ ← Main orchestrator
├─────────────────────┤
│ PostgresFlowStateStore │ ← Persistence layer
├─────────────────────┤
│ SecureCheckpointManager │ ← Checkpoint management
├─────────────────────┤
│ FlowStateRecovery   │ ← Recovery and repair
└─────────────────────┘
```

## Core State Management Patterns

### 1. FlowStateManager - Main Orchestrator

The central component managing all flow state operations:

```python
class FlowStateManager:
    """
    Manages CrewAI flow state with PostgreSQL as single source of truth.
    Provides comprehensive state lifecycle management with recovery capabilities.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()
        self.recovery = FlowStateRecovery(db, context)
        self.secure_checkpoint_manager = SecureCheckpointManager(context)

    async def create_flow_state(
        self, flow_id: str, initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new flow state with comprehensive initialization."""
        try:
            logger.info(f"Creating new flow state: {flow_id}")

            # Create initial state structure
            flow_state = {
                "flow_id": flow_id,
                "client_account_id": str(self.context.client_account_id),
                "engagement_id": str(self.context.engagement_id),
                "user_id": str(self.context.user_id),
                "current_phase": "initialization",
                "status": "running",
                "progress_percentage": 0.0,
                "phase_completion": {
                    "data_import": False,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_creation": False,
                    "asset_inventory": False,
                    "dependency_analysis": False,
                    "tech_debt_analysis": False,
                },
                "crew_status": {},
                "raw_data": initial_data.get("raw_data", []),
                "metadata": initial_data.get("metadata", {}),
                "errors": [],
                "warnings": [],
                "agent_insights": [],
                "user_clarifications": [],
                "workflow_log": [],
                "agent_confidences": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Save to PostgreSQL with initial state
            await self.store.save_state(flow_id, flow_state, "initialization")

            logger.info(f"✅ Flow state created successfully: {flow_id}")
            return flow_state

        except Exception as e:
            logger.error(f"❌ Failed to create flow state {flow_id}: {e}")
            raise
```

### 2. PostgresFlowStateStore - Persistence Layer

Handles all database operations with security and caching:

```python
class PostgresFlowStateStore:
    """
    Single source of truth for CrewAI flow state with secure caching.
    
    Security Features:
    - Encrypts sensitive flow state data before caching
    - Proper tenant isolation in cache keys
    - Atomic state updates with optimistic locking
    - State recovery with encrypted persistence
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
        """
        try:
            # Get current record for version checking
            existing_record = await self._get_flow_record(flow_id)
            
            if existing_record and version is not None:
                if existing_record.version != version:
                    raise ConcurrentModificationError(
                        f"Version mismatch for flow {flow_id}. "
                        f"Expected {version}, found {existing_record.version}"
                    )

            # Map phase to valid status
            status = self._map_phase_to_status(phase)

            if existing_record:
                # Update existing record
                await self._update_existing_record(
                    existing_record, state, phase, status
                )
            else:
                # Create new record
                await self._create_new_record(flow_id, state, phase, status)

            # Update secure cache
            await self._update_cache(flow_id, state, phase)

            logger.info(f"✅ State saved for flow {flow_id}, phase: {phase}")

        except Exception as e:
            logger.error(f"❌ Failed to save state for flow {flow_id}: {e}")
            raise

    async def _update_existing_record(
        self,
        record: CrewAIFlowStateExtensions,
        state: Dict[str, Any],
        phase: str,
        status: str
    ) -> None:
        """Update existing flow record with new state."""
        
        # Update record fields
        record.flow_state = state
        record.current_phase = phase
        record.flow_status = status
        record.version += 1  # Increment version for optimistic locking
        record.updated_at = datetime.utcnow()
        
        # Update progress tracking
        if "progress_percentage" in state:
            record.progress_percentage = state["progress_percentage"]
        
        # Update error tracking
        if "errors" in state and state["errors"]:
            record.last_error = json.dumps(state["errors"][-1])
        
        # Commit changes
        await self.db.commit()
        await self.db.refresh(record)

    async def _create_new_record(
        self,
        flow_id: str,
        state: Dict[str, Any],
        phase: str,
        status: str
    ) -> None:
        """Create new flow state record."""
        
        record = CrewAIFlowStateExtensions(
            flow_id=uuid.UUID(flow_id),
            client_account_id=uuid.UUID(self.client_account_id),
            engagement_id=uuid.UUID(self.engagement_id),
            user_id=self.user_id,
            flow_type=state.get("flow_type", "discovery"),
            flow_name=state.get("flow_name", f"Flow {flow_id[:8]}"),
            flow_state=state,
            current_phase=phase,
            flow_status=status,
            progress_percentage=state.get("progress_percentage", 0.0),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
```

### 3. Repository Pattern Implementation

**Master Flow Repository:**
```python
class CrewAIFlowStateExtensionsRepository(BaseRepo):
    """
    Repository for master CrewAI flow state management.
    Central coordination table for all flow types.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str = None,
        user_id: Optional[str] = None,
    ):
        super().__init__(
            db=db,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=user_id,
        )
        self.queries = MasterFlowQueries(db, self.client_account_id, self.engagement_id)
        self.enrich = MasterFlowEnrichment(
            db, self.client_account_id, self.engagement_id, user_id
        )
        self.commands = MasterFlowCommands(
            db, self.client_account_id, self.engagement_id, user_id
        )

    async def create_master_flow(
        self,
        flow_id: str,
        flow_type: str,
        user_id: str = None,
        flow_name: str = None,
        flow_configuration: Dict[str, Any] = None,
        initial_state: Dict[str, Any] = None,
        auto_commit: bool = True,
    ) -> CrewAIFlowStateExtensions:
        """Create master flow with comprehensive initialization."""
        return await self.commands.create_master_flow(
            flow_id,
            flow_type,
            user_id,
            flow_name,
            flow_configuration,
            initial_state,
            auto_commit,
        )

    async def update_flow_state(
        self,
        flow_id: str,
        state_updates: Dict[str, Any],
        auto_commit: bool = True
    ) -> Optional[CrewAIFlowStateExtensions]:
        """Update flow state with atomic operations."""
        return await self.commands.update_flow_state(
            flow_id, state_updates, auto_commit
        )
```

**Child Flow Repository (Discovery Example):**
```python
class DiscoveryFlowRepository:
    """Repository for discovery-specific flow data."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def create_discovery_flow(
        self,
        flow_id: str,
        master_flow_id: str,
        data_import_id: str,
        flow_name: str
    ) -> DiscoveryFlow:
        """Create discovery flow linked to master flow."""
        
        discovery_flow = DiscoveryFlow(
            flow_id=uuid.UUID(flow_id),
            master_flow_id=uuid.UUID(master_flow_id),
            client_account_id=uuid.UUID(self.context.client_account_id),
            engagement_id=uuid.UUID(self.context.engagement_id),
            user_id=self.context.user_id,
            data_import_id=uuid.UUID(data_import_id),
            flow_name=flow_name,
            current_phase="initialization",
            flow_status="running",
            created_at=datetime.utcnow()
        )
        
        self.db.add(discovery_flow)
        await self.db.commit()
        await self.db.refresh(discovery_flow)
        
        return discovery_flow

    async def get_by_flow_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get discovery flow with tenant filtering."""
        query = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == uuid.UUID(flow_id),
                DiscoveryFlow.client_account_id == uuid.UUID(self.context.client_account_id),
                DiscoveryFlow.engagement_id == uuid.UUID(self.context.engagement_id)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

## Transaction Management

### 1. Atomic Operations

**Cross-Table Transactions:**
```python
class FlowTransactionManager:
    """Manages atomic operations across master and child tables."""

    async def create_flow_atomically(
        self,
        flow_id: str,
        flow_type: str,
        initial_data: Dict[str, Any],
        child_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create flow with atomic master-child relationship."""
        
        async with self.db.begin():
            try:
                # Create master flow record
                master_repo = CrewAIFlowStateExtensionsRepository(
                    self.db, self.context.client_account_id, self.context.engagement_id
                )
                
                master_flow = await master_repo.create_master_flow(
                    flow_id=flow_id,
                    flow_type=flow_type,
                    initial_state=initial_data,
                    auto_commit=False  # Defer commit for atomic operation
                )
                
                # Create child flow record
                if flow_type == "discovery":
                    child_repo = DiscoveryFlowRepository(self.db, self.context)
                    child_flow = await child_repo.create_discovery_flow(
                        flow_id=flow_id,
                        master_flow_id=str(master_flow.flow_id),
                        **child_data
                    )
                
                # Both operations succeed - commit will happen automatically
                logger.info(f"✅ Flow created atomically: {flow_id}")
                
                return {
                    "master_flow": master_flow,
                    "child_flow": child_flow if flow_type == "discovery" else None
                }
                
            except Exception as e:
                # Transaction will automatically rollback
                logger.error(f"❌ Atomic flow creation failed: {e}")
                raise

    async def update_flow_with_child_atomically(
        self,
        flow_id: str,
        master_updates: Dict[str, Any],
        child_updates: Dict[str, Any]
    ) -> None:
        """Update both master and child records atomically."""
        
        async with self.db.begin():
            try:
                # Update master record
                master_repo = CrewAIFlowStateExtensionsRepository(
                    self.db, self.context.client_account_id, self.context.engagement_id
                )
                await master_repo.update_flow_state(
                    flow_id, master_updates, auto_commit=False
                )
                
                # Update child record
                child_repo = DiscoveryFlowRepository(self.db, self.context)
                await child_repo.update_flow_data(
                    flow_id, child_updates
                )
                
                logger.info(f"✅ Flow updated atomically: {flow_id}")
                
            except Exception as e:
                logger.error(f"❌ Atomic flow update failed: {e}")
                raise
```

### 2. Optimistic Locking

**Version-Based Concurrency Control:**
```python
class OptimisticLockingManager:
    """Handles optimistic locking for concurrent flow updates."""

    async def update_with_version_check(
        self,
        flow_id: str,
        updates: Dict[str, Any],
        expected_version: int
    ) -> CrewAIFlowStateExtensions:
        """Update flow state with version checking."""
        
        try:
            # Get current record with version
            current_record = await self._get_with_version(flow_id)
            
            if not current_record:
                raise StateValidationError(f"Flow {flow_id} not found")
            
            if current_record.version != expected_version:
                raise ConcurrentModificationError(
                    f"Version mismatch for flow {flow_id}. "
                    f"Expected {expected_version}, found {current_record.version}"
                )
            
            # Update with version increment
            await self._update_with_version_increment(
                current_record, updates
            )
            
            return current_record
            
        except ConcurrentModificationError:
            # Let caller handle conflict resolution
            raise
        except Exception as e:
            logger.error(f"❌ Optimistic locking update failed: {e}")
            raise

    async def _update_with_version_increment(
        self,
        record: CrewAIFlowStateExtensions,
        updates: Dict[str, Any]
    ) -> None:
        """Apply updates with version increment."""
        
        # Apply updates to record
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)
            elif key in record.flow_state:
                record.flow_state[key] = value
        
        # Increment version for next update
        record.version += 1
        record.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(record)
```

## State Recovery and Checkpointing

### 1. Secure Checkpoint Management

**Encrypted State Checkpoints:**
```python
class SecureCheckpointManager:
    """Manages encrypted state checkpoints for recovery."""

    def __init__(self, context: RequestContext):
        self.context = context
        self.encryption_key = self._get_tenant_encryption_key()
        self.redis_cache = get_redis_cache()

    async def create_checkpoint(
        self,
        flow_id: str,
        state: Dict[str, Any],
        checkpoint_type: str = "auto"
    ) -> str:
        """Create encrypted checkpoint of current state."""
        
        checkpoint_id = str(uuid.uuid4())
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "flow_id": flow_id,
            "state": state,
            "checkpoint_type": checkpoint_type,
            "created_at": datetime.utcnow().isoformat(),
            "client_account_id": self.context.client_account_id,
            "engagement_id": self.context.engagement_id
        }
        
        # Encrypt sensitive data
        encrypted_data = self._encrypt_checkpoint_data(checkpoint_data)
        
        # Store with TTL
        cache_key = self._get_checkpoint_cache_key(flow_id, checkpoint_id)
        await self.redis_cache.setex(
            cache_key,
            86400,  # 24 hours TTL
            encrypted_data
        )
        
        logger.info(f"✅ Checkpoint created: {checkpoint_id} for flow {flow_id}")
        return checkpoint_id

    async def restore_from_checkpoint(
        self,
        flow_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """Restore state from encrypted checkpoint."""
        
        cache_key = self._get_checkpoint_cache_key(flow_id, checkpoint_id)
        encrypted_data = await self.redis_cache.get(cache_key)
        
        if not encrypted_data:
            raise StateRecoveryError(
                f"Checkpoint {checkpoint_id} not found for flow {flow_id}"
            )
        
        # Decrypt and validate
        checkpoint_data = self._decrypt_checkpoint_data(encrypted_data)
        
        # Validate tenant access
        if (checkpoint_data["client_account_id"] != self.context.client_account_id or
            checkpoint_data["engagement_id"] != self.context.engagement_id):
            raise SecurityError("Access denied to checkpoint")
        
        logger.info(f"✅ Restored from checkpoint: {checkpoint_id}")
        return checkpoint_data["state"]
```

### 2. State Recovery System

**Automated Recovery Mechanisms:**
```python
class FlowStateRecovery:
    """Handles flow state recovery and repair operations."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def recover_corrupted_flow(self, flow_id: str) -> Dict[str, Any]:
        """Attempt to recover a corrupted flow state."""
        
        try:
            logger.info(f"🔧 Attempting recovery for flow: {flow_id}")
            
            # Try to get last known good state
            last_good_state = await self._find_last_good_state(flow_id)
            
            if last_good_state:
                # Restore from last good state
                await self._restore_state(flow_id, last_good_state)
                logger.info(f"✅ Flow recovered from last good state: {flow_id}")
                return last_good_state
            
            # Try checkpoint recovery
            checkpoint_state = await self._recover_from_checkpoint(flow_id)
            
            if checkpoint_state:
                await self._restore_state(flow_id, checkpoint_state)
                logger.info(f"✅ Flow recovered from checkpoint: {flow_id}")
                return checkpoint_state
            
            # Create minimal viable state
            minimal_state = await self._create_minimal_state(flow_id)
            await self._restore_state(flow_id, minimal_state)
            
            logger.warning(f"⚠️ Flow recovered with minimal state: {flow_id}")
            return minimal_state
            
        except Exception as e:
            logger.error(f"❌ Recovery failed for flow {flow_id}: {e}")
            raise StateRecoveryError(f"Unable to recover flow {flow_id}: {e}")

    async def _find_last_good_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find the last known good state from audit trail."""
        
        # Query flow state history
        query = select(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.flow_id == uuid.UUID(flow_id),
                CrewAIFlowStateExtensions.client_account_id == uuid.UUID(self.context.client_account_id),
                CrewAIFlowStateExtensions.flow_status != "failed"
            )
        ).order_by(CrewAIFlowStateExtensions.updated_at.desc())
        
        result = await self.db.execute(query)
        record = result.scalar_one_or_none()
        
        if record and record.flow_state:
            # Validate state integrity
            if await self._validate_state_integrity(record.flow_state):
                return record.flow_state
        
        return None

    async def _validate_state_integrity(self, state: Dict[str, Any]) -> bool:
        """Validate that state structure is intact."""
        
        required_fields = [
            "flow_id", "current_phase", "status", "progress_percentage"
        ]
        
        try:
            for field in required_fields:
                if field not in state:
                    return False
            
            # Validate data types
            if not isinstance(state["progress_percentage"], (int, float)):
                return False
            
            if state["progress_percentage"] < 0 or state["progress_percentage"] > 100:
                return False
            
            return True
            
        except Exception:
            return False
```

## Caching Strategy

### 1. Multi-Level Caching

**L1: In-Memory Cache:**
```python
class FlowStateL1Cache:
    """In-memory cache for frequently accessed flow states."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, datetime] = {}
        self.max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get from L1 cache with LRU tracking."""
        async with self._lock:
            if flow_id in self._cache:
                self._access_times[flow_id] = datetime.utcnow()
                return self._cache[flow_id].copy()
            return None
    
    async def set(self, flow_id: str, state: Dict[str, Any]) -> None:
        """Set in L1 cache with eviction."""
        async with self._lock:
            if len(self._cache) >= self.max_size:
                await self._evict_lru()
            
            self._cache[flow_id] = state.copy()
            self._access_times[flow_id] = datetime.utcnow()
```

**L2: Redis Distributed Cache:**
```python
class FlowStateL2Cache:
    """Redis-based distributed cache for flow states."""
    
    def __init__(self, redis_client, context: RequestContext):
        self.redis = redis_client
        self.context = context
        self.ttl = 3600  # 1 hour default TTL
    
    async def get(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get from Redis with tenant isolation."""
        cache_key = self._get_tenant_cache_key(flow_id)
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    async def set(self, flow_id: str, state: Dict[str, Any]) -> None:
        """Set in Redis with tenant isolation and TTL."""
        cache_key = self._get_tenant_cache_key(flow_id)
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(state, default=str)
        )
    
    def _get_tenant_cache_key(self, flow_id: str) -> str:
        """Generate tenant-isolated cache key."""
        return f"flow_state:{self.context.client_account_id}:{self.context.engagement_id}:{flow_id}"
```

### 2. Cache Invalidation

**Event-Driven Invalidation:**
```python
class FlowStateCacheInvalidator:
    """Handles cache invalidation on state changes."""
    
    async def invalidate_on_update(
        self,
        flow_id: str,
        updated_fields: List[str]
    ) -> None:
        """Invalidate caches when flow state changes."""
        
        # Invalidate L1 cache
        await self.l1_cache.delete(flow_id)
        
        # Invalidate L2 cache
        await self.l2_cache.delete(flow_id)
        
        # Publish invalidation event for distributed systems
        await self._publish_invalidation_event(flow_id, updated_fields)
    
    async def _publish_invalidation_event(
        self,
        flow_id: str,
        updated_fields: List[str]
    ) -> None:
        """Publish cache invalidation event."""
        
        event = {
            "event_type": "flow_state_updated",
            "flow_id": flow_id,
            "updated_fields": updated_fields,
            "timestamp": datetime.utcnow().isoformat(),
            "client_account_id": self.context.client_account_id,
            "engagement_id": self.context.engagement_id
        }
        
        await self.event_publisher.publish("flow_state_events", event)
```

## Performance Optimization

### 1. Batch Operations

**Bulk State Updates:**
```python
class FlowStateBatchProcessor:
    """Handles batch operations for multiple flows."""
    
    async def batch_update_states(
        self,
        updates: List[Dict[str, Any]]
    ) -> List[str]:
        """Update multiple flow states in a single transaction."""
        
        updated_flows = []
        
        async with self.db.begin():
            try:
                for update in updates:
                    flow_id = update["flow_id"]
                    state_data = update["state"]
                    
                    # Update individual flow
                    await self._update_flow_in_batch(flow_id, state_data)
                    updated_flows.append(flow_id)
                
                logger.info(f"✅ Batch updated {len(updated_flows)} flows")
                return updated_flows
                
            except Exception as e:
                logger.error(f"❌ Batch update failed: {e}")
                raise

    async def _update_flow_in_batch(
        self,
        flow_id: str,
        state_data: Dict[str, Any]
    ) -> None:
        """Update single flow within batch transaction."""
        
        # Use bulk update for efficiency
        stmt = update(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.flow_id == uuid.UUID(flow_id),
                CrewAIFlowStateExtensions.client_account_id == uuid.UUID(self.context.client_account_id)
            )
        ).values(
            flow_state=state_data,
            updated_at=datetime.utcnow(),
            version=CrewAIFlowStateExtensions.version + 1
        )
        
        await self.db.execute(stmt)
```

### 2. Query Optimization

**Efficient State Queries:**
```python
class OptimizedFlowQueries:
    """Optimized queries for flow state retrieval."""
    
    async def get_flows_by_status(
        self,
        statuses: List[str],
        limit: int = 100
    ) -> List[CrewAIFlowStateExtensions]:
        """Get flows by status with optimized query."""
        
        query = select(CrewAIFlowStateExtensions).where(
            and_(
                CrewAIFlowStateExtensions.client_account_id == uuid.UUID(self.context.client_account_id),
                CrewAIFlowStateExtensions.engagement_id == uuid.UUID(self.context.engagement_id),
                CrewAIFlowStateExtensions.flow_status.in_(statuses)
            )
        ).order_by(
            CrewAIFlowStateExtensions.updated_at.desc()
        ).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_flow_summary(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get lightweight flow summary without full state."""
        
        query = select(
            CrewAIFlowStateExtensions.flow_id,
            CrewAIFlowStateExtensions.flow_name,
            CrewAIFlowStateExtensions.flow_status,
            CrewAIFlowStateExtensions.current_phase,
            CrewAIFlowStateExtensions.progress_percentage,
            CrewAIFlowStateExtensions.updated_at
        ).where(
            and_(
                CrewAIFlowStateExtensions.flow_id == uuid.UUID(flow_id),
                CrewAIFlowStateExtensions.client_account_id == uuid.UUID(self.context.client_account_id)
            )
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if row:
            return {
                "flow_id": str(row.flow_id),
                "flow_name": row.flow_name,
                "status": row.flow_status,
                "current_phase": row.current_phase,
                "progress": row.progress_percentage,
                "last_updated": row.updated_at.isoformat()
            }
        
        return None
```

## Testing State Management

### 1. Unit Tests

**State Manager Testing:**
```python
@pytest.mark.asyncio
async def test_flow_state_creation():
    """Test flow state creation with proper initialization."""
    
    context = RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        user_id="test-user"
    )
    
    manager = FlowStateManager(db, context)
    flow_id = str(uuid.uuid4())
    
    initial_data = {
        "flow_type": "discovery",
        "raw_data": [{"test": "data"}],
        "metadata": {"source": "test"}
    }
    
    result = await manager.create_flow_state(flow_id, initial_data)
    
    assert result["flow_id"] == flow_id
    assert result["status"] == "running"
    assert result["progress_percentage"] == 0.0
    assert result["current_phase"] == "initialization"

@pytest.mark.asyncio
async def test_optimistic_locking():
    """Test optimistic locking prevents concurrent modifications."""
    
    # Create flow state
    flow_id = str(uuid.uuid4())
    await manager.create_flow_state(flow_id, {})
    
    # Get current version
    state = await store.get_state(flow_id)
    current_version = state["version"]
    
    # Simulate concurrent update with wrong version
    with pytest.raises(ConcurrentModificationError):
        await store.save_state(
            flow_id, 
            {"test": "update"}, 
            "processing", 
            version=current_version - 1
        )
```

### 2. Integration Tests

**Transaction Testing:**
```python
@pytest.mark.asyncio
async def test_atomic_master_child_creation():
    """Test atomic creation of master and child records."""
    
    flow_id = str(uuid.uuid4())
    transaction_manager = FlowTransactionManager(db, context)
    
    # This should either fully succeed or fully fail
    result = await transaction_manager.create_flow_atomically(
        flow_id=flow_id,
        flow_type="discovery",
        initial_data={"test": "master"},
        child_data={"data_import_id": str(uuid.uuid4())}
    )
    
    # Verify both records exist
    assert result["master_flow"] is not None
    assert result["child_flow"] is not None
    
    # Verify relationship
    assert str(result["child_flow"].master_flow_id) == str(result["master_flow"].flow_id)
```

This comprehensive state management implementation provides enterprise-grade reliability, performance, and security for managing complex flow lifecycles across the AI Modernize Migration Platform.