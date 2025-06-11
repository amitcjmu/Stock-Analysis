import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';

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
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['rehostProjects'],
    queryFn: async () => {
      const response = await fetch('/api/v1/execute/rehost', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch rehost projects');
      return response.json();
    }
  });
};

export const useReplatformProjects = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['replatformProjects'],
    queryFn: async () => {
      const response = await fetch('/api/v1/execute/replatform', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch replatform projects');
      return response.json();
    }
  });
};

export const useCutoverEvents = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['cutoverEvents'],
    queryFn: async () => {
      const response = await fetch('/api/v1/execute/cutovers', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch cutover events');
      return response.json();
    }
  });
};

export const useLessonsLearned = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['lessonsLearned'],
    queryFn: async () => {
      const response = await fetch('/api/v1/execute/lessons', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch lessons learned');
      return response.json();
    }
  });
};

export const useExecutionMetrics = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['executionMetrics'],
    queryFn: async () => {
      const response = await fetch('/api/v1/execute/metrics', {
        headers: await getAuthHeaders()
      });
      if (!response.ok) throw new Error('Failed to fetch execution metrics');
      return response.json();
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