/**
 * Analytics and Reporting API Types
 * 
 * @deprecated This file has been modularized. Please import from specific modules:
 * - @/types/api/admin/analytics for all analytics types
 * - @/types/api/admin/analytics/api-types for API request/response types
 * - @/types/api/admin/analytics/platform for platform analytics types
 * - @/types/api/admin/analytics/usage for usage analytics types
 * - @/types/api/admin/analytics/performance for performance analytics types
 * - @/types/api/admin/analytics/reports for report generation types
 * - @/types/api/admin/analytics/insights for insights and alerts types
 * - @/types/api/admin/common for shared types
 * 
 * This file now re-exports all types for backward compatibility.
 * 
 * Generated with CC for modular admin type organization.
 */

// Re-export all analytics types for backward compatibility
export type * from './analytics';

// Re-export common types that might have been used from this file
export type { 
  AnalyticsTimeRange,
  AnalyticsPeriod,
  AnalyticsMetadata,
  ReportMetadata,
  DataSource,
  DataSourceType,
  ConfidenceLevel,
  TrendDirection,
  FilterOperator
} from './common';