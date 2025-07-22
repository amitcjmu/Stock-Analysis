/**
 * Real-time API Types
 * 
 * Types for WebSocket connections, subscriptions, and real-time messaging.
 */

import { BaseApiRequest, BaseApiResponse } from './base-types';
import { MultiTenantContext } from './tenant-types';
import { FilterParameter } from './query-types';

// Real-time updates
export interface WebSocketMessage<T = unknown> {
  id: string;
  type: string;
  event: string;
  data: T;
  timestamp: string;
  context: MultiTenantContext;
  correlation?: string;
  retry?: number;
}

export interface SubscriptionRequest extends BaseApiRequest {
  events: string[];
  filters?: FilterParameter[];
  context: MultiTenantContext;
  heartbeat?: number;
  compression?: boolean;
}

export interface SubscriptionResponse extends BaseApiResponse<SubscriptionInfo> {
  data: SubscriptionInfo;
  subscriptionId: string;
  websocketUrl: string;
  events: string[];
  expiresAt: string;
}

export interface SubscriptionInfo {
  id: string;
  events: string[];
  filters: FilterParameter[];
  status: 'active' | 'paused' | 'expired' | 'error';
  createdAt: string;
  expiresAt: string;
  lastHeartbeat?: string;
  messageCount: number;
  errorCount: number;
}