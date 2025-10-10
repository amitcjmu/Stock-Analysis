/**
 * Collection Progress Components Index
 *
 * Exports for progress monitoring components.
 * Updated with redesigned components for better UX.
 */

// Metrics
export { default as FlowMetricsGrid } from './FlowMetricsGrid';
export type { FlowMetricsGridProps, FlowMetrics } from './FlowMetricsGrid';

// Legacy components (kept for backward compatibility)
export { default as FlowListSidebar } from './FlowListSidebar';
export type { FlowListSidebarProps } from './FlowListSidebar';

export { default as FlowDetailsCard } from './FlowDetailsCard';
export type { FlowDetailsCardProps } from './FlowDetailsCard';

// Enhanced components (new)
export { default as EnhancedFlowList } from './EnhancedFlowList';
export type { EnhancedFlowListProps } from './EnhancedFlowList';

export { default as PhaseTimeline } from './PhaseTimeline';
export type { PhaseTimelineProps, PhaseInfo } from './PhaseTimeline';

export { default as TabbedFlowDetails } from './TabbedFlowDetails';
export type { TabbedFlowDetailsProps } from './TabbedFlowDetails';

// Container
export { default as ProgressMonitorContainer } from './ProgressMonitorContainer';
export type { ProgressMonitorContainerProps } from './ProgressMonitorContainer';

// Re-export common types
export type { CollectionFlow } from './EnhancedFlowList';
