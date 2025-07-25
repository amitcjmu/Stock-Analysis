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

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Assessment Flow API client
export const assessmentFlowAPI = {
  async initialize(data: { selected_application_ids: string[] }, headers: Record<string, string>) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/initialize`, {
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

  async getStatus(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/status`);

    if (!response.ok) {
      throw new Error(`Failed to get flow status: ${response.statusText}`);
    }

    return response.json();
  },

  async resume(flowId: string, data: { user_input: UserInput; save_progress: boolean }) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/resume`, {
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

  async navigateToPhase(flowId: string, phase: AssessmentPhase) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/navigate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ phase }),
    });

    if (!response.ok) {
      throw new Error(`Failed to navigate to phase: ${response.statusText}`);
    }

    return response.json();
  },

  async updateArchitectureStandards(flowId: string, data: {
    engagement_standards: ArchitectureStandard[];
    application_overrides: Record<string, ArchitectureStandard>
  }) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/architecture-standards`, {
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

  async updateApplicationComponents(flowId: string, appId: string, components: ApplicationComponent[]) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/applications/${appId}/components`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ components }),
    });

    if (!response.ok) {
      throw new Error(`Failed to update application components: ${response.statusText}`);
    }

    return response.json();
  },

  async updateSixRDecision(flowId: string, appId: string, decision: Partial<SixRDecision>) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/applications/${appId}/sixr-decision`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(decision),
    });

    if (!response.ok) {
      throw new Error(`Failed to update 6R decision: ${response.statusText}`);
    }

    return response.json();
  },

  async getArchitectureStandards(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/architecture-standards`);

    if (!response.ok) {
      throw new Error(`Failed to get architecture standards: ${response.statusText}`);
    }

    return response.json();
  },

  async getTechDebtAnalysis(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/tech-debt-analysis`);

    if (!response.ok) {
      throw new Error(`Failed to get tech debt analysis: ${response.statusText}`);
    }

    return response.json();
  },

  async getApplicationComponents(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/application-components`);

    if (!response.ok) {
      throw new Error(`Failed to get application components: ${response.statusText}`);
    }

    return response.json();
  },

  async getSixRDecisions(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/sixr-decisions`);

    if (!response.ok) {
      throw new Error(`Failed to get 6R decisions: ${response.statusText}`);
    }

    return response.json();
  },

  async finalize(flowId: string) {
    const response = await fetch(`${API_BASE}/api/v1/assessment-flow/${flowId}/finalize`, {
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
};
