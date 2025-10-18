# Collection Flow Question Generation: Architectural Analysis & Recommendations

**Date**: 2025-10-18
**Issue**: All asset types (applications, servers, databases, network devices) receive identical questions that aren't asset-type-specific. Agentic analysis doesn't prune invalid questions, only adds confidence scores.

---

## Executive Summary

### The Problem
The collection flow generates the same questions for all asset types because:
1. **Hardcoded Default**: `asset_type` always defaults to `"application"` in question generation
2. **Missing Lookup**: No method exists to retrieve actual asset type from the database
3. **Data Loss**: Gap analysis doesn't preserve asset type metadata through the pipeline
4. **No Intelligence**: Agents add confidence scores but don't filter irrelevant questions

### The Good News
**The infrastructure for asset-specific questions already exists and works correctly.** We have:
- `DatabaseQuestionsGenerator` - Database-specific questions (replication, engines, performance)
- `ApplicationQuestionsGenerator` - Application questions (frameworks, languages, containers)
- `ServerQuestionsGenerator` - Server questions (CPU, RAM, virtualization)
- `_generate_technical_detail_question()` - Routing logic that selects the right generator

**The problem**: This infrastructure is never reached because `asset_type` is hardcoded to `"application"`.

---

## Root Cause Analysis

### 1. Hardcoded Default in Question Generation
**File**: `backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py:254`

```python
"asset_type": "application",  # ← HARDCODED DEFAULT
```

**Impact**: ALL assets - databases, servers, network devices - get routed to the application question generator.

### 2. Missing Asset Type Retrieval
**File**: `backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py:58-96`

```python
async def _get_asset_name(self, asset_id: str) -> str:
    # This method EXISTS ✓

# async def _get_asset_type(self, asset_id: str) -> str:
    # This method DOES NOT EXIST ✗
```

**Impact**: System never attempts to lookup the actual asset type from `business_context` table.

### 3. Gap Analysis Doesn't Preserve Asset Metadata
**File**: `backend/app/services/flow_configs/collection_phases/gap_analysis_phase.py:39-63`

```python
# Current output structure
{
    "field_name": "database_engine",
    "priority": "high",
    "description": "Missing database engine information"
    # MISSING: "asset_id": "uuid"
    # MISSING: "asset_type": "database"
}
```

**Impact**: Question generation receives gaps without knowing which asset has each gap or what type that asset is.

### 4. Agents Have No Filtering Capability
**Files**:
- `backend/app/services/ai_analysis/questionnaire_generator/agents.py`
- `backend/app/services/ai_analysis/questionnaire_generator/tasks.py`

**Current Agent Roles**:
- Questionnaire Designer: Generates questions
- Context Specialist: Adds migration context
- Quality Validator: Assigns confidence scores

**Missing Role**: Filter/prune questions that don't apply to the asset type

**Impact**: Database-specific questions go to applications, server questions go to databases, etc.

### 5. Confidence Scores Are Metadata Only
**File**: `backend/app/services/flow_configs/collection_handlers/questionnaire_handlers.py`

```python
# Confidence is recorded but NOT used for:
# - Filtering generated questions
# - Triggering question removal
# - Validating question/asset relevance
```

---

## Current vs Desired Architecture

### Current Broken Flow
```
Collection
    ↓
Gap Analysis (no asset_type)
    ↓
Question Generation (defaults to "application")
    ↓
Application Question Generator (always)
    ↓
Agents (confidence scoring only)
    ↓
ALL assets get same questions ❌
```

### Desired Architecture
```
Collection (knows asset_type from business_context)
    ↓
Gap Analysis (preserve asset_type + asset_id per gap)
    ↓
Question Generation (lookup asset_type from business_context)
    ↓
Route to Correct Generator:
    ├─ Database → DatabaseQuestionsGenerator
    ├─ Application → ApplicationQuestionsGenerator
    ├─ Server → ServerQuestionsGenerator
    └─ Network → NetworkQuestionsGenerator
    ↓
Agents (confidence scoring + relevance validation)
    ↓
Filter: confidence >= threshold AND is_relevant == true
    ↓
Asset-specific questions ✓
```

---

## Recommended Solution: Four-Phase Implementation

### Phase 1: Fix Asset Type Lookup (QUICK WIN - High Impact, Low Effort)

**Changes Required**:

1. **Add `_get_asset_type()` method** in `generation.py`
   ```python
   async def _get_asset_type(self, asset_id: str) -> str:
       """Retrieve asset type from business_context table."""
       try:
           result = await self.db.execute(
               select(BusinessContext.asset_type)
               .where(BusinessContext.asset_id == asset_id)
               .where(BusinessContext.client_account_id == self.client_account_id)
               .where(BusinessContext.engagement_id == self.engagement_id)
           )
           row = result.scalar_one_or_none()
           return row if row else "application"  # Safe fallback
       except Exception as e:
           self.logger.error(f"Error fetching asset type: {e}")
           return "application"
   ```

2. **Replace hardcoded default** in `generation.py:254`
   ```python
   # Before
   "asset_type": "application",  # ← HARDCODED

   # After
   "asset_type": await self._get_asset_type(gap.get("asset_id")) if gap.get("asset_id") else "application",
   ```

**Impact**:
- ✅ Activates existing asset-specific generators
- ✅ Database assets get database questions
- ✅ Server assets get server questions
- ✅ Zero new code - just connects existing infrastructure

**Effort**: 2-3 hours
**Risk**: Low (safe fallback to "application" if lookup fails)

---

### Phase 2: Enhance Data Pipeline (Medium Priority)

**Changes Required**:

1. **Enhance Gap Analysis Output** in `gap_analysis_phase.py`
   ```python
   # Current structure
   identified_gaps = [
       {
           "field_name": str,
           "priority": str,
           "description": str
       }
   ]

   # Enhanced structure
   identified_gaps = [
       {
           "field_name": str,
           "priority": str,
           "description": str,
           "asset_id": str,        # ← ADD
           "asset_type": str       # ← ADD
       }
   ]
   ```

2. **Update Gap Identifier Tool** to accept and preserve asset metadata
   - File: `backend/app/services/tools/gap_analysis/gap_identifier.py`
   - Add asset_id and asset_type to input schema
   - Pass through to output structure

3. **Modify Phase Configuration** to provide asset context
   - File: `backend/app/services/flow_configs/collection_phases/gap_analysis_phase.py:39-63`
   - Include asset metadata in phase inputs

**Impact**:
- ✅ Asset context flows through entire pipeline
- ✅ Question generation has full context
- ✅ Supports multi-asset gap analysis
- ✅ Better error messages (can show which asset has issues)

**Effort**: 4-6 hours
**Risk**: Medium (requires coordinated changes across multiple components)

---

### Phase 3: Add Agent Intelligence (High Value)

**Changes Required**:

1. **Enhance Quality Validator Agent** in `agents.py`
   ```python
   # Add to agent backstory/goal
   "You validate that questions are appropriate for the asset type. "
   "Remove questions that don't apply (e.g., database questions for applications)."
   ```

2. **Add Asset Context to Agent Inputs** in `tasks.py`
   ```python
   # Current
   {
       "gaps": identified_gaps,
       "asset_name": asset_name,
       "context": context
   }

   # Enhanced
   {
       "gaps": identified_gaps,
       "asset_name": asset_name,
       "asset_type": asset_type,     # ← ADD
       "context": context
   }
   ```

3. **Update Agent Output Schema**
   ```python
   # Current output
   {
       "question": str,
       "confidence": float
   }

   # Enhanced output
   {
       "question": str,
       "confidence": float,
       "is_relevant_for_asset_type": bool,  # ← ADD
       "relevance_reason": str              # ← ADD (optional, for debugging)
   }
   ```

4. **Implement Two-Level Filtering** in `questionnaire_handlers.py`
   ```python
   # Current filtering
   filtered = [q for q in questions if q["confidence"] >= threshold]

   # Enhanced filtering
   filtered = [
       q for q in questions
       if q["confidence"] >= threshold
       and q.get("is_relevant_for_asset_type", True)  # Safe default
   ]
   ```

**Impact**:
- ✅ Agents actively prune irrelevant questions
- ✅ Reduces noise for data collection teams
- ✅ Provides reasoning for why questions were removed
- ✅ Better user experience in UI

**Effort**: 6-8 hours
**Risk**: Medium (requires LLM prompt tuning to avoid over-filtering)

---

### Phase 4: Optimization (Future Enhancement)

**Potential Improvements**:

1. **Pre-Agent Filtering**
   - Before sending questions to agents, filter obvious mismatches
   - Example: Don't send "database_engine" questions to servers
   - Saves LLM tokens and processing time

2. **Question Template Caching**
   - Cache asset-type-specific question templates
   - Reduces duplicate LLM calls for similar assets
   - Store in `TenantMemoryManager` with `LearningScope.CLIENT`

3. **Deduplication Across Assets**
   - If 10 servers have same gap, generate questions once
   - Apply to all similar assets
   - Reduces processing time from O(n) to O(unique_asset_types)

4. **Confidence Score Learning**
   - Track which questions actually get answered
   - Use TenantMemoryManager to store successful patterns
   - Adjust confidence scores based on historical success

**Impact**:
- ✅ Better performance
- ✅ Lower LLM costs
- ✅ Faster question generation

**Effort**: 12-16 hours
**Risk**: Low (optional optimizations on top of working system)

---

## Implementation Priority Matrix

| Phase | Impact | Effort | Risk | Priority |
|-------|--------|--------|------|----------|
| Phase 1: Asset Type Lookup | **HIGH** | Low (2-3h) | Low | **DO FIRST** |
| Phase 2: Enhanced Pipeline | Medium | Medium (4-6h) | Medium | Do Second |
| Phase 3: Agent Intelligence | **HIGH** | Medium (6-8h) | Medium | **DO THIRD** |
| Phase 4: Optimization | Low | High (12-16h) | Low | Future |

---

## Specific Files to Modify

### Phase 1 (Immediate)
- ✏️ `backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py`
  - Line 254: Remove hardcoded "application" default
  - Lines 58-96: Add `_get_asset_type()` method (similar to `_get_asset_name()`)

### Phase 2 (Near-term)
- ✏️ `backend/app/services/flow_configs/collection_phases/gap_analysis_phase.py`
  - Lines 39-63: Add asset_id and asset_type to output structure
- ✏️ `backend/app/services/tools/gap_analysis/gap_identifier.py`
  - Accept and preserve asset metadata

### Phase 3 (Important)
- ✏️ `backend/app/services/ai_analysis/questionnaire_generator/agents.py`
  - Enhance Quality Validator agent backstory/goal
- ✏️ `backend/app/services/ai_analysis/questionnaire_generator/tasks.py`
  - Add asset_type to agent inputs
  - Add is_relevant_for_asset_type to output schema
- ✏️ `backend/app/services/flow_configs/collection_handlers/questionnaire_handlers.py`
  - Implement two-level filtering (confidence + relevance)

### Phase 4 (Future)
- 🔮 Pre-filtering logic in generation service
- 🔮 Caching layer using TenantMemoryManager
- 🔮 Deduplication logic in processors
- 🔮 Learning feedback loop

---

## Key Architectural Principles Applied

1. **Enhance, Don't Replace**: Asset-specific generators already exist and work. We're just fixing the routing to use them.

2. **Preserve Multi-Tenancy**: All lookups include `client_account_id` and `engagement_id` scoping.

3. **Graceful Degradation**: Safe fallback to "application" if asset type lookup fails.

4. **Two-Level Filtering**:
   - Level 1 (Pre-agent): Route to correct generator based on asset type
   - Level 2 (Agent-based): Validate relevance and provide confidence

5. **Data Integrity**: Asset metadata flows through entire pipeline without loss.

---

## Testing Strategy

### Unit Tests
- ✅ Test `_get_asset_type()` with valid/invalid asset_ids
- ✅ Test routing logic selects correct generator
- ✅ Test agent filtering marks irrelevant questions correctly

### Integration Tests
- ✅ End-to-end: Database asset → database-specific questions
- ✅ End-to-end: Server asset → server-specific questions
- ✅ End-to-end: Application asset → application-specific questions
- ✅ Multi-asset scenario: Mixed asset types get appropriate questions

### Regression Tests
- ✅ Existing tests still pass (fallback to "application" for legacy data)
- ✅ Confidence scoring still works
- ✅ Multi-tenant isolation maintained

---

## Expected Outcomes

### After Phase 1 (Immediate Win)
- Database assets ask about engines, replication, performance
- Server assets ask about CPU, RAM, storage, virtualization
- Application assets ask about languages, frameworks, containers
- Network devices get network-specific questions

### After Phase 3 (Full Solution)
- Questions are both **asset-type-specific** AND **intelligently filtered**
- Data collection teams see only relevant questions
- Reduced noise and faster data gathering
- Better user experience in collection UI

### Metrics to Track
- **Question Relevance**: % of questions marked as "not applicable" by users
- **Collection Time**: Time to complete data collection per asset
- **Question Volume**: Average questions per asset type (should decrease)
- **Agent Filtering Rate**: % of questions removed by relevance validation

---

## Conclusion

The collection flow question generation has **solid infrastructure that's simply disconnected**. The fix is straightforward:

1. **Immediate** (Phase 1): Connect asset type lookup to existing generators (2-3 hours)
2. **Near-term** (Phase 2): Preserve asset metadata through pipeline (4-6 hours)
3. **Important** (Phase 3): Add agent intelligence for filtering (6-8 hours)

**Total effort for full solution: 12-17 hours**

This follows the codebase principle: **enhance existing implementations rather than replace them**. We have DatabaseQuestionsGenerator, ApplicationQuestionsGenerator, and ServerQuestionsGenerator that work correctly - we just need to route to them properly and add intelligent filtering.

The result will be a more intelligent, asset-aware question generation system that provides value to data collection teams without massive architectural changes.
