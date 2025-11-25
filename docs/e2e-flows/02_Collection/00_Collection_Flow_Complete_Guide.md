# Collection Flow - Complete Implementation Guide

**Last Updated:** 2025-11-24
**Version:** 5.0.0 (ADR-037 Intelligent Gap Detection)
**Pattern:** Child Service (CollectionChildFlowService)
**Status:** ✅ PRODUCTION READY

## 1. Quick Reference Card

- **Pattern**: Child Service Pattern (ADR-025)
- **Primary Entry**: `/api/v1/collection/*` and `/api/v1/master-flows/*`
- **Master Table**: `crewai_flow_state_extensions`
- **Child Table**: `collection_flows`
- **Key Files**:
  - `backend/app/services/child_flow_services/collection/service.py`
  - `backend/app/api/v1/endpoints/collection_flow/`
  - `backend/app/services/collection/gap_analysis/intelligent_gap_scanner.py`
  - `backend/app/services/collection/gap_analysis/data_awareness_agent.py`
  - `backend/app/services/collection/gap_analysis/section_question_generator.py`
  - `backend/app/models/collection_flows.py`
- **Critical ADRs**:
  - **ADR-037 (NEW)**: Intelligent Gap Detection (Nov 2025)
  - ADR-025 (Child Service Pattern)
  - ADR-030 (Adaptive Questionnaires)
  - ADR-034 (Asset-Centric Deduplication)
  - ADR-035 (Per-Asset Generation)
  - ADR-036 (Canonical Junction)

## 2. ADR-037: Intelligent Gap Detection Architecture (November 2025)

**Reference**: `/docs/adr/037-intelligent-gap-detection-and-questionnaire-generation.md`

### Overview

ADR-037 introduces a **two-phase intelligent gap detection and questionnaire generation architecture** that eliminates false gaps by checking **ALL 6 data sources** before flagging a field as missing. This replaces the legacy `ProgrammaticGapScanner` which only checked standard columns.

### Problem Solved

**Before ADR-037 (Legacy Pattern)**:
- ❌ Checked ONLY standard columns (`assets.cpu_count`, etc.)
- ❌ Missed data in `custom_attributes`, `enrichment_data`, `environment`, `canonical_applications`, `related_assets`
- ❌ Generated false gaps: "cpu_count is missing" when it exists as `custom_attributes.cpu`
- ❌ Users forced to re-enter data the system already has
- ❌ Agent confusion with 3 tools + conflicting prompt instructions
- ❌ Slow: 44 seconds for 9 questions (8.3s per question)

**After ADR-037 (Intelligent Pattern)**:
- ✅ Checks ALL 6 data sources before flagging a gap
- ✅ Returns TRUE gaps only (no data in ANY source)
- ✅ No false gaps: Users never asked for existing data
- ✅ No agent tools: Direct JSON generation (no tool confusion)
- ✅ Fast: 14 seconds for 9 questions (2-3s per question) - 76% faster
- ✅ 65% cost reduction: $0.006 per question (vs $0.017)

### Six Data Sources Architecture

```
┌─────────────────────────────────────────────────────────┐
│  IntelligentGapScanner (6-Source Data Awareness)        │
│  Phase 1: Check ALL data sources                        │
│    1. Standard columns (assets.{field})                 │
│       - Confidence: 1.0 (highest)                       │
│       - Example: assets.cpu_count = 8                   │
│    2. Custom attributes (custom_attributes JSONB)       │
│       - Confidence: 0.95                                │
│       - Example: custom_attributes.cpu = 8              │
│       - Example: custom_attributes.hardware.cpu_count=8 │
│    3. Enrichment data (enrichment tables)               │
│       - Confidence: 0.90                                │
│       - Tables: asset_tech_debt, asset_performance,     │
│         asset_cost_optimization                         │
│    4. Environment field (environment JSON)              │
│       - Confidence: 0.85                                │
│       - Example: environment.cpu_count = 8              │
│    5. Canonical apps (canonical_applications)           │
│       - Confidence: 0.80                                │
│       - Junction: collection_flow_applications          │
│    6. Related assets (asset_dependencies)               │
│       - Confidence: 0.70 (lowest)                       │
│       - Data propagation from upstream/downstream       │
│  Phase 2: Mark "data exists elsewhere"                  │
│  Phase 3: Return TRUE gaps only (with confidence)       │
└─────────────────────────────────────────────────────────┘
          ↓ TRUE GAPS (cached in Redis: intelligent_gaps:{flow_id})
┌─────────────────────────────────────────────────────────┐
│  DataAwarenessAgent (ONE-TIME per flow)                 │
│  - Comprehensive asset data map                         │
│  - Understands where data exists                        │
│  - Provides context for question generation             │
│  - Cross-asset pattern recognition                      │
│  - No tools: Direct JSON generation                     │
└─────────────────────────────────────────────────────────┘
          ↓ DATA MAP (cached in Redis: data_map:{flow_id})
┌─────────────────────────────────────────────────────────┐
│  SectionQuestionGenerator (NO TOOLS)                    │
│  - Clear, unambiguous prompts                           │
│  - Direct JSON generation (no tool calls)               │
│  - TRUE gaps only                                       │
│  - Cross-section deduplication                          │
│  - Intelligent context-aware options                    │
└─────────────────────────────────────────────────────────┘
          ↓ FAST + ACCURATE
     9 questions in 14s (76% faster than legacy)
```

### Component 1: IntelligentGapScanner

**File**: `backend/app/services/collection/gap_analysis/intelligent_gap_scanner.py`

**Purpose**: Scan ALL 6 data sources to determine TRUE gaps vs. data-exists-elsewhere.

**Key Method**: `async def scan_gaps(asset: Asset) -> List[IntelligentGap]`

**Example Usage**:
```python
from app.services.collection.gap_analysis.intelligent_gap_scanner import (
    IntelligentGapScanner
)

scanner = IntelligentGapScanner(db, client_account_id=1, engagement_id=123)

# Scan asset for TRUE gaps only
gaps = await scanner.scan_gaps(asset)

for gap in gaps:
    if gap.is_true_gap:
        print(f"TRUE GAP: {gap.field_name}")
        print(f"  Checked {len(gap.data_found)} sources, found no data")
    else:
        print(f"DATA EXISTS: {gap.field_name}")
        for source in gap.data_found:
            print(f"  Found in: {source.source_type} = {source.value}")
```

**Field Mapping Reference**: See `/backend/docs/data_model/six_source_field_mapping.md` for complete field → data source mappings.

**Example Field Mapping** (cpu_count):
```python
"cpu_count": [
    "assets.cpu_count",  # Source 1: Standard column
    "custom_attributes.cpu",  # Source 2: Direct key
    "custom_attributes.hardware.cpu_count",  # Source 2: Nested
    "enrichment_performance.cpu_utilization_avg",  # Source 3: Indicator
]
```

**Confidence Scoring**:
- 1.0 = No data found (TRUE gap, high confidence)
- 0.95 = Data in custom_attributes
- 0.90 = Data in enrichment tables
- 0.85 = Data in environment field
- 0.80 = Data in canonical_applications
- 0.70 = Data in related assets
- 0.0 = High-confidence data exists (NOT a gap)

### Component 2: DataAwarenessAgent

**File**: `backend/app/services/collection/gap_analysis/data_awareness_agent.py`

**Purpose**: ONE-TIME agent that creates comprehensive data map for ALL assets in flow.

**Execution**: Runs **ONCE per flow** (not per-section, not per-asset) to understand data coverage across all assets.

**Key Method**: `async def create_data_map(flow_id, assets, intelligent_gaps, client_account_id, engagement_id) -> Dict`

**Example Usage**:
```python
from app.services.collection.gap_analysis.data_awareness_agent import (
    DataAwarenessAgent
)

agent = DataAwarenessAgent()
data_map = await agent.create_data_map(
    flow_id="abc-123",
    assets=[asset1, asset2, ...],
    intelligent_gaps={
        "asset1_id": [gap1, gap2, ...],
        "asset2_id": [gap3, gap4, ...]
    },
    client_account_id=1,
    engagement_id=123
)
```

**Output Format**:
```json
{
    "flow_id": "abc-123",
    "assets": [
        {
            "asset_id": "def-456",
            "asset_name": "Consul Production",
            "data_coverage": {
                "standard_columns": 60,
                "custom_attributes": 30,
                "enrichment_data": 10,
                "environment": 15,
                "canonical_apps": 5,
                "related_assets": 0
            },
            "true_gaps": [
                {
                    "field": "cpu_count",
                    "priority": "critical",
                    "section": "infrastructure",
                    "checked_sources": 6,
                    "found_in": []
                }
            ],
            "data_exists_elsewhere": [
                {
                    "field": "database_type",
                    "found_in": "custom_attributes.db_type",
                    "value": "PostgreSQL 14",
                    "no_question_needed": true
                }
            ]
        }
    ],
    "cross_asset_patterns": {
        "common_gaps": ["cpu_count", "memory_gb"],
        "common_data_sources": ["custom_attributes"],
        "recommendations": [
            "Use custom_attributes for additional fields",
            "Populate enrichment_data for resilience info"
        ]
    }
}
```

**Why ONE-TIME?**:
- Avoids redundant analysis across sections
- Provides comprehensive view for all sections
- Cached in Redis for reuse
- Enables cross-asset pattern recognition
- Faster: Single LLM call instead of 5 per asset

### Component 3: SectionQuestionGenerator

**File**: `backend/app/services/collection/gap_analysis/section_question_generator.py`

**Purpose**: Tool-free question generator with clear, unambiguous prompts.

**Key Change**: **NO TOOLS** - Removes agent confusion and redundant tool calls.

**Key Method**: `async def generate_questions_for_section(asset, section_id, true_gaps, data_map, previously_asked_questions, client_account_id, engagement_id) -> List[Dict]`

**Example Usage**:
```python
from app.services.collection.gap_analysis.section_question_generator import (
    SectionQuestionGenerator
)

generator = SectionQuestionGenerator()
questions = await generator.generate_questions_for_section(
    asset=asset,
    section_id="infrastructure",
    true_gaps=true_gaps_for_section,
    data_map=data_map,
    previously_asked_questions=["What is the Operating System?"],
    client_account_id=1,
    engagement_id=123
)
```

**Output Format**:
```json
[
    {
        "field_id": "cpu_count",
        "question_text": "How many CPU cores does this asset have?",
        "field_type": "number",
        "required": true,
        "priority": "critical",
        "options": null,
        "help_text": "Total number of physical CPU cores",
        "section": "infrastructure"
    },
    {
        "field_id": "operating_system",
        "question_text": "What is the Operating System?",
        "field_type": "select",
        "required": true,
        "priority": "critical",
        "options": [
            {"value": "aix_7.3", "label": "IBM AIX 7.3"},
            {"value": "rhel_8", "label": "Red Hat Enterprise Linux 8"}
        ],
        "help_text": "Choose the operating system",
        "section": "infrastructure"
    }
]
```

**Critical Prompt Rules** (no conflicts):
1. Generate questions ONLY for TRUE gaps
2. DO NOT use any tools - generate JSON directly
3. Maximum 5-8 questions per section
4. Prioritize critical/high priority gaps first
5. DO NOT duplicate questions from other sections
6. Generate intelligent options based on asset context

### Redis Caching

ADR-037 introduces new Redis cache keys for performance:

```python
# Intelligent gaps (5 min TTL)
f"intelligent_gaps:{flow_id}" - List[IntelligentGap] per asset

# Data awareness map (5 min TTL)
f"data_map:{flow_id}" - Comprehensive data map from DataAwarenessAgent

# Per-section questionnaires (30 min TTL)
f"collection:{engagement_id}:{asset_id}:{section}:questions" - Generated questions
```

### API Endpoints

No new endpoints - ADR-037 enhances existing questionnaire generation internally:

```python
# Existing endpoint uses new architecture under the hood
GET /api/v1/collection/{flow_id}/questionnaires
```

**Internal Flow**:
1. Check Redis cache for `intelligent_gaps:{flow_id}`
2. If not cached, run IntelligentGapScanner for all assets
3. Run DataAwarenessAgent ONCE per flow
4. Cache data map in Redis
5. For each asset/section, run SectionQuestionGenerator
6. Return questionnaires with deduplication

### Performance Metrics

| Metric | Legacy (Pre-ADR-037) | Intelligent (ADR-037) | Improvement |
|--------|---------------------|---------------------|-------------|
| Time for 9 questions | 44 seconds | 14 seconds | 76% faster |
| Time per question | 8.3 seconds | 2-3 seconds | 70% faster |
| Cost per question | $0.017 | $0.006 | 65% reduction |
| False gaps | 30-40% | 0% | 100% elimination |
| LLM calls | 29 calls | 11 calls | 62% reduction |
| Gap scans | 4 scans | 1 scan | 75% reduction |
| Agent tool calls | 10+ redundant | 0 | 100% removal |

### Developer Guide: Adding New Data Sources

If you need to add a new data source (e.g., Source 7):

1. **Update Field Mappings**:
```python
# In intelligent_gap_scanner.py
FIELD_MAPPINGS = {
    "cpu_count": [
        "assets.cpu_count",
        "custom_attributes.cpu",
        # ... existing sources
        "new_source_table.cpu_field"  # Add new source
    ]
}
```

2. **Add Extraction Logic**:
```python
# In intelligent_gap_scanner.py
def _extract_from_new_source(self, new_source_data, field_id):
    """Extract field from new data source."""
    if field_id in ["cpu_count", "memory_gb"]:
        value = getattr(new_source_data, field_id, None)
        if value:
            return DataSource(
                source_type="new_source",
                field_path=f"new_source.{field_id}",
                value=value,
                confidence=0.75  # Define confidence level
            )
    return None
```

3. **Load New Source Data**:
```python
# In scan_gaps() method
new_source_data = await self._load_new_source_data(asset.id)

# Check new source for each field
new_source_value = self._extract_from_new_source(new_source_data, field_id)
if new_source_value:
    data_sources.append(new_source_value)
```

4. **Update Documentation**:
- Add to `/backend/docs/data_model/six_source_field_mapping.md`
- Update ADR-037 with new source details

### Testing Intelligent Gap Detection

**Unit Test Example**:
```python
# backend/tests/unit/services/test_intelligent_gap_scanner.py
@pytest.mark.asyncio
async def test_intelligent_gap_scanner_checks_all_6_sources():
    """Verify scanner checks all 6 data sources."""
    asset = Asset(
        id=uuid4(),
        name="Test Asset",
        cpu_count=None,  # Missing in standard column
        custom_attributes={"cpu": 8},  # Exists in custom_attributes
    )

    scanner = IntelligentGapScanner(db, client_account_id=1, engagement_id=1)
    gaps = await scanner.scan_gaps(asset)

    # cpu_count should NOT be in gaps (data exists in custom_attributes)
    cpu_gap = next((g for g in gaps if g.field_id == "cpu_count"), None)
    assert cpu_gap is None or not cpu_gap.is_true_gap

    # Verify data_found shows custom_attributes source
    if cpu_gap:
        assert any(ds.source_type == "custom_attributes" for ds in cpu_gap.data_found)
```

**Integration Test Example**:
```python
# backend/tests/integration/test_intelligent_questionnaire_generation_e2e.py
@pytest.mark.asyncio
async def test_end_to_end_intelligent_generation():
    """End-to-end test of intelligent questionnaire generation."""
    # Setup: Create collection flow with 2 assets
    flow = await create_collection_flow(...)
    asset1 = await create_asset(
        name="Consul",
        cpu_count=None,  # Missing
        custom_attributes={"db_type": "PostgreSQL"},  # Database type exists here
    )

    # Execute: Generate questionnaires
    result = await generate_questionnaires_intelligent(
        flow_id=str(flow.id),
        assets=[asset1],
        db=db,
        context=context
    )

    # Verify: cpu_count asked but database_type NOT asked
    asset1_questions = await get_questionnaires_for_asset(db, asset1.id)
    assert any(q.field_id == "cpu_count" for q in asset1_questions)
    assert not any(q.field_id == "database_type" for q in asset1_questions)
```

### Debugging False Gaps

If you suspect false gaps in production:

1. **Check Redis Cache**:
```bash
# In Docker container
docker exec -it migration_backend bash
redis-cli
> GET intelligent_gaps:abc-123
```

2. **Review Scanner Logs**:
```python
logger.info(
    f"✅ Asset '{asset.name}': {len(true_gaps)} true gaps found "
    f"({len(all_gaps) - len(true_gaps)} fields have data elsewhere)"
)
```

3. **Inspect Data Sources**:
```python
for gap in gaps:
    if not gap.is_true_gap:
        print(f"{gap.field_name}: Found in {gap.data_found}")
```

4. **Verify Field Mappings**:
- Check `/backend/docs/data_model/six_source_field_mapping.md`
- Ensure all variant names are mapped

### Migration Guide: Legacy → Intelligent

**Step 1: Identify Legacy Pattern**:
```python
# ❌ OLD: Legacy ProgrammaticGapScanner
from app.services.collection.gap_analysis.gap_scanner import ProgrammaticGapScanner

scanner = ProgrammaticGapScanner()
gaps = scanner.scan_gaps(asset)  # Only checks standard columns
```

**Step 2: Replace with Intelligent Pattern**:
```python
# ✅ NEW: IntelligentGapScanner
from app.services.collection.gap_analysis.intelligent_gap_scanner import (
    IntelligentGapScanner
)

scanner = IntelligentGapScanner(db, client_account_id, engagement_id)
gaps = await scanner.scan_gaps(asset)  # Checks all 6 sources
```

**Step 3: Update Questionnaire Generation**:
```python
# ✅ NEW: Use SectionQuestionGenerator (tool-free)
from app.services.collection.gap_analysis.section_question_generator import (
    SectionQuestionGenerator
)

generator = SectionQuestionGenerator()
questions = await generator.generate_questions_for_section(
    asset=asset,
    section_id="infrastructure",
    true_gaps=true_gaps,
    data_map=data_map,
    previously_asked_questions=[],
    client_account_id=client_account_id,
    engagement_id=engagement_id
)
```

**Breaking Changes**: None - ADR-037 is backward compatible. Legacy code continues to work.

---

## 3. Architecture Layers Map

### API Layer (Request Handling)
```python
# Location: backend/app/api/v1/endpoints/collection_flow/
# Additional: backend/app/api/v1/endpoints/collection_crud_*/
```

**Endpoints:**
- `POST /api/v1/master-flows/create` - Create collection flow
- `GET /api/v1/collection/{flow_id}/status` - Get flow status
- `POST /api/v1/collection/{flow_id}/submit-gaps` - Submit gap analysis
- `GET /api/v1/collection/{flow_id}/questionnaires` - Get questionnaires
- `POST /api/v1/collection/{flow_id}/submit-responses` - Submit answers
- `GET /api/v1/collection/{flow_id}/validation-results` - Get validation
- `POST /api/v1/collection/{flow_id}/transition-assessment` - Handoff to assessment

**Request/Response Schemas:**
```python
# backend/app/models/schemas/collection_flow_schema.py
class CollectionFlowCreate(BaseModel):
    flow_name: str
    selected_asset_ids: List[UUID]
    collection_type: str = "comprehensive"
    client_account_id: int
    engagement_id: int

class GapSubmissionRequest(BaseModel):
    flow_id: UUID
    gaps: List[DataGap]
    tier: str = "tier_1"  # or "tier_2"

class QuestionnaireResponse(BaseModel):
    questionnaire_id: UUID
    asset_id: UUID
    section: str
    responses: Dict[str, Any]
```

### Service Layer (Business Logic)
```python
# Location: backend/app/services/child_flow_services/collection/
# Gap Analysis: backend/app/services/collection/gap_analysis/
# Questionnaires: backend/app/services/collection/questionnaire_generation/
```

**Core Classes:**
- `CollectionChildFlowService` - Routes phase execution (Child Service Pattern)
- `GapAnalysisService` - Two-phase gap detection (Tier 1 & 2)
- `QuestionnaireGenerationService` - Intelligent MCQ generation (Issue #980)
- `CollectionFlowStateService` - State management
- `ValidationService` - Response validation

**Phase Routing:**
```python
# backend/app/services/child_flow_services/collection/service.py
class CollectionChildFlowService(CollectionChildFlowServiceBase):
    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Route to phase handlers using persistent agents"""

        if phase_name == "gap_analysis":
            return await self._execute_gap_analysis(flow_id, phase_input)
        elif phase_name == "questionnaire_generation":
            return await self._execute_questionnaire_generation(flow_id, phase_input)
        elif phase_name == "manual_collection":
            return await self._handle_manual_collection(flow_id, phase_input)
        elif phase_name == "data_validation":
            return await self._execute_validation(flow_id, phase_input)
        elif phase_name == "finalization":
            return await self._finalize_collection(flow_id, phase_input)
```

### Repository Layer (Data Access)
```python
# Location: backend/app/repositories/collection_flow_repository.py
```

**Repository Pattern:**
```python
class CollectionFlowRepository(ContextAwareRepository):
    """Repository with tenant scoping per ADR-025"""

    def __init__(self, db: AsyncSession, client_account_id: int, engagement_id: int):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def get_by_master_flow_id(self, master_flow_id: UUID) -> Optional[CollectionFlow]:
        stmt = select(CollectionFlow).where(
            and_(
                CollectionFlow.master_flow_id == master_flow_id,
                CollectionFlow.client_account_id == self.client_account_id,
                CollectionFlow.engagement_id == self.engagement_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

### Model Layer (Data Structures)

**SQLAlchemy Models:**
```python
# backend/app/models/collection_flows.py
class CollectionFlow(Base):
    __tablename__ = "collection_flows"
    __table_args__ = {"schema": "migration"}

    id = Column(UUID, primary_key=True)  # Internal ID
    flow_id = Column(UUID, unique=True)  # Legacy external ID
    master_flow_id = Column(UUID, ForeignKey("migration.crewai_flow_state_extensions.flow_id"))

    # 7 Phases (migration 076 consolidated from 8)
    current_phase = Column(String)
    initialization_completed = Column(Boolean, default=False)
    asset_selection_completed = Column(Boolean, default=False)
    gap_analysis_completed = Column(Boolean, default=False)
    questionnaire_generation_completed = Column(Boolean, default=False)
    manual_collection_completed = Column(Boolean, default=False)
    data_validation_completed = Column(Boolean, default=False)
    finalization_completed = Column(Boolean, default=False)

    # Phase results
    phase_results = Column(JSONB)
    selected_asset_ids = Column(JSONB)

    # Multi-tenant
    client_account_id = Column(Integer, nullable=False)
    engagement_id = Column(Integer, nullable=False)
```

**Gap Analysis Model:**
```python
# backend/app/models/collection_data_gaps.py
class CollectionDataGap(Base):
    __tablename__ = "collection_data_gaps"

    id = Column(UUID, primary_key=True)
    collection_flow_id = Column(UUID, ForeignKey("migration.collection_flows.id"))
    asset_id = Column(UUID, ForeignKey("migration.assets.id"))

    field_name = Column(String)  # e.g., "operating_system"
    gap_type = Column(String)  # missing_field, incomplete, invalid
    priority = Column(Integer)  # 1 (critical) to 3 (nice-to-have)
    category = Column(String)  # infrastructure, application, business, tech_debt

    # Tier 2 AI enhancements
    confidence_score = Column(Float)
    suggested_resolution = Column(String)
    ai_insights = Column(JSONB)
```

**Questionnaire Model (Asset-Centric per ADR-034):**
```python
# backend/app/models/collection_questionnaires.py
class CollectionQuestionnaire(Base):
    __tablename__ = "collection_questionnaires"

    id = Column(UUID, primary_key=True)
    # Asset-centric (not flow-centric)
    engagement_id = Column(Integer, nullable=False)
    asset_id = Column(UUID, ForeignKey("migration.assets.id"))
    section = Column(String)  # infrastructure, application, etc.

    questions = Column(JSONB)  # MCQ format per Issue #980
    status = Column(String)  # draft, published, completed

    # Unique per asset-section within engagement
    __table_args__ = (
        UniqueConstraint('engagement_id', 'asset_id', 'section',
                        name='uq_collection_quest_asset_section'),
    )
```

### Cache Layer (Performance)
```python
# Location: backend/app/core/cache/
```

**Redis Caching (ADR-035):**
```python
# Per-asset questionnaire caching
f"collection:{engagement_id}:{asset_id}:{section}:questions" - TTL: 1800s
f"collection:{flow_id}:gaps:tier1" - TTL: 600s
f"collection:{flow_id}:gaps:tier2" - TTL: 300s
f"collection:{flow_id}:validation" - TTL: 120s
```

### Queue Layer (Async Processing)
```python
# Location: backend/app/services/background_tasks/
```

**Background Tasks:**
```python
# Questionnaire generation (chunked per ADR-035)
@background_task
async def generate_questionnaires_chunked(flow_id: UUID):
    """Generate per-asset, per-section to avoid 16KB limit"""
    for asset_id in selected_assets:
        for section in CRITICAL_SECTIONS:
            await generate_single_questionnaire(
                flow_id, asset_id, section
            )
            await cache_questionnaire(engagement_id, asset_id, section)
```

### Integration Layer (External Services)

**CrewAI Agents:**
```python
# Location: backend/app/services/persistent_agents/agent_pool_constants.py

COLLECTION_AGENTS = {
    "gap_analysis_specialist": {
        "role": "Gap Analysis Specialist",
        "goal": "Identify missing critical attributes",
        "tools": ["critical_attributes_assessor", "gap_detector"],
        "memory": False  # Per ADR-024
    },
    "questionnaire_designer": {
        "role": "Intelligent Questionnaire Designer",
        "goal": "Generate context-aware MCQ questions",
        "tools": ["question_generator", "option_builder"],
        "memory": False
    },
    "quality_assessor": {
        "role": "Data Quality Assessment Agent",
        "goal": "Validate responses and identify conflicts",
        "tools": ["validation_tool", "conflict_resolver"],
        "memory": False
    }
}
```

## 3. Phase Execution Details

### Phase 1: Initialization
**Purpose**: Setup flow state and configuration

**Entry Point**:
```python
# Automatic on flow creation
# Service: CollectionChildFlowService._initialize_flow()
```

**Operations**:
- Create flow records in master and child tables
- Initialize phase tracking
- Set up tenant context

### Phase 2: Asset Selection
**Purpose**: Identify assets for data collection

**Entry Point**:
```python
# API: POST /api/v1/collection/{flow_id}/select-assets
# Service: CollectionChildFlowService._execute_asset_selection()
```

**Agent**: Platform Detection Agent + Data Collection Agent

**Asset Selection Logic**:
```python
# Can select from:
- Discovery flow assets
- Manually specified assets
- Filtered by criteria (environment, type, criticality)
```

### Phase 3: Gap Analysis (Two-Phase)
**Purpose**: Detect missing/incomplete data

**Entry Point**:
```python
# API: POST /api/v1/collection/{flow_id}/submit-gaps
# Service: GapAnalysisService.execute_gap_analysis()
```

#### Tier 1: Programmatic Scanning
```python
# backend/app/services/collection/gap_analysis/tier_processors.py
async def execute_tier_1(assets: List[Asset]) -> List[DataGap]:
    """Fast, deterministic gap detection"""
    gaps = []

    for asset in assets:
        # Check 22 critical attributes
        for attribute in CRITICAL_ATTRIBUTES:
            value = getattr(asset, attribute, None)
            if not value or is_incomplete(value):
                gaps.append(DataGap(
                    asset_id=asset.id,
                    field_name=attribute,
                    gap_type="missing" if not value else "incomplete",
                    priority=get_priority(attribute),
                    category=get_category(attribute)
                ))

    return gaps
```

#### Tier 2: AI Enhancement
```python
# Agent: gap_analysis_specialist
async def execute_tier_2(tier1_gaps: List[DataGap]) -> List[EnhancedGap]:
    """Add AI insights to gaps"""
    agent = await get_agent("gap_analysis_specialist")

    enhanced = await agent.execute({
        "gaps": tier1_gaps,
        "context": asset_context
    })

    # Returns confidence scores and suggested resolutions
    return [
        EnhancedGap(
            **gap,
            confidence_score=enhanced["confidence"],
            suggested_resolution=enhanced["resolution"],
            ai_insights=enhanced["insights"]
        )
        for gap in tier1_gaps
    ]
```

### Phase 4: Questionnaire Generation (Intelligent MCQ)
**Purpose**: Generate context-aware questions

**Entry Point**:
```python
# Automatic after gap analysis
# Service: QuestionnaireGenerationService.generate_questionnaires()
```

**Agent**: `questionnaire_designer`

**Intelligent Generation (Issue #980):**
```python
async def generate_intelligent_questions(
    asset_id: UUID,
    section: str,
    gaps: List[DataGap]
) -> Dict:
    """Generate MCQ questions based on gaps"""

    agent = await get_agent("questionnaire_designer")

    # Context-aware generation
    result = await agent.execute({
        "asset": asset_details,
        "gaps": section_gaps,
        "context": {
            "eol_status": check_eol(asset),
            "criticality": asset.business_criticality,
            "environment": asset.environment
        }
    })

    # Example output (90.9% MCQ format achieved)
    return {
        "questions": [
            {
                "field": "operating_system",
                "question": "Select the operating system version",
                "type": "mcq",
                "options": [
                    {"value": "aix_7.3", "label": "IBM AIX 7.3"},
                    {"value": "aix_7.2", "label": "IBM AIX 7.2"},
                    {"value": "rhel_8", "label": "Red Hat Enterprise Linux 8"}
                ],
                "required": True
            }
        ]
    }
```

**Per-Asset, Per-Section Generation (ADR-035):**
```python
# Avoid 16KB JSON limit by chunking
async def generate_chunked(flow_id: UUID):
    for asset in selected_assets:
        for section in ["infrastructure", "application", "business", "technical_debt"]:
            questionnaire = await generate_for_section(
                asset.id, section, gaps_for_asset_section
            )

            # Store with deduplication
            await store_with_deduplication(
                engagement_id=context.engagement_id,
                asset_id=asset.id,
                section=section,
                questions=questionnaire
            )

            # Cache in Redis
            await cache.set(
                f"collection:{engagement_id}:{asset.id}:{section}",
                questionnaire,
                ttl=1800
            )
```

### Phase 5: Manual Collection (Adaptive Forms)
**Purpose**: User completes questionnaires

**Entry Point**:
```python
# UI: Adaptive form display
# API: POST /api/v1/collection/{flow_id}/submit-responses
```

**Adaptive Behavior (Issue #795 - FEATURE not bug):**
```python
# Fewer questions = better data quality
def get_questions_for_asset(asset_id: UUID) -> List[Question]:
    """Show only questions for actual gaps"""

    gaps = get_gaps_for_asset(asset_id)

    # Asset with good data = fewer questions
    # Asset with poor data = more questions
    questions = []
    for gap in gaps:
        if gap.priority <= 2:  # Only critical and important
            questions.append(
                get_question_for_gap(gap)
            )

    return questions  # Could be 3 or 30 depending on gaps
```

### Phase 6: Data Validation
**Purpose**: Validate responses and resolve conflicts

**Entry Point**:
```python
# API: GET /api/v1/collection/{flow_id}/validation-results
# Service: ValidationService.validate_responses()
```

**Agent**: `quality_assessor`

**Validation Logic**:
```python
async def validate_responses(flow_id: UUID):
    agent = await get_agent("quality_assessor")

    result = await agent.execute({
        "responses": user_responses,
        "original_data": asset_data,
        "validation_rules": rules
    })

    return {
        "validation_score": result["score"],
        "conflicts": result["conflicts"],
        "recommendations": result["recommendations"]
    }
```

### Phase 7: Finalization
**Purpose**: Prepare for assessment handoff

**Entry Point**:
```python
# API: POST /api/v1/collection/{flow_id}/transition-assessment
# Service: CollectionChildFlowService._finalize_collection()
```

**Handoff Operations**:
```python
async def transition_to_assessment(flow_id: UUID):
    # Update assets with collected data
    await update_assets_from_responses(flow_id)

    # Create canonical applications (ADR-036)
    await create_canonical_applications(flow_id)

    # Mark collection complete
    await mark_flow_completed(flow_id)

    # Trigger assessment flow creation
    assessment_flow_id = await create_assessment_flow(
        selected_assets=get_collected_assets(flow_id)
    )

    return {"assessment_flow_id": assessment_flow_id}
```

## 4. Critical Code Patterns

### Asset-Centric Questionnaire Pattern (ADR-034)
```python
# CORRECT: Link to asset, not flow
class CollectionQuestionnaire(Base):
    # Unique per (engagement, asset, section)
    engagement_id = Column(Integer)
    asset_id = Column(UUID)
    section = Column(String)

    __table_args__ = (
        UniqueConstraint('engagement_id', 'asset_id', 'section'),
    )

# Reuse across flows
async def get_or_create_questionnaire(
    engagement_id: int,
    asset_id: UUID,
    section: str
):
    existing = await db.execute(
        select(CollectionQuestionnaire).where(
            and_(
                CollectionQuestionnaire.engagement_id == engagement_id,
                CollectionQuestionnaire.asset_id == asset_id,
                CollectionQuestionnaire.section == section
            )
        )
    ).scalar_one_or_none()

    if existing:
        return existing  # Reuse from previous flow

    # Generate new only if needed
    return await generate_new_questionnaire(...)
```

### Canonical Application Junction (ADR-036)
```python
# CORRECT: Use junction table for canonical mapping
async def create_canonical_mapping(asset: Asset):
    if asset.application_name:
        # Find or create canonical app
        canonical_app = await CanonicalApplication.find_or_create_canonical(
            db=db,
            application_name=asset.application_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )

        # Create junction record
        junction = CollectionFlowApplication(
            collection_flow_id=flow.id,
            asset_id=asset.id,
            canonical_application_id=canonical_app.id,
            deduplication_method="collection_auto",
            match_confidence=canonical_app.confidence_score
        )
        db.add(junction)
```

### TenantMemoryManager Pattern (ADR-024)
```python
# Store collection patterns
async def store_collection_patterns(context, patterns):
    memory_manager = TenantMemoryManager(
        crewai_service=crewai_service,
        database_session=db
    )

    await memory_manager.store_learning(
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        scope=LearningScope.ENGAGEMENT,
        pattern_type="collection_patterns",
        pattern_data={
            "gap_patterns": patterns["gaps"],
            "question_effectiveness": patterns["effectiveness"],
            "response_patterns": patterns["responses"]
        }
    )
```

## 5. Visual Flow Diagrams

### Overall Architecture
```mermaid
graph TB
    subgraph "User Interface"
        UI[Adaptive Forms<br/>React Components]
    end

    subgraph "API Layer"
        API[Collection API<br/>/api/v1/collection/*]
        MFO[Master Flow<br/>Orchestrator]
    end

    subgraph "Service Layer"
        CCS[CollectionChildFlowService<br/>Phase Router]
        GAS[Gap Analysis<br/>Service]
        QGS[Questionnaire<br/>Generation Service]
        VS[Validation<br/>Service]
    end

    subgraph "Agent Layer"
        Pool[TenantScopedAgentPool]
        GA[gap_analysis_specialist]
        QD[questionnaire_designer]
        QA[quality_assessor]
    end

    subgraph "Data Layer"
        Master[(Master Flow)]
        Child[(Collection Flow)]
        Gaps[(Data Gaps)]
        Quest[(Questionnaires)]
        Assets[(Assets)]
    end

    UI -->|Submit| API
    API -->|Create| MFO
    MFO -->|Execute| CCS
    CCS -->|Tier 1&2| GAS
    CCS -->|Generate| QGS
    CCS -->|Validate| VS
    GAS -->|Agent| Pool
    QGS -->|Agent| Pool
    VS -->|Agent| Pool
    Pool --> GA
    Pool --> QD
    Pool --> QA
    CCS -->|Update| Child
    GAS -->|Store| Gaps
    QGS -->|Store| Quest
    VS -->|Update| Assets
```

### Two-Phase Gap Analysis Flow
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Service as GapAnalysisService
    participant Tier1 as Tier 1 Scanner
    participant Tier2 as Tier 2 AI
    participant DB

    Client->>API: Submit gap analysis
    API->>Service: execute_gap_analysis()

    Service->>Tier1: Programmatic scan
    Tier1->>Tier1: Check 22 attributes
    Tier1-->>Service: Basic gaps

    Service->>DB: Store tier 1 gaps

    Service->>Tier2: Enhance with AI
    Tier2->>Tier2: Add confidence scores
    Tier2->>Tier2: Suggest resolutions
    Tier2-->>Service: Enhanced gaps

    Service->>DB: Update with tier 2
    Service-->>Client: Gap analysis complete
```

### Adaptive Questionnaire Flow
```mermaid
graph LR
    subgraph "Asset Quality Assessment"
        A1[Asset 1<br/>Poor Data]
        A2[Asset 2<br/>Good Data]
        A3[Asset 3<br/>Medium Data]
    end

    subgraph "Gap Detection"
        G1[22 Gaps Found]
        G2[3 Gaps Found]
        G3[10 Gaps Found]
    end

    subgraph "Question Generation"
        Q1[22 Questions<br/>All Sections]
        Q2[3 Questions<br/>1 Section]
        Q3[10 Questions<br/>2 Sections]
    end

    subgraph "Adaptive Display"
        D1[Full Form]
        D2[Minimal Form]
        D3[Partial Form]
    end

    A1 --> G1 --> Q1 --> D1
    A2 --> G2 --> Q2 --> D2
    A3 --> G3 --> Q3 --> D3
```

## 6. Common Pitfalls & Solutions

### Pitfall 1: Treating Fewer Questions as Bug
```python
# ❌ WRONG (Issue #795 misunderstanding)
# Trying to "fix" adaptive behavior
def get_all_questions():
    return ALL_POSSIBLE_QUESTIONS  # Shows unnecessary questions

# ✅ CORRECT - Adaptive is a FEATURE
def get_relevant_questions(asset_id):
    gaps = get_gaps_for_asset(asset_id)
    return generate_questions_for_gaps(gaps)  # Only what's needed
```

### Pitfall 2: Flow-Centric Questionnaires
```python
# ❌ WRONG - Creates duplicates
class Questionnaire:
    collection_flow_id = Column(UUID)  # Tied to flow

# ✅ CORRECT (ADR-034) - Asset-centric
class Questionnaire:
    engagement_id = Column(Integer)
    asset_id = Column(UUID)
    section = Column(String)
    # Reusable across flows
```

### Pitfall 3: Single Large JSON Generation
```python
# ❌ WRONG - Hits 16KB limit (Bug #996-998)
async def generate_all_questionnaires():
    all_questions = await agent.generate_for_all_assets_and_sections()
    # Returns 16KB+ JSON that gets truncated

# ✅ CORRECT (ADR-035) - Chunked generation
async def generate_chunked():
    for asset in assets:
        for section in sections:
            questions = await agent.generate_single(asset, section)
            await store_and_cache(questions)
```

## 7. Testing Guide

### Unit Tests
```bash
pytest backend/tests/unit/services/collection_flow_test.py -v
pytest backend/tests/unit/services/gap_analysis_test.py -v
pytest backend/tests/unit/services/questionnaire_generation_test.py -v
```

**Example Unit Test:**
```python
# backend/tests/unit/services/gap_analysis_test.py
@pytest.mark.asyncio
async def test_two_phase_gap_analysis():
    # Arrange
    service = GapAnalysisService(db=mock_db, context=mock_context)
    assets = [create_test_asset(missing_fields=5)]

    # Act - Tier 1
    tier1_gaps = await service.execute_tier_1(assets)
    assert len(tier1_gaps) == 5

    # Act - Tier 2
    mock_agent = AsyncMock()
    mock_agent.execute.return_value = {
        "confidence": 0.85,
        "resolution": "Collect from CMDB"
    }

    with patch("get_agent", return_value=mock_agent):
        tier2_gaps = await service.execute_tier_2(tier1_gaps)

        # Assert
        assert tier2_gaps[0].confidence_score == 0.85
        assert tier2_gaps[0].suggested_resolution == "Collect from CMDB"
```

### Integration Tests
```bash
pytest backend/tests/integration/collection_flow_integration_test.py -v
```

**Example Integration Test:**
```python
@pytest.mark.integration
async def test_adaptive_questionnaire_generation(test_client, test_db):
    # Create assets with different data quality
    asset_good = await create_asset(complete_data=True)
    asset_poor = await create_asset(complete_data=False)

    # Create collection flow
    response = await test_client.post(
        "/api/v1/master-flows/create",
        json={
            "flow_type": "collection",
            "selected_asset_ids": [str(asset_good.id), str(asset_poor.id)]
        }
    )
    flow_id = response.json()["flow_id"]

    # Execute gap analysis
    response = await test_client.post(
        f"/api/v1/collection/{flow_id}/submit-gaps",
        json={"tier": "tier_1"}
    )

    # Get questionnaires
    response = await test_client.get(
        f"/api/v1/collection/{flow_id}/questionnaires"
    )
    questionnaires = response.json()["questionnaires"]

    # Assert adaptive behavior
    good_asset_questions = [
        q for q in questionnaires
        if q["asset_id"] == str(asset_good.id)
    ]
    poor_asset_questions = [
        q for q in questionnaires
        if q["asset_id"] == str(asset_poor.id)
    ]

    # Good asset has fewer questions (FEATURE!)
    assert len(good_asset_questions) < len(poor_asset_questions)
```

### E2E Playwright Tests
```typescript
// tests/e2e/collection-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Collection Flow E2E', () => {
  test('Adaptive forms show different questions per asset', async ({ page }) => {
    // Navigate to collection
    await page.goto('http://localhost:8081/collection/create');

    // Select assets
    await page.click('[data-testid="asset-selector"]');
    await page.click('[data-testid="asset-1"]'); // Good data
    await page.click('[data-testid="asset-2"]'); // Poor data

    // Start collection
    await page.click('[data-testid="start-collection"]');

    // Execute gap analysis
    await page.click('[data-testid="run-gap-analysis"]');
    await expect(page.locator('[data-testid="gaps-found"]')).toBeVisible();

    // Navigate to forms
    await page.click('[data-testid="view-questionnaires"]');

    // Check Asset 1 (good data) - fewer questions
    await page.click('[data-testid="asset-1-form"]');
    const asset1Questions = await page.locator('[data-testid="question"]').count();

    // Check Asset 2 (poor data) - more questions
    await page.click('[data-testid="asset-2-form"]');
    const asset2Questions = await page.locator('[data-testid="question"]').count();

    // This is the CORRECT behavior (Issue #795)
    expect(asset1Questions).toBeLessThan(asset2Questions);
  });

  test('MCQ questions have context-aware options', async ({ page }) => {
    await page.goto('http://localhost:8081/collection/questionnaire/asset-123');

    // Find OS question
    const osQuestion = page.locator('[data-testid="question-operating_system"]');

    // Check for intelligent options (Issue #980)
    await expect(osQuestion.locator('option[value="aix_7.3"]')).toBeVisible();
    await expect(osQuestion.locator('option[value="aix_7.2"]')).toBeVisible();

    // Should not have generic options
    await expect(osQuestion.locator('option[value="other"]')).not.toBeVisible();
  });
});
```

## 8. Quick Code Navigation

### Find gap analysis:
```bash
grep -r "execute_tier_1\|execute_tier_2" backend/app/services/collection/
grep -r "GapAnalysisService" backend/app/services/
```

### Find questionnaire generation:
```bash
grep -r "generate_intelligent_questions" backend/
grep -r "per_asset.*per_section" backend/
```

### Find adaptive form logic:
```bash
grep -r "get_questions_for_asset" backend/
grep -r "adaptive.*form" backend/
```

### Find canonical junction:
```bash
grep -r "CollectionFlowApplication" backend/
grep -r "find_or_create_canonical" backend/
```

## 9. Version History

| Date | Version | Changes | ADRs | Issues |
|------|---------|---------|------|--------|
| 2025-11-24 | 5.0.0 | **ADR-037: Intelligent Gap Detection** | ADR-037 | #1109-1118 |
|  |  | - IntelligentGapScanner (6-source awareness) |  |  |
|  |  | - DataAwarenessAgent (one-time per flow) |  |  |
|  |  | - SectionQuestionGenerator (tool-free) |  |  |
|  |  | - 76% performance improvement (44s → 14s) |  |  |
|  |  | - 65% cost reduction ($0.017 → $0.006) |  |  |
|  |  | - 100% false gap elimination |  |  |
| 2025-11-19 | 4.0.0 | Complete documentation overhaul | - | - |
| 2025-11-11 | 3.5.0 | Per-asset questionnaire generation | ADR-035 | #996-998 |
| 2025-11-08 | 3.4.0 | Asset-centric deduplication | ADR-034 | - |
| 2025-11-05 | 3.3.0 | Intelligent MCQ generation | - | #980 |
| 2025-10-30 | 3.2.0 | Adaptive forms (not a bug!) | ADR-030 | #795 |
| 2025-10-25 | 3.1.0 | Two-phase gap analysis | - | - |
| 2025-10-15 | 3.0.0 | Child service pattern | ADR-025 | - |
| 2025-10-07 | 2.5.0 | 7 phases (consolidated from 8) | - | Migration 076 |
| 2025-10-02 | 2.0.0 | TenantMemoryManager | ADR-024 | - |

## 10. Deprecated Features

### Removed/Superseded in v5.0.0 (ADR-037)
- **ProgrammaticGapScanner** → Replaced by IntelligentGapScanner
  - Old scanner only checked standard columns
  - New scanner checks all 6 data sources
  - Legacy code: `backend/app/services/collection/gap_analysis/gap_scanner.py` (deprecated)
  - New code: `backend/app/services/collection/gap_analysis/intelligent_gap_scanner.py`
- **Tool-based agents** → Tool-free direct JSON generation
  - Removed 3 tools: `questionnaire_generation`, `gap_analysis`, `asset_intelligence`
  - Eliminates agent confusion and redundant tool calls
  - 76% faster generation

### Removed in v3.0.0
- **platform_detection phase** → Merged into asset_selection
- **automated_collection phase** → Merged into asset_selection
- **8 phases** → Consolidated to 7 phases

### Deprecated Patterns
- **Flow-centric questionnaires** → Asset-centric (ADR-034)
- **Single JSON generation** → Chunked per-asset (ADR-035)
- **Generic questions** → Context-aware MCQ (Issue #980)
- **Single-source gap detection** → Six-source intelligent detection (ADR-037)

## 11. Monitoring & Observability

### Key Metrics
```python
# Grafana Dashboard: /d/collection-flow/
```

**Flow Metrics:**
- Gap detection rate: `collection_gaps_found_total`
- Question generation: `collection_questions_generated_total`
- MCQ percentage: `collection_mcq_percentage` (target: >80%)
- Response rate: `collection_response_rate`

**Quality Metrics:**
- Data completeness before: `collection_completeness_before`
- Data completeness after: `collection_completeness_after`
- Validation score: `collection_validation_score`

**Performance Metrics:**
- Gap analysis duration: `gap_analysis_duration_seconds`
- Question generation time: `question_generation_duration_seconds`
- Per-asset processing: `per_asset_processing_seconds`

**ADR-037 Metrics (Intelligent Gap Detection)**:
- True gaps found: `intelligent_gap_scanner_true_gaps_total`
- False gaps eliminated: `intelligent_gap_scanner_false_gaps_prevented_total`
- Data sources checked: `intelligent_gap_scanner_sources_checked_total` (should be 6)
- Scanner performance: `intelligent_gap_scanner_duration_seconds` (target: <500ms per asset)
- DataAwarenessAgent calls: `data_awareness_agent_executions_total` (should be 1 per flow)
- DataAwarenessAgent performance: `data_awareness_agent_duration_seconds` (target: <5s)
- SectionQuestionGenerator tool calls: `section_question_generator_tool_calls_total` (should be 0)
- SectionQuestionGenerator performance: `section_question_generator_duration_seconds` (target: <3s per section)
- Redis cache hits: `intelligent_gaps_cache_hits_total`, `data_map_cache_hits_total`

### Logging
```python
logger.info(
    "collection_phase_executed",
    flow_id=flow_id,
    phase=phase_name,
    asset_count=len(assets),
    gaps_found=len(gaps),
    mcq_percentage=mcq_rate,
    client_account_id=context.client_account_id,
    engagement_id=context.engagement_id
)
```

## 12. Performance Optimization

### Chunked Processing (ADR-035)
```python
# Process assets in parallel chunks
async def process_assets_chunked(assets: List[Asset]):
    CHUNK_SIZE = 10

    chunks = [
        assets[i:i + CHUNK_SIZE]
        for i in range(0, len(assets), CHUNK_SIZE)
    ]

    tasks = []
    for chunk in chunks:
        tasks.append(process_chunk(chunk))

    results = await asyncio.gather(*tasks)
    return flatten(results)
```

### Redis Caching
```python
# Cache questionnaires to avoid regeneration
@cache_key("collection:{engagement_id}:{asset_id}:{section}")
async def get_cached_questionnaire(
    engagement_id: int,
    asset_id: UUID,
    section: str
):
    # Check cache first
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Generate if not cached
    questions = await generate_questionnaire(...)
    await redis.setex(cache_key, 1800, json.dumps(questions))
    return questions
```

## 13. Security Considerations

### Input Validation
```python
# Validate gap submission
class GapSubmissionValidator:
    def validate(self, gaps: List[DataGap]):
        for gap in gaps:
            # Prevent injection
            if not gap.field_name.isidentifier():
                raise ValueError(f"Invalid field name: {gap.field_name}")

            # Validate priority
            if gap.priority not in [1, 2, 3]:
                raise ValueError(f"Invalid priority: {gap.priority}")

            # Validate category
            if gap.category not in VALID_CATEGORIES:
                raise ValueError(f"Invalid category: {gap.category}")
```

### Response Sanitization
```python
# Sanitize user responses
def sanitize_response(response: str) -> str:
    # Remove potential XSS
    response = bleach.clean(response)

    # Validate against allowed values
    if response not in ALLOWED_VALUES:
        raise ValueError(f"Invalid response: {response}")

    return response
```

### Multi-Tenant Isolation
```python
# Always scope by tenant
async def get_collection_flow(flow_id: UUID, context: RequestContext):
    flow = await db.execute(
        select(CollectionFlow).where(
            and_(
                CollectionFlow.id == flow_id,
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id
            )
        )
    ).scalar_one_or_none()

    if not flow:
        raise HTTPException(403, "Access denied")

    return flow
```

---

**End of Collection Flow Documentation**

*For questions about adaptive behavior, see Issue #795. For MCQ generation, see Issue #980.*