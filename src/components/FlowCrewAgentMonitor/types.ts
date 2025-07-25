// TypeScript interfaces for Flow Crew Agent Monitor
export type FlowStatus = 'running' | 'completed' | 'failed' | 'pending' | 'paused';
export type CrewStatus = 'active' | 'completed' | 'failed' | 'pending' | 'paused';
export type AgentStatus = 'active' | 'idle' | 'error' | 'completed' | 'paused';

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  current_task: string;
  performance: {
    success_rate: number;
    tasks_completed: number;
    avg_response_time: number;
  };
  collaboration: {
    is_collaborating: boolean;
    collaboration_partner?: string;
    shared_memory_access: boolean;
  };
  last_activity: string;
}

export interface Crew {
  id: string;
  name: string;
  manager: string;
  status: CrewStatus;
  progress: number;
  agents: Agent[];
  current_phase: string;
  started_at: string;
  estimated_completion?: string;
  collaboration_metrics: {
    internal_effectiveness: number;
    cross_crew_sharing: number;
    memory_utilization: number;
  };
}

export interface DiscoveryFlow {
  flow_id: string;
  status: FlowStatus;
  current_phase: string;
  progress: number;
  crews: Crew[];
  started_at: string;
  estimated_completion?: string;
  performance_metrics: {
    overall_efficiency: number;
    crew_coordination: number;
    agent_collaboration: number;
  };
  events_count: number;
  last_event: string;
}

export interface FlowCrewAgentData {
  active_flows: DiscoveryFlow[];
  system_health: {
    status: string;
    total_flows: number;
    active_crews: number;
    active_agents: number;
    event_listener_active: boolean;
  };
  performance_summary: {
    avg_flow_efficiency: number;
    total_tasks_completed: number;
    success_rate: number;
    collaboration_effectiveness: number;
  };
}

export interface AgentMonitorState {
  data: FlowCrewAgentData | null;
  isLoading: boolean;
  error: string | null;
  activeTab: string;
  selectedFlow: string | null;
  refreshing: boolean;
  isStartingFlow: boolean;
  usePhase2Monitor: boolean;
  discoveryFlows: DiscoveryFlow[];
}
