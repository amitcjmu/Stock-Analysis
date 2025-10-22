# JSON Sanitization Pattern Application Audit

**Date**: 2025-10-22
**ADR**: ADR-029
**Issue**: #682 (Questionnaire generation JSON serialization failures)
**Agent**: Python-CrewAI-FastAPI Expert

## Executive Summary

Successfully created shared `sanitize_for_json()` utility at `/backend/app/utils/json_sanitization.py` and applied it to questionnaire generation endpoint. Comprehensive unit tests created with 20 test cases covering all edge cases.

**Test Results**: ✅ 20/20 tests passing in Docker environment

## Shared Utility Created

### Location
`/backend/app/utils/json_sanitization.py`

### Features
- Recursively sanitizes nested dictionaries and lists
- Converts NaN → null
- Converts Infinity/-Infinity → null
- Converts datetime/date objects → ISO 8601 strings
- Preserves all valid primitive types
- Handles non-serializable objects → string representation

### Usage Pattern
```python
from app.utils.json_sanitization import sanitize_for_json

# Before returning LLM data in API response
return ResponseModel(
    data=sanitize_for_json(llm_generated_data)
)
```

## Endpoints Already Using Sanitization

### 1. Collection Questionnaire Generation ✅
- **File**: `/backend/app/api/v1/endpoints/collection_serializers/core.py`
- **Function**: `build_questionnaire_response()`
- **Status**: COMPLETED (Issue #682 fix)
- **Data Sanitized**: `questions` array (adaptive questionnaire data)
- **Risk Fields**:
  - `confidence` scores from LLM
  - `business_impact_score` from AI agent
  - Custom question scoring fields

## Endpoints Requiring Sanitization Application

Based on codebase analysis, the following endpoints return LLM/AI-generated numeric data that **MAY** contain NaN/Infinity values:

### High Priority (Direct LLM Outputs)

#### 1. SixR Analysis Recommendations
- **Files**:
  - `/backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/recommendation_handlers.py`
  - `/backend/app/api/v1/endpoints/sixr_analysis_modular/handlers/analysis_handlers.py`
- **Functions**:
  - `get_sixr_recommendation()` → `SixRRecommendationResponse`
  - `get_analysis()` → `SixRAnalysisResponse`
  - `list_analyses()` → `SixRAnalysisListResponse`
- **Risk Fields**:
  - `confidence_score` (Float, 0-1)
  - `progress_percentage` (Float)
  - `analysis_duration` (Float, seconds)
- **Recommendation**: APPLY - These responses come from CrewAI agents analyzing migration strategies

#### 2. Gap Analysis Enhancement Results
- **File**: `/backend/app/api/v1/endpoints/collection_gap_analysis/analysis_endpoints/background_workers.py`
- **Function**: `process_gap_enhancement_job()` (background task)
- **Risk Fields**:
  - `business_impact` scores from AI
  - `confidence` scores from pattern matching
  - `collection_difficulty` estimates
- **Recommendation**: APPLY - Background job results stored in database, then returned via API

#### 3. Agent Insights & Status
- **Files**:
  - `/backend/app/api/v1/endpoints/agents/discovery/handlers/status_insights.py`
  - `/backend/app/api/v1/endpoints/agents/discovery/handlers/agent_ui_integration.py`
  - `/backend/app/api/v1/endpoints/agent_performance.py`
- **Functions**: Agent status and insights endpoints
- **Risk Fields**:
  - Performance metrics (confidence, accuracy)
  - Agent decision scores
  - Learning pattern confidence values
- **Recommendation**: APPLY - Agents may return numeric insights with edge case values

### Medium Priority (Indirect LLM Outputs)

#### 4. Field Mapping Suggestions
- **File**: `/backend/app/api/v1/endpoints/data_import/field_mapping/services/suggestion_service.py`
- **Risk Fields**:
  - `confidence_score` for mapping suggestions
  - Similarity scores from vector comparisons
- **Recommendation**: EVALUATE - May already handle via Pydantic validation

#### 5. Critical Attribute Analysis
- **File**: `/backend/app/api/v1/endpoints/data_import/agentic_critical_attributes/services/attribute_analyzer.py`
- **Risk Fields**:
  - `confidence` scores from AI analysis
  - `criticality_score` calculations
- **Recommendation**: EVALUATE - Check if agentic service returns raw scores

### Low Priority (Calculated Values, Not Direct LLM)

#### 6. Data Quality Scores
- **File**: `/backend/app/api/v1/endpoints/data_import/quality_analysis.py`
- **Risk Fields**: Quality percentages (calculated, not from LLM)
- **Recommendation**: MONITOR - Unlikely to produce NaN unless division by zero

#### 7. Agent Performance Metrics
- **File**: `/backend/app/api/v1/endpoints/monitoring/agent_performance.py`
- **Risk Fields**: Aggregated metrics (calculated, not from LLM)
- **Recommendation**: MONITOR - Database aggregations should be safe

## Implementation Strategy

### Phase 1: High Priority (Immediate) ✅
1. ✅ Collection questionnaires (COMPLETED - Issue #682)
2. ⏳ SixR analysis recommendations
3. ⏳ Gap analysis enhancement results
4. ⏳ Agent insights endpoints

### Phase 2: Medium Priority (Next Sprint)
1. Field mapping suggestions (evaluate first)
2. Critical attribute analysis (evaluate first)

### Phase 3: Low Priority (Monitor in Production)
1. Add telemetry to track NaN/Infinity occurrences
2. Update documentation for future LLM endpoints
3. Consider pre-commit hook to enforce pattern

## Testing Results

### Unit Tests Created
- **File**: `/backend/tests/backend/unit/test_json_sanitization.py`
- **Test Count**: 20 test cases
- **Coverage**:
  - Basic sanitization (NaN, Infinity, datetime)
  - Nested structures
  - Edge cases (Unicode, large arrays, deep nesting)
  - Real-world LLM use cases (gap analysis, recommendations, insights)
  - Performance testing (500-item arrays)

### Test Execution
```bash
docker exec migration_backend python -m pytest tests/backend/unit/test_json_sanitization.py -v
# Result: ✅ 20 passed in 0.06s
```

### Backward Compatibility
```bash
docker exec migration_backend python -m pytest tests/backend/unit/test_collection_serializers.py -v
# Result: ✅ 14 passed in 0.05s (all existing tests still pass)
```

## Files Modified

### Created
1. `/backend/app/utils/json_sanitization.py` - Shared utility
2. `/backend/tests/backend/unit/test_json_sanitization.py` - Comprehensive unit tests

### Modified
1. `/backend/app/api/v1/endpoints/collection_serializers/core.py` - Import from shared utility (removed local implementation)
2. `/backend/tests/backend/unit/test_collection_serializers.py` - Updated import path

## Next Steps

1. **Apply to SixR Endpoints**: Add sanitization to recommendation and analysis response builders
2. **Apply to Gap Analysis**: Wrap background job results before storing to database
3. **Apply to Agent Insights**: Sanitize agent performance and insights data
4. **Add Pre-commit Hook**: Detect unsanitized LLM response patterns
5. **Update Developer Docs**: Add pattern to coding guidelines
6. **Production Telemetry**: Track NaN/Infinity occurrence frequency to guide LLM prompt improvements

## Success Metrics

- ✅ Zero JSON serialization RuntimeErrors in questionnaire generation
- ✅ Shared utility created with comprehensive docs
- ✅ 20 unit tests passing (100% of written tests)
- ✅ Backward compatibility maintained (14 existing tests still pass)
- ⏳ Pattern applied to 3+ additional LLM endpoints (in progress)
- ⏳ Pre-commit hooks updated (planned)

## References

- **ADR-029**: `/docs/adr/029-llm-output-json-sanitization-pattern.md`
- **Issue #682**: Questionnaire generation produces empty questionnaire
- **Memory File**: `.serena/memories/json-serialization-safety-pattern.md`
- **Coding Guide**: `/docs/analysis/Notes/coding-agent-guide.md` (to be updated)
