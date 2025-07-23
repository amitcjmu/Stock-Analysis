import type { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface RefactorProject {
  id: string;
  application: string;
  complexity: 'High' | 'Medium' | 'Low';
  status: 'Planning' | 'In Progress' | 'Completed' | 'On Hold';
  progress: number;
  effort: string;
  benefits: string[];
  aiRecommendation: string;
}

export interface AIInsights {
  patterns: {
    count: number;
    description: string;
  };
  priorityProject: string;
  analysis: string;
  lastUpdated: string;
  qualityImprovement: number;
}

export interface RefactorData {
  projects: RefactorProject[];
  aiInsights: AIInsights;
  metrics: {
    totalProjects: number;
    completedProjects: number;
    inProgressProjects: number;
    averageCompletion: number;
    codeQualityImprovement: number;
  };
}

export const useRefactor = (filterStatus: string = 'All') => {
  const { getContextHeaders } = useAuth();

  return useQuery<RefactorData>({
    queryKey: ['refactor', filterStatus],
    queryFn: async () => {
      const response = await apiCall('modernize/refactor', {
        method: 'GET',
        headers: {
          ...getContextHeaders(),
          'x-filter-status': filterStatus
        }
      });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
}; 