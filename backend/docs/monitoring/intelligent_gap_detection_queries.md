# Intelligent Gap Detection Monitoring Queries

This document provides SQL queries for monitoring the intelligent gap detection and questionnaire generation system (ADR-037).

## Table of Contents
- [Performance Metrics](#performance-metrics)
- [Cost Metrics](#cost-metrics)
- [Quality Metrics](#quality-metrics)
- [Error Analysis](#error-analysis)
- [Gap Scan Analysis](#gap-scan-analysis)
- [Question Generation Analysis](#question-generation-analysis)

---

## Performance Metrics

### Gap Scan Performance (Target: <500ms per asset)

```sql
-- Average gap scan response time (last hour)
SELECT
    AVG(response_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) as p50_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time_ms) as p99_ms,
    MIN(response_time_ms) as min_ms,
    MAX(response_time_ms) as max_ms,
    COUNT(*) as total_scans
FROM migration.llm_usage_logs
WHERE feature_context = 'intelligent_gap_detection'
  AND created_at >= NOW() - INTERVAL '1 hour'
  AND success = true;
```

**Target**: Average <500ms, p95 <800ms

---

### Question Generation Time (Target: <2s per question)

```sql
-- Average question generation response time (last hour)
SELECT
    feature_context,
    AVG(response_time_ms) / 1000.0 as avg_response_time_sec,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY response_time_ms) / 1000.0 as p50_sec,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) / 1000.0 as p95_sec,
    COUNT(*) as total_calls
FROM migration.llm_usage_logs
WHERE feature_context IN ('section_question_generator', 'data_awareness_agent')
  AND created_at >= NOW() - INTERVAL '1 hour'
  AND success = true
GROUP BY feature_context;
```

**Target**:
- `section_question_generator`: <2s average, <3s p95
- `data_awareness_agent`: <5s average (one-time per flow)

---

### End-to-End Flow Performance (Target: <15s for 9 questions)

```sql
-- Total time from gap scan to questions generated (per flow)
SELECT
    flow_id,
    MIN(created_at) as start_time,
    MAX(created_at) as end_time,
    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) as total_duration_seconds,
    COUNT(DISTINCT CASE WHEN feature_context = 'intelligent_gap_detection' THEN id END) as gap_scans,
    COUNT(DISTINCT CASE WHEN feature_context = 'section_question_generator' THEN id END) as question_generations,
    SUM(total_cost) as total_flow_cost
FROM migration.llm_usage_logs
WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
  AND created_at >= NOW() - INTERVAL '6 hours'
  AND success = true
  AND flow_id IS NOT NULL
GROUP BY flow_id
ORDER BY start_time DESC
LIMIT 50;
```

**Target**: <15s total for typical flow (2 assets, 9 questions)

---

## Cost Metrics

### LLM Cost Per Question (Target: <$0.008)

```sql
-- Average cost per question generated
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    AVG(total_cost) as avg_cost_per_question,
    SUM(total_cost) as total_cost,
    COUNT(*) as questions_generated,
    AVG(input_tokens) as avg_input_tokens,
    AVG(output_tokens) as avg_output_tokens
FROM migration.llm_usage_logs
WHERE feature_context = 'section_question_generator'
  AND created_at >= NOW() - INTERVAL '24 hours'
  AND success = true
GROUP BY hour
ORDER BY hour DESC;
```

**Target**: Average <$0.008 per question (65% reduction from $0.017 baseline)

---

### Cost Breakdown by Feature

```sql
-- Total cost by feature context (last 24 hours)
SELECT
    feature_context,
    COUNT(*) as total_calls,
    SUM(total_cost) as total_cost,
    AVG(total_cost) as avg_cost_per_call,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    ROUND((SUM(total_cost) / (SELECT SUM(total_cost) FROM migration.llm_usage_logs
        WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
        AND created_at >= NOW() - INTERVAL '24 hours' AND success = true)) * 100, 2) as cost_percentage
FROM migration.llm_usage_logs
WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
  AND created_at >= NOW() - INTERVAL '24 hours'
  AND success = true
GROUP BY feature_context
ORDER BY total_cost DESC;
```

---

### Cost Savings Calculation

```sql
-- Calculate savings vs baseline ($0.017 per question)
SELECT
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as questions_generated,
    AVG(total_cost) as avg_actual_cost,
    0.017 as baseline_cost,
    (0.017 - AVG(total_cost)) as savings_per_question,
    (0.017 - AVG(total_cost)) * COUNT(*) as total_savings,
    ROUND(((0.017 - AVG(total_cost)) / 0.017) * 100, 1) as savings_percentage
FROM migration.llm_usage_logs
WHERE feature_context = 'section_question_generator'
  AND created_at >= NOW() - INTERVAL '30 days'
  AND success = true
GROUP BY date
ORDER BY date DESC;
```

**Expected**: 65% cost reduction ($0.009 savings per question)

---

## Quality Metrics

### False Gap Detection Rate (Target: 0)

```sql
-- Count of false gaps (data exists elsewhere)
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) FILTER (WHERE is_true_gap = false) as false_gaps,
    COUNT(*) FILTER (WHERE is_true_gap = true) as true_gaps,
    COUNT(*) as total_gaps_detected,
    ROUND(COUNT(*) FILTER (WHERE is_true_gap = false)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as false_gap_percentage
FROM migration.collection_data_gaps
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

**Target**: 0 false gaps (100% accuracy)

**Note**: Requires `collection_data_gaps` table with `is_true_gap` boolean column

---

### Duplicate Question Detection (Target: 0)

```sql
-- Find duplicate questions within same flow
SELECT
    collection_flow_id,
    questions_json->>'question_text' as question_text,
    COUNT(*) as occurrence_count,
    ARRAY_AGG(DISTINCT section_id) as sections,
    ARRAY_AGG(DISTINCT asset_id) as assets
FROM migration.questionnaires
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY collection_flow_id, questions_json->>'question_text'
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;
```

**Target**: 0 duplicates across sections

---

### Gap Detection Accuracy by Data Source

```sql
-- Analyze which data sources prevent false gaps
SELECT
    data_source_type,
    COUNT(*) as gaps_found_in_source,
    AVG(confidence_score) as avg_confidence,
    COUNT(DISTINCT asset_id) as assets_with_data
FROM migration.collection_data_gaps
WHERE created_at >= NOW() - INTERVAL '24 hours'
  AND data_found IS NOT NULL
GROUP BY data_source_type
ORDER BY gaps_found_in_source DESC;
```

**Expected distribution**:
- `custom_attributes`: 30-40%
- `standard_columns`: 25-35%
- `enrichment_data`: 15-20%
- `environment`: 10-15%
- `canonical_applications`: 5-10%
- `related_assets`: 5-10%

---

## Error Analysis

### LLM Call Failures

```sql
-- Analyze failures by feature context
SELECT
    feature_context,
    error_type,
    COUNT(*) as error_count,
    ARRAY_AGG(DISTINCT LEFT(error_message, 100)) as sample_errors,
    MIN(created_at) as first_occurrence,
    MAX(created_at) as last_occurrence
FROM migration.llm_usage_logs
WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
  AND success = false
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY feature_context, error_type
ORDER BY error_count DESC;
```

---

### Success Rate Trend

```sql
-- Success rate by hour
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    feature_context,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE success = true) as successful_calls,
    COUNT(*) FILTER (WHERE success = false) as failed_calls,
    ROUND(COUNT(*) FILTER (WHERE success = true)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as success_rate_percentage
FROM migration.llm_usage_logs
WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
  AND created_at >= NOW() - INTERVAL '48 hours'
GROUP BY hour, feature_context
ORDER BY hour DESC, feature_context;
```

**Target**: >95% success rate

---

## Gap Scan Analysis

### Gap Scan Count Per Flow (Target: 1)

```sql
-- Count gap scans per flow (should be 1 with caching)
SELECT
    flow_id,
    COUNT(*) as scan_count,
    MIN(created_at) as first_scan,
    MAX(created_at) as last_scan,
    EXTRACT(EPOCH FROM (MAX(created_at) - MIN(created_at))) as time_between_scans_sec
FROM migration.llm_usage_logs
WHERE feature_context = 'intelligent_gap_detection'
  AND created_at >= NOW() - INTERVAL '24 hours'
  AND success = true
  AND flow_id IS NOT NULL
GROUP BY flow_id
HAVING COUNT(*) > 1  -- Show only flows with multiple scans (potential caching issue)
ORDER BY scan_count DESC;
```

**Target**: 1 scan per flow (cached for 5 minutes)

---

### Gap Scan Cache Efficiency

```sql
-- Analyze Redis cache hit rate (inferred from scan count)
WITH flow_scans AS (
    SELECT
        flow_id,
        COUNT(*) as scan_count,
        CASE WHEN COUNT(*) = 1 THEN 1 ELSE 0 END as cache_hit
    FROM migration.llm_usage_logs
    WHERE feature_context = 'intelligent_gap_detection'
      AND created_at >= NOW() - INTERVAL '24 hours'
      AND success = true
      AND flow_id IS NOT NULL
    GROUP BY flow_id
)
SELECT
    COUNT(*) as total_flows,
    SUM(cache_hit) as flows_with_single_scan,
    COUNT(*) - SUM(cache_hit) as flows_with_multiple_scans,
    ROUND(SUM(cache_hit)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as cache_efficiency_percentage
FROM flow_scans;
```

**Target**: >90% cache efficiency (single scan per flow)

---

### Gaps Detected by Priority

```sql
-- Distribution of gaps by priority
SELECT
    priority,
    COUNT(*) as gap_count,
    COUNT(DISTINCT asset_id) as assets_with_gaps,
    AVG(confidence_score) as avg_confidence,
    ARRAY_AGG(DISTINCT field_name ORDER BY field_name) FILTER (WHERE field_name IS NOT NULL) as common_fields
FROM migration.collection_data_gaps
WHERE created_at >= NOW() - INTERVAL '24 hours'
  AND is_true_gap = true
GROUP BY priority
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
    END;
```

---

## Question Generation Analysis

### Questions Generated Per Asset

```sql
-- Average questions generated per asset
SELECT
    DATE_TRUNC('day', created_at) as date,
    COUNT(DISTINCT asset_id) as unique_assets,
    COUNT(*) as total_questions,
    ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT asset_id), 0), 1) as avg_questions_per_asset
FROM migration.questionnaires
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY date
ORDER BY date DESC;
```

**Expected**: 3-9 questions per asset (adaptive based on data quality)

---

### Questions by Section Distribution

```sql
-- Questions generated by section
SELECT
    section_id,
    COUNT(*) as question_count,
    COUNT(DISTINCT asset_id) as assets_covered,
    ROUND(AVG((questions_json->>'priority')::int), 1) as avg_priority,
    ARRAY_AGG(DISTINCT questions_json->>'field_type') as field_types_used
FROM migration.questionnaires
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY section_id
ORDER BY question_count DESC;
```

---

### Data Awareness Agent Performance

```sql
-- Data awareness agent execution metrics (one-time per flow)
SELECT
    flow_id,
    created_at,
    response_time_ms / 1000.0 as response_time_sec,
    input_tokens,
    output_tokens,
    total_cost,
    success
FROM migration.llm_usage_logs
WHERE feature_context = 'data_awareness_agent'
  AND created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

**Expected**:
- Execution count: 1 per flow
- Response time: 3-5 seconds
- Input tokens: 5,000-8,000 (comprehensive asset data)
- Cost: $0.015-$0.025 per flow

---

## Performance Comparison Queries

### Before vs After ADR-037 Implementation

```sql
-- Compare performance before and after intelligent gap detection
-- Assumes deployment timestamp is stored in a table or known
WITH deployment_date AS (
    SELECT '2025-11-24'::timestamp as deployed_at  -- Replace with actual deployment date
),
before_metrics AS (
    SELECT
        AVG(response_time_ms) / 1000.0 as avg_time_sec,
        AVG(total_cost) as avg_cost,
        AVG(input_tokens) as avg_input_tokens,
        COUNT(*) as total_calls
    FROM migration.llm_usage_logs, deployment_date
    WHERE feature_context IN ('questionnaire_generation', 'legacy_gap_analysis')  -- Old feature contexts
      AND created_at < deployed_at
      AND created_at >= deployed_at - INTERVAL '7 days'
      AND success = true
),
after_metrics AS (
    SELECT
        AVG(response_time_ms) / 1000.0 as avg_time_sec,
        AVG(total_cost) as avg_cost,
        AVG(input_tokens) as avg_input_tokens,
        COUNT(*) as total_calls
    FROM migration.llm_usage_logs, deployment_date
    WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
      AND created_at >= deployed_at
      AND success = true
)
SELECT
    'Before ADR-037' as period,
    before_metrics.avg_time_sec,
    before_metrics.avg_cost,
    before_metrics.avg_input_tokens,
    before_metrics.total_calls
FROM before_metrics
UNION ALL
SELECT
    'After ADR-037' as period,
    after_metrics.avg_time_sec,
    after_metrics.avg_cost,
    after_metrics.avg_input_tokens,
    after_metrics.total_calls
FROM after_metrics;
```

**Expected improvements**:
- Time: 76% faster (8.3s → 2s per question)
- Cost: 65% reduction ($0.017 → $0.006 per question)
- Tokens: 66% reduction (10,405 → 3,500 input tokens)

---

## Usage Notes

### Database Connection

All queries assume connection to the `migration_db` PostgreSQL database:

```bash
# Via Docker
docker exec -it migration_postgres psql -U postgres -d migration_db

# Via psql client
psql -h localhost -p 5433 -U postgres -d migration_db
```

### Query Performance

For optimal performance:
- Add indexes on `feature_context`, `created_at`, `flow_id` if not already present
- Use time range filters (e.g., `>= NOW() - INTERVAL '24 hours'`)
- Consider materialized views for frequently run aggregations

### Scheduled Reporting

These queries can be scheduled using:
- **Grafana**: Configure PostgreSQL datasource and create automated reports
- **Cron jobs**: Export results to CSV/JSON for stakeholder reports
- **Application monitoring**: Integrate into observability dashboard

---

## Related Documentation

- **ADR-037**: Intelligent Gap Detection Architecture
- **LLM Usage Tracker**: `backend/app/services/llm_usage_tracker.py`
- **Grafana Dashboard**: `monitoring/grafana/dashboards/intelligent-gap-detection.json`
- **Alert Configuration**: `config/grafana/alerts/intelligent-gap-detection-alerts.yml`
