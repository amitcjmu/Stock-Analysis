# Collection Flow Validation Checklist

## Overview
This document defines the comprehensive validation requirements for the Collection Flow, ensuring data integrity across all related tables and proper flow progression.

## Pre-Collection Validation

### 1. Application Selection
- [ ] **MUST** have at least one application selected
- [ ] Each selected application **MUST** have:
  - Valid application name
  - Associated asset ID from `assets` table
  - Status in `assets` table must be 'active' or 'discovered'

### 2. Asset Linkage Verification
```sql
-- Verify all selected apps have asset records
SELECT a.id, a.asset_name, a.asset_type, a.discovery_status
FROM migration.assets a
WHERE a.id IN (selected_application_ids)
  AND a.client_account_id = :client_account_id
  AND a.engagement_id = :engagement_id;
```

## During Collection Validation

### 3. Gap Analysis Population
- [ ] `collection_gaps` table **MUST** be populated with:
  - Gap identification for each selected application
  - Critical vs optional gap classification
  - Field mapping requirements
  - Data quality scores

### 4. Collection Tables Population
Required tables that **MUST** have entries:
- [ ] `collection_flows` - Main flow record with status tracking
- [ ] `collection_flow_applications` - Links flow to applications
- [ ] `collection_flow_gaps` - Identified data gaps
- [ ] `collection_flow_progress` - Progress tracking per application
- [ ] `collection_flow_field_mappings` - Field mapping results

### 5. Data Integrity Checks
```sql
-- Verify collection flow has all required data
SELECT 
  cf.flow_id,
  cf.status,
  cf.progress_percentage,
  COUNT(DISTINCT cfa.asset_id) as app_count,
  COUNT(DISTINCT cfg.id) as gap_count,
  COUNT(DISTINCT cffm.id) as mapping_count
FROM migration.collection_flows cf
LEFT JOIN migration.collection_flow_applications cfa ON cf.flow_id = cfa.collection_flow_id
LEFT JOIN migration.collection_flow_gaps cfg ON cf.flow_id = cfg.collection_flow_id
LEFT JOIN migration.collection_flow_field_mappings cffm ON cf.flow_id = cffm.collection_flow_id
WHERE cf.flow_id = :flow_id
GROUP BY cf.flow_id, cf.status, cf.progress_percentage;
```

## Pre-Assessment Transition Validation

### 6. Readiness Assessment
Before transitioning to assessment, validate:
- [ ] Collection completeness >= 70% (configurable threshold)
- [ ] All critical gaps addressed
- [ ] Data quality score >= 65%
- [ ] Field mappings validated
- [ ] No blocking errors in `collection_flow_errors` table

### 7. Application Readiness
Each application must have:
- [ ] Complete CMDB data (if required)
- [ ] Technical stack identified
- [ ] Dependencies mapped
- [ ] Business criticality assessed
- [ ] Migration complexity calculated

### 8. Master Flow Synchronization
- [ ] Master flow record in `crewai_flow_state_extensions` updated
- [ ] Status synchronized between master and child flows
- [ ] Progress percentage accurate
- [ ] Phase transitions logged

## Assessment Transition Validation

### 9. Assessment Flow Creation
Upon successful transition:
- [ ] `assessment_flows` record created with:
  - Linked collection_flow_id
  - Selected application IDs
  - Initial status = 'initialized'
  - All required columns populated

### 10. Data Transfer Verification
```sql
-- Verify data transferred to assessment
SELECT 
  af.id as assessment_id,
  af.flow_name,
  af.status,
  af.configuration->>'selected_application_ids' as apps,
  cf.flow_id as collection_id,
  cf.status as collection_status
FROM migration.assessment_flows af
JOIN migration.collection_flows cf ON cf.assessment_flow_id = af.id
WHERE af.id = :assessment_flow_id;
```

## Automated Test Script Requirements

### Test Coverage Areas:
1. **Happy Path**: Complete collection → successful assessment transition
2. **Edge Cases**: 
   - No applications selected
   - Partial data collection
   - Failed field mappings
   - Threshold not met
3. **Error Handling**:
   - Database constraint violations
   - Missing required fields
   - Agent execution failures

### Key Assertions:
```python
def validate_collection_flow(flow_id: str) -> ValidationResult:
    """
    Comprehensive validation of collection flow data integrity.
    
    Returns:
        ValidationResult with pass/fail status and detailed findings
    """
    checks = {
        "has_applications": check_applications_selected(flow_id),
        "assets_linked": check_asset_linkage(flow_id),
        "gaps_identified": check_gaps_populated(flow_id),
        "mappings_complete": check_field_mappings(flow_id),
        "readiness_met": check_readiness_threshold(flow_id),
        "master_flow_synced": check_master_flow_sync(flow_id),
        "no_blocking_errors": check_for_errors(flow_id)
    }
    
    return ValidationResult(
        passed=all(checks.values()),
        details=checks,
        ready_for_assessment=calculate_readiness(checks)
    )
```

## Manual QA Checklist

### UI Validation:
- [ ] Collection progress bar reflects actual completion
- [ ] Application cards show correct status
- [ ] Gap analysis summary displays accurately
- [ ] "Start Assessment Phase" button enabled only when ready
- [ ] Error messages are user-friendly and actionable

### Database Validation:
- [ ] No orphaned records in child tables
- [ ] All foreign key constraints satisfied
- [ ] Timestamps (created_at, updated_at) populated
- [ ] JSONB fields have valid structure
- [ ] No NULL values in NOT NULL columns

### Integration Validation:
- [ ] CrewAI agents execute successfully
- [ ] Field mapping produces valid results
- [ ] Persistent agent pool manages resources correctly
- [ ] Memory patches apply without errors
- [ ] API endpoints return correct status codes

## Regression Test Triggers

Run full validation suite when:
1. Any changes to collection flow models
2. Database schema modifications
3. Agent executor updates
4. Field mapping logic changes
5. Assessment transition code updates
6. Master flow orchestration changes

## Success Criteria

Collection flow is considered successful when:
- ✅ All selected applications have complete data
- ✅ Gap analysis identifies < 30% critical gaps
- ✅ Field mappings achieve > 80% accuracy
- ✅ Readiness score exceeds configured threshold
- ✅ Assessment flow created without errors
- ✅ Master flow status = 'completed'
- ✅ No blocking errors in any log

## Monitoring & Alerts

Set up monitoring for:
- Collection flows stuck in 'running' > 1 hour
- Flows with error_count > 5
- Orphaned collection flows (no master flow)
- Failed assessment transitions
- Agent pool resource exhaustion

## Related Documentation
- [Collection Flow Architecture](./collection-flow-architecture.md)
- [Field Mapping Guide](./field-mapping-guide.md)
- [Assessment Transition Process](../03_Assessment/transition-from-collection.md)
- [Master Flow Orchestration](../00_Common/master-flow-orchestration.md)