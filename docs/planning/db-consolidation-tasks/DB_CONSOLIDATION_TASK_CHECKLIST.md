# Database Consolidation Task Checklist

## Pre-Implementation Setup
- [ ] Review `docs/planning/FINAL-DATABASE-CONSOLIDATION-PLAN.md`
- [ ] Ensure Docker environment is running
- [ ] Create feature branch: `feature/db-consolidation`
- [ ] Backup current development database

## Day 1: Schema Migration (8 tasks) ✅

### Morning (4 hours)
- [x] **Task 1.1.1**: Create new Alembic migration file `001_consolidated_schema.py`
- [x] **Task 1.1.2**: Define all enum types (asset_type, flow_status, import_status)
- [x] **Task 1.1.3**: Create core multi-tenant tables (client_accounts, engagements, users)
- [x] **Task 1.1.4**: Create master orchestration table (crewai_flow_state_extensions)

### Afternoon (4 hours)
- [x] **Task 1.1.5**: Create consolidated discovery tables with new field names
- [x] **Task 1.1.6**: Create assets table with ALL fields preserved (except is_mock)
- [x] **Task 1.2.1**: Write schema validation script
- [x] **Task 1.3.1**: Create test data seeding script

### Validation
- [ ] Run migration on test database successfully
- [ ] Validation script confirms no V3 tables
- [ ] Test data seeds without errors

## Day 2: Model Updates (12 tasks) ✅

### Morning (4 hours)
- [x] **Task 2.1.1**: Delete entire `backend/app/models/v3/` directory
- [x] **Task 2.2.1**: Update DataImport model (field renames, remove is_mock)
- [x] **Task 2.2.2**: Update DiscoveryFlow model (add JSON fields, keep booleans)
- [x] **Task 2.2.3**: Update ImportFieldMapping model (simplify structure)
- [x] **Task 2.2.4**: Update RawImportRecord model (minimal fields)
- [x] **Task 2.2.5**: Update Asset model (preserve ALL fields except is_mock)

### Afternoon (4 hours)
- [x] **Task 2.3.1**: Delete workflow_state.py
- [x] **Task 2.3.2**: Delete discovery_asset.py  
- [x] **Task 2.3.3**: Delete mapping_learning_pattern.py
- [x] **Task 2.3.4**: Delete remaining deprecated models
- [x] **Task 2.4.1**: Update models/__init__.py registry
- [ ] **Task 2.4.2**: Run model unit tests and fix any issues

### Validation
- [ ] All model imports work correctly
- [ ] No V3 model references remain
- [ ] Model unit tests pass

## Day 3: Repository & Service Updates (10 tasks)

### Morning (4 hours)
- [ ] **Task 3.1.1**: Update V3 repositories to use consolidated table names
- [ ] **Task 3.2.1**: Update V3 DataImportRepository (handle field renames)
- [ ] **Task 3.2.2**: Update V3 DiscoveryFlowRepository (hybrid state management)
- [ ] **Task 3.2.3**: Update V3 FieldMappingRepository (simplified operations)
- [ ] **Task 3.2.4**: Update V3 AssetRepository (preserve all operations)

### Afternoon (4 hours)
- [ ] **Task 3.3.1**: Update V3 DataImportService
- [ ] **Task 3.3.2**: Update V3 DiscoveryFlowService  
- [ ] **Task 3.3.3**: Update remaining V3 services
- [ ] **Task 3.3.4**: Update import statements to use consolidated models
- [ ] **Task 3.3.5**: Update context-aware base classes

### Validation
- [ ] All repository tests pass
- [ ] Service integration tests pass
- [ ] No V3 code references remain

## Day 4: API & Frontend Updates (10 tasks)

### Morning (4 hours)
- [ ] **Task 4.1.1**: Update V3 data import API endpoints
- [ ] **Task 4.1.2**: Update V3 discovery flow API endpoints
- [ ] **Task 4.1.3**: Update V3 field mapping API endpoints
- [ ] **Task 4.1.4**: Add backward compatibility for field names
- [ ] **Task 4.1.5**: Update API error handling

### Afternoon (4 hours)
- [ ] **Task 4.2.1**: Update TypeScript interfaces in api.ts
- [ ] **Task 4.3.1**: Update DataImportForm component
- [ ] **Task 4.3.2**: Update all components using old field names
- [ ] **Task 4.4.1**: Create API migration guide
- [ ] **Task 4.4.2**: Update API documentation

### Validation
- [ ] API tests pass with new field names
- [ ] Frontend builds without errors
- [ ] E2E tests pass

## Day 5: Testing & Staging Deployment (8 tasks)

### Morning (4 hours)
- [ ] **Task 5.1.1**: Write integration tests for DB consolidation
- [ ] **Task 5.1.2**: Write E2E tests for full discovery flow
- [ ] **Task 5.1.3**: Write performance tests
- [ ] **Task 5.1.4**: Run all test suites and fix failures

### Afternoon (4 hours)
- [ ] **Task 5.2.1**: Create deployment script
- [ ] **Task 5.2.2**: Create rollback script
- [ ] **Task 5.3.1**: Deploy to Railway staging
- [ ] **Task 5.3.2**: Run staging validation tests

### Validation
- [ ] All tests pass in CI/CD
- [ ] Staging deployment successful
- [ ] No V3 tables in staging database

## Day 6: Production Deployment (6 tasks)

### Morning (3 hours)
- [ ] **Task 6.1.1**: Backup production databases
- [ ] **Task 6.1.2**: Schedule maintenance window
- [ ] **Task 6.1.3**: Notify stakeholders

### Afternoon (3 hours)
- [ ] **Task 6.2.1**: Deploy to Railway production
- [ ] **Task 6.2.2**: Deploy to AWS production
- [ ] **Task 6.3.1**: Run production validation

### Validation
- [ ] Production deployment successful
- [ ] All health checks passing
- [ ] No performance degradation
- [ ] No V3 tables in production

## Post-Implementation (4 tasks)
- [ ] Monitor error rates for 24 hours
- [ ] Document any issues encountered
- [ ] Create post-mortem if needed
- [ ] Close PR and merge to main

## Emergency Contacts
- Database Admin: [Contact Info]
- DevOps Lead: [Contact Info]
- Product Owner: [Contact Info]

## Rollback Procedure
1. Stop all application instances
2. Run: `./scripts/rollback_db_consolidation.sh production backup_file.sql`
3. Restart application with previous version
4. Notify team of rollback

## Success Metrics
- Zero data loss
- No V3 tables remain
- All tests passing
- Performance maintained
- Zero customer impact

---

**Total Tasks**: 58
**Estimated Time**: 6 days
**Risk Level**: Medium
**Rollback Time**: 30 minutes