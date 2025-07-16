/**
 * Discovery Flow Service
 * 
 * Service for operational discovery flow status and management.
 * This service queries child flow status (discovery_flows table) for operational decisions.
 * 
 * As per ADR-012: Flow Status Management Separation, this service should be used for:
 * - All operational decisions (field mapping, data cleansing, agent decisions)
 * - Phase-specific state management
 * - Frontend display of current status
 * - Agent decision context
 */

import { apiClient } from './apiClient';
import { FlowStatusResponse } from './masterFlowService';

export interface DiscoveryFlowStatusResponse {
  success: boolean;
  flow_id: string;
  status: string;
  current_phase: string;
  progress_percentage: number;
  summary: {
    data_import_completed: boolean;
    field_mapping_completed: boolean;
    data_cleansing_completed: boolean;
    asset_inventory_completed: boolean;
    dependency_analysis_completed: boolean;
    tech_debt_assessment_completed: boolean;
    total_records: number;
    records_processed: number;
    quality_score: number;
  };
  created_at: string;
  updated_at: string;
  // Additional operational fields
  field_mappings?: any;
  cleaned_data?: any[];
  asset_inventory?: any;
  dependencies?: any;
  technical_debt?: any;
  agent_insights?: any[];
  errors?: string[];
  warnings?: string[];
}

export interface DiscoveryFlowService {
  /**
   * Get operational discovery flow status
   * This returns the child flow status for operational decisions
   */
  getOperationalStatus(flowId: string, clientAccountId: string, engagementId: string): Promise<DiscoveryFlowStatusResponse>;
  
  /**
   * Execute discovery flow phase
   */
  executePhase(flowId: string, phase: string, data: any, clientAccountId: string, engagementId: string): Promise<any>;
  
  /**
   * Submit agent clarification answers
   */
  submitClarificationAnswers(flowId: string, answers: any, clientAccountId: string, engagementId: string): Promise<any>;
}

class DiscoveryFlowServiceImpl implements DiscoveryFlowService {
  
  async getOperationalStatus(flowId: string, clientAccountId: string, engagementId: string): Promise<DiscoveryFlowStatusResponse> {
    console.log(`🔍 [DiscoveryFlowService] Getting operational status for flow: ${flowId}`);
    
    const response = await apiClient.get(`/api/v1/discovery/flow/status`, {
      params: {
        flow_id: flowId,
        client_account_id: clientAccountId,
        engagement_id: engagementId
      },
      headers: {
        'X-Client-Account-ID': clientAccountId,
        'X-Engagement-ID': engagementId
      }
    });
    
    console.log(`✅ [DiscoveryFlowService] Retrieved operational status:`, response.data);
    return response.data;
  }
  
  async executePhase(flowId: string, phase: string, data: any, clientAccountId: string, engagementId: string): Promise<any> {
    console.log(`🚀 [DiscoveryFlowService] Executing phase ${phase} for flow: ${flowId}`);
    
    // For now, fall back to the extended master flow service for phase execution
    // This will be updated once we implement proper discovery flow phase execution endpoints
    const response = await apiClient.post(`/api/v1/flows/${flowId}/execute`, {
      phase,
      data,
      client_account_id: clientAccountId,
      engagement_id: engagementId
    }, {
      headers: {
        'X-Client-Account-ID': clientAccountId,
        'X-Engagement-ID': engagementId
      }
    });
    
    console.log(`✅ [DiscoveryFlowService] Phase execution result:`, response.data);
    return response.data;
  }
  
  async submitClarificationAnswers(flowId: string, answers: any, clientAccountId: string, engagementId: string): Promise<any> {
    console.log(`📝 [DiscoveryFlowService] Submitting clarification answers for flow: ${flowId}`);
    
    const response = await apiClient.post(`/api/v1/discovery/flows/${flowId}/clarifications/submit`, {
      answers,
      client_account_id: clientAccountId,
      engagement_id: engagementId
    }, {
      headers: {
        'X-Client-Account-ID': clientAccountId,
        'X-Engagement-ID': engagementId
      }
    });
    
    console.log(`✅ [DiscoveryFlowService] Clarification submission result:`, response.data);
    return response.data;
  }
}

export const discoveryFlowService = new DiscoveryFlowServiceImpl();
export default discoveryFlowService;