/**
 * MFO-Compliant API Service
 *
 * This service ensures all API calls follow the Master Flow Orchestrator (MFO) pattern.
 * NEVER call legacy discovery endpoints (/api/v1/discovery/...) as this bypasses the MFO and corrupts state.
 * ALWAYS use the MasterFlowOrchestrator via /api/v1/flows for all workflow operations.
 */

import { apiCall } from '@/lib/api';

/**
 * MFO-compliant endpoints mapping
 * Maps legacy endpoints to their MFO-compliant equivalents
 */
export const MFO_ENDPOINTS = {
  // Flow management
  FLOWS_LIST: '/api/v1/flows',
  FLOW_DETAILS: (flowId: string) => `/api/v1/flows/${flowId}`,
  FLOW_STATUS: (flowId: string) => `/api/v1/flows/${flowId}/status`,
  FLOW_EXECUTE: (flowId: string) => `/api/v1/flows/${flowId}/execute`,
  FLOW_EVENTS: (flowId: string) => `/api/v1/flows/${flowId}/events`,
  FLOW_PAUSE: (flowId: string) => `/api/v1/flows/${flowId}/pause`,
  FLOW_RESUME: (flowId: string) => `/api/v1/flows/${flowId}/resume`,
  FLOWS_ACTIVE: '/api/v1/flows/active',

  // Flow-scoped agent operations
  FLOW_AGENT_QUESTIONS: (flowId: string, page?: string) =>
    `/api/v1/flows/${flowId}/agent-questions${page ? `?page=${page}` : ''}`,
  FLOW_AGENT_INSIGHTS: (flowId: string, page?: string) =>
    `/api/v1/flows/${flowId}/agent-insights${page ? `?page=${page}` : ''}`,
  FLOW_AGENT_STATUS: (flowId: string) => `/api/v1/flows/${flowId}/agent-status`,
  FLOW_AGENT_ANSWER: (flowId: string) => `/api/v1/flows/${flowId}/agent-questions/answer`,

  // Flow-scoped data operations
  FLOW_APPLICATIONS: (flowId: string, appId?: string) =>
    appId ? `/api/v1/flows/${flowId}/applications/${appId}` : `/api/v1/flows/${flowId}/applications`,
  FLOW_DATA_CLASSIFICATIONS: (flowId: string, page?: string) =>
    `/api/v1/flows/${flowId}/data-classifications${page ? `?page=${page}` : ''}`,
  FLOW_FIELD_MAPPINGS: (flowId: string) => `/api/v1/flows/${flowId}/field-mappings`,
  FLOW_MONITORING: (flowId: string) => `/api/v1/flows/${flowId}/monitoring`,
} as const;

/**
 * Service for MFO-compliant API operations
 */
export class MFOApiService {
  /**
   * Get active flows (replaces /api/v1/unified-discovery/flows/active)
   */
  static async getActiveFlows(flowType?: 'discovery' | 'assessment' | 'migration') {
    const params = flowType ? `?type=${flowType}` : '';
    return apiCall(`${MFO_ENDPOINTS.FLOWS_ACTIVE}${params}`);
  }

  /**
   * Get flow details (replaces direct discovery flow queries)
   */
  static async getFlowDetails(flowId: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_DETAILS(flowId));
  }

  /**
   * Get flow status (replaces /api/v1/unified-discovery/flow/{id}/status)
   */
  static async getFlowStatus(flowId: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_STATUS(flowId));
  }

  /**
   * Execute flow (replaces /api/v1/unified-discovery/flow/run-redesigned)
   */
  static async executeFlow(flowId: string, data?: any) {
    return apiCall(MFO_ENDPOINTS.FLOW_EXECUTE(flowId), {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Create new flow (replaces legacy flow creation)
   */
  static async createFlow(flowData: {
    name: string;
    type: 'discovery' | 'assessment' | 'migration';
    metadata?: any;
  }) {
    return apiCall(MFO_ENDPOINTS.FLOWS_LIST, {
      method: 'POST',
      body: JSON.stringify(flowData),
    });
  }

  /**
   * Get agent questions for a flow (replaces /api/v1/agents/discovery/agent-questions)
   */
  static async getFlowAgentQuestions(flowId: string, page?: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_AGENT_QUESTIONS(flowId, page));
  }

  /**
   * Answer agent question (replaces /api/v1/agents/discovery/agent-questions/answer)
   */
  static async answerFlowAgentQuestion(flowId: string, answer: any) {
    return apiCall(MFO_ENDPOINTS.FLOW_AGENT_ANSWER(flowId), {
      method: 'POST',
      body: JSON.stringify(answer),
    });
  }

  /**
   * Get agent insights (replaces /api/v1/agents/discovery/agent-insights)
   */
  static async getFlowAgentInsights(flowId: string, page?: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_AGENT_INSIGHTS(flowId, page));
  }

  /**
   * Get agent status (replaces /api/v1/agents/discovery/agent-status)
   */
  static async getFlowAgentStatus(flowId: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_AGENT_STATUS(flowId));
  }

  /**
   * Get flow applications (replaces /api/v1/unified-discovery/applications)
   */
  static async getFlowApplications(flowId: string, applicationId?: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_APPLICATIONS(flowId, applicationId));
  }

  /**
   * Get flow monitoring (replaces /api/v1/unified-discovery/flow/crews/monitoring)
   */
  static async getFlowMonitoring(flowId: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_MONITORING(flowId));
  }

  /**
   * Pause flow execution
   */
  static async pauseFlow(flowId: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_PAUSE(flowId), {
      method: 'POST',
    });
  }

  /**
   * Resume flow execution
   */
  static async resumeFlow(flowId: string) {
    return apiCall(MFO_ENDPOINTS.FLOW_RESUME(flowId), {
      method: 'POST',
    });
  }
}

/**
 * Migration helper to detect and warn about legacy API usage
 */
export function detectLegacyApiUsage(endpoint: string): boolean {
  const legacyPatterns = [
    '/api/v1/discovery/',
    '/api/v1/agents/discovery/',
    '/api/v1/unified-discovery/',
  ];

  for (const pattern of legacyPatterns) {
    if (endpoint.includes(pattern)) {
      console.warn(
        `⚠️ Legacy API pattern detected: ${endpoint}\n` +
        `This violates MFO pattern and should be migrated to /api/v1/flows/*\n` +
        `See docs/analysis/notes/000-lessons.md for details.`
      );
      return true;
    }
  }

  return false;
}

/**
 * Hook to get current flow context
 * Components should use this to get the current flow ID for MFO operations
 */
export function useFlowContext(): { flowId: string | null } {
  // This should be implemented to get flowId from React Context or route params
  // For now, returning null as placeholder
  return { flowId: null };
}
