# Grafana Dashboard: Gap Detection Metrics

**Issue:** #980
**Status:** Implemented
**Author:** CC (Claude Code)
**Date:** November 2025

## Overview

Comprehensive Grafana dashboard for monitoring gap detection system performance, accuracy, and usage patterns.

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Gap Detection System - Real-Time Monitoring                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Row 1: Performance Metrics                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Avg Analysis│  │ Cache Hit   │  │ Batch Throughput        │
│  │ Time: 38ms  │  │ Rate: 82%   │  │ 450 assets/min │        │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                   │
│  Row 2: Gap Analysis Trends                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Analysis Time Histogram (P50, P95, P99)                  │  │
│  │  [Time series graph showing latency distribution]         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Row 3: Assessment Readiness                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Readiness Ratio Over Time                                 │  │
│  │  [Stacked area chart: Ready vs Not Ready assets]          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Row 4: Gap Distribution                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  By Priority │  │  By Inspector│  │  By Field    │         │
│  │  [Pie chart] │  │  [Bar chart] │  │  [Table]     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                   │
│  Row 5: Cache Performance                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Cache Hit/Miss Ratio & Response Time Savings             │  │
│  │  [Dual-axis line chart]                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Prometheus Metrics

### Performance Metrics

#### 1. Analysis Duration
```promql
# Histogram of gap analysis duration in milliseconds
gap_detection_analysis_duration_ms{job="migration_backend"}

# Query for P50, P95, P99
histogram_quantile(0.50, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le))
histogram_quantile(0.95, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le))
```

**Panel:** Time series graph
**Target:** P95 < 50ms, P99 < 100ms

#### 2. Cache Hit Rate
```promql
# Cache hit rate percentage
(
  sum(rate(gap_detection_cache_hits_total[5m]))
  /
  sum(rate(gap_detection_cache_requests_total[5m]))
) * 100

# Separate hit and miss metrics
sum(rate(gap_detection_cache_hits_total[5m])) by (engagement_id)
sum(rate(gap_detection_cache_misses_total[5m])) by (engagement_id)
```

**Panel:** Gauge (target: >80%)
**Alert:** < 70% for 15 minutes

#### 3. Batch Throughput
```promql
# Assets analyzed per minute
sum(rate(gap_detection_assets_analyzed_total[1m])) * 60

# Batch analysis rate
sum(rate(gap_detection_batch_analyses_total[5m])) by (batch_size)
```

**Panel:** Graph (line chart)
**Target:** 400+ assets/minute

### Gap Detection Metrics

#### 4. Gaps Found by Priority
```promql
# Count of gaps by priority level
sum(gap_detection_gaps_found_total) by (priority)

# Rate of critical gaps over time
sum(rate(gap_detection_gaps_found_total{priority="critical"}[5m]))
```

**Panel:** Stacked bar chart
**Categories:** CRITICAL, HIGH, MEDIUM, LOW

#### 5. Assessment Readiness Ratio
```promql
# Percentage of assessment-ready assets
(
  sum(gap_detection_assessment_ready_total{ready="true"})
  /
  sum(gap_detection_assessment_ready_total)
) * 100

# By engagement
sum(gap_detection_assessment_ready_total{ready="true"}) by (engagement_id)
sum(gap_detection_assessment_ready_total{ready="false"}) by (engagement_id)
```

**Panel:** Gauge + time series
**Target:** >70% ready

#### 6. Inspector Performance
```promql
# Gaps detected per inspector
sum(gap_detection_gaps_found_total) by (inspector)

# Inspector execution time
histogram_quantile(0.95, sum(rate(gap_detection_inspector_duration_ms_bucket[5m])) by (inspector, le))
```

**Panel:** Bar chart
**Inspectors:** column, enrichment, jsonb, requirements, standards

### System Health Metrics

#### 7. Error Rate
```promql
# Analysis error rate
sum(rate(gap_detection_analysis_errors_total[5m]))

# Error rate by type
sum(rate(gap_detection_analysis_errors_total[5m])) by (error_type)
```

**Panel:** Time series
**Alert:** > 5% error rate

#### 8. Database Query Performance
```promql
# Gap detection DB query duration
histogram_quantile(0.95, sum(rate(gap_detection_db_query_duration_ms_bucket[5m])) by (le))

# Query count
sum(rate(gap_detection_db_queries_total[5m]))
```

**Panel:** Dual-axis chart
**Target:** P95 < 10ms

## Dashboard Queries

### Row 1: Performance Overview

**Panel 1: Average Analysis Time**
```json
{
  "title": "Avg Gap Analysis Time",
  "type": "stat",
  "targets": [
    {
      "expr": "histogram_quantile(0.50, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le))",
      "legendFormat": "P50"
    }
  ],
  "fieldConfig": {
    "unit": "ms",
    "thresholds": {
      "mode": "absolute",
      "steps": [
        {"value": 0, "color": "green"},
        {"value": 40, "color": "yellow"},
        {"value": 50, "color": "red"}
      ]
    }
  }
}
```

**Panel 2: Cache Hit Rate**
```json
{
  "title": "Cache Hit Rate",
  "type": "stat",
  "targets": [
    {
      "expr": "(sum(rate(gap_detection_cache_hits_total[5m])) / sum(rate(gap_detection_cache_requests_total[5m]))) * 100"
    }
  ],
  "fieldConfig": {
    "unit": "percent",
    "thresholds": {
      "steps": [
        {"value": 0, "color": "red"},
        {"value": 70, "color": "yellow"},
        {"value": 80, "color": "green"}
      ]
    }
  }
}
```

**Panel 3: Batch Throughput**
```json
{
  "title": "Assets Analyzed per Minute",
  "type": "stat",
  "targets": [
    {
      "expr": "sum(rate(gap_detection_assets_analyzed_total[1m])) * 60"
    }
  ],
  "fieldConfig": {
    "unit": "assets/min",
    "thresholds": {
      "steps": [
        {"value": 0, "color": "green"}
      ]
    }
  }
}
```

### Row 2: Analysis Time Distribution

**Panel: Analysis Time Histogram**
```json
{
  "title": "Gap Analysis Time Distribution",
  "type": "graph",
  "targets": [
    {
      "expr": "histogram_quantile(0.50, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le))",
      "legendFormat": "P50"
    },
    {
      "expr": "histogram_quantile(0.95, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le))",
      "legendFormat": "P95"
    },
    {
      "expr": "histogram_quantile(0.99, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le))",
      "legendFormat": "P99"
    }
  ],
  "yAxis": {"label": "Duration (ms)"}
}
```

### Row 3: Assessment Readiness

**Panel: Readiness Ratio Over Time**
```json
{
  "title": "Assessment Readiness Trend",
  "type": "graph",
  "targets": [
    {
      "expr": "(sum(gap_detection_assessment_ready_total{ready=\"true\"}) / sum(gap_detection_assessment_ready_total)) * 100",
      "legendFormat": "Ready %"
    }
  ],
  "yAxis": {"label": "Percentage", "min": 0, "max": 100}
}
```

### Row 4: Gap Distribution

**Panel 1: By Priority (Pie Chart)**
```json
{
  "title": "Gaps by Priority",
  "type": "piechart",
  "targets": [
    {
      "expr": "sum(gap_detection_gaps_found_total) by (priority)"
    }
  ]
}
```

**Panel 2: By Inspector (Bar Chart)**
```json
{
  "title": "Gaps Detected by Inspector",
  "type": "bargauge",
  "targets": [
    {
      "expr": "sum(gap_detection_gaps_found_total) by (inspector)"
    }
  ],
  "options": {
    "orientation": "horizontal"
  }
}
```

**Panel 3: Top Missing Fields (Table)**
```json
{
  "title": "Top Missing Fields",
  "type": "table",
  "targets": [
    {
      "expr": "topk(10, sum(gap_detection_gaps_found_total) by (field_name))",
      "format": "table"
    }
  ]
}
```

### Row 5: Cache Performance

**Panel: Cache Performance Dual-Axis**
```json
{
  "title": "Cache Performance",
  "type": "graph",
  "targets": [
    {
      "expr": "(sum(rate(gap_detection_cache_hits_total[5m])) / sum(rate(gap_detection_cache_requests_total[5m]))) * 100",
      "legendFormat": "Hit Rate %",
      "yAxisIndex": 0
    },
    {
      "expr": "avg(gap_detection_cache_response_time_ms)",
      "legendFormat": "Avg Response Time (ms)",
      "yAxisIndex": 1
    }
  ],
  "yAxes": [
    {"label": "Hit Rate %", "position": "left"},
    {"label": "Response Time (ms)", "position": "right"}
  ]
}
```

## Alerts

### Critical Alerts

**1. High Analysis Latency**
```yaml
- alert: GapDetectionHighLatency
  expr: histogram_quantile(0.95, sum(rate(gap_detection_analysis_duration_ms_bucket[5m])) by (le)) > 100
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Gap detection P95 latency exceeds 100ms"
    description: "P95 analysis time is {{ $value }}ms, target is <50ms"
```

**2. Low Cache Hit Rate**
```yaml
- alert: GapDetectionLowCacheHitRate
  expr: (sum(rate(gap_detection_cache_hits_total[5m])) / sum(rate(gap_detection_cache_requests_total[5m]))) < 0.7
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Gap detection cache hit rate below 70%"
    description: "Cache hit rate is {{ $value | humanizePercentage }}, target is >80%"
```

**3. High Error Rate**
```yaml
- alert: GapDetectionHighErrorRate
  expr: sum(rate(gap_detection_analysis_errors_total[5m])) / sum(rate(gap_detection_analyses_total[5m])) > 0.05
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Gap detection error rate exceeds 5%"
    description: "Error rate is {{ $value | humanizePercentage }}"
```

## SLI/SLO Definitions

### Service Level Indicators (SLIs)

| Metric | SLI Definition | Measurement |
|--------|----------------|-------------|
| **Availability** | % of successful analyses | `(total_analyses - errors) / total_analyses` |
| **Latency** | P95 analysis time | `histogram_quantile(0.95, duration_ms_bucket)` |
| **Throughput** | Assets analyzed per minute | `rate(assets_analyzed_total[1m]) * 60` |
| **Cache Efficiency** | Cache hit rate | `cache_hits / cache_requests` |

### Service Level Objectives (SLOs)

| SLO | Target | Measurement Window | Alert Threshold |
|-----|--------|-------------------|----------------|
| **Availability** | 99.9% | 30 days | <99.5% for 5min |
| **Latency (P95)** | <50ms | 24 hours | >100ms for 10min |
| **Latency (P99)** | <100ms | 24 hours | >200ms for 10min |
| **Cache Hit Rate** | >80% | 24 hours | <70% for 15min |
| **Batch Throughput** | >400 assets/min | 1 hour | <300 for 15min |

## Dashboard Installation

### Step 1: Export Dashboard JSON

Save the dashboard configuration from Grafana UI:
1. Open Grafana
2. Navigate to Dashboards → Import
3. Upload the JSON configuration from `grafana_dashboards/gap_detection.json`

### Step 2: Configure Data Source

Ensure Prometheus data source is configured:
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Step 3: Import Alerts

Import alert rules into Prometheus/Alertmanager:
```bash
kubectl apply -f prometheus-alerts/gap-detection-alerts.yaml
```

## Usage

### Accessing the Dashboard

**URL:** `https://grafana.example.com/d/gap-detection/gap-detection-system`

**Filters:**
- Time range: Last 24 hours (default)
- Engagement ID: (select from dropdown)
- Client Account: (select from dropdown)

### Interpreting Metrics

**Green Status:** All metrics within targets
**Yellow Status:** Approaching threshold, monitor closely
**Red Status:** SLO violated, investigate immediately

### Common Investigations

**Scenario 1: High Latency**
1. Check batch size distribution
2. Verify database connection pool
3. Examine cache hit rate
4. Review inspector execution times

**Scenario 2: Low Cache Hit Rate**
1. Check cache TTL settings
2. Verify Redis connectivity
3. Examine data update frequency
4. Review cache key patterns

**Scenario 3: High Error Rate**
1. Check application logs for stack traces
2. Verify database connectivity
3. Examine tenant scoping issues
4. Review inspector error rates

## Maintenance

### Dashboard Updates

Dashboard version controlled in:
`/config/grafana/dashboards/gap_detection.json`

Update procedure:
1. Make changes in Grafana UI
2. Export dashboard JSON
3. Commit to repository
4. Deploy via ConfigMap

### Metric Retention

- **Real-time data:** 24 hours (15s resolution)
- **Historical data:** 90 days (5m resolution)
- **Long-term trends:** 1 year (1h resolution)

## References

- **Prometheus Metrics:** `backend/app/services/gap_detection/metrics.py`
- **Logging:** `backend/app/services/gap_detection/logging_config.py`
- **Alert Rules:** `config/prometheus/alerts/gap-detection.yaml`
