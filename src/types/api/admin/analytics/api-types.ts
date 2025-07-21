/**
 * Analytics API Types
 * 
 * Request and response type definitions for analytics and reporting APIs.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../../shared';

import { AnalyticsTimeRange, BaseFilter } from '../common';
import {
  PlatformAnalytics,
  UsageAnalytics,
  PerformanceAnalytics,
  AdoptionAnalytics,
  AnalyticsTrend,
  AnalyticsForecast
} from './platform';
import { AdminReport, ReportCustomization } from './reports';
import { ReportType, ReportFormat, AggregationType } from './enums';

// Platform Analytics APIs
export interface GetPlatformAnalyticsRequest extends BaseApiRequest {
  timeRange?: AnalyticsTimeRange;
  metrics?: string[];
  dimensions?: string[];
  aggregation?: AggregationType;
  includeForecasts?: boolean;
  context: MultiTenantContext;
}

export interface GetPlatformAnalyticsResponse extends BaseApiResponse<PlatformAnalytics> {
  data: PlatformAnalytics;
  usage: UsageAnalytics;
  performance: PerformanceAnalytics;
  adoption: AdoptionAnalytics;
  trends: AnalyticsTrend[];
  forecasts: AnalyticsForecast[];
}

// Report Generation APIs
export interface GenerateAdminReportRequest extends BaseApiRequest {
  reportType: ReportType;
  format: ReportFormat;
  timeRange?: AnalyticsTimeRange;
  filters?: ReportFilter[];
  sections?: string[];
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateAdminReportResponse extends BaseApiResponse<AdminReport> {
  data: AdminReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Report filter extends base filter
export type ReportFilter = BaseFilter;