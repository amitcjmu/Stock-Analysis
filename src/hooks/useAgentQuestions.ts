import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import type { ApiError, NetworkError } from '@/types/hooks/error-types';

interface AgentQuestion {
  id: string;
  agent_id: string;
  agent_name: string;
  question_type: string;
  page: string;
  title: string;
  question: string;
  options: string[];
  context: Record<string, string | number | boolean>;
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
  response: string | number | boolean | string[];
  confidence?: number;
}

export const useAgentQuestions = (page: string = "dependencies") => {
  const consecutiveErrors = useRef<number>(0);
  const maxConsecutiveErrors = 3;
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<AgentQuestionsResponse>({
    queryKey: ['agent-questions', page],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/agents/discovery/agent-questions?page=${page}`);
        consecutiveErrors.current = 0; // Reset on success
        return response;
      } catch (err: Error | ApiError | NetworkError | unknown) {
        consecutiveErrors.current += 1;
        console.error(`❌ Agent questions fetch error (attempt ${consecutiveErrors.current}):`, err);
        
        // Type guard for error with status property
        const error = err as { status?: number; response?: { status?: number } };
        
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (error.status === 404 || error.response?.status === 404) {
          console.log('Agent questions endpoint not available yet');
          return { questions: [], total: 0 };
        }
        
        // Handle 403 auth errors gracefully - auth context may not be ready
        if (error.status === 403 || error.response?.status === 403) {
          console.log('Agent questions endpoint requires authentication - context may not be ready yet');
          return { questions: [], total: 0 };
        }
        
        // Stop polling after max consecutive errors
        if (consecutiveErrors.current >= maxConsecutiveErrors) {
          console.warn(`🚫 Stopping agent questions polling after ${maxConsecutiveErrors} consecutive failures`);
        }
        
        throw err;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement, // Only run query when authenticated with context
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: false, // Disable automatic polling for agent questions
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      // Don't retry 404 or 403 errors
      if (error && ('status' in error && (error.status === 404 || error.status === 403))) {
        return false;
      }
      return failureCount < 2 && consecutiveErrors.current < maxConsecutiveErrors;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
};

export const useAnswerAgentQuestion = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: AgentQuestionResponse) => {
      return await apiCall('/api/v1/agents/discovery/agent-questions/answer', {
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
  const consecutiveErrors = useRef<number>(0);
  const maxConsecutiveErrors = 3;
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery({
    queryKey: ['agent-insights', page],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/agents/discovery/agent-insights?page=${page}`);
        consecutiveErrors.current = 0; // Reset on success
        return response;
      } catch (err: Error | ApiError | NetworkError | unknown) {
        consecutiveErrors.current += 1;
        console.error(`❌ Agent insights fetch error (attempt ${consecutiveErrors.current}):`, err);
        
        // Type guard for error with status property
        const error = err as { status?: number; response?: { status?: number } };
        
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (error.status === 404 || error.response?.status === 404) {
          console.log('Agent insights endpoint not available yet');
          return { insights: [], total: 0 };
        }
        
        // Handle 403 auth errors gracefully - auth context may not be ready
        if (error.status === 403 || error.response?.status === 403) {
          console.log('Agent insights endpoint requires authentication - context may not be ready yet');
          return { insights: [], total: 0 };
        }
        
        // Stop polling after max consecutive errors
        if (consecutiveErrors.current >= maxConsecutiveErrors) {
          console.warn(`🚫 Stopping agent insights polling after ${maxConsecutiveErrors} consecutive failures`);
        }
        
        throw err;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement, // Only run query when authenticated with context
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: false, // Disable automatic polling for agent insights
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      // Don't retry 404 or 403 errors
      if (error && ('status' in error && (error.status === 404 || error.status === 403))) {
        return false;
      }
      return failureCount < 2 && consecutiveErrors.current < maxConsecutiveErrors;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
};

// Hook for agent status
export const useAgentStatus = () => {
  const consecutiveErrors = useRef<number>(0);
  const maxConsecutiveErrors = 3;
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery({
    queryKey: ['agent-status'],
    queryFn: async () => {
      try {
        const response = await apiCall('/api/v1/agents/discovery/agent-status');
        consecutiveErrors.current = 0; // Reset on success
        return response;
      } catch (err: Error | ApiError | NetworkError | unknown) {
        consecutiveErrors.current += 1;
        console.error(`❌ Agent status fetch error (attempt ${consecutiveErrors.current}):`, err);
        
        // Type guard for error with status property
        const error = err as { status?: number; response?: { status?: number } };
        
        // Handle 404 errors gracefully - these endpoints may not exist yet
        if (error.status === 404 || error.response?.status === 404) {
          console.log('Agent status endpoint not available yet');
          return { agents: [], status: 'unknown' };
        }
        
        // Handle 403 auth errors gracefully - auth context may not be ready
        if (error.status === 403 || error.response?.status === 403) {
          console.log('Agent status endpoint requires authentication - context may not be ready yet');
          return { agents: [], status: 'unknown' };
        }
        
        // Stop polling after max consecutive errors
        if (consecutiveErrors.current >= maxConsecutiveErrors) {
          console.warn(`🚫 Stopping agent status polling after ${maxConsecutiveErrors} consecutive failures`);
        }
        
        throw err;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement, // Only run query when authenticated with context
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: false, // Disable automatic polling for agent status
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      // Don't retry 404 or 403 errors
      if (error && ('status' in error && (error.status === 404 || error.status === 403))) {
        return false;
      }
      return failureCount < 2 && consecutiveErrors.current < maxConsecutiveErrors;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
};

// Hook for confidence scores
export const useConfidenceScores = (page: string = "dependencies") => {
  const consecutiveErrors = useRef<number>(0);
  const maxConsecutiveErrors = 3;
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery({
    queryKey: ['confidence-scores', page],
    queryFn: async () => {
      try {
        const response = await apiCall(`/api/v1/agents/discovery/confidence-scores?page=${page}`);
        consecutiveErrors.current = 0; // Reset on success
        return response;
      } catch (err: Error | ApiError | NetworkError | unknown) {
        consecutiveErrors.current += 1;
        console.error(`❌ Confidence scores fetch error (attempt ${consecutiveErrors.current}):`, err);
        
        // Type guard for error with status property
        const error = err as { status?: number; response?: { status?: number } };
        
        // Handle 403 auth errors gracefully - auth context may not be ready
        if (error.status === 403 || error.response?.status === 403) {
          console.log('Confidence scores endpoint requires authentication - context may not be ready yet');
          return { confidence_scores: [], total: 0 };
        }
        
        // Stop polling after max consecutive errors
        if (consecutiveErrors.current >= maxConsecutiveErrors) {
          console.warn(`🚫 Stopping confidence scores polling after ${maxConsecutiveErrors} consecutive failures`);
        }
        
        throw err;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement, // Only run query when authenticated with context
    staleTime: 45 * 1000, // 45 seconds
    refetchInterval: consecutiveErrors.current >= maxConsecutiveErrors ? false : 45 * 1000, // Stop polling on errors
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      // Don't retry 403 errors
      if (error && ('status' in error && error.status === 403)) {
        return false;
      }
      return failureCount < 2 && consecutiveErrors.current < maxConsecutiveErrors;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
  });
};

// Hook for triggering agent thinking
export const useAgentThink = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: { agent_id: string; context: Record<string, unknown>; complexity_level?: string }) => {
      return await apiCall('/api/v1/agents/discovery/think', {
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
    mutationFn: async (data: { agent_id: string; context: Record<string, unknown>; collaboration_type?: string }) => {
      return await apiCall('/api/v1/agents/discovery/ponder-more', {
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