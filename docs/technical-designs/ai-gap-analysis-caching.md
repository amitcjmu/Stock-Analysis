# Intelligent AI Gap Analysis Caching

**Status**: Design Proposal
**Created**: 2025-01-13
**Author**: Claude Code
**Related PR**: #1043

## Problem Statement

AI gap analysis using Llama 4 is expensive and time-consuming:
- **Cost**: ~$0.50-$2.00 per asset analyzed
- **Time**: 30-60 seconds per asset
- **Current Behavior**: Re-analyzes assets even if data hasn't changed
- **Impact**: Unnecessary LLM costs and user wait time

**User Concern**: "We should avoid costly unnecessary repetition of agent calls for the same data over and over again."

## Goals

1. **Detect unchanged assets**: Skip AI analysis if asset data hasn't changed
2. **Return cached results**: Use previously generated gaps and questionnaires
3. **Detect data changes**: Re-analyze only when asset data changes
4. **Provide force-refresh**: Allow manual re-analysis when needed
5. **Maintain accuracy**: Never show stale data

## Solution Design

### 1. Asset Data Fingerprinting

**Add data hash column** to track asset state:

```sql
-- Migration: Add data_hash column to assets table
ALTER TABLE migration.assets
ADD COLUMN data_hash VARCHAR(64);

-- Create index for fast lookups
CREATE INDEX idx_assets_data_hash ON migration.assets(data_hash);
```

**Hash calculation** (SHA-256 of critical fields):

```python
import hashlib
import json

def calculate_asset_hash(asset: Asset) -> str:
    """Calculate SHA-256 hash of asset's critical data fields.

    Includes:
    - name, asset_type, environment
    - os_platform, os_version
    - application_name, application_version
    - hosting_model, deployment_model
    - custom_attributes (sorted for consistency)
    - dependencies (sorted)
    """
    hash_data = {
        "name": asset.name,
        "type": asset.asset_type,
        "environment": asset.environment,
        "os_platform": asset.os_platform,
        "os_version": asset.os_version,
        "app_name": asset.application_name,
        "app_version": asset.application_version,
        "hosting": asset.hosting_model,
        "deployment": asset.deployment_model,
        "custom_attrs": sorted(asset.custom_attributes.items()) if asset.custom_attributes else [],
        "dependencies": sorted([
            {"name": d.dependency_name, "type": d.dependency_type}
            for d in asset.dependencies
        ], key=lambda x: x["name"]),
    }

    hash_input = json.dumps(hash_data, sort_keys=True)
    return hashlib.sha256(hash_input.encode()).hexdigest()
```

### 2. AI Analysis Cache Table

**Create new table** to track AI analysis history:

```sql
CREATE TABLE migration.ai_gap_analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Asset tracking
    asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
    collection_flow_id UUID NOT NULL REFERENCES migration.collection_flows(id) ON DELETE CASCADE,

    -- Data versioning
    asset_data_hash VARCHAR(64) NOT NULL,
    analyzed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Analysis metadata
    ai_model VARCHAR(100) NOT NULL, -- e.g., "meta-llama/Llama-4-Maverick-17B"
    analysis_tier VARCHAR(20) NOT NULL, -- "tier_1" or "tier_2"

    -- Results references
    gaps_count INTEGER NOT NULL DEFAULT 0,
    questionnaire_sections_count INTEGER NOT NULL DEFAULT 0,

    -- Cost tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 4),

    -- Tenant isolation
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    UNIQUE(asset_id, asset_data_hash, collection_flow_id),

    -- Indexes
    INDEX idx_ai_cache_asset_hash (asset_id, asset_data_hash),
    INDEX idx_ai_cache_flow (collection_flow_id),
    INDEX idx_ai_cache_tenant (client_account_id, engagement_id)
);
```

### 3. Cache Validation Logic

**Check if asset needs re-analysis**:

```python
async def should_analyze_asset(
    asset: Asset,
    collection_flow_id: UUID,
    db: AsyncSession,
    force_refresh: bool = False
) -> bool:
    """Determine if asset needs AI analysis.

    Returns:
        True: Asset needs analysis (data changed or no cache)
        False: Use cached results (data unchanged)
    """
    if force_refresh:
        logger.info(f"🔄 Force refresh requested for asset {asset.id}")
        return True

    # Calculate current asset hash
    current_hash = calculate_asset_hash(asset)

    # Check if hash changed since last update
    if asset.data_hash != current_hash:
        logger.info(
            f"📊 Asset {asset.id} data changed - "
            f"old_hash={asset.data_hash[:8]}, new_hash={current_hash[:8]}"
        )
        # Update asset hash
        asset.data_hash = current_hash
        await db.flush()
        return True

    # Check if AI analysis exists for this hash
    from sqlalchemy import select
    stmt = select(AIGapAnalysisCache).where(
        AIGapAnalysisCache.asset_id == asset.id,
        AIGapAnalysisCache.asset_data_hash == current_hash,
        AIGapAnalysisCache.collection_flow_id == collection_flow_id,
    )
    result = await db.execute(stmt)
    cache_entry = result.scalar_one_or_none()

    if cache_entry:
        logger.info(
            f"✅ Using cached AI analysis for asset {asset.id} - "
            f"analyzed_at={cache_entry.analyzed_at}, gaps={cache_entry.gaps_count}"
        )
        return False

    logger.info(f"🆕 No AI analysis cache found for asset {asset.id} - analyzing")
    return True
```

### 4. Selective Asset Analysis

**Split assets** into cached and needs-analysis groups:

```python
async def analyze_assets_with_cache(
    assets: List[Asset],
    collection_flow_id: UUID,
    db: AsyncSession,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Analyze assets with intelligent caching.

    Returns:
        {
            "assets_analyzed": [...],  # Assets that needed analysis
            "assets_cached": [...],     # Assets using cached results
            "total_cost_saved_usd": 1.25,
            "analysis_results": {...}
        }
    """
    assets_to_analyze = []
    assets_cached = []

    # Categorize assets
    for asset in assets:
        if await should_analyze_asset(asset, collection_flow_id, db, force_refresh):
            assets_to_analyze.append(asset)
        else:
            assets_cached.append(asset)

    logger.info(
        f"📊 Asset analysis plan - "
        f"Analyze: {len(assets_to_analyze)}, "
        f"Cached: {len(assets_cached)}, "
        f"Cost saved: ~${len(assets_cached) * 1.5:.2f}"
    )

    # Run AI analysis only on changed/new assets
    if assets_to_analyze:
        analysis_results = await run_tier_2_ai_analysis(
            assets=assets_to_analyze,
            collection_flow_id=collection_flow_id,
            db=db
        )

        # Store cache entries
        for asset in assets_to_analyze:
            cache_entry = AIGapAnalysisCache(
                asset_id=asset.id,
                collection_flow_id=collection_flow_id,
                asset_data_hash=asset.data_hash,
                analyzed_at=datetime.now(timezone.utc),
                ai_model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                analysis_tier="tier_2",
                gaps_count=len([g for g in analysis_results["gaps"] if g["asset_id"] == str(asset.id)]),
                questionnaire_sections_count=len(analysis_results.get("questionnaire", {}).get("sections", [])),
                client_account_id=asset.client_account_id,
                engagement_id=asset.engagement_id,
            )
            db.add(cache_entry)

        await db.commit()
    else:
        analysis_results = {"gaps": [], "questionnaire": {"sections": []}}

    # Retrieve cached gaps for unchanged assets
    if assets_cached:
        cached_gaps = await load_cached_gaps(assets_cached, collection_flow_id, db)
        analysis_results["gaps"].extend(cached_gaps)

    return {
        "assets_analyzed": len(assets_to_analyze),
        "assets_cached": len(assets_cached),
        "total_cost_saved_usd": len(assets_cached) * 1.5,  # Avg cost per asset
        "analysis_results": analysis_results,
    }
```

### 5. Frontend Force Refresh Option

**Add "Force Refresh" checkbox** in UI:

```typescript
// src/components/collection/DataGapDiscovery.tsx

const [forceRefresh, setForceRefresh] = useState(false);

// Add checkbox in UI
<div className="flex items-center space-x-2 mb-4">
  <input
    type="checkbox"
    id="force-refresh"
    checked={forceRefresh}
    onChange={(e) => setForceRefresh(e.target.checked)}
    className="rounded border-gray-300"
  />
  <label htmlFor="force-refresh" className="text-sm text-gray-700">
    Force re-analysis (ignore cache)
    <span className="ml-2 text-gray-500">
      - Use if asset data was updated externally
    </span>
  </label>
</div>

// Pass force_refresh parameter to API
const response = await collectionFlowApi.analyzeGaps(
  flowId,
  null,
  selectedAssetIds,
  forceRefresh  // New parameter
);
```

**Update API schema**:

```python
# backend/app/schemas/collection_gap_analysis.py

class AnalyzeGapsRequest(BaseModel):
    gaps: Optional[List[DataGap]] = Field(None, ...)
    selected_asset_ids: List[str] = Field(...)
    force_refresh: bool = Field(
        False,
        description="Force re-analysis even if cached results exist"
    )
```

### 6. Cache Invalidation Strategies

**Auto-invalidate cache** when:

1. **Asset data updated**:
   ```python
   # In asset update endpoint
   asset.data_hash = calculate_asset_hash(asset)
   await db.flush()
   # Next analysis will detect hash change and re-analyze
   ```

2. **Manual cache clear** (admin endpoint):
   ```python
   @router.delete("/api/v1/collection/{flow_id}/cache")
   async def clear_analysis_cache(flow_id: str, db: AsyncSession):
       """Clear AI analysis cache for debugging/testing."""
       await db.execute(
           delete(AIGapAnalysisCache).where(
               AIGapAnalysisCache.collection_flow_id == UUID(flow_id)
           )
       )
       await db.commit()
       return {"status": "success", "message": "Cache cleared"}
   ```

3. **Time-based expiration** (optional):
   ```python
   # Add to cache validation
   cache_age = datetime.now(timezone.utc) - cache_entry.analyzed_at
   if cache_age > timedelta(days=30):
       logger.info(f"🕐 Cache expired for asset {asset.id} - age={cache_age.days} days")
       return True  # Re-analyze
   ```

## Implementation Plan

### Phase 1: Database Schema (Week 1)
- [ ] Create migration for `assets.data_hash` column
- [ ] Create migration for `ai_gap_analysis_cache` table
- [ ] Add indexes for performance

### Phase 2: Cache Logic (Week 1-2)
- [ ] Implement `calculate_asset_hash()` function
- [ ] Implement `should_analyze_asset()` function
- [ ] Update `analyze_assets_with_cache()` in tier_processors.py
- [ ] Update asset update endpoints to recalculate hash

### Phase 3: Frontend (Week 2)
- [ ] Add "Force Refresh" checkbox
- [ ] Update API call to pass `force_refresh` parameter
- [ ] Add cache status indicator (e.g., "Using cached results for 2/3 assets")

### Phase 4: Monitoring & Metrics (Week 2-3)
- [ ] Add Grafana dashboard for cache hit rate
- [ ] Track cost savings in `llm_usage_logs`
- [ ] Add cache performance metrics

### Phase 5: Testing (Week 3)
- [ ] Unit tests for hash calculation
- [ ] Integration tests for cache logic
- [ ] E2E tests for force refresh
- [ ] Performance benchmarks

## Benefits

### Cost Savings
- **Scenario**: User re-analyzes same 10 assets 5 times
- **Without Cache**: 50 LLM calls × $1.50 = **$75**
- **With Cache**: 10 LLM calls × $1.50 = **$15**
- **Savings**: **$60 (80% reduction)**

### Performance Improvement
- **Without Cache**: 10 assets × 45s = **7.5 minutes**
- **With Cache**: Instant retrieval (< 1 second)
- **Improvement**: **450x faster** for cached assets

### User Experience
- Instant results for unchanged assets
- Clear indication when using cached data
- Option to force refresh when needed

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Hash calculation overhead | Minimal (~1ms per asset), indexed lookups |
| Cache invalidation bugs | Force refresh option, time-based expiration |
| Stale cached data | Hash includes ALL critical fields, detects changes |
| Storage growth | Add cleanup job for old cache entries (>90 days) |

## Metrics to Track

1. **Cache Hit Rate**: % of assets using cached results
2. **Cost Savings**: LLM costs avoided via caching
3. **Time Savings**: User wait time reduced
4. **Cache Size**: Number of cache entries
5. **Force Refresh Usage**: How often users override cache

## Future Enhancements

1. **Distributed cache**: Use Redis for cross-instance caching
2. **Predictive pre-warming**: Pre-analyze likely-to-be-requested assets
3. **Partial cache**: Cache individual gap results, not just entire asset analysis
4. **ML-based cache invalidation**: Predict when cache is likely stale

## References

- PR #1043: Async gap analysis auto-trigger
- ADR-024: TenantMemoryManager architecture
- `docs/guidelines/OBSERVABILITY_PATTERNS.md`: LLM usage tracking

---

**Estimated Implementation Time**: 2-3 weeks
**Estimated Cost Savings**: 60-80% reduction in LLM costs for re-analysis
**Estimated Performance Gain**: 450x faster for cached assets
