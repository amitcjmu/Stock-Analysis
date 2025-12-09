/**
 * Custom hook for audit logging with automatic authentication context.
 *
 * Encapsulates the logic for retrieving authentication context and calling
 * the audit logging function, simplifying usage within components.
 *
 * @example
 * ```tsx
 * const logAuditEvent = useAuditLogger();
 *
 * // Simple usage - auth context is automatically included
 * logAuditEvent({
 *   action_type: 'action_blocked',
 *   resource_type: 'discovery_flow',
 *   result: 'blocked',
 *   reason: 'Flow is in terminal state',
 * }, flowId);
 * ```
 */

import { useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { logTerminalStateAuditEvent, type AuditLogEvent } from '@/utils/auditLogger';

/**
 * Hook that provides a simplified audit logging function with automatic auth context.
 *
 * @returns A memoized function that logs audit events with auth context automatically included
 */
export const useAuditLogger = () => {
  const { client, engagement, getAuthHeaders } = useAuth();

  const logAuditEvent = useCallback(
    (
      event: AuditLogEvent,
      flowId?: string,
      clientId?: string,
      engagementId?: string
    ): Promise<void> => {
      // Use provided IDs or fall back to auth context
      const effectiveClientId = clientId || client?.id;
      const effectiveEngagementId = engagementId || engagement?.id;

      return logTerminalStateAuditEvent(
        event,
        flowId,
        effectiveClientId,
        effectiveEngagementId,
        getAuthHeaders()
      );
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [client?.id, engagement?.id]
    // Note: getAuthHeaders is intentionally excluded from dependencies
    // to prevent unnecessary re-renders. It's called at execution time.
  );

  return logAuditEvent;
};
