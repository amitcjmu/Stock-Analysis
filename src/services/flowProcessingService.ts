/**
 * Flow Processing Service - Frontend integration with the Flow Processing Agent
 * 
 * This service provides the frontend interface to the Flow Processing Agent,
 * which serves as the central routing agent for all CrewAI flows.
 */

import { apiCall } from '@/lib/api';
import { BaseMetadata } from '../types/shared/metadata-types';

export interface TaskResult {
  task_id: string;
  task_name: string;
  status: 'completed' | 'pending' | 'blocked' | 'not_started' | 'in_progress';
  confidence: number;
  next_steps: string[];
}

export interface PhaseChecklistResult {
  phase_id: string;
  phase_name: string;
  status: 'completed' | 'in_progress' | 'pending' | 'blocked' | 'not_started';
  completion_percentage: number;
  tasks: TaskResult[];
  estimated_time_remaining?: number;
}

export interface FlowContinuationResponse {
  success: boolean;
  flow_id: string;
  flow_type: string;
  current_phase: string;
  routing_context: {
    target_page: string;
    recommended_page: string;
    flow_id: string;
    phase: string;
    flow_type: string;
  };
  user_guidance: {
    primary_message: string;
    action_items: string[];
    user_actions: string[];
    system_actions: string[];
    estimated_completion_time?: number;
  };
  checklist_status: PhaseChecklistResult[];
  agent_insights: Array<{
    agent: string;
    analysis: string;
    confidence: number;
    issues_found: string[];
  }>;
  confidence: number;
  reasoning: string;
  execution_time: number;
  error_message?: string;
}

export interface FlowChecklistResponse {
  flow_id: string;
  phases: PhaseChecklistResult[];
  overall_completion: number;
  next_required_tasks: string[];
  blocking_issues: string[];
}

export interface FlowState extends BaseMetadata {
  current_phase: string;
  phase_progress: Record<string, number>;
  completed_tasks: string[];
  pending_tasks: string[];
  blocked_tasks: string[];
  error_states: string[];
  flow_metadata: Record<string, unknown>;
}

export interface ChecklistAnalysisResult {
  phase_id: string;
  phase_name: string;
  completed_tasks: number;
  total_tasks: number;
  completion_percentage: number;
  blocking_issues: string[];
  next_actions: string[];
}

export interface UserGuidanceData {
  primary_message: string;
  action_items: string[];
  user_actions: string[];
  system_actions: string[];
  estimated_completion_time?: number;
  priority_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface FlowAnalysisResponse {
  flow_id: string;
  timestamp: string;
  analysis: {
    flow_state: FlowState;
    checklist_results: ChecklistAnalysisResult[];
    routing_decision: {
      target_page: string;
      phase: string;
      specific_task?: string;
    };
    user_guidance: UserGuidanceData;
  };
}

class FlowProcessingService {
  private baseUrl = '/api/v1/flow-processing';

  /**
   * Process flow continuation using the Flow Processing Agent.
   * This is the main entry point for all "Continue Flow" requests.
   */
  async processContinuation(
    flowId: string,
    userContext: Record<string, unknown> = {}
  ): Promise<FlowContinuationResponse> {
    try {
      console.log(`🤖 FLOW PROCESSING SERVICE: Requesting continuation for flow ${flowId}`);
      
      const response = await apiCall(`${this.baseUrl}/continue/${flowId}`, {
        method: 'POST',
        body: JSON.stringify({
          user_context: userContext,
          user_action: 'continue_flow'
        })
      });

      if (response.success) {
        console.log(`✅ FLOW PROCESSING SUCCESS: ${flowId} -> ${response.routing_context.target_page}`);
        console.log(`📋 USER GUIDANCE: ${response.user_guidance.primary_message}`);
        console.log(`🎯 NEXT STEPS:`, response.user_guidance.action_items);
      } else {
        console.error(`❌ FLOW PROCESSING FAILED: ${flowId} - ${response.error_message}`);
      }

      return response;
    } catch (error) {
      console.error('Flow Processing Service error:', error);
      throw new Error(`Failed to process flow continuation: ${error.message}`);
    }
  }

  /**
   * Get detailed checklist status for a flow.
   * Shows what tasks have been completed and what still needs to be done.
   */
  async getChecklistStatus(flowId: string): Promise<FlowChecklistResponse> {
    try {
      console.log(`📋 CHECKLIST SERVICE: Getting status for flow ${flowId}`);
      
      const response = await apiCall(`${this.baseUrl}/checklist/${flowId}`);
      
      console.log(`📊 CHECKLIST RESULT: ${response.overall_completion.toFixed(1)}% complete`);
      console.log(`🔄 NEXT TASKS:`, response.next_required_tasks);
      
      return response;
    } catch (error) {
      console.error('Checklist Service error:', error);
      throw new Error(`Failed to get checklist status: ${error.message}`);
    }
  }

  /**
   * Get comprehensive flow analysis for debugging and monitoring.
   * Provides detailed information about the Flow Processing Agent's decision making.
   */
  async analyzeFlowState(flowId: string): Promise<FlowAnalysisResponse> {
    try {
      console.log(`🔍 ANALYSIS SERVICE: Analyzing flow state for ${flowId}`);
      
      const response = await apiCall(`${this.baseUrl}/analyze/${flowId}`, {
        method: 'POST'
      });
      
      console.log(`🧠 ANALYSIS RESULT:`, response.analysis.routing_decision);
      
      return response;
    } catch (error) {
      console.error('Analysis Service error:', error);
      throw new Error(`Failed to analyze flow state: ${error.message}`);
    }
  }

  /**
   * Helper method to format user guidance for display
   */
  formatUserGuidance(guidance: FlowContinuationResponse['user_guidance']): string {
    const { primary_message, action_items, estimated_completion_time } = guidance;
    
    let formatted = `🤖 ${primary_message}\n\n`;
    
    if (action_items.length > 0) {
      formatted += `🎯 Next Steps:\n`;
      action_items.forEach((step, index) => {
        formatted += `  ${index + 1}. ${step}\n`;
      });
    }
    
    if (estimated_completion_time) {
      formatted += `⏳ Estimated Completion Time: ${estimated_completion_time} minutes\n`;
    }
    
    return formatted;
  }

  /**
   * Helper method to get phase display name
   */
  getPhaseDisplayName(phase: string): string {
    const phaseNames = {
      'data_import': 'Data Import',
      'attribute_mapping': 'Attribute Mapping',
      'data_cleansing': 'Data Cleansing',
      'inventory': 'Asset Inventory',
      'dependencies': 'Dependency Analysis',
      'tech_debt': 'Technical Debt Analysis'
    };
    
    return phaseNames[phase] || phase.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Helper method to get task status icon
   */
  getTaskStatusIcon(status: TaskResult['status']): string {
    const icons = {
      'completed': '✅',
      'pending': '⏳',
      'blocked': '🚫',
      'not_started': '⭕',
      'in_progress': '🔄'
    };
    
    return icons[status] || '❓';
  }

  /**
   * Helper method to get phase status color
   */
  getPhaseStatusColor(status: PhaseChecklistResult['status']): string {
    const colors = {
      'completed': 'text-green-600',
      'in_progress': 'text-blue-600',
      'pending': 'text-yellow-600',
      'blocked': 'text-red-600',
      'not_started': 'text-gray-600'
    };
    
    return colors[status] || 'text-gray-600';
  }
}

// Export singleton instance
export const flowProcessingService = new FlowProcessingService();

// Export for use in React hooks
export default flowProcessingService; 