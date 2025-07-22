/**
 * Audit Types
 * 
 * Audit logging and activity tracking type definitions including
 * audit logs, activity records, and related enums.
 */

export interface AuditLog {
  id: string;
  userId?: string;
  userName?: string;
  sessionId?: string;
  action: AuditAction;
  resource: string;
  resourceId?: string;
  oldValue?: unknown;
  newValue?: unknown;
  result: AuditResult;
  reason?: string;
  ipAddress?: string;
  userAgent?: string;
  location?: string;
  timestamp: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface UserActivity {
  id: string;
  userId: string;
  sessionId?: string;
  type: ActivityType;
  action: string;
  resource?: string;
  details?: string;
  data?: Record<string, string | number | boolean | null>;
  duration?: number;
  ipAddress?: string;
  userAgent?: string;
  timestamp: string;
  metadata?: Record<string, string | number | boolean | null>;
}

// Enum and union types
export type AuditAction = 'create' | 'read' | 'update' | 'delete' | 'login' | 'logout' | 'access' | 'export' | 'import' | 'configure';
export type AuditResult = 'success' | 'failure' | 'partial' | 'denied' | 'error';
export type ActivityType = 'navigation' | 'interaction' | 'api_call' | 'data_access' | 'configuration' | 'authentication' | 'security' | 'system';