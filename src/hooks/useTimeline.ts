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
  const { isAuthenticated, client, engagement } = useAuth();

  return useQuery<TimelineData>({
    queryKey: ['timeline'],
    queryFn: async () => {
      try {
        const response = await apiCall('/api/v1/plan/timeline');
        return response;
      } catch (error: unknown) {
        // Handle errors gracefully - return mock data for development
        if (error.status === 404 || error.status === 403) {
          console.log('Timeline endpoint not available, returning mock data');
          return {
            phases: [],
            metrics: {
              total_duration_weeks: 0,
              completed_phases: 0,
              total_phases: 0,
              overall_progress: 0,
              delayed_milestones: 0,
              at_risk_milestones: 0
            },
            schedule_health: {
              status: 'On Track',
              issues: [],
              recommendations: []
            },
            critical_path: []
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
