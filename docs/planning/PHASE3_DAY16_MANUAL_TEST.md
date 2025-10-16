# Phase 3 Day 16: Enrichment Pipeline Manual Testing Guide

**Date**: October 15, 2025
**Purpose**: Manual testing procedures for AutoEnrichmentPipeline integration
**Prerequisites**: Docker environment running, backend services healthy

---

## Test Scenario 1: Basic Enrichment with Small Dataset

### Objective
Verify enrichment pipeline works end-to-end with 3-5 assets.

### Setup

1. **Start Docker Environment**:
   ```bash
   cd /Users/chocka/CursorProjects/migrate-ui-orchestrator/config/docker
   docker-compose up -d
   ```

2. **Access Backend Container**:
   ```bash
   docker exec -it migration_backend bash
   ```

3. **Create Test Assets in Database**:
   ```sql
   -- Run from Docker container
   docker exec -it migration_postgres psql -U postgres -d migration_db

   -- Set your test client_account_id and engagement_id
   \set client_id '12345678-1234-5678-1234-567812345678'
   \set engagement_id '87654321-4321-8765-4321-876543218765'

   -- Create test assets
   INSERT INTO migration.assets (
       id, client_account_id, engagement_id,
       asset_name, asset_type, technology_stack, operating_system,
       environment, data_sensitivity, business_criticality,
       assessment_readiness, assessment_readiness_score
   ) VALUES
   (
       gen_random_uuid(), :'client_id', :'engagement_id',
       'Test Web Server', 'server', 'Apache Tomcat 9.0', 'Linux Ubuntu 22.04',
       'production', 'high', 'critical',
       'not_ready', 0.3
   ),
   (
       gen_random_uuid(), :'client_id', :'engagement_id',
       'Test Database', 'database', 'PostgreSQL 14', 'Linux',
       'production', 'high', 'critical',
       'not_ready', 0.2
   ),
   (
       gen_random_uuid(), :'client_id', :'engagement_id',
       'Test Application', 'application', 'Java Spring Boot', 'Linux',
       'production', 'medium', 'high',
       'not_ready', 0.4
   );

   -- Capture asset IDs for testing
   SELECT id, asset_name FROM migration.assets
   WHERE client_account_id = :'client_id'
   ORDER BY created_at DESC LIMIT 3;
   ```

### Execution

4. **Run Enrichment via Python**:
   ```python
   # From Docker container (migration_backend)
   docker exec -it migration_backend python

   import asyncio
   from uuid import UUID
   from app.database import get_db
   from app.services.enrichment.auto_enrichment_pipeline import AutoEnrichmentPipeline

   # Set your IDs from SQL output above
   client_account_id = UUID('12345678-1234-5678-1234-567812345678')
   engagement_id = UUID('87654321-4321-8765-4321-876543218765')
   asset_ids = [
       UUID('REPLACE_WITH_ASSET_ID_1'),
       UUID('REPLACE_WITH_ASSET_ID_2'),
       UUID('REPLACE_WITH_ASSET_ID_3')
   ]

   async def run_test():
       async for db in get_db():
           pipeline = AutoEnrichmentPipeline(
               db=db,
               client_account_id=client_account_id,
               engagement_id=engagement_id
           )

           result = await pipeline.trigger_auto_enrichment(asset_ids)
           print("\n=== Enrichment Results ===")
           print(f"Total Assets: {result['total_assets']}")
           print(f"Enrichment Results: {result['enrichment_results']}")
           print(f"Elapsed Time: {result['elapsed_time_seconds']:.2f}s")

           if 'error' in result:
               print(f"ERROR: {result['error']}")

           return result

   # Run the test
   result = asyncio.run(run_test())
   ```

### Verification

5. **Verify custom_attributes Populated**:
   ```sql
   -- Check custom_attributes field
   SELECT
       id, asset_name,
       custom_attributes -> 'compliance_enrichment' as compliance,
       custom_attributes -> 'license_info' as licenses,
       custom_attributes -> 'vulnerability_scan' as vulnerabilities
   FROM migration.assets
   WHERE client_account_id = :'client_id'
   ORDER BY created_at DESC LIMIT 3;
   ```

6. **Verify Assessment Readiness Updated**:
   ```sql
   SELECT
       id, asset_name,
       assessment_readiness,
       assessment_readiness_score,
       completeness_score,
       array_length(assessment_blockers, 1) as blocker_count
   FROM migration.assets
   WHERE client_account_id = :'client_id'
   ORDER BY created_at DESC LIMIT 3;
   ```

### Expected Results

- **Enrichment Execution**:
  - `total_assets` = 3
  - `enrichment_results.compliance_flags` >= 2
  - `enrichment_results.licenses` >= 1
  - `enrichment_results.vulnerabilities` >= 2
  - `enrichment_results.resilience` >= 1
  - `enrichment_results.dependencies` >= 2
  - `enrichment_results.product_links` >= 1
  - `elapsed_time_seconds` < 60 (1 minute for 3 assets)
  - No errors in result

- **Database Verification**:
  - `custom_attributes` JSONB field populated with enrichment data
  - At least 2/3 assets have `compliance_enrichment` data
  - At least 1/3 assets have `license_info` data
  - `assessment_readiness_score` increased from initial values (or recalculated)
  - `assessment_blockers` array populated with missing critical attributes

### Troubleshooting

- **No Enrichment Data**:
  - Check backend logs: `docker logs migration_backend --tail 100`
  - Verify LLM API keys configured: `echo $DEEPINFRA_API_KEY`
  - Check database connection: `docker exec migration_postgres pg_isready`

- **Low Enrichment Counts**:
  - Normal if assets have minimal metadata
  - Agents return low confidence scores for insufficient data
  - Check individual agent logs for specific failures

---

## Test Scenario 2: Performance Test (50 Assets)

### Objective
Verify enrichment pipeline meets performance target (<10 minutes for 50+ assets).

### Setup

1. **Bulk Create 50 Test Assets**:
   ```sql
   -- Run from PostgreSQL container
   docker exec -it migration_postgres psql -U postgres -d migration_db

   \set client_id '12345678-1234-5678-1234-567812345678'
   \set engagement_id '87654321-4321-8765-4321-876543218765'

   -- Generate 50 test assets
   INSERT INTO migration.assets (
       id, client_account_id, engagement_id,
       asset_name, asset_type, technology_stack, operating_system,
       environment, data_sensitivity, business_criticality,
       cpu_cores, memory_gb, storage_gb,
       assessment_readiness, assessment_readiness_score
   )
   SELECT
       gen_random_uuid(),
       :'client_id',
       :'engagement_id',
       'Perf Test Asset ' || i,
       CASE (i % 4)
           WHEN 0 THEN 'server'
           WHEN 1 THEN 'database'
           WHEN 2 THEN 'application'
           WHEN 3 THEN 'network_device'
       END,
       CASE (i % 5)
           WHEN 0 THEN 'Apache Tomcat'
           WHEN 1 THEN 'PostgreSQL'
           WHEN 2 THEN 'Java Spring Boot'
           WHEN 3 THEN 'Cisco IOS'
           WHEN 4 THEN 'Node.js'
       END,
       CASE (i % 2) WHEN 0 THEN 'Linux' ELSE 'Windows' END,
       CASE (i % 3) WHEN 0 THEN 'production' WHEN 1 THEN 'staging' ELSE 'development' END,
       CASE (i % 3) WHEN 0 THEN 'high' WHEN 1 THEN 'medium' ELSE 'low' END,
       CASE (i % 4) WHEN 0 THEN 'critical' WHEN 1 THEN 'high' WHEN 2 THEN 'medium' ELSE 'low' END,
       (i % 8) + 2,
       ((i % 16) * 4 + 8)::numeric,
       ((i % 10) * 100 + 100)::numeric,
       'not_ready',
       0.3 + (i % 5) * 0.1
   FROM generate_series(1, 50) AS i;

   -- Get asset IDs
   SELECT array_agg(id::text) FROM migration.assets
   WHERE client_account_id = :'client_id'
   ORDER BY created_at DESC LIMIT 50;
   ```

### Execution

2. **Run Performance Test**:
   ```python
   # From Docker container
   docker exec -it migration_backend python

   import asyncio
   import time
   from uuid import UUID
   from app.database import get_db
   from app.services.enrichment.auto_enrichment_pipeline import AutoEnrichmentPipeline

   client_account_id = UUID('12345678-1234-5678-1234-567812345678')
   engagement_id = UUID('87654321-4321-8765-4321-876543218765')

   # Get asset IDs from database query above
   asset_ids = [
       # Paste asset IDs from SQL output
       # UUID('...'), UUID('...'), ...
   ]

   async def performance_test():
       async for db in get_db():
           pipeline = AutoEnrichmentPipeline(
               db=db,
               client_account_id=client_account_id,
               engagement_id=engagement_id
           )

           print(f"\n=== Starting Performance Test ===")
           print(f"Asset Count: {len(asset_ids)}")

           start_time = time.time()
           result = await pipeline.trigger_auto_enrichment(asset_ids)
           elapsed = time.time() - start_time

           print(f"\n=== Performance Test Results ===")
           print(f"Total Assets: {result['total_assets']}")
           print(f"Elapsed Time: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
           print(f"\nEnrichment Results:")
           for enrichment_type, count in result['enrichment_results'].items():
               print(f"  - {enrichment_type}: {count} assets")

           # Calculate success rate
           total_enrichments = sum(result['enrichment_results'].values())
           max_possible = len(asset_ids) * 6  # 6 enrichment types
           success_rate = (total_enrichments / max_possible) * 100 if max_possible > 0 else 0

           print(f"\nSuccess Rate: {success_rate:.1f}% ({total_enrichments}/{max_possible} enrichments)")
           print(f"Performance Target: < 600s (10 minutes)")
           print(f"Actual: {elapsed:.2f}s")
           print(f"Status: {'✅ PASS' if elapsed < 600 else '❌ FAIL'}")

           return result

   # Run test
   result = asyncio.run(performance_test())
   ```

### Expected Results

- **Performance**:
  - Execution time < 600 seconds (10 minutes) ✅
  - Ideally < 300 seconds (5 minutes) for 50 assets
  - Success rate > 50% (at least 150/300 total enrichments)

- **Throughput**:
  - ~10 assets/minute or faster
  - Concurrent execution of all 6 enrichment types

- **Resource Usage**:
  - No memory leaks
  - No database connection pool exhaustion
  - Backend container remains responsive

### Troubleshooting

- **Timeout or Performance Issues**:
  - Check LLM API rate limits
  - Verify concurrent execution (not sequential)
  - Monitor database connection pool
  - Check backend CPU/memory usage: `docker stats migration_backend`

---

## Test Scenario 3: Error Handling (Minimal Metadata)

### Objective
Verify enrichment gracefully handles assets with missing/minimal data.

### Setup

1. **Create Minimal Asset**:
   ```sql
   INSERT INTO migration.assets (
       id, client_account_id, engagement_id,
       asset_name, asset_type,
       assessment_readiness, assessment_readiness_score
   ) VALUES (
       gen_random_uuid(),
       :'client_id',
       :'engagement_id',
       'Minimal Test Asset',
       'server',
       'not_ready',
       0.1
   );

   -- Get asset ID
   SELECT id, asset_name FROM migration.assets
   WHERE asset_name = 'Minimal Test Asset';
   ```

### Execution

2. **Run Enrichment**:
   ```python
   # Same Python approach as Scenario 1, but with single minimal asset
   asset_ids = [UUID('MINIMAL_ASSET_ID')]
   ```

### Expected Results

- **Graceful Failure**:
  - Pipeline completes without exception
  - Some enrichments may return 0 count (expected)
  - Low confidence scores in custom_attributes
  - No backend crashes or errors

- **Assessment Readiness**:
  - Still recalculated (even if unchanged)
  - Blockers list populated with missing attributes

---

## Test Scenario 4: LLM Usage Tracking Verification

### Objective
Verify all LLM calls are tracked in `llm_usage_logs` table.

### Execution

1. **Run Any Enrichment Test**:
   - Use Scenario 1 (3 assets)

2. **Check LLM Usage Logs**:
   ```sql
   SELECT
       provider,
       model,
       feature_context,
       input_tokens,
       output_tokens,
       cost,
       created_at
   FROM migration.llm_usage_logs
   WHERE client_account_id = :'client_id'
   ORDER BY created_at DESC
   LIMIT 20;
   ```

### Expected Results

- **LLM Logs Created**:
  - At least 1 log entry per enriched asset
  - Provider = 'deepinfra' or configured provider
  - Model = 'llama-3.1-405b' or configured model
  - Feature context includes 'enrichment_pipeline', 'compliance_analysis', etc.
  - Token counts > 0
  - Cost calculated correctly

- **Frontend Visibility**:
  - Navigate to `/finops/llm-costs` in browser
  - Should see enrichment LLM usage in dashboard

---

## Test Scenario 5: Integration with Frontend (Future)

### Objective
(Once frontend UI is implemented) Verify enrichment data visible in Assessment Overview.

### Steps

1. Navigate to Assessment Flow Overview page
2. Verify application groups displayed with enrichment status
3. Check readiness dashboard shows enrichment progress
4. Confirm blockers UI displays missing critical attributes

### Expected Results

- Assessment Overview shows:
  - Enrichment status summary (compliance, licenses, vulnerabilities, etc.)
  - Readiness scores per asset/application
  - Missing critical attributes with guidance
  - "Collect Missing Data" action button

---

## Cleanup After Testing

```sql
-- Remove test assets
DELETE FROM migration.assets
WHERE client_account_id = :'client_id'
AND asset_name LIKE '%Test%';

-- Verify cleanup
SELECT COUNT(*) FROM migration.assets
WHERE client_account_id = :'client_id';
```

---

## Success Criteria Summary

- ✅ Basic enrichment (3 assets) completes in < 60 seconds
- ✅ Performance test (50 assets) completes in < 10 minutes
- ✅ Success rate > 50% for enrichments
- ✅ custom_attributes populated with enrichment data
- ✅ Assessment readiness recalculated correctly
- ✅ LLM usage tracked in llm_usage_logs table
- ✅ Error handling works without crashes
- ✅ No memory leaks or resource exhaustion

---

**Document Status**: Ready for Manual Testing
**Last Updated**: October 15, 2025
**Next Steps**: Execute test scenarios and document results
