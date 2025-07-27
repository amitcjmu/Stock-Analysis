import { apiCall } from '../../config/api';
import { API_CONFIG } from '../../config/api';

export interface TechDebtItem {
  id: string;
  assetId: string;
  assetName: string;
  component: 'web' | 'app' | 'database' | 'os' | 'framework';
  technology: string;
  currentVersion: string;
  latestVersion: string;
  supportStatus: 'supported' | 'extended' | 'deprecated' | 'end_of_life';
  endOfLifeDate?: string;
  securityRisk: 'low' | 'medium' | 'high' | 'critical';
  migrationEffort: 'low' | 'medium' | 'high' | 'complex';
  businessImpact: 'low' | 'medium' | 'high' | 'critical';
  recommendedAction: string;
  dependencies: string[];
}

export interface SupportTimeline {
  technology: string;
  currentVersion: string;
  supportEnd: string;
  extendedSupportEnd?: string;
  replacementOptions: string[];
}

export interface TechDebtSummary {
  totalItems: number;
  highRisk: number;
  mediumRisk: number;
  lowRisk: number;
  criticalRisk: number;
  endOfLife: number;
  extendedSupport: number;
  deprecated: number;
}

export interface TechDebtAnalysisResponse {
  items: TechDebtItem[];
  summary: TechDebtSummary;
  timeline: SupportTimeline[];
}

export const fetchTechDebtAnalysis = async (clientAccountId: string, engagementId: string): Promise<TechDebtAnalysisResponse> => {
  try {
    const response = await apiCall(
      `${API_CONFIG.ENDPOINTS.DISCOVERY}/tech-debt-analysis?client_account_id=${clientAccountId}&engagement_id=${engagementId}`,
      { method: 'GET' }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching tech debt analysis:', error);
    throw error;
  }
};

export interface MigrationPlanResponse {
  plan: {
    phases: Array<{
      name: string;
      duration: string;
      items: string[];
      effort: string;
    }>;
    totalDuration: string;
    totalEffort: string;
    criticalPath: string[];
  };
}

export const generateMigrationPlan = async (clientAccountId: string, engagementId: string, items: string[]): Promise<MigrationPlanResponse> => {
  try {
    const response = await apiCall(
      `${API_CONFIG.ENDPOINTS.DISCOVERY}/generate-migration-plan`,
      {
        method: 'POST',
        body: JSON.stringify({
          client_account_id: clientAccountId,
          engagement_id: engagementId,
          items,
        }),
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error generating migration plan:', error);
    throw error;
  }
};
