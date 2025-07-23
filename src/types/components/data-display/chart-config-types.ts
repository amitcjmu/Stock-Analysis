/**
 * Chart Configuration Types
 * 
 * Type definitions for chart configuration including datasets, options,
 * tooltips, legends, axes, grids, zoom, brush, and export configurations.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../shared';
import type { ChartTooltipItem, ChartDomain, ChartScale, ChartContext, ChartEvent, ChartSize, ChartFont, ChartLabels, ChartTitle, ChartTicks, ChartBorder, ChartTimeOptions, ChartAdapters, ChartInteractionOptions, ChartType } from './chart-types'
import type { ChartDataPoint, ChartLegendItem, ChartGrid } from './chart-types'

export interface ChartProps extends BaseComponentProps {
  type: ChartType;
  data: ChartData;
  options?: ChartOptions;
  width?: number | string;
  height?: number | string;
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  loading?: boolean;
  error?: string | null;
  theme?: 'light' | 'dark' | 'auto';
  colorScheme?: string[];
  animation?: boolean;
  animationDuration?: number;
  interaction?: boolean;
  tooltip?: ChartTooltipConfig;
  legend?: ChartLegendConfig;
  axes?: ChartAxesConfig;
  grid?: ChartGridConfig;
  zoom?: ChartZoomConfig;
  brush?: ChartBrushConfig;
  export?: ChartExportConfig;
  onDataPointClick?: (data: ChartDataPoint, index: number) => void;
  onDataPointHover?: (data: ChartDataPoint, index: number) => void;
  onLegendClick?: (legendItem: ChartLegendItem) => void;
  onLegendHover?: (legendItem: ChartLegendItem) => void;
  onZoom?: (domain: ChartDomain) => void;
  onBrush?: (domain: ChartDomain) => void;
  renderTooltip?: (data: ChartTooltipItem) => ReactNode;
  renderLegend?: (legendItems: ChartLegendItem[]) => ReactNode;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
}

export interface ChartData {
  labels?: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label?: string;
  data: ChartDataPoint[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  pointRadius?: number;
  pointHoverRadius?: number;
  [key: string]: unknown;
}

export interface ChartOptions {
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  aspectRatio?: number;
  resizeDelay?: number;
  devicePixelRatio?: number;
  locale?: string;
  interaction?: ChartInteractionOptions;
  onHover?: (event: ChartEvent, elements: ChartDataPoint[]) => void;
  onClick?: (event: ChartEvent, elements: ChartDataPoint[]) => void;
  onResize?: (chart: ChartContext, size: ChartSize) => void;
  plugins?: Record<string, unknown>;
  scales?: Record<string, ChartScale>;
  elements?: Record<string, unknown>;
  layout?: Record<string, unknown>;
  animation?: Record<string, unknown>;
  animations?: Record<string, unknown>;
  transitions?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ChartTooltipConfig {
  enabled?: boolean;
  position?: string;
  filter?: (tooltipItem: ChartTooltipItem) => boolean;
  itemSort?: (a: ChartTooltipItem, b: ChartTooltipItem) => number;
  external?: (context: ChartContext) => void;
  callbacks?: Record<string, unknown>;
  displayColors?: boolean;
  backgroundColor?: string;
  titleColor?: string;
  bodyColor?: string;
  borderColor?: string;
  borderWidth?: number;
  cornerRadius?: number;
  caretPadding?: number;
  caretSize?: number;
  titleFont?: ChartFont;
  bodyFont?: ChartFont;
  footerFont?: ChartFont;
  titleAlign?: string;
  bodyAlign?: string;
  footerAlign?: string;
  titleSpacing?: number;
  titleMarginBottom?: number;
  bodySpacing?: number;
  footerSpacing?: number;
  footerMarginTop?: number;
  padding?: number;
  xPadding?: number;
  yPadding?: number;
  multiKeyBackground?: string;
  usePointStyle?: boolean;
  boxWidth?: number;
  boxHeight?: number;
  boxPadding?: number;
}

export interface ChartLegendConfig {
  display?: boolean;
  position?: 'top' | 'left' | 'bottom' | 'right' | 'chartArea';
  align?: 'start' | 'center' | 'end';
  maxHeight?: number;
  maxWidth?: number;
  fullSize?: boolean;
  onClick?: (event: ChartEvent, legendItem: ChartLegendItem, legend: ChartLegendConfig) => void;
  onHover?: (event: ChartEvent, legendItem: ChartLegendItem, legend: ChartLegendConfig) => void;
  onLeave?: (event: ChartEvent, legendItem: ChartLegendItem, legend: ChartLegendConfig) => void;
  reverse?: boolean;
  labels?: ChartLabels;
  rtl?: boolean;
  textDirection?: string;
  title?: ChartTitle;
}

export interface ChartAxesConfig {
  x?: ChartAxisConfig;
  y?: ChartAxisConfig;
  [key: string]: ChartAxisConfig | undefined;
}

export interface ChartAxisConfig {
  type?: string;
  position?: string;
  display?: boolean | string;
  title?: ChartTitle;
  min?: number;
  max?: number;
  suggestedMin?: number;
  suggestedMax?: number;
  beginAtZero?: boolean;
  bounds?: string;
  clip?: boolean;
  grace?: number | string;
  stack?: string;
  stackWeight?: number;
  axis?: string;
  offset?: boolean;
  reverse?: boolean;
  ticks?: ChartTicks;
  grid?: ChartGrid;
  border?: ChartBorder;
  time?: ChartTimeOptions;
  adapters?: ChartAdapters;
  afterBuildTicks?: (scale: ChartScale) => void;
  beforeCalculateLabelRotation?: (scale: ChartScale) => void;
  afterCalculateLabelRotation?: (scale: ChartScale) => void;
  beforeFit?: (scale: ChartScale) => void;
  afterFit?: (scale: ChartScale) => void;
  afterTickToLabelConversion?: (scale: ChartScale) => void;
  beforeSetDimensions?: (scale: ChartScale) => void;
  afterSetDimensions?: (scale: ChartScale) => void;
  beforeDataLimits?: (scale: ChartScale) => void;
  afterDataLimits?: (scale: ChartScale) => void;
  beforeTickToLabelConversion?: (scale: ChartScale) => void;
  beforeUpdate?: (scale: ChartScale) => void;
  afterUpdate?: (scale: ChartScale) => void;
}

export interface ChartGridConfig {
  display?: boolean;
  circular?: boolean;
  color?: string | string[];
  lineWidth?: number | number[];
  drawBorder?: boolean;
  drawOnChartArea?: boolean;
  drawTicks?: boolean;
  tickBorderDash?: number[];
  tickBorderDashOffset?: number;
  tickColor?: string | string[];
  tickLength?: number;
  tickWidth?: number;
  offset?: boolean;
  z?: number;
}

export interface ChartZoomConfig {
  enabled?: boolean;
  mode?: 'x' | 'y' | 'xy';
  rangeMin?: ChartDomain;
  rangeMax?: ChartDomain;
  speed?: number;
  threshold?: number;
  sensitivity?: number;
  onZoom?: (context: ChartContext) => void;
  onZoomComplete?: (context: ChartContext) => void;
  onZoomRejected?: (context: ChartContext) => void;
  onZoomStart?: (context: ChartContext) => void;
}

export interface ChartBrushConfig {
  enabled?: boolean;
  mode?: 'x' | 'y' | 'xy';
  onBrush?: (domain: ChartDomain) => void;
  onBrushEnd?: (domain: ChartDomain) => void;
  brushStyle?: React.CSSProperties;
  handleStyle?: React.CSSProperties;
}

export interface ChartExportConfig {
  enabled?: boolean;
  formats?: ExportFormat[];
  onExport?: (format: ExportFormat, dataUrl: string) => void;
  filename?: string;
  backgroundColor?: string;
  width?: number;
  height?: number;
  pixelRatio?: number;
}

// Shared utility types
export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description?: string;
}