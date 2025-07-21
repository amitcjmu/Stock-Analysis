/**
 * Observability Components Index
 * Export all agent observability components
 * Part of the Agent Observability Enhancement Phases 4A & 4B
 */

// Phase 4A Core Components
// Status Indicators
export { default as AgentStatusIndicator, AgentOnlineIndicator, AgentStatusGroup } from './AgentStatusIndicator';

// Performance Cards
export { 
  default as AgentPerformanceCard, 
  AgentPerformanceCardCompact, 
  AgentPerformanceCardDetailed 
} from './AgentPerformanceCard';

// Metrics and Charts
export { 
  default as AgentMetricsChart,
  default as AgentMetricsDashboard,
  SparklineChart,
  PerformanceDistributionChart,
  SuccessRateGauge
} from './AgentMetricsChart';

// Main Overview Components
export { default as AgentListOverview } from './AgentListOverview';
export { default as ResponsiveAgentListOverview } from './ResponsiveAgentListOverview';

// Error Handling Components
export { 
  ObservabilityErrorBoundary, 
  LoadingError, 
  NetworkError 
} from './ErrorBoundary';

// Loading State Components
export { 
  default as LoadingSpinner,
  AgentCardSkeleton,
  AgentListSkeleton,
  MetricsChartSkeleton,
  PulsingLoader,
  AgentOverviewLoading,
  ProgressiveLoader,
  EmptyState
} from './LoadingStates';

// Phase 4B Advanced Components
// Activity Feed
export { 
  default as ActivityFeed, 
  ActivityEventRow, 
  ActivityEventIcon 
} from './ActivityFeed';

// Agent Comparison
export { default as AgentComparison } from './AgentComparison';

// Recommendation Engine
export { default as RecommendationEngine } from './RecommendationEngine';

// Advanced Analytics
export { default as AdvancedAnalytics } from './AdvancedAnalytics';

// Hooks
export { 
  useResponsiveLayout, 
  useGridLayout, 
  useComponentVisibility 
} from './hooks/useResponsiveLayout';

// Re-export types for convenience
export type {
  AgentCardData,
  AgentMetricsData,
  StatusIndicatorProps,
  PerformanceCardProps,
  MetricsChartProps,
  AgentListOverviewProps,
  SparklineData,
  ChartDataPoint,
  LoadingState,
  ErrorState
} from '../../types/api/observability/agent-performance';

// Phase 4B Advanced Component Types
export type { ActivityEvent, ActivityFeedProps, ActivityFilters } from './ActivityFeed';
export type { AgentComparisonProps, AgentComparisonData } from './AgentComparison';
export type { RecommendationEngineProps, Recommendation } from './RecommendationEngine';
export type { AdvancedAnalyticsProps, AnalyticsData } from './AdvancedAnalytics';