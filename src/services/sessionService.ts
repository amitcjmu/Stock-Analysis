import { apiCall } from "@/lib/api";

export type SessionType = 'data_import' | 'validation_run' | 'incremental_update' | 'comparison_analysis' | 'cleanup_operation';

export interface Session {
  id: string;
  session_name: string;
  session_display_name: string;
  session_type: SessionType;
  engagement_id: string;
  client_account_id: string;
  is_default: boolean;
  status: 'active' | 'archived' | 'deleted';
  auto_created: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CreateSessionRequest {
  session_name: string;
  session_display_name: string;
  engagement_id: string;
  client_account_id: string;
  is_default: boolean;
  session_type: SessionType;
  status: 'active' | 'archived' | 'deleted';
  auto_created: boolean;
  created_by: string;
}

export interface MergeSessionsRequest {
  source_session_id: string;
  target_session_id: string;
  merge_strategy: 'preserve_target' | 'overwrite' | 'merge';
}

const SESSION_ENDPOINTS = {
  SESSIONS: '/api/v1/sessions',
  SESSION_BY_ID: (id: string) => `/api/v1/sessions/${id}`,
  SET_DEFAULT: (id: string) => `/api/v1/sessions/${id}/set-default`,
  MERGE: '/api/v1/sessions/merge',
  ENGAGEMENT_DEFAULT: (engagementId: string) => 
    `/api/v1/engagements/${engagementId}/sessions/default`,
  ENGAGEMENT_SESSIONS: (engagementId: string) => 
    `/api/v1/sessions/engagement/${engagementId}`
} as const;

export const sessionService = {
  /**
   * Create a new session
   */
  async createSession(data: CreateSessionRequest): Promise<Session> {
    return apiCall(SESSION_ENDPOINTS.SESSIONS, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Get a session by ID
   */
  async getSession(sessionId: string): Promise<Session> {
    return apiCall(SESSION_ENDPOINTS.SESSION_BY_ID(sessionId));
  },

  /**
   * Get the default session for an engagement
   */
  async getDefaultSession(engagementId: string): Promise<Session> {
    return apiCall(SESSION_ENDPOINTS.ENGAGEMENT_DEFAULT(engagementId));
  },

  /**
   * Set a session as the default for its engagement
   */
  async setDefaultSession(sessionId: string): Promise<Session> {
    return apiCall(SESSION_ENDPOINTS.SET_DEFAULT(sessionId), {
      method: 'POST',
    });
  },

  /**
   * Merge two sessions
   */
  async mergeSessions(engagementId: string, sourceSessionId: string, targetSessionId: string, strategy: 'preserve_target' | 'overwrite' | 'merge'): Promise<void> {
    await apiCall(SESSION_ENDPOINTS.MERGE, {
      method: 'POST',
      body: JSON.stringify({
        source_session_id: sourceSessionId,
        target_session_id: targetSessionId,
        merge_strategy: strategy,
      }),
    });
  },

  /**
   * List all sessions for a given engagement
   */
  async listSessions(engagementId: string): Promise<Session[]> {
    return apiCall(SESSION_ENDPOINTS.ENGAGEMENT_SESSIONS(engagementId));
  },

  /**
   * Update a session
   */
  async updateSession(sessionId: string, data: Partial<Session>): Promise<Session> {
    return apiCall(SESSION_ENDPOINTS.SESSION_BY_ID(sessionId), {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await apiCall(SESSION_ENDPOINTS.SESSION_BY_ID(sessionId), {
      method: 'DELETE',
    });
  },
};
