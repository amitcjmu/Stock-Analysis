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
import { collectionFlowApi, TransitionResult } from '@/services/api/collection-flow';
import { useToast } from '@/components/ui/use-toast';


/**
 * Collection Progress Monitoring page
 * Refactored to use modular components and custom hooks for better maintainability
 * Phase 1 Fix: Added assessment CTA for completed flows to prevent endless loop
 */
const CollectionProgress: React.FC = () => {
  const navigate = useNavigate();
  const { flowId: flowIdParam } = useParams<{ flowId: string }>();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  // Get specific flow ID from URL params or search params
  const flowId = flowIdParam || searchParams.get('flowId');

  // Phase 3: Transition state management
  const [isTransitioning, setIsTransitioning] = React.useState(false);

  // Use the progress monitoring hook for all state management
  const {
    flows,
    metrics,
    selectedFlow,
    isLoading,
    error,
    autoRefresh,
    readiness,
    showAssessmentCTA, // Phase 1 fix: Get assessment CTA state
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

  // Phase 1 fix: Get the current flow for assessment readiness check
  const currentFlow = flows.find(f => f.id === selectedFlow);

  // Phase 3: Enhanced transition handler with proper error handling
  const handleTransitionToAssessment = async () => {
    try {
      setIsTransitioning(true);

      // Call dedicated transition endpoint
      const result = await collectionFlowApi.transitionToAssessment(selectedFlow!);

      toast({
        title: 'Transition Successful',
        description: 'Assessment flow created successfully. Redirecting to assessment...',
        variant: 'default',
      });

      // Navigate to EXISTING assessment route
      navigate(`/assessment/${result.assessment_flow_id}/architecture`);

    } catch (error: any) {
      if (error?.response?.data?.error === 'not_ready') {
        // Show specific missing requirements using toast
        toast({
          title: 'Not Ready for Assessment',
          description: error.response.data.reason,
          variant: 'destructive',
        });

        // Log missing requirements for debugging
        console.warn('Missing requirements:', error.response.data.missing_requirements);
      } else {
        // Generic error handling with toast
        toast({
          title: 'Transition Failed',
          description: error?.message || 'Failed to transition to assessment',
          variant: 'destructive',
        });
      }
    } finally {
      setIsTransitioning(false);
    }
  };

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

  // Phase 1 fix: Show assessment CTA for completed flows
  if (showAssessmentCTA || currentFlow?.assessment_ready || currentFlow?.status === 'completed') {
    return (
      <CollectionPageLayout
        title="Collection Progress Monitor"
        description="Data collection completed - ready for assessment"
      >
        <div className="flex items-center justify-center min-h-64">
          <div className="text-center max-w-md">
            <div className="p-6 bg-green-50 border-l-4 border-green-500 rounded-r-lg">
              <div className="flex items-center justify-center mb-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              <h3 className="text-lg font-medium text-green-800 mb-2">
                Collection Complete
              </h3>
              <p className="text-green-700 mb-6">
                Data collection is complete. Proceed to assessment phase to analyze your applications and infrastructure.
              </p>

              <div className="space-y-3">
                <Button
                  onClick={handleTransitionToAssessment} // Phase 3: Use enhanced transition
                  disabled={isTransitioning || !selectedFlow}
                  className="w-full bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                  size="lg"
                >
                  {isTransitioning ? 'Creating Assessment...' : 'Start Assessment Phase'}
                </Button>

                <Button
                  onClick={refreshData}
                  variant="outline"
                  className="w-full border-green-200 text-green-700 hover:bg-green-50"
                  size="sm"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh Status
                </Button>
              </div>

              {/* Show collection summary if available */}
              {currentFlow && (
                <div className="mt-6 p-4 bg-white rounded-lg border border-green-200">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Collection Summary</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Applications:</span>
                      <span className="ml-2 font-medium">{currentFlow.completed_applications}/{currentFlow.application_count}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Progress:</span>
                      <span className="ml-2 font-medium">{currentFlow.progress}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </CollectionPageLayout>
    );
  }

  // Main component render for incomplete flows
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
