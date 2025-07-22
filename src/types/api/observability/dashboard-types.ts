/**
 * Dashboard Management Types
 * 
 * Type definitions for creating, managing, and customizing dashboards
 * for observability data visualization and monitoring interfaces.
 */

import {
  BaseApiResponse,
  CreateRequest,
  CreateResponse,
  GetRequest,
  GetResponse,
  UpdateRequest,
  UpdateResponse
} from '../shared';

// Dashboard Management
export interface CreateDashboardRequest extends CreateRequest<DashboardData> {
  flowId: string;
  data: DashboardData;
  dashboardType: 'operational' | 'executive' | 'technical' | 'business' | 'custom';
  widgets: WidgetConfiguration[];
  layout: DashboardLayout;
  sharing: SharingConfiguration;
  refresh: RefreshConfiguration;
}

export interface CreateDashboardResponse extends CreateResponse<Dashboard> {
  data: Dashboard;
  dashboardId: string;
  validationResults: DashboardValidation[];
  previewUrl: string;
  estimatedLoadTime: number;
}

export interface GetDashboardRequest extends GetRequest {
  dashboardId: string;
  includeData?: boolean;
  includeMetadata?: boolean;
  timeRange?: {
    start: string;
    end: string;
  };
  refresh?: boolean;
}

export interface GetDashboardResponse extends GetResponse<Dashboard> {
  data: Dashboard;
  widgetData: WidgetData[];
  dashboardMetadata: DashboardMetadata;
  lastRefreshed: string;
}

export interface UpdateDashboardRequest extends UpdateRequest<Partial<DashboardData>> {
  dashboardId: string;
  data: Partial<DashboardData>;
  updateType: 'layout' | 'widgets' | 'settings' | 'sharing';
  validateChanges?: boolean;
}

export interface UpdateDashboardResponse extends UpdateResponse<Dashboard> {
  data: Dashboard;
  validationResults: DashboardValidation[];
  changeImpact: DashboardChangeImpact;
}

// Supporting Types
export interface DashboardData {
  name: string;
  description?: string;
  category: string;
  tags: string[];
  variables: DashboardVariable[];
  timeRange: TimeRangeConfig;
  refreshInterval: string;
  timezone: string;
  theme: 'light' | 'dark' | 'auto';
  metadata: Record<string, any>;
}

export interface WidgetConfiguration {
  id: string;
  type: WidgetType;
  title: string;
  description?: string;
  position: WidgetPosition;
  size: WidgetSize;
  dataSource: DataSourceConfig;
  visualization: VisualizationConfig;
  interactions: InteractionConfig;
  styling: StylingConfig;
  options: WidgetOptions;
}

export interface DashboardLayout {
  type: 'grid' | 'flex' | 'absolute' | 'masonry';
  columns: number;
  rows?: number;
  gap: number;
  padding: number;
  responsive: boolean;
  breakpoints: Breakpoint[];
}

export interface SharingConfiguration {
  visibility: 'private' | 'internal' | 'public' | 'custom';
  permissions: Permission[];
  publicUrl?: string;
  embedEnabled: boolean;
  embedOptions: EmbedOptions;
  expiration?: string;
}

export interface RefreshConfiguration {
  enabled: boolean;
  interval: string;
  autoRefresh: boolean;
  onDataChange: boolean;
  backgroundRefresh: boolean;
  refreshOnLoad: boolean;
}

export interface Dashboard {
  id: string;
  dashboardId: string;
  name: string;
  description?: string;
  type: 'operational' | 'executive' | 'technical' | 'business' | 'custom';
  category: string;
  tags: string[];
  widgets: Widget[];
  layout: DashboardLayout;
  sharing: SharingConfiguration;
  refresh: RefreshConfiguration;
  variables: DashboardVariable[];
  timeRange: TimeRangeConfig;
  timezone: string;
  theme: 'light' | 'dark' | 'auto';
  status: 'draft' | 'published' | 'archived' | 'deprecated';
  version: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  lastModifiedBy: string;
  viewCount: number;
  metadata: Record<string, any>;
}

export interface DashboardValidation {
  rule: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  widgetId?: string;
  field?: string;
  suggestion?: string;
}

export interface WidgetData {
  widgetId: string;
  data: unknown;
  metadata: WidgetMetadata;
  status: 'loading' | 'success' | 'error' | 'empty';
  error?: string;
  lastUpdated: string;
  executionTime: number;
}

export interface DashboardMetadata {
  totalWidgets: number;
  loadTime: number;
  dataVolume: number;
  lastRefresh: string;
  refreshStatus: 'success' | 'partial' | 'failed';
  errors: DashboardError[];
  performance: DashboardPerformanceMetrics;
}

export interface DashboardChangeImpact {
  widgetsAffected: string[];
  layoutChanged: boolean;
  dataSourcesChanged: string[];
  performanceImpact: 'none' | 'minimal' | 'moderate' | 'significant';
  migrationRequired: boolean;
  estimatedDowntime: string;
}

// Widget Types
export type WidgetType = 
  | 'chart' | 'table' | 'stat' | 'gauge' | 'heatmap' | 'histogram'
  | 'timeline' | 'worldmap' | 'piechart' | 'bargraph' | 'linegraph'
  | 'scatterplot' | 'treemap' | 'sankey' | 'text' | 'image' | 'iframe'
  | 'log' | 'metric' | 'alert' | 'status' | 'custom';

export interface WidgetPosition {
  x: number;
  y: number;
  z?: number;
}

export interface WidgetSize {
  width: number;
  height: number;
  minWidth?: number;
  minHeight?: number;
  maxWidth?: number;
  maxHeight?: number;
}

export interface DataSourceConfig {
  type: 'prometheus' | 'influxdb' | 'elasticsearch' | 'mysql' | 'postgres' | 'api' | 'static';
  connection: ConnectionConfig;
  query: QueryConfig;
  transformation: TransformationConfig;
  caching: CachingConfig;
}

export interface VisualizationConfig {
  chartType?: string;
  axes: AxisConfig[];
  series: SeriesConfig[];
  legend: LegendConfig;
  colors: ColorConfig;
  thresholds: ThresholdConfig[];
  formatting: FormattingConfig;
}

export interface InteractionConfig {
  clickThrough: boolean;
  drilling: DrillingConfig;
  filtering: FilteringConfig;
  crossFiltering: boolean;
  tooltips: TooltipConfig;
  zoom: ZoomConfig;
}

export interface StylingConfig {
  background: string;
  border: BorderConfig;
  padding: number;
  margin: number;
  borderRadius: number;
  shadow: ShadowConfig;
  font: FontConfig;
}

export interface WidgetOptions {
  showTitle: boolean;
  showDescription: boolean;
  showLegend: boolean;
  showTooltips: boolean;
  showGrid: boolean;
  showAxes: boolean;
  showDataLabels: boolean;
  allowFullscreen: boolean;
  allowExport: boolean;
  customOptions: Record<string, any>;
}

export interface Widget {
  id: string;
  widgetId: string;
  type: WidgetType;
  title: string;
  description?: string;
  position: WidgetPosition;
  size: WidgetSize;
  dataSource: DataSourceConfig;
  visualization: VisualizationConfig;
  interactions: InteractionConfig;
  styling: StylingConfig;
  options: WidgetOptions;
  status: 'active' | 'inactive' | 'error';
  version: string;
  createdAt: string;
  updatedAt: string;
}

export interface WidgetMetadata {
  dataPoints: number;
  series: number;
  timeRange: string;
  lastQuery: string;
  queryTime: number;
  dataSize: number;
  warnings: string[];
}

// Additional supporting interfaces
export interface DashboardVariable {
  name: string;
  type: 'text' | 'select' | 'multiselect' | 'date' | 'timerange' | 'number';
  value: unknown;
  options?: VariableOption[];
  query?: string;
  refresh: 'never' | 'onload' | 'onchange';
  hide: boolean;
}

export interface TimeRangeConfig {
  from: string;
  to: string;
  timezone?: string;
  quickRanges: QuickRange[];
  customAllowed: boolean;
}

export interface Breakpoint {
  name: string;
  width: number;
  columns: number;
  gap: number;
}

export interface Permission {
  user?: string;
  role?: string;
  team?: string;
  level: 'view' | 'edit' | 'admin';
  restrictions?: string[];
}

export interface EmbedOptions {
  showControls: boolean;
  showTimeRange: boolean;
  showVariables: boolean;
  showTitle: boolean;
  autoFit: boolean;
  theme?: 'light' | 'dark';
}

export interface ConnectionConfig {
  url: string;
  timeout: number;
  authentication?: AuthConfig;
  headers?: Record<string, string>;
  proxy?: ProxyConfig;
}

export interface QueryConfig {
  query: string;
  parameters: Record<string, any>;
  timeout: number;
  retries: number;
  interval: string;
}

export interface TransformationConfig {
  operations: TransformationOperation[];
  aggregation?: AggregationOperation;
  filtering?: FilterOperation[];
  sorting?: SortOperation;
}

export interface CachingConfig {
  enabled: boolean;
  ttl: number;
  invalidateOn: string[];
  strategy: 'memory' | 'disk' | 'redis';
}

export interface AxisConfig {
  name: string;
  type: 'linear' | 'logarithmic' | 'datetime' | 'category';
  position: 'left' | 'right' | 'top' | 'bottom';
  min?: number;
  max?: number;
  unit?: string;
  format?: string;
  gridLines: boolean;
  tickInterval?: number;
}

export interface SeriesConfig {
  name: string;
  type: 'line' | 'bar' | 'area' | 'scatter' | 'point';
  yAxis: string;
  color?: string;
  lineWidth?: number;
  fillOpacity?: number;
  markers: boolean;
  stacking?: 'none' | 'normal' | 'percent';
}

export interface LegendConfig {
  show: boolean;
  position: 'top' | 'bottom' | 'left' | 'right';
  alignment: 'start' | 'center' | 'end';
  layout: 'horizontal' | 'vertical';
  maxItems?: number;
  showValues: boolean;
}

export interface ColorConfig {
  mode: 'auto' | 'palette' | 'gradient' | 'custom';
  palette?: string[];
  gradient?: GradientConfig;
  overrides: ColorOverride[];
}

export interface ThresholdConfig {
  value: number;
  color: string;
  label?: string;
  fill?: boolean;
  line?: boolean;
}

export interface FormattingConfig {
  unit: string;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  nullValue?: string;
  dateFormat?: string;
  locale?: string;
}

export interface DrillingConfig {
  enabled: boolean;
  targetDashboard?: string;
  targetView?: string;
  parameters: Record<string, string>;
  newTab: boolean;
}

export interface FilteringConfig {
  enabled: boolean;
  fields: string[];
  operators: string[];
  multiValue: boolean;
  caseSensitive: boolean;
}

export interface TooltipConfig {
  enabled: boolean;
  mode: 'single' | 'multi' | 'x' | 'y' | 'closest';
  sort: 'none' | 'asc' | 'desc';
  shared: boolean;
  valueFormat?: string;
}

export interface ZoomConfig {
  enabled: boolean;
  wheel: boolean;
  pinch: boolean;
  drag: boolean;
  resetButton: boolean;
}

export interface BorderConfig {
  width: number;
  style: 'solid' | 'dashed' | 'dotted';
  color: string;
}

export interface ShadowConfig {
  enabled: boolean;
  x: number;
  y: number;
  blur: number;
  color: string;
}

export interface FontConfig {
  family: string;
  size: number;
  weight: 'normal' | 'bold' | 'light';
  style: 'normal' | 'italic';
  color: string;
}

export interface DashboardError {
  widgetId?: string;
  type: 'data' | 'rendering' | 'configuration' | 'permission';
  message: string;
  timestamp: string;
  resolved: boolean;
}

export interface DashboardPerformanceMetrics {
  loadTime: number;
  renderTime: number;
  queryTime: number;
  dataTransferSize: number;
  memoryUsage: number;
}

export interface VariableOption {
  text: string;
  value: unknown;
  selected: boolean;
}

export interface QuickRange {
  label: string;
  from: string;
  to: string;
}

export interface AuthConfig {
  type: 'basic' | 'bearer' | 'apikey' | 'oauth';
  credentials: Record<string, string>;
}

export interface ProxyConfig {
  enabled: boolean;
  url: string;
  authentication?: AuthConfig;
}

export interface TransformationOperation {
  type: 'filter' | 'map' | 'reduce' | 'groupby' | 'join' | 'pivot' | 'sort';
  parameters: Record<string, any>;
}

export interface AggregationOperation {
  function: 'sum' | 'avg' | 'min' | 'max' | 'count' | 'first' | 'last';
  groupBy: string[];
  having?: Record<string, any>;
}

export interface FilterOperation {
  field: string;
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin' | 'contains' | 'regex';
  value: unknown;
}

export interface SortOperation {
  field: string;
  direction: 'asc' | 'desc';
}

export interface GradientConfig {
  stops: GradientStop[];
  direction: 'horizontal' | 'vertical' | 'radial';
}

export interface ColorOverride {
  matcher: string;
  color: string;
  condition?: string;
}

export interface GradientStop {
  offset: number;
  color: string;
}