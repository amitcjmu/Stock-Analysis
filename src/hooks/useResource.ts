import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';
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
  const { getContextHeaders } = useAuth();

  return useQuery<ResourceData>({
    queryKey: ['resources'],
    queryFn: async () => {
      const response = await apiCall('plan/resources', {
        method: 'GET',
        headers: getContextHeaders()
      });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
}; 