# Data Flow Analysis Report: Target Architecture Page

**Analysis Date:** 2025-10-29
**Previous Version:** 2024-07-29 (Placeholder Analysis)
**Status:** Scope Under Review - May Belong to Execute Phase

---

## Overview

The Target Architecture page was originally intended to capture and document the desired target cloud architecture for each application or wave. This includes cloud service selections, architecture patterns, and design decisions.

**IMPORTANT ARCHITECTURAL QUESTION:** This functionality may belong to the **Execute phase** rather than the Planning phase.

---

## Placement Discussion

### Option A: Target Architecture in Planning Phase

**Rationale:**

- Design before execution follows waterfall methodology
- Allows for cost estimation based on specific cloud services
- Enables resource allocation with architectural expertise requirements
- Provides complete migration plan before execution begins

**Challenges:**

- May create analysis paralysis
- Target architecture may change during execution
- Agile methodology favors iterative design

### Option B: Target Architecture in Execute Phase

**Rationale:**

- Aligns with agile/iterative methodology
- Design emerges as teams work on migration
- Allows for experimentation and adjustment
- More practical for cloud-native patterns (e.g., serverless)

**Challenges:**

- Cost estimation less precise without detailed architecture
- Resource requirements harder to predict
- May require rework if architecture decisions change

### Option C: Separate Architecture Phase

**Rationale:**

- Architecture is a distinct discipline
- Deserves its own workflow and governance
- Can occur in parallel with planning
- Supports architecture review boards

**Challenges:**

- Adds complexity to flow progression
- May delay migration if architecture not approved

---

## Current Implementation Status

### Frontend: `src/pages/plan/Target.tsx`

**Status:** Placeholder UI (no real implementation)

**Features Intended:**

- Cloud service selector (EC2, ECS, Lambda, etc.)
- Architecture diagram editor
- Best practices recommendations
- Cost calculator integration

### Backend: No Dedicated Implementation

**Observation:** No `target_architecture` table or service layer found in migrations 112-114.

**Possible Storage Location:**

- Could use `planning_flows.ui_state` JSONB for target architecture data
- Or create new migration for `target_architectures` table

---

## Recommendation: Defer to Execute Phase

### Reasoning

Based on assessment of the codebase and Planning flow implementation:

1. **Planning Phase Focus:** Wave sequencing, resource allocation, timeline, cost estimation
2. **Execute Phase Focus:** Detailed technical implementation, architecture decisions, testing, deployment
3. **Agile Alignment:** Target architecture emerges iteratively during execution
4. **Cost Estimation:** High-level estimates sufficient for planning (detailed architecture not required)

### Proposed Flow

1. **Assessment Phase:**
   - 6R strategy per application (Rehost, Replatform, Refactor, etc.)
   - High-level cloud readiness score

2. **Planning Phase:**
   - Wave planning (which applications migrate when)
   - Resource allocation (which roles needed)
   - Timeline generation (how long will it take)
   - Cost estimation (high-level budget)

3. **Execute Phase** (where target architecture belongs):
   - Detailed architecture design per application
   - Cloud service selection based on 6R strategy
   - Technical spike and proof-of-concept
   - Architecture review and approval
   - Implementation and testing

---

## If Target Architecture Stays in Planning Phase

### Required Implementation

#### Database Schema (New Migration)

```sql
CREATE TABLE migration.target_architectures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    planning_flow_id UUID NOT NULL REFERENCES migration.planning_flows(planning_flow_id) ON DELETE CASCADE,
    application_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,
    client_account_id INTEGER NOT NULL,
    engagement_id INTEGER NOT NULL,

    -- Architecture Details
    target_cloud_provider VARCHAR(50), -- AWS, Azure, GCP
    compute_pattern VARCHAR(50), -- EC2, ECS, EKS, Lambda, AppService, etc.
    architecture_diagram_url TEXT,
    architecture_notes TEXT,

    -- Service Selections (JSONB for flexibility)
    compute_services JSONB DEFAULT '[]'::jsonb,
    storage_services JSONB DEFAULT '[]'::jsonb,
    database_services JSONB DEFAULT '[]'::jsonb,
    network_services JSONB DEFAULT '[]'::jsonb,
    security_services JSONB DEFAULT '[]'::jsonb,

    -- Cost Impact
    estimated_monthly_cost NUMERIC(10,2),
    estimated_migration_cost NUMERIC(10,2),

    -- Status
    status VARCHAR(20) CHECK (status IN ('draft', 'under_review', 'approved', 'rejected')),
    approved_by UUID,
    approved_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

#### Service Layer Method

```python
async def design_target_architecture(
    self,
    planning_flow_id: UUID,
    application_id: UUID,
    architecture_details: Dict[str, Any]
) -> TargetArchitecture:
    """
    Create or update target architecture for application.

    May invoke ArchitectureDesignSpecialist agent for recommendations.
    """
```

#### Frontend Component

- Cloud service selector dropdown
- Architecture diagram upload
- Cost calculator integration
- Approval workflow UI

---

## Related Files

- **Frontend Page:** `src/pages/plan/Target.tsx` (placeholder)
- **No Backend Implementation:** Target architecture not in migrations 112-114

---

## Decision Required

**Action Item:** Product/architecture team needs to decide:

1. **Should target architecture be in Planning or Execute phase?**
2. **If Planning:** Allocate development effort for database schema, service layer, agent integration
3. **If Execute:** Remove `Target.tsx` from planning phase, add to Execute phase planning
4. **If Separate:** Create new Architecture phase between Planning and Execute

---

## Summary

The Target Architecture page is currently a **placeholder with no backend implementation**. Its placement in the Planning phase is **under architectural review**.

**Recommendation:** Move to Execute phase for agile/iterative design approach.

**Alternative:** If target architecture is deemed critical for planning (e.g., for cost estimation), implement as part of Planning phase with database schema and service layer.

**Current Priority:** LOW (defer until Planning phase frontend integration complete)
