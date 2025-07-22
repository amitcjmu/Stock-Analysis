/**
 * Agent Performance Types
 * Type definitions for agent observability API responses
 * Part of the Agent Observability Enhancement Phase 3
 */

// Base types
export interface AgentPerformanceSummary {
  agent_name: string;
  period_days: number;
  summary: {
    total_tasks: number;
    successful_tasks: number;
    failed_tasks: number;
    success_rate: number;
    avg_duration_seconds: number;
    avg_confidence_score: number;
    total_llm_calls: number;
    total_thinking_phases: number;
  };
  token_usage: {
    total_input_tokens: number;
    total_output_tokens: number;
    total_tokens: number;
    avg_tokens_per_task: number;
  };
  error_patterns: Array<{
    error_type: string;
    count: number;
  }>;
  trends: {
    dates: string[];
    success_rates: number[];
    avg_durations: number[];
    task_counts: number[];
    confidence_scores: number[];
  };
  current_status?: {
    is_active: boolean;
    active_tasks: unknown[];
    last_activity: string;
  };
}

export interface AgentTask {
  id: string;
  agent_name: string;
  task_description: string;
  status: 'completed' | 'failed' | 'timeout';
  success: boolean;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  confidence_score?: number;
  llm_calls_count: number;
  thinking_phases_count: number;
  token_usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  error_message?: string;
  memory_usage_mb?: number;
  flow_id?: string;
  crew_name?: string;
  created_at: string;
  updated_at: string;
}

export interface AgentTaskHistory {
  agent_name: string;
  total_tasks: number;
  limit: number;
  offset: number;
  tasks: AgentTask[];
}

export interface AgentAnalytics {
  agent_name: string;
  period_days: number;
  analytics: {
    performance_distribution: {
      duration_percentiles: {
        p25?: number;
        p50?: number;
        p75?: number;
        p90?: number;
        p95?: number;
        p99?: number;
      };
      status_distribution: {
        [status: string]: number;
      };
    };
    resource_usage: {
      avg_memory_usage_mb: number;
      peak_memory_usage_mb: number;
      llm_call_distribution: {
        [bucket: string]: number;
      };
    };
    pattern_discovery: {
      total_patterns_discovered: number;
      pattern_types: {
        [type: string]: number;
      };
      total_pattern_references: number;
      high_confidence_patterns: number;
      avg_confidence_score: number;
    };
    task_complexity: {
      complexity_distribution: {
        simple: number;
        moderate: number;
        complex: number;
        very_complex: number;
      };
      avg_thinking_phases_per_task: number;
    };
  };
  performance_trends?: {
    agent_name: string;
    period_days: number;
    daily_metrics: Array<{
      date: string;
      tasks_attempted: number;
      tasks_completed: number;
      tasks_failed: number;
      success_rate: number;
      avg_duration_seconds?: number;
      avg_confidence_score?: number;
      total_llm_calls: number;
      total_tokens_used: number;
    }>;
    overall_stats: {
      total_tasks_attempted: number;
      total_tasks_completed: number;
      overall_success_rate: number;
      avg_daily_tasks: number;
      total_llm_calls: number;
      total_tokens_used: number;
    };
  };
}

export interface AgentActivity {
  id: string;
  type: 'task_active' | 'task_completed';
  agent: string;
  task: string;
  status: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  success?: boolean;
  confidence_score?: number;
  details: unknown;
}

export interface AgentActivityFeed {
  activities: AgentActivity[];
  total_activities: number;
  monitoring_active: boolean;
  filters: {
    agent?: string;
    include_completed: boolean;
    limit: number;
  };
}

export interface DiscoveredPattern {
  id: string;
  pattern_type: string;
  pattern_name: string;
  description: string;
  metadata: unknown;
  confidence_score: number;
  times_referenced: number;
  discovered_by_agent: string;
  discovered_at: string;
  last_referenced_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AllAgentsSummary {
  period_days: number;
  agents: Array<{
    agent_name: string;
    total_tasks: number;
    total_completed: number;
    avg_success_rate: number;
    avg_duration_seconds?: number;
    total_llm_calls: number;
    is_active?: boolean;
  }>;
  total_agents: number;
  active_agents: number;
}

// API Response types
export interface AgentPerformanceResponse {
  success: boolean;
  timestamp: string;
  data: AgentPerformanceSummary;
}

export interface AgentTaskHistoryResponse {
  success: boolean;
  timestamp: string;
  data: AgentTaskHistory;
}

export interface AgentAnalyticsResponse {
  success: boolean;
  timestamp: string;
  data: AgentAnalytics;
}

export interface AgentActivityFeedResponse {
  success: boolean;
  timestamp: string;
  data: AgentActivityFeed;
}

export interface DiscoveredPatternsResponse {
  success: boolean;
  timestamp: string;
  data: {
    patterns: DiscoveredPattern[];
    total_patterns: number;
    filters: {
      agent_name?: string;
      pattern_type?: string;
      min_confidence: number;
    };
  };
}

export interface AllAgentsSummaryResponse {
  success: boolean;
  timestamp: string;
  data: AllAgentsSummary;
}

// Enhanced monitoring status with individual agent data
export interface EnhancedMonitoringStatus {
  success: boolean;
  timestamp: string;
  monitoring: {
    active: boolean;
    active_tasks: number;
    completed_tasks: number;
    hanging_tasks: number;
  };
  agents: {
    total_registered: number;
    active_agents: number;
    learning_enabled: number;
    cross_page_communication: number;
    modular_handlers: number;
    phase_distribution: {
      [phase: string]: number;
    };
    capabilities: unknown;
    system_status: unknown;
  };
  tasks: {
    active: unknown[];
    hanging: unknown[];
  };
  registry_status: unknown;
  individual_agent_performance?: {
    period_days: number;
    agents: Array<{
      agent_name: string;
      total_tasks: number;
      total_completed: number;
      avg_success_rate: number;
      avg_duration_seconds?: number;
      total_llm_calls: number;
      is_active?: boolean;
    }>;
    data_source: string;
  };
}