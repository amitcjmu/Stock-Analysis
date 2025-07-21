/**
 * Time Range Types
 * 
 * Common time-related type definitions used across admin modules
 * for filtering, analytics, and reporting.
 * 
 * Generated with CC for modular admin type organization.
 */

/**
 * Basic time range
 */
export interface TimeRange {
  start: string;
  end: string;
}

/**
 * Extended time range with timezone
 */
export interface TimeRangeWithTimezone extends TimeRange {
  timezone?: string;
}

/**
 * Analytics time range with granularity
 */
export interface AnalyticsTimeRange extends TimeRangeWithTimezone {
  granularity?: TimePeriod;
}

/**
 * Analytics period information
 */
export interface AnalyticsPeriod {
  start: string;
  end: string;
  granularity: TimePeriod;
  total_periods: number;
  current_period: number;
  timezone: string;
}

/**
 * Time period units
 */
export type TimePeriod = 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';

/**
 * Schedule frequency types
 */
export type ScheduleFrequency = 'minutely' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly';

/**
 * Delay time units
 */
export type DelayUnit = 'minutes' | 'hours' | 'days' | 'weeks' | 'months';

/**
 * Recurring schedule configuration
 */
export interface RecurringSchedule {
  frequency: ScheduleFrequency;
  interval: number;
  days_of_week?: number[];
  days_of_month?: number[];
  months?: number[];
  end_date?: string;
  max_occurrences?: number;
}

/**
 * Schedule delay configuration
 */
export interface ScheduleDelay {
  amount: number;
  unit: DelayUnit;
  condition?: any;
}

/**
 * Quiet hours configuration
 */
export interface QuietHours {
  enabled: boolean;
  start_time: string;
  end_time: string;
  timezone: string;
  days: number[];
}