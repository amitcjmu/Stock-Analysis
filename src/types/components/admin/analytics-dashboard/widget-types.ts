/**
 * Widget Types
 * 
 * Widget-related type definitions including configuration and layout.
 */

import { DataSource, VisualizationConfig } from './data-types';
import { WidgetFilter, AggregationConfig, FormattingConfig, InteractionConfig, RefreshConfig } from './configuration-types';

export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  description?: string;
  position: WidgetPosition;
  size: WidgetSize;
  configuration: WidgetConfiguration;
  data?: unknown;
  loading?: boolean;
  error?: string;
  refreshInterval?: number;
  lastUpdated?: string;
  permissions?: string[];
  visible: boolean;
}

export interface DashboardLayout {
  id: string;
  name: string;
  description?: string;
  widgets: WidgetLayout[];
  breakpoints: LayoutBreakpoint[];
  settings: LayoutSettings;
  isDefault?: boolean;
  isShared?: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface WidgetLayout {
  widgetId: string;
  position: WidgetPosition;
  size: WidgetSize;
  breakpoints?: Record<string, { position: WidgetPosition; size: WidgetSize }>;
}

export interface WidgetPosition {
  x: number;
  y: number;
}

export interface WidgetSize {
  width: number;
  height: number;
}

export interface WidgetConfiguration {
  dataSource: DataSource;
  visualization: VisualizationConfig;
  filters?: WidgetFilter[];
  aggregation?: AggregationConfig;
  formatting?: FormattingConfig;
  interaction?: InteractionConfig;
  refresh?: RefreshConfig;
}

export interface DashboardFilter {
  id: string;
  label: string;
  type: FilterType;
  field: string;
  options?: FilterOption[];
  value?: unknown;
  required?: boolean;
  cascading?: boolean;
  dependencies?: string[];
}

export interface DashboardTemplate {
  id: string;
  name: string;
  description?: string;
  preview?: string;
  category: string;
  tags: string[];
  layout: DashboardLayout;
  isPublic: boolean;
  createdBy: string;
  createdAt: string;
  downloads: number;
  rating: number;
}

export interface TimeRange {
  start: string;
  end: string;
  preset?: TimeRangePreset;
  timezone?: string;
}

export interface LayoutBreakpoint {
  breakpoint: string;
  cols: number;
  rowHeight: number;
  margin: [number, number];
  containerPadding: [number, number];
}

export interface LayoutSettings {
  margin: [number, number];
  containerPadding: [number, number];
  rowHeight: number;
  autoSize: boolean;
  verticalCompact: boolean;
  preventCollision: boolean;
}

export interface FilterOption {
  label: string;
  value: unknown;
  description?: string;
  count?: number;
}

export interface ExportFormat {
  type: 'png' | 'jpg' | 'svg' | 'pdf' | 'csv' | 'excel' | 'json';
  label: string;
  options?: ExportOptions;
}

export interface ExportOptions {
  width?: number;
  height?: number;
  quality?: number;
  includeData?: boolean;
  includeConfiguration?: boolean;
}

// Enum types
export type WidgetType = 'chart' | 'table' | 'metric' | 'text' | 'map' | 'image' | 'iframe' | 'custom';
export type FilterType = 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'numberrange' | 'boolean';
export type TimeRangePreset = 'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days' | 'last_90_days' | 'last_year' | 'this_week' | 'this_month' | 'this_year' | 'custom';