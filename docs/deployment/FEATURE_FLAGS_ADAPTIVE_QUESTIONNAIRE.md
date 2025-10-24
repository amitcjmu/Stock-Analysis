# Feature Flags: Collection Flow Adaptive Questionnaire

Feature flags for gradual rollout and testing of Collection Flow adaptive questionnaire enhancements (Issue #768).

## Feature Flags Overview

| Feature Flag | Default | Description | Impact |
|-------------|---------|-------------|---------|
| `collection.adaptive.bulk_answer` | `True` | Multi-asset bulk answer operations | Enables bulk answer preview and submission endpoints |
| `collection.adaptive.dynamic_questions` | `True` | Dynamic question filtering | Enables asset-type-specific and answered/unanswered filtering |
| `collection.adaptive.bulk_import` | `True` | CSV/JSON bulk import | Enables file upload, analysis, and background task execution |
| `collection.adaptive.gap_analysis` | `True` | Incremental gap analysis | Enables weight-based progress and fast/thorough modes |
| `collection.adaptive.agent_pruning` | `True` | AI agent-based question pruning | Enables intelligent question filtering with fallback |
| `collection.adaptive.field_mapping` | `True` | Intelligent field mapping | Enables confidence-scored CSV column mapping suggestions |
| `collection.adaptive.conflict_resolution` | `True` | Conflict detection and resolution | Enables multi-value conflict detection in bulk operations |

## Deployment Strategies

### Strategy 1: Full Rollout (Recommended for Internal Testing)

All features enabled - ideal for comprehensive testing in staging environment:

```bash
# No environment variables needed - all default to True
docker-compose up -d
```

### Strategy 2: Gradual Rollout

Enable features incrementally to test each capability:

**Phase 1: Dynamic Questions Only**
```bash
export FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_ANSWER=false
export FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_IMPORT=false
export FEATURE_FLAG_COLLECTION_ADAPTIVE_GAP_ANALYSIS=false
export FEATURE_FLAG_COLLECTION_ADAPTIVE_AGENT_PRUNING=false
export FEATURE_FLAG_COLLECTION_ADAPTIVE_FIELD_MAPPING=false
export FEATURE_FLAG_COLLECTION_ADAPTIVE_CONFLICT_RESOLUTION=false
export FEATURE_FLAG_COLLECTION_ADAPTIVE_DYNAMIC_QUESTIONS=true
docker-compose up -d
```

**Phase 2: Add Bulk Answer**
```bash
export FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_ANSWER=true
export FEATURE_FLAG_COLLECTION_ADAPTIVE_CONFLICT_RESOLUTION=true
# Keep others disabled
docker-compose up -d
```

**Phase 3: Add Bulk Import**
```bash
export FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_IMPORT=true
export FEATURE_FLAG_COLLECTION_ADAPTIVE_FIELD_MAPPING=true
# Enable all dynamic and bulk answer features
docker-compose up -d
```

**Phase 4: Full Enablement**
```bash
# Enable all features
export FEATURE_FLAG_COLLECTION_ADAPTIVE_AGENT_PRUNING=true
export FEATURE_FLAG_COLLECTION_ADAPTIVE_GAP_ANALYSIS=true
docker-compose up -d
```

### Strategy 3: Disable Specific Features

For troubleshooting or A/B testing, disable specific features:

**Disable AI Agent Pruning (Fallback Only)**
```bash
export FEATURE_FLAG_COLLECTION_ADAPTIVE_AGENT_PRUNING=false
# All other features remain enabled
docker-compose up -d
```

**Disable Conflict Resolution (Skip Conflicting Assets)**
```bash
export FEATURE_FLAG_COLLECTION_ADAPTIVE_CONFLICT_RESOLUTION=false
docker-compose up -d
```

## Railway Deployment

For Railway staging environment:

1. **Navigate to Project Settings → Variables**

2. **Add Environment Variables**:
   ```
   FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_ANSWER=true
   FEATURE_FLAG_COLLECTION_ADAPTIVE_DYNAMIC_QUESTIONS=true
   FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_IMPORT=true
   FEATURE_FLAG_COLLECTION_ADAPTIVE_GAP_ANALYSIS=true
   FEATURE_FLAG_COLLECTION_ADAPTIVE_AGENT_PRUNING=true
   FEATURE_FLAG_COLLECTION_ADAPTIVE_FIELD_MAPPING=true
   FEATURE_FLAG_COLLECTION_ADAPTIVE_CONFLICT_RESOLUTION=true
   ```

3. **Trigger Redeploy**

4. **Verify in Logs**:
   ```bash
   railway logs --tail 100
   # Look for: "🚩 Feature Flags Configuration:"
   ```

## Testing Feature Flags

### Check Enabled Features (API Endpoint)

```bash
# Local
curl http://localhost:8000/api/v1/admin/feature-flags

# Staging
curl https://migrate-ui-orchestrator-staging.up.railway.app/api/v1/admin/feature-flags
```

### Test Individual Feature

```python
from app.core.feature_flags import is_feature_enabled

# In route handler
if is_feature_enabled("collection.adaptive.bulk_answer"):
    # Bulk answer logic
    pass
else:
    # Return 404 or disabled message
    pass
```

### Use `@require_feature` Decorator

```python
from app.core.feature_flags import require_feature

@router.post("/bulk-answer")
@require_feature("collection.adaptive.bulk_answer")
async def bulk_answer_endpoint(...):
    # This endpoint only accessible if feature enabled
    pass
```

## Rollback Strategy

If issues are detected in production:

1. **Immediate Rollback (Disable All)**:
   ```bash
   export FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_ANSWER=false
   export FEATURE_FLAG_COLLECTION_ADAPTIVE_DYNAMIC_QUESTIONS=false
   export FEATURE_FLAG_COLLECTION_ADAPTIVE_BULK_IMPORT=false
   export FEATURE_FLAG_COLLECTION_ADAPTIVE_GAP_ANALYSIS=false
   export FEATURE_FLAG_COLLECTION_ADAPTIVE_AGENT_PRUNING=false
   export FEATURE_FLAG_COLLECTION_ADAPTIVE_FIELD_MAPPING=false
   export FEATURE_FLAG_COLLECTION_ADAPTIVE_CONFLICT_RESOLUTION=false
   # Redeploy
   ```

2. **Partial Rollback (Disable Problematic Feature)**:
   - Identify feature causing issues from logs/monitoring
   - Disable only that feature flag
   - Keep other features enabled

3. **Verify Rollback**:
   ```bash
   # Check logs for feature flag configuration
   # Verify affected endpoints return 404
   curl -I https://migrate-ui-orchestrator.up.railway.app/api/v1/collection/bulk-answer
   # Should return 404 if feature disabled
   ```

## Monitoring and Observability

### Feature Usage Metrics

Monitor feature flag usage through:
- **Application logs**: Feature access attempts
- **API metrics**: Endpoint call rates
- **Error rates**: Track if features cause increased errors

### Log Patterns to Watch

```
# Feature flag configuration at startup
🚩 Feature Flags Configuration:
  collection.adaptive.bulk_answer: True
  ...

# Feature access attempts
Access denied to disabled feature 'collection.adaptive.bulk_import' for endpoint bulk_import_analyze

# Environment overrides
Feature flag 'collection.adaptive.agent_pruning' overridden by FEATURE_FLAG_COLLECTION_ADAPTIVE_AGENT_PRUNING=false -> False
```

## Best Practices

1. **Test Locally First**: Always test feature flag changes in local Docker environment before staging

2. **Document Decisions**: Log why features were enabled/disabled in deployment notes

3. **Monitor After Changes**: Watch logs and metrics for 1 hour after flag changes

4. **Gradual Enablement**: Enable one feature at a time in production, not all at once

5. **Keep Defaults True in Code**: Use environment variables for disabling, not code changes

6. **Coordinate with Team**: Notify team before changing feature flags in shared environments

## Related Documentation

- **ADR-030**: Collection Flow Adaptive Questionnaire Architecture
- **Issue #768**: Collection Flow Adaptive Questionnaire Enhancements
- **API Documentation**: `/api/v1/docs` (Swagger UI)
- **Testing Guide**: `/docs/testing/COLLECTION_FLOW_TESTING.md`

## Support

For issues with feature flags:
1. Check application logs for feature flag configuration
2. Verify environment variables are set correctly
3. Review `/api/v1/admin/feature-flags` endpoint response
4. Contact DevOps team for Railway-specific issues
