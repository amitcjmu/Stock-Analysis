/**
 * Audit logging utility for terminal state events and action blocking.
 * Provides audit trail for troubleshooting and compliance requirements.
 */

import { apiCall } from '../config/api';
import SecureLogger from './secureLogger';

export interface AuditLogEvent {
  action_type: string;
  resource_type: string;
  resource_id?: string;
  result: 'blocked' | 'denied' | 'closed';
  reason: string;
  details?: Record<string, unknown>;
}

/**
 * Log an audit event when terminal state causes action blocking or modal closure.
 * This provides an audit trail for troubleshooting and compliance.
 *
 * @param event - Audit event details
 * @param flowId - Flow ID (optional, for flow-related events)
 * @param clientId - Client account ID (optional, from auth context)
 * @param engagementId - Engagement ID (optional, from auth context)
 * @param authHeaders - Authentication headers (optional, should be passed from AuthContext.getAuthHeaders())
 */
export async function logTerminalStateAuditEvent(
  event: AuditLogEvent,
  flowId?: string,
  clientId?: string,
  engagementId?: string,
  authHeaders?: Record<string, string>
): Promise<void> {
  try {
    // Use provided auth headers or empty object
    // Callers should pass auth headers from AuthContext.getAuthHeaders() to follow established pattern
    const headers = authHeaders || {};

    // Prepare audit payload
    const auditPayload = {
      action_type: event.action_type,
      resource_type: event.resource_type,
      resource_id: event.resource_id || flowId || undefined,
      result: event.result,
      reason: event.reason,
      details: {
        ...event.details,
        flow_id: flowId,
        client_account_id: clientId,
        engagement_id: engagementId,
        timestamp: new Date().toISOString(),
      },
    };

    // Send audit event to backend
    await apiCall('/api/v1/audit/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(auditPayload),
    });

    SecureLogger.debug('Audit event logged successfully', {
      action_type: event.action_type,
      resource_type: event.resource_type,
    });
  } catch (error) {
    // Don't throw - audit logging should not break the application
    // Log error for debugging but continue execution
    // Include HTTP status code and error details for audit integrity tracking
    const errorDetails: Record<string, unknown> = {
      action_type: event.action_type,
      resource_type: event.resource_type,
      error: error instanceof Error ? error.message : String(error),
    };

    // Extract HTTP status code if available (from apiCall error)
    if (error && typeof error === 'object' && 'status' in error) {
      errorDetails.http_status = error.status;
      errorDetails.error_code = 'code' in error ? error.code : undefined;
    }

    SecureLogger.warn('Failed to log audit event', errorDetails);
  }
}
