/**
 * API Functions
 * 
 * API interactions for agent planning dashboard.
 */

import { apiCall, API_CONFIG } from '@/config/api';
import type { FeedbackType, TaskInput } from './types'
import type { AgentPlan } from './types'
import { generateDemoPlan } from './demo-data';

export const fetchAgentPlan = async (pageContext: string): Promise<AgentPlan> => {
  try {
    console.log('🤖 Fetching agent plan for context:', pageContext);
    
    // Get current agent plan for the page context
    const response = await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_ANALYSIS}/plan`, {
      method: 'POST',
      body: JSON.stringify({
        page_context: pageContext,
        analysis_type: 'planning_workflow',
        include_human_feedback_opportunities: true
      })
    });
    
    console.log('🤖 Agent plan response:', response);
    
    if (response.agent_plan) {
      return response.agent_plan;
    } else {
      // Generate a demo plan based on page context
      console.log('🎭 No agent plan in response, generating demo plan');
      return generateDemoPlan(pageContext);
    }
  } catch (err) {
    console.error('Failed to fetch agent plan:', err);
    
    // Always provide demo plan for development - don't show error state
    const demoPlan = generateDemoPlan(pageContext);
    
    // Only throw error if it's not a 404 (which just means the endpoint isn't implemented yet)
    if (err.message && !err.message.includes('404')) {
      console.warn('Agent planning service partially available - using demo workflow');
    } else {
      console.log('🎭 Agent planning endpoint not available, using demo plan');
    }
    
    return demoPlan;
  }
};

export const submitTaskApproval = async (
  taskId: string, 
  approved: boolean, 
  pageContext: string
): Promise<void> => {
  try {
    await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING}`, {
      method: 'POST',
      body: JSON.stringify({
        task_id: taskId,
        approval: approved,
        page_context: pageContext,
        learning_type: 'task_approval_feedback'
      })
    });
  } catch (error) {
    console.error('Failed to submit task approval:', error);
    throw error;
  }
};

export const submitHumanInput = async (
  taskId: string, 
  input: TaskInput, 
  pageContext: string
): Promise<void> => {
  try {
    await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING}`, {
      method: 'POST',
      body: JSON.stringify({
        task_id: taskId,
        human_input: input,
        page_context: pageContext,
        learning_type: 'human_input_feedback'
      })
    });
  } catch (error) {
    console.error('Failed to submit human input:', error);
    throw error;
  }
};

export const submitPlanSuggestion = async (
  planId: string,
  suggestion: string,
  feedbackType: FeedbackType,
  pageContext: string
): Promise<void> => {
  try {
    await apiCall(`${API_CONFIG.ENDPOINTS.DISCOVERY.AGENT_LEARNING}`, {
      method: 'POST',
      body: JSON.stringify({
        plan_id: planId,
        suggestion: suggestion,
        feedback_type: feedbackType,
        page_context: pageContext,
        learning_type: 'plan_modification_feedback'
      })
    });
  } catch (error) {
    console.error('Failed to submit plan suggestion:', error);
    throw error;
  }
};