export interface SixRParameters {
  business_value: number;
  technical_complexity: number;
  migration_urgency: number;
  compliance_requirements: number;
  cost_sensitivity: number;
  risk_tolerance: number;
  innovation_priority: number;
  application_type: 'custom' | 'cots' | 'hybrid';
}

export interface SixRRecommendation {
  id: string;
  recommendation: string;
  confidence: number;
  parameters: Record<string, string | number | boolean | null>;
}

export interface QuestionResponse {
  questionId: string;
  response: unknown;
}

export interface AnalysisProgress {
  status: 'idle' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  message?: string;
}

export interface Analysis {
  id: string;
  applicationId: string;
  status: string;
  parameters: SixRParameters;
  recommendation?: SixRRecommendation;
  createdAt: string;
  updatedAt: string;
}

export interface AnalysisQueueItem {
  id: string;
  name: string;
  applicationIds: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';
  progress: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  error?: string;
  currentApp?: string;
}

export interface Application {
  id: string;
  name: string;
  description?: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Shared Assessment Architecture Enhancement Types (Phase 4)
// CRITICAL: ALL field names use snake_case (NEVER camelCase) per ADR compliance
// ============================================================================

/**
 * Readiness summary for a group of assets
 */
export interface ReadinessSummary {
  ready: number;
  not_ready: number;
  in_progress: number;
  avg_completeness_score: number; // 0-1 scale
}

/**
 * Detailed asset information for display in UI
 * Provides asset name and readiness status for clearer visibility
 */
export interface AssetDetail {
  asset_id: string;
  asset_name: string;
  asset_type?: string;
  environment?: string;
  assessment_readiness: 'ready' | 'not_ready' | 'in_progress';
  assessment_readiness_score?: number;
}

/**
 * Application asset group with canonical application linkage
 */
export interface ApplicationAssetGroup {
  canonical_application_id: string | null;
  canonical_application_name: string;
  asset_ids: string[];
  assets?: AssetDetail[]; // Detailed asset info with names and readiness status
  asset_count: number;
  asset_types: string[]; // e.g., ["server", "database", "network_device"]
  readiness_summary: ReadinessSummary;
}

/**
 * Enrichment status tracking for asset data completeness
 */
export interface EnrichmentStatus {
  compliance_flags: number; // Count of assets with compliance data
  licenses: number; // Count of assets with license data
  vulnerabilities: number; // Count of assets with vulnerability data
  resilience: number; // Count of assets with resilience data (HA, DR, backup)
  dependencies: number; // Count of assets with dependency mapping
  product_links: number; // Count of assets linked to vendor products
  field_conflicts: number; // Count of assets with field conflict resolution
}

/**
 * Detailed readiness information for a single asset
 */
export interface AssetReadinessDetail {
  asset_id: string;
  asset_name: string;
  asset_type: string; // e.g., "server", "database", "application"
  assessment_readiness: 'ready' | 'not_ready' | 'in_progress';
  assessment_readiness_score: number; // 0-1 scale (percentage of 22 critical attributes filled)
  assessment_blockers: string[]; // Array of missing critical attribute names
  missing_attributes: {
    infrastructure: string[]; // Missing attributes from Infrastructure category (6 total)
    application: string[]; // Missing attributes from Application category (8 total)
    business: string[]; // Missing attributes from Business category (4 total)
    technical_debt: string[]; // Missing attributes from Technical Debt category (4 total)
  };
}

/**
 * Complete assessment readiness response
 */
export interface AssessmentReadinessResponse {
  total_assets: number;
  readiness_summary: ReadinessSummary;
  asset_details: AssetReadinessDetail[];
}

/**
 * Assessment progress by attribute category
 */
export interface AssessmentProgressResponse {
  flow_id: string;
  total_attributes: number;
  filled_attributes: number;
  completeness_percentage: number;
  by_category: {
    infrastructure: { total: number; filled: number; percentage: number };
    application: { total: number; filled: number; percentage: number };
    business: { total: number; filled: number; percentage: number };
    technical_debt: { total: number; filled: number; percentage: number };
  };
}

/**
 * Critical attribute definition for assessment
 */
export interface CriticalAttribute {
  name: string;
  category: 'infrastructure' | 'application' | 'business' | 'technical_debt';
  required: boolean; // true = required for assessment, false = recommended
  description: string;
  importance: string; // Why this attribute is important for 6R assessment
}

// ============================================================================
// 22 Critical Attributes for 6R Assessment
// ============================================================================

export const CRITICAL_ATTRIBUTES: CriticalAttribute[] = [
  // Infrastructure (6 attributes)
  {
    name: 'application_name',
    category: 'infrastructure',
    required: true,
    description: 'Name of the application or workload',
    importance: 'Identifies the application in migration planning and grouping',
  },
  {
    name: 'technology_stack',
    category: 'infrastructure',
    required: true,
    description: 'Programming languages, frameworks, and technologies used',
    importance: 'Determines platform compatibility and modernization opportunities',
  },
  {
    name: 'operating_system',
    category: 'infrastructure',
    required: true,
    description: 'Operating system and version',
    importance: 'Critical for lift-and-shift vs. replatform decisions',
  },
  {
    name: 'cpu_cores',
    category: 'infrastructure',
    required: false,
    description: 'Number of CPU cores allocated',
    importance: 'Helps right-size cloud instances and estimate costs',
  },
  {
    name: 'memory_gb',
    category: 'infrastructure',
    required: true,
    description: 'Memory allocation in GB',
    importance: 'Critical for instance sizing and performance planning',
  },
  {
    name: 'storage_gb',
    category: 'infrastructure',
    required: false,
    description: 'Storage capacity in GB',
    importance: 'Determines storage requirements and backup strategies',
  },

  // Application (8 attributes)
  {
    name: 'business_criticality',
    category: 'application',
    required: true,
    description: 'Business impact rating (critical, high, medium, low)',
    importance: 'Prioritizes migration waves and determines acceptable downtime',
  },
  {
    name: 'application_type',
    category: 'application',
    required: true,
    description: 'Type of application (web, mobile, desktop, batch, etc.)',
    importance: 'Influences migration strategy and cloud architecture patterns',
  },
  {
    name: 'architecture_pattern',
    category: 'application',
    required: false,
    description: 'Architecture style (monolithic, microservices, serverless)',
    importance: 'Determines refactoring vs. rehosting approach',
  },
  {
    name: 'dependencies',
    category: 'application',
    required: true,
    description: 'Upstream and downstream dependencies',
    importance: 'Ensures proper migration sequencing and avoids breaking integrations',
  },
  {
    name: 'user_base',
    category: 'application',
    required: false,
    description: 'Number of users and usage patterns',
    importance: 'Informs scaling requirements and migration timing',
  },
  {
    name: 'data_sensitivity',
    category: 'application',
    required: true,
    description: 'Data classification (public, internal, confidential, restricted)',
    importance: 'Determines security controls and compliance requirements',
  },
  {
    name: 'compliance_requirements',
    category: 'application',
    required: false,
    description: 'Regulatory compliance needs (HIPAA, PCI-DSS, SOC 2, etc.)',
    importance: 'Impacts cloud region selection and security architecture',
  },
  {
    name: 'sla_requirements',
    category: 'application',
    required: false,
    description: 'Service level agreement targets (uptime, recovery time)',
    importance: 'Drives HA/DR design and cloud service tier selection',
  },

  // Business (4 attributes)
  {
    name: 'business_owner',
    category: 'business',
    required: true,
    description: 'Business unit or individual owning the application',
    importance: 'Ensures accountability and decision-making authority',
  },
  {
    name: 'annual_operating_cost',
    category: 'business',
    required: false,
    description: 'Current annual operating cost',
    importance: 'Establishes baseline for TCO comparison and ROI calculation',
  },
  {
    name: 'business_value',
    category: 'business',
    required: true,
    description: 'Revenue generation or cost savings impact',
    importance: 'Justifies migration investment and prioritizes modernization',
  },
  {
    name: 'strategic_importance',
    category: 'business',
    required: false,
    description: 'Strategic value to organization (transformational, competitive advantage)',
    importance: 'Identifies candidates for rearchitecting vs. retiring',
  },

  // Technical Debt (4 attributes)
  {
    name: 'code_quality_score',
    category: 'technical_debt',
    required: false,
    description: 'Code quality metrics (maintainability, test coverage)',
    importance: 'Indicates refactoring effort and technical risk',
  },
  {
    name: 'last_update_date',
    category: 'technical_debt',
    required: true,
    description: 'Date of last significant update or release',
    importance: 'Identifies stale applications that may be candidates for retirement',
  },
  {
    name: 'support_status',
    category: 'technical_debt',
    required: false,
    description: 'Vendor support status (active, extended, end-of-life)',
    importance: 'Forces migration timeline decisions for unsupported platforms',
  },
  {
    name: 'known_vulnerabilities',
    category: 'technical_debt',
    required: true,
    description: 'Count and severity of known security vulnerabilities',
    importance: 'Prioritizes security remediation and influences rehost vs. replatform',
  },
];

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Calculate readiness percentage from score (0-1 to 0-100)
 */
export function getReadinessPercentage(score: number): number {
  return Math.round(score * 100);
}

/**
 * Get readiness status from percentage
 */
export function getReadinessStatus(
  percentage: number
): 'ready' | 'not_ready' | 'in_progress' {
  if (percentage >= 75) return 'ready';
  if (percentage >= 50) return 'in_progress';
  return 'not_ready';
}

/**
 * Get readiness color variant based on percentage
 */
export function getReadinessColor(percentage: number): {
  variant: 'default' | 'secondary' | 'destructive';
  className: string;
} {
  if (percentage >= 75) {
    return { variant: 'default', className: 'text-green-600' };
  }
  if (percentage >= 50) {
    return { variant: 'secondary', className: 'text-yellow-600' };
  }
  return { variant: 'destructive', className: 'text-red-600' };
}

/**
 * Get critical attributes by category
 */
export function getCriticalAttributesByCategory(
  category: 'infrastructure' | 'application' | 'business' | 'technical_debt'
): CriticalAttribute[] {
  return CRITICAL_ATTRIBUTES.filter((attr) => attr.category === category);
}

/**
 * Count total critical attributes by category
 */
export function countCriticalAttributesByCategory(): Record<string, number> {
  return {
    infrastructure: getCriticalAttributesByCategory('infrastructure').length,
    application: getCriticalAttributesByCategory('application').length,
    business: getCriticalAttributesByCategory('business').length,
    technical_debt: getCriticalAttributesByCategory('technical_debt').length,
  };
}

// ============================================================================
// Day 12 - Comprehensive Gap Analysis Types (Issue #980)
// ============================================================================

/**
 * Column gap report from ColumnInspector.
 *
 * Categorizes missing data in Asset SQLAlchemy columns:
 * - missing_attributes: Required columns that don't exist
 * - empty_attributes: Columns with empty strings/lists/dicts
 * - null_attributes: Columns with None/NULL values
 */
export interface ColumnGapReport {
  missing_attributes: string[];
  empty_attributes: string[];
  null_attributes: string[];
  completeness_score: number; // 0.0-1.0
}

/**
 * Enrichment gap report from EnrichmentInspector.
 *
 * Checks 7 enrichment tables:
 * - resilience, compliance_flags, vulnerabilities, tech_debt,
 *   dependencies, performance_metrics, cost_optimization
 */
export interface EnrichmentGapReport {
  missing_tables: string[];
  incomplete_tables: Record<string, string[]>; // table_name -> [missing_fields]
  completeness_score: number; // 0.0-1.0
}

/**
 * JSONB gap report from JSONBInspector.
 *
 * Checks JSONB fields: custom_attributes, technical_details, metadata
 * Supports nested key checking with dot notation.
 */
export interface JSONBGapReport {
  missing_keys: Record<string, string[]>; // field_name -> [missing_keys]
  empty_values: Record<string, string[]>; // field_name -> [empty_keys]
  completeness_score: number; // 0.0-1.0
}

/**
 * Application gap report from ApplicationInspector.
 *
 * Checks CanonicalApplication metadata:
 * - Application metadata (name, description, type, business unit)
 * - Technology stack completeness
 * - Business context fields (owners, stakeholders, user base)
 */
export interface ApplicationGapReport {
  missing_metadata: string[];
  incomplete_tech_stack: string[];
  missing_business_context: string[];
  completeness_score: number; // 0.0-1.0
}

/**
 * Standards violation details.
 *
 * Represents a failure to meet an EngagementArchitectureStandard.
 */
export interface StandardViolation {
  standard_name: string;
  requirement_type: string; // security, performance, compliance
  violation_details: string; // Expected vs actual values
  is_mandatory: boolean;
  override_available: boolean;
}

/**
 * Standards gap report from StandardsInspector.
 *
 * Validates asset against EngagementArchitectureStandard records.
 * Uses tenant-scoped database queries (client_account_id + engagement_id).
 */
export interface StandardsGapReport {
  violated_standards: StandardViolation[];
  missing_mandatory_data: string[];
  override_required: boolean;
  completeness_score: number; // 0.0-1.0
}

/**
 * Comprehensive gap analysis across all data layers.
 *
 * Orchestrates all 5 inspectors (column, enrichment, JSONB, application, standards)
 * to produce a complete picture of asset data completeness.
 *
 * Performance: <50ms per asset
 * Part of Issue #980: Intelligent Multi-Layer Gap Detection System
 */
export interface ComprehensiveGapReport {
  // Inspector reports
  column_gaps: ColumnGapReport;
  enrichment_gaps: EnrichmentGapReport;
  jsonb_gaps: JSONBGapReport;
  application_gaps: ApplicationGapReport;
  standards_gaps: StandardsGapReport;

  // Weighted completeness
  overall_completeness: number; // 0.0-1.0 weighted score
  weighted_scores: Record<string, number>; // Layer name -> score

  // Prioritized gaps
  critical_gaps: string[]; // Priority 1 missing fields (blocks assessment)
  high_priority_gaps: string[]; // Priority 2 missing fields
  medium_priority_gaps: string[]; // Priority 3 missing fields

  // Assessment readiness
  is_ready_for_assessment: boolean;
  readiness_blockers: string[]; // Reasons why not ready
  completeness_threshold: number; // Minimum score for readiness (default 0.75)

  // Metadata
  asset_id: string;
  asset_name: string;
  asset_type: string;
  analyzed_at: string; // ISO 8601 timestamp
}

/**
 * Batch readiness summary for all flow assets.
 *
 * Lightweight or detailed mode for performance optimization.
 */
export interface BatchReadinessSummary {
  flow_id: string;
  total_assets: number;
  ready_count: number;
  not_ready_count: number;
  overall_readiness_rate: number; // Percentage 0-100
  asset_reports?: Record<string, ComprehensiveGapReport>; // Optional detailed reports (detailed=true)
  summary_by_type: Record<string, TypeReadinessSummary>;
  analyzed_at: string; // ISO 8601 timestamp
}

/**
 * Readiness summary grouped by asset type.
 */
export interface TypeReadinessSummary {
  asset_type: string;
  total: number;
  ready: number;
  not_ready: number;
  readiness_rate: number; // Percentage 0-100
}
