# 6R Analysis Frontend Current State - Phase 1 Documentation

**Status**: Phase 1 Complete - Deprecation Warnings Added
**Date**: 2025-10-28
**Issue**: #837 - Assessment Flow MFO Migration Phase 1
**Parent Issue**: #611 - Assessment Flow Complete

---

## Overview

This document captures the current state of the 6R Analysis frontend implementation as part of Phase 1 of the Assessment Flow MFO Migration. This serves as a reference for the migration process documented in `/docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md`.

---

## API Client

### Primary API Client
- **File**: `/src/lib/api/sixr.ts`
- **Class**: `SixRApiClient`
- **Export**: `sixrApi` (singleton instance)
- **Status**: ⚠️ DEPRECATED (Phase 1) - Warnings added

### Deprecation Implementation
- Constructor now logs deprecation warning on first instantiation
- Warning appears once per page load in browser console
- Includes migration path and timeline information
- References migration plan and related issues

### API Endpoints Used
All endpoints are under `/6r/*` prefix (will be replaced with `/assessment-flow/*`):

1. **Analysis Management**:
   - `POST /6r/analyze` - Create new analysis
   - `GET /6r/{analysisId}` - Get analysis status
   - `PUT /6r/{analysisId}/parameters` - Update parameters
   - `POST /6r/{analysisId}/questions` - Submit qualifying questions
   - `POST /6r/{analysisId}/iterate` - Iterate analysis
   - `DELETE /6r/{analysisId}` - Delete analysis
   - `POST /6r/{analysisId}/archive` - Archive analysis

2. **Recommendations**:
   - `GET /6r/{analysisId}/recommendation` - Get recommendation
   - `GET /6r/{analysisId}/questions` - Get qualifying questions

3. **Bulk Operations**:
   - `POST /6r/bulk` - Create bulk analysis
   - `GET /6r/bulk` - List bulk jobs
   - `GET /6r/bulk/{jobId}/results` - Get job results
   - `GET /6r/bulk/summary` - Get bulk summary
   - `POST /6r/bulk/{jobId}/{action}` - Control job (start/pause/cancel/retry)
   - `DELETE /6r/bulk/{jobId}` - Delete job

4. **Export**:
   - `POST /6r/export` - Export analyses (CSV/PDF/JSON)
   - `POST /6r/bulk/{jobId}/export` - Export bulk results

5. **Listing**:
   - `GET /6r/` - List all analyses (paginated)

6. **Inline Gap Filling** (PR #816):
   - `POST /sixr-analyses/{analysisId}/inline-answers` - Submit inline answers

---

## Components Using sixrApi

### Direct Usage (3 files)

1. **`/src/pages/assess/Treatment.tsx`**
   - Primary treatment page
   - Creates new 6R analyses
   - Displays recommendations
   - Handles user acceptance of strategies
   - **Migration Priority**: HIGH (core user flow)

2. **`/src/hooks/useSixRAnalysis.ts`**
   - React Query hook for analysis data
   - Manages polling and state
   - Used by multiple components
   - **Migration Priority**: HIGH (shared hook)

3. **`/src/hooks/__tests__/useSixRAnalysis.test.ts`**
   - Unit tests for the hook
   - **Migration Priority**: MEDIUM (update after hook migration)

### Imports via Re-exports (14 additional files)

4. **`/src/pages/assessment/[flowId]/sixr-review.tsx`**
   - Review page for 6R recommendations
   - Displays detailed analysis results
   - **Migration Priority**: HIGH (core review flow)

5. **`/src/hooks/useApplications.ts`**
   - Application data management
   - May import types or utilities
   - **Migration Priority**: MEDIUM

6. **`/src/components/sixr/Tier1GapFillingModal.tsx`**
   - Modal for inline gap filling (PR #816)
   - **Migration Priority**: MEDIUM

7. **`/src/components/lazy/routes/LazyRoutes.tsx`**
   - Route definitions with lazy loading
   - **Migration Priority**: LOW (routing only)

8. **`/src/lib/api/index.ts`**
   - API client exports
   - **Migration Priority**: HIGH (central export)

9. **`/src/hooks/assessment/useSixRStatistics.ts`**
   - Statistics hook for 6R data
   - **Migration Priority**: MEDIUM

10. **`/src/components/lazy/components/LazyComponents.tsx`**
    - Component lazy loading definitions
    - **Migration Priority**: LOW

11. **`/src/components/assessment/index.ts`**
    - Assessment component exports
    - **Migration Priority**: MEDIUM

12. **`/src/components/assessment/sixr-review/SixRAppDecisionSummary.tsx`**
    - Decision summary component
    - **Migration Priority**: MEDIUM

13. **`/src/components/assessment/sixr-review/SixROverallStats.tsx`**
    - Overall statistics display
    - **Migration Priority**: MEDIUM

14. **`/src/types/api/assessment.ts`**
    - Type definitions
    - **Migration Priority**: HIGH (shared types)

15. **`/src/types/api/decommission.ts`**
    - Decommission types
    - **Migration Priority**: LOW

16. **`/src/types/api/modernize.ts`**
    - Modernization types
    - **Migration Priority**: LOW

17. **`/src/utils/assessment/sixrHelpers.ts`**
    - Utility functions for 6R analysis
    - **Migration Priority**: MEDIUM

---

## Related Components (sixr-prefixed, not using API directly)

### sixr-review Components (7 files)
Located in `/src/components/assessment/sixr-review/`:

1. **`SixRActionButtons.tsx`**
   - Action buttons for review workflow

2. **`SixROverallStats.tsx`**
   - Overall statistics display

3. **`SixRMainTabs.tsx`**
   - Tab navigation for review

4. **`SixRAppDecisionSummary.tsx`**
   - Per-application decision summary

5. **`SixRStatusAlert.tsx`**
   - Status alerts and notifications

6. **`__tests__/SixRReviewModularization.test.tsx`**
   - Component tests

### Other sixr Components (3 files)

7. **`/src/components/discovery/inventory/components/SixRRecommendations.tsx`**
   - Recommendations display in discovery

8. **`/src/components/assessment/SixRDecisionRationale.tsx`**
   - Decision rationale display

9. **`/src/components/assessment/SixRStrategyMatrix.tsx`**
   - Strategy matrix visualization

### Pages (2 files)

10. **`/src/pages/assessment/[flowId]/sixr-review.tsx`**
    - Main review page

11. **`/src/pages/planning/SixRAnalysis.tsx`**
    - Planning integration page

---

## TypeScript Types and Interfaces

### From sixr.ts

```typescript
// Core Analysis Types
export interface SixRAnalysisResponse {
  analysis_id: number;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'requires_input';
  current_iteration: number;
  applications: Array<{id: number}>;
  parameters: SixRParameters;
  qualifying_questions: QualifyingQuestion[];
  recommendation?: SixRRecommendation;
  progress_percentage: number;
  estimated_completion?: string;
  created_at: string;
  updated_at: string;
  tier1_gaps_by_asset?: Record<string, Tier1GapDetail[]>;
  retry_after_inline?: boolean;
}

// Request Types
export interface CreateAnalysisRequest {
  application_ids: string[]; // UUIDs
  parameters?: Partial<SixRParameters>;
  queue_name?: string;
}

export interface UpdateParametersRequest {
  parameters: SixRParameters;
  trigger_reanalysis?: boolean;
}

export interface SubmitQuestionsRequest {
  responses: QuestionResponse[];
  is_partial?: boolean;
}

export interface IterateAnalysisRequest {
  parameters?: Partial<SixRParameters>;
  additional_responses?: QuestionResponse[];
  iteration_notes?: string;
}

// Inline Gap Filling (PR #816)
export interface Tier1GapDetail {
  field_name: string;
  display_name: string;
  reason: string;
  tier: number;
  priority: number;
}

export interface InlineAnswersRequest {
  asset_id: string;
  answers: Record<string, string>;
}

export interface InlineAnswersResponse {
  success: boolean;
  analysis_id: string;
  asset_id: string;
  fields_updated: string[];
  can_proceed: boolean;
  remaining_tier1_gaps: number;
}

// Bulk Operations
export interface BulkAnalysisRequest {
  name: string;
  description?: string;
  application_ids: string[];
  priority: 'low' | 'medium' | 'high' | 'urgent';
  parameters?: {
    parallel_limit: number;
    retry_failed: boolean;
    auto_approve_high_confidence: boolean;
    confidence_threshold: number;
  };
}

export interface AnalysisFilters {
  status?: string;
  application_id?: string;
  created_after?: string;
  created_before?: string;
  limit?: number;
  offset?: number;
}

export interface SixRAnalysisListResponse {
  analyses: SixRAnalysisResponse[];
  total_count: number;
  page: number;
  page_size: number;
}
```

### Types Imported from Components

From `/src/components/sixr`:
- `QuestionResponse`
- `AnalysisProgressType`
- `BulkAnalysisResult`
- `BulkAnalysisSummary`
- `SixRParameters`
- `QualifyingQuestion`
- `SixRRecommendation`
- `AnalysisHistoryItem`
- `BulkAnalysisJob`

---

## WebSocket Usage

### Current Implementation
- **Class**: `WebSocketManager` (internal to sixr.ts)
- **Base URL**: Derived from `getWsBaseUrl()` function
- **Endpoints**:
  - `/ws/6r/{analysisId}` - Real-time analysis updates
  - `/ws/6r/bulk/{jobId}` - Bulk job progress

### ⚠️ CRITICAL ARCHITECTURAL VIOLATION
**WebSocket usage violates coding-agent-guide.md guidelines**:
- Banned pattern: `WebSocket | new WebSocket | ws://`
- Required: HTTP polling ONLY
- Railway deployment does NOT support WebSockets

### Migration Requirements
1. Remove all WebSocket code from Assessment Flow implementation
2. Use HTTP polling with React Query `refetchInterval`
3. Follow pattern from Discovery Flow (5s active/15s waiting)

---

## State Management

### React Query Integration
- Analysis state managed via `useSixRAnalysis` hook
- Polling for status updates (should be HTTP polling, not WebSocket)
- Cache invalidation on mutations

### Local State
- Analysis parameters stored in component state
- Form state for qualifying questions
- UI state for modals and wizards

---

## Data Flow

### Current Flow (To Be Replaced)
```
User Action → Treatment.tsx → sixrApi → /6r/* endpoints → 6R Analysis Tables
                     ↓
              useSixRAnalysis hook → React Query → Component Re-render
```

### Future Flow (Assessment Flow)
```
User Action → Treatment.tsx → assessmentFlowApi → /assessment-flow/* endpoints
                     ↓                                    ↓
              useAssessmentFlow hook              Master Flow Orchestrator
                     ↓                                    ↓
              React Query → Component          Master + Child Tables
                     ↓                          (Two-table pattern)
              Component Re-render
```

---

## Known Issues and Tech Debt

### Issue #813
- Changed `application_ids` from `number[]` to `string[]` (UUIDs)
- Backend serves different data structure than frontend expects
- Field name mismatches between frontend and backend

### Issue #814
- Backend returns paginated response, frontend expects array
- Status value mapping required between backend/frontend
- GET /6r/ used instead of /6r/history

### Issue #816 (PR #816)
- Two-tier inline gap-filling feature
- Adds `tier1_gaps_by_asset` to analysis response
- New endpoint: `POST /sixr-analyses/{analysisId}/inline-answers`

### WebSocket Usage
- Violates architectural guidelines (ADR-006)
- Not compatible with Railway deployment
- Should be replaced with HTTP polling

### Field Naming
- Some camelCase usage in types (legacy)
- Should be migrated to snake_case per CLAUDE.md

---

## Migration Checklist (Phase 2-5)

### Phase 2: Backend Assessment Flow Enable
- [ ] Enable `/assessment-flow/*` endpoints
- [ ] Create MFO integration layer
- [ ] Implement two-table pattern
- [ ] Remove WebSocket dependencies

### Phase 3: Frontend Migration
- [ ] Create `assessmentFlowApi` client
- [ ] Migrate `Treatment.tsx` to use new API
- [ ] Create `useAssessmentFlow` hook
- [ ] Update all component imports
- [ ] Remove WebSocket code
- [ ] Implement HTTP polling

### Phase 4: Backend Code Removal
- [ ] Delete `/6r/*` endpoints
- [ ] Remove 6R Analysis models
- [ ] Remove 6R Analysis services
- [ ] Migrate strategy crew to Assessment Flow
- [ ] Create database migration to drop tables

### Phase 5: Frontend Code Removal
- [ ] Delete `sixr.ts` API client
- [ ] Delete `useSixRAnalysis.ts` hook
- [ ] Remove `sixr` components directory
- [ ] Update all imports and references
- [ ] Remove test files

---

## Success Criteria

### Phase 1 (Current)
- [x] Deprecation warnings added to `sixrApi`
- [x] All components using `sixrApi` documented
- [x] Current state documentation created
- [ ] Warnings visible in browser console (pending verification)

### Overall Migration Success
- [ ] Zero references to `sixrApi` in codebase
- [ ] All 6R functionality working via Assessment Flow
- [ ] MFO integration complete
- [ ] Two-table pattern implemented
- [ ] HTTP polling only (no WebSockets)
- [ ] All tests passing

---

## Resources

### Documentation
- Migration Plan: `/docs/planning/ASSESSMENT_FLOW_MFO_MIGRATION_PLAN.md`
- ADR-006: Master Flow Orchestrator
- ADR-012: Flow Status Management Separation
- Coding Guide: `/docs/analysis/Notes/coding-agent-guide.md`
- CLAUDE.md: Project guidelines

### Issues
- #837: Assessment Flow MFO Migration Phase 1 (this phase)
- #611: Assessment Flow Complete (parent issue)
- #813: Application IDs UUID migration
- #814: Backend/frontend data structure mismatch
- #816: Two-tier inline gap-filling

---

**Document Owner**: Frontend Team
**Last Updated**: 2025-10-28
**Next Review**: After Phase 2 completion
