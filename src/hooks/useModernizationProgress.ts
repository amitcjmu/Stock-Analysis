import type { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface ProgressMetric {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
}

export interface ProjectTreatment {
  treatment: string;
  total: number;
  completed: number;
  inProgress: number;
  delayed: number;
  onTrack: number;
}

export interface Activity {
  id: number;
  type: 'completion' | 'milestone' | 'delay' | 'start';
  project: string;
  time: string;
  status: 'success' | 'info' | 'warning';
}

export interface Milestone {
  project: string;
  milestone: string;
  date: string;
  daysLeft: number;
}

export interface ModernizationProgress {
  metrics: ProgressMetric[];
  projectsByTreatment: ProjectTreatment[];
  recentActivities: Activity[];
  upcomingMilestones: Milestone[];
  aiInsights: {
    prediction: string;
    recommendations: string[];
    lastUpdated: string;
    accuracy: number;
  };
}

export const useModernizationProgress = (timeframe: 'week' | 'month' | 'quarter') => {
  const { getContextHeaders } = useAuth();

  return useQuery<ModernizationProgress>({
    queryKey: ['modernization-progress', timeframe],
    queryFn: async () => {
      const response = await apiCall('modernize/progress', {
        method: 'GET',
        headers: {
          ...getContextHeaders(),
          'x-timeframe': timeframe
        }
      });
      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false
  });
}; 