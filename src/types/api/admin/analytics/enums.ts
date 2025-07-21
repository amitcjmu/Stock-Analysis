/**
 * Analytics Enums
 * 
 * Enumeration types specific to analytics and reporting.
 * 
 * Generated with CC for modular admin type organization.
 */

// Report types
export type ReportType = 
  | 'usage' 
  | 'performance' 
  | 'security' 
  | 'billing' 
  | 'engagement' 
  | 'user_activity' 
  | 'compliance' 
  | 'health' 
  | 'custom';

// Report formats
export type ReportFormat = 'pdf' | 'html' | 'docx' | 'xlsx' | 'json' | 'csv';

// Aggregation types
export type AggregationType = 'sum' | 'avg' | 'min' | 'max' | 'count' | 'distinct' | 'percentile';

// Section types for reports
export type SectionType = 
  | 'summary' 
  | 'chart' 
  | 'table' 
  | 'text' 
  | 'metric_grid' 
  | 'kpi_dashboard' 
  | 'trend_analysis' 
  | 'comparison' 
  | 'forecast' 
  | 'insights' 
  | 'recommendations';

// Insight types
export type InsightType = 
  | 'anomaly' 
  | 'trend' 
  | 'correlation' 
  | 'prediction' 
  | 'opportunity' 
  | 'risk' 
  | 'optimization';

// Alert types
export type AlertType = 
  | 'threshold' 
  | 'anomaly' 
  | 'trend' 
  | 'forecast' 
  | 'quality' 
  | 'performance';

// Alert severity levels
export type AlertSeverity = 'info' | 'warning' | 'critical' | 'emergency';

// Delivery methods
export type DeliveryMethod = 'email' | 'download' | 'api' | 'webhook' | 's3' | 'ftp';

// Data visualization types
export type DataVisualizationType = 
  | 'chart' 
  | 'table' 
  | 'map' 
  | 'gauge' 
  | 'metric' 
  | 'text';