/**
 * Report Generation Types
 * 
 * Type definitions for generating observability reports, customizing report formats,
 * and managing report templates and branding configurations.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../../shared';
import { TimeRange } from '../core-types';

// Report Generation Requests and Responses
export interface GenerateObservabilityReportRequest extends BaseApiRequest {
  flowId: string;
  reportType: 'health' | 'performance' | 'availability' | 'capacity' | 'incident';
  format: 'pdf' | 'html' | 'docx' | 'json';
  timeRange?: {
    start: string;
    end: string;
  };
  sections?: string[];
  includeCharts?: boolean;
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateObservabilityReportResponse extends BaseApiResponse<ObservabilityReport> {
  data: ObservabilityReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Core Report Types
export interface ObservabilityReport {
  id: string;
  reportId: string;
  type: 'health' | 'performance' | 'availability' | 'capacity' | 'incident';
  format: 'pdf' | 'html' | 'docx' | 'json';
  title: string;
  summary: ReportSummary;
  sections: ReportSection[];
  metadata: ReportMetadata;
  generatedAt: string;
  generatedBy: string;
}

export interface ReportCustomization {
  template: string;
  theme: 'light' | 'dark' | 'corporate' | 'minimal';
  branding: BrandingConfig;
  sections: SectionCustomization[];
  charts: ChartCustomization[];
  formatting: FormattingConfig;
}

// Report Content Types
export interface ReportSummary {
  executiveSummary: string;
  keyFindings: string[];
  recommendations: string[];
  metrics: ReportMetric[];
  trends: string[];
}

export interface ReportSection {
  id: string;
  title: string;
  content: string;
  charts: ReportChart[];
  tables: ReportTable[];
  insights: string[];
}

export interface ReportMetadata {
  version: string;
  template: string;
  dataSource: string;
  timeRange: TimeRange;
  generationTime: number;
  accuracy: number;
  limitations: string[];
}

export interface ReportMetric {
  name: string;
  value: number;
  unit: string;
  change: number;
  status: 'good' | 'warning' | 'critical';
}

export interface ReportChart {
  id: string;
  type: string;
  title: string;
  data: any;
  config: ChartConfig;
}

export interface ReportTable {
  id: string;
  title: string;
  headers: string[];
  rows: any[][];
  formatting?: TableFormatting;
}

// Customization Types
export interface BrandingConfig {
  logo: string;
  colors: ColorScheme;
  fonts: FontScheme;
  header: string;
  footer: string;
}

export interface SectionCustomization {
  sectionId: string;
  title?: string;
  include: boolean;
  order: number;
  customContent?: string;
}

export interface ChartCustomization {
  chartId: string;
  type: string;
  title?: string;
  colors?: string[];
  size?: ChartSize;
}

export interface FormattingConfig {
  dateFormat: string;
  numberFormat: string;
  currency: string;
  timezone: string;
  locale: string;
}

// Styling Types
export interface ColorScheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
}

export interface FontScheme {
  heading: string;
  body: string;
  monospace: string;
  sizes: FontSizes;
}

export interface FontSizes {
  small: number;
  medium: number;
  large: number;
  xlarge: number;
}

export interface ChartSize {
  width: number;
  height: number;
}

export interface ChartConfig {
  theme: string;
  responsive: boolean;
  legend: boolean;
  grid: boolean;
  animation: boolean;
}

export interface TableFormatting {
  striped: boolean;
  bordered: boolean;
  hover: boolean;
  compact: boolean;
  sortable: boolean;
}