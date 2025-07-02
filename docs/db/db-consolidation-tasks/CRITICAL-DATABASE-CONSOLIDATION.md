# CRITICAL: Database Consolidation Plan

## Problem Statement
The remediation plan created V3 tables without a migration strategy, resulting in:
- Parallel table systems (original + V3)
- Data split across two systems
- No clear migration path
- Risk of data inconsistency

## Current State Analysis

### Active Production Tables (Original)
- `data_imports` - 23 records (ACTIVE)
- `import_field_mappings` - 232 records (ACTIVE)
- `discovery_flows` - 18 records (ACTIVE)
- `raw_import_records` - 38 records (ACTIVE)

### New V3 Tables (Pilot)
- `v3_data_imports` - 4 records
- `v3_field_mappings` - 10 records
- `v3_discovery_flows` - 4 records
- `v3_raw_import_records` - 0 records

## Immediate Action Required

### Option 1: Migrate to V3 (RECOMMENDED)
**Timeline**: 2-3 days
**Risk**: Low-Medium

1. **Data Migration Script**
   ```sql
   -- Migrate existing data from original to V3 tables
   INSERT INTO v3_data_imports (...)
   SELECT ... FROM data_imports;
   ```

2. **Update All Code References**
   - Change all imports/models to use V3 tables
   - Update all repository classes
   - Modify API endpoints

3. **Deprecate Original Tables**
   - Rename original tables with `_deprecated` suffix
   - Keep for 30 days as backup
   - Then drop

### Option 2: Revert to Original Tables
**Timeline**: 1 day
**Risk**: Low

1. **Drop V3 Tables**
   ```sql
   DROP TABLE v3_field_mappings CASCADE;
   DROP TABLE v3_raw_import_records CASCADE;
   DROP TABLE v3_discovery_flows CASCADE;
   DROP TABLE v3_data_imports CASCADE;
   ```

2. **Update V3 APIs to use Original Tables**
   - Modify V3 service layer to use original models
   - Keep V3 API contracts but use original persistence

### Option 3: Unified Table Design (Long-term Best)
**Timeline**: 4-5 days
**Risk**: Medium

1. **Create New Unified Tables**
   - Combine best of original + V3 designs
   - Single source of truth
   - Proper migration strategy

2. **Implement Dual-Write**
   - Write to both systems during transition
   - Gradual migration

## Recommended Immediate Steps

### Phase 0: Database Consolidation (NEW - URGENT)

#### Step 1: Choose Strategy (Day 1)
- [ ] Decision: Migrate to V3, Revert to Original, or Unified Design
- [ ] Create detailed migration plan
- [ ] Identify all code touchpoints

#### Step 2: Implement Migration (Day 2-3)
- [ ] Create migration scripts
- [ ] Update model references
- [ ] Test data integrity
- [ ] Update API endpoints

#### Step 3: Validate & Cleanup (Day 4)
- [ ] Verify all data migrated correctly
- [ ] Update documentation
- [ ] Remove/deprecate old tables
- [ ] Performance testing

## Code Changes Required

### If Migrating to V3:

1. **Update Model Imports**
   ```python
   # FROM
   from app.models import DataImport, DiscoveryFlow
   
   # TO
   from app.models.v3 import V3DataImport as DataImport
   from app.models.v3 import V3DiscoveryFlow as DiscoveryFlow
   ```

2. **Update Repository Classes**
   ```python
   # Update all repository classes to use V3 models
   class DataImportRepository:
       model = V3DataImport  # Instead of DataImport
   ```

3. **Update API Services**
   - Ensure all services use V3 repositories
   - Maintain API contracts

### If Reverting to Original:

1. **Update V3 Services**
   ```python
   # In v3/data_import_service.py
   from app.models import DataImport  # Use original
   # Remove V3 model imports
   ```

2. **Drop V3 Tables**
   - Run migration to remove V3 tables
   - Clean up V3 model files

## Impact on Phase 2

### Must Complete Before Phase 2:
- Database consolidation prevents further bifurcation
- Clean foundation for CrewAI transformation
- Avoid building on unstable data layer

### Modified Phase 2 Timeline:
- Days 1-4: Database Consolidation
- Days 5-11: Original Phase 2 Week 1
- Days 12-18: Original Phase 2 Week 2

## Risk Mitigation

1. **Backup Everything**
   ```bash
   pg_dump -U postgres -d migration_db > backup_before_consolidation.sql
   ```

2. **Test Migration Script**
   - Run on development first
   - Verify record counts
   - Check foreign key integrity

3. **Rollback Plan**
   - Keep backup for immediate restore
   - Document all changes for reversal

## Decision Matrix

| Factor | Migrate to V3 | Revert to Original | Unified Design |
|--------|--------------|-------------------|----------------|
| Time | 2-3 days | 1 day | 4-5 days |
| Risk | Medium | Low | Medium-High |
| Future-Proof | Good | Poor | Excellent |
| Complexity | Medium | Low | High |
| Team Impact | Medium | Low | High |

## Recommendation

**Migrate to V3** because:
1. V3 APIs already built and frontend expects them
2. Simpler, cleaner design
3. Already has some data
4. Aligns with future architecture

**Action**: Implement Option 1 immediately before proceeding with Phase 2.