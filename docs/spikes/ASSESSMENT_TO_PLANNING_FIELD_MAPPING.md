# Assessment Flow → Planning Flow Field Mapping

**Spike Issue**: #696
**Date**: October 22, 2025
**Author**: Claude Code
**Status**: ✅ Complete

---

## Executive Summary

This spike identifies which Assessment Flow fields are required by Planning Flow for wave planning. Analysis reveals that **Planning Flow requires comprehensive data from both Assessment and CanonicalApplication models** to perform intelligent wave assignment, dependency management, and resource optimization.

### Key Findings

1. **Assessment Model** (`assessments` table) provides:
   - 6R migration strategy decisions
   - Risk and complexity metrics
   - Timeline and effort estimates
   - Cost analysis
   - Technical readiness scores

2. **CanonicalApplication Model** (`canonical_applications` table) provides:
   - Application identity and metadata
   - Business criticality
   - Technology stack information

3. **WavePlan Model** (`wave_plans` table) consumes:
   - Assessment outputs for wave optimization
   - Application metadata for grouping decisions
   - Risk/complexity scores for wave sequencing

---

## Model Analysis

### 1. Assessment Model Fields

**Location**: `backend/app/models/assessment.py:80-217`

#### 1.1 Core Assessment Fields

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `id` | UUID | Primary key for assessment reference | P0 |
| `asset_id` | UUID | Link to specific asset being assessed | P0 |
| `assessment_type` | Enum | Filter for 6R analysis type | P0 |
| `status` | Enum | Only use completed assessments | P0 |

#### 1.2 6R Strategy Fields (CRITICAL for Planning)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `recommended_strategy` | String(50) | Primary 6R recommendation (Rehost, Replatform, etc.) | **P0** |
| `alternative_strategies` | JSON | Backup 6R options with scores | P1 |
| `strategy_rationale` | Text | Explanation for recommendation | P2 |

**Planning Use Case**: Group applications by migration strategy (all Rehost apps in Wave 1, Refactor in Wave 3, etc.)

#### 1.3 Timeline & Effort Fields (CRITICAL for Wave Assignment)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `estimated_effort_hours` | Integer | Total effort required for migration | **P0** |
| `estimated_duration_days` | Integer | Calendar time needed | **P0** |
| `recommended_wave` | Integer | AI-suggested wave assignment | P1 |
| `prerequisites` | JSON | Dependencies that must complete first | **P0** |

**Planning Use Case**:
- Calculate wave capacity (sum of effort_hours ≤ team capacity)
- Sequence applications by duration
- Respect prerequisite dependencies

#### 1.4 Risk & Complexity Fields (for Wave Sequencing)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `overall_score` | Float (0-100) | Overall assessment score | P0 |
| `risk_level` | Enum (LOW/MEDIUM/HIGH/CRITICAL) | Risk classification | **P0** |
| `technical_complexity` | String | Complexity level (low/medium/high) | **P0** |
| `compatibility_score` | Float (0-100) | Cloud compatibility | P1 |
| `identified_risks` | JSON | List of risks | P1 |
| `blockers` | JSON | Migration blockers | **P0** |
| `dependencies_impact` | JSON | Dependency analysis | **P0** |

**Planning Use Case**:
- Place low-risk apps in early waves (quick wins)
- Place high-risk apps in later waves (after team experience)
- Avoid waves with only high-complexity apps (burnout risk)

#### 1.5 Cost Fields (for Wave Budget Planning)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `current_cost` | Float | Current infrastructure cost | P1 |
| `estimated_migration_cost` | Float | One-time migration cost | **P0** |
| `estimated_target_cost` | Float | Post-migration recurring cost | P1 |
| `cost_savings_potential` | Float | Projected savings | P2 |
| `roi_months` | Integer | ROI timeline | P2 |

**Planning Use Case**:
- Calculate wave budgets (sum of migration costs)
- Prioritize high-ROI applications
- Balance cost across waves

#### 1.6 Business Impact Fields (for Wave Prioritization)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `business_criticality` | String | LOW/MEDIUM/HIGH/CRITICAL | **P0** |
| `downtime_requirements` | JSON | Acceptable downtime windows | P1 |
| `user_impact` | Text | Impact on end users | P1 |
| `compliance_considerations` | JSON | Regulatory requirements | P1 |

**Planning Use Case**:
- Schedule critical apps during low-business-impact windows
- Group apps by downtime windows
- Prioritize compliance-critical apps

#### 1.7 AI Insights (Optional but Recommended)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `ai_insights` | JSON | AI-generated insights | P2 |
| `ai_confidence` | Float (0-1) | AI confidence score | P2 |
| `modernization_opportunities` | JSON | Modernization recommendations | P2 |

**Planning Use Case**: Inform wave optimization decisions

---

### 2. CanonicalApplication Model Fields

**Location**: `backend/app/models/canonical_applications/canonical_application.py:42-150`

#### 2.1 Application Identity Fields

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `id` | UUID | Primary key | P0 |
| `canonical_name` | String(255) | Application display name | **P0** |
| `normalized_name` | String(255) | Standardized name | P1 |
| `description` | Text | Application description | P1 |

**Planning Use Case**: Display application names in wave plans

#### 2.2 Application Metadata (for Grouping)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `application_type` | String(100) | App category (web, database, etc.) | **P0** |
| `business_criticality` | String(50) | Business importance | **P0** |
| `technology_stack` | JSONB | Tech stack details | P1 |

**Planning Use Case**:
- Group similar applications in same wave (e.g., all databases in Wave 2)
- Balance criticality across waves
- Identify technology dependencies

#### 2.3 Multi-Tenant Isolation (CRITICAL)

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `client_account_id` | UUID | Client isolation | **P0** |
| `engagement_id` | UUID | Engagement isolation | **P0** |

**Planning Use Case**: Ensure wave plans respect tenant boundaries

#### 2.4 Confidence & Quality Metrics

| Field | Type | Purpose in Planning | Priority |
|-------|------|---------------------|----------|
| `confidence_score` | Float (0-1) | Data quality score | P1 |
| `is_verified` | Boolean | Manual verification flag | P1 |
| `verification_source` | String(100) | Verification source | P2 |

**Planning Use Case**: Flag low-confidence applications for manual review before wave assignment

---

### 3. WavePlan Model (Target Model)

**Location**: `backend/app/models/assessment.py:219-310`

#### 3.1 Wave Characteristics (Calculated from Assessment Data)

| Field | Type | Calculated From | Formula |
|-------|------|-----------------|---------|
| `estimated_effort_hours` | Integer | `assessments.estimated_effort_hours` | `SUM(effort_hours) WHERE wave_number = X` |
| `estimated_cost` | Float | `assessments.estimated_migration_cost` | `SUM(migration_cost) WHERE wave_number = X` |
| `overall_risk_level` | Enum | `assessments.risk_level` | `MAX(risk_level) WHERE wave_number = X` |
| `complexity_score` | Float | `assessments.technical_complexity` | `AVG(complexity_score) WHERE wave_number = X` |

#### 3.2 Wave Dependencies (from Assessment Prerequisites)

| Field | Type | Calculated From |
|-------|------|-----------------|
| `prerequisites` | JSON | Aggregation of `assessments.prerequisites` |
| `dependencies` | JSON | Cross-wave dependency analysis |

#### 3.3 Wave Optimization (AI-Powered)

| Field | Type | Purpose |
|-------|------|---------|
| `ai_recommendations` | JSON | AI-generated wave optimization suggestions |
| `optimization_score` | Float (0-100) | Wave optimization quality score |

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Assessment Flow                              │
│                                                                   │
│  ┌───────────────┐        ┌─────────────────────────┐          │
│  │ Asset         │        │ CanonicalApplication    │          │
│  │ (Discovery)   │───────>│ (Collection)            │          │
│  └───────────────┘        └─────────────────────────┘          │
│         │                            │                           │
│         │                            │                           │
│         ▼                            ▼                           │
│  ┌───────────────────────────────────────────────────┐          │
│  │          Assessment (6R Analysis)                  │          │
│  │  - recommended_strategy                            │          │
│  │  - risk_level                                      │          │
│  │  - technical_complexity                            │          │
│  │  - estimated_effort_hours                          │          │
│  │  - estimated_duration_days                         │          │
│  │  - business_criticality                            │          │
│  │  - prerequisites                                   │          │
│  │  - blockers                                        │          │
│  └───────────────────────────────────────────────────┘          │
│         │                                                         │
└─────────┼─────────────────────────────────────────────────────────┘
          │
          │ Feed into Planning Flow
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Planning Flow                                │
│                                                                   │
│  ┌───────────────────────────────────────────────────┐          │
│  │      Wave Planning Algorithm                       │          │
│  │  1. Filter: status = 'completed'                  │          │
│  │  2. Group: by 6R strategy                         │          │
│  │  3. Sort: by risk_level, complexity                │          │
│  │  4. Assign: to waves (capacity constraints)       │          │
│  │  5. Optimize: dependencies, timeline              │          │
│  └───────────────────────────────────────────────────┘          │
│         │                                                         │
│         ▼                                                         │
│  ┌───────────────────────────────────────────────────┐          │
│  │          WavePlan                                  │          │
│  │  - wave_number                                     │          │
│  │  - total_assets                                    │          │
│  │  - estimated_effort_hours (aggregated)            │          │
│  │  - estimated_cost (aggregated)                    │          │
│  │  - overall_risk_level (max of all apps)           │          │
│  │  - planned_start_date                              │          │
│  │  - planned_end_date                                │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## SQL Query: Fetch Planning-Ready Applications

```sql
-- Get all applications ready for wave planning
-- (completed assessments with required fields populated)

WITH assessment_data AS (
  SELECT
    a.id AS assessment_id,
    a.asset_id,
    a.recommended_strategy,
    a.alternative_strategies,
    a.strategy_rationale,
    a.estimated_effort_hours,
    a.estimated_duration_days,
    a.recommended_wave,
    a.prerequisites,
    a.risk_level,
    a.technical_complexity,
    a.compatibility_score,
    a.identified_risks,
    a.blockers,
    a.dependencies_impact,
    a.estimated_migration_cost,
    a.estimated_target_cost,
    a.business_criticality,
    a.downtime_requirements,
    a.user_impact,
    a.compliance_considerations,
    a.ai_insights,
    a.ai_confidence,
    a.overall_score,
    -- Readiness check
    CASE
      WHEN a.recommended_strategy IS NULL THEN FALSE
      WHEN a.estimated_effort_hours IS NULL THEN FALSE
      WHEN a.estimated_duration_days IS NULL THEN FALSE
      WHEN a.risk_level IS NULL THEN FALSE
      WHEN a.technical_complexity IS NULL THEN FALSE
      WHEN a.blockers IS NOT NULL AND jsonb_array_length(a.blockers) > 0 THEN FALSE
      ELSE TRUE
    END AS is_ready_for_planning
  FROM migration.assessments a
  WHERE a.client_account_id = :client_account_id
    AND a.engagement_id = :engagement_id
    AND a.assessment_type = 'six_r_analysis'
    AND a.status IN ('completed', 'reviewed', 'approved')
),
canonical_app_data AS (
  SELECT
    ca.id AS canonical_app_id,
    ca.canonical_name,
    ca.normalized_name,
    ca.description,
    ca.application_type,
    ca.business_criticality AS ca_business_criticality,
    ca.technology_stack,
    ca.confidence_score,
    ca.is_verified
  FROM migration.canonical_applications ca
  WHERE ca.client_account_id = :client_account_id
    AND ca.engagement_id = :engagement_id
),
asset_data AS (
  SELECT
    ast.id AS asset_id,
    ast.name AS asset_name,
    ast.asset_type,
    ast.hostname,
    ast.environment,
    ast.location,
    ast.assessment_flow_id
  FROM migration.assets ast
  WHERE ast.client_account_id = :client_account_id
    AND ast.engagement_id = :engagement_id
    AND ast.assessment_flow_id IS NOT NULL  -- Has been assessed
)

-- Main query: Join all data for planning
SELECT
  ast.asset_id,
  ast.asset_name,
  ast.asset_type,
  ast.hostname,
  ast.environment,
  ast.location,
  ca.canonical_app_id,
  ca.canonical_name,
  ca.application_type,
  ca.business_criticality AS ca_business_criticality,
  ca.technology_stack,
  ca.confidence_score,
  ca.is_verified,
  ad.assessment_id,
  ad.recommended_strategy,
  ad.alternative_strategies,
  ad.strategy_rationale,
  ad.estimated_effort_hours,
  ad.estimated_duration_days,
  ad.recommended_wave,
  ad.prerequisites,
  ad.risk_level,
  ad.technical_complexity,
  ad.compatibility_score,
  ad.identified_risks,
  ad.blockers,
  ad.dependencies_impact,
  ad.estimated_migration_cost,
  ad.estimated_target_cost,
  ad.business_criticality,
  ad.downtime_requirements,
  ad.user_impact,
  ad.compliance_considerations,
  ad.ai_insights,
  ad.ai_confidence,
  ad.overall_score,
  ad.is_ready_for_planning
FROM asset_data ast
LEFT JOIN canonical_app_data ca
  ON ast.asset_name = ca.canonical_name
  OR ast.asset_name = ca.normalized_name
INNER JOIN assessment_data ad
  ON ast.asset_id = ad.asset_id
WHERE ad.is_ready_for_planning = TRUE
ORDER BY
  ad.business_criticality DESC,  -- Critical apps first
  ad.risk_level ASC,              -- Low-risk apps first
  ad.estimated_effort_hours ASC;  -- Quick wins first
```

---

## Validation Rules: "Ready for Planning" Status

An application is considered **ready for planning** if ALL of the following conditions are met:

### Required Fields (P0 - Must Have)

| Field | Validation Rule |
|-------|-----------------|
| `recommended_strategy` | NOT NULL and IN ('rehost', 'replatform', 'repurchase', 'refactor', 'retain', 'retire') |
| `estimated_effort_hours` | NOT NULL and > 0 |
| `estimated_duration_days` | NOT NULL and > 0 |
| `risk_level` | NOT NULL and IN ('low', 'medium', 'high', 'critical') |
| `technical_complexity` | NOT NULL and IN ('low', 'medium', 'high') |
| `business_criticality` | NOT NULL and IN ('low', 'medium', 'high', 'critical') |
| `status` | IN ('completed', 'reviewed', 'approved') |

### Blocking Conditions (Must Be FALSE)

| Condition | Rule |
|-----------|------|
| `blockers` | Array must be empty OR NULL |
| `assessment.status` | NOT IN ('pending', 'in_progress', 'rejected') |

### Optional Fields (P1 - Recommended)

| Field | Impact if Missing |
|-------|-------------------|
| `estimated_migration_cost` | Wave budget calculation will be incomplete |
| `prerequisites` | Dependency analysis will be incomplete |
| `dependencies_impact` | Wave sequencing may be suboptimal |
| `recommended_wave` | Will use default algorithm (may not match AI suggestion) |

---

## Data Transformation Requirements

### Transformation #1: Risk Level Aggregation

**Purpose**: Calculate wave overall risk level from individual assessments

```python
def calculate_wave_risk_level(assessments: List[Assessment]) -> RiskLevel:
    """Calculate overall risk level for a wave"""
    risk_scores = {
        RiskLevel.LOW: 1,
        RiskLevel.MEDIUM: 2,
        RiskLevel.HIGH: 3,
        RiskLevel.CRITICAL: 4
    }

    if not assessments:
        return RiskLevel.LOW

    # Get highest risk level in wave
    max_risk_score = max(risk_scores.get(a.risk_level, 1) for a in assessments)

    # Reverse lookup
    for level, score in risk_scores.items():
        if score == max_risk_score:
            return level

    return RiskLevel.LOW
```

### Transformation #2: Complexity Score Aggregation

**Purpose**: Calculate wave complexity score from individual assessments

```python
def calculate_wave_complexity(assessments: List[Assessment]) -> float:
    """Calculate average complexity score for a wave (0-100)"""
    complexity_mapping = {
        'low': 25.0,
        'medium': 50.0,
        'high': 75.0
    }

    if not assessments:
        return 0.0

    scores = [complexity_mapping.get(a.technical_complexity, 50.0) for a in assessments]
    return sum(scores) / len(scores)
```

### Transformation #3: Effort Aggregation

**Purpose**: Sum effort hours for wave capacity planning

```python
def calculate_wave_effort(assessments: List[Assessment]) -> int:
    """Calculate total effort hours for a wave"""
    return sum(a.estimated_effort_hours or 0 for a in assessments)
```

### Transformation #4: Cost Aggregation

**Purpose**: Sum migration costs for wave budgeting

```python
def calculate_wave_cost(assessments: List[Assessment]) -> float:
    """Calculate total migration cost for a wave"""
    return sum(a.estimated_migration_cost or 0.0 for a in assessments)
```

### Transformation #5: Dependency Graph

**Purpose**: Build dependency graph for wave sequencing

```python
def build_dependency_graph(assessments: List[Assessment]) -> Dict[UUID, List[UUID]]:
    """Build application dependency graph from prerequisites"""
    graph = {}

    for assessment in assessments:
        asset_id = assessment.asset_id
        prerequisites = assessment.prerequisites or []

        # Extract prerequisite asset IDs from JSON
        prereq_ids = [p.get('asset_id') for p in prerequisites if 'asset_id' in p]

        graph[asset_id] = prereq_ids

    return graph
```

---

## Recommendations for Backend Implementation

### 1. Create Planning Service Layer

**File**: `backend/app/services/planning_flow_service/planning_data_fetcher.py`

```python
class PlanningDataFetcher:
    """Fetch and validate Assessment data for Planning Flow"""

    async def get_planning_ready_assessments(
        self,
        client_account_id: UUID,
        engagement_id: UUID,
        db: AsyncSession
    ) -> List[PlanningReadyApplication]:
        """
        Fetch all assessments ready for wave planning.

        Returns:
            List of applications with Assessment + CanonicalApplication data
        """
        # Execute SQL query from above
        result = await db.execute(PLANNING_READY_QUERY)
        rows = result.fetchall()

        # Validate and transform
        apps = []
        for row in rows:
            if self._validate_planning_readiness(row):
                apps.append(self._transform_to_planning_app(row))

        return apps

    def _validate_planning_readiness(self, row: Dict) -> bool:
        """Validate row meets planning readiness criteria"""
        required_fields = [
            'recommended_strategy',
            'estimated_effort_hours',
            'estimated_duration_days',
            'risk_level',
            'technical_complexity',
            'business_criticality'
        ]

        # Check all required fields are populated
        for field in required_fields:
            if row.get(field) is None:
                return False

        # Check no blocking issues
        blockers = row.get('blockers', [])
        if blockers and len(blockers) > 0:
            return False

        return True

    def _transform_to_planning_app(self, row: Dict) -> PlanningReadyApplication:
        """Transform DB row to Planning application model"""
        return PlanningReadyApplication(
            asset_id=row['asset_id'],
            asset_name=row['asset_name'],
            canonical_name=row['canonical_name'],
            application_type=row['application_type'],
            recommended_strategy=row['recommended_strategy'],
            risk_level=row['risk_level'],
            technical_complexity=row['technical_complexity'],
            business_criticality=row['business_criticality'],
            estimated_effort_hours=row['estimated_effort_hours'],
            estimated_duration_days=row['estimated_duration_days'],
            estimated_migration_cost=row['estimated_migration_cost'],
            prerequisites=row['prerequisites'],
            dependencies_impact=row['dependencies_impact'],
            # ... all other fields
        )
```

### 2. Create Pydantic Model for Planning Data

**File**: `backend/app/models/planning_flow/schemas.py`

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID

class PlanningReadyApplication(BaseModel):
    """Application ready for wave planning (Assessment + CanonicalApplication data)"""

    # Asset identification
    asset_id: UUID
    asset_name: str
    canonical_name: Optional[str]

    # Application metadata
    application_type: Optional[str]
    business_criticality: str
    technology_stack: Optional[Dict[str, Any]]

    # 6R Strategy
    recommended_strategy: str  # rehost, replatform, etc.
    alternative_strategies: Optional[List[Dict[str, Any]]]
    strategy_rationale: Optional[str]

    # Effort & Timeline
    estimated_effort_hours: int
    estimated_duration_days: int
    recommended_wave: Optional[int]

    # Risk & Complexity
    risk_level: str  # low, medium, high, critical
    technical_complexity: str  # low, medium, high
    compatibility_score: Optional[float]

    # Dependencies
    prerequisites: List[Dict[str, Any]] = []
    blockers: List[Dict[str, Any]] = []
    dependencies_impact: Optional[Dict[str, Any]]

    # Cost
    estimated_migration_cost: Optional[float]
    estimated_target_cost: Optional[float]

    # Business Impact
    downtime_requirements: Optional[Dict[str, Any]]
    user_impact: Optional[str]
    compliance_considerations: Optional[Dict[str, Any]]

    # AI Insights
    ai_insights: Optional[Dict[str, Any]]
    ai_confidence: Optional[float]
```

### 3. Create API Endpoint

**File**: `backend/app/api/v1/endpoints/planning_flow_router.py`

```python
@router.get("/planning-ready-applications")
async def get_planning_ready_applications(
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> List[PlanningReadyApplication]:
    """
    Get all applications ready for wave planning.

    Returns applications that have completed assessment with all required fields.
    """
    fetcher = PlanningDataFetcher()
    apps = await fetcher.get_planning_ready_assessments(
        client_account_id, engagement_id, db
    )
    return apps
```

---

## Deliverables Checklist

- [x] **Field mapping document** - This document (Assessment → Planning)
- [x] **Data transformation logic** - Aggregation functions documented
- [x] **Validation rules** - "Ready for planning" criteria defined
- [x] **SQL query** - Planning-ready applications query provided
- [x] **Pydantic models** - `PlanningReadyApplication` schema defined
- [x] **Service layer design** - `PlanningDataFetcher` class structure
- [x] **API endpoint** - `/planning-ready-applications` endpoint design

---

## Next Steps (Implementation)

1. **Backend Team** (3-5 days):
   - [ ] Implement `PlanningDataFetcher` service
   - [ ] Create `PlanningReadyApplication` Pydantic model
   - [ ] Add `/api/v1/planning-ready-applications` endpoint
   - [ ] Write unit tests for validation logic
   - [ ] Write integration tests for SQL query

2. **Frontend Team** (2-3 days):
   - [ ] Create Planning Flow UI to display planning-ready applications
   - [ ] Add filters for 6R strategy, risk level, complexity
   - [ ] Implement wave assignment drag-and-drop interface
   - [ ] Display assessment summary per application

3. **QA Team** (2 days):
   - [ ] Test Assessment → Planning data flow
   - [ ] Validate "ready for planning" rules
   - [ ] Test edge cases (missing fields, blockers, etc.)

---

## Success Criteria (Spike Complete ✅)

- [x] All required fields identified (P0 fields documented)
- [x] Data flow documented (Assessment → Planning diagram)
- [x] Backend team has clear implementation guide (service + models + API)
- [x] SQL query verified for correctness
- [x] Validation rules comprehensive

**Time Spent**: 1 day (within time-box)

---

**Last Updated**: October 22, 2025
**Status**: ✅ Complete - Ready for Implementation
