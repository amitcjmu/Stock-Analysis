/**
 * Audit API Types
 * 
 * Request and response type definitions for audit logging and security APIs.
 * 
 * Generated with CC for modular admin type organization.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  ListRequest,
  ListResponse,
  CreateRequest,
  CreateResponse
} from '../../shared';

import type { TimeRange } from '../common';
import type { AuditLogData, ActionSummary, UserActivitySummary } from './audit-log'
import { AuditLog } from './audit-log'
import type { SecurityEvent, IncidentSummary } from './security-events'
import { SecurityRecommendation } from './security-events'
import type { SecurityEventType, ThreatLevel } from './enums'
import { AuditSeverity, SecuritySeverity } from './enums'

// Audit Log APIs
export interface GetAuditLogsRequest extends ListRequest {
  userId?: string;
  action?: string;
  resource?: string;
  clientAccountId?: string;
  engagementId?: string;
  timeRange?: TimeRange;
  severity?: AuditSeverity[];
  includeDetails?: boolean;
}

export interface GetAuditLogsResponse extends ListResponse<AuditLog> {
  data: AuditLog[];
  actionSummary: ActionSummary[];
  userActivity: UserActivitySummary[];
  securityEvents: SecurityEvent[];
}

export interface CreateAuditLogRequest extends CreateRequest<AuditLogData> {
  data: AuditLogData;
  severity: AuditSeverity;
  automated?: boolean;
  alertRequired?: boolean;
}

export interface CreateAuditLogResponse extends CreateResponse<AuditLog> {
  data: AuditLog;
  logId: string;
  alertTriggered: boolean;
  notificationsSent: string[];
}

// Security Event APIs
export interface GetSecurityEventsRequest extends ListRequest {
  eventTypes?: SecurityEventType[];
  severity?: SecuritySeverity[];
  resolved?: boolean;
  timeRange?: TimeRange;
  includeContext?: boolean;
}

export interface GetSecurityEventsResponse extends ListResponse<SecurityEvent> {
  data: SecurityEvent[];
  threatLevel: ThreatLevel;
  incidentSummary: IncidentSummary;
  recommendations: SecurityRecommendation[];
}