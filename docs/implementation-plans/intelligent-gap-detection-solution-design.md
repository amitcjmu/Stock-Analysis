## Intelligent Multi-Layer Gap Detection - Solution Design & Implementation Plan

### Executive Summary

Replace the current 22-attribute hardcoded gap detection with an intelligent, context-aware system that:
- Scans ALL data layers (columns, enrichments, JSONB, standards)
- Adapts to asset type, 6R strategy, and compliance requirements
- Generates targeted questionnaires based on actual missing data
- Validates architecture standards before assessment
- Provides transparent gap breakdown by category

**Estimated Timeline**: 3-4 weeks (Weeks 2-5 after investigation)

**Impact**:
- ✅ Eliminates false "0 missing attributes" positives
- ✅ Improves collection questionnaire relevance by ~70%
- ✅ Increases assessment 6R recommendation accuracy
- ✅ Reduces user confusion with transparent gap reporting
- ✅ Enables compliance-driven data collection

---

## Solution Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Layer Gap Analyzer                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ Asset Columns  │  │  Enrichments   │  │ JSONB Fields   │    │
│  │  Inspector     │  │   Inspector    │  │   Inspector    │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│          │                   │                    │              │
│          └───────────────────┴────────────────────┘              │
│                              │                                   │
│                    ┌─────────▼──────────┐                        │
│                    │  Context Analyzer  │                        │
│                    │  - Asset Type      │                        │
│                    │  - 6R Strategy     │                        │
│                    │  - Compliance      │                        │
│                    │  - Criticality     │                        │
│                    └─────────┬──────────┘                        │
│                              │                                   │
│                    ┌─────────▼──────────┐                        │
│                    │ Requirements Model │                        │
│                    │  - Required attrs  │                        │
│                    │  - Optional attrs  │                        │
│                    │  - Priority levels │                        │
│                    └─────────┬──────────┘                        │
│                              │                                   │
│                    ┌─────────▼──────────┐                        │
│                    │   Gap Calculator   │                        │
│                    │  - Missing data    │                        │
│                    │  - Priority score  │                        │
│                    │  - Category group  │                        │
│                    └─────────┬──────────┘                        │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Gap Response (API)  │
                    │  {                   │
                    │    column_gaps: [],  │
                    │    enrichment_gaps:[]│
                    │    jsonb_gaps: [],   │
                    │    standards_gaps:[] │
                    │    total_score: 0.72 │
                    │  }                   │
                    └──────────────────────┘
```

### Core Components

#### 1. Multi-Layer Inspector System

**Purpose**: Scan all data sources for completeness

**Components**:

**a) ColumnInspector** (`backend/app/services/gap_detection/inspectors/column_inspector.py`)
```python
class ColumnInspector:
    """Inspects Asset SQLAlchemy columns for missing data."""

    async def inspect(self, asset: Asset) -> ColumnGapReport:
        """
        Returns:
            ColumnGapReport:
                - missing_attributes: List[str]
                - empty_attributes: List[str]  # Empty strings
                - null_attributes: List[str]
        """
```

**b) EnrichmentInspector** (`backend/app/services/gap_detection/inspectors/enrichment_inspector.py`)
```python
class EnrichmentInspector:
    """Inspects 7 enrichment tables for missing data."""

    ENRICHMENT_TABLES = [
        "resilience",
        "compliance_flags",
        "vulnerabilities",
        "licenses",
        "dependencies",
        "product_links",
        "field_conflicts",
    ]

    async def inspect(self, asset: Asset) -> EnrichmentGapReport:
        """
        Returns:
            EnrichmentGapReport:
                - missing_tables: List[str]  # No row in enrichment table
                - incomplete_tables: Dict[str, List[str]]  # Table exists but fields missing
                - completeness_score: float  # 0.0-1.0
        """
```

**c) JSONBInspector** (`backend/app/services/gap_detection/inspectors/jsonb_inspector.py`)
```python
class JSONBInspector:
    """Inspects JSONB fields for missing nested data."""

    JSONB_FIELDS = ["custom_attributes", "technical_details", "metadata"]

    async def inspect(self, asset: Asset, expected_keys: List[str]) -> JSONBGapReport:
        """
        Args:
            expected_keys: List of expected JSONB keys based on asset type

        Returns:
            JSONBGapReport:
                - missing_keys: Dict[str, List[str]]  # Per JSONB field
                - empty_values: Dict[str, List[str]]
                - completeness_score: float
        """
```

**d) ApplicationInspector** (`backend/app/services/gap_detection/inspectors/application_inspector.py`)
```python
class ApplicationInspector:
    """Inspects CanonicalApplication metadata for completeness."""

    async def inspect(self, application: CanonicalApplication) -> ApplicationGapReport:
        """
        Returns:
            ApplicationGapReport:
                - missing_metadata: List[str]
                - incomplete_tech_stack: bool
                - missing_business_context: List[str]
        """
```

**e) StandardsInspector** (`backend/app/services/gap_detection/inspectors/standards_inspector.py`)
```python
class StandardsInspector:
    """Validates against EngagementArchitectureStandard requirements."""

    async def inspect(
        self,
        asset: Asset,
        application: CanonicalApplication,
        engagement_id: str
    ) -> StandardsGapReport:
        """
        Returns:
            StandardsGapReport:
                - violated_standards: List[StandardViolation]
                - missing_mandatory_data: List[str]
                - override_required: bool
        """
```

#### 2. Context-Aware Requirements Engine

**Purpose**: Determine what data is REQUIRED based on context

**File**: `backend/app/services/gap_detection/requirements/requirements_engine.py`

```python
class RequirementsEngine:
    """Determines required attributes based on context."""

    async def get_requirements(
        self,
        asset_type: str,
        six_r_strategy: Optional[str],
        business_criticality: Optional[str],
        compliance_scopes: List[str],
    ) -> DataRequirements:
        """
        Returns:
            DataRequirements:
                - required_columns: List[str]
                - required_enrichments: List[str]
                - required_jsonb_keys: Dict[str, List[str]]
                - required_standards: List[str]
                - priority_weights: Dict[str, float]
        """
```

**Requirements Matrix** (`backend/app/services/gap_detection/requirements/matrix.py`):

```python
ASSET_TYPE_REQUIREMENTS = {
    "server": {
        "required_columns": ["cpu_cores", "memory_gb", "storage_gb", "operating_system"],
        "required_enrichments": ["resilience"],
        "optional_columns": ["virtualization_platform"],
    },
    "database": {
        "required_columns": ["database_type", "database_version", "data_volume_gb"],
        "required_enrichments": ["resilience", "licenses", "vulnerabilities"],
        "required_jsonb": {"technical_details": ["query_performance", "replication_config"]},
    },
    "application": {
        "required_columns": ["application_type", "technology_stack", "user_base"],
        "required_enrichments": ["dependencies", "licenses"],
        "required_jsonb": {"custom_attributes": ["api_endpoints", "integration_points"]},
    },
    "network_device": {
        "required_columns": ["device_type", "bandwidth_mbps", "routing_protocol"],
        "required_enrichments": ["dependencies"],
        "optional_jsonb": {"technical_details": ["vlan_config", "firewall_rules"]},
    },
}

SIX_R_STRATEGY_REQUIREMENTS = {
    "rehost": {
        "required_columns": ["cpu_cores", "memory_gb", "storage_gb", "operating_system"],
        "required_enrichments": ["resilience"],
        "priority": "infrastructure",
    },
    "replatform": {
        "required_columns": ["technology_stack", "dependencies", "license_type"],
        "required_enrichments": ["licenses", "dependencies"],
        "priority": "compatibility",
    },
    "refactor": {
        "required_columns": ["code_quality_score", "technical_debt_score", "api_contracts"],
        "required_enrichments": ["dependencies", "vulnerabilities"],
        "required_jsonb": {"technical_details": ["architecture_pattern", "integration_complexity"]},
        "priority": "modernization",
    },
    "repurchase": {
        "required_columns": ["annual_operating_cost", "license_costs", "user_base"],
        "required_enrichments": ["licenses"],
        "required_jsonb": {"custom_attributes": ["saas_alternatives", "migration_cost_estimate"]},
        "priority": "financial",
    },
    "retire": {
        "required_columns": ["business_value", "last_update_date", "user_base"],
        "required_jsonb": {"custom_attributes": ["replacement_timeline", "sunset_plan"]},
        "priority": "decommission",
    },
    "retain": {
        "required_columns": ["compliance_requirements", "support_status", "upgrade_path"],
        "required_enrichments": ["compliance_flags", "licenses"],
        "priority": "compliance",
    },
}

COMPLIANCE_REQUIREMENTS = {
    "GDPR": {
        "required_enrichments": ["compliance_flags"],
        "required_jsonb": {"custom_attributes": ["data_residency", "privacy_controls"]},
        "mandatory_standards": ["data_encryption", "access_controls"],
    },
    "HIPAA": {
        "required_enrichments": ["compliance_flags", "vulnerabilities"],
        "required_jsonb": {"custom_attributes": ["phi_handling", "audit_logging"]},
        "mandatory_standards": ["encryption_at_rest", "audit_trails"],
    },
    "PCI-DSS": {
        "required_enrichments": ["compliance_flags", "vulnerabilities"],
        "required_jsonb": {"custom_attributes": ["cardholder_data_flow", "network_segmentation"]},
        "mandatory_standards": ["network_isolation", "vulnerability_scanning"],
    },
}

CRITICALITY_REQUIREMENTS = {
    "tier_1_critical": {
        "required_enrichments": ["resilience", "compliance_flags", "dependencies"],
        "required_standards": ["high_availability", "disaster_recovery"],
        "completeness_threshold": 0.95,  # 95% data completeness required
    },
    "tier_2_important": {
        "required_enrichments": ["resilience"],
        "completeness_threshold": 0.85,
    },
    "tier_3_standard": {
        "completeness_threshold": 0.70,
    },
}
```

#### 3. Gap Analyzer Service

**Purpose**: Orchestrate inspectors and calculate comprehensive gaps

**File**: `backend/app/services/gap_detection/gap_analyzer.py`

```python
class GapAnalyzer:
    """Main service for multi-layer gap analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.column_inspector = ColumnInspector()
        self.enrichment_inspector = EnrichmentInspector()
        self.jsonb_inspector = JSONBInspector()
        self.application_inspector = ApplicationInspector()
        self.standards_inspector = StandardsInspector()
        self.requirements_engine = RequirementsEngine()

    async def analyze_asset(
        self,
        asset: Asset,
        application: Optional[CanonicalApplication] = None,
        engagement_id: Optional[str] = None,
    ) -> ComprehensiveGapReport:
        """
        Performs comprehensive gap analysis across all data layers.

        Returns:
            ComprehensiveGapReport:
                - column_gaps: ColumnGapReport
                - enrichment_gaps: EnrichmentGapReport
                - jsonb_gaps: JSONBGapReport
                - application_gaps: ApplicationGapReport
                - standards_gaps: StandardsGapReport
                - overall_completeness_score: float
                - priority_missing_data: List[MissingDataItem]
                - assessment_ready: bool
                - blocking_gaps: List[str]
        """

        # Step 1: Determine requirements based on context
        requirements = await self.requirements_engine.get_requirements(
            asset_type=asset.asset_type,
            six_r_strategy=asset.six_r_strategy,
            business_criticality=asset.business_criticality,
            compliance_scopes=getattr(asset.compliance_flags, "compliance_scopes", []) if hasattr(asset, "compliance_flags") else [],
        )

        # Step 2: Run all inspectors in parallel
        column_gaps, enrichment_gaps, jsonb_gaps, application_gaps, standards_gaps = await asyncio.gather(
            self.column_inspector.inspect(asset),
            self.enrichment_inspector.inspect(asset),
            self.jsonb_inspector.inspect(asset, requirements.required_jsonb_keys),
            self.application_inspector.inspect(application) if application else None,
            self.standards_inspector.inspect(asset, application, engagement_id) if engagement_id else None,
        )

        # Step 3: Calculate overall completeness
        overall_score = self._calculate_completeness_score(
            column_gaps,
            enrichment_gaps,
            jsonb_gaps,
            application_gaps,
            standards_gaps,
            requirements,
        )

        # Step 4: Identify priority gaps
        priority_gaps = self._prioritize_gaps(
            column_gaps,
            enrichment_gaps,
            jsonb_gaps,
            requirements,
        )

        # Step 5: Determine assessment readiness
        assessment_ready, blocking_gaps = self._check_assessment_readiness(
            overall_score,
            standards_gaps,
            requirements,
        )

        return ComprehensiveGapReport(
            column_gaps=column_gaps,
            enrichment_gaps=enrichment_gaps,
            jsonb_gaps=jsonb_gaps,
            application_gaps=application_gaps,
            standards_gaps=standards_gaps,
            overall_completeness_score=overall_score,
            priority_missing_data=priority_gaps,
            assessment_ready=assessment_ready,
            blocking_gaps=blocking_gaps,
        )
```

#### 4. Intelligent Questionnaire Generator

**Purpose**: Generate targeted questions based on actual gaps

**File**: `backend/app/services/gap_detection/questionnaire_generator.py`

```python
class IntelligentQuestionnaireGenerator:
    """Generates context-aware questionnaires based on gap analysis."""

    async def generate_questionnaire(
        self,
        gap_report: ComprehensiveGapReport,
        asset: Asset,
        application: Optional[CanonicalApplication] = None,
    ) -> AdaptiveQuestionnaire:
        """
        Generates adaptive questionnaire focusing on missing data.

        Strategy:
        1. Skip questions for data that already exists
        2. Prioritize by business impact (criticality × gap priority)
        3. Group by category for better UX
        4. Add conditional logic (e.g., if compliance scope = GDPR, ask privacy controls)

        Returns:
            AdaptiveQuestionnaire:
                - sections: List[QuestionnaireSection]
                - total_questions: int
                - estimated_completion_time: int  # minutes
                - priority_order: List[str]  # section names
        """

        sections = []

        # Infrastructure section (only if column gaps exist)
        if gap_report.column_gaps.missing_attributes:
            infrastructure_section = self._build_infrastructure_section(
                gap_report.column_gaps,
                asset.asset_type,
            )
            sections.append(infrastructure_section)

        # Resilience section (only if enrichment gaps exist)
        if "resilience" in gap_report.enrichment_gaps.missing_tables:
            resilience_section = self._build_resilience_section(
                asset.business_criticality,
            )
            sections.append(resilience_section)

        # Compliance section (only if compliance gaps exist)
        if gap_report.standards_gaps and gap_report.standards_gaps.violated_standards:
            compliance_section = self._build_compliance_section(
                gap_report.standards_gaps,
                asset.compliance_flags.compliance_scopes if hasattr(asset, "compliance_flags") else [],
            )
            sections.append(compliance_section)

        # Dependencies section (only if enrichment gaps exist)
        if "dependencies" in gap_report.enrichment_gaps.missing_tables:
            dependencies_section = self._build_dependencies_section(
                asset.application_type,
            )
            sections.append(dependencies_section)

        # Technical debt section (only if 6R strategy is refactor/modernize)
        if asset.six_r_strategy in ["refactor", "modernize"] and gap_report.jsonb_gaps:
            tech_debt_section = self._build_tech_debt_section(
                gap_report.jsonb_gaps,
            )
            sections.append(tech_debt_section)

        # Sort sections by priority
        sections = self._prioritize_sections(sections, gap_report.priority_missing_data)

        return AdaptiveQuestionnaire(
            sections=sections,
            total_questions=sum(len(s.questions) for s in sections),
            estimated_completion_time=self._estimate_time(sections),
            priority_order=[s.name for s in sections],
        )
```

---

## Implementation Plan

### Week 2: Core Infrastructure (Days 6-10)

#### **Day 6: Repository Setup & Schema**

**Tasks**:
1. Create new service directory structure
2. Define Pydantic schemas for gap reports
3. Set up unit test framework

**Deliverables**:
```
backend/app/services/gap_detection/
├── __init__.py
├── gap_analyzer.py
├── inspectors/
│   ├── __init__.py
│   ├── base.py
│   ├── column_inspector.py
│   ├── enrichment_inspector.py
│   ├── jsonb_inspector.py
│   ├── application_inspector.py
│   └── standards_inspector.py
├── requirements/
│   ├── __init__.py
│   ├── requirements_engine.py
│   └── matrix.py
├── questionnaire_generator.py
└── schemas.py
```

**Schemas** (`backend/app/services/gap_detection/schemas.py`):
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ColumnGapReport(BaseModel):
    missing_attributes: List[str]
    empty_attributes: List[str]
    null_attributes: List[str]

class EnrichmentGapReport(BaseModel):
    missing_tables: List[str]
    incomplete_tables: Dict[str, List[str]]
    completeness_score: float = Field(ge=0.0, le=1.0)

class JSONBGapReport(BaseModel):
    missing_keys: Dict[str, List[str]]
    empty_values: Dict[str, List[str]]
    completeness_score: float = Field(ge=0.0, le=1.0)

class ApplicationGapReport(BaseModel):
    missing_metadata: List[str]
    incomplete_tech_stack: bool
    missing_business_context: List[str]

class StandardViolation(BaseModel):
    standard_name: str
    requirement_type: str
    violation_details: str
    is_mandatory: bool
    override_available: bool

class StandardsGapReport(BaseModel):
    violated_standards: List[StandardViolation]
    missing_mandatory_data: List[str]
    override_required: bool

class MissingDataItem(BaseModel):
    attribute_name: str
    data_layer: str  # "column", "enrichment", "jsonb", "application", "standard"
    priority: int  # 1=critical, 2=important, 3=optional
    reason: str
    estimated_effort: str  # "quick", "moderate", "complex"

class ComprehensiveGapReport(BaseModel):
    column_gaps: ColumnGapReport
    enrichment_gaps: EnrichmentGapReport
    jsonb_gaps: JSONBGapReport
    application_gaps: Optional[ApplicationGapReport]
    standards_gaps: Optional[StandardsGapReport]
    overall_completeness_score: float = Field(ge=0.0, le=1.0)
    priority_missing_data: List[MissingDataItem]
    assessment_ready: bool
    blocking_gaps: List[str]

class DataRequirements(BaseModel):
    required_columns: List[str]
    required_enrichments: List[str]
    required_jsonb_keys: Dict[str, List[str]]
    required_standards: List[str]
    priority_weights: Dict[str, float]
    completeness_threshold: float = Field(ge=0.0, le=1.0)
```

**Test Files**:
```
backend/tests/services/gap_detection/
├── test_column_inspector.py
├── test_enrichment_inspector.py
├── test_gap_analyzer.py
└── fixtures.py
```

**Acceptance Criteria**:
- [ ] Directory structure created
- [ ] All Pydantic schemas defined with validation
- [ ] Base inspector class with interface contract
- [ ] Unit test framework set up with pytest fixtures

---

#### **Day 7: Inspector Implementation (Columns & Enrichments)**

**Tasks**:
1. Implement ColumnInspector
2. Implement EnrichmentInspector
3. Write unit tests

**ColumnInspector Implementation**:
```python
class ColumnInspector:
    """Inspects Asset SQLAlchemy columns for missing data."""

    EXCLUDED_COLUMNS = [
        "id", "created_at", "updated_at", "deleted_at",
        "client_account_id", "engagement_id", "user_id",
        "flow_id", "master_flow_id", "phase_context",
    ]

    def inspect(self, asset: Asset) -> ColumnGapReport:
        """Inspect asset columns for missing data."""

        # Get all column attributes from SQLAlchemy model
        column_names = [
            c.name for c in asset.__table__.columns
            if c.name not in self.EXCLUDED_COLUMNS
        ]

        missing_attributes = []
        empty_attributes = []
        null_attributes = []

        for col_name in column_names:
            value = getattr(asset, col_name, None)

            if value is None:
                null_attributes.append(col_name)
                missing_attributes.append(col_name)
            elif isinstance(value, str) and not value.strip():
                empty_attributes.append(col_name)
                missing_attributes.append(col_name)
            elif isinstance(value, list) and len(value) == 0:
                empty_attributes.append(col_name)
                missing_attributes.append(col_name)
            elif isinstance(value, dict) and len(value) == 0:
                empty_attributes.append(col_name)
                missing_attributes.append(col_name)

        return ColumnGapReport(
            missing_attributes=missing_attributes,
            empty_attributes=empty_attributes,
            null_attributes=null_attributes,
        )
```

**EnrichmentInspector Implementation**:
```python
class EnrichmentInspector:
    """Inspects 7 enrichment tables for missing data."""

    ENRICHMENT_CONFIG = {
        "resilience": {
            "relationship_name": "resilience",
            "required_fields": ["rto_minutes", "rpo_minutes"],
            "optional_fields": ["sla_json"],
        },
        "compliance_flags": {
            "relationship_name": "compliance_flags",
            "required_fields": ["compliance_scopes", "data_classification"],
            "optional_fields": ["residency"],
        },
        "vulnerabilities": {
            "relationship_name": "vulnerabilities",
            "required_fields": [],  # At least one record should exist
            "optional_fields": ["cve_id", "severity"],
        },
        "licenses": {
            "relationship_name": "licenses",
            "required_fields": ["license_type"],
            "optional_fields": ["renewal_date", "support_tier"],
        },
        "dependencies": {
            "relationship_name": "dependencies",
            "required_fields": [],  # At least one record should exist
            "optional_fields": ["dependency_type", "criticality"],
        },
        "product_links": {
            "relationship_name": "product_links",
            "required_fields": [],
            "optional_fields": ["manufacturer_support", "eol_date"],
        },
        "field_conflicts": {
            "relationship_name": "field_conflicts",
            "required_fields": [],
            "optional_fields": ["conflict_type", "resolution_status"],
        },
    }

    def inspect(self, asset: Asset) -> EnrichmentGapReport:
        """Inspect enrichment tables for missing data."""

        missing_tables = []
        incomplete_tables = {}
        total_tables = len(self.ENRICHMENT_CONFIG)
        complete_tables = 0

        for table_name, config in self.ENRICHMENT_CONFIG.items():
            relationship_data = getattr(asset, config["relationship_name"], None)

            if relationship_data is None:
                missing_tables.append(table_name)
            elif isinstance(relationship_data, list) and len(relationship_data) == 0:
                missing_tables.append(table_name)
            else:
                # Check for incomplete fields
                missing_fields = []

                # Handle 1:1 relationships
                if not isinstance(relationship_data, list):
                    for field in config["required_fields"]:
                        value = getattr(relationship_data, field, None)
                        if value is None or (isinstance(value, (str, list)) and len(value) == 0):
                            missing_fields.append(field)

                if missing_fields:
                    incomplete_tables[table_name] = missing_fields
                else:
                    complete_tables += 1

        completeness_score = complete_tables / total_tables if total_tables > 0 else 0.0

        return EnrichmentGapReport(
            missing_tables=missing_tables,
            incomplete_tables=incomplete_tables,
            completeness_score=completeness_score,
        )
```

**Unit Tests** (`test_column_inspector.py`):
```python
import pytest
from app.services.gap_detection.inspectors.column_inspector import ColumnInspector
from app.models import Asset

def test_column_inspector_all_complete():
    asset = Asset(
        asset_name="Test Server",
        operating_system="Linux",
        cpu_cores=4,
        memory_gb=16.0,
    )

    inspector = ColumnInspector()
    report = inspector.inspect(asset)

    assert "asset_name" not in report.missing_attributes
    assert "operating_system" not in report.missing_attributes

def test_column_inspector_missing_data():
    asset = Asset(
        asset_name="Test Server",
        operating_system=None,  # Missing
        cpu_cores=4,
    )

    inspector = ColumnInspector()
    report = inspector.inspect(asset)

    assert "operating_system" in report.missing_attributes
    assert "operating_system" in report.null_attributes

def test_column_inspector_empty_string():
    asset = Asset(
        asset_name="",  # Empty string
        operating_system="Linux",
    )

    inspector = ColumnInspector()
    report = inspector.inspect(asset)

    assert "asset_name" in report.missing_attributes
    assert "asset_name" in report.empty_attributes
```

**Acceptance Criteria**:
- [ ] ColumnInspector scans all non-system columns
- [ ] EnrichmentInspector checks all 7 enrichment tables
- [ ] Handles 1:1 and 1:many relationships correctly
- [ ] Unit tests achieve >90% coverage
- [ ] Performance: <50ms per asset inspection

---

#### **Day 8: Inspector Implementation (JSONB, Application, Standards)**

**Tasks**:
1. Implement JSONBInspector
2. Implement ApplicationInspector
3. Implement StandardsInspector
4. Write unit tests

**JSONBInspector Implementation**:
```python
class JSONBInspector:
    """Inspects JSONB fields for missing nested data."""

    JSONB_FIELDS = ["custom_attributes", "technical_details", "metadata"]

    def inspect(self, asset: Asset, expected_keys: Dict[str, List[str]]) -> JSONBGapReport:
        """
        Inspect JSONB fields for missing keys.

        Args:
            asset: Asset to inspect
            expected_keys: Dict of JSONB field → list of expected keys
                           e.g., {"custom_attributes": ["api_endpoints", "integration_points"]}
        """

        missing_keys = {}
        empty_values = {}
        total_expected = 0
        total_found = 0

        for jsonb_field, keys in expected_keys.items():
            jsonb_data = getattr(asset, jsonb_field, None) or {}

            field_missing = []
            field_empty = []

            for key in keys:
                total_expected += 1

                if key not in jsonb_data:
                    field_missing.append(key)
                elif jsonb_data[key] is None or jsonb_data[key] == "":
                    field_empty.append(key)
                else:
                    total_found += 1

            if field_missing:
                missing_keys[jsonb_field] = field_missing
            if field_empty:
                empty_values[jsonb_field] = field_empty

        completeness_score = total_found / total_expected if total_expected > 0 else 1.0

        return JSONBGapReport(
            missing_keys=missing_keys,
            empty_values=empty_values,
            completeness_score=completeness_score,
        )
```

**ApplicationInspector Implementation**:
```python
class ApplicationInspector:
    """Inspects CanonicalApplication metadata for completeness."""

    REQUIRED_METADATA = [
        "description",
        "application_type",
        "business_criticality",
    ]

    def inspect(self, application: CanonicalApplication) -> ApplicationGapReport:
        """Inspect application metadata."""

        missing_metadata = []

        for field in self.REQUIRED_METADATA:
            value = getattr(application, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_metadata.append(field)

        # Check technology stack (JSONB field)
        tech_stack = application.technology_stack or {}
        incomplete_tech_stack = len(tech_stack) == 0

        # Check business context
        missing_business_context = []
        if not application.business_owner:
            missing_business_context.append("business_owner")
        if not application.primary_contact:
            missing_business_context.append("primary_contact")

        return ApplicationGapReport(
            missing_metadata=missing_metadata,
            incomplete_tech_stack=incomplete_tech_stack,
            missing_business_context=missing_business_context,
        )
```

**StandardsInspector Implementation**:
```python
class StandardsInspector:
    """Validates against EngagementArchitectureStandard requirements."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def inspect(
        self,
        asset: Asset,
        application: Optional[CanonicalApplication],
        engagement_id: str,
    ) -> StandardsGapReport:
        """Validate asset against architecture standards."""

        # Fetch engagement standards
        from app.models.assessment_flow import EngagementArchitectureStandard

        result = await self.db.execute(
            select(EngagementArchitectureStandard).where(
                EngagementArchitectureStandard.engagement_id == engagement_id
            )
        )
        standards = result.scalars().all()

        violated_standards = []
        missing_mandatory_data = []
        override_required = False

        for standard in standards:
            # Check minimum requirements
            violations = self._check_standard_compliance(
                asset,
                application,
                standard,
            )

            if violations:
                violated_standards.extend(violations)

                if standard.is_mandatory:
                    missing_mandatory_data.extend([v.violation_details for v in violations])
                    override_required = True

        return StandardsGapReport(
            violated_standards=violated_standards,
            missing_mandatory_data=missing_mandatory_data,
            override_required=override_required,
        )

    def _check_standard_compliance(
        self,
        asset: Asset,
        application: Optional[CanonicalApplication],
        standard: EngagementArchitectureStandard,
    ) -> List[StandardViolation]:
        """Check if asset complies with a specific standard."""

        violations = []

        # Example: Security standard requiring encryption
        if standard.requirement_type == "security":
            min_reqs = standard.minimum_requirements or {}

            if min_reqs.get("encryption_required") and not self._has_encryption(asset):
                violations.append(StandardViolation(
                    standard_name=standard.standard_name,
                    requirement_type=standard.requirement_type,
                    violation_details="Encryption at rest not configured",
                    is_mandatory=standard.is_mandatory,
                    override_available=not standard.is_mandatory,
                ))

        return violations
```

**Acceptance Criteria**:
- [ ] JSONBInspector handles nested JSONB structures
- [ ] ApplicationInspector validates CanonicalApplication metadata
- [ ] StandardsInspector fetches and validates against engagement standards
- [ ] Unit tests for all 3 inspectors
- [ ] Integration test with real database fixtures

---

#### **Day 9: Requirements Engine Implementation**

**Tasks**:
1. Implement RequirementsEngine
2. Define requirements matrix
3. Write unit tests

**RequirementsEngine Implementation** (see earlier in architecture section)

**Requirements Matrix** (see earlier in architecture section)

**Unit Tests** (`test_requirements_engine.py`):
```python
import pytest
from app.services.gap_detection.requirements.requirements_engine import RequirementsEngine

@pytest.mark.asyncio
async def test_server_rehost_requirements():
    engine = RequirementsEngine()

    requirements = await engine.get_requirements(
        asset_type="server",
        six_r_strategy="rehost",
        business_criticality="tier_1_critical",
        compliance_scopes=[],
    )

    assert "cpu_cores" in requirements.required_columns
    assert "memory_gb" in requirements.required_columns
    assert "resilience" in requirements.required_enrichments
    assert requirements.completeness_threshold == 0.95  # Tier 1 requires 95%

@pytest.mark.asyncio
async def test_application_refactor_requirements():
    engine = RequirementsEngine()

    requirements = await engine.get_requirements(
        asset_type="application",
        six_r_strategy="refactor",
        business_criticality="tier_2_important",
        compliance_scopes=["GDPR"],
    )

    assert "code_quality_score" in requirements.required_columns
    assert "dependencies" in requirements.required_enrichments
    assert "compliance_flags" in requirements.required_enrichments  # Because GDPR
    assert "architecture_pattern" in requirements.required_jsonb_keys.get("technical_details", [])

@pytest.mark.asyncio
async def test_database_with_compliance():
    engine = RequirementsEngine()

    requirements = await engine.get_requirements(
        asset_type="database",
        six_r_strategy="replatform",
        business_criticality="tier_1_critical",
        compliance_scopes=["HIPAA", "PCI-DSS"],
    )

    assert "compliance_flags" in requirements.required_enrichments
    assert "vulnerabilities" in requirements.required_enrichments
    assert "phi_handling" in requirements.required_jsonb_keys.get("custom_attributes", [])
```

**Acceptance Criteria**:
- [ ] RequirementsEngine merges requirements from multiple contexts
- [ ] Requirements matrix covers all asset types, 6R strategies, compliance scopes
- [ ] Priority weights calculated correctly
- [ ] Unit tests for all requirement combinations
- [ ] Documentation on adding new requirement types

---

#### **Day 10: Gap Analyzer Service Implementation**

**Tasks**:
1. Implement main GapAnalyzer service
2. Implement completeness scoring algorithm
3. Implement gap prioritization
4. Write integration tests

**GapAnalyzer Implementation** (see earlier in architecture section)

**Completeness Scoring Algorithm**:
```python
def _calculate_completeness_score(
    self,
    column_gaps: ColumnGapReport,
    enrichment_gaps: EnrichmentGapReport,
    jsonb_gaps: JSONBGapReport,
    application_gaps: Optional[ApplicationGapReport],
    standards_gaps: Optional[StandardsGapReport],
    requirements: DataRequirements,
) -> float:
    """
    Calculate weighted completeness score.

    Scoring:
    - Columns: 40% weight
    - Enrichments: 30% weight
    - JSONB: 15% weight
    - Application: 10% weight
    - Standards: 5% weight (compliance penalty)
    """

    # Column score
    required_columns = requirements.required_columns
    missing_required_columns = [
        attr for attr in column_gaps.missing_attributes
        if attr in required_columns
    ]
    column_score = 1.0 - (len(missing_required_columns) / len(required_columns)) if required_columns else 1.0

    # Enrichment score (already 0.0-1.0)
    enrichment_score = enrichment_gaps.completeness_score

    # JSONB score (already 0.0-1.0)
    jsonb_score = jsonb_gaps.completeness_score

    # Application score
    application_score = 1.0
    if application_gaps:
        total_app_fields = 6  # description, type, criticality, tech_stack, owner, contact
        missing_app_fields = (
            len(application_gaps.missing_metadata) +
            (1 if application_gaps.incomplete_tech_stack else 0) +
            len(application_gaps.missing_business_context)
        )
        application_score = 1.0 - (missing_app_fields / total_app_fields)

    # Standards penalty
    standards_penalty = 0.0
    if standards_gaps and standards_gaps.violated_standards:
        mandatory_violations = [v for v in standards_gaps.violated_standards if v.is_mandatory]
        standards_penalty = len(mandatory_violations) * 0.1  # 10% penalty per mandatory violation

    # Weighted average
    weighted_score = (
        column_score * 0.40 +
        enrichment_score * 0.30 +
        jsonb_score * 0.15 +
        application_score * 0.10
    ) - standards_penalty

    return max(0.0, min(1.0, weighted_score))  # Clamp to 0.0-1.0
```

**Gap Prioritization**:
```python
def _prioritize_gaps(
    self,
    column_gaps: ColumnGapReport,
    enrichment_gaps: EnrichmentGapReport,
    jsonb_gaps: JSONBGapReport,
    requirements: DataRequirements,
) -> List[MissingDataItem]:
    """Prioritize missing data items by business impact."""

    priority_gaps = []

    # Priority 1: Required columns missing
    for attr in column_gaps.missing_attributes:
        if attr in requirements.required_columns:
            priority_gaps.append(MissingDataItem(
                attribute_name=attr,
                data_layer="column",
                priority=1,
                reason="Required for assessment",
                estimated_effort="quick",
            ))

    # Priority 2: Required enrichments missing
    for table in enrichment_gaps.missing_tables:
        if table in requirements.required_enrichments:
            priority_gaps.append(MissingDataItem(
                attribute_name=table,
                data_layer="enrichment",
                priority=1 if table == "resilience" else 2,
                reason=f"Required enrichment table for {table} data",
                estimated_effort="moderate",
            ))

    # Priority 2: Incomplete enrichments
    for table, fields in enrichment_gaps.incomplete_tables.items():
        for field in fields:
            priority_gaps.append(MissingDataItem(
                attribute_name=f"{table}.{field}",
                data_layer="enrichment",
                priority=2,
                reason=f"Required field in {table} table",
                estimated_effort="quick",
            ))

    # Priority 3: Required JSONB keys
    for jsonb_field, keys in jsonb_gaps.missing_keys.items():
        for key in keys:
            if key in requirements.required_jsonb_keys.get(jsonb_field, []):
                priority_gaps.append(MissingDataItem(
                    attribute_name=f"{jsonb_field}.{key}",
                    data_layer="jsonb",
                    priority=2,
                    reason=f"Required for {requirements.priority_weights.get('priority', 'assessment')}",
                    estimated_effort="moderate",
                ))

    # Sort by priority
    priority_gaps.sort(key=lambda x: x.priority)

    return priority_gaps
```

**Integration Tests** (`test_gap_analyzer_integration.py`):
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.gap_detection.gap_analyzer import GapAnalyzer
from app.models import Asset, CanonicalApplication

@pytest.mark.asyncio
async def test_gap_analyzer_server_rehost(db: AsyncSession):
    # Create test asset
    asset = Asset(
        asset_name="Test Server",
        asset_type="server",
        six_r_strategy="rehost",
        business_criticality="tier_1_critical",
        operating_system="Linux",
        cpu_cores=4,
        memory_gb=16.0,
        # Missing: storage_gb, resilience table
    )

    analyzer = GapAnalyzer(db)
    report = await analyzer.analyze_asset(asset)

    assert report.overall_completeness_score < 1.0
    assert not report.assessment_ready  # Tier 1 requires 95% completeness
    assert "storage_gb" in [item.attribute_name for item in report.priority_missing_data]
    assert "resilience" in [item.attribute_name for item in report.priority_missing_data]

@pytest.mark.asyncio
async def test_gap_analyzer_complete_asset(db: AsyncSession):
    # Create fully populated asset
    asset = Asset(
        asset_name="Complete Server",
        asset_type="server",
        six_r_strategy="rehost",
        business_criticality="tier_2_important",
        operating_system="Linux",
        cpu_cores=4,
        memory_gb=16.0,
        storage_gb=500.0,
        # Assume resilience table exists
    )

    analyzer = GapAnalyzer(db)
    report = await analyzer.analyze_asset(asset)

    assert report.overall_completeness_score >= 0.85  # Tier 2 threshold
    assert report.assessment_ready
    assert len(report.blocking_gaps) == 0
```

**Acceptance Criteria**:
- [ ] GapAnalyzer orchestrates all inspectors correctly
- [ ] Completeness scoring matches business requirements
- [ ] Gap prioritization orders by business impact
- [ ] Assessment readiness check respects criticality thresholds
- [ ] Integration tests with database fixtures pass
- [ ] Performance: <200ms for full asset analysis

---

### Week 3: API Integration & Frontend (Days 11-15)

#### **Day 11: API Endpoint Implementation**

**Tasks**:
1. Replace `get_missing_critical_attributes()` with `GapAnalyzer`
2. Update assessment readiness endpoint
3. Add new gap detail endpoint
4. Write API tests

**Update Assessment Helpers** (`backend/app/api/v1/master_flows/assessment/helpers.py`):
```python
# BEFORE (REMOVE):
def get_missing_critical_attributes(asset: Any) -> List[str]:
    critical_attrs = [...22 hardcoded...]  # ❌ DELETE THIS

# AFTER (NEW):
async def get_comprehensive_gap_analysis(
    asset: Asset,
    application: Optional[CanonicalApplication],
    engagement_id: str,
    db: AsyncSession,
) -> ComprehensiveGapReport:
    """
    Replacement for get_missing_critical_attributes().
    Returns comprehensive gap analysis instead of simple list.
    """
    from app.services.gap_detection.gap_analyzer import GapAnalyzer

    analyzer = GapAnalyzer(db)
    return await analyzer.analyze_asset(
        asset=asset,
        application=application,
        engagement_id=engagement_id,
    )
```

**Update Assessment Readiness Endpoint** (`backend/app/api/v1/master_flows/assessment/info_endpoints.py`):
```python
# BEFORE (lines 234-275):
for asset in assets:
    missing_attrs = get_missing_critical_attributes(asset)  # ❌ OLD
    asset_details.append({
        "asset_id": str(asset.id),
        "asset_name": asset.asset_name,
        "missing_count": len(missing_attrs),
        "missing_attributes": missing_attrs,
    })

# AFTER:
for asset in assets:
    # Fetch canonical application
    application = await get_canonical_application_for_asset(db, asset)

    # Get comprehensive gap analysis
    gap_report = await get_comprehensive_gap_analysis(
        asset=asset,
        application=application,
        engagement_id=engagement_id,
        db=db,
    )

    asset_details.append({
        "asset_id": str(asset.id),
        "asset_name": asset.asset_name,
        "completeness_score": gap_report.overall_completeness_score,
        "assessment_ready": gap_report.assessment_ready,
        "missing_count": len(gap_report.priority_missing_data),
        # Detailed gap breakdown
        "gap_summary": {
            "column_gaps": len(gap_report.column_gaps.missing_attributes),
            "enrichment_gaps": len(gap_report.enrichment_gaps.missing_tables),
            "jsonb_gaps": sum(len(keys) for keys in gap_report.jsonb_gaps.missing_keys.values()),
            "standards_violations": len(gap_report.standards_gaps.violated_standards) if gap_report.standards_gaps else 0,
        },
        # Priority missing data for collection
        "missing_attributes": {
            "infrastructure": [
                item.attribute_name for item in gap_report.priority_missing_data
                if item.data_layer == "column"
            ],
            "enrichments": [
                item.attribute_name for item in gap_report.priority_missing_data
                if item.data_layer == "enrichment"
            ],
            "technical_details": [
                item.attribute_name for item in gap_report.priority_missing_data
                if item.data_layer == "jsonb"
            ],
            "standards_compliance": [
                v.violation_details for v in (gap_report.standards_gaps.violated_standards or [])
                if gap_report.standards_gaps
            ],
        },
        "blocking_gaps": gap_report.blocking_gaps,
    })
```

**New Gap Detail Endpoint** (`backend/app/api/v1/master_flows/assessment/info_endpoints.py`):
```python
@router.get("/{flow_id}/asset-gap-detail/{asset_id}")
async def get_asset_gap_detail(
    flow_id: str,
    asset_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get detailed gap analysis for a specific asset.

    Returns comprehensive breakdown of missing data across all layers.
    """

    # Fetch asset
    asset = await db.get(Asset, UUID(asset_id))
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Fetch canonical application
    application = await get_canonical_application_for_asset(db, asset)

    # Get comprehensive gap analysis
    gap_report = await get_comprehensive_gap_analysis(
        asset=asset,
        application=application,
        engagement_id=context.engagement_id,
        db=db,
    )

    return {
        "asset_id": asset_id,
        "asset_name": asset.asset_name,
        "asset_type": asset.asset_type,
        "six_r_strategy": asset.six_r_strategy,
        "business_criticality": asset.business_criticality,
        "gap_analysis": {
            "overall_completeness": gap_report.overall_completeness_score,
            "assessment_ready": gap_report.assessment_ready,
            "blocking_gaps": gap_report.blocking_gaps,

            # Layer-by-layer breakdown
            "column_gaps": {
                "missing": gap_report.column_gaps.missing_attributes,
                "empty": gap_report.column_gaps.empty_attributes,
                "null": gap_report.column_gaps.null_attributes,
            },
            "enrichment_gaps": {
                "missing_tables": gap_report.enrichment_gaps.missing_tables,
                "incomplete_tables": gap_report.enrichment_gaps.incomplete_tables,
                "completeness": gap_report.enrichment_gaps.completeness_score,
            },
            "jsonb_gaps": {
                "missing_keys": gap_report.jsonb_gaps.missing_keys,
                "empty_values": gap_report.jsonb_gaps.empty_values,
                "completeness": gap_report.jsonb_gaps.completeness_score,
            },
            "application_gaps": {
                "missing_metadata": gap_report.application_gaps.missing_metadata if gap_report.application_gaps else [],
                "incomplete_tech_stack": gap_report.application_gaps.incomplete_tech_stack if gap_report.application_gaps else False,
                "missing_business_context": gap_report.application_gaps.missing_business_context if gap_report.application_gaps else [],
            } if gap_report.application_gaps else None,
            "standards_gaps": {
                "violations": [
                    {
                        "standard_name": v.standard_name,
                        "requirement_type": v.requirement_type,
                        "violation_details": v.violation_details,
                        "is_mandatory": v.is_mandatory,
                        "override_available": v.override_available,
                    }
                    for v in gap_report.standards_gaps.violated_standards
                ],
                "missing_mandatory_data": gap_report.standards_gaps.missing_mandatory_data,
                "override_required": gap_report.standards_gaps.override_required,
            } if gap_report.standards_gaps else None,

            # Priority action items
            "priority_missing_data": [
                {
                    "attribute_name": item.attribute_name,
                    "data_layer": item.data_layer,
                    "priority": item.priority,
                    "reason": item.reason,
                    "estimated_effort": item.estimated_effort,
                }
                for item in gap_report.priority_missing_data
            ],
        },
    }
```

**API Tests** (`backend/tests/api/v1/master_flows/assessment/test_gap_endpoints.py`):
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_assessment_readiness_with_gaps(client: AsyncClient, test_flow_id: str):
    response = await client.get(f"/api/v1/master-flows/{test_flow_id}/assessment-readiness")

    assert response.status_code == 200
    data = response.json()

    assert "asset_details" in data
    assert len(data["asset_details"]) > 0

    asset = data["asset_details"][0]
    assert "completeness_score" in asset
    assert "assessment_ready" in asset
    assert "gap_summary" in asset
    assert "blocking_gaps" in asset

@pytest.mark.asyncio
async def test_asset_gap_detail(client: AsyncClient, test_flow_id: str, test_asset_id: str):
    response = await client.get(
        f"/api/v1/master-flows/{test_flow_id}/asset-gap-detail/{test_asset_id}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "gap_analysis" in data
    gap = data["gap_analysis"]

    assert "overall_completeness" in gap
    assert "column_gaps" in gap
    assert "enrichment_gaps" in gap
    assert "priority_missing_data" in gap
```

**Acceptance Criteria**:
- [ ] Old `get_missing_critical_attributes()` fully replaced
- [ ] Assessment readiness endpoint returns new gap format
- [ ] New gap detail endpoint implemented
- [ ] API tests pass with >90% coverage
- [ ] Backward compatibility maintained for frontend during transition

---

#### **Day 12: Frontend - Readiness Dashboard Update**

**Tasks**:
1. Update TypeScript interfaces
2. Enhance ReadinessDashboardWidget to show detailed gaps
3. Add gap breakdown visualization
4. Update "Collect Missing Data" button logic

**TypeScript Interfaces** (`src/types/assessment.ts`):
```typescript
// Add new gap analysis types
export interface GapSummary {
  column_gaps: number;
  enrichment_gaps: number;
  jsonb_gaps: number;
  standards_violations: number;
}

export interface MissingAttributesByCategory {
  infrastructure: string[];
  enrichments: string[];
  technical_details: string[];
  standards_compliance: string[];
}

export interface AssetReadinessDetail {
  asset_id: string;
  asset_name: string;
  completeness_score: number;
  assessment_ready: boolean;
  missing_count: number;
  gap_summary: GapSummary;
  missing_attributes: MissingAttributesByCategory;
  blocking_gaps: string[];
}

export interface AssessmentReadinessData {
  flow_id: string;
  total_applications: number;
  ready_count: number;
  not_ready_count: number;
  average_completeness: number;
  asset_details: AssetReadinessDetail[];
}
```

**Update ReadinessDashboardWidget** (`src/components/assessment/ReadinessDashboardWidget.tsx`):
```typescript
// Update rendering to show completeness score
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {readinessData.asset_details.map((asset) => (
    <Card key={asset.asset_id} className="relative">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{asset.asset_name}</span>
          {/* Completeness badge */}
          <Badge variant={asset.assessment_ready ? "success" : "warning"}>
            {Math.round(asset.completeness_score * 100)}%
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Gap breakdown */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Column Gaps:</span>
            <span className={asset.gap_summary.column_gaps > 0 ? "text-red-500" : "text-green-500"}>
              {asset.gap_summary.column_gaps}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Enrichment Gaps:</span>
            <span className={asset.gap_summary.enrichment_gaps > 0 ? "text-yellow-500" : "text-green-500"}>
              {asset.gap_summary.enrichment_gaps}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Technical Details:</span>
            <span className={asset.gap_summary.jsonb_gaps > 0 ? "text-orange-500" : "text-green-500"}>
              {asset.gap_summary.jsonb_gaps}
            </span>
          </div>
          {asset.gap_summary.standards_violations > 0 && (
            <div className="flex justify-between text-sm">
              <span>Standards Violations:</span>
              <span className="text-red-600 font-semibold">
                {asset.gap_summary.standards_violations}
              </span>
            </div>
          )}
        </div>

        {/* Blocking gaps warning */}
        {asset.blocking_gaps.length > 0 && (
          <Alert variant="destructive" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Blocking Issues</AlertTitle>
            <AlertDescription>
              <ul className="list-disc list-inside">
                {asset.blocking_gaps.map((gap, idx) => (
                  <li key={idx}>{gap}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* View details button */}
        <Button
          variant="outline"
          size="sm"
          className="mt-4 w-full"
          onClick={() => handleViewGapDetails(asset.asset_id)}
        >
          View Gap Details
        </Button>
      </CardContent>
    </Card>
  ))}
</div>

{/* Collect Missing Data button */}
<Button
  onClick={handleCollectMissingData}
  disabled={readinessData.asset_details.every(a => a.assessment_ready)}
  className="mt-6"
>
  Collect Missing Data ({readinessData.not_ready_count} assets)
</Button>
```

**Gap Details Modal** (`src/components/assessment/GapDetailsModal.tsx`):
```typescript
import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface GapDetailsModalProps {
  assetId: string;
  flowId: string;
  open: boolean;
  onClose: () => void;
}

export const GapDetailsModal: React.FC<GapDetailsModalProps> = ({
  assetId,
  flowId,
  open,
  onClose,
}) => {
  const { data: gapDetail, isLoading } = useQuery({
    queryKey: ['asset-gap-detail', flowId, assetId],
    queryFn: () => assessmentFlowApi.getAssetGapDetail(flowId, assetId),
    enabled: open && !!assetId,
  });

  if (isLoading) return <div>Loading...</div>;
  if (!gapDetail) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Gap Analysis: {gapDetail.asset_name}
          </DialogTitle>
        </DialogHeader>

        {/* Overall completeness */}
        <div className="mb-6">
          <div className="flex justify-between mb-2">
            <span className="font-semibold">Overall Completeness</span>
            <span>{Math.round(gapDetail.gap_analysis.overall_completeness * 100)}%</span>
          </div>
          <Progress value={gapDetail.gap_analysis.overall_completeness * 100} />
        </div>

        {/* Layer-by-layer breakdown */}
        <Tabs defaultValue="columns">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="columns">
              Columns
              <Badge variant="outline" className="ml-2">
                {gapDetail.gap_analysis.column_gaps.missing.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="enrichments">
              Enrichments
              <Badge variant="outline" className="ml-2">
                {gapDetail.gap_analysis.enrichment_gaps.missing_tables.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="technical">
              Technical
              <Badge variant="outline" className="ml-2">
                {Object.keys(gapDetail.gap_analysis.jsonb_gaps.missing_keys).length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="standards">
              Standards
              <Badge variant="outline" className="ml-2">
                {gapDetail.gap_analysis.standards_gaps?.violations.length || 0}
              </Badge>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="columns" className="space-y-4">
            <h3 className="font-semibold">Missing Columns</h3>
            <ul className="list-disc list-inside space-y-1">
              {gapDetail.gap_analysis.column_gaps.missing.map((attr) => (
                <li key={attr} className="text-sm">{attr}</li>
              ))}
            </ul>
          </TabsContent>

          <TabsContent value="enrichments" className="space-y-4">
            <h3 className="font-semibold">Missing Enrichment Tables</h3>
            <ul className="list-disc list-inside space-y-1">
              {gapDetail.gap_analysis.enrichment_gaps.missing_tables.map((table) => (
                <li key={table} className="text-sm">{table}</li>
              ))}
            </ul>

            {Object.keys(gapDetail.gap_analysis.enrichment_gaps.incomplete_tables).length > 0 && (
              <>
                <h3 className="font-semibold mt-4">Incomplete Tables</h3>
                {Object.entries(gapDetail.gap_analysis.enrichment_gaps.incomplete_tables).map(
                  ([table, fields]) => (
                    <div key={table} className="mb-2">
                      <p className="font-medium">{table}</p>
                      <ul className="list-disc list-inside ml-4">
                        {fields.map((field) => (
                          <li key={field} className="text-sm">{field}</li>
                        ))}
                      </ul>
                    </div>
                  )
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="technical" className="space-y-4">
            <h3 className="font-semibold">Missing Technical Details</h3>
            {Object.entries(gapDetail.gap_analysis.jsonb_gaps.missing_keys).map(
              ([field, keys]) => (
                <div key={field} className="mb-2">
                  <p className="font-medium">{field}</p>
                  <ul className="list-disc list-inside ml-4">
                    {keys.map((key) => (
                      <li key={key} className="text-sm">{key}</li>
                    ))}
                  </ul>
                </div>
              )
            )}
          </TabsContent>

          <TabsContent value="standards" className="space-y-4">
            {gapDetail.gap_analysis.standards_gaps?.violations.map((violation, idx) => (
              <Alert key={idx} variant={violation.is_mandatory ? "destructive" : "warning"}>
                <AlertTitle>{violation.standard_name}</AlertTitle>
                <AlertDescription>
                  <p><strong>Type:</strong> {violation.requirement_type}</p>
                  <p><strong>Issue:</strong> {violation.violation_details}</p>
                  {violation.override_available && (
                    <p className="mt-2 text-sm">
                      <Badge variant="outline">Override Available</Badge>
                    </p>
                  )}
                </AlertDescription>
              </Alert>
            ))}
          </TabsContent>
        </Tabs>

        {/* Priority action items */}
        <div className="mt-6">
          <h3 className="font-semibold mb-3">Priority Action Items</h3>
          <div className="space-y-2">
            {gapDetail.gap_analysis.priority_missing_data.map((item, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 border rounded"
              >
                <div>
                  <p className="font-medium">{item.attribute_name}</p>
                  <p className="text-sm text-gray-600">{item.reason}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={item.priority === 1 ? "destructive" : "secondary"}>
                    P{item.priority}
                  </Badge>
                  <Badge variant="outline">{item.estimated_effort}</Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
```

**Acceptance Criteria**:
- [ ] Readiness dashboard shows completeness scores
- [ ] Gap breakdown visible per asset
- [ ] Gap details modal displays all layers
- [ ] "Collect Missing Data" button shows count of incomplete assets
- [ ] Blocking gaps clearly highlighted

---

#### **Day 13: Frontend - Collection Flow Integration**

**Tasks**:
1. Update collection flow creation to use new gap format
2. Enhance adaptive questionnaire rendering
3. Add gap category filters
4. Test end-to-end flow

**Update Collection Flow API** (`src/lib/api/collectionFlow.ts`):
```typescript
// Update ensureFlow to use new missing_attributes format
async ensureFlow(
  missing_attributes: Record<string, MissingAttributesByCategory>,
  assessment_flow_id?: string
): Promise<CollectionFlowResponse> {
  // Flatten missing attributes for backend
  const flattened_missing: Record<string, string[]> = {};

  for (const [asset_id, categories] of Object.entries(missing_attributes)) {
    flattened_missing[asset_id] = [
      ...categories.infrastructure,
      ...categories.enrichments,
      ...categories.technical_details,
      ...categories.standards_compliance,
    ];
  }

  const response = await apiCall(`/api/v1/collection/ensure-flow`, {
    method: 'POST',
    body: JSON.stringify({
      missing_attributes: flattened_missing,
      assessment_flow_id,
    }),
  });

  return response;
}
```

**Update Adaptive Forms** (`src/components/collection/AdaptiveFormsPage.tsx`):
```typescript
// Add category-based section rendering
const renderQuestionsByCategory = () => {
  const categories = ['infrastructure', 'enrichments', 'technical_details', 'standards_compliance'];

  return categories.map((category) => {
    const categoryQuestions = questionnaire.sections.filter(
      (section) => section.category === category
    );

    if (categoryQuestions.length === 0) return null;

    return (
      <div key={category} className="mb-8">
        <h2 className="text-2xl font-bold mb-4">
          {category.replace('_', ' ').toUpperCase()}
        </h2>
        <p className="text-gray-600 mb-4">
          {getCategoryDescription(category)}
        </p>

        {categoryQuestions.map((section) => (
          <QuestionSection
            key={section.id}
            section={section}
            onAnswer={handleAnswer}
          />
        ))}
      </div>
    );
  });
};

const getCategoryDescription = (category: string): string => {
  const descriptions = {
    infrastructure: "Basic infrastructure and hardware information",
    enrichments: "Business continuity, compliance, and operational details",
    technical_details: "Application architecture and technical specifications",
    standards_compliance: "Architecture standards and compliance requirements",
  };
  return descriptions[category] || "";
};
```

**Acceptance Criteria**:
- [ ] Collection flow created with categorized missing attributes
- [ ] Questionnaire sections grouped by gap category
- [ ] Frontend handles new API response format
- [ ] End-to-end test: Assessment → Collection → Questionnaire

---

#### **Day 14: Questionnaire Generator Integration**

**Tasks**:
1. Integrate IntelligentQuestionnaireGenerator with collection flow
2. Test adaptive question generation
3. Verify questions skip existing data
4. Performance testing

**Update Collection Flow Creation** (`backend/app/api/v1/endpoints/collection_crud_create_commands.py`):
```python
# After creating collection flow, generate intelligent questionnaire
from app.services.gap_detection.questionnaire_generator import IntelligentQuestionnaireGenerator

async def create_collection_flow(...):
    # ... existing code ...

    # Generate adaptive questionnaire based on gap analysis
    questionnaire_generator = IntelligentQuestionnaireGenerator()

    for asset_id in collection_config["selected_application_ids"]:
        asset = await db.get(Asset, UUID(asset_id))
        application = await get_canonical_application_for_asset(db, asset)

        # Get gap report
        gap_analyzer = GapAnalyzer(db)
        gap_report = await gap_analyzer.analyze_asset(asset, application, context.engagement_id)

        # Generate adaptive questionnaire
        questionnaire = await questionnaire_generator.generate_questionnaire(
            gap_report=gap_report,
            asset=asset,
            application=application,
        )

        # Create questionnaire record
        from app.models import AdaptiveQuestionnaire

        db_questionnaire = AdaptiveQuestionnaire(
            asset_id=asset.id,
            collection_flow_id=collection_flow.id,
            engagement_id=context.engagement_id,
            sections=questionnaire.sections,
            total_questions=questionnaire.total_questions,
            estimated_completion_time=questionnaire.estimated_completion_time,
            priority_order=questionnaire.priority_order,
            status="pending",
        )
        db.add(db_questionnaire)

    await db.flush()
    # ... rest of existing code ...
```

**Acceptance Criteria**:
- [ ] Questionnaire generator integrated with collection flow creation
- [ ] Questions generated based on actual gaps
- [ ] Existing data skipped (no redundant questions)
- [ ] Performance: <500ms for questionnaire generation per asset
- [ ] Integration test verifies correct question targeting

---

#### **Day 15: Testing & Documentation**

**Tasks**:
1. Comprehensive end-to-end testing
2. Performance benchmarking
3. Update API documentation
4. Create user guide

**End-to-End Test Scenarios**:
```python
# backend/tests/e2e/test_gap_detection_flow.py

@pytest.mark.asyncio
async def test_complete_assessment_collection_flow(client: AsyncClient):
    """
    E2E test: Discovery → Assessment → Gap Detection → Collection → Questionnaire
    """

    # Step 1: Create assessment flow with incomplete asset
    asset = await create_test_asset(
        asset_name="Incomplete App",
        cpu_cores=4,
        # Missing: memory_gb, storage_gb, resilience table
    )

    assessment_flow = await create_assessment_flow(assets=[asset])

    # Step 2: Get assessment readiness
    response = await client.get(f"/api/v1/master-flows/{assessment_flow.id}/assessment-readiness")
    assert response.status_code == 200

    data = response.json()
    asset_detail = data["asset_details"][0]

    # Verify gap detection found missing data
    assert asset_detail["completeness_score"] < 0.85
    assert not asset_detail["assessment_ready"]
    assert asset_detail["gap_summary"]["column_gaps"] > 0
    assert asset_detail["gap_summary"]["enrichment_gaps"] > 0

    # Step 3: Create collection flow from assessment
    missing_attrs = {
        str(asset.id): asset_detail["missing_attributes"]
    }

    collection_response = await client.post(
        "/api/v1/collection/ensure-flow",
        json={
            "missing_attributes": missing_attrs,
            "assessment_flow_id": str(assessment_flow.id),
        }
    )
    assert collection_response.status_code == 200

    collection_flow = collection_response.json()

    # Step 4: Verify questionnaire generated
    questionnaire_response = await client.get(
        f"/api/v1/collection/{collection_flow['flow_id']}/questionnaires"
    )
    assert questionnaire_response.status_code == 200

    questionnaires = questionnaire_response.json()
    assert len(questionnaires) == 1

    questionnaire = questionnaires[0]
    # Verify questions target actual gaps
    assert questionnaire["total_questions"] > 0
    assert "infrastructure" in [s["category"] for s in questionnaire["sections"]]
    assert "enrichments" in [s["category"] for s in questionnaire["sections"]]

    # Step 5: Verify questions skip existing data
    section_questions = [q for s in questionnaire["sections"] for q in s["questions"]]
    question_fields = [q["field_name"] for q in section_questions]

    # Should NOT ask about cpu_cores (already has value)
    assert "cpu_cores" not in question_fields
    # SHOULD ask about memory_gb (missing)
    assert "memory_gb" in question_fields
```

**Performance Benchmarks**:
```python
# backend/tests/performance/test_gap_detection_performance.py

@pytest.mark.benchmark
async def test_gap_analyzer_performance():
    """Ensure gap analysis completes in <200ms per asset."""

    assets = await create_test_assets(count=100)

    start = time.time()

    for asset in assets:
        analyzer = GapAnalyzer(db)
        report = await analyzer.analyze_asset(asset)

    elapsed = time.time() - start
    avg_time = elapsed / 100

    assert avg_time < 0.2, f"Gap analysis took {avg_time}s per asset (target: <200ms)"

@pytest.mark.benchmark
async def test_questionnaire_generation_performance():
    """Ensure questionnaire generation completes in <500ms per asset."""

    gap_reports = await create_test_gap_reports(count=50)

    start = time.time()

    generator = IntelligentQuestionnaireGenerator()
    for report in gap_reports:
        questionnaire = await generator.generate_questionnaire(report, asset, application)

    elapsed = time.time() - start
    avg_time = elapsed / 50

    assert avg_time < 0.5, f"Questionnaire generation took {avg_time}s (target: <500ms)"
```

**API Documentation** (`docs/api/gap-detection.md`):
```markdown
# Gap Detection API

## GET /api/v1/master-flows/{flow_id}/assessment-readiness

Returns assessment readiness status with comprehensive gap analysis.

**Response**:
```json
{
  "flow_id": "uuid",
  "total_applications": 10,
  "ready_count": 7,
  "not_ready_count": 3,
  "average_completeness": 0.82,
  "asset_details": [
    {
      "asset_id": "uuid",
      "asset_name": "App Name",
      "completeness_score": 0.75,
      "assessment_ready": false,
      "missing_count": 12,
      "gap_summary": {
        "column_gaps": 3,
        "enrichment_gaps": 2,
        "jsonb_gaps": 5,
        "standards_violations": 2
      },
      "missing_attributes": {
        "infrastructure": ["memory_gb", "storage_gb"],
        "enrichments": ["resilience", "compliance_flags"],
        "technical_details": ["api_endpoints", "integration_points"],
        "standards_compliance": ["Encryption at rest not configured"]
      },
      "blocking_gaps": ["Mandatory security standard violated"]
    }
  ]
}
```

## GET /api/v1/master-flows/{flow_id}/asset-gap-detail/{asset_id}

Returns detailed gap analysis for a specific asset.

**Response**:
```json
{
  "asset_id": "uuid",
  "asset_name": "App Name",
  "gap_analysis": {
    "overall_completeness": 0.75,
    "assessment_ready": false,
    "blocking_gaps": ["Mandatory security standard violated"],
    "column_gaps": {
      "missing": ["memory_gb", "storage_gb"],
      "empty": [],
      "null": ["memory_gb", "storage_gb"]
    },
    "enrichment_gaps": {
      "missing_tables": ["resilience", "compliance_flags"],
      "incomplete_tables": {
        "licenses": ["renewal_date"]
      },
      "completeness": 0.57
    },
    "priority_missing_data": [
      {
        "attribute_name": "memory_gb",
        "data_layer": "column",
        "priority": 1,
        "reason": "Required for assessment",
        "estimated_effort": "quick"
      }
    ]
  }
}
```
```

**User Guide** (`docs/user-guide/gap-detection.md`):
```markdown
# Understanding Gap Detection

## What is Gap Detection?

Gap detection identifies missing or incomplete data across multiple layers:

- **Infrastructure Data** (CPU, memory, storage)
- **Enrichment Data** (resilience, compliance, vulnerabilities)
- **Technical Details** (architecture, dependencies, APIs)
- **Standards Compliance** (security, performance requirements)

## Completeness Scores

Assets receive a completeness score (0-100%):

- **90-100%**: Excellent - Ready for assessment
- **70-89%**: Good - Minor gaps, likely ready
- **50-69%**: Fair - Significant gaps, not ready
- **Below 50%**: Poor - Major gaps, data collection needed

## Gap Categories

### Infrastructure Gaps (Red)
Basic hardware and platform information missing. High priority.

### Enrichment Gaps (Yellow)
Business continuity, compliance, or operational details missing. Medium priority.

### Technical Gaps (Orange)
Application architecture and integration details missing. Varies by 6R strategy.

### Standards Violations (Red)
Mandatory architecture standards not met. Blocking issue.

## What to Do About Gaps

1. **View Gap Details**: Click "View Gap Details" on any asset card
2. **Review Priority Items**: Focus on P1 (critical) gaps first
3. **Collect Missing Data**: Click "Collect Missing Data" to start questionnaire
4. **Answer Questions**: Complete adaptive questionnaire (only asks about actual gaps)
5. **Check Readiness**: Return to assessment to verify completeness improved
```

**Acceptance Criteria**:
- [ ] E2E tests pass with >95% success rate
- [ ] Performance benchmarks meet targets (<200ms gap analysis, <500ms questionnaire)
- [ ] API documentation complete with examples
- [ ] User guide published with screenshots

---

### Week 4: Optimization & Deployment (Days 16-20)

#### **Day 16: Caching & Performance Optimization**

**Tasks**:
1. Implement caching for requirements matrix
2. Add database query optimization
3. Batch gap analysis for multiple assets
4. Profile and optimize hotspots

**Requirements Caching** (`backend/app/services/gap_detection/requirements/requirements_engine.py`):
```python
from functools import lru_cache

class RequirementsEngine:
    @lru_cache(maxsize=1000)
    def _get_asset_type_requirements(self, asset_type: str) -> Dict:
        """Cached lookup for asset type requirements."""
        return ASSET_TYPE_REQUIREMENTS.get(asset_type, {})

    @lru_cache(maxsize=1000)
    def _get_six_r_requirements(self, six_r_strategy: str) -> Dict:
        """Cached lookup for 6R strategy requirements."""
        return SIX_R_STRATEGY_REQUIREMENTS.get(six_r_strategy, {})
```

**Batch Gap Analysis** (`backend/app/services/gap_detection/gap_analyzer.py`):
```python
async def analyze_assets_batch(
    self,
    assets: List[Asset],
    applications: Dict[str, CanonicalApplication],
    engagement_id: str,
) -> List[ComprehensiveGapReport]:
    """
    Batch analyze multiple assets in parallel.

    Args:
        assets: List of assets to analyze
        applications: Dict mapping asset_id → CanonicalApplication
        engagement_id: Engagement ID for standards lookup

    Returns:
        List of gap reports in same order as input assets
    """

    # Fetch all engagement standards once
    standards = await self._fetch_engagement_standards(engagement_id)

    # Analyze all assets in parallel
    tasks = [
        self._analyze_asset_with_standards(
            asset=asset,
            application=applications.get(str(asset.id)),
            standards=standards,
        )
        for asset in assets
    ]

    return await asyncio.gather(*tasks)
```

**Database Query Optimization**:
```python
# Use selectinload to avoid N+1 queries
from sqlalchemy.orm import selectinload

async def fetch_assets_with_enrichments(
    db: AsyncSession,
    asset_ids: List[str],
) -> List[Asset]:
    """Fetch assets with all enrichment relationships eager-loaded."""

    result = await db.execute(
        select(Asset)
        .options(
            selectinload(Asset.resilience),
            selectinload(Asset.compliance_flags),
            selectinload(Asset.vulnerabilities),
            selectinload(Asset.licenses),
            selectinload(Asset.dependencies),
            selectinload(Asset.product_links),
            selectinload(Asset.field_conflicts),
        )
        .where(Asset.id.in_([UUID(aid) for aid in asset_ids]))
    )

    return result.scalars().all()
```

**Acceptance Criteria**:
- [ ] Requirements matrix cached (>95% cache hit rate)
- [ ] Batch analysis 5x faster than sequential
- [ ] Database queries optimized (no N+1 queries)
- [ ] Performance benchmarks improved by 50%

---

#### **Day 17: Backward Compatibility & Migration**

**Tasks**:
1. Add feature flag for gradual rollout
2. Create data migration script
3. Add fallback for old API clients
4. Test mixed-version scenarios

**Feature Flag** (`backend/app/core/feature_flags.py`):
```python
class FeatureFlags:
    INTELLIGENT_GAP_DETECTION = "intelligent_gap_detection_v2"

    @staticmethod
    def is_enabled(flag: str, engagement_id: str) -> bool:
        """Check if feature flag is enabled for engagement."""
        # Start with 10% rollout, then gradually increase
        from app.core.rollout_manager import RolloutManager
        return RolloutManager.is_enabled(flag, engagement_id)
```

**API Compatibility Layer** (`backend/app/api/v1/master_flows/assessment/helpers.py`):
```python
async def get_missing_attributes_compatible(
    asset: Asset,
    application: Optional[CanonicalApplication],
    engagement_id: str,
    db: AsyncSession,
    use_v2: bool = True,
) -> Union[List[str], ComprehensiveGapReport]:
    """
    Backward-compatible wrapper for gap detection.

    Args:
        use_v2: If True, use new comprehensive gap analysis
                If False, fall back to old 22-attribute check

    Returns:
        v1: List of missing attribute names
        v2: ComprehensiveGapReport
    """

    if use_v2:
        # New comprehensive analysis
        return await get_comprehensive_gap_analysis(
            asset=asset,
            application=application,
            engagement_id=engagement_id,
            db=db,
        )
    else:
        # Old 22-attribute check (for backward compatibility)
        return get_missing_critical_attributes_v1(asset)

def get_missing_critical_attributes_v1(asset: Asset) -> List[str]:
    """Legacy implementation for backward compatibility."""
    # Keep old logic for gradual migration
    critical_attrs = [...22 hardcoded...]
    missing = []
    for attr in critical_attrs:
        value = getattr(asset, attr, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(attr)
    return missing
```

**Data Migration Script** (`backend/alembic/versions/093_migrate_gap_detection_data.py`):
```python
"""Migrate existing gap data to new format

Revision ID: 093
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    # No schema changes needed (new service is code-only)
    # But we can pre-populate cache or audit existing data quality

    # Optional: Create gap_analysis_cache table for performance
    op.create_table(
        'gap_analysis_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gap_report', postgresql.JSONB, nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        schema='migration',
    )

    op.create_index(
        'idx_gap_cache_asset_engagement',
        'gap_analysis_cache',
        ['asset_id', 'engagement_id'],
        schema='migration',
    )

def downgrade() -> None:
    op.drop_table('gap_analysis_cache', schema='migration')
```

**Acceptance Criteria**:
- [ ] Feature flag implemented with gradual rollout
- [ ] Old API clients continue to work during migration
- [ ] Data migration script tested on staging
- [ ] Rollback plan documented and tested

---

#### **Day 18: Standards Template Population**

**Tasks**:
1. Create industry-standard templates (PCI-DSS, HIPAA, SOC2)
2. Implement template loading on engagement creation
3. Add standards override workflow
4. Test standards validation

**Standards Templates** (`backend/app/services/gap_detection/standards/templates.py`):
```python
PCI_DSS_STANDARDS = [
    {
        "requirement_type": "security",
        "standard_name": "Network Segmentation",
        "minimum_requirements": {
            "network_isolation": True,
            "firewall_required": True,
            "dmz_configuration": True,
        },
        "preferred_patterns": {
            "zero_trust_architecture": True,
            "micro_segmentation": True,
        },
        "constraints": {
            "cardholder_data_environment": "must_be_isolated",
        },
        "is_mandatory": True,
    },
    {
        "requirement_type": "security",
        "standard_name": "Encryption",
        "minimum_requirements": {
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "key_management": "hsm_or_kms",
        },
        "is_mandatory": True,
    },
    {
        "requirement_type": "compliance",
        "standard_name": "Vulnerability Management",
        "minimum_requirements": {
            "regular_scanning": "monthly",
            "patch_management": "critical_within_30_days",
            "penetration_testing": "annual",
        },
        "is_mandatory": True,
    },
]

HIPAA_STANDARDS = [
    {
        "requirement_type": "security",
        "standard_name": "PHI Protection",
        "minimum_requirements": {
            "encryption_at_rest": True,
            "access_controls": True,
            "audit_logging": True,
            "phi_data_classification": True,
        },
        "is_mandatory": True,
    },
    {
        "requirement_type": "compliance",
        "standard_name": "Business Associate Agreements",
        "minimum_requirements": {
            "baa_required": True,
            "subcontractor_agreements": True,
        },
        "is_mandatory": True,
    },
]

SOC2_STANDARDS = [
    {
        "requirement_type": "availability",
        "standard_name": "High Availability",
        "minimum_requirements": {
            "redundancy": "multi_az",
            "failover_capability": True,
            "backup_strategy": "automated_daily",
        },
        "preferred_patterns": {
            "disaster_recovery": "cross_region",
            "rpo_minutes": 60,
            "rto_minutes": 240,
        },
        "is_mandatory": False,
    },
]
```

**Template Loader** (`backend/app/services/gap_detection/standards/template_loader.py`):
```python
async def populate_engagement_standards(
    db: AsyncSession,
    engagement_id: str,
    compliance_scopes: List[str],
) -> None:
    """
    Populate EngagementArchitectureStandard table with industry templates.

    Args:
        engagement_id: Engagement to populate standards for
        compliance_scopes: List of compliance requirements (e.g., ["PCI-DSS", "HIPAA"])
    """

    from app.models.assessment_flow import EngagementArchitectureStandard

    standards_to_create = []

    for scope in compliance_scopes:
        if scope == "PCI-DSS":
            templates = PCI_DSS_STANDARDS
        elif scope == "HIPAA":
            templates = HIPAA_STANDARDS
        elif scope == "SOC2":
            templates = SOC2_STANDARDS
        else:
            continue

        for template in templates:
            standard = EngagementArchitectureStandard(
                engagement_id=engagement_id,
                requirement_type=template["requirement_type"],
                standard_name=template["standard_name"],
                minimum_requirements=template["minimum_requirements"],
                preferred_patterns=template.get("preferred_patterns", {}),
                constraints=template.get("constraints", {}),
                is_mandatory=template["is_mandatory"],
                source="industry_template",
                template_version="1.0",
            )
            standards_to_create.append(standard)

    db.add_all(standards_to_create)
    await db.flush()
```

**Acceptance Criteria**:
- [ ] PCI-DSS, HIPAA, SOC2 templates defined
- [ ] Template loader populates standards on engagement creation
- [ ] Standards validation integrated with gap detection
- [ ] Override workflow allows approved exceptions

---

#### **Day 19: Monitoring & Observability**

**Tasks**:
1. Add logging for gap detection operations
2. Create metrics for completeness scores
3. Add alerts for blocking gaps
4. Build analytics dashboard

**Logging** (`backend/app/services/gap_detection/gap_analyzer.py`):
```python
import structlog

logger = structlog.get_logger(__name__)

async def analyze_asset(self, asset: Asset, ...) -> ComprehensiveGapReport:
    logger.info(
        "gap_analysis_started",
        asset_id=str(asset.id),
        asset_type=asset.asset_type,
        six_r_strategy=asset.six_r_strategy,
    )

    try:
        report = await self._perform_analysis(...)

        logger.info(
            "gap_analysis_completed",
            asset_id=str(asset.id),
            completeness_score=report.overall_completeness_score,
            assessment_ready=report.assessment_ready,
            column_gaps=len(report.column_gaps.missing_attributes),
            enrichment_gaps=len(report.enrichment_gaps.missing_tables),
            blocking_gaps=len(report.blocking_gaps),
        )

        return report

    except Exception as e:
        logger.error(
            "gap_analysis_failed",
            asset_id=str(asset.id),
            error=str(e),
            exc_info=True,
        )
        raise
```

**Metrics** (`backend/app/services/gap_detection/metrics.py`):
```python
from prometheus_client import Histogram, Counter, Gauge

gap_analysis_duration = Histogram(
    'gap_analysis_duration_seconds',
    'Time spent analyzing asset gaps',
    ['asset_type', 'six_r_strategy'],
)

completeness_score_gauge = Gauge(
    'asset_completeness_score',
    'Asset data completeness score',
    ['asset_type', 'criticality'],
)

gap_detection_errors = Counter(
    'gap_detection_errors_total',
    'Total gap detection errors',
    ['error_type'],
)

blocking_gaps_gauge = Gauge(
    'blocking_gaps_total',
    'Number of assets with blocking gaps',
    ['engagement_id'],
)
```

**Analytics Dashboard** (Grafana):
```json
{
  "title": "Gap Detection Analytics",
  "panels": [
    {
      "title": "Average Completeness Score",
      "targets": [
        {
          "expr": "avg(asset_completeness_score) by (asset_type)"
        }
      ]
    },
    {
      "title": "Assets Not Ready for Assessment",
      "targets": [
        {
          "expr": "count(asset_completeness_score < 0.85)"
        }
      ]
    },
    {
      "title": "Gap Analysis Performance",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, gap_analysis_duration_seconds)"
        }
      ]
    },
    {
      "title": "Blocking Gaps by Engagement",
      "targets": [
        {
          "expr": "blocking_gaps_total"
        }
      ]
    }
  ]
}
```

**Acceptance Criteria**:
- [ ] Structured logging captures all gap analysis operations
- [ ] Prometheus metrics exported
- [ ] Grafana dashboard deployed
- [ ] Alerts configured for blocking gaps

---

#### **Day 20: Deployment & Rollout**

**Tasks**:
1. Deploy to staging environment
2. Run smoke tests
3. Gradual rollout to production (10% → 50% → 100%)
4. Monitor metrics and error rates

**Deployment Checklist**:
```markdown
## Staging Deployment

- [ ] Deploy backend services
- [ ] Deploy frontend changes
- [ ] Run database migrations
- [ ] Populate standards templates for test engagements
- [ ] Run E2E smoke tests
- [ ] Verify performance benchmarks
- [ ] Check Grafana dashboard

## Production Rollout

### Phase 1: 10% Traffic (Day 20, 9am)
- [ ] Enable feature flag for 10% of engagements
- [ ] Monitor error rates (target: <0.1%)
- [ ] Monitor performance (target: p95 < 200ms)
- [ ] Check user feedback
- [ ] Wait 4 hours

### Phase 2: 50% Traffic (Day 20, 1pm)
- [ ] Increase to 50% of engagements
- [ ] Monitor metrics
- [ ] Verify no regressions
- [ ] Wait 4 hours

### Phase 3: 100% Traffic (Day 20, 5pm)
- [ ] Enable for all engagements
- [ ] Monitor overnight
- [ ] Prepare rollback plan

## Rollback Plan

If error rate > 1% or performance degradation > 50%:
1. Disable feature flag (revert to v1)
2. Investigate logs
3. Fix issue
4. Re-deploy with fix
```

**Smoke Tests** (`backend/tests/smoke/test_gap_detection_smoke.py`):
```python
@pytest.mark.smoke
async def test_gap_detection_basic_flow():
    """Smoke test: Basic gap detection works."""
    # Create incomplete asset
    # Run gap analysis
    # Verify report returned
    # Verify no exceptions
    pass

@pytest.mark.smoke
async def test_collection_flow_with_gaps():
    """Smoke test: Collection flow creation works."""
    # Create assessment with gaps
    # Create collection flow
    # Verify questionnaire generated
    pass

@pytest.mark.smoke
async def test_standards_validation():
    """Smoke test: Standards validation works."""
    # Create engagement with PCI-DSS
    # Populate standards templates
    # Analyze asset against standards
    # Verify violations detected
    pass
```

**Monitoring During Rollout**:
```bash
# Watch error rates
kubectl logs -f deployment/backend --tail=100 | grep -i error

# Watch gap analysis metrics
curl http://prometheus:9090/api/v1/query?query=rate(gap_detection_errors_total[5m])

# Check Grafana dashboard
open https://grafana.example.com/d/gap-detection
```

**Acceptance Criteria**:
- [ ] Staging deployment successful
- [ ] Smoke tests pass
- [ ] 10% rollout completes without errors
- [ ] 50% rollout completes without errors
- [ ] 100% rollout completes without errors
- [ ] Metrics within target ranges
- [ ] User feedback positive

---

## Success Metrics

### Technical Metrics
- **Gap Detection Accuracy**: >95% (manual validation of 100 assets)
- **Performance**: <200ms per asset gap analysis
- **API Response Time**: <500ms for assessment readiness endpoint
- **Error Rate**: <0.1% during rollout
- **Test Coverage**: >90% for new code

### Business Metrics
- **False Positive Reduction**: Eliminate "0 missing attributes" when data gaps exist
- **Questionnaire Relevance**: 70% fewer irrelevant questions (user survey)
- **Assessment Quality**: 30% increase in 6R recommendation confidence scores
- **User Satisfaction**: >4.0/5.0 rating for gap detection accuracy
- **Collection Completion Rate**: 20% increase (fewer abandoned questionnaires)

### Operational Metrics
- **Rollout Success**: 100% of engagements on v2 within 1 week
- **Zero Rollbacks**: No production rollbacks required
- **Support Tickets**: <5 gap-detection-related tickets per week
- **Documentation Quality**: 100% of new features documented

---

## Risks & Mitigation

### Risk 1: Performance Degradation
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Implement caching at multiple levels
- Use batch processing for multiple assets
- Add database query optimization
- Set up performance alerts

### Risk 2: Backward Compatibility Issues
**Probability**: Medium
**Impact**: Medium
**Mitigation**:
- Maintain v1 compatibility layer
- Gradual rollout with feature flags
- Comprehensive API versioning
- Fallback mechanism to old logic

### Risk 3: Data Quality Issues
**Probability**: Low
**Impact**: High
**Mitigation**:
- Validate requirements matrix against real data
- Test with production-like datasets
- Add data quality checks in inspectors
- Monitor completeness score distributions

### Risk 4: User Adoption Resistance
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Clear user documentation
- Training videos for new features
- Gradual UI changes (no big bang)
- Collect and act on user feedback

---

## Rollback Plan

### Triggers for Rollback
- Error rate >1% for >15 minutes
- Performance degradation >50% from baseline
- Critical bug affecting data integrity
- User feedback indicates major UX regression

### Rollback Procedure
1. **Immediate**: Disable feature flag (revert to v1 logic)
2. **Verify**: Confirm error rates drop
3. **Investigate**: Analyze logs and metrics
4. **Fix**: Address root cause
5. **Re-deploy**: Gradual rollout with fix

### Post-Rollback Actions
- Root cause analysis document
- Fix implementation and testing
- Enhanced monitoring before re-deployment
- User communication about temporary revert

---

## Future Enhancements (Post-MVP)

### Phase 2 (Week 6+)
- **AI-Powered Gap Prediction**: Use ML to predict likely missing data based on asset type patterns
- **Auto-Population from CMDB**: Automatically fill gaps from external CMDB systems
- **Smart Questionnaire Ordering**: Use NLP to optimize question order for faster completion
- **Gap Trend Analytics**: Track gap improvement over time per engagement

### Phase 3 (Month 2+)
- **Custom Requirements Builder**: UI for defining custom architecture standards
- **Gap Resolution Workflow**: Track gap resolution status with approval workflows
- **Integration with Discovery Agents**: Auto-fill enrichment data from discovery scans
- **Multi-Language Support**: Localize questionnaires for global deployments

---

## Dependencies

### External Dependencies
- PostgreSQL 16 with pgvector
- SQLAlchemy 2.0+
- Pydantic 2.0+
- FastAPI 0.104+
- React 18+
- TanStack Query 5+

### Internal Dependencies
- Asset model (columns + enrichment relationships)
- CanonicalApplication model
- EngagementArchitectureStandard model
- Collection flow system
- Assessment flow system
- Master Flow Orchestrator

---

## Approval & Sign-Off

**Technical Reviewer**: _________________
**Product Owner**: _________________
**Architect**: _________________
**Date**: _________________

---

## Appendix A: Migration Guide for Developers

### For Backend Developers

**Old Code**:
```python
missing_attrs = get_missing_critical_attributes(asset)
```

**New Code**:
```python
gap_analyzer = GapAnalyzer(db)
gap_report = await gap_analyzer.analyze_asset(asset, application, engagement_id)
missing_attrs = [item.attribute_name for item in gap_report.priority_missing_data]
```

### For Frontend Developers

**Old Interface**:
```typescript
interface AssetDetail {
  missing_count: number;
  missing_attributes: string[];
}
```

**New Interface**:
```typescript
interface AssetDetail {
  completeness_score: number;
  assessment_ready: boolean;
  gap_summary: GapSummary;
  missing_attributes: MissingAttributesByCategory;
  blocking_gaps: string[];
}
```

### For QA Testers

**Test Scenarios**:
1. Create asset with missing columns → Verify column gaps detected
2. Create asset without enrichment tables → Verify enrichment gaps detected
3. Create asset with empty JSONB → Verify JSONB gaps detected
4. Create asset violating standards → Verify standards violations detected
5. Complete questionnaire → Verify gaps resolved, completeness score improves

---

## Appendix B: Database Schema Changes

No schema changes required to existing tables. New optional table for caching:

```sql
CREATE TABLE migration.gap_analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES migration.assets(id),
    engagement_id UUID NOT NULL,
    gap_report JSONB NOT NULL,
    cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_asset FOREIGN KEY (asset_id) REFERENCES migration.assets(id) ON DELETE CASCADE
);

CREATE INDEX idx_gap_cache_asset_engagement ON migration.gap_analysis_cache(asset_id, engagement_id);
CREATE INDEX idx_gap_cache_expires ON migration.gap_analysis_cache(expires_at);
```

---

## Appendix C: API Response Examples

See Day 11 implementation section for detailed API response examples.
