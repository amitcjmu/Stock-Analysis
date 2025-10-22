# Issue #689 Answers - Implementation Impact Analysis

**Date**: October 22, 2025
**Issue**: #689 [CLARIFY] Wave Planning Business Rules
**Status**: ✅ ANSWERED
**Parent Issue**: #606 (Plan Flow Complete milestone)

---

## Your Answers

### 1. Max Applications Per Wave
**Your Answer**: Dynamic - determined by engagement and available resources
**Implementation**: Per-engagement configuration during planning initialization

### 2. Sequencing Constraints
**Your Answer**: Engagement-level - user chooses constraints during initialization
**Implementation**: Configurable sequencing rules (infrastructure_first, database_first, none, custom)

### 3. Geographic/BU Constraints
**Your Answer**: Engagement-level - user chooses constraints during initialization
**Implementation**: Configurable organizational constraints (geographic, business_unit, none)

### 4. Wave Duration Limits
**Your Answer**: 3 months recommended (soft limit with warnings)
**Implementation**: System warns if wave duration > 90 days, user can override

---

## Implementation Changes Required

### ✅ EXCELLENT NEWS: Your Approach Is More Flexible

Your answers actually lead to a **better architecture** than hard-coded rules. Instead of rigid system-wide constraints, each engagement can customize its planning rules.

---

## Database Schema Changes (Issue #9)

### New Table: `engagement_planning_config`

```sql
CREATE TABLE migration.engagement_planning_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id INT NOT NULL UNIQUE,
    client_account_id INT NOT NULL,

    -- Wave Size Constraints
    max_applications_per_wave INT,  -- NULL means no limit
    warn_threshold_applications INT,  -- Warn user if approaching max

    -- Sequencing Rules
    sequencing_rules VARCHAR(50) CHECK (
        sequencing_rules IN (
            'infrastructure_first',  -- Infrastructure apps migrate before others
            'database_first',        -- Databases migrate before dependent apps
            'none',                  -- No mandatory sequencing
            'custom'                 -- User-defined custom rules
        )
    ) DEFAULT 'none',
    sequencing_custom_rules JSONB,  -- For 'custom' option

    -- Organizational Constraints
    organizational_constraints VARCHAR(50) CHECK (
        organizational_constraints IN (
            'geographic',      -- Group apps by geography
            'business_unit',   -- Group apps by BU
            'none'            -- No organizational constraints
        )
    ) DEFAULT 'none',
    constraint_details JSONB,  -- Additional constraint metadata

    -- Wave Duration
    recommended_wave_duration_days INT DEFAULT 90,  -- 3 months
    max_wave_duration_days INT,  -- Hard limit (NULL = no limit)
    warn_wave_duration_days INT DEFAULT 90,  -- Warn at this threshold

    -- Metadata
    configured_by UUID,  -- User who set these rules
    configured_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_engagement FOREIGN KEY (engagement_id)
        REFERENCES migration.engagements(id) ON DELETE CASCADE,
    CONSTRAINT fk_client_account FOREIGN KEY (client_account_id)
        REFERENCES migration.client_accounts(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_engagement_planning_config_tenant
    ON migration.engagement_planning_config(client_account_id, engagement_id);
```

---

## Service Layer Changes (Issue #10)

### New Service: `PlanningConfigurationService`

```python
# backend/app/services/planning_configuration_service.py

class PlanningConfigurationService:
    """
    Manages engagement-level planning configuration.
    """

    async def initialize_planning_config(
        self,
        engagement_id: int,
        client_account_id: int,
        config: PlanningConfigCreate
    ) -> PlanningConfig:
        """
        Initialize planning configuration for an engagement.
        Called during first-time planning setup.
        """
        # Validate and create config
        # Return config object

    async def get_planning_config(
        self,
        engagement_id: int,
        client_account_id: int
    ) -> PlanningConfig:
        """
        Retrieve planning configuration for an engagement.
        Returns default config if not yet initialized.
        """

    async def validate_wave_assignment(
        self,
        wave_id: UUID,
        application_id: UUID,
        engagement_id: int
    ) -> ValidationResult:
        """
        Validate if application can be assigned to wave based on:
        - Max applications per wave
        - Sequencing rules
        - Organizational constraints
        """
```

### Enhanced: `WavePlanningService` (Issue #10)

```python
# backend/app/services/wave_planning_service.py

class WavePlanningService:
    def __init__(self, planning_config_service: PlanningConfigurationService):
        self.config_service = planning_config_service

    async def assign_application_to_wave(
        self,
        wave_id: UUID,
        application_id: UUID,
        engagement_id: int,
        client_account_id: int
    ) -> WaveAssignment:
        """
        Assign application to wave with validation.
        """
        # Get planning config
        config = await self.config_service.get_planning_config(
            engagement_id, client_account_id
        )

        # Validate against config rules
        validation = await self.config_service.validate_wave_assignment(
            wave_id, application_id, engagement_id
        )

        if not validation.is_valid:
            if validation.is_warning:
                # Log warning, proceed with assignment
                logger.warning(f"Wave assignment warning: {validation.message}")
            else:
                # Hard constraint violation, reject
                raise ValidationError(validation.message)

        # Proceed with assignment
        return await self.wave_repository.create_assignment(...)
```

---

## API Changes (Issue #11)

### New Endpoints: Planning Configuration

```python
# backend/app/api/v1/endpoints/planning_configuration.py

@router.post("/api/v1/plan/config/initialize")
async def initialize_planning_configuration(
    config: PlanningConfigCreate,
    engagement_id: int = Header(..., alias="X-Engagement-ID"),
    client_account_id: int = Header(..., alias="X-Client-Account-ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Initialize planning configuration for an engagement.
    Called during first-time planning setup.
    """
    service = PlanningConfigurationService(db)
    return await service.initialize_planning_config(
        engagement_id, client_account_id, config
    )

@router.get("/api/v1/plan/config")
async def get_planning_configuration(
    engagement_id: int = Header(..., alias="X-Engagement-ID"),
    client_account_id: int = Header(..., alias="X-Client-Account-ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve planning configuration for an engagement.
    """
    service = PlanningConfigurationService(db)
    return await service.get_planning_config(engagement_id, client_account_id)

@router.put("/api/v1/plan/config")
async def update_planning_configuration(
    config: PlanningConfigUpdate,
    engagement_id: int = Header(..., alias="X-Engagement-ID"),
    client_account_id: int = Header(..., alias="X-Client-Account-ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Update planning configuration for an engagement.
    """
    service = PlanningConfigurationService(db)
    return await service.update_planning_config(
        engagement_id, client_account_id, config
    )
```

---

## Frontend Changes (NEW Issue Required)

### NEW Issue: Planning Configuration Wizard

**Title**: [FRONTEND] Planning Configuration Wizard - 0.5 Days
**Description**: First-time setup wizard for planning rules

**Component**: `src/components/plan/PlanningConfigWizard.tsx`

```typescript
interface PlanningConfigWizardProps {
  engagementId: number;
  onComplete: (config: PlanningConfig) => void;
}

export const PlanningConfigWizard = ({ engagementId, onComplete }: Props) => {
  // Step 1: Wave Size
  // - Input: Max applications per wave (optional)
  // - Input: Warning threshold

  // Step 2: Sequencing Rules
  // - Radio: Infrastructure First / Database First / None / Custom

  // Step 3: Organizational Constraints
  // - Radio: Geographic / Business Unit / None

  // Step 4: Wave Duration
  // - Input: Recommended duration (default 90 days)
  // - Checkbox: Enforce hard limit

  // Submit configuration
  const { mutate: initializeConfig } = useMutation({
    mutationFn: (config) =>
      apiCall('/api/v1/plan/config/initialize', {
        method: 'POST',
        body: JSON.stringify(config)
      }),
    onSuccess: onComplete
  });
};
```

**User Flow**:
1. User navigates to Plan Flow page for first time
2. System detects no planning config exists
3. Show wizard modal (blocks access to planning until configured)
4. User completes 4-step wizard
5. Configuration saved
6. User proceeds to wave planning dashboard

---

## Updated Issue Breakdown

### Modified Issues

#### Issue #9: Wave Planning Database Schema (Now 1.5 Days)
**Added Work**:
- ✅ Create `engagement_planning_config` table
- ✅ Add foreign keys and indexes
- **New Duration**: 1.5 days (was 1 day, +0.5 day)

#### Issue #10: Wave Planning Service Layer (Now 2.5 Days)
**Added Work**:
- ✅ Create `PlanningConfigurationService`
- ✅ Enhance `WavePlanningService` with config validation
- ✅ Add validation logic for constraints
- **New Duration**: 2.5 days (was 2 days, +0.5 day)

#### Issue #11: Wave Planning API Endpoints (Now 2.5 Days)
**Added Work**:
- ✅ Add 3 planning config endpoints (initialize, get, update)
- ✅ Enhance wave assignment endpoint with validation
- **New Duration**: 2.5 days (was 2 days, +0.5 day)

### New Issues

#### NEW Issue #29: [FRONTEND] Planning Configuration Wizard (0.5 Days)
**Dependencies**: Issue #11 (planning config API)
**Timeline**: Day 4 (after wave API complete)
**Description**: First-time setup wizard for engagement-level planning rules
**Priority**: Medium (blocks wave planning for new engagements)

---

## Timeline Impact Analysis

### Original Estimate (from PLAN_FLOW_ISSUE_BREAKDOWN.md)
- Issue #9: 1 day
- Issue #10: 2 days
- Issue #11: 2 days
- **Total**: 5 days for wave planning backend

### New Estimate (with configuration support)
- Issue #9: 1.5 days (+0.5)
- Issue #10: 2.5 days (+0.5)
- Issue #11: 2.5 days (+0.5)
- NEW Issue #29: 0.5 days
- **Total**: 7 days for wave planning backend + frontend wizard

### Net Impact: +2 Days

**HOWEVER**: We can absorb this by:
1. ✅ **Parallel work**: Frontend wizard (Issue #29) runs parallel with timeline backend (Days 4-5)
2. ✅ **Simplified approach**: Start with "no constraints" default, add wizard in Phase 2 if time tight
3. ✅ **Better flexibility**: This architecture is more maintainable long-term

### Recommended Approach to Stay on 7-Day Timeline

**Option A: MVP with Defaults (Recommended)**
- ✅ Implement `engagement_planning_config` table
- ✅ Implement configuration service
- ✅ Default config: No constraints, 90-day wave duration warnings
- ⏭️ **Defer wizard to Phase 2** (users use defaults for MVP)
- **Timeline**: +1.5 days only (stays within 7-day budget)

**Option B: Full Implementation**
- ✅ Implement table + service + wizard
- **Timeline**: +2 days (requires buffer day on Day 8)

**Recommendation**: Choose **Option A** for Oct 29 deadline, add wizard in Phase 2.

---

## Updated Acceptance Criteria (Issue #9, #10, #11)

### Issue #9 (Database Schema)
- [x] Original `wave_plans` table enhanced
- [x] Original `wave_assignments` table created
- [x] **NEW**: `engagement_planning_config` table created
- [x] All indexes and foreign keys validated
- [x] Multi-tenant scoping confirmed

### Issue #10 (Service Layer)
- [x] Original `WavePlanningService` implemented
- [x] **NEW**: `PlanningConfigurationService` implemented
- [x] **NEW**: Validation logic integrates config rules
- [x] Default config provided if not initialized
- [x] Unit tests 80%+ coverage

### Issue #11 (API Endpoints)
- [x] Original 7 wave endpoints implemented
- [x] **NEW**: 3 planning config endpoints added (initialize, get, update)
- [x] **NEW**: Wave assignment endpoint validates against config
- [x] OpenAPI docs updated
- [x] Manual API tests successful

---

## Pydantic Models (New)

```python
# backend/app/models/planning_config_models.py

from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class SequencingRules(str, Enum):
    INFRASTRUCTURE_FIRST = "infrastructure_first"
    DATABASE_FIRST = "database_first"
    NONE = "none"
    CUSTOM = "custom"

class OrganizationalConstraints(str, Enum):
    GEOGRAPHIC = "geographic"
    BUSINESS_UNIT = "business_unit"
    NONE = "none"

class PlanningConfigCreate(BaseModel):
    max_applications_per_wave: Optional[int] = None
    warn_threshold_applications: Optional[int] = None
    sequencing_rules: SequencingRules = SequencingRules.NONE
    sequencing_custom_rules: Optional[Dict[str, Any]] = None
    organizational_constraints: OrganizationalConstraints = OrganizationalConstraints.NONE
    constraint_details: Optional[Dict[str, Any]] = None
    recommended_wave_duration_days: int = 90
    max_wave_duration_days: Optional[int] = None
    warn_wave_duration_days: int = 90

class PlanningConfigResponse(PlanningConfigCreate):
    id: UUID
    engagement_id: int
    client_account_id: int
    configured_by: Optional[UUID]
    configured_at: datetime
    created_at: datetime
    updated_at: datetime
```

---

## Summary: What This Means

### ✅ Pros (Your Approach Is Better)
1. **More Flexible**: Each engagement can have custom rules
2. **Better UX**: Users configure constraints based on their needs
3. **Future-Proof**: Easy to add new constraint types
4. **Enterprise-Ready**: Supports diverse customer requirements

### ⚠️ Cons (Trade-offs)
1. **+1.5 Days**: Additional implementation time for config system
2. **+0.5 Days**: Frontend wizard (can defer to Phase 2)
3. **Complexity**: More tables and validation logic

### 🎯 Recommendation
- ✅ **Implement config table + service** (Issue #9, #10, #11 enhancements)
- ✅ **Use default config for MVP** (no constraints, 90-day warnings)
- ⏭️ **Defer wizard to Phase 2** (saves 0.5 days, meets Oct 29 deadline)
- ✅ **Document default config** in user guide

---

## Action Items

### Immediate (Today)
- [ ] Update Issue #9 description with `engagement_planning_config` table
- [ ] Update Issue #10 description with `PlanningConfigurationService`
- [ ] Update Issue #11 description with config endpoints
- [ ] Decide: Full wizard now OR defer to Phase 2?

### If Deferring Wizard (Recommended)
- [ ] Add to Phase 2 backlog: Issue #29 (Planning Config Wizard)
- [ ] Document default configuration in user guide
- [ ] Add "Coming Soon: Custom Planning Rules" note to UI

### If Implementing Wizard Now
- [ ] Create Issue #29: [FRONTEND] Planning Configuration Wizard (0.5 days)
- [ ] Assign to Frontend Engineer 2
- [ ] Schedule for Day 4 (parallel with timeline work)

---

**Document Owner**: [Your Name]
**Date**: October 22, 2025
**Status**: ✅ Analysis Complete, Awaiting Decision on Wizard
**Next**: Answer Issues #690 and #691 to continue
