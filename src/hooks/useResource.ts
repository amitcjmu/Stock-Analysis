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

/**
 * Fetch resource planning data with AI-estimated teams based on 6R strategies.
 *
 * @param planning_flow_id - Optional planning flow UUID for 6R-based resource estimation.
 *   When provided, analyzes wave applications by migration strategy to estimate staffing needs.
 */
export const useResource = (planning_flow_id?: string) => {
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<ResourceData>({
    queryKey: ['resources', planning_flow_id, client?.id, engagement?.id],
    queryFn: async () => {
      // Pass planning_flow_id for 6R-based resource estimation from wave data
      const url = planning_flow_id
        ? `/api/v1/plan/resources?planning_flow_id=${planning_flow_id}`
        : '/api/v1/plan/resources';
      const response = await apiCall(url);
      return response;
    },
    enabled: isAuthenticated && !!client && !!engagement,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};
