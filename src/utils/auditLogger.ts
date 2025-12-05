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
 */
export async function logTerminalStateAuditEvent(
  event: AuditLogEvent,
  flowId?: string,
  clientId?: string,
  engagementId?: string
): Promise<void> {
  try {
    // Get auth context if available
    let authHeaders: Record<string, string> = {};
    try {
      // Try to get auth headers from localStorage or context
      const authToken = localStorage.getItem('auth_token');
      if (authToken) {
        authHeaders = {
          'Authorization': `Bearer ${authToken}`,
        };
      }
    } catch (e) {
      // Auth context not available, continue without it
      SecureLogger.debug('Auth context not available for audit logging', { error: e });
    }

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
        ...authHeaders,
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
    SecureLogger.warn('Failed to log audit event', {
      error: error instanceof Error ? error.message : String(error),
      action_type: event.action_type,
      resource_type: event.resource_type,
    });
  }
}
