import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';

interface AgentQuestion {
  id: string;
  agent_id: string;
  agent_name: string;
  question_type: string;
  page: string;
  title: string;
  question: string;
  options: string[];
  context: Record<string, any>;
  confidence: string;
  priority: string;
  created_at: string;
  is_resolved: boolean;
}

interface AgentQuestionsResponse {
  success: boolean;
  questions: AgentQuestion[];
  count: number;
  page: string;
}

interface AgentQuestionResponse {
  question_id: string;
  response: any;
  confidence?: number;
}

export const useAgentQuestions = (page: string = "dependencies") => {
  return useQuery<AgentQuestionsResponse>({
    queryKey: ['agent-questions', page],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/discovery/agents/agent-questions?page=${page}`);
        return response;
      } catch (err: any) {
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (err.status === 404 || err.response?.status === 404) {
          console.log('Agent questions endpoint not available yet');
          return { questions: [], total: 0 };
        }
        throw err;
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
    refetchOnWindowFocus: false,
  });
};

export const useAnswerAgentQuestion = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: AgentQuestionResponse) => {
      return await apiCall('/api/v1/discovery/agents/agent-questions/answer', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: (_, variables) => {
      // Invalidate and refetch agent questions
      queryClient.invalidateQueries({ queryKey: ['agent-questions'] });
      
      // Also invalidate agent insights as answering questions might generate new insights
      queryClient.invalidateQueries({ queryKey: ['agent-insights'] });
    },
  });
};

// Hook for agent insights
export const useAgentInsights = (page: string = "dependencies") => {
  return useQuery({
    queryKey: ['agent-insights', page],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/discovery/agents/agent-insights?page=${page}`);
        return response;
      } catch (err: any) {
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (err.status === 404 || err.response?.status === 404) {
          console.log('Agent insights endpoint not available yet');
          return { insights: [], total: 0 };
        }
        throw err;
      }
    },
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 60 * 1000, // Refresh every minute
    refetchOnWindowFocus: false,
  });
};

// Hook for agent status
export const useAgentStatus = () => {
  return useQuery({
    queryKey: ['agent-status'],
    queryFn: async () => {
      try {
        const response = await apiCall('/api/v1/agents/discovery/agent-status');
        return response;
      } catch (err: any) {
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (err.status === 404 || err.response?.status === 404) {
          console.log('Agent status endpoint not available yet');
          return { agents: [], status: 'unknown' };
        }
        throw err;
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Refresh every 30 seconds
    refetchOnWindowFocus: false,
  });
};

// Hook for confidence scores
export const useConfidenceScores = (page: string = "dependencies") => {
  return useQuery({
    queryKey: ['confidence-scores', page],
    queryFn: async () => {
      const response = await apiCall(`/api/v1/discovery/agents/confidence-scores?page=${page}`);
      return response;
    },
    staleTime: 45 * 1000, // 45 seconds
    refetchInterval: 45 * 1000, // Refresh every 45 seconds
    refetchOnWindowFocus: false,
  });
};

// Hook for triggering agent thinking
export const useAgentThink = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { agent_id: string; context: Record<string, any>; complexity_level?: string }) => {
      return await apiCall('/api/v1/discovery/agents/think', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      // Invalidate agent status and insights after thinking
      queryClient.invalidateQueries({ queryKey: ['agent-status'] });
      queryClient.invalidateQueries({ queryKey: ['agent-insights'] });
      queryClient.invalidateQueries({ queryKey: ['confidence-scores'] });
    },
  });
};

// Hook for triggering crew collaboration
export const useAgentPonderMore = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { agent_id: string; context: Record<string, any>; collaboration_type?: string }) => {
      return await apiCall('/api/v1/discovery/agents/ponder-more', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      // Invalidate agent status and insights after crew collaboration
      queryClient.invalidateQueries({ queryKey: ['agent-status'] });
      queryClient.invalidateQueries({ queryKey: ['agent-insights'] });
      queryClient.invalidateQueries({ queryKey: ['confidence-scores'] });
    },
  });
}; 