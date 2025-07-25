/**
 * Data Types
 *
 * Data source and transformation type definitions.
 */

import type { ChartConfig, TableConfig, MetricConfig, TextConfig, MapConfig } from './visualization-types';

export interface DataSource {
  type: DataSourceType;
  endpoint?: string;
  query?: string;
  parameters?: Record<string, string | number | boolean | null>;
  headers?: Record<string, string>;
  authentication?: DataSourceAuth;
  transformation?: DataTransformation;
}

export interface VisualizationConfig {
  type: VisualizationType;
  chart?: ChartConfig;
  table?: TableConfig;
  metric?: MetricConfig;
  text?: TextConfig;
  map?: MapConfig;
}

export interface DataSourceAuth {
  type: AuthType;
  username?: string;
  password?: string;
  token?: string;
  apiKey?: string;
  headers?: Record<string, string>;
}

export interface DataTransformation {
  fields?: FieldMapping[];
  aggregations?: AggregationRule[];
  filters?: FilterRule[];
  sorting?: SortRule[];
  grouping?: GroupRule[];
  calculations?: CalculationRule[];
}

export interface FieldMapping {
  source: string;
  target: string;
  transform?: string;
}

export interface AggregationRule {
  field: string;
  operation: AggregationType;
  alias?: string;
}

export interface FilterRule {
  field: string;
  operator: FilterOperator;
  value: unknown;
}

export interface SortRule {
  field: string;
  direction: 'asc' | 'desc';
  priority?: number;
}

export interface GroupRule {
  field: string;
  aggregations?: AggregationRule[];
}

export interface CalculationRule {
  alias: string;
  expression: string;
  type: 'number' | 'string' | 'date' | 'boolean';
}

// Enum types
export type DataSourceType = 'api' | 'database' | 'file' | 'realtime' | 'mock' | 'static';
export type VisualizationType = 'chart' | 'table' | 'metric' | 'text' | 'map';
export type AuthType = 'none' | 'basic' | 'bearer' | 'api_key' | 'oauth' | 'custom';
export type AggregationType = 'sum' | 'avg' | 'min' | 'max' | 'count' | 'distinct' | 'first' | 'last' | 'median' | 'mode';
export type FilterOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in' | 'is_null' | 'is_not_null';
