// Main exports for EnhancedDiscoveryDashboard module
export { default } from './index';

// Hook exports
export { useDashboard } from './hooks/useDashboard';
export { useFlowMetrics } from './hooks/useFlowMetrics';
export { useDashboardFilters } from './hooks/useDashboardFilters';

// Component exports
export { DashboardHeader } from './components/DashboardHeader';
export { FlowsOverview } from './components/FlowsOverview';
export { MetricsPanel } from './components/MetricsPanel';
export { ActivityTimeline } from './components/ActivityTimeline';
export { QuickActions } from './components/QuickActions';

// Service exports
export { dashboardService } from './services/dashboardService';

// Type exports
export type {
  FlowSummary,
  SystemMetrics,
  CrewPerformanceMetrics,
  PlatformAlert,
  DashboardState,
  DashboardFilters
} from './types';
