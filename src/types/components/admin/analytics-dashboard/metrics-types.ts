/**
 * Metrics Types
 * 
 * Metrics overview and metric-specific type definitions.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../../shared';
import { TimeRange, ExportFormat } from './widget-types';

export interface MetricsOverviewProps extends BaseComponentProps {
  metrics: Metric[];
  loading?: boolean;
  error?: string | null;
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  comparisonEnabled?: boolean;
  comparisonPeriod?: TimeRange;
  onComparisonPeriodChange?: (timeRange: TimeRange) => void;
  groupBy?: string;
  onGroupByChange?: (groupBy: string) => void;
  filters?: MetricFilter[];
  onFiltersChange?: (filters: Record<string, string | number | boolean | null>) => void;
  onMetricClick?: (metric: Metric) => void;
  onDrillDown?: (metric: Metric, filters?: Record<string, string | number | boolean | null>) => void;
  refreshInterval?: number;
  onRefresh?: () => void;
  showTrends?: boolean;
  showTargets?: boolean;
  showAlerts?: boolean;
  showExport?: boolean;
  exportFormats?: ExportFormat[];
  onExport?: (format: ExportFormat, metrics: Metric[]) => void;
  renderMetric?: (metric: Metric) => ReactNode;
  renderTrend?: (metric: Metric, trend: MetricTrend) => ReactNode;
  renderTarget?: (metric: Metric, target: MetricTarget) => ReactNode;
  renderAlert?: (metric: Metric, alert: MetricAlert) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'cards' | 'table' | 'chart' | 'tiles';
  layout?: 'grid' | 'list' | 'masonry';
  columns?: number;
  spacing?: number | string;
  showValues?: boolean;
  showPercentages?: boolean;
  showChanges?: boolean;
  showSparklines?: boolean;
}

export interface Metric {
  id: string;
  name: string;
  description?: string;
  value: number | string;
  previousValue?: number | string;
  change?: number;
  changeType?: ChangeType;
  unit?: string;
  format?: MetricFormat;
  trend?: MetricTrend;
  target?: MetricTarget;
  alert?: MetricAlert;
  category?: string;
  tags?: string[];
  priority?: MetricPriority;
  visibility?: MetricVisibility;
  permissions?: string[];
  lastUpdated?: string;
  dataSource?: string;
  calculation?: MetricCalculation;
}

export interface MetricFilter {
  id: string;
  label: string;
  type: FilterType;
  field: string;
  options?: FilterOption[];
  value?: unknown;
  required?: boolean;
}

export interface MetricTrend {
  direction: TrendDirection;
  data: TrendDataPoint[];
  period: TrendPeriod;
  confidence?: number;
  forecast?: TrendForecast;
}

export interface MetricTarget {
  value: number;
  type: TargetType;
  period: TargetPeriod;
  status: TargetStatus;
  progress?: number;
  deadline?: string;
  description?: string;
}

export interface MetricAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  condition: AlertCondition;
  message: string;
  triggered: boolean;
  triggeredAt?: string;
  acknowledged?: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
}

export interface MetricFormat {
  type: FormatType;
  decimals?: number;
  thousandsSeparator?: string;
  decimalSeparator?: string;
  prefix?: string;
  suffix?: string;
  currency?: string;
  showSign?: boolean;
  compact?: boolean;
}

export interface MetricCalculation {
  formula: string;
  dependencies: string[];
  schedule?: CalculationSchedule;
  cache?: boolean;
  cacheTTL?: number;
}

export interface TrendDataPoint {
  timestamp: string;
  value: number;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface TrendForecast {
  enabled: boolean;
  periods: number;
  confidence: number;
  data: TrendDataPoint[];
}

export interface AlertCondition {
  field: string;
  operator: AlertOperator;
  value: unknown;
  duration?: number;
  consecutive?: boolean;
}

export interface FilterOption {
  label: string;
  value: unknown;
  description?: string;
  count?: number;
}

export interface CalculationSchedule {
  enabled: boolean;
  frequency: ScheduleFrequency;
  cron?: string;
  timezone?: string;
}

// Enum types
export type ChangeType = 'increase' | 'decrease' | 'stable' | 'unknown';
export type MetricPriority = 'low' | 'medium' | 'high' | 'critical';
export type MetricVisibility = 'public' | 'private' | 'restricted';
export type FilterType = 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'numberrange' | 'boolean';
export type TrendDirection = 'up' | 'down' | 'stable' | 'volatile';
export type TrendPeriod = 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';
export type TargetType = 'minimum' | 'maximum' | 'goal' | 'threshold' | 'range';
export type TargetPeriod = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
export type TargetStatus = 'on_track' | 'at_risk' | 'off_track' | 'achieved' | 'failed';
export type AlertType = 'threshold' | 'anomaly' | 'trend' | 'custom';
export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';
export type AlertOperator = 'greater_than' | 'less_than' | 'equals' | 'not_equals' | 'between' | 'outside';
export type FormatType = 'number' | 'percentage' | 'currency' | 'bytes' | 'duration' | 'custom';
export type ScheduleFrequency = 'realtime' | 'minute' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'custom';