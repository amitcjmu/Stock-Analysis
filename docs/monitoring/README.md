# Monitoring Documentation

This directory contains monitoring setup and documentation for the Migration UI Orchestrator platform.

## Available Monitoring

### Intelligent Gap Detection (ADR-037)

**Performance and cost monitoring for intelligent gap detection and questionnaire generation system.**

**Issue**: #1119 - Performance Validation and Monitoring Setup

#### Quick Links

- **Grafana Dashboard**: [http://localhost:9999/d/intelligent-gap-detection/](http://localhost:9999/d/intelligent-gap-detection/)
- **LLM Cost Dashboard**: [http://localhost:8081/finops/llm-costs](http://localhost:8081/finops/llm-costs)

#### Documentation

- **Performance Baseline**: [INTELLIGENT_GAP_DETECTION_BASELINE.md](./INTELLIGENT_GAP_DETECTION_BASELINE.md) - Performance targets, cost targets, quality metrics
- **Database Queries**: [/backend/docs/monitoring/intelligent_gap_detection_queries.md](/backend/docs/monitoring/intelligent_gap_detection_queries.md) - SQL queries for monitoring

#### Configuration

- **Grafana Dashboard**: `/monitoring/grafana/dashboards/intelligent-gap-detection.json`
- **Alert Rules**: `/config/grafana/alerts/intelligent-gap-detection-alerts.yml`

#### Key Metrics

| Metric | Target | Current Baseline |
|--------|--------|------------------|
| Gap Scan Performance | <500ms | 160ms ✅ |
| Question Generation Time | <2s | 8.3s 🔴 |
| LLM Cost Per Question | <$0.008 | $0.017 🔴 |
| False Gap Rate | 0 | Unknown 🔴 |
| Duplicate Question Rate | 0 | Unknown 🔴 |
| Success Rate | >95% | Unknown 🔴 |

---

## Setting Up Monitoring

### 1. Grafana Dashboard Installation

#### Option A: Docker Compose (Recommended)

If Grafana is included in docker-compose:

```bash
cd config/docker
docker-compose up -d grafana
```

Access: [http://localhost:9999](http://localhost:9999)

#### Option B: Manual Import

1. Navigate to Grafana: [http://localhost:9999](http://localhost:9999)
2. Go to **Dashboards** → **Import**
3. Upload `/monitoring/grafana/dashboards/intelligent-gap-detection.json`
4. Select PostgreSQL datasource: `migration-db`
5. Click **Import**

---

### 2. Configure PostgreSQL Datasource

**Name**: `migration-db`

**Connection Settings**:
```
Host: localhost:5433
Database: migration_db
User: postgres
Password: postgres
SSL Mode: disable (for local dev)
```

**Test Query**:
```sql
SELECT COUNT(*) FROM migration.llm_usage_logs;
```

---

### 3. Alert Configuration

#### Prerequisites

- Grafana v9.0+ with Alerting enabled
- Notification channels configured (Slack, Email)

#### Installation

1. Copy alert file to Grafana provisioning directory:
   ```bash
   cp config/grafana/alerts/intelligent-gap-detection-alerts.yml \
      /path/to/grafana/provisioning/alerting/
   ```

2. Configure notification channels in Grafana:
   - **Backend Team**: Slack webhook (`SLACK_WEBHOOK_BACKEND` env var)
   - **FinOps Team**: Email (`finops@yourcompany.com`)
   - **AI/ML Team**: Slack webhook (`SLACK_WEBHOOK_AI_ML` env var)

3. Restart Grafana:
   ```bash
   docker-compose restart grafana
   ```

#### Alert Rules

**Critical Alerts** (Immediate Action):
- False Gap Detected (Target: 0)
- LLM API Error Rate >10%
- Daily Cost Budget Exceeded

**Warning Alerts** (Review Required):
- Gap Scan Performance >500ms
- Question Generation >2s
- Cost Per Question >$0.008
- Cache Efficiency <90%

---

## Monitoring Queries

### Quick Performance Check

```bash
# Connect to database
docker exec -it migration_postgres psql -U postgres -d migration_db

# Run performance summary
\i /app/docs/monitoring/intelligent_gap_detection_queries.md
```

### Common Queries

**Performance Summary (Last Hour)**:
```sql
SELECT
    feature_context,
    AVG(response_time_ms) as avg_ms,
    COUNT(*) as calls,
    AVG(total_cost) as avg_cost
FROM migration.llm_usage_logs
WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
  AND created_at >= NOW() - INTERVAL '1 hour'
  AND success = true
GROUP BY feature_context;
```

**Cost Summary (Last 24 Hours)**:
```sql
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    SUM(total_cost) as hourly_cost,
    COUNT(*) as calls
FROM migration.llm_usage_logs
WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator', 'data_awareness_agent')
  AND created_at >= NOW() - INTERVAL '24 hours'
  AND success = true
GROUP BY hour
ORDER BY hour DESC;
```

**Error Analysis**:
```sql
SELECT
    feature_context,
    error_type,
    COUNT(*) as error_count,
    MAX(created_at) as last_occurrence
FROM migration.llm_usage_logs
WHERE success = false
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY feature_context, error_type
ORDER BY error_count DESC;
```

---

## Validation Checklist

### Pre-Deployment

- [ ] Unit tests pass (`pytest tests/unit/collection/test_intelligent_gap_scanner.py`)
- [ ] Integration tests pass (`pytest tests/integration/collection/test_intelligent_questionnaire_generation_e2e.py`)
- [ ] E2E tests pass (`npm run test:e2e -- tests/e2e/intelligent-questionnaire-ui.spec.ts`)
- [ ] Grafana dashboard loads without errors
- [ ] PostgreSQL datasource connected
- [ ] Alert rules deployed

### Post-Deployment (Week 1)

- [ ] Gap scan performance <500ms
- [ ] Question generation <2s per question
- [ ] Cost per question <$0.008
- [ ] False gap rate = 0
- [ ] Duplicate question rate = 0
- [ ] Success rate >95%
- [ ] Cache efficiency >90%

### Monthly Review

- [ ] Cost report generated (before vs after ADR-037)
- [ ] False gap incidents reviewed (root cause analysis)
- [ ] Duplicate question patterns analyzed
- [ ] Prompt optimization opportunities identified
- [ ] Model pricing updated if changed

---

## Troubleshooting

### Dashboard Not Loading

**Symptom**: Grafana dashboard shows "No data"

**Solutions**:
1. Check PostgreSQL datasource connection
2. Verify `llm_usage_logs` table has data:
   ```sql
   SELECT COUNT(*) FROM migration.llm_usage_logs
   WHERE feature_context IN ('intelligent_gap_detection', 'section_question_generator');
   ```
3. Check time range (default: last 6 hours)
4. Verify feature_context values match exactly

---

### Alerts Not Firing

**Symptom**: No alerts received despite metric thresholds exceeded

**Solutions**:
1. Check Grafana alerting status: **Alerting** → **Alert rules**
2. Verify notification channels configured
3. Test notification channels: **Alerting** → **Contact points** → **Test**
4. Check alert evaluation interval (default: 1-5 minutes)
5. Review alert logs: **Alerting** → **Alert rules** → **View state history**

---

### High Costs Detected

**Symptom**: Alert "LLM Cost Per Question Exceeds Budget" triggered

**Investigation Steps**:
1. Check Grafana dashboard: **Cost Breakdown by Feature Context**
2. Run cost analysis query:
   ```sql
   SELECT
       DATE_TRUNC('hour', created_at) as hour,
       AVG(input_tokens) as avg_input_tokens,
       AVG(total_cost) as avg_cost,
       COUNT(*) as calls
   FROM migration.llm_usage_logs
   WHERE feature_context = 'section_question_generator'
     AND created_at >= NOW() - INTERVAL '24 hours'
     AND success = true
   GROUP BY hour
   ORDER BY hour DESC;
   ```
3. Review input token usage (target: <3,500)
4. Check for prompt regression or model changes
5. Review LLM provider pricing changes

---

### False Gaps Detected

**Symptom**: Alert "False Gap Detection Occurred" triggered

**Investigation Steps**:
1. Query false gaps:
   ```sql
   SELECT asset_id, field_name, data_found, confidence_score
   FROM migration.collection_data_gaps
   WHERE is_true_gap = false
     AND created_at >= NOW() - INTERVAL '24 hours';
   ```
2. Identify which data source was missed (1 of 6)
3. Review `IntelligentGapScanner` logic for that source
4. Check if data exists in custom_attributes, enrichment_data, etc.
5. Create bug report with asset_id and field_name

---

## Performance Benchmarks

### By Flow Size

| Flow Size | Assets | Questions | Time | Cost |
|-----------|--------|-----------|------|------|
| Small | 1-2 | 3-9 | <10s | <$0.08 |
| Medium | 3-10 | 10-40 | <40s | <$0.35 |
| Large | 11-50 | 41-200 | <3min | <$1.75 |
| Enterprise | 51+ | 201+ | <10min | <$6.00 |

### By Component

| Component | Target Time | Target Cost |
|-----------|-------------|-------------|
| IntelligentGapScanner | <500ms | $0.001 |
| DataAwarenessAgent | 3-5s | $0.020/flow |
| SectionQuestionGenerator | <2s | $0.006/question |

---

## Related Documentation

- **ADR-037**: [/docs/adr/037-intelligent-gap-detection-and-questionnaire-generation.md](/docs/adr/037-intelligent-gap-detection-and-questionnaire-generation.md)
- **Implementation Issues**: #1117, #1118, #1119
- **Parent Issue**: #1109 (Data Gaps and Questionnaire Agent Optimization)

---

## Contact

**Questions or Issues**: Create issue with label `intelligent-gap-detection` or `monitoring`

**Grafana Access**: [http://localhost:9999/d/intelligent-gap-detection/](http://localhost:9999/d/intelligent-gap-detection/)

**LLM Cost Dashboard**: [http://localhost:8081/finops/llm-costs](http://localhost:8081/finops/llm-costs)
