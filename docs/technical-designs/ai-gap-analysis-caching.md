# Simple AI Gap Analysis Status Tracking

**Status**: Design Proposal - Simplified
**Created**: 2025-01-13
**Updated**: 2025-01-13
**Author**: Claude Code
**Related PR**: #1043

## Problem Statement

AI gap analysis using Llama 4 is expensive and time-consuming:
- **Cost**: ~$0.50-$2.00 per asset analyzed
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

## Solution Design

### 1. Add AI Analysis Status Flag to Assets Table

**Simple status tracking** using integer flag in `assets` table:

```sql
-- Migration: Add ai_gap_analysis_status column to assets table
ALTER TABLE migration.assets
ADD COLUMN ai_gap_analysis_status INTEGER NOT NULL DEFAULT 0;

-- Create index for fast lookups
CREATE INDEX idx_assets_ai_analysis_status ON migration.assets(ai_gap_analysis_status);

-- Add comment explaining status codes
COMMENT ON COLUMN migration.assets.ai_gap_analysis_status IS
'AI gap analysis status: 0 = not started, 1 = in progress, 2 = completed successfully';
```

**Status Codes**:
- `0` = AI analysis not started (default)
- `1` = AI analysis in progress (job running)
- `2` = AI analysis completed and results persisted to database

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

    # Filter assets based on AI analysis status
    if force_refresh:
        # User forced re-analysis - analyze all assets
        assets_to_analyze = all_assets
        logger.info(f"🔄 Force refresh enabled - analyzing all {len(all_assets)} assets")
    else:
        # Skip assets that already completed AI analysis (status = 2)
        assets_to_analyze = [
            asset for asset in all_assets
            if asset.ai_gap_analysis_status != 2
        ]
        assets_skipped = len(all_assets) - len(assets_to_analyze)

        logger.info(
            f"📊 AI analysis plan - "
            f"Analyze: {len(assets_to_analyze)}, "
            f"Skipped (already completed): {assets_skipped}"
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

        # Mark assets as completed (status = 2)
        for asset in assets_to_analyze:
            asset.ai_gap_analysis_status = 2
        await db.commit()

        logger.info(f"✅ AI analysis completed for {len(assets_to_analyze)} assets")

    except Exception as e:
        # Reset status to 0 on failure so analysis can be retried
        for asset in assets_to_analyze:
            asset.ai_gap_analysis_status = 0
        await db.commit()

        logger.error(f"❌ AI analysis failed: {e}")
        raise
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
# backend/alembic/versions/093_add_ai_gap_analysis_status_to_assets.py

"""Add ai_gap_analysis_status to assets table

Revision ID: 093_ai_gap_status
Revises: 092_add_supported_versions_requirement_details
Create Date: 2025-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '093_ai_gap_status'
down_revision: Union[str, None] = '092_add_supported_versions_requirement_details'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ai_gap_analysis_status column to assets table."""

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
                'AI gap analysis status: 0 = not started, 1 = in progress, 2 = completed successfully';
            END IF;

            -- Create index if it doesn't exist
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'assets'
                AND indexname = 'idx_assets_ai_analysis_status'
            ) THEN
                CREATE INDEX idx_assets_ai_analysis_status
                ON migration.assets(ai_gap_analysis_status);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove ai_gap_analysis_status column from assets table."""

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

            -- Drop column if exists
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

### Phase 1: Database Schema
- [ ] Create migration `093_add_ai_gap_analysis_status_to_assets.py`
- [ ] Run migration: `cd backend && alembic upgrade head`
- [ ] Verify column and index created

### Phase 2: Backend Logic
- [ ] Add `force_refresh` parameter to `AnalyzeGapsRequest` schema
- [ ] Update `process_gap_enhancement_job()` to check status and skip completed assets
- [ ] Update `analyze_gaps()` endpoint to pass `force_refresh` parameter
- [ ] Mark assets as status=1 when starting, status=2 when completed, status=0 on failure

### Phase 3: Frontend UI
- [ ] Add `force_refresh` parameter to `analyzeGaps()` API call
- [ ] Check `ai_gap_analysis_status` to determine if AI analysis completed
- [ ] Show Accept/Reject buttons ONLY when status=2 (AI completed)
- [ ] Update status message based on AI completion
- [ ] Add "Force Re-Analysis" button for manual re-triggering
- [ ] Delay questionnaire button by 20 seconds

### Phase 4: Testing
- [ ] Test auto-trigger skips assets with status=2
- [ ] Test force refresh re-analyzes all assets
- [ ] Test Accept/Reject buttons only appear when status=2
- [ ] Test status messages show correct text
- [ ] Test questionnaire button appears after 20-second delay

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

**Estimated Implementation Time**: 2-3 days
**Estimated Cost Savings**: 80% reduction in LLM costs for repeat analysis
**Complexity**: Low (single column, simple status checks)
