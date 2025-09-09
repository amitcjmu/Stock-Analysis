/**
 * Assessment Flow API Client
 *
 * API client functions for interacting with the assessment flow backend.
 */

import type {
  AssessmentPhase,
  ArchitectureStandard,
  ApplicationComponent,
  SixRDecision,
  UserInput
} from './types';
import { masterFlowService } from '../../services/api/masterFlowService';

// API base URL
const getApiBase = (): string => {
  // Force proxy usage for development - Docker container on port 8081
  if (typeof window !== 'undefined' && window.location.port === '8081') {
    return '';
  }

  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

const API_BASE = getApiBase();

// Assessment Flow API client
export const assessmentFlowAPI = {
  async initialize(data: { selected_application_ids: string[] }, headers: Record<string, string>): Promise<Response> {
    // Use MFO endpoint for initialization
    const response = await fetch(`${API_BASE}/api/v1/master-flows/new/assessment/initialize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to initialize assessment flow: ${response.statusText}`);
    }

    return response.json();
  },

  async getStatus(flowId: string): Promise<AssessmentFlowStatus> {
    // Use MFO endpoint for status
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment-status`);

    if (!response.ok) {
      throw new Error(`Failed to get flow status: ${response.statusText}`);
    }

    return response.json();
  },

  async resume(flowId: string, data: { user_input: UserInput; save_progress: boolean }): Promise<AssessmentFlowStatus> {
    // Use MFO endpoint for resume
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment/resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to resume flow: ${response.statusText}`);
    }

    return response.json();
  },

  async navigateToPhase(flowId: string, phase: AssessmentPhase): Promise<AssessmentFlowStatus> {
    // TODO: Implement MFO endpoint for phase navigation
    // For now, use resume endpoint with phase change
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment/resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_input: { navigate_to_phase: phase }, save_progress: true }),
    });

    if (!response.ok) {
      throw new Error(`Failed to navigate to phase: ${response.statusText}`);
    }

    return response.json();
  },

  async updateArchitectureStandards(flowId: string, data: {
    engagement_standards: ArchitectureStandard[];
    application_overrides: Record<string, ArchitectureStandard>
  }): Promise<Response> {
    // Use MFO endpoint for architecture standards
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment/architecture-standards`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to update architecture standards: ${response.statusText}`);
    }

    return response.json();
  },

  async updateApplicationComponents(flowId: string, appId: string, components: ApplicationComponent[]): Promise<Response> {
    // TODO: Implement MFO endpoint for component updates
    // Temporarily disabled - use phase data updates instead
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment/phase-data`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ phase: 'component_analysis', data: { app_id: appId, components } }),
    });

    if (!response.ok) {
      throw new Error(`Failed to update application components: ${response.statusText}`);
    }

    return response.json();
  },

  async updateSixRDecision(flowId: string, appId: string, decision: Partial<SixRDecision>): Promise<Response> {
    // TODO: Implement MFO endpoint for 6R decisions
    // Temporarily disabled - use phase data updates instead
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment/phase-data`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ phase: 'six_r_decision', data: { app_id: appId, decision } }),
    });

    if (!response.ok) {
      throw new Error(`Failed to update 6R decision: ${response.statusText}`);
    }

    return response.json();
  },

  async getArchitectureStandards(flowId: string): Promise<Response> {
    // DEPRECATED: Get this data from assessment-status endpoint instead
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment-status`);

    if (!response.ok) {
      throw new Error(`Failed to get architecture standards: ${response.statusText}`);
    }

    return response.json();
  },

  async getTechDebtAnalysis(flowId: string): Promise<Response> {
    // DEPRECATED: Get this data from assessment-status endpoint instead
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment-status`);

    if (!response.ok) {
      throw new Error(`Failed to get tech debt analysis: ${response.statusText}`);
    }

    return response.json();
  },

  async getApplicationComponents(flowId: string): Promise<Response> {
    // DEPRECATED: Get this data from assessment-status endpoint instead
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment-status`);

    if (!response.ok) {
      throw new Error(`Failed to get application components: ${response.statusText}`);
    }

    return response.json();
  },

  async getSixRDecisions(flowId: string): Promise<Response> {
    // DEPRECATED: Get this data from assessment-status endpoint instead
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment-status`);

    if (!response.ok) {
      throw new Error(`Failed to get 6R decisions: ${response.statusText}`);
    }

    return response.json();
  },

  async finalize(flowId: string): Promise<Response> {
    // Use MFO endpoint for finalization
    const response = await fetch(`${API_BASE}/api/v1/master-flows/${flowId}/assessment/finalize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to finalize assessment: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get assessment status with application count using MFO endpoints
   */
  async getAssessmentStatus(flowId: string, clientAccountId: string, engagementId?: string): Promise<{
    flow_id: string;
    status: string;
    progress: number;
    current_phase: string;
    application_count: number;
  }> {
    return masterFlowService.getAssessmentStatus(flowId, clientAccountId, engagementId);
  },

  /**
   * Get assessment applications with full details using MFO endpoints
   */
  async getAssessmentApplications(flowId: string, clientAccountId: string, engagementId?: string): Promise<{
    applications: Array<{
      application_id: string;
      application_name: string;
      application_type: string;
      environment: string;
      business_criticality: string;
      technology_stack: string[];
      complexity_score: number;
      readiness_score: number;
      discovery_completed_at: string;
    }>;
  }> {
    return masterFlowService.getAssessmentApplications(flowId, clientAccountId, engagementId);
  },
};
