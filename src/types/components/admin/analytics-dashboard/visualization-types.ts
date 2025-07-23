/**
 * Visualization Types
 * 
 * Chart, table, metric, and other visualization configuration types.
 */

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

export interface TextConfig {
  content: string;
  format: 'plain' | 'markdown' | 'html';
  styling?: TextStyling;
}

export interface MapConfig {
  type: 'geographic' | 'network' | 'floor_plan';
  center?: [number, number];
  zoom?: number;
  layers?: MapLayer[];
  markers?: MapMarker[];
  regions?: MapRegion[];
}

export interface AxisConfig {
  label?: string;
  type?: AxisType;
  scale?: ScaleType;
  min?: number;
  max?: number;
  ticks?: TickConfig;
  grid?: boolean;
  format?: string;
}

export interface SeriesConfig {
  name: string;
  type?: SeriesType;
  data: unknown[];
  color?: string;
  yAxisIndex?: number;
  stack?: string;
  smooth?: boolean;
  symbol?: string;
  symbolSize?: number;
}

export interface LegendConfig {
  show: boolean;
  position: LegendPosition;
  orientation: 'horizontal' | 'vertical';
  align?: 'left' | 'center' | 'right';
  verticalAlign?: 'top' | 'middle' | 'bottom';
}

export interface TooltipConfig {
  show: boolean;
  trigger: 'item' | 'axis' | 'none';
  formatter?: string;
  backgroundColor?: string;
  borderColor?: string;
  textStyle?: unknown;
}

export interface TableColumn {
  key: string;
  title: string;
  dataIndex: string;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  filterable?: boolean;
  render?: string;
  format?: string;
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
  multiple?: boolean;
  defaultSort?: Array<{ field: string; direction: 'asc' | 'desc' }>;
}

export interface FilteringConfig {
  enabled: boolean;
  filters?: TableFilter[];
  search?: SearchConfig;
}

export interface SelectionConfig {
  enabled: boolean;
  type: 'single' | 'multiple';
  showCheckbox?: boolean;
}

export interface TableStyling {
  striped?: boolean;
  bordered?: boolean;
  hover?: boolean;
  compact?: boolean;
  rowHeight?: number;
}

export interface MetricValue {
  current: number | string;
  previous?: number | string;
  target?: number | string;
  unit?: string;
  precision?: number;
}

export interface MetricComparison {
  enabled: boolean;
  period: ComparisonPeriod;
  showPercentage?: boolean;
  showAbsolute?: boolean;
}

export interface MetricTrend {
  enabled: boolean;
  data: TrendData[];
  sparkline?: boolean;
  color?: string;
}

export interface MetricTarget {
  value: number;
  type: TargetType;
  color?: string;
  showProgress?: boolean;
}

export interface MetricFormat {
  type: FormatType;
  decimals?: number;
  thousandsSeparator?: string;
  decimalSeparator?: string;
  prefix?: string;
  suffix?: string;
  currency?: string;
}

export interface MetricStyling {
  fontSize?: string;
  fontWeight?: string;
  color?: string;
  backgroundColor?: string;
  borderColor?: string;
  borderRadius?: string;
}

export interface TextStyling {
  fontSize?: string;
  fontWeight?: string;
  color?: string;
  textAlign?: 'left' | 'center' | 'right';
  lineHeight?: string;
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
  data?: unknown;
}

export interface MapRegion {
  id: string;
  coordinates: Array<[number, number]>;
  color?: string;
  opacity?: number;
  popup?: string;
  data?: unknown;
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

export interface SearchConfig {
  enabled: boolean;
  placeholder?: string;
  fields?: string[];
}

export interface ChartTheme {
  name: string;
  colors: string[];
  backgroundColor?: string;
  textColor?: string;
  gridColor?: string;
}

export interface TrendData {
  timestamp: string;
  value: number;
}

export interface FilterOption {
  label: string;
  value: unknown;
  count?: number;
}

// Enum types
export type ChartType = 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter' | 'bubble' | 'radar' | 'gauge' | 'funnel' | 'sankey' | 'treemap' | 'heatmap' | 'candlestick';
export type AxisType = 'category' | 'value' | 'time' | 'log';
export type ScaleType = 'linear' | 'log' | 'time' | 'band' | 'point';
export type SeriesType = 'line' | 'bar' | 'area' | 'scatter' | 'candlestick';
export type LegendPosition = 'top' | 'bottom' | 'left' | 'right' | 'inside';
export type ComparisonPeriod = 'previous_period' | 'same_period_last_year' | 'custom';
export type TargetType = 'minimum' | 'maximum' | 'goal' | 'threshold';
export type FormatType = 'number' | 'percentage' | 'currency' | 'bytes' | 'duration' | 'custom';
export type FilterType = 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'numberrange' | 'boolean';