import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/config/api';
import { useAuth } from '@/contexts/AuthContext';

export interface AgentStatus {
  id: string;
  name: string;
  status: 'Active' | 'Idle' | 'Error' | 'Offline';
  last_active: string;
  current_task?: string;
  performance: {
    success_rate: number;
    avg_response_time: number;
    tasks_completed: number;
  };
  memory_usage: {
    current: number;
    peak: number;
  };
}

export interface AgentMetrics {
  total_agents: number;
  active_agents: number;
  total_tasks_completed: number;
  average_success_rate: number;
  system_health: {
    status: 'Healthy' | 'Warning' | 'Critical';
    issues: string[];
  };
}

export interface AgentMonitorData {
  agents: AgentStatus[];
  metrics: AgentMetrics;
  recent_activities: Array<{
    agent_id: string;
    agent_name: string;
    action: string;
    timestamp: string;
    status: 'Success' | 'Failed' | 'In Progress';
  }>;
}

export const useAgentMonitor = (options: { enabled?: boolean; polling?: boolean } = {}) => {
  const { getAuthHeaders } = useAuth();
  const { enabled = true, polling = false } = options;

  return useQuery<AgentMonitorData>({
    queryKey: ['agent-monitor'],
    queryFn: async () => {
      const response = await apiCall('agents/monitor', {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return response;
    },
    enabled,
    staleTime: 60 * 1000, // 1 minute - much longer stale time
    refetchInterval: polling ? 30 * 1000 : false, // Poll every 30 seconds only if explicitly enabled
    refetchOnWindowFocus: false, // Disable focus refetching
    refetchOnMount: false, // Only fetch on first mount
    refetchOnReconnect: false, // Don't refetch on network reconnect
    retry: 1, // Minimal retries
    retryDelay: 3000 // 3 second delay between retries
  });
};
