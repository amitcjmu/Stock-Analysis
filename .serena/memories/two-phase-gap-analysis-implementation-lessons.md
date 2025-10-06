# Two-Phase Gap Analysis Implementation & Debugging Lessons

## 1. Vite Proxy Timeout for Long-Running AI Operations

**Problem**: Vite dev server proxy defaults to 120s timeout, causing failures for AI operations taking 85-165s

**Solution**: Configure `proxyTimeout` in vite.config.ts proxy settings

```typescript
// vite.config.ts
export default defineConfig(({ mode }) => ({
  server: {
    proxy: {
      '/api': {
        target: process.env.DOCKER_ENV === 'true' ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        proxyTimeout: 200000, // 200 seconds - support long AI operations
      }
    }
  }
}));
```

**Usage**: Apply when frontend operations involve AI agents, ML inference, or batch processing >60s

---

## 2. AG Grid Cell Renderers Must Return JSX, Not HTML Strings

**Problem**: AG Grid v34 displays HTML as text when cellRenderer returns strings like `<span class="...">Value</span>`

**Solution**: Return JSX elements directly from cellRenderer functions

```typescript
// ❌ WRONG - Displays HTML as text
cellRenderer: (params: { value: number }) => {
  return '<span class="text-red-600">Critical</span>';
}

// ✅ CORRECT - Renders properly
cellRenderer: (params: { value: number }) => {
  return <span className="text-red-600">Critical</span>;
}

// Priority badge example
{
  field: 'priority',
  cellRenderer: (params: { value: number }) => {
    const badges = {
      1: <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">Critical</span>,
      2: <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">High</span>,
      3: <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">Medium</span>,
      4: <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">Low</span>
    };
    return badges[params.value as 1 | 2 | 3 | 4] || badges[4];
  }
}
```

**Usage**: When using AG Grid React with custom cell rendering - always return JSX, not HTML strings

---

## 3. Pydantic Model Access in Gap Analysis Endpoints

**Problem**: `AttributeError: 'DataGap' object has no attribute 'get'` when treating Pydantic models as dictionaries

**Solution**: Use dot notation for Pydantic models, `.get()` for dicts, and `model_dump()` to convert

```python
# collection_gap_analysis_router.py - Correct pattern
for input_gap in request_body.gaps:  # input_gap is Pydantic DataGap
    matching_ai_gap = next(
        (
            ag for ag in all_ai_gaps  # ag is dict from parse_task_output
            if ag.get("field_name") == input_gap.field_name  # Pydantic: dot notation
            and ag.get("asset_id") == input_gap.asset_id    # dict: .get()
        ),
        None
    )

    if matching_ai_gap:
        enhanced_gap = input_gap.model_dump()  # Convert Pydantic to dict
        enhanced_gap["confidence_score"] = matching_ai_gap.get("confidence_score")
        enhanced_gaps.append(enhanced_gap)
    else:
        enhanced_gaps.append(input_gap.model_dump())
```

**Usage**: When mixing Pydantic models and dicts in API endpoints - never use `.get()` on Pydantic models

---

## 4. Two-Phase Gap Analysis Architecture

**Problem**: Unique constraint violations when AI analysis tries to INSERT gaps already created by programmatic scan

**Solution**: Create separate non-persisting AI analysis method for enhancement-only operations

```python
# service.py - Non-persisting AI analysis for enhancement
async def _run_tier_2_ai_analysis_no_persist(
    self, assets: List, collection_flow_id: str
) -> Dict[str, Any]:
    """Run tier_2 AI WITHOUT persisting (for enhancement only).

    Prevents duplicate key violations on unique constraint:
    (collection_flow_id, field_name, gap_type, asset_id)
    """
    agent = await TenantScopedAgentPool.get_or_create_agent(...)
    task_output = await self._execute_agent_task(agent, task_description)
    result_dict = parse_task_output(task_output)

    # DO NOT PERSIST - this method is for enhancement only
    result_dict["summary"]["gaps_persisted"] = 0
    return result_dict

# Router uses non-persisting method
async def analyze_gaps(...):
    ai_result = await gap_service._run_tier_2_ai_analysis_no_persist(
        assets=assets,
        collection_flow_id=str(collection_flow.id),
    )

    # Merge AI enhancements with input gaps in-memory
    for input_gap in request_body.gaps:
        matching_ai_gap = find_match(all_ai_gaps, input_gap)
        if matching_ai_gap:
            enhanced_gap = {**input_gap.model_dump(), **ai_enhancements}
```

**Usage**: When implementing multi-phase workflows where phase 2 enhances phase 1 results without re-persisting

---

## 5. API Client Timeout Configuration

**Problem**: ApiClient default timeout (60s) insufficient for AI operations, but timeout parameter not passed through properly

**Solution**: Ensure timeout flows from service → apiCall → ApiClient.executeRequest

```typescript
// collection-flow.ts - Service layer
async analyzeGaps(flowId: string, gaps: DataGap[], selectedAssetIds: string[]): Promise<AnalyzeGapsResponse> {
  return await apiCall(`${this.baseUrl}/flows/${flowId}/analyze-gaps`, {
    method: 'POST',
    body: JSON.stringify({ gaps, selected_asset_ids: selectedAssetIds }),
    timeout: 180000 // 3 minutes for tier_2 AI analysis
  });
}

// apiClient.ts - Execute request with timeout
private async executeRequest<T>(endpoint: string, options: RequestInit & { timeout?: number }): Promise<T> {
  const controller = new AbortController();
  const timeoutMs = options.timeout || 60000; // Default 1 minute

  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const response = await fetch(url, {
    ...options,
    signal: controller.signal
  });

  clearTimeout(timeoutId);
  return response;
}
```

**Usage**: For long-running operations, set timeout at service layer and ensure it propagates through API client stack

---

## Key Files Modified

- `vite.config.ts:17` - Added `proxyTimeout: 200000`
- `DataGapDiscovery.tsx:311-345` - Changed cellRenderers to JSX
- `collection_gap_analysis_router.py:299-324` - Fixed Pydantic access pattern
- `service.py:266-321` - Added `_run_tier_2_ai_analysis_no_persist()`
- `collection-flow.ts:846` - Added `timeout: 180000`

## Outcome

All technical infrastructure working correctly:
- ✅ Vite proxy supports 200s timeout
- ✅ AG Grid renders JSX properly
- ✅ Pydantic/dict access pattern correct
- ✅ No unique constraint violations
- ✅ Frontend timeout sufficient (180s)
- ✅ AI analysis completes successfully (39s)

**Remaining Issue**: AI matching logic - AI agent found 8 gaps vs 20 programmatic gaps, resulting in 0/20 enhancement rate. This requires adjusting AI agent task prompt or matching algorithm.
