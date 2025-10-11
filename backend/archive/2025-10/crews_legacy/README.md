# Archived Legacy Crews

**Archived**: 2025-10-11
**Reason**: Superseded by persistent agent pattern (ADR-015, ADR-024) or service layer

## Files Archived (6 items)

### Legacy Crew Implementations
- `inventory_building_crew_legacy.py` - Superseded by persistent agents via TenantScopedAgentPool
- `manual_collection_crew.py` - Superseded by validation_service.py
- `data_synthesis_crew.py` - No active imports found in dependency analysis
- `field_mapping_crew_fast.py` - Superseded by persistent_field_mapping.py
- `agentic_asset_enrichment_crew.py` - **CORRECTED from GPT5 plan**: No active imports (was incorrectly marked as "widely referenced")
- `optimized_field_mapping_crew/` - **CORRECTED from GPT5 plan**: Only self-referential imports (was incorrectly marked as "heavily referenced")

## Verification

**Dependency Analysis**:
- Run date: 2025-10-10
- Tool: `backend/scripts/analysis/dependency_analyzer.py`
- Results: `/docs/analysis/backend_cleanup/dependency_graphs/SUMMARY.md`
- Finding: 0 orphaned files, but these crews had no external imports

**Manual Verification**:
- Checked `backend/app/services/crewai_flows/handlers/unified_flow_crew_manager.py` - uses persistent agents
- Checked service layer - validation_service.py replaced manual collection crew
- Grep search: No active imports found outside self-references

## Migration Context

These crews were part of the **Crew() → TenantScopedAgentPool migration** (ADR-015):

**Old Pattern** (deprecated):
```python
from crewai import Crew
crew = Crew(agents=[...], tasks=[...], memory=False)
```

**New Pattern** (active):
```python
from app.services.persistent_agents import TenantScopedAgentPool
agent = await TenantScopedAgentPool.get_agent(context, agent_type, service_registry)
result = await agent.process(input_data)
```

## Related Documentation

- `/docs/adr/015-persistent-multi-tenant-agent-architecture.md` - Persistent agent architecture
- `/docs/adr/024-tenant-memory-manager-architecture.md` - TenantMemoryManager (replaces CrewAI memory)
- `/docs/analysis/backend_cleanup/FINAL-PARALLEL-EXECUTION-PLAN.md` - Full cleanup plan (Task A2)
- `/docs/analysis/backend_cleanup/dependency_graphs/coupling_analysis.md` - Circular dependency analysis

## Restoration

If restoration is needed:
```bash
# Copy files back to original locations
cp archive/2025-10/crews_legacy/inventory_building_crew_legacy.py app/services/crewai_flows/crews/
cp archive/2025-10/crews_legacy/manual_collection_crew.py app/services/crewai_flows/crews/collection/
# etc.
```

**Warning**: Restoration requires re-enabling direct Crew() instantiation, which violates ADR-015 and ADR-024.
