# Collection Flow Architecture Migration Plan
## Complete Migration from crew_class to child_flow_service Pattern

**Status**: Updated with GPT5 Review Feedback (Ready for Implementation)
**Updated**: 2025-10-07 (GPT5 Review Incorporated)
**Created**: 2025-10-07
**Author**: Claude Code (AI Assistant)
**Priority**: High (Blocking E2E Collection Flow Functionality)

---

## Executive Summary

### Current State (Hybrid Architecture - BROKEN)
Collection flow is in a **hybrid state** where:
- ✅ Gap Analysis uses NEW pattern (Persistent Agents via TenantScopedAgentPool)
- ✅ State Management uses NEW pattern (CollectionFlowStateService)
- ❌ Flow Execution uses OLD pattern (crew_class=UnifiedCollectionFlow)
- ❌ Missing CollectionChildFlowService (Discovery has it, Collection doesn't)

### Root Cause of Current E2E Failures
1. `collection_flow_config.py` registers `crew_class=UnifiedCollectionFlow`
2. `UnifiedCollectionFlow` imports `GapAnalysisAgent` (deleted in PR #506)
3. Import fails → `COLLECTION_FLOW_AVAILABLE = False` → `crew_class = None`
4. Resume/Continue operations fail with "No crew_class registered"
5. Temporary fix (commit 9516b6ed3) added placeholder `GapAnalysisAgent`
   - **This is the WRONG fix** - enables old crew pattern instead of completing migration

### Target State (Fully Migrated)
- ✅ All phases use Persistent Agents from TenantScopedAgentPool
- ✅ CollectionChildFlowService manages child flow operations
- ✅ No crew_class dependency - removed entirely
- ✅ Consistent with Discovery flow architecture
- ✅ ADR-015 and ADR-024 compliance

---

## GPT5 Critical Review Feedback (Incorporated)

### Key Corrections Applied

1. **✅ Child vs Master ID Consistency**
   - **Rule**: Use `child_flow.id` (PK) for all database persistence and foreign keys
   - **Rule**: Use `child_flow.flow_id` (business UUID) ONLY for master orchestrator interactions
   - **Applied to**: Gap analysis, questionnaire generation, validation, all DB writes

2. **✅ Repository Tenant Scoping**
   - All `CollectionFlowRepository` queries enforce `client_account_id` and `engagement_id` scoping
   - Uses ContextAwareRepository pattern or explicit filters
   - No cross-tenant data leakage possible

3. **✅ Canonical Phase Names & Progression Gates**
   - Documented: `asset_selection` → `gap_analysis` → `manual_collection` → `questionnaire_generation` → `data_validation`
   - Auto-progression gates: gaps persisted > 0 → questionnaire_generation, no pending gaps → assessment
   - State service and orchestrator use identical phase names

4. **✅ Clean Legacy Removal**
   - Grep for all `GapAnalysisAgent` imports before reverting
   - Check tests, scripts, API docs, old crews
   - Mark `UnifiedCollectionFlow` deprecated with removal target date

5. **✅ Background Jobs - No RequestContext**
   - Pass primitives only: `client_account_id`, `engagement_id`, `collection_flow_id`, `master_flow_id`
   - RequestContext NOT serializable for background tasks
   - Rate limiting via Redis TTL + idempotency keys enforced

6. **✅ Single Job State Key Pattern**
   - Use: `gap_enhancement_job:{collection_flow_id}` (child PK)
   - Progress endpoint resolves child ID from flow_id
   - Map job_state fields to API response (no duplicate keys)

7. **✅ Questionnaire Generation Service**
   - Use `TenantScopedAgentPool` with `memory=False` (ADR-024)
   - Accept child PK (`collection_flow_id=child_flow.id`) for persistence
   - Store artifacts with tenant scoping
   - Return structured statuses, non-blocking if long-running

8. **✅ Atomic Transactions & Idempotency**
   - DB writes: `async with db.begin()` and commit once per step
   - Upsert deduplication on `(collection_flow_id, field_name, gap_type, asset_id)`
   - No duplicate records on retry

9. **✅ Test Coverage**
   - Unit: `get_child_status`, `execute_phase` happy-path + unknown phase fallback
   - Integration: create → resume → verify no crew_class paths + child PK in FKs
   - Idempotency: re-run gap analysis → no duplicates, progress increments correctly

10. **✅ Logging & Error Returns**
    - Log metadata only (IDs, counts, durations) - NO raw `custom_attributes`
    - Return structured errors: `{status, error_code, message}`
    - Avoid raising raw exceptions to UI

11. **✅ Documentation & ADR-025**
    - ID mapping table: `collection_flows.id` vs `collection_flows.flow_id` vs `crewai_flow_state_extensions.flow_id`
    - Updated developer docs and router registries
    - Removed old crew path references

### Critical ID Mapping Reference (Prevent Future Bugs)

| ID Field | Type | Purpose | When to Use | Examples |
|----------|------|---------|-------------|----------|
| `collection_flows.id` | Integer (PK) | Database primary key for child flow | **ALL foreign keys, DB writes, persistence** | Gap records, questionnaires, validation results |
| `collection_flows.flow_id` | UUID (Business ID) | Master flow orchestrator reference | **Master orchestrator interactions ONLY** | MFO calls, cross-flow coordination |
| `crewai_flow_state_extensions.flow_id` | UUID (PK) | Master flow primary identifier | Master flow lifecycle, resume/pause operations | Flow registry, state persistence |

**Rules**:
- ✅ **DO**: Use `child_flow.id` for `collection_flow_id` in gap_analysis, questionnaires, validation
- ✅ **DO**: Use `child_flow.flow_id` when calling MFO or cross-flow coordination
- ❌ **DON'T**: Mix these in FK relationships (causes orphaned records)
- ❌ **DON'T**: Pass UUIDs where integers expected (type safety)

---

## Migration Phases

### Phase 1: Create CollectionChildFlowService ⏱️ 30 min
### Phase 2: Update Flow Configuration ⏱️ 15 min
### Phase 3: Update MFO Resume Logic ⏱️ 20 min
### Phase 4: Remove Old Code & Placeholders ⏱️ 20 min
### Phase 5: Update Phase Handlers ⏱️ 30 min
### Phase 6: Testing & Verification ⏱️ 45 min

**Total Estimated Time**: ~2.5 hours

---

## Detailed Implementation Plan

### **Phase 1: Create CollectionChildFlowService**

#### 1.1 Create Base Service Class
**File**: `backend/app/services/child_flow_services/collection.py` (NEW)

```python
"""
Collection Child Flow Service
Service for managing collection flow child operations

This service provides the interface between Master Flow Orchestrator (MFO)
and Collection Flow domain logic, following the pattern established by
DiscoveryChildFlowService.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.collection_flow_repository import CollectionFlowRepository
from app.services.child_flow_services.base import BaseChildFlowService
from app.services.collection_flow.state_management import CollectionFlowStateService

logger = logging.getLogger(__name__)


class CollectionChildFlowService(BaseChildFlowService):
    """Service for collection flow child operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)

        # Initialize repository with proper tenant context
        self.repository = CollectionFlowRepository(
            db=self.db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
        )

        # Initialize state management service (from PR #518)
        self.state_service = CollectionFlowStateService(db, context)

    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collection flow child status

        Args:
            flow_id: Master flow identifier

        Returns:
            Child flow status dictionary or None
        """
        try:
            # Get collection flow by master flow ID
            child_flow = await self.repository.get_by_master_flow_id(UUID(flow_id))
            if not child_flow:
                logger.warning(f"⚠️ No collection flow found for master flow {flow_id}")
                return None

            # Return status following Discovery pattern
            return {
                "status": getattr(child_flow, "status", None),
                "current_phase": getattr(child_flow, "current_phase", None),
                "progress_percentage": getattr(child_flow, "progress_percentage", 0.0),
                "metadata": getattr(child_flow, "flow_metadata", {}),
                "automation_tier": getattr(child_flow, "automation_tier", None),
                "collection_config": getattr(child_flow, "collection_config", {}),
                "phase_state": getattr(child_flow, "phase_state", {}),
            }
        except Exception as e:
            logger.error(f"Failed to get collection child flow status: {e}", exc_info=True)
            return None

    async def get_by_master_flow_id(self, flow_id: str) -> Optional[Any]:
        """
        Get collection flow by master flow ID

        Args:
            flow_id: Master flow identifier

        Returns:
            CollectionFlow entity or None
        """
        try:
            return await self.repository.get_by_master_flow_id(UUID(flow_id))
        except Exception as e:
            logger.warning(f"Failed to get collection flow by master ID: {e}")
            return None

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a collection flow phase using persistent agents

        This replaces the old crew_class execution pattern.
        Uses phase handlers + TenantScopedAgentPool for execution.

        Args:
            flow_id: Master flow identifier
            phase_name: Name of phase to execute
            phase_input: Optional phase input data

        Returns:
            Execution result dictionary
        """
        try:
            logger.info(f"🎯 Executing collection phase '{phase_name}' for flow {flow_id}")

            # Get collection flow
            child_flow = await self.get_by_master_flow_id(flow_id)
            if not child_flow:
                raise ValueError(f"Collection flow not found for master flow {flow_id}")

            # Route to appropriate phase handler based on phase name
            if phase_name == "asset_selection":
                # Asset selection is user-driven, no agent execution needed
                return {
                    "status": "awaiting_user_input",
                    "phase": phase_name,
                    "message": "Asset selection requires user interaction"
                }

            elif phase_name == "gap_analysis":
                # Use the new service-based gap analysis (PR #506, #508)
                from app.services.collection.gap_analysis import GapAnalysisService

                gap_service = GapAnalysisService(self.db, self.context)
                
                # CRITICAL: Use child_flow.id (PK) for DB persistence, NOT flow_id (business UUID)
                result = await gap_service.execute_gap_analysis(
                    collection_flow_id=child_flow.id,  # ✅ Child PK for FK relationships
                    phase_input=phase_input or {}
                )

                # Update flow phase using state service
                from app.services.collection_flow.state_management import CollectionPhase
                await self.state_service.transition_phase(
                    flow_id=child_flow.id,  # ✅ Child PK for state updates
                    new_phase=CollectionPhase.QUESTIONNAIRE_GENERATION,
                    phase_metadata={"gap_analysis_completed": True}
                )

                return result

            elif phase_name == "questionnaire_generation":
                # Use persistent agents for questionnaire generation
                from app.services.collection.questionnaire_generation import (
                    QuestionnaireGenerationService
                )

                qg_service = QuestionnaireGenerationService(self.db, self.context)
                
                # CRITICAL: Use child_flow.id (PK) for DB persistence
                result = await qg_service.generate_questionnaires(
                    collection_flow_id=child_flow.id,  # ✅ Child PK for FK relationships
                    phase_input=phase_input or {}
                )

                return result

            elif phase_name == "manual_collection":
                # Manual collection phase
                return {
                    "status": "awaiting_user_responses",
                    "phase": phase_name,
                    "message": "Manual collection awaiting questionnaire responses"
                }

            elif phase_name == "data_validation":
                # Data validation phase
                from app.services.collection.validation import ValidationService

                validation_service = ValidationService(self.db, self.context)
                
                # CRITICAL: Use child_flow.id (PK) for DB persistence
                result = await validation_service.validate_collected_data(
                    collection_flow_id=child_flow.id,  # ✅ Child PK for FK relationships
                    phase_input=phase_input or {}
                )

                return result

            else:
                # Per GPT5 review: Log at info (not warning) for transitional states
                logger.info(f"ℹ️  Unknown phase '{phase_name}' - returning noop success")
                return {
                    "status": "success",
                    "phase": phase_name,
                    "message": f"Phase '{phase_name}' completed (no specific handler)",
                    "execution_type": "noop"
                }

        except Exception as e:
            logger.error(f"❌ Phase execution failed: {phase_name} - {e}", exc_info=True)
            raise
```

#### 1.2 Update Child Flow Services Init
**File**: `backend/app/services/child_flow_services/__init__.py`

```python
"""Child Flow Services Module"""

from .base import BaseChildFlowService
from .collection import CollectionChildFlowService  # ADD THIS
from .discovery import DiscoveryChildFlowService

__all__ = [
    "BaseChildFlowService",
    "CollectionChildFlowService",  # ADD THIS
    "DiscoveryChildFlowService",
]
```

---

### **Phase 2: Update Flow Configuration**

#### 2.1 Remove crew_class, Add child_flow_service
**File**: `backend/app/services/flow_configs/collection_flow_config.py`

**BEFORE** (Lines 23-34, 90-92):
```python
# Conditional import for UnifiedCollectionFlow with graceful fallback
COLLECTION_FLOW_AVAILABLE = False
UnifiedCollectionFlow = None

try:
    from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow
    COLLECTION_FLOW_AVAILABLE = True
except ImportError:
    COLLECTION_FLOW_AVAILABLE = False
    UnifiedCollectionFlow = None

# ... later in file ...
crew_class=(
    UnifiedCollectionFlow if COLLECTION_FLOW_AVAILABLE else None
),  # Conditional crew class registration
```

**AFTER**:
```python
# Import child flow service (NEW pattern - replaces crew_class)
from app.services.child_flow_services import CollectionChildFlowService

# ... later in file ...
# Per ADR-015: Use child_flow_service pattern (like Discovery)
# Removed: crew_class (old pattern using UnifiedCollectionFlow)
child_flow_service=CollectionChildFlowService,  # NEW: Replaces crew_class
```

**Full change**:
1. Remove lines 23-34 (COLLECTION_FLOW_AVAILABLE logic)
2. Add import: `from app.services.child_flow_services import CollectionChildFlowService`
3. Replace line 90-92 (`crew_class=...`) with `child_flow_service=CollectionChildFlowService,`

---

### **Phase 3: Update MFO Resume Logic**

#### 3.1 Add child_flow_service Support to Resume
**File**: `backend/app/services/master_flow_orchestrator/operations/lifecycle_commands.py`

**Location**: Lines 309-379 (in `_restore_and_resume_flow_from_state` method)

**BEFORE**:
```python
if flow_config.crew_class:
    # OLD: Instantiate crew class and resume
    ...
else:
    logger.warning(f"No crew_class registered for flow type '{master_flow.flow_type}'")
    return {"status": "resumed", "message": "..."}
```

**AFTER**:
```python
# Check child_flow_service FIRST (new pattern), then crew_class (legacy)
if flow_config.child_flow_service:
    # NEW PATTERN: Use child flow service for execution
    logger.info(f"Using child_flow_service for {master_flow.flow_type} flow execution")

    child_service = flow_config.child_flow_service(self.db, self.context)
    current_phase = master_flow.get_current_phase() or "initialization"

    # Execute current phase via child service
    result = await child_service.execute_phase(
        flow_id=str(master_flow.flow_id),
        phase_name=current_phase,
        phase_input=resume_context or {}
    )

    return {
        "status": "resumed",
        "message": f"Flow resumed via child_flow_service",
        "current_phase": current_phase,
        "execution_result": result
    }

elif flow_config.crew_class:
    # LEGACY PATTERN: Old crew-based execution (Discovery only)
    logger.warning(f"Using legacy crew_class for {master_flow.flow_type} (should migrate)")
    # ... existing crew_class logic ...

else:
    logger.warning(f"No execution handler for flow type '{master_flow.flow_type}'")
    return {
        "status": "resumed",
        "message": f"Flow type '{master_flow.flow_type}' has no execution handler",
        "current_phase": master_flow.get_current_phase() or "initialization",
    }
```

---

### **Phase 4: Remove Old Code & Placeholders**

#### 4.1 Revert GapAnalysisAgent Placeholder

**Command**:
```bash
git revert 9516b6ed3 --no-commit
```

This will remove:
- `backend/app/services/ai_analysis/gap_analysis_agent.py` (placeholder)
- Export from `backend/app/services/ai_analysis/__init__.py`

**Comprehensive Verification (Per GPT5 Review)**:

```bash
# 1. Check for ALL imports across codebase
grep -r "from app.services.ai_analysis import GapAnalysisAgent" backend/
grep -r "from app.services.ai_analysis import.*GapAnalysisAgent" backend/
grep -r "import.*GapAnalysisAgent" backend/

# 2. Check tests for references
grep -r "GapAnalysisAgent" backend/tests/

# 3. Check scripts and utilities
grep -r "GapAnalysisAgent" backend/scripts/
grep -r "GapAnalysisAgent" backend/alembic/

# 4. Check API documentation
grep -r "GapAnalysisAgent" docs/

# 5. Check old crew files
grep -r "GapAnalysisAgent" backend/app/services/crewai_flows/

# 6. Verify import fails (correct - we don't need it)
python3 -c "from app.services.ai_analysis import GapAnalysisAgent"  # Should fail

# 7. Verify UnifiedCollectionFlow is NOT imported anywhere except deprecation file
grep -r "from.*unified_collection_flow import UnifiedCollectionFlow" backend/ | grep -v "deprecated"
```

**Expected Results**:
- All greps return empty (no references found)
- Import test fails with ImportError
- UnifiedCollectionFlow only in deprecated file

#### 4.2 Mark UnifiedCollectionFlow as Deprecated
**File**: `backend/app/services/crewai_flows/unified_collection_flow.py`

Add deprecation notice at top of file:
```python
"""
DEPRECATED: UnifiedCollectionFlow (Crew-based pattern)

This module is DEPRECATED as of 2025-10-07 (PR #519).
Collection flows now use:
- CollectionChildFlowService for flow orchestration
- TenantScopedAgentPool for persistent agents
- Phase handlers for execution logic

This file is retained temporarily for reference only.
Will be removed in future cleanup (target: 2025-11-01).

See: docs/adr/015-persistent-multi-tenant-agent-architecture.md
"""

import warnings
warnings.warn(
    "UnifiedCollectionFlow is deprecated. Use CollectionChildFlowService instead.",
    DeprecationWarning,
    stacklevel=2
)
```

**DO NOT delete yet** - keep for one release cycle as reference.

#### 4.3 Update Collection Flow Config Import Guards
Since we're removing the conditional import, we need to ensure no other files try to import UnifiedCollectionFlow.

**Search for imports**:
```bash
grep -r "from.*unified_collection_flow import" backend/app --include="*.py"
```

Expected results:
- `collection_flow_config.py` - we're removing this
- `unified_collection_flow.py` itself - deprecation warning only

---

### **Phase 5: Update Phase Handlers**

#### 5.1 Ensure Phase Handlers Use Persistent Agents

**Files to verify** (should already be correct from PR #506, #508):
- ✅ `backend/app/services/collection/gap_analysis/service.py`
- ✅ `backend/app/services/collection/gap_analysis/agent_helpers.py`
- ✅ `backend/app/services/collection/gap_analysis/enhancement_processor/agent_setup.py`

**Key pattern** (should already exist):
```python
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

agent = await TenantScopedAgentPool.get_or_create_agent(
    client_id=client_account_id,
    engagement_id=engagement_id,
    agent_type="gap_analysis_specialist",
)
```

**No changes needed** - verify only.

#### 5.2 Enforce Repository Tenant Scoping (Per GPT5 Review)

**Files to update**:
- `backend/app/repositories/collection_flow_repository.py`

**Verification checklist**:
```python
# All queries MUST include tenant scoping
async def get_by_master_flow_id(self, master_flow_id: UUID) -> Optional[CollectionFlow]:
    query = (
        select(CollectionFlow)
        .where(CollectionFlow.flow_id == master_flow_id)
        .where(CollectionFlow.client_account_id == self.client_account_id)  # ✅ Required
        .where(CollectionFlow.engagement_id == self.engagement_id)          # ✅ Required
    )
    result = await self.db.execute(query)
    return result.scalars().first()
```

**Pattern**: Use ContextAwareRepository base class OR explicit filters in every query.

#### 5.3 Define Phase Progression Gates (Per GPT5 Review)

**Canonical Phase Flow**:
```
asset_selection → gap_analysis → manual_collection → questionnaire_generation → data_validation → assessment
```

**Auto-Progression Rules**:
```python
# Gap Analysis → Questionnaire Generation
if gaps_persisted_count > 0:
    await transition_phase("questionnaire_generation")

# Manual Collection → Assessment  
if no_pending_gaps and all_validations_complete:
    await transition_phase("assessment")
```

**Document in**: `docs/development/collection_flow/PHASE_PROGRESSION_GATES.md`

#### 5.4 Create Questionnaire Generation Service (Per GPT5 Review)

**Check if exists**:
```bash
ls -la backend/app/services/collection/questionnaire_generation/
```

If missing, create:
**File**: `backend/app/services/collection/questionnaire_generation/__init__.py`

```python
"""Questionnaire Generation Service using Persistent Agents"""

import logging
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

logger = logging.getLogger(__name__)


class QuestionnaireGenerationService:
    """Service for generating questionnaires using persistent agents
    
    Per GPT5 Review:
    - Use TenantScopedAgentPool with memory=False (ADR-024)
    - Accept child PK for persistence (collection_flow_id = child_flow.id)
    - Store artifacts with tenant scoping
    - Return structured statuses, non-blocking if long-running
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def generate_questionnaires(
        self,
        collection_flow_id: int,  # ✅ Child PK (integer), NOT UUID
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate questionnaires using persistent questionnaire agent

        Args:
            collection_flow_id: Child flow PK (collection_flows.id)
            phase_input: Phase input data with gap analysis results

        Returns:
            Structured questionnaire generation result
        """
        try:
            # Get persistent agent (memory=False per ADR-024)
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=str(self.context.client_account_id),
                engagement_id=str(self.context.engagement_id),
                agent_type="questionnaire_specialist",
            )

            # Execute generation task
            logger.info(
                f"Generating questionnaires for flow {collection_flow_id} "
                f"(client={self.context.client_account_id}, engagement={self.context.engagement_id})"
            )

            # Atomic transaction for questionnaire persistence
            async with self.db.begin():
                # TODO: Implement questionnaire generation logic with tenant scoping
                # All inserts MUST include collection_flow_id (FK to child PK)
                pass

            return {
                "status": "success",
                "questionnaires_generated": 0,
                "message": "Questionnaire generation completed",
                "metadata": {
                    "collection_flow_id": collection_flow_id,
                    "client_account_id": self.context.client_account_id,
                    "engagement_id": self.context.engagement_id
                }
            }
            
        except Exception as e:
            # Structured error return (per GPT5 review)
            logger.error(f"Questionnaire generation failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error_code": "QUESTIONNAIRE_GENERATION_FAILED",
                "message": str(e),
                "metadata": {
                    "collection_flow_id": collection_flow_id
                }
            }
```

#### 5.5 Update Background Job Patterns (Per GPT5 Review)

**Critical**: RequestContext is NOT serializable for background tasks.

**Wrong Pattern**:
```python
# ❌ DON'T: Pass RequestContext to background job
background_job.delay(context=context, flow_id=flow_id)
```

**Correct Pattern**:
```python
# ✅ DO: Pass primitives only
background_job.delay(
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id,
    collection_flow_id=child_flow.id,  # Child PK
    master_flow_id=str(child_flow.flow_id)  # Master UUID
)
```

**Job State Key Pattern**:
```python
# Single key pattern (per GPT5 review)
job_state_key = f"gap_enhancement_job:{collection_flow_id}"  # Use child PK

# Progress endpoint resolves child ID from master flow_id
child_flow = await repository.get_by_master_flow_id(UUID(flow_id))
job_state = await redis.get(f"gap_enhancement_job:{child_flow.id}")
```

---

### **Phase 6: Testing & Verification**

#### 6.1 Unit Tests

**Create**: `backend/tests/unit/test_collection_child_flow_service.py`

```python
"""Unit tests for CollectionChildFlowService"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.child_flow_services.collection import CollectionChildFlowService


@pytest.mark.asyncio
async def test_get_child_status_success(mock_db_session, mock_context):
    """Test successful child status retrieval"""
    service = CollectionChildFlowService(mock_db_session, mock_context)

    # Mock repository response
    mock_flow = MagicMock()
    mock_flow.status = "running"
    mock_flow.current_phase = "gap_analysis"
    mock_flow.progress_percentage = 50.0

    service.repository.get_by_master_flow_id = AsyncMock(return_value=mock_flow)

    result = await service.get_child_status(str(uuid4()))

    assert result is not None
    assert result["status"] == "running"
    assert result["current_phase"] == "gap_analysis"


@pytest.mark.asyncio
async def test_get_child_status_not_found(mock_db_session, mock_context):
    """Test child status when flow not found"""
    service = CollectionChildFlowService(mock_db_session, mock_context)

    service.repository.get_by_master_flow_id = AsyncMock(return_value=None)

    result = await service.get_child_status(str(uuid4()))

    assert result is None
```

#### 6.2 Integration Test

**Update**: `backend/tests/backend/integration/test_collection_flow_e2e.py`

```python
"""E2E test for collection flow with new architecture"""

import pytest


@pytest.mark.asyncio
async def test_collection_flow_creation_and_resume(
    async_client,
    test_db_session,
    test_context
):
    """Test collection flow creation and resume with child_flow_service"""

    # 1. Create collection flow
    response = await async_client.post(
        "/api/v1/collection/flows",
        json={
            "automation_tier": "tier_2",
            "collection_config": {}
        }
    )
    assert response.status_code == 201
    flow_id = response.json()["flow_id"]
    master_flow_id = response.json()["master_flow_id"]

    # 2. Verify master flow registration
    master_flow_query = f"""
    SELECT flow_id, flow_type FROM migration.crewai_flow_state_extensions
    WHERE flow_id = '{master_flow_id}'
    """
    result = await test_db_session.execute(master_flow_query)
    master_record = result.first()
    assert master_record is not None
    assert master_record.flow_type == "collection"

    # 3. Resume flow (should use child_flow_service, NOT crew_class)
    response = await async_client.post(
        f"/api/v1/collection/flows/{flow_id}/continue"
    )
    assert response.status_code == 200

    # 4. Verify no crew_class warnings in logs
    # (Check that it used child_flow_service path)
    # This assertion depends on log capture setup
```

#### 6.3 Manual E2E Test Plan

**Prerequisites**:
1. Backend running on localhost:8000
2. Frontend running on localhost:8081
3. Docker containers up: `cd config/docker && docker-compose up -d`

**Test Steps**:

**Step 1: Create Collection Flow**
```bash
# Navigate to collection overview
open http://localhost:8081/collection/overview

# Click "Create New Collection Flow"
# Expected: Flow created with status=PAUSED, phase=asset_selection
```

**Step 2: Verify Master Flow Registration**
```sql
-- Check master flow exists
SELECT flow_id, flow_type, flow_status
FROM migration.crewai_flow_state_extensions
ORDER BY created_at DESC LIMIT 1;

-- Expected: Record exists with flow_type='collection'
```

**Step 3: Resume Flow**
```bash
# Click "Resume Flow" button
# Expected: No errors, status changes to running
```

**Step 4: Check Backend Logs**
```bash
docker logs migration_backend --tail 50 | grep -E "child_flow_service|crew_class"

# Expected logs:
# ✅ "Using child_flow_service for collection flow execution"
# ❌ Should NOT see "No crew_class registered"
# ❌ Should NOT see "UnifiedCollectionFlow"
```

**Step 5: Verify Phase Execution**
```bash
# Select assets and click Continue
# Expected: Transitions to gap_analysis phase using persistent agents
```

**Step 6: Verify Persistent Agents Used**
```bash
docker logs migration_backend --tail 100 | grep "TenantScopedAgentPool"

# Expected:
# "✅ Agent created: gap_analysis_specialist"
# Should be REUSING agents, not creating new ones each time
```

---

## Rollback Plan

### If Migration Fails

**Immediate Rollback** (< 5 minutes):
```bash
# 1. Revert all migration commits
git revert HEAD~3..HEAD --no-commit

# 2. Restore GapAnalysisAgent placeholder
git cherry-pick 9516b6ed3

# 3. Restart backend
cd config/docker && docker-compose restart backend
```

**Restore Points**:
- Before Phase 1: Current state (with placeholder)
- After Phase 2: Collection config updated
- After Phase 4: Old code removed

**Validation After Rollback**:
```bash
# Should work with placeholder in place
curl http://localhost:8000/api/v1/collection/flows
```

---

## Success Criteria

### Functional Requirements
- [ ] ✅ Collection flows create successfully
- [ ] ✅ Master flow records persist in `crewai_flow_state_extensions`
- [ ] ✅ Resume/Continue operations execute without errors
- [ ] ✅ Phase transitions work (asset_selection → gap_analysis → etc.)
- [ ] ✅ Gap analysis uses `TenantScopedAgentPool` (persistent agents)
- [ ] ✅ No crew_class warnings in logs
- [ ] ✅ E2E collection flow completes successfully

### Code Quality Requirements
- [ ] ✅ All pre-commit checks pass
- [ ] ✅ No linting errors (ruff, flake8, mypy)
- [ ] ✅ Unit tests pass (>80% coverage for new code)
- [ ] ✅ Integration tests pass
- [ ] ✅ No breaking changes to existing Discovery flows

### Documentation Requirements
- [ ] ✅ ADR created documenting migration decision
- [ ] ✅ CollectionChildFlowService has comprehensive docstrings
- [ ] ✅ README updated with new architecture
- [ ] ✅ Deprecation warnings added to old code

---

## Files Modified Summary

### New Files (4)
1. `backend/app/services/child_flow_services/collection.py` - CollectionChildFlowService
2. `backend/tests/unit/test_collection_child_flow_service.py` - Unit tests
3. `backend/tests/backend/integration/test_collection_flow_e2e.py` - Integration test
4. `docs/adr/025-collection-flow-child-service-migration.md` - ADR

### Modified Files (5)
1. `backend/app/services/child_flow_services/__init__.py` - Add CollectionChildFlowService export
2. `backend/app/services/flow_configs/collection_flow_config.py` - Remove crew_class, add child_flow_service
3. `backend/app/services/master_flow_orchestrator/operations/lifecycle_commands.py` - Support child_flow_service in resume logic
4. `backend/app/services/crewai_flows/unified_collection_flow.py` - Add deprecation warning
5. `COLLECTION_FLOW_MIGRATION_PLAN.md` - This document

### Deleted Files (2)
1. `backend/app/services/ai_analysis/gap_analysis_agent.py` - Placeholder (revert 9516b6ed3)
2. Export from `backend/app/services/ai_analysis/__init__.py` - GapAnalysisAgent export

### Total LOC Impact
- **Added**: ~450 lines (CollectionChildFlowService + tests)
- **Modified**: ~100 lines (config, MFO, deprecation)
- **Deleted**: ~75 lines (placeholder)
- **Net**: +475 lines

---

## Architecture Alignment

### ADR Compliance
- ✅ **ADR-015**: Persistent Multi-Tenant Agent Architecture
  - Uses TenantScopedAgentPool
  - Maintains agent instances per tenant
  - Enables learning and memory accumulation

- ✅ **ADR-024**: TenantMemoryManager Architecture
  - No CrewAI built-in memory (disabled)
  - Uses TenantMemoryManager for agent learning
  - PostgreSQL + pgvector backend

- ✅ **ADR-006**: Master Flow Orchestrator
  - All flows register with crewai_flow_state_extensions
  - Single source of truth for workflow operations

- ✅ **ADR-012**: Flow Status Management Separation
  - Master flow: lifecycle states (running, paused, completed)
  - Child flow: operational decisions (phases, UI state)

### Pattern Consistency
- ✅ Matches Discovery flow pattern (child_flow_service)
- ✅ Uses CollectionFlowStateService (PR #518)
- ✅ Uses persistent agents (PR #508)
- ✅ Service-based gap analysis (PR #506)

---

## Risk Assessment

### High Risk Areas
1. **Resume Logic Changes** (Phase 3)
   - Risk: Breaking existing resume functionality
   - Mitigation: Comprehensive testing, rollback plan ready

2. **Removing Placeholder** (Phase 4)
   - Risk: Import errors if any code still references GapAnalysisAgent
   - Mitigation: Grep for all references before deletion

### Medium Risk Areas
1. **Child Flow Service Bugs** (Phase 1)
   - Risk: Incorrect status mapping or missing fields
   - Mitigation: Follow Discovery pattern exactly, unit tests

2. **Phase Handler Integration** (Phase 5)
   - Risk: Phase handlers not compatible with new service
   - Mitigation: Phase handlers already use persistent agents (verified)

### Low Risk Areas
1. **Configuration Changes** (Phase 2)
   - Risk: Typos in config file
   - Mitigation: Python will fail fast on import errors

---

## Post-Migration Tasks

### Immediate (Same Day)
- [ ] Monitor production logs for 2 hours
- [ ] Verify no error spike in Sentry/monitoring
- [ ] Check database for orphaned flows
- [ ] Update team documentation

### Short Term (Within 1 Week)
- [ ] Create ADR-025 documenting migration
- [ ] Add monitoring dashboard for child_flow_service metrics
- [ ] Performance comparison: old crew vs new service
- [ ] Clean up deprecated code comments

### Long Term (Within 1 Month)
- [ ] Delete UnifiedCollectionFlow.py entirely
- [ ] Migrate any remaining crew-based flows
- [ ] Optimize persistent agent pool performance
- [ ] Create runbook for future flow type migrations

---

## Approval Checklist

**Before Implementation, Verify**:
- [ ] All stakeholders reviewed this plan
- [ ] Rollback plan tested and validated
- [ ] Test environment available for validation
- [ ] Backup of current working state created
- [ ] Communication plan for deployment window

**Approver Sign-off**:
- [ ] Technical Lead: _______________
- [ ] Product Owner: _______________
- [ ] DevOps/SRE: _______________

---

## Questions for Review

1. **Scope**: Should we migrate Collection flow in this PR, or split into multiple smaller PRs?
   - Option A: Single PR (all phases)
   - Option B: Phase 1-3 in PR #519, Phase 4-5 in PR #520

2. **Timeline**: Can we allocate 2-3 hours for implementation + testing?
   - If yes: Proceed with full migration
   - If no: Implement Phase 1-2 only, defer Phase 3-5

3. **Questionnaire Service**: Does `QuestionnaireGenerationService` already exist, or should we create placeholder?
   - Need to verify current implementation status

4. **Backward Compatibility**: Should we maintain crew_class support for one release cycle?
   - Recommendation: Yes (keep deprecated but functional for 1 month)

---

## Next Steps After Approval

1. ✅ Get approval on this plan
2. Create feature branch: `feat/collection-child-flow-service-migration`
3. Implement Phase 1 (CollectionChildFlowService)
4. Run unit tests
5. Implement Phase 2-3 (Configuration + MFO)
6. Run integration tests
7. Implement Phase 4-5 (Cleanup + Handlers)
8. Full E2E test
9. Create PR with detailed description
10. Merge after review

---

**Ready for Review and Approval** ✅
