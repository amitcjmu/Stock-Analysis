import React from 'react';
import { useParams, useSearchParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'

// Import modular components
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import ProgressMonitorContainer from '@/components/collection/progress/ProgressMonitorContainer';

// Import custom hooks
import { useProgressMonitoring, getFlowMilestones } from '@/hooks/collection/useProgressMonitoring';


/**
 * Collection Progress Monitoring page
 * Refactored to use modular components and custom hooks for better maintainability
 */
const CollectionProgress: React.FC = () => {
  const navigate = useNavigate();
  const { flowId: flowIdParam } = useParams<{ flowId: string }>();
  const [searchParams] = useSearchParams();

  // Get specific flow ID from URL params or search params
  const flowId = flowIdParam || searchParams.get('flowId');

  // Use the progress monitoring hook for all state management
  const {
    flows,
    metrics,
    selectedFlow,
    isLoading,
    autoRefresh,
    readiness,
    selectFlow,
    handleFlowAction,
    refreshData,
    exportReport,
    toggleAutoRefresh
  } = useProgressMonitoring({
    flowId,
    autoRefresh: true,
    refreshInterval: 3000
  });



  // Show loading state while data is being fetched
  if (isLoading) {
    return (
      <CollectionPageLayout
        title="Collection Progress Monitor"
        description="Loading collection workflow data"
        isLoading={true}
        loadingMessage="Loading collection progress..."
      >
        {/* Loading content handled by layout */}
      </CollectionPageLayout>
    );
  }

  // Main component render
  return (
    <CollectionPageLayout
      title="Collection Progress Monitor"
      description="Real-time monitoring of collection workflows and progress"
    >
      <ProgressMonitorContainer
        flows={flows}
        metrics={metrics}
        selectedFlow={selectedFlow}
        autoRefresh={autoRefresh}
        readiness={readiness || undefined}
        onFlowSelect={selectFlow}
        onFlowAction={handleFlowAction}
        onToggleAutoRefresh={toggleAutoRefresh}
        onExportReport={exportReport}
        getFlowMilestones={getFlowMilestones}
      />
    </CollectionPageLayout>
  );
};

export default CollectionProgress;
