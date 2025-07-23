/**
 * Session Management Types
 * 
 * Session handling, monitoring, and management API types.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../shared';

import type { DeviceInfo } from './core-types'
import type { UserSession, SessionActivity } from './core-types'

// Session Management APIs
export interface GetSessionsRequest extends BaseApiRequest {
  userId?: string;
  active?: boolean;
  deviceType?: string;
  includeExpired?: boolean;
  context: MultiTenantContext;
}

export interface GetSessionsResponse extends BaseApiResponse<UserSession[]> {
  data: UserSession[];
  activeSessions: number;
  expiredSessions: number;
  currentSession: string;
}

export interface GetSessionDetailsRequest extends BaseApiRequest {
  sessionId: string;
  includeActivity?: boolean;
  context: MultiTenantContext;
}

export interface GetSessionDetailsResponse extends BaseApiResponse<UserSession> {
  data: UserSession;
  activities: SessionActivity[];
  securityEvents: unknown[];
  riskScore: number;
}

export interface RevokeSessionRequest extends BaseApiRequest {
  sessionId: string;
  reason?: string;
  context: MultiTenantContext;
}

export interface RevokeSessionResponse extends BaseApiResponse<unknown> {
  data: unknown;
  revoked: boolean;
  revokedAt: string;
  notificationSent: boolean;
}

export interface RevokeAllSessionsRequest extends BaseApiRequest {
  excludeCurrent?: boolean;
  reason?: string;
  context: MultiTenantContext;
}

export interface RevokeAllSessionsResponse extends BaseApiResponse<unknown> {
  data: unknown;
  sessionsRevoked: number;
  tokensRevoked: number;
  devicesUntrusted: number;
}

export interface UpdateSessionRequest extends BaseApiRequest {
  sessionId: string;
  extendExpiry?: boolean;
  updateLocation?: boolean;
  context: MultiTenantContext;
}

export interface UpdateSessionResponse extends BaseApiResponse<UserSession> {
  data: UserSession;
  updated: boolean;
  expiryExtended: boolean;
  locationUpdated: boolean;
}

export interface GetSessionActivityRequest extends BaseApiRequest {
  sessionId?: string;
  startDate?: string;
  endDate?: string;
  eventType?: string;
  context: MultiTenantContext;
}

export interface GetSessionActivityResponse extends BaseApiResponse<SessionActivity[]> {
  data: SessionActivity[];
  totalEvents: number;
  riskEvents: number;
  lastActivity: string;
}