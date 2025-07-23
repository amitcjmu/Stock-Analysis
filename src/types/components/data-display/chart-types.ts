/**
 * Chart Component Types
 * 
 * Type definitions for chart components including data points, legends,
 * tooltips, scales, and chart configuration options.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps, InteractiveComponentProps } from '../shared';

// Basic chart data types
export interface ChartDataPoint {
  x?: number | string;
  y?: number | string;
  [key: string]: unknown;
}

export interface ChartLegendItem {
  text: string;
  fillStyle?: string;
  strokeStyle?: string;
  lineWidth?: number;
  hidden?: boolean;
  [key: string]: unknown;
}

export interface ChartTooltipItem {
  label: string;
  value: string | number;
  color?: string;
  [key: string]: unknown;
}

export interface ChartDomain {
  min?: number;
  max?: number;
  [key: string]: unknown;
}

export interface ChartScale {
  id: string;
  type: string;
  options: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ChartContext {
  chart: {
    canvas: HTMLCanvasElement;
    width: number;
    height: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface ChartEvent {
  native: Event;
  x: number;
  y: number;
  [key: string]: unknown;
}

export interface ChartSize {
  width: number;
  height: number;
  [key: string]: unknown;
}

export interface ChartFont {
  family: string;
  size: number;
  style: string;
  weight: string;
  [key: string]: unknown;
}

export interface ChartLabels {
  boxWidth: number;
  color: string;
  font: ChartFont;
  padding: number;
  [key: string]: unknown;
}

export interface ChartTitle {
  display: boolean;
  text: string;
  font: ChartFont;
  [key: string]: unknown;
}

export interface ChartTicks {
  display: boolean;
  color: string;
  font: ChartFont;
  [key: string]: unknown;
}

export interface ChartGrid {
  display: boolean;
  color: string;
  lineWidth: number;
  [key: string]: unknown;
}

export interface ChartBorder {
  display: boolean;
  color: string;
  width: number;
  [key: string]: unknown;
}

export interface ChartTimeOptions {
  unit: 'millisecond' | 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';
  displayFormats: Record<string, string>;
  [key: string]: unknown;
}

export interface ChartAdapters {
  date: {
    locale: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface ChartInteractionOptions {
  intersect?: boolean;
  mode?: 'point' | 'nearest' | 'index' | 'dataset' | 'x' | 'y';
  axis?: 'x' | 'y' | 'xy';
  [key: string]: unknown;
}

// Chart type definition
export type ChartType = 'line' | 'bar' | 'pie' | 'doughnut' | 'scatter' | 'bubble' | 'radar' | 'polarArea' | 'area';