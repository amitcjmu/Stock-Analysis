import React from 'react';
import { useParams, useSearchParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, RefreshCw } from 'lucide-react';

// Import modular components
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import ProgressMonitorContainer from '@/components/collection/progress/ProgressMonitorContainer';
import { Button } from '@/components/ui/button';

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
    error,
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
    refreshInterval: 30000 // Reduced from 3 seconds to 30 seconds to prevent spam
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

  // Show error state if data loading failed
  if (error) {
    return (
      <CollectionPageLayout
        title="Collection Progress Monitor"
        description="Error loading collection workflow data"
      >
        <div className="flex items-center justify-center min-h-64">
          <div className="text-center max-w-md">
            <div className="p-6 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
              <div className="flex items-center justify-center mb-4">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>
              <h3 className="text-lg font-medium text-red-800 mb-2">
                Failed to Load Collection Data
              </h3>
              <p className="text-red-700 mb-4">
                {error instanceof Error
                  ? error.message
                  : typeof error === 'string'
                  ? error
                  : 'Unable to load collection flow data. This may be due to a context extraction error or connection issue.'}
              </p>
              <Button
                onClick={refreshData}
                variant="outline"
                className="border-red-200 text-red-700 hover:bg-red-50"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry Loading
              </Button>
            </div>
          </div>
        </div>
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
