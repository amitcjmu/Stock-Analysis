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

// Hooks - Original
export {
  useResponsiveLayout,
  useGridLayout,
  useComponentVisibility
} from './hooks/useResponsiveLayout';

// Hooks - New Modular
export {
  useAgentData,
  useAgentPerformance,
  useAgentAnalytics
} from './hooks/useAgentData';
export { useAgentComparison } from './hooks/useAgentComparison';
export { useRecommendations } from './hooks/useRecommendations';
export { useAgentFilters } from './hooks/useAgentFilters';

// Context
export { ObservabilityProvider } from './context/ObservabilityContext';
export {
  useObservability,
  useAgentSelection,
  useViewPreferences
} from './context/hooks';

// Utilities
export * from './utils/constants';
export * from './utils/formatters';

// Sub-components - Agent Comparison
export { MetricCard } from './comparison/MetricCard';
export { AgentSelector } from './comparison/AgentSelector';
export { RankingsOverview } from './comparison/RankingsOverview';
export { SuccessRateTrendChart, PerformanceRadarChart } from './comparison/ComparisonCharts';

// Sub-components - Recommendations
export { RecommendationCard } from './recommendations/RecommendationCard';

// Sub-components - Overview
export { FilterControls } from './overview/FilterControls';
export { AgentSummaryFooter } from './overview/AgentSummaryFooter';

// Reusable UI Components
export { MetricCard as MetricDisplayCard, MetricBadge, MetricComparison } from './ui/MetricDisplay';
export { StatusBadge, StatusGroup } from './ui/StatusDisplay';

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
export type { RecommendationEngineProps } from './RecommendationEngine';
export type { AdvancedAnalyticsProps, AnalyticsData } from './AdvancedAnalytics';

// New Types
export type { Recommendation } from './recommendations/RecommendationCard';
export type { UseAgentDataOptions, UseAgentDataReturn } from './hooks/useAgentData';
export type { UseRecommendationsOptions } from './hooks/useRecommendations';
export type { AgentFilters } from './hooks/useAgentFilters';
export type { MetricCardProps, MetricBadgeProps, MetricComparisonProps } from './ui/MetricDisplay';
export type { StatusBadgeProps, StatusGroupProps, StatusType } from './ui/StatusDisplay';
