import { apiCall } from "@/config/api";

export type SessionType = 'analysis' | 'migration' | 'testing' | 'other';

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
    `/api/v1/engagements/${engagementId}/sessions`
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
  async mergeSessions(data: MergeSessionsRequest): Promise<Session> {
    return apiCall(SESSION_ENDPOINTS.MERGE, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List all sessions for a given engagement
   * @param engagementId The engagement ID
   */
  listSessions: async (engagementId?: string | null): Promise<Session[]> => {
    if (!engagementId) {
      console.warn('No engagementId provided to listSessions');
      return [];
    }

    console.log('Fetching sessions for engagement:', engagementId);
    const endpoint = SESSION_ENDPOINTS.ENGAGEMENT_SESSIONS(engagementId);
    console.log('API Endpoint:', endpoint);
    
    try {
      const response = await apiCall(endpoint, {
        method: 'GET',
      }, true);
      
      // Handle different response formats
      if (Array.isArray(response)) {
        return response as Session[];
      } else if (response && typeof response === 'object' && 'data' in response) {
        return Array.isArray(response.data) ? response.data : [];
      }
      
      console.warn('Unexpected response format for sessions:', response);
      return [];
    } catch (error) {
      // Handle 404s gracefully - return empty array instead of throwing
      if ((error as any)?.status === 404) {
        console.log('No sessions found for engagement:', engagementId);
        return [];
      }
      
      console.error('Error fetching sessions:', error);
      throw error;
    }
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
