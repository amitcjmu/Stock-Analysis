/**
 * Admin Analytics Dashboard Component Types
 * 
 * Type definitions for analytics dashboard components including dashboard widgets,
 * metrics overview, and data visualization systems.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

// Analytics Dashboard component types
export interface AnalyticsDashboardProps extends BaseComponentProps {
  widgets: DashboardWidget[];
  layout: DashboardLayout;
  onLayoutChange?: (layout: DashboardLayout) => void;
  onWidgetAdd?: (widget: DashboardWidget) => void;
  onWidgetRemove?: (widgetId: string) => void;
  onWidgetUpdate?: (widgetId: string, updates: Partial<DashboardWidget>) => void;
  onWidgetResize?: (widgetId: string, size: { width: number; height: number }) => void;
  onWidgetMove?: (widgetId: string, position: { x: number; y: number }) => void;
  loading?: boolean;
  error?: string | null;
  editable?: boolean;
  resizable?: boolean;
  draggable?: boolean;
  responsive?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onRefresh?: () => void;
  filters?: DashboardFilter[];
  onFiltersChange?: (filters: Record<string, any>) => void;
  timeRange?: TimeRange;
  onTimeRangeChange?: (timeRange: TimeRange) => void;
  templates?: DashboardTemplate[];
  onLoadTemplate?: (template: DashboardTemplate) => void;
  onSaveTemplate?: (name: string, description?: string) => void;
  onExport?: (format: ExportFormat) => void;
  renderWidget?: (widget: DashboardWidget) => ReactNode;
  renderWidgetHeader?: (widget: DashboardWidget) => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  variant?: 'default' | 'compact' | 'detailed';
  theme?: 'light' | 'dark' | 'auto';
  gridSize?: number;
  margin?: number | [number, number];
  padding?: number | [number, number];
  containerPadding?: number | [number, number];
  rowHeight?: number;
  maxRows?: number;
  cols?: number;
  breakpoints?: Record<string, number>;
  colWidths?: Record<string, number>;
}

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
  onFiltersChange?: (filters: Record<string, any>) => void;
  onMetricClick?: (metric: Metric) => void;
  onDrillDown?: (metric: Metric, filters?: Record<string, any>) => void;
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

// Supporting types for Analytics Dashboard
export interface DashboardWidget {
  id: string;
  type: WidgetType;
  title: string;
  description?: string;
  position: WidgetPosition;
  size: WidgetSize;
  configuration: WidgetConfiguration;
  data?: any;
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

export interface DataSource {
  type: DataSourceType;
  endpoint?: string;
  query?: string;
  parameters?: Record<string, any>;
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

export interface ChartConfig {
  chartType: ChartType;
  xAxis?: AxisConfig;
  yAxis?: AxisConfig;
  series?: SeriesConfig[];
  legend?: LegendConfig;
  tooltip?: TooltipConfig;
  colors?: string[];
  theme?: ChartTheme;
  animations?: boolean;
  responsive?: boolean;
}

export interface TableConfig {
  columns: TableColumn[];
  pagination?: PaginationConfig;
  sorting?: SortingConfig;
  filtering?: FilteringConfig;
  selection?: SelectionConfig;
  styling?: TableStyling;
}

export interface MetricConfig {
  value: MetricValue;
  comparison?: MetricComparison;
  trend?: MetricTrend;
  target?: MetricTarget;
  format?: MetricFormat;
  styling?: MetricStyling;
}

export interface DashboardFilter {
  id: string;
  label: string;
  type: FilterType;
  field: string;
  options?: FilterOption[];
  value?: any;
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
  category: string;
  tags: string[];
  lastUpdated: string;
}

export interface MetricFilter {
  id: string;
  label: string;
  type: FilterType;
  field: string;
  operator: FilterOperator;
  value?: any;
  options?: FilterOption[];
}

export interface MetricTrend {
  data: TrendDataPoint[];
  direction: TrendDirection;
  confidence: number;
  period: string;
}

export interface TrendDataPoint {
  timestamp: string;
  value: number;
}

export interface MetricTarget {
  value: number;
  type: TargetType;
  period: string;
  status: TargetStatus;
  progress: number;
}

export interface MetricAlert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  threshold: number;
  triggered: boolean;
  triggeredAt?: string;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
}

export interface LayoutBreakpoint {
  name: string;
  width: number;
  cols: number;
  margin?: [number, number];
  containerPadding?: [number, number];
}

export interface LayoutSettings {
  responsive: boolean;
  compactType?: CompactType;
  preventCollision?: boolean;
  useCSSTransforms?: boolean;
  autoSize?: boolean;
  margin?: [number, number];
  containerPadding?: [number, number];
  rowHeight?: number;
  maxRows?: number;
}

export interface WidgetFilter {
  field: string;
  operator: FilterOperator;
  value: any;
  label?: string;
}

export interface AggregationConfig {
  type: AggregationType;
  field?: string;
  groupBy?: string[];
  having?: FilterCondition[];
}

export interface FormattingConfig {
  numberFormat?: NumberFormat;
  dateFormat?: string;
  colorScheme?: string[];
  conditional?: ConditionalFormatting[];
}

export interface InteractionConfig {
  clickEnabled?: boolean;
  hoverEnabled?: boolean;
  selectionEnabled?: boolean;
  drillDownEnabled?: boolean;
  onClickAction?: InteractionAction;
  onHoverAction?: InteractionAction;
}

export interface RefreshConfig {
  enabled: boolean;
  interval: number;
  autoRefresh: boolean;
  refreshOnFilter: boolean;
  refreshOnWindowFocus: boolean;
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
  type: TransformationType;
  script?: string;
  mapping?: FieldMapping[];
  aggregation?: AggregationRule[];
  filtering?: FilterRule[];
}

export interface AxisConfig {
  label?: string;
  type?: AxisType;
  scale?: ScaleType;
  min?: number;
  max?: number;
  format?: string;
  grid?: boolean;
  ticks?: TickConfig;
}

export interface SeriesConfig {
  name: string;
  type?: SeriesType;
  data: any[];
  color?: string;
  axis?: 'left' | 'right';
  visible?: boolean;
}

export interface LegendConfig {
  show: boolean;
  position: LegendPosition;
  orientation: LegendOrientation;
  itemStyle?: any;
}

export interface TooltipConfig {
  show: boolean;
  trigger: TooltipTrigger;
  formatter?: string;
  backgroundColor?: string;
  textStyle?: any;
}

export interface TableColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: any, index: number) => ReactNode;
  align?: 'left' | 'center' | 'right';
  fixed?: 'left' | 'right';
}

export interface PaginationConfig {
  enabled: boolean;
  pageSize: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
}

export interface SortingConfig {
  enabled: boolean;
  defaultSort?: { field: string; direction: SortDirection };
  multiSort?: boolean;
}

export interface FilteringConfig {
  enabled: boolean;
  filters: TableFilter[];
  searchEnabled?: boolean;
  searchFields?: string[];
}

export interface SelectionConfig {
  enabled: boolean;
  type: SelectionType;
  rowKey: string;
  checkboxColumn?: boolean;
}

export interface TableStyling {
  striped?: boolean;
  bordered?: boolean;
  hover?: boolean;
  compact?: boolean;
  size?: TableSize;
}

export interface MetricValue {
  current: number | string;
  previous?: number | string;
  target?: number | string;
}

export interface MetricComparison {
  type: ComparisonType;
  period: string;
  value: number;
  percentage: number;
}

export interface MetricFormat {
  type: FormatType;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  separator?: string;
}

export interface MetricStyling {
  size?: MetricSize;
  color?: string;
  backgroundColor?: string;
  iconColor?: string;
  showIcon?: boolean;
  iconName?: string;
}

// Supporting types and enums
export type WidgetType = 
  | 'chart' 
  | 'table' 
  | 'metric' 
  | 'text' 
  | 'map' 
  | 'gauge' 
  | 'progress' 
  | 'list' 
  | 'calendar' 
  | 'timeline';

export type DataSourceType = 
  | 'api' 
  | 'database' 
  | 'csv' 
  | 'json' 
  | 'websocket' 
  | 'static';

export type VisualizationType = 
  | 'chart' 
  | 'table' 
  | 'metric' 
  | 'text' 
  | 'map' 
  | 'custom';

export type ChartType = 
  | 'line' 
  | 'bar' 
  | 'area' 
  | 'pie' 
  | 'doughnut' 
  | 'scatter' 
  | 'bubble' 
  | 'radar' 
  | 'heatmap' 
  | 'treemap' 
  | 'sankey' 
  | 'funnel';

export type FilterType = 
  | 'text' 
  | 'select' 
  | 'multiselect' 
  | 'date' 
  | 'daterange' 
  | 'number' 
  | 'numberrange' 
  | 'boolean';

export type TimeRangePreset = 
  | 'last_hour' 
  | 'last_24_hours' 
  | 'last_7_days' 
  | 'last_30_days' 
  | 'last_90_days' 
  | 'last_year' 
  | 'this_week' 
  | 'this_month' 
  | 'this_year' 
  | 'custom';

export type ChangeType = 'increase' | 'decrease' | 'neutral';
export type TrendDirection = 'up' | 'down' | 'stable';
export type TargetType = 'minimum' | 'maximum' | 'exact' | 'range';
export type TargetStatus = 'met' | 'not_met' | 'exceeded' | 'approaching';
export type AlertType = 'threshold' | 'anomaly' | 'trend' | 'custom';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type CompactType = 'vertical' | 'horizontal';
export type FilterOperator = 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'in' | 'between';
export type AggregationType = 'sum' | 'average' | 'count' | 'min' | 'max' | 'distinct';
export type AuthType = 'none' | 'basic' | 'bearer' | 'api_key' | 'oauth';
export type TransformationType = 'javascript' | 'jmespath' | 'jsonata' | 'custom';
export type AxisType = 'linear' | 'logarithmic' | 'time' | 'category';
export type ScaleType = 'linear' | 'log' | 'time' | 'ordinal';
export type SeriesType = 'line' | 'bar' | 'area' | 'scatter';
export type LegendPosition = 'top' | 'bottom' | 'left' | 'right';
export type LegendOrientation = 'horizontal' | 'vertical';
export type TooltipTrigger = 'hover' | 'click' | 'focus';
export type SortDirection = 'asc' | 'desc';
export type SelectionType = 'single' | 'multiple';
export type TableSize = 'small' | 'medium' | 'large';
export type ComparisonType = 'absolute' | 'percentage';
export type FormatType = 'number' | 'currency' | 'percentage' | 'bytes' | 'duration';
export type MetricSize = 'small' | 'medium' | 'large';

// Additional supporting interfaces
export interface FilterOption {
  label: string;
  value: any;
  disabled?: boolean;
}

export interface FilterCondition {
  field: string;
  operator: FilterOperator;
  value: any;
}

export interface NumberFormat {
  locale?: string;
  style?: 'decimal' | 'currency' | 'percent';
  currency?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
}

export interface ConditionalFormatting {
  condition: FilterCondition;
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
  value: any;
}

export interface TickConfig {
  count?: number;
  interval?: number;
  formatter?: string;
}

export interface TableFilter {
  field: string;
  type: FilterType;
  options?: FilterOption[];
}

export interface ChartTheme {
  name: string;
  colors: string[];
  backgroundColor?: string;
  textColor?: string;
  gridColor?: string;
}

export interface TextConfig {
  content: string;
  format: 'plain' | 'markdown' | 'html';
  styling?: TextStyling;
}

export interface TextStyling {
  fontSize?: string;
  fontWeight?: string;
  color?: string;
  textAlign?: 'left' | 'center' | 'right';
  lineHeight?: string;
}

export interface MapConfig {
  type: 'geographic' | 'network' | 'floor_plan';
  center?: [number, number];
  zoom?: number;
  layers?: MapLayer[];
  markers?: MapMarker[];
  regions?: MapRegion[];
}

export interface MapLayer {
  id: string;
  type: 'base' | 'overlay';
  source: string;
  visible: boolean;
  opacity?: number;
}

export interface MapMarker {
  id: string;
  position: [number, number];
  icon?: string;
  size?: number;
  color?: string;
  popup?: string;
  data?: any;
}

export interface MapRegion {
  id: string;
  coordinates: [number, number][];
  color?: string;
  opacity?: number;
  popup?: string;
  data?: any;
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