/**
 * Metadata Types
 *
 * Common metadata patterns and structures used across admin modules
 * for tracking additional information and context.
 *
 * Generated with CC for modular admin type organization.
 */

/**
 * Base metadata interface
 */
export interface BaseMetadata {
  version: string;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
  tags?: string[];
  custom?: Record<string, string | number | boolean | null | undefined>;
}

/**
 * Audit log metadata
 */
export interface AuditMetadata extends BaseMetadata {
  source: AuditSource;
  correlation_id?: string;
  request_id?: string;
  trace_id?: string;
  schema_version: string;
}

/**
 * Notification metadata
 */
export interface NotificationMetadata extends BaseMetadata {
  correlation_id?: string;
  campaign_id?: string;
  engagement_id?: string;
  client_account_id?: string;
  source_system?: string;
}

/**
 * Analytics metadata
 */
export interface AnalyticsMetadata extends BaseMetadata {
  data_sources: DataSource[];
  calculation_method: string;
  quality_score: number;
  completeness: number;
  freshness: string;
  accuracy_estimate: number;
  limitations: string[];
  notes: string[];
}

/**
 * Report metadata
 */
export interface ReportMetadata extends BaseMetadata {
  template_id?: string;
  template_version?: string;
  data_sources: DataSource[];
  generation_time: number;
  filters_applied: unknown[];
  permissions: ReportPermission[];
}

/**
 * Security event metadata
 */
export interface SecurityEventMetadata extends BaseMetadata {
  correlation_id: string;
  investigation_id?: string;
  incident_id?: string;
  source_system: string;
  detection_rule?: string;
  false_positive: boolean;
  analyst_notes?: string[];
}

/**
 * Template metadata
 */
export interface TemplateMetadata extends BaseMetadata {
  author: string;
  version_notes?: string;
  approval_status?: ApprovalStatus;
  approved_by?: string;
  approved_at?: string;
  usage_count: number;
  performance_metrics?: unknown;
}

/**
 * Data source information
 */
export interface DataSource {
  name: string;
  type: DataSourceType;
  last_updated: string;
  quality_score: number;
  completeness: number;
}

/**
 * Report permission
 */
export interface ReportPermission {
  userId: string;
  permissions: string[];
  scope: string;
}

/**
 * Audit source types
 */
export type AuditSource = 'user' | 'system' | 'api' | 'webhook' | 'scheduled' | 'automated';

/**
 * Data source types
 */
export type DataSourceType = 'database' | 'api' | 'file' | 'stream' | 'cache' | 'external';

/**
 * Approval status types
 */
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'needs_review';
