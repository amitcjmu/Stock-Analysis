/**
 * Dashboard Types
 * 
 * Core dashboard component type definitions including props and layout.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../../shared';
import type { DashboardLayout, DashboardFilter, TimeRange, ExportFormat } from './widget-types'
import type { DashboardWidget, DashboardTemplate } from './widget-types'

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
  onFiltersChange?: (filters: Record<string, string | number | boolean | string[] | undefined>) => void;
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