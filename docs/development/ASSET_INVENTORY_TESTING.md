# Asset Inventory Redesign - Testing Plan

## Overview

This testing plan ensures the Asset Inventory redesign preserves existing functionality while adding comprehensive assessment readiness capabilities. Each test validates that we build upon rather than replace the existing intelligent classification and 6R readiness work.

## Pre-Implementation Testing (Baseline)

### Test Current Asset Inventory Functionality ✅
Before starting implementation, document existing behavior:

- [ ] **Test existing asset classification**
  - Import sample CMDB data
  - Verify intelligent asset type classification works (Applications, Servers, Databases, Devices)
  - Confirm device breakdown widget displays properly
  - Test 6R readiness assessment for different asset types

- [ ] **Test existing UI functionality**
  - Verify asset filtering by type works
  - Check 6R readiness and complexity badges display
  - Confirm device breakdown statistics are accurate
  - Test existing CrewAI integration for classification

- [ ] **Document baseline performance**
  - Record asset processing time for sample dataset
  - Note current memory usage during asset analysis
  - Document current API response times

## Sprint 1 Testing: Database Infrastructure

### Database Migration Tests

#### Test 1.1: Schema Migration Validation
```bash
# Run migration in test environment
docker exec -it migration_backend alembic upgrade head

# Verify new tables created
docker exec -it migration_db psql -U user -d migration_db -c "\dt" | grep asset
```

**Expected Results:**
- [ ] `asset_inventory` table created with all 20+ migration fields
- [ ] `asset_dependencies` table created with proper foreign keys
- [ ] `workflow_progress` table created with phase tracking
- [ ] All existing asset data preserved

#### Test 1.2: Data Migration Preservation
```python
# Test script: tests/backend/migration/test_data_preservation.py
def test_existing_data_preserved():
    # Before migration: Record existing asset data
    # After migration: Verify all data preserved
    # Check intelligent_asset_type → asset_type mapping
    # Verify sixr_ready → assessment_readiness mapping
    # Confirm migration_complexity preserved
```

**Expected Results:**
- [ ] All existing assets migrated to new schema
- [ ] Asset classification preserved (Applications/Servers/Databases/Devices)
- [ ] 6R readiness status properly mapped
- [ ] Migration complexity data preserved
- [ ] No data loss during migration

### Model Integration Tests

#### Test 1.3: Repository Pattern Validation
```python
# Test script: tests/backend/repositories/test_asset_inventory_repository.py
def test_asset_inventory_repository():
    # Test ContextAwareRepository pattern
    # Verify multi-tenant data scoping
    # Test existing query patterns work
    # Validate new workflow queries
```

**Expected Results:**
- [ ] ContextAwareRepository pattern working
- [ ] Multi-tenant data scoping functional
- [ ] Existing asset queries return correct results
- [ ] New workflow status queries working

## Sprint 2 Testing: Workflow Integration

### Workflow API Tests

#### Test 2.1: Workflow Status Initialization
```python
# Test script: tests/backend/services/test_workflow_initialization.py
def test_workflow_status_initialization():
    # Import sample CMDB data
    # Initialize workflow status based on data completeness
    # Verify existing 6R readiness integrated with workflow status
    # Test mapping status based on field completeness
```

**Expected Results:**
- [ ] Assets with complete data → discovery_status = 'completed'
- [ ] Assets with mapping completed → mapping_status = 'completed' 
- [ ] Assets with 6R readiness 'Ready' → appropriate workflow advancement
- [ ] Assessment readiness calculated correctly

#### Test 2.2: Workflow Advancement Logic
```bash
# Test workflow advancement through API
curl -X POST localhost:8000/api/v1/discovery/assets/{id}/workflow/advance \
  -H "Content-Type: application/json" \
  -d '{"phase": "mapping", "status": "completed"}'
```

**Expected Results:**
- [ ] Workflow advancement updates asset status
- [ ] Assessment readiness recalculated
- [ ] Workflow progress percentages updated
- [ ] Existing functionality preserved

### Integration with Existing Workflow Tests

#### Test 2.3: Data Import Integration
```python
# Test script: tests/backend/integration/test_data_import_workflow.py
def test_data_import_workflow_integration():
    # Import CMDB data using existing import service
    # Verify workflow status initialized
    # Check existing classification logic preserved
    # Confirm asset processing pipeline working
```

**Expected Results:**
- [ ] CMDB import populates new AssetInventory model
- [ ] Existing asset classification logic functional
- [ ] Workflow status properly initialized
- [ ] 6R readiness assessment preserved

## Sprint 3 Testing: Analysis Service Integration

### Comprehensive Analysis Tests

#### Test 3.1: Analysis API Functionality
```bash
# Test comprehensive analysis endpoint
curl -X GET localhost:8000/api/v1/discovery/assets/comprehensive-analysis
```

**Expected Response Structure:**
```json
{
  "status": "success",
  "total_assets": 150,
  "assessment_ready": {
    "ready": true,
    "overall_score": 85.5,
    "criteria": {
      "mapping_completion": {"current": 88.0, "required": 80, "met": true},
      "cleanup_completion": {"current": 72.0, "required": 70, "met": true},
      "data_quality": {"current": 76.0, "required": 70, "met": true}
    }
  },
  "recommendations": [...],
  "ai_insights": {...}
}
```

**Expected Results:**
- [ ] Analysis integrates existing asset classification
- [ ] 6R readiness data included in analysis
- [ ] Workflow progress calculated correctly
- [ ] Assessment readiness criteria working
- [ ] AI insights enhanced with existing intelligence

#### Test 3.2: Performance Validation
```python
# Test script: tests/backend/performance/test_analysis_performance.py
def test_comprehensive_analysis_performance():
    # Test with 100, 500, 1000 assets
    # Measure response time and memory usage
    # Verify acceptable performance thresholds
    # Test concurrent analysis requests
```

**Expected Results:**
- [ ] Analysis completes within 5 seconds for 500 assets
- [ ] Memory usage remains under 512MB
- [ ] Concurrent requests handled properly
- [ ] No performance degradation vs existing system

## Sprint 4 Testing: Dashboard Enhancement

### Dashboard Integration Tests

#### Test 4.1: UI Functionality Preservation
```typescript
// Test script: tests/frontend/components/AssetInventoryRedesigned.test.tsx
describe('AssetInventoryRedesigned', () => {
  it('preserves existing device breakdown functionality', () => {
    // Render component with sample data
    // Verify device breakdown widget displays
    // Check asset type filtering works
    // Confirm existing badges and indicators present
  });
});
```

**Expected Results:**
- [ ] All existing UI functionality preserved
- [ ] Device breakdown widget functional
- [ ] Asset type filtering working
- [ ] 6R readiness and complexity badges display
- [ ] New assessment readiness banner appears

#### Test 4.2: Assessment Readiness Display
```typescript
// Test assessment readiness banner
describe('Assessment Readiness Banner', () => {
  it('displays correct readiness status', () => {
    // Test with ready assets (80%+ mapping, 70%+ cleanup, 70%+ quality)
    // Test with not-ready assets
    // Verify criteria display correctly
    // Check next steps recommendations
  });
});
```

**Expected Results:**
- [ ] Banner shows "Ready" when criteria met
- [ ] Banner shows "Prepare" when criteria not met
- [ ] Criteria progress bars accurate
- [ ] Next steps provide actionable guidance

### End-to-End Dashboard Tests

#### Test 4.3: Complete User Workflow
```bash
# Manual testing checklist
1. Navigate to Asset Inventory page
2. Verify assessment readiness banner displays
3. Check workflow progress section shows accurate percentages
4. Test asset filtering and search
5. Verify device breakdown statistics
6. Check data quality analysis display
7. Review AI recommendations
8. Test refresh functionality
```

**Expected Results:**
- [ ] Seamless transition from existing Asset Inventory
- [ ] All data displays correctly
- [ ] User can understand assessment readiness status
- [ ] Workflow guidance is clear and actionable

## Integration Testing

### End-to-End Workflow Tests

#### Test E2E1: Complete Asset Assessment Workflow
```python
# Test script: tests/backend/integration/test_complete_workflow.py
def test_complete_assessment_workflow():
    # 1. Import CMDB data
    # 2. Verify asset classification and workflow initialization
    # 3. Complete attribute mapping simulation
    # 4. Perform data cleanup simulation
    # 5. Check assessment readiness achieved
    # 6. Verify 6R analysis can proceed
```

**Expected Results:**
- [ ] Assets progress through discovery → mapping → cleanup → assessment phases
- [ ] Assessment readiness criteria properly calculated
- [ ] 6R analysis can proceed with assessment-ready assets
- [ ] Existing functionality preserved throughout

#### Test E2E2: AI Learning Integration
```python
# Test script: tests/backend/integration/test_ai_learning.py
def test_ai_learning_integration():
    # Import CMDB data with existing field mappings
    # Verify field mapping intelligence preserved
    # Test AI analysis with enhanced capabilities
    # Check learning from existing classification patterns
```

**Expected Results:**
- [ ] Existing field mapping intelligence preserved
- [ ] AI analysis enhanced with workflow insights
- [ ] Learning patterns from existing classification work
- [ ] No degradation in AI accuracy

## Performance Testing

### Load Testing

#### Test P1: Asset Inventory Scale Testing
```bash
# Load test with large dataset
python tests/backend/performance/load_test.py --assets 5000 --concurrent 10
```

**Expected Results:**
- [ ] System handles 5000+ assets without performance degradation
- [ ] Concurrent user requests processed efficiently
- [ ] Database queries optimized for scale
- [ ] Memory usage remains stable

#### Test P2: Real-time Analysis Performance
```python
# Test real-time analysis with WebSocket updates
def test_realtime_analysis_performance():
    # Simulate multiple users requesting analysis
    # Test WebSocket performance
    # Verify analysis caching works
    # Check memory cleanup
```

**Expected Results:**
- [ ] Real-time analysis completes within acceptable time
- [ ] WebSocket updates efficient
- [ ] Analysis results cached appropriately
- [ ] No memory leaks detected

## Deployment Testing

### Production Environment Tests

#### Test D1: Railway Deployment Validation
```bash
# Test Railway environment setup
./scripts/test_railway_deployment.sh
```

**Expected Results:**
- [ ] Database migration runs successfully on Railway
- [ ] All API endpoints functional in production
- [ ] Environment variables properly configured
- [ ] Comprehensive analysis API working

#### Test D2: Vercel Frontend Validation
```bash
# Test Vercel deployment
npm run build && npm run test:e2e
```

**Expected Results:**
- [ ] Enhanced dashboard builds without errors
- [ ] All components render correctly in production
- [ ] API integration working with Railway backend
- [ ] Assessment readiness functionality working

## Acceptance Criteria

### Sprint 1 Acceptance
- [ ] ✅ Database migration preserves all existing asset data
- [ ] ✅ Asset classification and 6R readiness functionality preserved
- [ ] ✅ New workflow tracking models functional
- [ ] ✅ No performance degradation vs existing system

### Sprint 2 Acceptance
- [ ] ✅ Workflow status tracking functional
- [ ] ✅ Integration with existing Data Import → Attribute Mapping → Data Cleanup flow
- [ ] ✅ Assessment readiness criteria calculated correctly
- [ ] ✅ Existing 6R readiness preserved and enhanced

### Sprint 3 Acceptance
- [ ] ✅ Comprehensive analysis API provides valuable insights
- [ ] ✅ AI analysis enhanced while preserving existing intelligence
- [ ] ✅ Performance acceptable for production use
- [ ] ✅ Assessment readiness guidance actionable

### Sprint 4 Acceptance
- [ ] ✅ Enhanced dashboard superior to existing Asset Inventory
- [ ] ✅ All existing functionality preserved and accessible
- [ ] ✅ Assessment readiness provides clear guidance
- [ ] ✅ User can navigate discovery through assessment phases

## Test Data Requirements

### Sample Datasets
- [ ] **Basic Dataset**: 50 assets (mix of Applications, Servers, Databases, Devices)
- [ ] **Medium Dataset**: 200 assets with varying completeness levels
- [ ] **Large Dataset**: 1000+ assets for performance testing
- [ ] **Edge Cases**: Assets with missing data, complex dependencies, unusual types

### Test Scenarios
- [ ] **Ready for Assessment**: Assets meeting all criteria (80%+ mapping, 70%+ cleanup, 70%+ quality)
- [ ] **Needs Improvement**: Assets requiring more data or cleanup
- [ ] **Complex Dependencies**: Assets with multiple interconnections
- [ ] **Mixed Environments**: Production, development, test assets

This testing plan ensures we validate both the preservation of existing functionality and the successful implementation of new assessment readiness capabilities. 