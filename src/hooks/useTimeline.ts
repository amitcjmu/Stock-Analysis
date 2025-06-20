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

export const useTimeline = () => {
  const { getContextHeaders } = useAuth();

  return useQuery<TimelineData>({
    queryKey: ['timeline'],
    queryFn: async () => {
      const response = await apiCall('plan/timeline', {
        method: 'GET',
        headers: getContextHeaders()
      });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
}; 