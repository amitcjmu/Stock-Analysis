/**
 * Report Generation Types
 *
 * Types for report creation, customization, and delivery.
 *
 * Generated with CC for modular admin type organization.
 */

import type { ReportMetadata, DataSource, ReportPermission, AnalyticsPeriod } from '../common';
import type { ReportType, ReportFormat, SectionType, DeliveryMethod } from './enums';

// Admin report structure
export interface AdminReport {
  id: string;
  type: ReportType;
  title: string;
  description?: string;
  generated_at: string;
  generated_by: string;
  period: AnalyticsPeriod;
  format: ReportFormat;
  size: number;
  sections: ReportSection[];
  metadata: ReportMetadata;
  customizations: ReportCustomization;
  delivery: ReportDelivery;
}

// Report section
export interface ReportSection {
  id: string;
  title: string;
  type: SectionType;
  content: SectionContent;
  order: number;
  visible: boolean;
  customizations?: SectionCustomization;
}

// Report customization options
export interface ReportCustomization {
  title?: string;
  subtitle?: string;
  logo?: string;
  branding?: BrandingOptions;
  layout?: LayoutOptions;
  styling?: StylingOptions;
  sections?: SectionCustomization[];
  charts?: ChartCustomization[];
  tables?: TableCustomization[];
}

// Report delivery configuration
export interface ReportDelivery {
  method: DeliveryMethod;
  recipients: ReportRecipient[];
  schedule?: DeliverySchedule;
  notifications: DeliveryNotification[];
  history: DeliveryHistory[];
}

// Section content wrapper
export interface SectionContent {
  type: string;
  data: unknown;
  configuration: Record<string, string | number | boolean | null>;
}

// Section customization
export interface SectionCustomization {
  id?: string;
  title?: string;
  visible?: boolean;
  styling?: Record<string, string | number | boolean | null>;
  layout?: Record<string, string | number | boolean | null>;
  filters?: Record<string, string | number | boolean | null>;
}

// Branding options
export interface BrandingOptions {
  logo_url?: string;
  company_name?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  font_family?: string;
  header_template?: string;
  footer_template?: string;
}

// Layout options
export interface LayoutOptions {
  orientation: PageOrientation;
  page_size: PageSize;
  margins: PageMargins;
  columns: number;
  spacing: number;
  section_break: boolean;
}

// Styling options
export interface StylingOptions {
  theme: ReportTheme;
  color_scheme: ColorScheme;
  fonts: FontSettings;
  borders: BorderSettings;
  shadows: boolean;
  animations: boolean;
}

// Chart customization
export interface ChartCustomization {
  id?: string;
  type?: ChartType;
  title?: string;
  styling?: ChartStyling;
  data_settings?: DataSettings;
  interactions?: ChartInteractions;
}

// Table customization
export interface TableCustomization {
  id?: string;
  columns?: ColumnCustomization[];
  sorting?: SortingOptions;
  filtering?: FilteringOptions;
  pagination?: PaginationOptions;
  styling?: TableStyling;
}

// Report recipient
export interface ReportRecipient {
  email: string;
  name: string;
  type: RecipientType;
  format_preference?: ReportFormat;
  language?: string;
}

// Delivery schedule
export interface DeliverySchedule {
  frequency: ScheduleFrequency;
  day_of_week?: number;
  day_of_month?: number;
  time: string;
  timezone: string;
  active: boolean;
  end_date?: string;
}

// Delivery notification
export interface DeliveryNotification {
  enabled: boolean;
  channels: NotificationChannel[];
  recipients: string[];
  include_summary: boolean;
  include_link: boolean;
}

// Delivery history entry
export interface DeliveryHistory {
  timestamp: string;
  recipient: string;
  status: DeliveryStatus;
  method: DeliveryMethod;
  size: number;
  error?: string;
}

// Supporting interfaces
export interface PageMargins {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface FontSettings {
  heading_font?: string;
  body_font?: string;
  monospace_font?: string;
  sizes: FontSizes;
}

export interface FontSizes {
  h1?: number;
  h2?: number;
  h3?: number;
  body?: number;
  small?: number;
}

export interface BorderSettings {
  style: BorderStyle;
  width: number;
  color: string;
  radius?: number;
}

export interface ChartStyling {
  colors?: string[];
  background?: string;
  grid?: GridSettings;
  legend?: LegendSettings;
  axis?: AxisSettings;
}

export interface GridSettings {
  show: boolean;
  color: string;
  style: LineStyle;
}

export interface LegendSettings {
  show: boolean;
  position: LegendPosition;
  alignment: Alignment;
}

export interface AxisSettings {
  x?: AxisConfig;
  y?: AxisConfig;
}

export interface AxisConfig {
  show: boolean;
  label?: string;
  format?: string;
  min?: number;
  max?: number;
}

export interface DataSettings {
  aggregation?: string;
  grouping?: string[];
  filtering?: Record<string, string | number | boolean | null>;
  sorting?: SortConfig;
}

export interface ChartInteractions {
  hover: boolean;
  click: boolean;
  zoom: boolean;
  pan: boolean;
  export: boolean;
}

export interface ColumnCustomization {
  field: string;
  title?: string;
  width?: number;
  align?: Alignment;
  format?: string;
  sortable?: boolean;
  filterable?: boolean;
}

export interface SortingOptions {
  enabled: boolean;
  default_field?: string;
  default_direction?: SortDirection;
  multi_sort: boolean;
}

export interface FilteringOptions {
  enabled: boolean;
  quick_filter: boolean;
  advanced_filter: boolean;
  default_filters?: Record<string, string | number | boolean | null>;
}

export interface PaginationOptions {
  enabled: boolean;
  page_size: number;
  page_sizes: number[];
  show_total: boolean;
}

export interface TableStyling {
  striped: boolean;
  bordered: boolean;
  hover: boolean;
  compact: boolean;
  header_style?: HeaderStyle;
}

export interface SortConfig {
  field: string;
  direction: SortDirection;
}

export interface HeaderStyle {
  background: string;
  color: string;
  font_weight: string;
  text_transform?: string;
}

// Import types
type ScheduleFrequency = import('../common').ScheduleFrequency;

// Enums
export type PageOrientation = 'portrait' | 'landscape';
export type PageSize = 'a4' | 'letter' | 'legal' | 'tabloid' | 'custom';
export type ReportTheme = 'light' | 'dark' | 'professional' | 'colorful' | 'minimal';
export type ColorScheme = 'default' | 'monochrome' | 'blue' | 'green' | 'red' | 'custom';
export type ChartType = 'line' | 'bar' | 'pie' | 'donut' | 'area' | 'scatter' | 'heatmap' | 'gauge';
export type RecipientType = 'internal' | 'client' | 'stakeholder' | 'automated';
export type NotificationChannel = 'email' | 'sms' | 'in_app' | 'webhook';
export type DeliveryStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';
export type BorderStyle = 'solid' | 'dashed' | 'dotted' | 'none';
export type LineStyle = 'solid' | 'dashed' | 'dotted';
export type LegendPosition = 'top' | 'right' | 'bottom' | 'left';
export type Alignment = 'left' | 'center' | 'right';
export type SortDirection = 'asc' | 'desc';
