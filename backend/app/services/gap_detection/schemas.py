"""
Pydantic schemas for gap detection reports.

All schemas use Field constraints to ensure JSON safety (GPT-5 Rec #8).
Completeness scores are clamped to [0.0, 1.0] to prevent NaN/Infinity issues.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GapPriority(str, Enum):
    """Priority levels for gaps - determines order of resolution."""

    CRITICAL = "critical"  # Blocks assessment
    HIGH = "high"  # Important for assessment
    MEDIUM = "medium"  # Nice to have
    LOW = "low"  # Optional


class FieldGap(BaseModel):
    """Represents a single missing or incomplete field."""

    field_name: str = Field(description="Name of the missing field")
    layer: str = Field(
        description="Data layer (column, enrichment, jsonb, application, standards)"
    )
    priority: GapPriority = Field(description="Priority level")
    reason: Optional[str] = Field(
        None, description="Why this field is missing/incomplete"
    )

    class Config:
        use_enum_values = True


class DataRequirements(BaseModel):
    """
    Context-aware requirements for gap detection.

    Defines what data is required based on:
    - Asset type (server, application, database, etc.)
    - 6R strategy (rehost, refactor, etc.)
    - Compliance scope (PCI-DSS, HIPAA, etc.)
    - Criticality tier (tier_1_critical, tier_2_important, tier_3_standard)

    Used by all inspectors to determine what to check.
    """

    required_columns: List[str] = Field(
        default_factory=list,
        description="SQLAlchemy column names required for this asset",
    )
    required_enrichments: List[str] = Field(
        default_factory=list,
        description="Enrichment table names required (resilience, compliance_flags, etc.)",
    )
    required_jsonb_keys: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="JSONB field keys required (e.g., {'custom_attributes': ['environment']})",
    )
    required_standards: List[str] = Field(
        default_factory=list,
        description="Architecture standard names required",
    )
    priority_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Weight for each data layer (columns, enrichments, jsonb, standards)",
    )
    completeness_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum completeness score to be considered assessment-ready",
    )


class ColumnGapReport(BaseModel):
    """
    Gap report for Asset SQLAlchemy columns.

    Categorizes missing data into:
    - missing_attributes: Required columns that don't exist on the asset
    - empty_attributes: Columns that exist but have empty strings/lists/dicts
    - null_attributes: Columns that exist but have None values
    """

    missing_attributes: List[str] = Field(
        default_factory=list,
        description="Required columns that are not present on asset",
    )
    empty_attributes: List[str] = Field(
        default_factory=list,
        description="Columns with empty strings, empty lists, or empty dicts",
    )
    null_attributes: List[str] = Field(
        default_factory=list,
        description="Columns with None/NULL values",
    )
    completeness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Completeness score [0.0-1.0] clamped for JSON safety",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "missing_attributes": [],
                "empty_attributes": ["technology_stack"],
                "null_attributes": ["cpu_cores", "memory_gb"],
                "completeness_score": 0.25,
            }
        }


class EnrichmentGapReport(BaseModel):
    """
    Gap report for Asset enrichment tables.

    7 Enrichment Tables:
    - resilience: AssetResilience (RTO, RPO, backup strategy)
    - compliance_flags: AssetComplianceFlags (compliance scopes, data classification)
    - vulnerabilities: AssetVulnerabilities (CVE, severity, remediation)
    - tech_debt: AssetTechDebt (technical debt score, modernization priority)
    - dependencies: AssetDependencies (upstream/downstream dependencies)
    - performance_metrics: AssetPerformanceMetrics (CPU, memory utilization)
    - cost_optimization: AssetCostOptimization (monthly cost, optimization potential)
    """

    missing_tables: List[str] = Field(
        default_factory=list,
        description="Enrichment tables that don't exist for this asset",
    )
    incomplete_tables: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Enrichment tables that exist but have incomplete fields (table_name -> [fields])",
    )
    completeness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Completeness score [0.0-1.0]: complete=1.0, partial=0.5, missing=0.0",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "missing_tables": ["resilience", "compliance_flags"],
                "incomplete_tables": {
                    "tech_debt": ["technical_debt_score", "modernization_priority"]
                },
                "completeness_score": 0.33,
            }
        }


class JSONBGapReport(BaseModel):
    """
    Gap report for JSONB fields.

    JSONB fields checked:
    - custom_attributes: Dict[str, Any] - Custom metadata
    - technical_details: Dict[str, Any] - Technical specifications
    - metadata: Dict[str, Any] - Additional metadata

    Supports nested key checking with dot notation (e.g., "deployment.strategy").
    """

    missing_keys: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="JSONB fields with missing keys (field_name -> [missing_keys])",
    )
    empty_values: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="JSONB fields with empty values (field_name -> [empty_keys])",
    )
    completeness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Completeness score [0.0-1.0] clamped for JSON safety",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "missing_keys": {
                    "custom_attributes": ["environment", "vm_type"],
                    "technical_details": ["api_endpoints"],
                },
                "empty_values": {"metadata": ["documentation_url"]},
                "completeness_score": 0.5,
            }
        }


class ApplicationGapReport(BaseModel):
    """
    Gap report for CanonicalApplication metadata.

    Checks:
    - Application metadata (name, description, type, business unit)
    - Technology stack completeness
    - Business context fields (owners, stakeholders, user base)
    """

    missing_metadata: List[str] = Field(
        default_factory=list,
        description="Missing application metadata fields",
    )
    incomplete_tech_stack: List[str] = Field(
        default_factory=list,
        description="Incomplete technology stack fields",
    )
    missing_business_context: List[str] = Field(
        default_factory=list,
        description="Missing business context fields",
    )
    completeness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Completeness score [0.0-1.0] clamped for JSON safety",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "missing_metadata": ["application_description", "business_unit"],
                "incomplete_tech_stack": ["programming_languages", "frameworks"],
                "missing_business_context": ["business_owner_name"],
                "completeness_score": 0.4,
            }
        }


class StandardViolation(BaseModel):
    """
    A single standards violation.

    Represents a failure to meet an EngagementArchitectureStandard.
    """

    standard_name: str = Field(description="Name of the violated standard")
    requirement_type: str = Field(
        description="Type of requirement (security, performance, compliance)"
    )
    violation_details: str = Field(
        description="Details of the violation with expected vs actual values"
    )
    is_mandatory: bool = Field(
        description="Whether this is a mandatory standard (blocks assessment if violated)"
    )
    override_available: bool = Field(
        default=False,
        description="Whether an override is available for this violation",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "standard_name": "Encryption at Rest",
                "requirement_type": "security",
                "violation_details": "Required: encryption_enabled=True, Found: False",
                "is_mandatory": True,
                "override_available": False,
            }
        }


class StandardsGapReport(BaseModel):
    """
    Gap report for architecture standards validation.

    Validates asset against EngagementArchitectureStandard records.
    Uses tenant-scoped database queries (client_account_id + engagement_id).
    """

    violated_standards: List[StandardViolation] = Field(
        default_factory=list,
        description="List of violated standards with details",
    )
    missing_mandatory_data: List[str] = Field(
        default_factory=list,
        description="Mandatory standards that are violated (blocks assessment)",
    )
    override_required: bool = Field(
        default=False,
        description="Whether an override is required to proceed with assessment",
    )
    completeness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Completeness score [0.0-1.0] based on standards compliance",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "violated_standards": [
                    {
                        "standard_name": "Network Segmentation",
                        "requirement_type": "security",
                        "violation_details": "Required: firewall_enabled=True, Found: False",
                        "is_mandatory": True,
                        "override_available": False,
                    }
                ],
                "missing_mandatory_data": ["Network Segmentation"],
                "override_required": True,
                "completeness_score": 0.75,
            }
        }


class ComprehensiveGapReport(BaseModel):
    """
    Comprehensive gap analysis across all data layers.

    Orchestrates all 5 inspectors (column, enrichment, JSONB, application, standards)
    to produce a complete picture of asset data completeness.

    Performance: <50ms per asset (target from implementation plan)
    Part of Issue #980: Intelligent Multi-Layer Gap Detection System
    """

    # Inspector reports
    column_gaps: ColumnGapReport = Field(
        description="Gap report for Asset SQLAlchemy columns"
    )
    enrichment_gaps: EnrichmentGapReport = Field(
        description="Gap report for enrichment tables"
    )
    jsonb_gaps: JSONBGapReport = Field(description="Gap report for JSONB fields")
    application_gaps: ApplicationGapReport = Field(
        description="Gap report for CanonicalApplication metadata"
    )
    standards_gaps: StandardsGapReport = Field(
        description="Gap report for architecture standards"
    )

    # Weighted completeness
    overall_completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="Weighted completeness score [0.0-1.0] across all layers",
    )
    weighted_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual weighted scores by layer (e.g., {'columns': 0.85, 'enrichments': 0.70})",
    )

    # Prioritized gaps
    critical_gaps: List[str] = Field(
        default_factory=list,
        description="Priority 1 missing fields (blocks assessment)",
    )
    high_priority_gaps: List[str] = Field(
        default_factory=list,
        description="Priority 2 missing fields (important for assessment)",
    )
    medium_priority_gaps: List[str] = Field(
        default_factory=list,
        description="Priority 3 missing fields (nice to have)",
    )
    all_gaps: List[FieldGap] = Field(
        default_factory=list,
        description="Complete list of all gaps across all layers",
    )

    # Assessment readiness
    is_ready_for_assessment: bool = Field(
        description="Whether asset has sufficient data for assessment"
    )
    readiness_blockers: List[str] = Field(
        default_factory=list,
        description="Reasons why asset is not ready for assessment",
    )
    completeness_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum completeness score required for assessment readiness",
    )

    # Metadata
    asset_id: str = Field(description="Asset UUID")
    asset_name: str = Field(description="Asset name for display")
    asset_type: str = Field(description="Asset type (server, application, etc.)")
    analyzed_at: str = Field(description="ISO 8601 timestamp of analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "column_gaps": {
                    "missing_attributes": ["cpu_cores", "memory_gb"],
                    "empty_attributes": ["technology_stack"],
                    "null_attributes": [],
                    "completeness_score": 0.75,
                },
                "enrichment_gaps": {
                    "missing_tables": ["resilience", "compliance_flags"],
                    "incomplete_tables": {},
                    "completeness_score": 0.60,
                },
                "jsonb_gaps": {
                    "missing_keys": {"custom_attributes": ["environment"]},
                    "empty_values": {},
                    "completeness_score": 0.85,
                },
                "application_gaps": {
                    "missing_metadata": ["business_unit"],
                    "incomplete_tech_stack": [],
                    "missing_business_context": [],
                    "completeness_score": 0.90,
                },
                "standards_gaps": {
                    "violated_standards": [],
                    "missing_mandatory_data": [],
                    "override_required": False,
                    "completeness_score": 1.0,
                },
                "overall_completeness": 0.76,
                "weighted_scores": {
                    "columns": 0.75,
                    "enrichments": 0.60,
                    "jsonb": 0.85,
                    "application": 0.90,
                    "standards": 1.0,
                },
                "critical_gaps": ["cpu_cores", "memory_gb"],
                "high_priority_gaps": ["resilience", "compliance_flags"],
                "medium_priority_gaps": ["environment"],
                "is_ready_for_assessment": True,
                "readiness_blockers": [],
                "completeness_threshold": 0.75,
                "asset_id": "123e4567-e89b-12d3-a456-426614174000",
                "asset_name": "app-server-01",
                "asset_type": "server",
                "analyzed_at": "2025-11-08T10:30:00Z",
            }
        }
