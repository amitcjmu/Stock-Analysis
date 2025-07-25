import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface ResourceTeam {
  id: string;
  name: string;
  size: number;
  skills: string[];
  availability: number;
  utilization: number;
  assignments: Array<{
    project: string;
    allocation: number;
    start_date: string;
    end_date: string;
  }>;
}

export interface ResourceMetrics {
  total_teams: number;
  total_resources: number;
  average_utilization: number;
  skill_coverage: {
    [key: string]: number;
  };
}

export interface ResourceData {
  teams: ResourceTeam[];
  metrics: ResourceMetrics;
  recommendations: Array<{
    type: string;
    description: string;
    impact: 'High' | 'Medium' | 'Low';
  }>;
  upcoming_needs: Array<{
    skill: string;
    demand: number;
    timeline: string;
  }>;
}

export const useResource = () => {
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<ResourceData>({
    queryKey: ['resources'],
    queryFn: async () => {
      try {
        const response = await apiCall('/api/v1/plan/resources');
        return response;
      } catch (error: unknown) {
        // Handle errors gracefully - return mock data for development
        if (error.status === 404 || error.status === 403) {
          console.log('Resources endpoint not available, returning mock data');
          return {
            teams: [],
            metrics: {
              total_teams: 0,
              total_resources: 0,
              average_utilization: 0,
              skill_coverage: {}
            },
            recommendations: [],
            upcoming_needs: []
          };
        }
        throw error;
      }
    },
    enabled: isAuthenticated && !!client && !!engagement,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      // Don't retry 404 or 403 errors
      if (error && ('status' in error && (error.status === 404 || error.status === 403))) {
        return false;
      }
      return failureCount < 2;
    }
  });
};
