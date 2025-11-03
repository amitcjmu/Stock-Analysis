# Grafana Dashboard Line Format Bug - October 2025

## Issue
User reported: "Error logs don't have any details only timestamp entries"

## Root Cause
LogQL `line_format` pipe was stripping log content in Panel 4 (Error Logs) and Panel 6 (Audit Events).

**Why it failed:**
```logql
{container="migration_backend"} |~ "ERROR" | line_format "{{.level}} | {{.line}}"
```
- Attempted to extract `.level` and `.line` fields that don't exist in unstructured Docker logs
- Result: Empty string `" | "` - ALL log content discarded
- Only metadata remained (container, compose_service, stream)

## Fix Applied
**File:** `config/docker/observability/grafana/dashboards/app-logs-enhanced.json`

**Panel 4 (Line 323):** Removed `| line_format "{{.level}} | {{.line}}"`
**Panel 6 (Line 401):** Removed `| json | line_format "{{.category}} | {{.operation}} | {{.success}} | {{.error_message}}"`

```bash
docker restart migration_grafana
```

## Verification Method
Used Playwright MCP to inspect actual dashboard rendering in browser (not curl):
- Screenshot before fix: Only timestamps and metadata visible
- Screenshot after fix: Full error messages, JSON payloads, stack traces visible

## Result
✅ Panel 4: Error logs now show complete details (error messages, validation failures, stack traces)
✅ Panel 5: Phase transition logs working
✅ All 8 dashboard panels functional

## Lesson Learned
**NEVER use `line_format` with fields that don't exist in log structure.** Docker logs are unstructured text - use raw content or add structured logging at application level.

## References
- Investigation Report: `/tmp/dashboard-investigation-findings.md`
- Dashboard: `http://localhost:9999/d/app-logs-enhanced`
- Playwright screenshots: `.playwright-mcp/dashboard-*.png`
