/**
 * Shared Common Types
 * Reusable type definitions across components
 */

export type Status = 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused' | 'cancelled';

export type Priority = 'low' | 'medium' | 'high' | 'critical';

export type Trend = 'up' | 'down' | 'stable';

export interface BaseEntity {
  id: string | number;
  created_at?: string | Date;
  updated_at?: string | Date;
}

export interface TimestampedEntity extends BaseEntity {
  created_at: string | Date;
  updated_at: string | Date;
}

export interface NamedEntity extends BaseEntity {
  name: string;
  description?: string;
}

export interface MetricData {
  timestamp: string;
  value: number;
  label?: string;
}

export interface ChartData {
  data: MetricData[];
  color: string;
  trend: Trend;
  changePercent: number;
}

export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface PaginationOptions {
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
}

export interface SortOptions {
  field: string;
  direction: 'asc' | 'desc';
}

export interface SearchOptions {
  query: string;
  fields?: string[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface ListResponse<T> extends ApiResponse<T[]> {
  pagination?: PaginationOptions;
  total: number;
}

export interface ActionButton {
  label: string;
  onClick: () => void;
  variant?: 'default' | 'secondary' | 'outline' | 'destructive';
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
}

export interface Tab {
  id: string;
  label: string;
  count?: number;
  disabled?: boolean;
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  error: Error | string | null;
  data?: unknown;
}