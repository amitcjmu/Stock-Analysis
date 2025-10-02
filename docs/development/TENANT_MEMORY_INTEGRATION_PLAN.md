# TenantMemoryManager Integration Plan for All Agents

**Status**: Planned (Not Yet Implemented)
**Related**: ADR-024, PR #487 (Phase 1: Memory Disablement)
**Created**: October 2, 2025

## Executive Summary

**Phase 1 (Current PR)**: Successfully disabled CrewAI's built-in memory system across all 30+ files to eliminate 422 encoding errors on Railway.

**Phase 2 (Future PRs)**: Need to integrate TenantMemoryManager for 13 agent files to enable enterprise-grade learning with multi-tenant isolation.

---

## Current State (After Phase 1)

### ✅ Completed - Memory Disablement
- All agents have `memory=False` per ADR-024
- Eliminates 422 encoding_format errors in production
- No OpenAI embedding API calls
- All tests passing

### ❌ Not Yet Done - TenantMemoryManager Integration
**0 out of 13 agents** have proper TenantMemoryManager integration for learning.

**Exception**: `field_mapping_crew_fast.py` has FULL integration (reference implementation).

---

## Agent Integration Audit

### Priority 1 - CRITICAL (Highest Learning Value)

#### 1. modernization_agent.py
- **Current**: Uses OLD `ThreeTierMemoryManager` (needs replacement)
- **Pattern Type**: `modernization_strategy`
- **Learning Data**: Cloud readiness scores, modernization strategies, technology assessments
- **Effort**: Medium (replace existing memory manager)

#### 2. business_value_agent.py
- **Current**: Uses OLD `ThreeTierMemoryManager`
- **Pattern Type**: `business_value_assessment`
- **Learning Data**: Business impact scores, value assessments, ROI predictions
- **Effort**: Medium

#### 3. risk_assessment_agent.py
- **Current**: Uses OLD `ThreeTierMemoryManager`
- **Pattern Type**: `risk_assessment`
- **Learning Data**: Security risks, compliance issues, mitigation strategies
- **Effort**: Medium

#### 4. gap_prioritization_agent.py
- **Current**: No memory integration
- **Pattern Type**: `gap_prioritization`
- **Learning Data**: Gap criticality rankings, collection priorities, completion strategies
- **Effort**: High (greenfield integration)

### Priority 2 - HIGH

#### 5. critical_attribute_assessor.py
- **Pattern Type**: `attribute_assessment`
- **Learning Data**: Attribute importance scores, 6R framework decisions

#### 6. collection_orchestrator_agent.py
- **Pattern Type**: `collection_strategy`
- **Learning Data**: Collection workflows, adapter selection, optimization patterns

#### 7. tier_recommendation_agent.py
- **Pattern Type**: `tier_recommendation`
- **Learning Data**: Automation tier selections, manual/automated decisions

### Priority 3 - MEDIUM

#### 8. asset_inventory_agent.py
- **Pattern Type**: `asset_classification`
- **Learning Data**: Asset categorization, technology stack patterns

#### 9. data_validation_agent.py
- **Pattern Type**: `data_validation`
- **Learning Data**: Validation rules, data quality patterns

#### 10. questionnaire_dynamics_agent.py
- **Pattern Type**: `questionnaire_generation`
- **Learning Data**: Effective question patterns, form structures

### Priority 4 - LOW (Less Critical)

#### 11. credential_validation_agent.py
- **Pattern Type**: `credential_validation`

#### 12. data_cleansing_agent.py
- **Pattern Type**: `data_cleansing`

#### 13. progress_tracking_agent.py
- **Pattern Type**: `progress_monitoring`

---

## Integration Pattern (Reference Implementation)

See: `/app/services/crewai_flows/crews/field_mapping_crew_fast.py` (lines 55-177)

```python
async def agent_execution_with_memory(
    crewai_service,
    client_account_id: int,
    engagement_id: int,
    db: AsyncSession,
    agent_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Standard pattern for agent execution with TenantMemoryManager.

    This pattern should be applied to ALL agents that need learning.
    """

    # Step 1: Initialize TenantMemoryManager
    memory_manager = TenantMemoryManager(
        crewai_service=crewai_service,
        database_session=db
    )

    # Step 2: Retrieve historical patterns BEFORE execution
    historical_patterns = await memory_manager.retrieve_similar_patterns(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        pattern_type="agent_specific_pattern_type",  # e.g., "modernization_strategy"
        query_context={"key": "value"},  # Agent-specific context
        limit=10
    )

    # Step 3: Provide patterns to agent via task context
    task_context = {
        "input_data": agent_context,
        "historical_patterns": historical_patterns,
        "learning_guidance": "Use historical patterns to inform your analysis"
    }

    # Step 4: Execute agent/crew (with memory=False)
    agent = create_agent(
        role="Agent Role",
        goal="Agent Goal",
        backstory="Agent Backstory",
        memory=False,  # Per ADR-024
        # ... other config
    )

    crew = create_crew(
        agents=[agent],
        tasks=[task],
        memory=False,  # Per ADR-024
    )

    result = await crew.kickoff_async()

    # Step 5: Store learned patterns AFTER successful execution
    if result.get("status") == "success":
        pattern_id = await memory_manager.store_learning(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            scope=LearningScope.ENGAGEMENT,  # or ACCOUNT/GLOBAL
            pattern_type="agent_specific_pattern_type",
            pattern_data={
                "name": f"pattern_name_{timestamp}",
                "key_finding_1": result.get("finding_1"),
                "key_finding_2": result.get("finding_2"),
                "confidence": result.get("confidence_score"),
                # ... other learnings
            }
        )
        logger.info(f"✅ Stored pattern {pattern_id} for future learning")

    return result
```

---

## Implementation Steps Per Agent

For each agent in the priority list:

### Step 1: Update Imports
```python
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope,
)
```

### Step 2: Add Database Session Parameter
Ensure agent execution methods accept `db: AsyncSession` parameter.

### Step 3: Add Pattern Retrieval
Before crew execution, retrieve relevant historical patterns.

### Step 4: Modify Agent Context
Pass historical patterns to agent via task description or tool context.

### Step 5: Add Pattern Storage
After successful execution, store discovered patterns.

### Step 6: Test Integration
- Verify patterns are stored correctly
- Verify patterns are retrieved on subsequent runs
- Verify multi-tenant isolation works

---

## Required Database Schema (Already Exists)

TenantMemoryManager uses existing tables:
- `migration.agent_discovered_patterns` - Pattern storage
- Uses pgvector for similarity search
- Multi-tenant scoping via client_account_id + engagement_id

**No schema changes required** - just code integration.

---

## Testing Strategy

### Unit Tests
- Test pattern storage with valid data
- Test pattern retrieval with various query contexts
- Test multi-tenant isolation (no cross-tenant leakage)

### Integration Tests
- Test full agent execution with pattern retrieval
- Test pattern storage after execution
- Test pattern reuse on subsequent executions

### E2E Tests
- Verify agents learn from previous executions
- Verify pattern quality improves over time
- Verify no performance degradation

---

## Effort Estimates

| Priority | Agents | Effort Per Agent | Total Effort |
|----------|--------|-----------------|--------------|
| P1 (Critical) | 4 | 4-6 hours | 16-24 hours |
| P2 (High) | 3 | 3-4 hours | 9-12 hours |
| P3 (Medium) | 3 | 2-3 hours | 6-9 hours |
| P4 (Low) | 3 | 2-3 hours | 6-9 hours |
| **TOTAL** | **13** | **2.7 avg** | **37-54 hours** |

**Recommended Approach**: Integrate in 3 sprints:
- **Sprint 1**: Priority 1 agents (4 agents, 16-24 hours)
- **Sprint 2**: Priority 2 agents (3 agents, 9-12 hours)
- **Sprint 3**: Priority 3+4 agents (6 agents, 12-18 hours)

---

## Success Criteria

For each integrated agent:
- ✅ Has TenantMemoryManager import
- ✅ Calls `retrieve_similar_patterns()` before execution
- ✅ Calls `store_learning()` after successful execution
- ✅ Uses appropriate pattern_type for agent domain
- ✅ Includes multi-tenant scoping (client_account_id, engagement_id)
- ✅ Passes all integration tests
- ✅ No performance degradation
- ✅ Documented in agent docstring

---

## Related Documentation

- **ADR-024**: `/docs/adr/024-tenant-memory-manager-architecture.md`
- **Reference Implementation**: `/app/services/crewai_flows/crews/field_mapping_crew_fast.py`
- **TenantMemoryManager**: `/app/services/crewai_flows/memory/tenant_memory_manager/`
- **Serena Memory**: `/.serena/memories/adr024_crewai_memory_disabled_2025_10_02.md`

---

## Next Actions

1. **Complete Phase 1 PR** (Current PR) - Disable CrewAI memory, fix production
2. **Create Phase 2 Issues** - One GitHub issue per priority level
3. **Schedule Integration Sprints** - Allocate dev time across 3 sprints
4. **Start with Priority 1** - Highest value, immediate impact

---

**Status**: This plan is APPROVED and ready for implementation after Phase 1 merge.
**Last Updated**: October 2, 2025
**Owner**: Development Team
