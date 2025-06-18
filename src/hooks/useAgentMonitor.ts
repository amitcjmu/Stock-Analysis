import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/lib/api';
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

export const useAgentMonitor = () => {
  const { getAuthHeaders } = useAuth();

  return useQuery<AgentMonitorData>({
    queryKey: ['agent-monitor'],
    queryFn: async () => {
      const response = await apiCall('agents/monitor', {
        method: 'GET',
        headers: getAuthHeaders()
      });
      return response;
    },
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: 10 * 1000, // Poll every 10 seconds
    refetchOnWindowFocus: true
  });
}; 