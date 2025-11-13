# Phase 2 Day 10 - Manual Testing Guide

## Bulk Import with Canonical Deduplication

### Prerequisites
1. Docker containers running (`docker-compose up -d`)
2. Active Collection flow in database
3. Access to API at `http://localhost:8000`

### Test Scenario 1: Basic Bulk Import with Deduplication

#### Step 1: Create Collection Flow
```bash
# Get or create a collection flow
curl -X POST http://localhost:8000/api/v1/collection/flows/ensure \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>" \
  -H "X-Client-Account-ID: YOUR_CLIENT_ID" \
  -H "X-Engagement-ID: YOUR_ENGAGEMENT_ID"

# Save the flow_id from response
```

#### Step 2: Bulk Import with Duplicate Application Names
```bash
# Import CSV data with duplicate application names
curl -X POST http://localhost:8000/api/v1/collection/bulk-import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>" \
  -H "X-Client-Account-ID: YOUR_CLIENT_ID" \
  -H "X-Engagement-ID: YOUR_ENGAGEMENT_ID" \
  -d '{
    "flow_id": "YOUR_FLOW_ID",
    "asset_type": "servers",
    "csv_data": [
      {
        "application_name": "CRM System",
        "asset_name": "CRM-Server-01",
        "asset_type": "server",
        "technology_stack": "Java, Spring Boot",
        "business_criticality": "high"
      },
      {
        "application_name": "CRM System",
        "asset_name": "CRM-Database-01",
        "asset_type": "database",
        "technology_stack": "PostgreSQL",
        "business_criticality": "high"
      },
      {
        "application_name": "ERP System",
        "asset_name": "ERP-Server-01",
        "asset_type": "server",
        "technology_stack": "SAP",
        "business_criticality": "critical"
      }
    ]
  }'
```

#### Expected Response
```json
{
  "success": true,
  "flow_id": "...",
  "asset_type": "servers",
  "processed_count": 3,
  "created_assets": ["uuid1", "uuid2", "uuid3"],
  "canonical_applications_created": 2,
  "canonical_applications_linked": 1,
  "canonical_applications_failed": 0,
  "enrichment_triggered": false,
  "gap_analysis_triggered": true,
  "errors": [],
  "message": "Successfully imported 3 servers, 2 new canonical apps, linked 1 to existing apps"
}
```

### Test Scenario 2: Verify Database State

#### Check Canonical Applications Created
```sql
-- Connect to database
docker exec -it migration_postgres psql -U postgres -d migration_db

-- Query canonical applications
SELECT
  canonical_name,
  normalized_name,
  usage_count,
  confidence_score,
  is_verified
FROM migration.canonical_applications
WHERE engagement_id = 'YOUR_ENGAGEMENT_ID'
ORDER BY created_at DESC
LIMIT 10;

-- Expected: 2 canonical applications (CRM System, ERP System)
-- CRM System should have usage_count = 2
-- ERP System should have usage_count = 1
```

#### Check Junction Table Entries
```sql
SELECT
  cfa.id,
  cfa.application_name,
  ca.canonical_name,
  cfa.deduplication_method,
  cfa.match_confidence,
  cfa.collection_status
FROM migration.collection_flow_applications cfa
LEFT JOIN migration.canonical_applications ca
  ON cfa.canonical_application_id = ca.id
WHERE cfa.collection_flow_id = 'YOUR_FLOW_ID'
ORDER BY cfa.created_at DESC;

-- Expected: 3 junction entries
-- All should have:
--   - canonical_application_id NOT NULL
--   - deduplication_method = 'bulk_import_auto'
--   - match_confidence > 0.8
-- Two entries should point to same canonical_application_id (CRM System)
```

#### Check Assets Created
```sql
SELECT
  a.id,
  a.asset_name,
  a.asset_type,
  a.application_name,
  a.assessment_readiness,
  a.completeness_score
FROM migration.assets a
WHERE a.engagement_id = 'YOUR_ENGAGEMENT_ID'
  AND a.created_at > NOW() - INTERVAL '10 minutes'
ORDER BY a.created_at DESC;

-- Expected: 3 assets (CRM-Server-01, CRM-Database-01, ERP-Server-01)
```

### Test Scenario 3: Case Variations and Normalization

#### Import with Case Variations
```bash
curl -X POST http://localhost:8000/api/v1/collection/bulk-import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>" \
  -H "X-Client-Account-ID: YOUR_CLIENT_ID" \
  -H "X-Engagement-ID: YOUR_ENGAGEMENT_ID" \
  -d '{
    "flow_id": "YOUR_FLOW_ID",
    "asset_type": "servers",
    "csv_data": [
      {
        "application_name": "crm system",
        "asset_name": "CRM-App-Server-01",
        "asset_type": "server"
      },
      {
        "application_name": "CRM-SYSTEM",
        "asset_name": "CRM-Web-Server-01",
        "asset_type": "server"
      }
    ]
  }'
```

#### Expected Behavior
- Both should link to existing "CRM System" canonical application
- `canonical_applications_created` should be 0
- `canonical_applications_linked` should be 2
- Case normalization should work correctly

### Test Scenario 4: Missing Application Names

#### Import without Application Names
```bash
curl -X POST http://localhost:8000/api/v1/collection/bulk-import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>" \
  -H "X-Client-Account-ID: YOUR_CLIENT_ID" \
  -H "X-Engagement-ID: YOUR_ENGAGEMENT_ID" \
  -d '{
    "flow_id": "YOUR_FLOW_ID",
    "asset_type": "servers",
    "csv_data": [
      {
        "asset_name": "Unknown-Server-01",
        "asset_type": "server",
        "technology_stack": "Unknown"
      }
    ]
  }'
```

#### Expected Behavior
- Should use `asset_name` as fallback for `application_name`
- Canonical application created with name "Unknown-Server-01"
- No errors thrown

### Success Criteria

#### Functional
- ✅ All imported assets have canonical_application_id
- ✅ Duplicate application names link to same canonical application
- ✅ Junction table entries created with proper metadata
- ✅ Response includes canonical deduplication stats
- ✅ Case normalization works correctly

#### Performance
- ✅ Bulk import completes in < 5 seconds for 10 assets
- ✅ No N+1 query issues
- ✅ Atomic transaction ensures data consistency

#### Error Handling
- ✅ Partial failures don't corrupt data
- ✅ Missing application names handled gracefully
- ✅ Failed canonical deduplication doesn't fail entire import

### Troubleshooting

#### Issue: No canonical applications created
**Check**: Verify imports in `collection_bulk_import.py` line 88-91
```python
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
```

#### Issue: Junction table entries missing
**Check**: Database transaction committed successfully
```sql
SELECT COUNT(*) FROM migration.collection_flow_applications
WHERE collection_flow_id = 'YOUR_FLOW_ID';
```

#### Issue: Duplicate canonical applications created
**Check**: Name normalization and hashing working
```sql
SELECT canonical_name, normalized_name, name_hash, usage_count
FROM migration.canonical_applications
WHERE engagement_id = 'YOUR_ENGAGEMENT_ID';
```

### Rollback Procedure

If issues arise, rollback changes:
```bash
# Revert code changes
git checkout main -- backend/app/api/v1/endpoints/collection_bulk_import.py

# Clear test data from database
docker exec migration_postgres psql -U postgres -d migration_db -c "
  DELETE FROM migration.collection_flow_applications
  WHERE deduplication_method = 'bulk_import_auto'
    AND created_at > NOW() - INTERVAL '1 hour';
"
```
