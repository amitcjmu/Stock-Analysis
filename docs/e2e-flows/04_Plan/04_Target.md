# Data Flow Analysis Report: Target Architecture Page

**Analysis Date:** 2025-11-10
**Previous Version:** 2025-10-29 (Architectural Review)
**Status:** ARCHITECTURAL DECISION - RECOMMENDED FOR EXECUTE PHASE
**Decision Date:** 2025-11-10

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

## Architectural Decision (November 2025)

**RECOMMENDATION: Move Target Architecture to Execute Phase**

### Rationale

After comprehensive review of the Planning Flow implementation (November 2025), the following factors support moving target architecture to the Execute phase:

1. **Planning Flow Completeness**: Planning phase successfully provides:
   - Wave planning with dependency analysis
   - Resource allocation with role-based staffing
   - Timeline generation with critical path
   - Cost estimation with contingency planning
   - **Conclusion**: High-level planning is sufficient without detailed architecture

2. **Agile Methodology Alignment**:
   - Current implementation follows iterative, phased approach
   - Target architecture naturally emerges during execution
   - Allows for experimentation and adjustment based on real-world constraints
   - Aligns with cloud-native best practices (infrastructure as code, DevOps)

3. **Assessment Phase Coverage**:
   - 6R strategy already determined per application (Rehost, Replatform, Refactor, etc.)
   - High-level cloud readiness assessed
   - Sufficient for cost estimation and resource planning

4. **Execute Phase Natural Fit**:
   - Detailed technical implementation requires architecture decisions
   - Architecture design, technical spikes, POCs belong in execution
   - Architecture review and approval workflow fits execution gate checks

### Implementation Actions

1. ✅ **Keep `Target.tsx` as placeholder** in Planning phase (low priority)
2. ⚠️ **Create Target Architecture module** in Execute phase (future work)
3. ⚠️ **Document transition** in Execute phase E2E flow documentation
4. ✅ **Update Planning documentation** to clarify scope boundaries (this document)

### Planning Phase Scope (Final Definition)

The Planning phase focuses on **WHEN and HOW MUCH**, NOT **HOW**:

- **WHEN**: Timeline generation (which applications migrate when, wave sequencing)
- **HOW MUCH**: Resource allocation (how many people, what roles, what cost)
- **NOT HOW**: Detailed architecture (which cloud services, architecture patterns, technical design)

### Execute Phase Scope (Future Definition)

The Execute phase will focus on **HOW**, including:

- Detailed architecture design per application
- Cloud service selection based on 6R strategy
- Technical spike and proof-of-concept
- Architecture review and approval
- Implementation, testing, deployment

---

## Summary

The Target Architecture page is currently a **placeholder with no backend implementation**. Its placement in the Planning phase is **under architectural review**.

**Recommendation:** Move to Execute phase for agile/iterative design approach.

**Alternative:** If target architecture is deemed critical for planning (e.g., for cost estimation), implement as part of Planning phase with database schema and service layer.

**Current Priority:** LOW (defer until Planning phase frontend integration complete)
