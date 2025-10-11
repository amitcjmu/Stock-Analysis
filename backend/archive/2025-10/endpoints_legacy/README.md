# Archived Legacy Endpoints

**Archived**: 2025-10-11
**Reason**: Unmounted from router_registry.py (never registered in production)

## Files Archived (6 files)

### Unmounted Endpoints
- `demo.py` - Demo endpoint (never registered in router_registry)
- `data_cleansing.py.bak` - Backup file (superseded)
- `flow_processing.py.backup` - Backup file (superseded)

### Legacy Discovery Endpoints
- `dependency_endpoints.py` - Legacy discovery endpoint (explicitly blocked in router_registry.py:116-124)
- `chat_interface.py` - Legacy discovery endpoint (explicitly blocked in router_registry.py:116-124)
- `app_server_mappings.py` - Legacy discovery endpoint (explicitly blocked in router_registry.py:116-124)

## Verification

**Dependency Analysis**: Dependency analyzer (backend/scripts/analysis/dependency_analyzer.py) confirmed these files had no active imports outside of archive.

**Router Registry Check**: Verified in `backend/app/api/v1/router_registry.py` that:
- `demo.py` was never registered
- Discovery legacy endpoints (dependency_endpoints, chat_interface, app_server_mappings) were explicitly excluded from registration

## Related Documentation

- `/docs/analysis/backend_cleanup/FINAL-PARALLEL-EXECUTION-PLAN.md` - Full cleanup plan
- `/docs/analysis/backend_cleanup/dependency_graphs/SUMMARY.md` - Dependency analysis results
- `/docs/analysis/backend_cleanup/001-comprehensive-review-report.md` - Manual verification

## Restoration

If restoration is needed:
```bash
# Copy files back to original locations
cp archive/2025-10/endpoints_legacy/demo.py app/api/v1/endpoints/
cp archive/2025-10/endpoints_legacy/dependency_endpoints.py app/api/v1/discovery/
# etc.
```
