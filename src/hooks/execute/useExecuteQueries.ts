import type { useQuery, useMutation } from '@tanstack/react-query'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '@/config/api';

// Types
export type ExecutionStatus = 'Planned' | 'In Progress' | 'Completed' | 'Blocked' | 'Failed';
export type RiskLevel = 'Low' | 'Medium' | 'High';
export type Environment = 'Production' | 'Non-Production';

export interface RehostProject {
  id: string;
  name: string;
  status: ExecutionStatus;
  progress: number;
  startDate: string;
  targetDate: string;
  environment: Environment;
  complexity: RiskLevel;
}

export interface ReplatformProject {
  id: string;
  name: string;
  status: ExecutionStatus;
  progress: number;
  startDate: string;
  targetDate: string;
  platform: string;
  complexity: RiskLevel;
}

export interface CutoverEvent {
  id: string;
  name: string;
  status: ExecutionStatus;
  type: Environment;
  date: string;
  time: string;
  duration: string;
  applications: string[];
  riskLevel: RiskLevel;
}

export interface LessonLearned {
  cutover: string;
  issue: string;
  resolution: string;
  impact: string;
  category: string;
}

export interface ExecutionMetrics {
  totalMigrations: number;
  successRate: number;
  avgMigrationTime: string;
  costEfficiency: number;
  activeRehost: number;
  activeReplatform: number;
  activeCutovers: number;
}

// Hooks
export const useRehostProjects = () => {
  return useQuery({
    queryKey: ['rehostProjects'],
    queryFn: async () => {
      try {
        return await apiCall('/execute/rehost');
      } catch (error) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        const errorObj = error as Error & { status?: number; response?: { status?: number } };
        if (errorObj.status === 404 || errorObj.response?.status === 404) {
          console.log('Rehost projects endpoint not available yet');
          return [];
        }
        throw error;
      }
    },
    retry: (failureCount, error) => {
      // Don't retry 404 errors
      if (error && ('status' in error && error.status === 404)) {
        return false;
      }
      return failureCount < 2;
    }
  });
};

export const useReplatformProjects = () => {
  return useQuery({
    queryKey: ['replatformProjects'],
    queryFn: async () => {
      try {
        return await apiCall('/execute/replatform');
      } catch (error) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        const errorObj = error as Error & { status?: number; response?: { status?: number } };
        if (errorObj.status === 404 || errorObj.response?.status === 404) {
          console.log('Replatform projects endpoint not available yet');
          return [];
        }
        throw error;
      }
    },
    retry: (failureCount, error) => {
      // Don't retry 404 errors
      if (error && ('status' in error && error.status === 404)) {
        return false;
      }
      return failureCount < 2;
    }
  });
};

export const useCutoverEvents = () => {
  return useQuery({
    queryKey: ['cutoverEvents'],
    queryFn: async () => {
      try {
        return await apiCall('/execute/cutovers');
      } catch (error) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        const errorObj = error as Error & { status?: number; response?: { status?: number } };
        if (errorObj.status === 404 || errorObj.response?.status === 404) {
          console.log('Cutover events endpoint not available yet');
          return [];
        }
        throw error;
      }
    },
    retry: (failureCount, error) => {
      // Don't retry 404 errors
      if (error && ('status' in error && error.status === 404)) {
        return false;
      }
      return failureCount < 2;
    }
  });
};

export const useLessonsLearned = () => {
  return useQuery({
    queryKey: ['lessonsLearned'],
    queryFn: async () => {
      try {
        return await apiCall('/execute/lessons');
      } catch (error) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        const errorObj = error as Error & { status?: number; response?: { status?: number } };
        if (errorObj.status === 404 || errorObj.response?.status === 404) {
          console.log('Lessons learned endpoint not available yet');
          return [];
        }
        throw error;
      }
    },
    retry: (failureCount, error) => {
      // Don't retry 404 errors
      if (error && ('status' in error && error.status === 404)) {
        return false;
      }
      return failureCount < 2;
    }
  });
};

export const useExecutionMetrics = () => {
  return useQuery({
    queryKey: ['executionMetrics'],
    queryFn: async () => {
      try {
        return await apiCall('/execute/metrics');
      } catch (error) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        const errorObj = error as Error & { status?: number; response?: { status?: number } };
        if (errorObj.status === 404 || errorObj.response?.status === 404) {
          console.log('Execution metrics endpoint not available yet');
          return {
            totalMigrations: 0,
            successRate: 0,
            avgMigrationTime: '0h',
            costEfficiency: 0,
            activeRehost: 0,
            activeReplatform: 0,
            activeCutovers: 0
          };
        }
        throw error;
      }
    },
    retry: (failureCount, error) => {
      // Don't retry 404 errors
      if (error && ('status' in error && error.status === 404)) {
        return false;
      }
      return failureCount < 2;
    }
  });
};

export const useExecutionReports = () => {
  return useQuery({
    queryKey: ['executionReports'],
    queryFn: async () => {
      try {
        return await apiCall('/execute/reports');
      } catch (error) {
        // Handle 404 errors gracefully - endpoint may not exist yet
        const errorObj = error as Error & { status?: number; response?: { status?: number } };
        if (errorObj.status === 404 || errorObj.response?.status === 404) {
          console.log('Execution reports endpoint not available yet');
          return {
            reports: [],
            metrics: {
              totalMigrations: 0,
              successRate: '0%',
              avgMigrationTime: '0h',
              activeProjects: 0,
              aiInsight: 'No insights available - endpoint not implemented yet'
            }
          };
        }
        throw error;
      }
    },
    retry: (failureCount, error) => {
      // Don't retry 404 errors
      if (error && ('status' in error && error.status === 404)) {
        return false;
      }
      return failureCount < 2;
    }
  });
};

// Mutations
export const useUpdateRehostProject = () => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (project: Partial<RehostProject> & { id: string }) => {
      const response = await fetch(`/api/v1/execute/rehost/${project.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(await getAuthHeaders())
        },
        body: JSON.stringify(project)
      });
      if (!response.ok) throw new Error('Failed to update rehost project');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rehostProjects'] });
    }
  });
};

export const useUpdateReplatformProject = () => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (project: Partial<ReplatformProject> & { id: string }) => {
      const response = await fetch(`/api/v1/execute/replatform/${project.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(await getAuthHeaders())
        },
        body: JSON.stringify(project)
      });
      if (!response.ok) throw new Error('Failed to update replatform project');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['replatformProjects'] });
    }
  });
};

export const useUpdateCutoverEvent = () => {
  const queryClient = useQueryClient();
  const { getAuthHeaders } = useAuth();

  return useMutation({
    mutationFn: async (event: Partial<CutoverEvent> & { id: string }) => {
      const response = await fetch(`/api/v1/execute/cutovers/${event.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...(await getAuthHeaders())
        },
        body: JSON.stringify(event)
      });
      if (!response.ok) throw new Error('Failed to update cutover event');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cutoverEvents'] });
    }
  });
}; 