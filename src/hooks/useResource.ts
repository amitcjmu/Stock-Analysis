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

export const useResource = (): JSX.Element => {
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<ResourceData>({
    queryKey: ['resources'],
    queryFn: async () => {
      const response = await apiCall('/api/v1/plan/resources');
      return response;
    },
    enabled: isAuthenticated && !!client && !!engagement,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};
