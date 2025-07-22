/**
 * Agent Performance Types for UI Components
 * Type definitions for agent observability dashboard components
 * Part of the Agent Observability Enhancement Phase 4A
 */

import { PrimitiveValue } from '../shared/value-types';

// Re-export existing agent performance types
export * from '../../agent-performance';

// Additional UI-specific types for components
export interface AgentCardData {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error' | 'offline';
  lastActive: string;
  successRate: number;
  totalTasks: number;
  avgDuration: number;
  isOnline: boolean;
}

export interface AgentMetricsData {
  agentName: string;
  metrics: {
    successRate: number;
    totalTasks: number;
    completedTasks: number;
    failedTasks: number;
    avgDuration: number;
    lastActive: string;
    confidence: number;
    memoryUsage?: number;
    llmCalls: number;
  };
  trends: {
    successRateHistory: number[];
    durationHistory: number[];
    taskCountHistory: number[];
    timestamps: string[];
  };
  status: {
    current: 'active' | 'idle' | 'error' | 'offline';
    isHealthy: boolean;
    lastHealthCheck: string;
  };
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface SparklineData {
  data: ChartDataPoint[];
  color: string;
  trend: 'up' | 'down' | 'stable';
  changePercent: number;
}

export interface StatusIndicatorConfig {
  status: 'active' | 'idle' | 'error' | 'offline';
  variant: 'dot' | 'badge' | 'icon';
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
}

export interface AgentListFilters {
  status?: ('active' | 'idle' | 'error' | 'offline')[];
  sortBy?: 'name' | 'successRate' | 'lastActive' | 'totalTasks';
  sortOrder?: 'asc' | 'desc';
  searchQuery?: string;
}

export interface AgentListState {
  agents: AgentCardData[];
  filteredAgents: AgentCardData[];
  loading: boolean;
  error: string | null;
  selectedAgentId: string | null;
  filters: AgentListFilters;
  refreshing: boolean;
}

export interface PerformanceCardProps {
  agent: AgentCardData;
  detailed?: boolean;
  showChart?: boolean;
  onClick?: (agent: AgentCardData) => void;
  className?: string;
}

export interface MetricsChartProps {
  data: SparklineData;
  title: string;
  height?: number;
  showGrid?: boolean;
  animate?: boolean;
}

export interface StatusIndicatorProps extends StatusIndicatorConfig {
  className?: string;
  onClick?: () => void;
}

export interface AgentListOverviewProps {
  refreshInterval?: number;
  maxAgents?: number;
  showFilters?: boolean;
  compactView?: boolean;
  onAgentSelect?: (agent: AgentCardData) => void;
  className?: string;
}

// Real-time update types
export interface RealTimeUpdate {
  type: 'agent_status' | 'task_completed' | 'task_started' | 'agent_error';
  agentName: string;
  timestamp: string;
  data: {
    taskId?: string;
    taskName?: string;
    status?: string;
    duration?: number;
    error?: string;
    result?: PrimitiveValue | Record<string, PrimitiveValue>;
  };
}

export interface RealTimeConfig {
  enabled: boolean;
  interval: number;
  maxUpdatesPerSecond: number;
  bufferSize: number;
}

// Loading and error states
export interface LoadingState {
  isLoading: boolean;
  loadingText?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  error: Error | null;
  errorMessage?: string;
  retryCount: number;
  canRetry: boolean;
}

// Pagination and data management
export interface PaginationConfig {
  page: number;
  pageSize: number;
  totalItems: number;
  showPageSizeSelector?: boolean;
}

export interface DataRefreshConfig {
  autoRefresh: boolean;
  refreshInterval: number;
  lastRefresh: string;
  canManualRefresh: boolean;
}