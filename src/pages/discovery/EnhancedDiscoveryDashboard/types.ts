// TypeScript interfaces for Enhanced Discovery Dashboard
export interface FlowSummary {
  flow_id: string;
  // session_id removed - use flow_id only
  engagement_name: string;
  engagement_id: string;
  client_name: string;
  client_id: string;
  status: 'running' | 'active' | 'completed' | 'failed' | 'paused' | 'not_found';
  progress: number;
  current_phase: string;
  started_at: string;
  estimated_completion?: string;
  last_updated?: string;
  crew_count: number;
  active_agents: number;
  data_sources: number;
  success_criteria_met: number;
  total_success_criteria: number;
  flow_type: 'discovery' | 'assessment' | 'planning' | 'execution';
}

export interface SystemMetrics {
  total_active_flows: number;
  total_agents: number;
  memory_utilization_gb: number;
  total_memory_gb: number;
  collaboration_events_today: number;
  success_rate: number;
  avg_completion_time_hours: number;
  knowledge_bases_loaded: number;
}

export interface CrewPerformanceMetrics {
  crew_name: string;
  total_executions: number;
  success_rate: number;
  avg_duration_minutes: number;
  collaboration_score: number;
  efficiency_trend: number;
  current_active: number;
}

export interface PlatformAlert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  flow_id?: string;
  action_required: boolean;
}

export interface DashboardState {
  currentFlow: unknown;
  flowLoading: boolean;
  flowError: unknown;
  isHealthy: boolean;
  activeFlows: FlowSummary[];
  systemMetrics: SystemMetrics | null;
  crewPerformance: CrewPerformanceMetrics[];
  platformAlerts: PlatformAlert[];
  selectedTimeRange: string;
  isLoading: boolean;
  lastUpdated: Date;
  error: string | null;
  showIncompleteFlowManager: boolean;
  selectedFlowForStatus: string | null;
}

export interface DashboardFilters {
  timeRange: string;
  status: string[];
  flowType: string[];
  searchQuery: string;
}
