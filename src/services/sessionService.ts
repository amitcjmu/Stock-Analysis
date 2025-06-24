/**
 * Session Service - DEPRECATED
 * 
 * ⚠️ DEPRECATION NOTICE: This service is deprecated in favor of V2 Discovery Flow architecture.
 * New implementations should use the V2 Discovery Flow API.
 * 
 * Migration Guide:
 * - Use /api/v2/discovery-flows/ endpoints instead of /api/v1/sessions/
 * - Replace session_id with flow_id patterns
 * - Use DiscoveryFlowService for flow management
 */

import { api } from '../config/api';

export interface SessionData {
  session_id: string;
  client_account_id: string;
  engagement_id: string;
  status: string;
  metadata?: Record<string, any>;
  migration_notice?: string;
}

export interface SessionCreateRequest {
  client_account_id: string;
  engagement_id: string;
  metadata?: Record<string, any>;
}

export interface SessionUpdateRequest {
  metadata?: Record<string, any>;
  status?: string;
}

export interface SessionListResponse {
  sessions: SessionData[];
  total: number;
  limit: number;
  offset: number;
  message?: string;
  migration_notice?: string;
}

class SessionService {
  private readonly baseUrl = '/api/v1/sessions';

  /**
   * ⚠️ DEPRECATED: Create a new session
   * 
   * Use V2 Discovery Flow API: POST /api/v2/discovery-flows/
   */
  async createSession(data: SessionCreateRequest): Promise<SessionData> {
    console.warn('⚠️ Deprecated: createSession() - Use V2 Discovery Flow API');
    
    try {
      const response = await api.post<SessionData>(this.baseUrl, data);
      return response.data;
    } catch (error) {
      console.error('Failed to create session (deprecated):', error);
      throw new Error('Session creation deprecated - use V2 Discovery Flow API');
    }
  }

  /**
   * ⚠️ DEPRECATED: Get session by ID
   * 
   * Use V2 Discovery Flow API: GET /api/v2/discovery-flows/{flow_id}
   */
  async getSession(sessionId: string): Promise<SessionData> {
    console.warn(`⚠️ Deprecated: getSession(${sessionId}) - Use V2 Discovery Flow API`);
    
    try {
      const response = await api.get<SessionData>(`${this.baseUrl}/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to get session ${sessionId} (deprecated):`, error);
      throw new Error('Session lookup deprecated - use V2 Discovery Flow API');
    }
  }

  /**
   * ⚠️ DEPRECATED: Update session
   * 
   * Use V2 Discovery Flow API: PUT /api/v2/discovery-flows/{flow_id}
   */
  async updateSession(sessionId: string, data: SessionUpdateRequest): Promise<SessionData> {
    console.warn(`⚠️ Deprecated: updateSession(${sessionId}) - Use V2 Discovery Flow API`);
    
    try {
      const response = await api.put<SessionData>(`${this.baseUrl}/${sessionId}`, data);
      return response.data;
    } catch (error) {
      console.error(`Failed to update session ${sessionId} (deprecated):`, error);
      throw new Error('Session update deprecated - use V2 Discovery Flow API');
    }
  }

  /**
   * ⚠️ DEPRECATED: Delete session
   * 
   * Use V2 Discovery Flow API: DELETE /api/v2/discovery-flows/{flow_id}
   */
  async deleteSession(sessionId: string): Promise<{ message: string }> {
    console.warn(`⚠️ Deprecated: deleteSession(${sessionId}) - Use V2 Discovery Flow API`);
    
    try {
      const response = await api.delete<{ message: string }>(`${this.baseUrl}/${sessionId}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to delete session ${sessionId} (deprecated):`, error);
      throw new Error('Session deletion deprecated - use V2 Discovery Flow API');
    }
  }

  /**
   * ⚠️ DEPRECATED: List sessions
   * 
   * Use V2 Discovery Flow API: GET /api/v2/discovery-flows/
   */
  async listSessions(limit = 50, offset = 0): Promise<SessionListResponse> {
    console.warn('⚠️ Deprecated: listSessions() - Use V2 Discovery Flow API');
    
    try {
      const response = await api.get<SessionListResponse>(
        `${this.baseUrl}?limit=${limit}&offset=${offset}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to list sessions (deprecated):', error);
      throw new Error('Session listing deprecated - use V2 Discovery Flow API');
    }
  }

  /**
   * ⚠️ DEPRECATED: Get session status
   * 
   * Use V2 Discovery Flow API: GET /api/v2/discovery-flows/{flow_id}/status
   */
  async getSessionStatus(sessionId: string): Promise<{
    session_id: string;
    status: string;
    current_phase: string;
    progress: number;
    message?: string;
    migration_notice?: string;
  }> {
    console.warn(`⚠️ Deprecated: getSessionStatus(${sessionId}) - Use V2 Discovery Flow API`);
    
    try {
      const response = await api.get(`${this.baseUrl}/${sessionId}/status`);
      return response.data;
    } catch (error) {
      console.error(`Failed to get session status ${sessionId} (deprecated):`, error);
      throw new Error('Session status lookup deprecated - use V2 Discovery Flow API');
    }
  }

  /**
   * Migration helper: Get V2 API recommendations
   */
  getV2MigrationGuide(): {
    deprecated_endpoints: string[];
    v2_endpoints: string[];
    migration_benefits: string[];
  } {
    return {
      deprecated_endpoints: [
        'POST /api/v1/sessions - Create session',
        'GET /api/v1/sessions/{id} - Get session',
        'PUT /api/v1/sessions/{id} - Update session',
        'DELETE /api/v1/sessions/{id} - Delete session',
        'GET /api/v1/sessions - List sessions',
        'GET /api/v1/sessions/{id}/status - Get session status'
      ],
      v2_endpoints: [
        'POST /api/v2/discovery-flows/ - Create discovery flow',
        'GET /api/v2/discovery-flows/{flow_id} - Get flow details',
        'PUT /api/v2/discovery-flows/{flow_id} - Update flow',
        'DELETE /api/v2/discovery-flows/{flow_id} - Delete flow',
        'GET /api/v2/discovery-flows/ - List flows',
        'GET /api/v2/discovery-flows/{flow_id}/status - Get flow status'
      ],
      migration_benefits: [
        'Simplified architecture with flow-based patterns',
        'Better performance with direct flow operations',
        'Enhanced debugging with flow_id traceability',
        'Real-time progress tracking and monitoring',
        'Multi-tenant isolation built-in',
        'CrewAI Flow integration for agentic workflows'
      ]
    };
  }
}

// Export singleton instance
export const sessionService = new SessionService();

// Export for backward compatibility
export default sessionService;
