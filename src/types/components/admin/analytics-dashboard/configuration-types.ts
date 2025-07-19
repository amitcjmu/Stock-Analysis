/**
 * Configuration Types
 * 
 * Widget configuration and interaction type definitions.
 */

export interface WidgetFilter {
  id: string;
  field: string;
  operator: FilterOperator;
  value: any;
  label?: string;
}

export interface AggregationConfig {
  enabled: boolean;
  rules: AggregationRule[];
  groupBy?: string[];
}

export interface FormattingConfig {
  enabled: boolean;
  rules: FormattingRule[];
  conditionalFormatting?: ConditionalFormatting[];
}

export interface InteractionConfig {
  enabled: boolean;
  clickAction?: InteractionAction;
  hoverAction?: InteractionAction;
  selectionAction?: InteractionAction;
  drillDown?: DrillDownConfig;
}

export interface RefreshConfig {
  enabled: boolean;
  interval: number;
  autoRefresh: boolean;
  lastRefresh?: string;
}

export interface AggregationRule {
  field: string;
  operation: AggregationType;
  alias?: string;
}

export interface FormattingRule {
  field: string;
  format: FormatType;
  options?: FormattingOptions;
}

export interface ConditionalFormatting {
  field: string;
  conditions: FormattingCondition[];
}

export interface FormattingCondition {
  operator: ConditionOperator;
  value: any;
  style: FormattingStyle;
}

export interface FormattingStyle {
  color?: string;
  backgroundColor?: string;
  fontWeight?: string;
  fontStyle?: string;
  icon?: string;
}

export interface InteractionAction {
  type: 'navigate' | 'filter' | 'drill_down' | 'modal' | 'custom';
  target?: string;
  parameters?: Record<string, any>;
}

export interface DrillDownConfig {
  enabled: boolean;
  levels: DrillDownLevel[];
  autoExpand?: boolean;
}

export interface DrillDownLevel {
  field: string;
  label: string;
  widget?: string;
  filters?: WidgetFilter[];
}

export interface FormattingOptions {
  decimals?: number;
  thousandsSeparator?: string;
  decimalSeparator?: string;
  prefix?: string;
  suffix?: string;
  currency?: string;
  dateFormat?: string;
  timeFormat?: string;
}

// Enum types
export type FilterOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in' | 'is_null' | 'is_not_null';
export type AggregationType = 'sum' | 'avg' | 'min' | 'max' | 'count' | 'distinct' | 'first' | 'last' | 'median' | 'mode';
export type FormatType = 'number' | 'percentage' | 'currency' | 'bytes' | 'duration' | 'date' | 'time' | 'custom';
export type ConditionOperator = 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'between' | 'contains' | 'starts_with' | 'ends_with';