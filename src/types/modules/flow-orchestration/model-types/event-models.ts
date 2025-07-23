/**
 * Event Models
 * 
 * Type definitions for flow events, subscriptions, and event metrics.
 */

import type { TimeRange, EventFilters } from '../base-types';

// Event Models
export interface FlowEvent {
  id: string;
  flowId: string;
  eventType: string;
  eventData: Record<string, string | number | boolean | null>;
  timestamp: string;
  source: 'system' | 'agent' | 'user' | 'external';
  sourceId?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: string;
  description: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface EventSubscription {
  id: string;
  flowId: string;
  eventTypes: string[];
  callback: string;
  filters: EventFilters;
  status: 'active' | 'paused' | 'cancelled';
  createdAt: string;
  lastTriggered?: string;
}

export interface EventMetrics {
  flowId: string;
  totalEvents: number;
  eventsByType: Record<string, number>;
  eventsBySeverity: Record<string, number>;
  eventsByCategory: Record<string, number>;
  eventRate: number;
  averageProcessingTime: number;
  timeRange: TimeRange;
}