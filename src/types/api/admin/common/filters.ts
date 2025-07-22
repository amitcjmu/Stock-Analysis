/**
 * Filter Types
 * 
 * Common filtering and query type definitions used across admin modules
 * for searching, filtering, and data retrieval.
 * 
 * Generated with CC for modular admin type organization.
 */

import { FilterOperator, ConditionOperator } from './enums';

/**
 * Base filter interface
 */
export interface BaseFilter {
  field: string;
  operator: FilterOperator;
  value: unknown;
  label?: string;
}

/**
 * Condition-based filter
 */
export interface Condition {
  type: ConditionType;
  operator: ConditionOperator;
  value: unknown;
  metadata?: Record<string, any>;
}

/**
 * Field-based condition
 */
export interface FieldCondition extends Condition {
  field: string;
}

/**
 * Condition types
 */
export type ConditionType = 
  | 'user_property' 
  | 'time_based' 
  | 'location' 
  | 'device' 
  | 'behavior' 
  | 'preference' 
  | 'custom';

/**
 * Rate limiting configuration
 */
export interface RateLimit {
  requests: number;
  period: string;
  unit: RateLimitUnit;
}

/**
 * Rate limit time units
 */
export type RateLimitUnit = 'second' | 'minute' | 'hour' | 'day';

/**
 * Retry policy configuration
 */
export interface RetryPolicy {
  max_attempts: number;
  initial_delay: number;
  max_delay: number;
  backoff_multiplier: number;
  retry_on: string[];
}

/**
 * Threshold definition
 */
export interface ThresholdDefinition {
  operator: ThresholdOperator;
  value: number;
  duration?: string;
  condition?: ThresholdCondition;
}

/**
 * Threshold operators
 */
export type ThresholdOperator = 'greater_than' | 'less_than' | 'equals' | 'not_equals' | 'between';

/**
 * Threshold condition
 */
export interface ThresholdCondition {
  field?: string;
  operator?: FilterOperator;
  value?: unknown;
}