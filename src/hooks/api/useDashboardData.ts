import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';
import { getAuthHeaders } from '@/utils/contextUtils';
import type { ApiError } from '../../types/shared/api-types';

export interface CrewPerformanceMetric {
  crew_id: string;
  crew_name: string;
  total_tasks: number;
  completed_tasks: number;
  success_rate: number;
  average_execution_time: number;
  last_activity: string;
  performance_score: number;
}

export interface PlatformAlert {
  alert_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  category: 'system' | 'flow' | 'performance' | 'security';
  created_at: string;
  acknowledged: boolean;
  source_component: string;
}

export interface FlowSummary {
  flow_id: string;
  status: string;
  type: string;
  current_phase: string;
  created_at: string;
  progress?: number;
  completion_percentage?: number;
  error_count?: number;
}

export interface DashboardData {
  activeFlows: FlowSummary[];
  systemMetrics: {
    total_flows: number;
    active_flows: number;
    completed_flows: number;
    error_flows: number;
  };
  crewPerformance: CrewPerformanceMetric[];
  platformAlerts: PlatformAlert[];
}

/**
 * Unified hook for fetching dashboard data with React Query
 * Replaces the dashboardService to prevent duplicate API calls
 */
export const useDashboardData = (): JSX.Element => {
  const { user, client, engagement, getAuthHeaders } = useAuth();

  return useQuery({
    queryKey: ['dashboard-data', user?.id, client?.id, engagement?.id],
    queryFn: async (): Promise<DashboardData> => {
      // Fetch discovery flows and latest import in parallel but through React Query
      const [discoveryFlowsResponse, dataImportsResponse] = await Promise.allSettled([
        // Get active Discovery flows
        apiCall('/api/v1/unified-discovery/flows/active', {
          method: 'GET',
          headers: getAuthHeaders({ user, client, engagement })
        }),

        // Get latest import data
        apiCall('/api/v1/data-import/latest-import', {
          method: 'GET',
          headers: getAuthHeaders({ user, client, engagement })
        })
      ]);

      // Process discovery flows
      let allFlows: FlowSummary[] = [];
      if (discoveryFlowsResponse.status === 'fulfilled') {
        const flowsData = discoveryFlowsResponse.value;
        if (Array.isArray(flowsData)) {
          allFlows = flowsData.map((flow: FlowSummary & Record<string, unknown>) => ({
            flow_id: flow.flow_id,
            status: flow.status,
            type: flow.type || 'discovery',
            current_phase: flow.current_phase,
            created_at: flow.created_at,
            progress: flow.progress || 0,
            completion_percentage: flow.completion_percentage || 0,
            error_count: flow.error_count || 0
          }));
        }
      }

      // Calculate system metrics
      const systemMetrics = {
        total_flows: allFlows.length,
        active_flows: allFlows.filter(f => ['in_progress', 'waiting_for_approval'].includes(f.status)).length,
        completed_flows: allFlows.filter(f => f.status === 'completed').length,
        error_flows: allFlows.filter(f => f.status === 'error').length
      };

      return {
        activeFlows: allFlows,
        systemMetrics,
        crewPerformance: [], // TODO: Implement if needed
        platformAlerts: []   // TODO: Implement if needed
      };
    },
    enabled: !!(user?.id && client?.id && engagement?.id),
    staleTime: 30 * 1000, // Consider fresh for 30 seconds
    cacheTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
    retry: (failureCount, error: Error | unknown) => {
      // Don't retry on 429 or auth errors
      if (error && typeof error === 'object' && 'status' in error &&
          (error.status === 429 || error.status === 401 || error.status === 403)) {
        return false;
      }
      return failureCount < 2;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000),
  });
};
