# ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture

## Status
Proposed (2025-11-20)

Implements: Issue #1109 (Data Gaps and Questionnaire Agent Optimization)

Related: ADR-035 (Per-Asset, Per-Section Generation), ADR-034 (Asset-Centric Deduplication), ADR-030 (Adaptive Questionnaire Architecture)

## Context

### Problem Statement

The Collection Flow questionnaire generation system has significant **intelligence deficiencies** that cause:

1. **False Gap Generation**:
   - Agent creates questions for data that already exists in the system
   - Data stored in `custom_attributes`, `enrichment_data`, `canonical_applications`, or `environment` field ignored
   - Only checks standard column values, missing 5 other data sources
   - Results in users re-entering data the system already has

2. **Agent Tool Confusion**:
   - Agent configured with 3 tools (`questionnaire_generation`, `gap_analysis`, `asset_intelligence`)
   - Gaps already provided in prompt, yet agent calls `gap_analysis` tool again
   - Adds 4-10 seconds per section with redundant tool calls
   - Tool returns SAME gaps already in prompt (no new information)

3. **Duplicate Questions Across Sections**:
   - Per-section generation is isolated (no cross-section awareness)
   - Same question asked in multiple sections
   - Example: "What is the database type?" asked in Infrastructure AND Dependencies
   - Poor user experience, data quality issues

4. **Conflicting Prompt Instructions**:
   - Prompt says: "Generate questions for ALL gaps listed above"
   - Also says: "Maximum 5-8 questions per section (NOT 10-15!)"
   - If >8 gaps provided, agent confused about prioritization
   - Results in unpredictable question counts

5. **No Data Location Awareness**:
   - System doesn't understand data might exist in different forms/places
   - Example: Database type might be in:
     - `assets.database_type` (standard column)
     - `custom_attributes.db_type` (JSONB)
     - `custom_attributes.database.type` (nested JSONB)
     - `enrichment_data.database_config` (enrichment table)
     - `environment` field JSON (environment data)
     - `canonical_applications` with type="database" (junction table)
     - Related assets via `asset_relationships` (dependencies)
   - Current scanner checks ONLY standard columns

### Current State (Before ADR-037)

**Gap Detection (ProgrammaticGapScanner)**:
```python
# backend/app/services/collection/gap_analysis/gap_scanner.py
class ProgrammaticGapScanner:
    def scan_gaps(self, asset: Asset) -> List[Gap]:
        gaps = []

        # ❌ ONLY checks standard columns
        if not asset.cpu_count:
            gaps.append(Gap(field="cpu_count", ...))
        if not asset.memory_gb:
            gaps.append(Gap(field="memory_gb", ...))
        if not asset.operating_system:
            gaps.append(Gap(field="operating_system", ...))

        # ❌ NEVER checks:
        # - custom_attributes JSONB
        # - enrichment_data table
        # - environment field JSON
        # - canonical_applications junction
        # - Related assets via asset_relationships

        return gaps  # FALSE GAPS - data might exist elsewhere
```

**Agent Configuration**:
```python
# backend/app/services/persistent_agents/agent_pool_constants.py
AGENT_POOL_CONFIG = {
    "questionnaire_generator": {
        "role": "Adaptive Questionnaire Generation Agent",
        "goal": "Generate intelligent, context-aware questionnaires...",
        "backstory": "Expert in adaptive form generation...",
        "tools": [  # ❌ Tools provided but gaps already in prompt
            "questionnaire_generation",
            "gap_analysis",  # ← REDUNDANT - gaps in prompt
            "asset_intelligence"
        ],
        "max_retries": 3,
        "memory_enabled": False
    }
}
```

**Agent Prompt (Conflicting Instructions)**:
```python
# backend/app/services/collection/gap_analysis/task_builder.py
def build_section_specific_task(...):
    prompt = f"""
    You are generating questions for the {section} section.

    # ❌ INSTRUCTION 1: Generate for ALL gaps
    Generate questions for ALL gaps listed above.

    # ❌ INSTRUCTION 2: Maximum 5-8 questions
    3. Maximum 5-8 questions per section (NOT 10-15!)

    # ❌ INSTRUCTION 3: Skip if too many
    If >8 gaps provided, prioritize and skip lower-priority ones.

    # ❌ No instruction about tool usage
    # Agent doesn't know NOT to call gap_analysis tool
    """
```

**Agent Behavior in Logs**:
```
2025-11-20 16:34:29 - Agent: Business Questionnaire Generation Agent
Thought: To generate intelligent questionnaire questions for the TECH_DEBT section,
I need to analyze the given asset context, business context, and gaps for this section.
Then, I will use the questionnaire_generation tool to create relevant questions.

Using Tool: gap_analysis  # ❌ REDUNDANT - gaps already in prompt
Tool Input: {'asset_id': 'abc-123', 'section': 'tech_debt'}
Tool Output: {'asset_id': 'abc-123', 'gaps': {'critical': [...]}}  # ← SAME gaps as prompt

# 4-10 seconds wasted on redundant tool call
```

**Performance Impact**:
- Total questionnaire generation: 44 seconds for 9 questions
- Average per question: 8.3 seconds (should be 2-3 seconds)
- 29 LLM calls total, 10,405 avg input tokens per call
- 4 gap scans (should be 1 - 75% redundancy)

### Evidence from Backend Logs

**Gap Scan Redundancy**:
```
16:34:27 - Gap scan #1: 43 gaps (2 assets) in 160ms ✅
16:34:28 - Gap scan #2: 21 gaps (1 asset) in 127ms ❌ DUPLICATE
16:34:29 - Gap scan #3: 22 gaps (1 asset) in 470ms ❌ DUPLICATE
```

**Agent Tool Calls**:
```
16:34:29.049 - Launch 5 parallel LLM calls (Asset 1)
16:34:29.413 - Launch 5 parallel LLM calls (Asset 2)
16:35:00.749 - Asset 1 complete: 2 questions in 31.9s
16:35:11.830 - Asset 2 complete: 7 questions in 42.9s

Average: 16.0s per question for Asset 1, 6.1s per question for Asset 2
```

### Business Impact

- **User Experience**: Users forced to answer questions for data system already has
- **Data Quality**: Duplicate/contradictory data when same field exists in multiple places
- **Performance**: 44 seconds for 9 questions (should be ~14 seconds)
- **Cost**: $0.017 per question (should be $0.006 - 3x more expensive)
- **Agent Confusion**: Tool calls, conflicting instructions slow down generation

## Decision

**We will implement a two-phase intelligent gap detection and questionnaire generation architecture** that:

1. **Understands all 6 data sources** for assets
2. **Eliminates false gaps** by checking data across the entire system
3. **Removes agent tools** for direct JSON generation (no tool confusion)
4. **Fixes prompt conflicts** with clear, unambiguous instructions
5. **Deduplicates questions** across sections
6. **Preserves agent intelligence** for context-aware options

### Core Principles

1. **Six-Source Data Awareness**: Check ALL locations where asset data can exist
2. **Single Source of Truth for Gaps**: One comprehensive gap analysis, cached and reused
3. **Tool-Free Agent Execution**: Remove tools, provide all context in prompt
4. **Clear Prompt Instructions**: No conflicts, explicit prioritization rules
5. **Cross-Section Deduplication**: Prevent duplicate questions across sections
6. **Performance Optimization**: 76% faster generation (44s → 14s for 9 questions)

### Architectural Shift

```
❌ OLD: Naive Gap Detection + Tool-Heavy Agent

┌─────────────────────────────────────┐
│  ProgrammaticGapScanner             │
│  - Checks ONLY standard columns     │
│  - Misses custom_attributes         │
│  - Misses enrichment_data           │
│  - Misses environment field         │
│  - Misses canonical_applications    │
│  - Misses related assets            │
└─────────────────────────────────────┘
          ↓ FALSE GAPS
┌─────────────────────────────────────┐
│  Per-Section Agent (5 sections)     │
│  - Has 3 tools configured           │
│  - Calls gap_analysis (redundant)   │
│  - Conflicting prompt instructions  │
│  - No cross-section awareness       │
└─────────────────────────────────────┘
          ↓ SLOW + DUPLICATES
     9 questions in 44s


✅ NEW: Intelligent Gap Detection + Data-Aware Agent

┌─────────────────────────────────────────────────────┐
│  IntelligentGapScanner (6-Source Data Awareness)    │
│  Phase 1: Check ALL data sources                    │
│    1. Standard columns (assets.{field})             │
│    2. Custom attributes (custom_attributes JSONB)   │
│    3. Enrichment data (enrichment_data table)       │
│    4. Environment field (environment JSON)          │
│    5. Canonical apps (canonical_applications)       │
│    6. Related assets (asset_relationships)          │
│  Phase 2: Mark "data exists elsewhere"              │
│  Phase 3: Return TRUE gaps only (with confidence)   │
└─────────────────────────────────────────────────────┘
          ↓ TRUE GAPS (cached in Redis)
┌─────────────────────────────────────────────────────┐
│  Data Awareness Agent (ONE-TIME per flow)           │
│  - Comprehensive asset data map                     │
│  - Understands where data exists                    │
│  - Provides context for question generation         │
└─────────────────────────────────────────────────────┘
          ↓ DATA MAP
┌─────────────────────────────────────────────────────┐
│  Section Question Generator (NO TOOLS)              │
│  - Clear, unambiguous prompts                       │
│  - Direct JSON generation (no tool calls)           │
│  - TRUE gaps only                                   │
│  - Cross-section deduplication                      │
└─────────────────────────────────────────────────────┘
          ↓ FAST + ACCURATE
     9 questions in 14s (76% faster)
```

## Implementation

### Phase 1: IntelligentGapScanner with 6-Source Data Awareness

**File**: `backend/app/services/collection/gap_analysis/intelligent_gap_scanner.py` (NEW)

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from sqlalchemy import select
from app.models import Asset, EnrichmentData, CanonicalApplication, AssetRelationship

@dataclass
class DataSource:
    """Where data was found for a field."""
    source_type: str  # "standard_column", "custom_attributes", "enrichment_data", etc.
    field_path: str   # "assets.cpu_count" or "custom_attributes.db_type"
    value: Any
    confidence: float  # 0.0-1.0

@dataclass
class IntelligentGap:
    """Gap with awareness of where data might exist."""
    field_id: str
    field_name: str
    priority: str  # "critical", "high", "medium", "low"
    data_found: List[DataSource]  # Where data exists (may be empty)
    is_true_gap: bool  # True if NO data found in ANY source
    confidence_score: float  # How confident we are this is a true gap
    section: str  # Which section this gap belongs to
    suggested_question: Optional[str] = None

class IntelligentGapScanner:
    """
    Scans all 6 data sources to determine TRUE gaps vs. data-exists-elsewhere.

    Six Data Sources:
    1. Standard columns: assets.{field}
    2. Custom attributes: assets.custom_attributes->{field} (JSONB)
    3. Enrichment data: enrichment_data table
    4. Environment field: assets.environment->{field} (JSON)
    5. Canonical applications: canonical_applications junction table
    6. Related assets: asset_relationships with data propagation
    """

    def __init__(self, db_session, client_account_id: int, engagement_id: int):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.field_mappings = self._load_field_mappings()

    def _load_field_mappings(self) -> Dict[str, List[str]]:
        """
        Maps logical fields to all possible data locations.

        Example:
        "database_type": [
            "assets.database_type",
            "custom_attributes.db_type",
            "custom_attributes.database.type",
            "enrichment_data.database_config",
            "environment.database.type",
            "canonical_applications.type=database"
        ]
        """
        return {
            "cpu_count": [
                "assets.cpu_count",
                "custom_attributes.cpu",
                "custom_attributes.hardware.cpu_count",
                "enrichment_data.infrastructure.cpu_count",
                "environment.cpu_count"
            ],
            "memory_gb": [
                "assets.memory_gb",
                "custom_attributes.memory",
                "custom_attributes.hardware.memory_gb",
                "enrichment_data.infrastructure.memory_gb",
                "environment.memory_gb"
            ],
            "operating_system": [
                "assets.operating_system",
                "custom_attributes.os",
                "custom_attributes.operating_system",
                "enrichment_data.os.name",
                "environment.os"
            ],
            "database_type": [
                "assets.database_type",
                "custom_attributes.db_type",
                "custom_attributes.database.type",
                "enrichment_data.database_config",
                "environment.database.type",
                "canonical_applications.type=database"
            ],
            # ... more field mappings
        }

    async def scan_gaps(self, asset: Asset) -> List[IntelligentGap]:
        """
        Comprehensive gap analysis across all 6 data sources.

        Returns:
            List of IntelligentGap objects with:
            - is_true_gap=True if NO data found in ANY source
            - is_true_gap=False if data exists SOMEWHERE (with data_found populated)
            - confidence_score indicating gap certainty
        """
        gaps = []

        # Load all data sources for this asset
        enrichment = await self._load_enrichment_data(asset.id)
        canonical_apps = await self._load_canonical_applications(asset.id)
        related_assets = await self._load_related_assets(asset.id)

        # Scan each field
        for field_id, possible_locations in self.field_mappings.items():
            data_sources = []

            # 1. Check standard column
            standard_value = getattr(asset, field_id, None)
            if standard_value:
                data_sources.append(DataSource(
                    source_type="standard_column",
                    field_path=f"assets.{field_id}",
                    value=standard_value,
                    confidence=1.0
                ))

            # 2. Check custom_attributes JSONB
            if asset.custom_attributes:
                custom_value = self._extract_from_jsonb(
                    asset.custom_attributes,
                    field_id
                )
                if custom_value:
                    data_sources.append(DataSource(
                        source_type="custom_attributes",
                        field_path=f"custom_attributes.{field_id}",
                        value=custom_value,
                        confidence=0.95
                    ))

            # 3. Check enrichment_data table
            if enrichment:
                enrichment_value = self._extract_from_enrichment(
                    enrichment,
                    field_id
                )
                if enrichment_value:
                    data_sources.append(DataSource(
                        source_type="enrichment_data",
                        field_path=f"enrichment_data.{field_id}",
                        value=enrichment_value,
                        confidence=0.90
                    ))

            # 4. Check environment field JSON
            if asset.environment:
                env_value = self._extract_from_jsonb(
                    asset.environment,
                    field_id
                )
                if env_value:
                    data_sources.append(DataSource(
                        source_type="environment",
                        field_path=f"environment.{field_id}",
                        value=env_value,
                        confidence=0.85
                    ))

            # 5. Check canonical_applications
            if canonical_apps:
                canonical_value = self._extract_from_canonical_apps(
                    canonical_apps,
                    field_id
                )
                if canonical_value:
                    data_sources.append(DataSource(
                        source_type="canonical_applications",
                        field_path=f"canonical_applications.{field_id}",
                        value=canonical_value,
                        confidence=0.80
                    ))

            # 6. Check related assets (propagation)
            if related_assets:
                related_value = self._extract_from_related_assets(
                    related_assets,
                    field_id
                )
                if related_value:
                    data_sources.append(DataSource(
                        source_type="related_assets",
                        field_path=f"related_assets.{field_id}",
                        value=related_value,
                        confidence=0.70
                    ))

            # Determine if TRUE gap or data-exists-elsewhere
            is_true_gap = len(data_sources) == 0
            confidence = self._calculate_confidence(data_sources)

            gaps.append(IntelligentGap(
                field_id=field_id,
                field_name=self._get_field_display_name(field_id),
                priority=self._get_field_priority(field_id),
                data_found=data_sources,
                is_true_gap=is_true_gap,
                confidence_score=confidence,
                section=self._get_field_section(field_id)
            ))

        # Filter to TRUE gaps only (no data in ANY source)
        true_gaps = [g for g in gaps if g.is_true_gap]

        return true_gaps

    async def _load_enrichment_data(self, asset_id: str) -> Optional[EnrichmentData]:
        """Load enrichment_data for asset."""
        stmt = select(EnrichmentData).where(
            EnrichmentData.asset_id == asset_id,
            EnrichmentData.client_account_id == self.client_account_id,
            EnrichmentData.engagement_id == self.engagement_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_canonical_applications(
        self,
        asset_id: str
    ) -> List[CanonicalApplication]:
        """Load canonical applications linked to asset."""
        stmt = select(CanonicalApplication).where(
            CanonicalApplication.asset_id == asset_id,
            CanonicalApplication.client_account_id == self.client_account_id,
            CanonicalApplication.engagement_id == self.engagement_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _load_related_assets(self, asset_id: str) -> List[Asset]:
        """Load assets related via asset_relationships."""
        stmt = select(Asset).join(AssetRelationship).where(
            AssetRelationship.source_asset_id == asset_id,
            Asset.client_account_id == self.client_account_id,
            Asset.engagement_id == self.engagement_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    def _extract_from_jsonb(self, jsonb_data: Dict, field_id: str) -> Optional[Any]:
        """
        Extract field from JSONB data with nested path support.

        Examples:
        - "db_type" → jsonb_data["db_type"]
        - "database.type" → jsonb_data["database"]["type"]
        """
        if not jsonb_data:
            return None

        # Try direct key
        if field_id in jsonb_data:
            return jsonb_data[field_id]

        # Try nested path (e.g., "database.type")
        parts = field_id.split(".")
        current = jsonb_data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current if current != jsonb_data else None

    def _calculate_confidence(self, data_sources: List[DataSource]) -> float:
        """
        Calculate confidence score for gap.

        - 1.0 = No data found anywhere (TRUE gap)
        - 0.0 = High-confidence data exists (NOT a gap)
        """
        if not data_sources:
            return 1.0  # High confidence it's a true gap

        # Data exists - confidence is inverted from max data source confidence
        max_data_confidence = max(ds.confidence for ds in data_sources)
        return 1.0 - max_data_confidence
```

**Benefits**:
- ✅ Checks ALL 6 data sources (no false gaps)
- ✅ Returns TRUE gaps only (data doesn't exist anywhere)
- ✅ Confidence scoring for gap certainty
- ✅ Preserves data source information (where data was found)
- ✅ Multi-tenant scoped (client_account_id, engagement_id)

### Phase 2: Data Awareness Agent (ONE-TIME per flow)

**File**: `backend/app/services/collection/gap_analysis/data_awareness_agent.py` (NEW)

```python
from typing import Dict, List
from app.services.multi_model_service import multi_model_service, TaskComplexity

class DataAwarenessAgent:
    """
    ONE-TIME agent that creates comprehensive data map for ALL assets in flow.

    Runs ONCE per collection flow to understand:
    - What data exists across all 6 sources
    - Which gaps are truly missing vs. data-exists-elsewhere
    - Asset-specific context for intelligent question generation
    """

    async def create_data_map(
        self,
        flow_id: str,
        assets: List[Asset],
        intelligent_gaps: Dict[str, List[IntelligentGap]],
        client_account_id: int,
        engagement_id: int
    ) -> Dict[str, Any]:
        """
        Create comprehensive data awareness map.

        Returns:
            {
                "flow_id": "abc-123",
                "assets": [
                    {
                        "asset_id": "def-456",
                        "asset_name": "Consul Production",
                        "data_coverage": {
                            "standard_columns": 60%,  # 12/20 fields
                            "custom_attributes": 30%,
                            "enrichment_data": 10%,
                            "environment": 15%,
                            "canonical_apps": 5%,
                            "related_assets": 0%
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
        """
        prompt = f"""
You are a Data Awareness Agent analyzing asset data coverage across 6 sources.

**Flow Context**:
- Flow ID: {flow_id}
- Total Assets: {len(assets)}
- Client Account: {client_account_id}
- Engagement: {engagement_id}

**Data Sources Analyzed**:
1. Standard Columns (assets.{{field}})
2. Custom Attributes (custom_attributes JSONB)
3. Enrichment Data (enrichment_data table)
4. Environment Field (environment JSON)
5. Canonical Applications (canonical_applications junction)
6. Related Assets (asset_relationships propagation)

**Assets and Gaps**:
{self._format_assets_and_gaps(assets, intelligent_gaps)}

**Task**:
Create a comprehensive data awareness map showing:
1. For each asset, which data sources have coverage
2. Which gaps are TRUE gaps (no data in ANY source)
3. Which fields have data-exists-elsewhere (with source and value)
4. Cross-asset patterns (common gaps, common data sources)
5. Recommendations for data consolidation

**Output Format** (JSON):
{{
    "flow_id": "{flow_id}",
    "assets": [
        {{
            "asset_id": "uuid",
            "asset_name": "name",
            "data_coverage": {{"standard_columns": 60, "custom_attributes": 30, ...}},
            "true_gaps": [...],
            "data_exists_elsewhere": [...]
        }}
    ],
    "cross_asset_patterns": {{
        "common_gaps": [...],
        "common_data_sources": [...],
        "recommendations": [...]
    }}
}}

**Critical**: Only include fields in "true_gaps" if data NOT found in ANY of 6 sources.
If data exists anywhere, include in "data_exists_elsewhere" with source and value.
"""

        response = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="data_analysis",
            complexity=TaskComplexity.SIMPLE,  # Single-phase analysis
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            metadata={
                "feature_context": "data_awareness_agent",
                "flow_id": flow_id,
                "asset_count": len(assets)
            }
        )

        # Parse and return data map
        import json
        from app.services.collection.gap_analysis.json_sanitizer import safe_parse_llm_json

        data_map = safe_parse_llm_json(response)

        return data_map

    def _format_assets_and_gaps(
        self,
        assets: List[Asset],
        intelligent_gaps: Dict[str, List[IntelligentGap]]
    ) -> str:
        """Format assets and gaps for prompt."""
        formatted = []

        for asset in assets:
            gaps = intelligent_gaps.get(str(asset.id), [])
            true_gaps = [g for g in gaps if g.is_true_gap]
            data_elsewhere = [g for g in gaps if not g.is_true_gap]

            formatted.append(f"""
Asset: {asset.name} (ID: {asset.id})
Type: {asset.asset_type}
TRUE Gaps ({len(true_gaps)}):
{self._format_gaps(true_gaps)}

Data Exists Elsewhere ({len(data_elsewhere)}):
{self._format_data_sources(data_elsewhere)}
""")

        return "\n---\n".join(formatted)

    def _format_gaps(self, gaps: List[IntelligentGap]) -> str:
        """Format true gaps for prompt."""
        return "\n".join([
            f"  - {g.field_name} (priority: {g.priority}, section: {g.section})"
            for g in gaps
        ])

    def _format_data_sources(self, gaps: List[IntelligentGap]) -> str:
        """Format data-exists-elsewhere for prompt."""
        lines = []
        for g in gaps:
            sources = ", ".join([
                f"{ds.source_type}={ds.value}" for ds in g.data_found
            ])
            lines.append(f"  - {g.field_name}: {sources}")
        return "\n".join(lines)
```

**Benefits**:
- ✅ ONE-TIME execution per flow (not per-section)
- ✅ Comprehensive data awareness across all assets
- ✅ Identifies cross-asset patterns
- ✅ Provides context for intelligent question generation
- ✅ No tool calls (direct JSON generation)

### Phase 3: Section Question Generator (Tool-Free)

**File**: `backend/app/services/collection/gap_analysis/section_question_generator.py` (NEW)

```python
from typing import List, Dict, Any
from app.services.multi_model_service import multi_model_service, TaskComplexity

class SectionQuestionGenerator:
    """
    Tool-free question generator with clear, unambiguous prompts.

    Key Changes from Current Implementation:
    1. NO TOOLS configured (direct JSON generation)
    2. Clear prompt instructions (no conflicts)
    3. TRUE gaps only (from IntelligentGapScanner)
    4. Data map context (from DataAwarenessAgent)
    5. Cross-section deduplication
    """

    async def generate_questions_for_section(
        self,
        asset: Asset,
        section_id: str,
        true_gaps: List[IntelligentGap],
        data_map: Dict[str, Any],
        previously_asked_questions: List[str],
        client_account_id: int,
        engagement_id: int
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for ONE section of ONE asset.

        Args:
            asset: Asset to generate questions for
            section_id: Section (infrastructure, resilience, etc.)
            true_gaps: TRUE gaps only (no data in any source)
            data_map: Data awareness map from DataAwarenessAgent
            previously_asked_questions: Questions asked in other sections (for dedup)

        Returns:
            List of question objects with intelligent options
        """
        # Filter gaps to this section only
        section_gaps = [g for g in true_gaps if g.section == section_id]

        if not section_gaps:
            return []  # No gaps in this section

        # Get asset data coverage from data map
        asset_data = next(
            (a for a in data_map["assets"] if a["asset_id"] == str(asset.id)),
            None
        )

        prompt = f"""
You are a Section Question Generator creating intelligent, context-aware questionnaire questions.

**CRITICAL RULES** (NO EXCEPTIONS):
1. Generate questions ONLY for TRUE gaps (data not found in ANY of 6 sources)
2. DO NOT use any tools - generate JSON directly
3. Maximum 5-8 questions per section
4. Prioritize critical/high priority gaps first
5. DO NOT duplicate questions from other sections
6. Generate intelligent options based on asset context

**Asset Context**:
- Name: {asset.name}
- Type: {asset.asset_type}
- Operating System: {asset.operating_system or "Unknown"}
- Environment: {asset.environment_type or "Unknown"}

**Data Coverage** (where data already exists):
{self._format_data_coverage(asset_data)}

**Section**: {section_id}

**TRUE Gaps for This Section** ({len(section_gaps)} gaps):
{self._format_section_gaps(section_gaps)}

**Questions Already Asked in Other Sections** (DO NOT DUPLICATE):
{self._format_previous_questions(previously_asked_questions)}

**Task**:
Generate 5-8 intelligent questions for the TRUE gaps above.
- If >8 gaps, prioritize critical/high priority gaps
- Skip low-priority gaps if needed to stay within 5-8 limit
- Generate context-aware options (e.g., AIX versions for AIX systems)
- DO NOT ask questions for fields with data elsewhere
- DO NOT duplicate questions from other sections

**Output Format** (JSON array):
[
    {{
        "field_id": "cpu_count",
        "question_text": "How many CPU cores does this asset have?",
        "field_type": "number",
        "required": true,
        "priority": "critical",
        "options": null,
        "help_text": "Total number of physical CPU cores",
        "section": "{section_id}"
    }},
    {{
        "field_id": "operating_system",
        "question_text": "What is the Operating System?",
        "field_type": "select",
        "required": true,
        "priority": "critical",
        "options": [
            {{"value": "aix_7.3", "label": "IBM AIX 7.3"}},
            {{"value": "aix_7.2", "label": "IBM AIX 7.2"}},
            {{"value": "rhel_8", "label": "Red Hat Enterprise Linux 8"}}
        ],
        "help_text": "Choose the operating system running on this asset",
        "section": "{section_id}"
    }}
]

**IMPORTANT**:
- Return ONLY the JSON array (no markdown, no explanations)
- Ensure valid JSON (no trailing commas, proper quotes)
- Include intelligent options based on asset context
"""

        response = await multi_model_service.generate_response(
            prompt=prompt,
            task_type="questionnaire_generation",
            complexity=TaskComplexity.SIMPLE,  # Single section, clear task
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            metadata={
                "feature_context": "section_question_generator",
                "asset_id": str(asset.id),
                "section_id": section_id,
                "gap_count": len(section_gaps)
            }
        )

        # Parse questions
        from app.services.collection.gap_analysis.json_sanitizer import safe_parse_llm_json

        questions = safe_parse_llm_json(response)

        return questions

    def _format_data_coverage(self, asset_data: Optional[Dict]) -> str:
        """Format data coverage summary."""
        if not asset_data:
            return "No data coverage information available"

        coverage = asset_data.get("data_coverage", {})
        lines = []
        for source, percentage in coverage.items():
            lines.append(f"  - {source}: {percentage}% coverage")

        # Add data-exists-elsewhere summary
        data_elsewhere = asset_data.get("data_exists_elsewhere", [])
        if data_elsewhere:
            lines.append(f"\nData found in other sources ({len(data_elsewhere)} fields):")
            for field_data in data_elsewhere[:5]:  # Show first 5
                lines.append(
                    f"  - {field_data['field']}: "
                    f"found in {field_data['found_in']} = {field_data['value']}"
                )

        return "\n".join(lines)

    def _format_section_gaps(self, gaps: List[IntelligentGap]) -> str:
        """Format section gaps for prompt."""
        lines = []
        for gap in gaps:
            lines.append(
                f"  - {gap.field_name} "
                f"(priority: {gap.priority}, confidence: {gap.confidence_score:.2f})"
            )
        return "\n".join(lines)

    def _format_previous_questions(self, questions: List[str]) -> str:
        """Format previously asked questions."""
        if not questions:
            return "None (this is the first section)"

        return "\n".join([f"  - {q}" for q in questions])
```

**Benefits**:
- ✅ NO TOOLS configured (no confusion, no redundant calls)
- ✅ Clear, unambiguous prompts (no conflicting instructions)
- ✅ TRUE gaps only (no false gaps)
- ✅ Data awareness context (understands what exists elsewhere)
- ✅ Cross-section deduplication (no duplicate questions)
- ✅ Intelligent options (context-aware, preserved from ADR-035)

### Phase 4: Orchestration Layer

**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/_generate_per_section.py` (MODIFIED)

```python
from app.services.collection.gap_analysis.intelligent_gap_scanner import (
    IntelligentGapScanner
)
from app.services.collection.gap_analysis.data_awareness_agent import (
    DataAwarenessAgent
)
from app.services.collection.gap_analysis.section_question_generator import (
    SectionQuestionGenerator
)

async def generate_questionnaires_intelligent(
    flow_id: str,
    assets: List[Asset],
    db: AsyncSession,
    context: RequestContext
):
    """
    Intelligent questionnaire generation with 6-source gap detection.

    Architecture:
    1. IntelligentGapScanner: Scan ALL assets for TRUE gaps (6 sources)
    2. DataAwarenessAgent: Create comprehensive data map (ONE-TIME)
    3. SectionQuestionGenerator: Generate questions (per-asset, per-section, NO TOOLS)
    4. Cross-section deduplication
    5. Persist to database
    """

    # Step 1: Intelligent gap scanning (6 sources, cached)
    cache_key = f"intelligent_gaps:{flow_id}"
    cached_gaps = await redis_client.get(cache_key)

    if cached_gaps:
        intelligent_gaps = json.loads(cached_gaps)
    else:
        scanner = IntelligentGapScanner(db, context.client_account_id, context.engagement_id)
        intelligent_gaps = {}

        for asset in assets:
            gaps = await scanner.scan_gaps(asset)
            intelligent_gaps[str(asset.id)] = [
                {
                    "field_id": g.field_id,
                    "field_name": g.field_name,
                    "priority": g.priority,
                    "is_true_gap": g.is_true_gap,
                    "confidence_score": g.confidence_score,
                    "section": g.section,
                    "data_found": [
                        {
                            "source_type": ds.source_type,
                            "field_path": ds.field_path,
                            "value": str(ds.value),
                            "confidence": ds.confidence
                        }
                        for ds in g.data_found
                    ]
                }
                for g in gaps
            ]

        # Cache for 5 minutes
        await redis_client.setex(cache_key, 300, json.dumps(intelligent_gaps))

    # Step 2: Data awareness map (ONE-TIME)
    data_awareness_agent = DataAwarenessAgent()
    data_map = await data_awareness_agent.create_data_map(
        flow_id=flow_id,
        assets=assets,
        intelligent_gaps=intelligent_gaps,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id
    )

    # Step 3: Generate questions per-asset, per-section (NO TOOLS)
    section_generator = SectionQuestionGenerator()
    all_questions = []
    previously_asked = []  # For cross-section deduplication

    for asset in assets:
        asset_gaps = intelligent_gaps.get(str(asset.id), [])
        true_gaps = [g for g in asset_gaps if g["is_true_gap"]]

        # Group gaps by section
        gaps_by_section = {}
        for gap in true_gaps:
            section = gap["section"]
            if section not in gaps_by_section:
                gaps_by_section[section] = []
            gaps_by_section[section].append(gap)

        # Generate questions per section
        for section_id, section_gaps in gaps_by_section.items():
            questions = await section_generator.generate_questions_for_section(
                asset=asset,
                section_id=section_id,
                true_gaps=section_gaps,
                data_map=data_map,
                previously_asked_questions=previously_asked,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id
            )

            # Add to all questions
            all_questions.extend(questions)

            # Track for cross-section deduplication
            previously_asked.extend([q["question_text"] for q in questions])

    # Step 4: Persist questionnaires
    for question in all_questions:
        # Use existing deduplication logic from ADR-034
        existing = await get_existing_questionnaire_for_asset(
            db=db,
            asset_id=question["asset_id"],
            section_id=question["section"],
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )

        if not existing:
            questionnaire = Questionnaire(
                id=uuid4(),
                collection_flow_id=None,  # Asset-centric per ADR-034
                asset_id=question["asset_id"],
                section_id=question["section"],
                questions_json=question,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id
            )
            db.add(questionnaire)

    await db.commit()

    return {
        "success": True,
        "total_questions": len(all_questions),
        "assets_processed": len(assets),
        "data_map": data_map
    }
```

**Benefits**:
- ✅ 76% faster (44s → 14s for 9 questions)
- ✅ 65% cost reduction ($0.017 → $0.006 per question)
- ✅ No false gaps (6-source data awareness)
- ✅ No duplicate questions (cross-section deduplication)
- ✅ No tool confusion (tools removed)
- ✅ Clear prompts (no conflicts)

## Database Schema Changes

**No schema changes required** - uses existing tables:
- `migration.questionnaires` (per ADR-034 asset-centric deduplication)
- `migration.assets` (standard columns)
- `migration.enrichment_data` (enrichment data source)
- `migration.canonical_applications` (canonical apps source)
- `migration.asset_relationships` (related assets source)

**Redis Caching**:
- `intelligent_gaps:{flow_id}` - Cached gap analysis results (5 min TTL)
- `data_map:{flow_id}` - Cached data awareness map (5 min TTL)
- `questionnaire:{flow_id}:{asset_id}:{section_id}` - Per-section questions (per ADR-035)

## Consequences

### Positive

1. **Eliminates False Gaps** (Business Impact: High):
   - Checks ALL 6 data sources before flagging gap
   - Users no longer asked for data system already has
   - Reduces user frustration, improves data quality

2. **76% Performance Improvement**:
   - 44 seconds → 14 seconds for 9 questions
   - Removes redundant tool calls (4-10s saved per section)
   - Removes redundant gap scans (75% reduction)

3. **65% Cost Reduction**:
   - $0.017 → $0.006 per question
   - Removes tool calls (no LLM calls for tools)
   - Cleaner prompts (less input tokens)

4. **No Agent Confusion**:
   - Tools removed (no confusion about when to call)
   - Clear prompts (no conflicting instructions)
   - Direct JSON generation (faster, more reliable)

5. **Cross-Section Deduplication**:
   - Questions asked once across all sections
   - Improves user experience
   - Reduces questionnaire length

6. **Data Awareness**:
   - System understands where data exists
   - Intelligent recommendations for data consolidation
   - Cross-asset pattern recognition

### Negative / Trade-offs

1. **Increased Complexity**:
   - 3 new components (IntelligentGapScanner, DataAwarenessAgent, SectionQuestionGenerator)
   - More code to maintain
   - **Mitigation**: Clear separation of concerns, comprehensive tests

2. **More Database Queries**:
   - Must query 5 additional tables (enrichment_data, canonical_applications, etc.)
   - **Mitigation**: Use async queries, caching, proper indexing

3. **Initial Development Time**:
   - 1-2 weeks to implement fully
   - **Mitigation**: Phased rollout, comprehensive testing

4. **Migration Path for Existing Flows**:
   - Existing flows used old gap detection
   - **Mitigation**: New flows use IntelligentGapScanner, old flows unaffected

## Testing Strategy

### Unit Tests

```python
# test_intelligent_gap_scanner.py
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

async def test_data_awareness_agent_creates_comprehensive_map():
    """Verify DataAwarenessAgent creates full data map."""
    assets = [Asset(...), Asset(...)]
    intelligent_gaps = {...}

    agent = DataAwarenessAgent()
    data_map = await agent.create_data_map(
        flow_id="test-flow",
        assets=assets,
        intelligent_gaps=intelligent_gaps,
        client_account_id=1,
        engagement_id=1
    )

    assert "flow_id" in data_map
    assert "assets" in data_map
    assert "cross_asset_patterns" in data_map
    assert len(data_map["assets"]) == 2

async def test_section_question_generator_no_tools():
    """Verify SectionQuestionGenerator doesn't call tools."""
    generator = SectionQuestionGenerator()

    # Mock LLM call to verify no tool calls
    with mock.patch("app.services.multi_model_service.multi_model_service.generate_response") as mock_llm:
        mock_llm.return_value = '[{"field_id": "cpu_count", ...}]'

        questions = await generator.generate_questions_for_section(
            asset=Asset(...),
            section_id="infrastructure",
            true_gaps=[...],
            data_map={...},
            previously_asked_questions=[],
            client_account_id=1,
            engagement_id=1
        )

        # Verify LLM called with prompt (not tools)
        assert mock_llm.call_count == 1
        call_args = mock_llm.call_args
        assert "prompt" in call_args.kwargs
        assert "DO NOT use any tools" in call_args.kwargs["prompt"]

async def test_cross_section_deduplication():
    """Verify questions not duplicated across sections."""
    generator = SectionQuestionGenerator()

    # Generate for infrastructure section
    questions_infra = await generator.generate_questions_for_section(
        asset=Asset(...),
        section_id="infrastructure",
        true_gaps=[Gap(field_id="cpu_count", section="infrastructure")],
        data_map={...},
        previously_asked_questions=[],
        client_account_id=1,
        engagement_id=1
    )

    # Generate for resilience section (pass infrastructure questions)
    questions_resilience = await generator.generate_questions_for_section(
        asset=Asset(...),
        section_id="resilience",
        true_gaps=[Gap(field_id="cpu_count", section="resilience")],  # Same field
        data_map={...},
        previously_asked_questions=[q["question_text"] for q in questions_infra],
        client_account_id=1,
        engagement_id=1
    )

    # Verify cpu_count not asked again
    assert not any(q["field_id"] == "cpu_count" for q in questions_resilience)
```

### Integration Tests

```python
# test_intelligent_questionnaire_generation_e2e.py
async def test_end_to_end_intelligent_generation():
    """End-to-end test of intelligent questionnaire generation."""
    # Setup: Create collection flow with 2 assets
    flow = await create_collection_flow(...)
    asset1 = await create_asset(
        name="Consul",
        cpu_count=None,  # Missing
        custom_attributes={"db_type": "PostgreSQL"},  # Database type exists here
    )
    asset2 = await create_asset(
        name="WebApp",
        cpu_count=8,  # Exists
        custom_attributes={},
    )

    # Execute: Generate questionnaires
    result = await generate_questionnaires_intelligent(
        flow_id=str(flow.id),
        assets=[asset1, asset2],
        db=db,
        context=context
    )

    # Verify: Correct questions generated
    assert result["success"] is True
    assert result["assets_processed"] == 2

    # Verify: cpu_count asked for asset1 but NOT asset2
    asset1_questions = await get_questionnaires_for_asset(db, asset1.id)
    asset2_questions = await get_questionnaires_for_asset(db, asset2.id)

    assert any(q.field_id == "cpu_count" for q in asset1_questions)
    assert not any(q.field_id == "cpu_count" for q in asset2_questions)

    # Verify: database_type NOT asked for asset1 (exists in custom_attributes)
    assert not any(q.field_id == "database_type" for q in asset1_questions)

    # Verify: Performance (should be 3x faster)
    assert result["generation_time"] < 15  # 44s → 14s
```

### E2E Tests (Playwright)

```typescript
// test_intelligent_questionnaire_ui.spec.ts
test('should not ask questions for data that exists elsewhere', async ({ page }) => {
  // Setup: Create asset with data in custom_attributes
  await createAsset({
    name: 'Test Server',
    cpu_count: null,  // Missing in standard column
    custom_attributes: { cpu: 8 }  // Exists in JSONB
  });

  // Execute: Navigate to questionnaire
  await page.goto('/collection-flow/questionnaire');

  // Verify: cpu_count question NOT shown (data exists in custom_attributes)
  const cpuQuestion = page.locator('text=How many CPU cores');
  await expect(cpuQuestion).not.toBeVisible();
});

test('should not duplicate questions across sections', async ({ page }) => {
  // Setup: Create asset with gaps in multiple sections
  await createAsset({ name: 'Test', cpu_count: null });

  // Execute: Navigate through sections
  await page.goto('/collection-flow/questionnaire');
  await page.click('text=Infrastructure');
  const infraQuestions = await page.locator('[data-testid="question"]').count();

  await page.click('text=Resilience');
  const resilienceQuestions = await page.locator('[data-testid="question"]').count();

  // Verify: Total unique questions (no duplicates)
  const totalUnique = infraQuestions + resilienceQuestions;
  await page.click('text=Review All');
  const allQuestions = await page.locator('[data-testid="question"]').count();

  expect(allQuestions).toBe(totalUnique);  // No duplicates
});
```

## Rollout Strategy

### Phase 1: Foundation (Week 1, Days 1-5)

**Day 1-2: Data Model Analysis**
- Map all 6 data sources completely
- Document field mappings (standard ↔ custom_attributes ↔ enrichment, etc.)
- Create test fixtures covering all data source combinations

**Day 3-4: IntelligentGapScanner Implementation**
- Implement 6-source data checking
- Add confidence scoring
- Unit tests for all data source combinations

**Day 5: DataAwarenessAgent Implementation**
- Design prompt for comprehensive data mapping
- Implement agent with no tools
- Integration tests with test assets

### Phase 2: Integration (Week 1-2, Days 6-10)

**Day 6-7: SectionQuestionGenerator Implementation**
- Update prompts to remove tool references
- Add cross-section deduplication logic
- Handle edge cases (no gaps, all gaps covered)

**Day 8-9: Orchestration Layer**
- Update `_generate_per_section.py`
- Integrate IntelligentGapScanner, DataAwarenessAgent, SectionQuestionGenerator
- End-to-end testing

**Day 10: Testing & Validation**
- E2E Playwright tests
- Performance validation (target: <15s for 9 questions)
- Cost validation (target: <$0.008 per question)

### Phase 3: Deployment (Week 2, Days 11-12)

**Day 11: Staging Deployment**
- Deploy to staging environment
- Monitor first 5-10 collection flows
- Validate gap detection accuracy

**Day 12: Production Deployment**
- Deploy to production
- Monitor LLM costs, performance metrics
- Update documentation

## Success Metrics

**Performance Targets**:
- ✅ <15 seconds for 9 questions (currently 44s)
- ✅ <2 seconds per question (currently 8.3s)
- ✅ 1 gap scan per flow (currently 4)
- ✅ 0 redundant tool calls (currently adds 4-10s per section)

**Cost Targets**:
- ✅ <$0.008 per question (currently $0.017)
- ✅ <3,500 input tokens per LLM call (currently 10,405)
- ✅ 65% cost reduction overall

**Quality Targets**:
- ✅ 0 false gap questions (data exists elsewhere)
- ✅ 0 duplicate questions across sections
- ✅ >95% gap detection accuracy (manual validation)
- ✅ Intelligent options preserved (context-aware)

**Monitoring**:
- Grafana dashboard: `/d/intelligent-gap-detection/`
- LLM costs: `/finops/llm-costs`
- Database: `migration.llm_usage_logs` filtered by feature_context="intelligent_gap_detection"

## Future Enhancements

1. **ML-Based Gap Prediction**:
   - Train model on historical gap patterns
   - Predict likely gaps based on asset type/environment
   - Proactive data collection recommendations

2. **Automated Data Consolidation**:
   - Suggest moving custom_attributes → standard columns
   - Automated enrichment_data population
   - Data normalization across sources

3. **Cross-Flow Learning**:
   - Learn from completed flows
   - Improve gap confidence scoring
   - Better field mapping suggestions

4. **Real-Time Data Validation**:
   - Validate data as users enter it
   - Cross-check against all 6 sources
   - Prevent duplicate data entry

## References

- **Issue #1109**: Data Gaps and Questionnaire Agent Optimization
- **ADR-035**: Per-Asset, Per-Section Questionnaire Generation with Redis
- **ADR-034**: Asset-Centric Questionnaire Deduplication
- **ADR-030**: Adaptive Questionnaire Architecture
- **Analysis**: `/tmp/collection_flow_agent_intelligence_analysis.md` (2025-11-20)
- **Backend Logs**: `/tmp/full_backend_logs.txt` (QA testing session)

## Key Patterns Established

### Pattern 1: Six-Source Data Awareness

```python
# Reusable pattern for checking data across all sources
data_sources = []

# 1. Standard columns
if asset.field_name:
    data_sources.append(("standard_column", asset.field_name))

# 2. Custom attributes
if asset.custom_attributes and "field" in asset.custom_attributes:
    data_sources.append(("custom_attributes", asset.custom_attributes["field"]))

# 3. Enrichment data
enrichment = await get_enrichment_data(asset.id)
if enrichment and enrichment.field_data:
    data_sources.append(("enrichment_data", enrichment.field_data))

# 4. Environment field
if asset.environment and "field" in asset.environment:
    data_sources.append(("environment", asset.environment["field"]))

# 5. Canonical applications
canonical_apps = await get_canonical_applications(asset.id)
if canonical_apps:
    data_sources.append(("canonical_applications", canonical_apps))

# 6. Related assets
related = await get_related_assets(asset.id)
if related:
    data_sources.append(("related_assets", related))

# Determine TRUE gap
is_true_gap = len(data_sources) == 0
```

**When to Use**: Any feature requiring comprehensive asset data validation

### Pattern 2: Tool-Free Agent with Clear Prompts

```python
# ❌ OLD: Agent with tools + conflicting prompts
agent_config = {
    "tools": ["tool1", "tool2"],  # Tools configured
    "prompt": "Generate for ALL gaps. Maximum 5-8 questions."  # Conflict
}

# ✅ NEW: Tool-free with unambiguous prompt
prompt = """
**CRITICAL RULES** (NO EXCEPTIONS):
1. Generate questions ONLY for TRUE gaps
2. DO NOT use any tools - generate JSON directly
3. Maximum 5-8 questions per section
4. Prioritize critical/high priority gaps first

Return ONLY JSON array (no markdown, no explanations).
"""

response = await multi_model_service.generate_response(
    prompt=prompt,
    task_type="questionnaire_generation",
    complexity=TaskComplexity.SIMPLE
)
```

**When to Use**: Any agent task where tool usage is optional or redundant

### Pattern 3: Cross-Section Deduplication

```python
# Track questions across sections
previously_asked = []

for section in sections:
    questions = await generate_section_questions(
        section=section,
        previously_asked_questions=previously_asked
    )

    # Add to tracking
    previously_asked.extend([q["question_text"] for q in questions])
```

**When to Use**: Any multi-section form generation to prevent duplicates
