import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface TimelinePhase {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: 'Not Started' | 'In Progress' | 'Completed' | 'Delayed';
  progress: number;
  dependencies: string[];
  wave_number?: number; // Optional wave grouping
  phase_number?: number; // Phase sequence number
  is_on_critical_path?: boolean; // Critical path indicator from backend
  milestones: Array<{
    name: string;
    date: string;
    status: 'Pending' | 'Completed' | 'At Risk';
    description: string;
  }>;
  risks: Array<{
    description: string;
    impact: 'High' | 'Medium' | 'Low';
    mitigation: string;
  }>;
}

export interface TimelineMetrics {
  total_duration_weeks: number;
  completed_phases: number;
  total_phases: number;
  overall_progress: number;
  delayed_milestones: number;
  at_risk_milestones: number;
}

export interface TimelineData {
  phases: TimelinePhase[];
  metrics: TimelineMetrics;
  critical_path: string[];
  schedule_health: {
    status: 'On Track' | 'At Risk' | 'Delayed';
    issues: string[];
    recommendations: string[];
  };
}

/**
 * Fetch timeline data derived from wave_plan_data.
 *
 * @param planning_flow_id - Optional planning flow UUID to fetch specific wave data.
 *   If provided, derives timeline phases from that flow's wave_plan_data.
 *   If not provided, uses the latest planning flow for the engagement.
 */
export const useTimeline = (planning_flow_id?: string) => {
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<TimelineData>({
    queryKey: ['timeline', planning_flow_id, client?.id, engagement?.id],
    queryFn: async () => {
      // Use roadmap endpoint which now derives phases from wave_plan_data
      const url = planning_flow_id
        ? `/api/v1/plan/roadmap?planning_flow_id=${planning_flow_id}`
        : '/api/v1/plan/roadmap';
      const response = await apiCall(url);
      return response;
    },
    enabled: isAuthenticated && !!client && !!engagement,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: 2
  });
};
