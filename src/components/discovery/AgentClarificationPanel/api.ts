/**
 * API Functions
 * 
 * API interactions for agent clarification panel.
 */

import { apiCall } from '../../../config/api';
import { AgentQuestion } from './types';

export const fetchAgentQuestions = async (pageContext: string): Promise<AgentQuestion[]> => {
  try {
    const result = await apiCall(`/api/v1/agents/discovery/agent-questions?page=${pageContext}`);
    if (result.success && result.questions) {
      return result.questions;
    }
    return [];
  } catch (err: any) {
    // Handle 404 errors gracefully - these endpoints may not exist yet
    if (err.status === 404 || err.response?.status === 404) {
      console.log('Agent questions endpoint not available yet');
      return [];
    } else {
      console.error('Error fetching agent questions:', err);
      throw new Error('Failed to load agent questions');
    }
  }
};

export const submitQuestionResponse = async (
  questionId: string,
  response: string,
  responseType: 'text' | 'selection',
  pageContext: string
): Promise<boolean> => {
  try {
    const result = await apiCall('/api/v1/agents/discovery/agent-questions/answer', {
      method: 'POST',
      body: JSON.stringify({
        question_id: questionId,
        response: response,
        response_type: responseType,
        page_context: pageContext
      })
    });

    return result.success;
  } catch (err) {
    console.error('Error submitting response:', err);
    throw new Error('Failed to submit response');
  }
};