# ADR-025: Data Cleansing and Asset Creation Architecture

## Status
Proposed

## Context
The Discovery flow's data processing pipeline has critical gaps between its intended agent-based architecture and actual implementation:

1. **Data Cleansing Phase** attempts to use non-existent `agentic_asset_enrichment` module
2. **Asset Creation** uses raw imported data directly, bypassing cleansing
3. **Database Design** includes `raw_import_records.cleansed_data` column that's never used
4. **Asset Inventory Phase** is implemented as a stub returning fake results

This creates data quality issues where:
- Invalid data types create assets (strings in numeric fields)
- Assets get generic names (asset_1, asset_2) instead of meaningful identifiers
- No business context enrichment occurs
- No data standardization happens

## Decision
Implement a two-phase approach to fix the data pipeline:

### Phase 1: Rule-Based Data Cleansing (Immediate)
Implement deterministic data cleansing without AI agents to restore basic functionality:

```python
# Basic cleansing operations
1. Type conversion (string → number, date parsing)
2. Value standardization (environment names, asset types)
3. Required field validation
4. Format normalization (hostnames, IPs)
5. Store results in raw_import_records.cleansed_data
```

### Phase 2: Agent-Based Enrichment (Future)
Add CrewAI agent intelligence as an enhancement layer:

```python
# Agent enrichment operations
1. Business context inference
2. Relationship discovery
3. Criticality assessment
4. Migration strategy suggestions
5. Pattern recognition across assets
```

### Data Flow Architecture
```
raw_import_records.raw_data (immutable source)
    ↓
[Data Cleansing Phase]
    → Basic cleansing rules (Phase 1)
    → Agent enrichment (Phase 2)
    ↓
raw_import_records.cleansed_data (working copy)
    ↓
[Asset Inventory Phase]
    → Read from cleansed_data
    → Create assets with ServiceRegistry
    ↓
assets table (final destination)
```

## Consequences

### Positive
- **Immediate Fix**: Restores data quality without waiting for agent implementation
- **Backward Compatible**: Existing data can be reprocessed
- **Progressive Enhancement**: Agent intelligence can be added incrementally
- **Maintainable**: Clear separation between deterministic and AI operations
- **Debuggable**: Rule-based cleansing is predictable and testable

### Negative
- **Two-Phase Development**: Requires implementing cleansing twice
- **Migration Needed**: Existing assets may need reprocessing
- **Partial Intelligence**: Initial implementation lacks AI insights

### Neutral
- **Database Schema**: Continues using existing `cleansed_data` column
- **API Contracts**: No changes to frontend interfaces
- **Performance**: Similar processing time (rules vs. simple agents)

## Implementation Plan

### Week 1: Basic Cleansing
1. **Day 1-2**: Implement rule-based DataCleansingExecutor
   - Remove agentic_asset_enrichment dependency
   - Add type conversion and validation
   - Store in cleansed_data column

2. **Day 3**: Modify asset creation pipeline
   - Read from cleansed_data instead of raw_data
   - Remove inline normalization logic

3. **Day 4**: Implement real AssetInventoryExecutor
   - Replace stub with actual implementation
   - Use CrewAI for asset categorization

4. **Day 5**: Testing and validation
   - Verify data types are correct
   - Confirm asset names are meaningful
   - Test with various CSV formats

### Week 2: Agent Enhancement (Optional)
1. Create `agentic_asset_enrichment` module
2. Implement pattern recognition agents
3. Add business context inference
4. Enable progressive enrichment

## Alternatives Considered

### Alternative 1: Direct Agent Implementation
**Rejected** because:
- Would delay fix by weeks
- Risk of agent failures blocking entire pipeline
- Harder to debug and maintain

### Alternative 2: Separate Cleansed Data Table
**Rejected** because:
- Requires schema migration
- Breaks existing code assumptions
- Adds complexity without clear benefit

### Alternative 3: Keep Using Raw Data
**Rejected** because:
- Perpetuates data quality issues
- Violates architectural principles
- Makes agent addition harder later

## Metrics for Success
- Zero type conversion errors in asset creation
- 100% of assets have meaningful names (not asset_1, asset_2)
- All numeric fields contain valid numbers
- Processing time < 5 seconds for 1000 records
- No data loss during cleansing

## Security Considerations
- Cleansed data must maintain multi-tenant isolation
- No sensitive data exposure in logs
- Validation prevents injection attacks

## References
- `/docs/analysis/data-flow-architecture-gaps.md` - Gap analysis
- `/docs/e2e-flows/01_Discovery/04_Data_Cleansing.md` - Original design
- `ADR-006` - Master Flow Orchestrator pattern
- `ADR-019` - CrewAI DeepInfra integration