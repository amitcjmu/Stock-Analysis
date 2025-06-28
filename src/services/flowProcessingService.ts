/**
 * Flow Processing Service - Frontend integration with the Flow Processing Agent
 * 
 * This service provides the frontend interface to the Flow Processing Agent,
 * which serves as the central routing agent for all CrewAI flows.
 */

import { apiCall } from '@/lib/api/apiCall';

export interface TaskResult {
  task_id: string;
  task_name: string;
  status: 'completed' | 'pending' | 'blocked' | 'not_started';
  confidence: number;
  next_steps: string[];
}

export interface PhaseChecklistResult {
  phase: string;
  status: 'completed' | 'in_progress' | 'pending' | 'blocked';
  completion_percentage: number;
  tasks: TaskResult[];
  next_required_actions: string[];
}

export interface FlowContinuationResponse {
  success: boolean;
  flow_id: string;
  current_phase: string;
  next_action: string;
  routing_context: {
    target_page: string;
    context_data: any;
    specific_task?: string;
  };
  checklist_status: PhaseChecklistResult[];
  user_guidance: {
    summary: string;
    phase: string;
    completion_percentage: number;
    next_steps: string[];
    detailed_status: {
      completed_tasks: Array<{ name: string; confidence: number }>;
      pending_tasks: Array<{ name: string; next_steps: string[] }>;
    };
  };
  error_message?: string;
}

export interface FlowChecklistResponse {
  flow_id: string;
  phases: PhaseChecklistResult[];
  overall_completion: number;
  next_required_tasks: string[];
  blocking_issues: string[];
}

export interface FlowAnalysisResponse {
  flow_id: string;
  timestamp: string;
  analysis: {
    flow_state: any;
    checklist_results: any[];
    routing_decision: {
      target_page: string;
      phase: string;
      specific_task?: string;
    };
    user_guidance: any;
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
    userContext: Record<string, any> = {}
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
        console.log(`📋 USER GUIDANCE: ${response.user_guidance.summary}`);
        console.log(`🎯 NEXT STEPS:`, response.user_guidance.next_steps);
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
    const { summary, next_steps, detailed_status } = guidance;
    
    let formatted = `🤖 ${summary}\n\n`;
    
    if (detailed_status.completed_tasks.length > 0) {
      formatted += `✅ Completed Tasks:\n`;
      detailed_status.completed_tasks.forEach(task => {
        formatted += `  • ${task.name} (${(task.confidence * 100).toFixed(0)}% confidence)\n`;
      });
      formatted += '\n';
    }
    
    if (detailed_status.pending_tasks.length > 0) {
      formatted += `⏳ Pending Tasks:\n`;
      detailed_status.pending_tasks.forEach(task => {
        formatted += `  • ${task.name}\n`;
        if (task.next_steps.length > 0) {
          task.next_steps.forEach(step => {
            formatted += `    - ${step}\n`;
          });
        }
      });
      formatted += '\n';
    }
    
    if (next_steps.length > 0) {
      formatted += `🎯 Next Steps:\n`;
      next_steps.forEach((step, index) => {
        formatted += `  ${index + 1}. ${step}\n`;
      });
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
      'not_started': '⭕'
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
      'blocked': 'text-red-600'
    };
    
    return colors[status] || 'text-gray-600';
  }
}

// Export singleton instance
export const flowProcessingService = new FlowProcessingService();

// Export for use in React hooks
export default flowProcessingService; 