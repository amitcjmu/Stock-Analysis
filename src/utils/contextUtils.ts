import type { AuthContextType } from '../contexts/AuthContext';

interface ContextWithIds {
  client?: { id: string };
  engagement?: { id: string };
  currentEngagementId?: string | null;
  flowId?: string | null;
  user?: { id: string; role: string } | null;
}

/**
 * Gets authentication headers including auth token and context headers
 * @param context - The auth context
 * @returns Headers object with authentication and context information
 */
export const getAuthHeaders = (context?: Partial<AuthContextType & ContextWithIds>): Record<string, string> => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  const headers: Record<string, string> = {};

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (context?.user) {
    headers['X-User-ID'] = context.user.id;
    headers['X-User-Role'] = context.user.role;
  }

  if (context?.currentEngagementId) {
    headers['X-Engagement-ID'] = context.currentEngagementId;
  }

  if (context?.flowId) {
    headers['X-Flow-ID'] = context.flowId;
  }

  return headers;
};

/**
 * Generates context headers for API requests
 * @param context - The auth context containing client and engagement info
 * @returns Headers object with context information
 */
export const getContextHeaders = (context?: Partial<ContextWithIds>) => {
  const headers: Record<string, string> = {};

  if (context?.client?.id) {
    headers['X-Client-Account-ID'] = context.client.id;
  }

  if (context?.engagement?.id) {
    headers['X-Engagement-ID'] = context.engagement.id;
  } else if (context?.currentEngagementId) {
    headers['X-Engagement-ID'] = context.currentEngagementId;
  }

  if (context?.flowId) {
    headers['X-Flow-ID'] = context.flowId;
  }

  return headers;
};

/**
 * Extracts context IDs from headers
 * @param headers - Response headers
 * @returns Object containing context IDs
 */
export const extractContextFromHeaders = (headers: Headers): Record<string, string> => {
  return {
    clientId: headers.get('X-Client-ID') || '',
    engagementId: headers.get('X-Engagement-ID') || '',
    flowId: headers.get('X-Flow-ID') || '',
  };
};
