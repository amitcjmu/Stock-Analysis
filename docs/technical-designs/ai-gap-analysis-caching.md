# Simple AI Gap Analysis Status Tracking

**Status**: Design Proposal - Simplified
**Created**: 2025-01-13
**Updated**: 2025-01-13
**Author**: Claude Code
**Related PR**: #1043

## Problem Statement

AI gap analysis using Llama 4 is expensive and time-consuming:
- **Cost**: ~$0.50-$2.00 per 1000 assets analyzed
- **Time**: 30-60 seconds per asset
- **Current Behavior**: Re-analyzes assets even when already completed
- **Impact**: Unnecessary LLM costs and user wait time

**User Requirement**: "We should avoid costly unnecessary repetition of agent calls for the same data over and over again."

## Goals

1. **Track AI analysis completion**: Simple flag per asset to indicate AI analysis status
2. **Skip completed assets**: Don't re-run AI analysis if already completed successfully
3. **Allow manual re-analysis**: User can force re-analysis when needed
4. **Show appropriate UI**: Display AI-specific buttons only when AI analysis completed
5. **Delay questionnaire access**: Give users time to review gaps before proceeding
6. **Detect stale analysis**: Re-analyze if asset data changed after last analysis
7. **Ensure consistency**: Verify that status matches actual gap data

## Architecture Rationale

### Per-Asset Status (Not Per-Flow)

**Critical Design Decision**: The `ai_gap_analysis_status` column is added to the **`assets` table**, NOT a flow-specific table.

**Why Per-Asset**:
- Gaps are **per-asset globally**, not scoped to individual collection flows
- When AI analysis completes for an asset, **all collection flows** referencing that asset benefit
- `collection_flow_id` in the gaps table is for **tracking/display purposes**, not uniqueness scoping
- Avoids redundant AI analysis across multiple flows for the same asset

**Example**:
- Asset A analyzed in Collection Flow 1 → status=2, gaps persisted
- Collection Flow 2 references Asset A → **skips analysis** (status already 2)
- Both flows see the same AI-enhanced gaps for Asset A

### Consistency Verification

**Why Needed**: Status on `assets` table could become inconsistent with actual gaps in `collection_data_gaps` table.

**Verification Logic**: After marking status=2, verify that gaps with `confidence_score IS NOT NULL` exist for the asset (across **all** flows, not just current flow).

**Handles Edge Cases**:
- Job crashes after partial gap persistence
- Manual database modifications
- Race conditions in concurrent processing

### Stale Detection

**Why Needed**: Asset data may change after AI analysis, making cached results outdated.

**Detection Logic**: Compare `ai_gap_analysis_timestamp` with `asset.updated_at`:
- If `updated_at > ai_gap_analysis_timestamp` → asset changed after analysis → re-analyze
- Timestamp is set when status changes to 2 (analysis completes)
- Status reset to 0 and timestamp cleared on failure

## Solution Design

### 1. Add AI Analysis Status Tracking to Assets Table

**Simple status tracking** using status flag and timestamp in `assets` table:

```sql
-- Migration: Add AI gap analysis tracking columns to assets table
ALTER TABLE migration.assets
ADD COLUMN ai_gap_analysis_status INTEGER NOT NULL DEFAULT 0,
ADD COLUMN ai_gap_analysis_timestamp TIMESTAMP WITH TIME ZONE;

-- Create index for fast lookups
CREATE INDEX idx_assets_ai_analysis_status ON migration.assets(ai_gap_analysis_status);

-- Add comments explaining columns
COMMENT ON COLUMN migration.assets.ai_gap_analysis_status IS
'AI gap analysis status: 0 = not started, 1 = in progress, 2 = completed successfully';

COMMENT ON COLUMN migration.assets.ai_gap_analysis_timestamp IS
'Timestamp when AI gap analysis was last completed (status changed to 2). Used to detect stale analysis when compared with asset.updated_at.';
```

**Status Codes**:
- `0` = AI analysis not started (default)
- `1` = AI analysis in progress (job running)
- `2` = AI analysis completed and results persisted to database

**Timestamp Purpose**:
- Records when AI analysis completed (status changed to 2)
- Compared with `asset.updated_at` to detect stale analysis
- If `updated_at > ai_gap_analysis_timestamp`, asset data changed after analysis → re-analyze needed

### 2. Backend Logic Changes

#### Check Status Before Running AI Analysis

```python
# backend/app/api/v1/endpoints/collection_gap_analysis/analysis_endpoints/background_workers.py

async def process_gap_enhancement_job(
    job_id: str,
    collection_flow_id: UUID,
    selected_asset_ids: list,
    client_account_id: str,
    engagement_id: str,
    force_refresh: bool = False,  # New parameter for manual re-analysis
):
    """Background worker for comprehensive AI gap analysis.

    Skips assets with ai_gap_analysis_status = 2 unless force_refresh = True.
    """
    # Load assets
    stmt = select(Asset).where(
        Asset.id.in_([UUID(aid) for aid in selected_asset_ids]),
        Asset.client_account_id == UUID(client_account_id),
        Asset.engagement_id == UUID(engagement_id),
    )
    result = await db.execute(stmt)
    all_assets = result.scalars().all()

    # Filter assets based on AI analysis status and staleness
    if force_refresh:
        # User forced re-analysis - analyze all assets
        assets_to_analyze = all_assets
        logger.info(f"🔄 Force refresh enabled - analyzing all {len(all_assets)} assets")
    else:
        # Skip assets that already completed AI analysis (status = 2) AND aren't stale
        assets_to_analyze = []
        assets_skipped = 0
        assets_stale = 0

        for asset in all_assets:
            # Check if AI analysis completed
            if asset.ai_gap_analysis_status != 2:
                assets_to_analyze.append(asset)
                continue

            # Check if analysis is stale (asset updated after analysis)
            if (asset.ai_gap_analysis_timestamp and
                asset.updated_at and
                asset.updated_at > asset.ai_gap_analysis_timestamp):
                assets_to_analyze.append(asset)
                assets_stale += 1
                logger.debug(
                    f"📊 Asset {asset.id} marked for re-analysis - "
                    f"updated_at={asset.updated_at} > "
                    f"ai_analysis_timestamp={asset.ai_gap_analysis_timestamp}"
                )
            else:
                assets_skipped += 1

        logger.info(
            f"📊 AI analysis plan - "
            f"Analyze: {len(assets_to_analyze)} "
            f"(new: {len(assets_to_analyze) - assets_stale}, stale: {assets_stale}), "
            f"Skipped (cached): {assets_skipped}"
        )

    if not assets_to_analyze:
        logger.info("✅ All assets already have AI analysis - nothing to do")
        await update_job_state(
            job_id=job_id,
            status="completed",
            progress=100,
            message="All assets already analyzed"
        )
        return

    # Mark assets as in-progress (status = 1)
    for asset in assets_to_analyze:
        asset.ai_gap_analysis_status = 1
    await db.flush()

    try:
        # Run comprehensive AI analysis
        ai_result = await gap_service._run_tier_2_ai_analysis(
            assets=assets_to_analyze,
            collection_flow_id=str(collection_flow_id),
            db=db,
        )

        # Mark assets as completed (status = 2) with timestamp
        from datetime import datetime, timezone
        completion_time = datetime.now(timezone.utc)

        for asset in assets_to_analyze:
            asset.ai_gap_analysis_status = 2
            asset.ai_gap_analysis_timestamp = completion_time

        await db.commit()

        # Verify consistency: gaps with confidence_score should exist
        await verify_ai_gaps_consistency(assets_to_analyze, db)

        logger.info(
            f"✅ AI analysis completed for {len(assets_to_analyze)} assets "
            f"at {completion_time.isoformat()}"
        )

    except Exception as e:
        # Reset status to 0 on failure so analysis can be retried
        for asset in assets_to_analyze:
            asset.ai_gap_analysis_status = 0
            asset.ai_gap_analysis_timestamp = None
        await db.commit()

        logger.error(f"❌ AI analysis failed: {e}")
        raise


async def verify_ai_gaps_consistency(
    assets: List[Asset],
    db: AsyncSession
) -> None:
    """Verify that assets marked as AI-analyzed have gaps with confidence_score.

    This ensures data consistency across all collection flows, not just the current one.
    """
    from sqlalchemy import select, func
    from app.models.collection_data_gap import CollectionDataGap

    for asset in assets:
        # Check if gaps with AI enhancement exist for this asset (across ALL flows)
        stmt = select(func.count()).where(
            CollectionDataGap.asset_id == asset.id,
            CollectionDataGap.confidence_score.is_not(None)
        )
        result = await db.execute(stmt)
        ai_gaps_count = result.scalar()

        if ai_gaps_count == 0:
            logger.warning(
                f"⚠️ Consistency issue: Asset {asset.id} marked as AI-analyzed "
                f"(status=2) but has no gaps with confidence_score"
            )
        else:
            logger.debug(
                f"✅ Asset {asset.id} consistency verified - "
                f"{ai_gaps_count} AI-enhanced gaps found"
            )
```

#### Add force_refresh Parameter to API

```python
# backend/app/schemas/collection_gap_analysis.py

class AnalyzeGapsRequest(BaseModel):
    """Request schema for gap analysis enhancement."""

    gaps: Optional[List[DataGap]] = Field(
        None,
        description="Gaps from programmatic scan. If None, triggers comprehensive analysis."
    )
    selected_asset_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Asset UUIDs for gap analysis context"
    )
    force_refresh: bool = Field(
        False,
        description="Force re-analysis even if AI analysis already completed (status=2)"
    )
```

```python
# backend/app/api/v1/endpoints/collection_gap_analysis/analysis_endpoints/gap_analysis_handlers.py

async def analyze_gaps(
    flow_id: str,
    request_body: AnalyzeGapsRequest,
    background_tasks: BackgroundTasks,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """Enqueues background job for AI-powered gap enhancement."""

    # ... existing validation ...

    # Enqueue background task with force_refresh parameter
    background_tasks.add_task(
        process_gap_enhancement_job,
        job_id=job_id,
        collection_flow_id=collection_flow.id,
        selected_asset_ids=request_body.selected_asset_ids,
        client_account_id=str(context.client_account_id),
        engagement_id=str(context.engagement_id),
        force_refresh=request_body.force_refresh,  # Pass force_refresh flag
    )
```

### 3. Frontend UI Changes

#### Add Force Re-Analysis Button

```typescript
// src/components/collection/DataGapDiscovery.tsx

const DataGapDiscovery = ({ flowId, selectedAssetIds }) => {
  const [forceRefresh, setForceRefresh] = useState(false);
  const [hasAIAnalysis, setHasAIAnalysis] = useState(false);
  const [showQuestionnaireButton, setShowQuestionnaireButton] = useState(false);

  // Check if selected assets have AI analysis completed (status = 2)
  useEffect(() => {
    const checkAIStatus = async () => {
      // Query assets to check ai_gap_analysis_status
      const assets = await fetchAssets(selectedAssetIds);
      const allCompleted = assets.every(a => a.ai_gap_analysis_status === 2);
      setHasAIAnalysis(allCompleted);
    };
    checkAIStatus();
  }, [selectedAssetIds]);

  // Auto-trigger AI analysis (only for assets without AI analysis)
  useEffect(() => {
    if (gaps.length > 0 && !isAnalyzing && !enhancementProgress && scanSummary) {
      // Check if any asset needs AI analysis (status != 2)
      const needsAIAnalysis = gaps.some(gap => {
        // Check if gap's asset has AI analysis completed
        return !gap.confidence_score; // Heuristic gap without AI enhancement
      });

      if (needsAIAnalysis) {
        console.log('🚀 Auto-triggering AI-enhanced gap analysis');
        handleAnalyzeGapsAuto();
      }
    }
  }, [gaps, scanSummary, isAnalyzing, enhancementProgress]);

  const handleAnalyzeGapsAuto = async () => {
    try {
      setIsAnalyzing(true);

      const response = await collectionFlowApi.analyzeGaps(
        flowId,
        null, // Triggers comprehensive analysis
        selectedAssetIds,
        false // force_refresh = false (skip completed assets)
      );

      console.log('✅ AI enhancement job queued:', response.job_id);
    } catch (error) {
      console.error('❌ AI analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleForceReAnalysis = async () => {
    try {
      setIsAnalyzing(true);

      const response = await collectionFlowApi.analyzeGaps(
        flowId,
        null,
        selectedAssetIds,
        true // force_refresh = true (re-analyze all assets)
      );

      console.log('✅ Force re-analysis job queued:', response.job_id);
    } catch (error) {
      console.error('❌ Force re-analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Delay showing questionnaire button for 15-30 seconds
  useEffect(() => {
    if (gaps.length > 0 && !showQuestionnaireButton) {
      const timer = setTimeout(() => {
        setShowQuestionnaireButton(true);
      }, 20000); // 20 seconds delay

      return () => clearTimeout(timer);
    }
  }, [gaps]);

  return (
    <div>
      {/* Gap Analysis Status Message */}
      {scanSummary && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          {hasAIAnalysis ? (
            <p className="text-green-700">
              ✅ AI-enhanced gap analysis is complete.
              Review gaps below and accept/reject AI classifications.
            </p>
          ) : (
            <p className="text-blue-700">
              📊 Heuristic gap analysis is complete.
              AI enhancement {isAnalyzing ? 'is running' : 'will run automatically'}.
            </p>
          )}
        </div>
      )}

      {/* AI-Specific Action Buttons - Only show if AI analysis completed */}
      {hasAIAnalysis && (
        <div className="mb-4 flex gap-2">
          <button
            onClick={handleAcceptAIGaps}
            className="px-4 py-2 bg-green-600 text-white rounded"
          >
            ✓ Accept AI Classifications
          </button>
          <button
            onClick={handleRejectAIGaps}
            className="px-4 py-2 bg-red-600 text-white rounded"
          >
            ✗ Reject AI Classifications
          </button>
        </div>
      )}

      {/* Force Re-Analysis Button */}
      {hasAIAnalysis && (
        <button
          onClick={handleForceReAnalysis}
          disabled={isAnalyzing}
          className="mb-4 px-4 py-2 bg-yellow-600 text-white rounded"
        >
          🔄 Force Re-Analysis
        </button>
      )}

      {/* Gaps Table */}
      <DataGapsTable gaps={gaps} />

      {/* Proceed to Questionnaire Button - Delayed */}
      {showQuestionnaireButton && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
          <p className="text-sm text-yellow-800 mb-2">
            ⏱️ Please review the data gaps above before proceeding.
          </p>
          <button
            onClick={handleProceedToQuestionnaire}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg"
          >
            Continue to Questionnaire →
          </button>
        </div>
      )}
    </div>
  );
};
```

#### Update API Service

```typescript
// src/services/api/collection-flow/questionnaires.ts

async analyzeGaps(
  flowId: string,
  gaps: DataGap[] | null,
  selectedAssetIds: string[],
  forceRefresh: boolean = false // New parameter
): Promise<AnalyzeGapsResponse> {
  return this.post(`/collection/${flowId}/analyze-gaps`, {
    gaps,
    selected_asset_ids: selectedAssetIds,
    force_refresh: forceRefresh
  });
}
```

### 4. Database Migration

```python
# backend/alembic/versions/093_add_ai_gap_analysis_tracking_to_assets.py

"""Add AI gap analysis tracking columns to assets table

Revision ID: 093_ai_gap_tracking
Revises: 092_add_supported_versions_requirement_details
Create Date: 2025-01-13

Adds:
- ai_gap_analysis_status: Track completion status (0=not started, 1=in progress, 2=completed)
- ai_gap_analysis_timestamp: Track when analysis completed (for stale detection)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '093_ai_gap_tracking'
down_revision: Union[str, None] = '092_add_supported_versions_requirement_details'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add AI gap analysis tracking columns to assets table."""

    op.execute("""
        DO $$
        BEGIN
            -- Add ai_gap_analysis_status column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_status'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN ai_gap_analysis_status INTEGER NOT NULL DEFAULT 0;

                -- Add comment explaining status codes
                COMMENT ON COLUMN migration.assets.ai_gap_analysis_status IS
                'AI gap analysis status: 0 = not started, 1 = in progress, 2 = completed successfully. Per-asset, shared across all collection flows.';
            END IF;

            -- Add ai_gap_analysis_timestamp column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_timestamp'
            ) THEN
                ALTER TABLE migration.assets
                ADD COLUMN ai_gap_analysis_timestamp TIMESTAMP WITH TIME ZONE;

                -- Add comment explaining timestamp purpose
                COMMENT ON COLUMN migration.assets.ai_gap_analysis_timestamp IS
                'Timestamp when AI gap analysis was last completed (status changed to 2). Used to detect stale analysis when compared with asset.updated_at.';
            END IF;

            -- Create partial index for fast lookups (only active statuses)
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_ai_analysis_status'
            ) THEN
                CREATE INDEX idx_assets_ai_analysis_status
                ON migration.assets(ai_gap_analysis_status)
                WHERE ai_gap_analysis_status IN (1, 2);  -- Partial index for active statuses
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove AI gap analysis tracking columns from assets table."""

    op.execute("""
        DO $$
        BEGIN
            -- Drop index if exists
            IF EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_ai_analysis_status'
            ) THEN
                DROP INDEX migration.idx_assets_ai_analysis_status;
            END IF;

            -- Drop ai_gap_analysis_timestamp column if exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_timestamp'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN ai_gap_analysis_timestamp;
            END IF;

            -- Drop ai_gap_analysis_status column if exists
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assets'
                AND column_name = 'ai_gap_analysis_status'
            ) THEN
                ALTER TABLE migration.assets
                DROP COLUMN ai_gap_analysis_status;
            END IF;
        END $$;
    """)
```

## Implementation Plan

### Phase 1: Database Schema (Must-Have)
- [ ] Create migration `093_add_ai_gap_analysis_tracking_to_assets.py`
  - [ ] Add `ai_gap_analysis_status` INTEGER column (default 0)
  - [ ] Add `ai_gap_analysis_timestamp` TIMESTAMP column
  - [ ] Create partial index on `ai_gap_analysis_status` for statuses 1 and 2
  - [ ] Add column comments explaining purpose
- [ ] Run migration: `cd backend && alembic upgrade head`
- [ ] Verify columns and index created:
  ```sql
  \d+ migration.assets;  -- Check columns exist
  \di migration.*ai_analysis*;  -- Check index exists
  ```

### Phase 2: Backend Logic (Must-Have)
- [ ] Add `force_refresh` parameter to `AnalyzeGapsRequest` schema
- [ ] Update `process_gap_enhancement_job()`:
  - [ ] Check status and skip completed assets (status=2)
  - [ ] Add stale detection (compare `ai_gap_analysis_timestamp` with `asset.updated_at`)
  - [ ] Mark assets as status=1 when starting
  - [ ] Mark assets as status=2 with timestamp when completed
  - [ ] Reset status=0 and timestamp=None on failure
- [ ] Add `verify_ai_gaps_consistency()` function:
  - [ ] Query gaps with `confidence_score IS NOT NULL` for each asset
  - [ ] Log warnings if status=2 but no AI-enhanced gaps exist
  - [ ] Called after successful analysis completion
- [ ] Update `analyze_gaps()` endpoint to pass `force_refresh` parameter

### Phase 3: Frontend UI (Must-Have)
- [ ] Add `force_refresh` parameter to `analyzeGaps()` API call
- [ ] Check `ai_gap_analysis_status` to determine if AI analysis completed
- [ ] Show Accept/Reject buttons ONLY when status=2 (AI completed)
- [ ] Update status message based on AI completion:
  - [ ] "AI-enhanced gap analysis is complete" when status=2
  - [ ] "Heuristic gap analysis is complete. AI enhancement will run automatically" when status ≠ 2
- [ ] Add "Force Re-Analysis" button for manual re-triggering
- [ ] Delay questionnaire button by 20 seconds

### Phase 4: Testing (Must-Have)
- [ ] Test auto-trigger skips assets with status=2
- [ ] Test stale detection re-analyzes assets when `updated_at > ai_gap_analysis_timestamp`
- [ ] Test force refresh re-analyzes all assets
- [ ] Test consistency verification logs warnings for mismatches
- [ ] Test Accept/Reject buttons only appear when status=2
- [ ] Test status messages show correct text
- [ ] Test questionnaire button appears after 20-second delay
- [ ] Test timestamp is set correctly when analysis completes

### Phase 5: Background Cleanup Job (Should-Have)
- [ ] Create background job to reset stale status=1 entries
  - [ ] Query assets with status=1 and `updated_at` > 1 hour ago
  - [ ] Reset to status=0 and timestamp=None
  - [ ] Run hourly via scheduler
- [ ] Add monitoring for cleanup job execution

### Phase 6: Monitoring & Metrics (Should-Have)
- [ ] Add Grafana dashboard panels:
  - [ ] Cache hit rate (assets skipped / total assets)
  - [ ] Stale detection rate (assets re-analyzed due to staleness)
  - [ ] Force refresh usage rate
  - [ ] Consistency verification failure rate
- [ ] Track cost savings in `llm_usage_logs`:
  - [ ] Log "cache_hit" when asset skipped
  - [ ] Calculate savings = skipped_assets × avg_cost_per_asset
- [ ] Add structured logging:
  ```python
  logger.info(
      "AI analysis plan",
      extra={
          "flow_id": collection_flow_id,
          "total_assets": len(all_assets),
          "assets_to_analyze": len(assets_to_analyze),
          "assets_skipped": assets_skipped,
          "assets_stale": assets_stale,
          "force_refresh": force_refresh
      }
  )
  ```

## Benefits

### Cost Savings
- **Scenario**: User re-analyzes same 10 assets 5 times
- **Without Status Flag**: 50 LLM calls × $1.50 = **$75**
- **With Status Flag**: 10 LLM calls × $1.50 = **$15** (first time only)
- **Savings**: **$60 (80% reduction)** on repeat analysis

### User Experience
- Clear indication when AI analysis completed vs heuristic-only
- Accept/Reject buttons only shown when AI has classified gaps
- 20-second delay encourages gap review before proceeding
- Manual force re-analysis option when data changes

### Simplicity
- Single integer column, no complex hash calculations
- Status flag easy to understand and debug
- No separate cache table to maintain
- Works with existing gap persistence logic

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Asset data changes but status still 2 | User can manually force re-analysis |
| Status stuck at 1 (in-progress) if job crashes | Reset to 0 on exception, allow retry |
| User bypasses 20s delay | Acceptable - delay is UX guidance, not enforcement |
| Multiple assets, some completed some not | Filter logic analyzes only incomplete assets |

## Future Enhancements

1. **Data change detection**: Add `last_modified_at` timestamp to detect stale analysis
2. **Auto-expiration**: Reset status=2 to status=0 after 30 days
3. **Partial re-analysis**: Allow re-analysis of specific fields instead of entire asset
4. **Progress indicator**: Show per-asset progress during multi-asset analysis

## References

- PR #1043: Async gap analysis auto-trigger
- `backend/app/models/asset/models.py`: Asset model definition
- `backend/app/models/collection_data_gap.py`: Gap model with AI enhancement fields

---

## Implementation Estimates

**Total Implementation Time**: 3-5 days

**Phase Breakdown**:
- Phase 1 (Database): 0.5 day (migration + verification)
- Phase 2 (Backend): 1-2 days (logic + consistency verification)
- Phase 3 (Frontend): 1 day (UI + force refresh)
- Phase 4 (Testing): 1 day (comprehensive testing)
- Phase 5 (Cleanup Job): 0.5 day (optional, should-have)
- Phase 6 (Monitoring): 0.5-1 day (optional, should-have)

**Estimated Cost Savings**: 80% reduction in LLM costs for repeat analysis
**Complexity**: Low-Medium (adds timestamp + consistency verification to simple status flag)
**Risk Level**: Low (well-defined scope, clear rollback strategy)
