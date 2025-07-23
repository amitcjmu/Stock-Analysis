import React from 'react'
import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query';
import { toast } from '@/components/ui/use-toast';

// Import modular components
import type CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import AdaptiveFormContainer from '@/components/collection/forms/AdaptiveFormContainer';
import { CollectionUploadBlocker } from '@/components/collection/CollectionUploadBlocker';

// Import custom hooks
import { useAdaptiveFormFlow } from '@/hooks/collection/useAdaptiveFormFlow';
import { useIncompleteCollectionFlows, useCollectionFlowManagement } from '@/hooks/collection/useCollectionFlowManagement';

// Import types
import type { ProgressMilestone } from '@/components/collection/types';

// Import UI components
import { Button } from '@/components/ui/button';

/**
 * Adaptive Forms collection page
 * Refactored to use modular components and custom hooks for better maintainability
 */
const AdaptiveForms: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  // Get application ID and flow ID from URL params
  const applicationId = searchParams.get('applicationId');
  const flowId = searchParams.get('flowId');

  // State to track flows being deleted
  const [deletingFlows, setDeletingFlows] = useState<Set<string>>(new Set());
  const [hasJustDeleted, setHasJustDeleted] = useState(false);
  
  // Check for incomplete flows that would block new collection processes
  const { 
    data: incompleteFlows = [], 
    isLoading: checkingFlows, 
    refetch: refetchFlows 
  } = useIncompleteCollectionFlows();
  
  // Filter out the current flow and flows being deleted from the blocking check
  const blockingFlows = incompleteFlows.filter(flow => {
    const id = flow.flow_id || flow.id;
    return id !== flowId && !deletingFlows.has(id);
  });
  
  const hasBlockingFlows = blockingFlows.length > 0;

  // Use collection flow management hook for flow operations
  const { deleteFlow, isDeleting } = useCollectionFlowManagement();

  // Use the adaptive form flow hook for all flow management
  const {
    formData,
    formValues,
    validation,
    isLoading,
    isSaving,
    error,
    handleFieldChange,
    handleValidationChange,
    handleSave,
    handleSubmit,
    initializeFlow
  } = useAdaptiveFormFlow({
    applicationId,
    flowId,
    autoInitialize: !checkingFlows && (!hasBlockingFlows || hasJustDeleted)
  });

  // Flow management handlers for incomplete flows
  const handleContinueFlow = async (flowId: string) => {
    try {
      // Navigate to appropriate collection phase
      navigate(`/collection/progress/${flowId}`);
    } catch (error) {
      console.error('Failed to continue collection flow:', error);
    }
  };

  const handleDeleteFlow = async (flowId: string) => {
    // Mark this flow as being deleted to hide it from UI immediately
    setDeletingFlows(prev => new Set(prev).add(flowId));
    
    try {
      // Force delete the flow since it's stuck
      await deleteFlow(flowId, true);
      
      // Wait a bit for backend to process
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Manually invalidate and refetch the specific query
      await queryClient.invalidateQueries({ 
        queryKey: ['collection-flows', 'incomplete'],
        exact: true 
      });
      
      // Also refetch to ensure UI updates
      await refetchFlows();
      
      // Mark that we just deleted a flow to trigger re-initialization
      setHasJustDeleted(true);
      
    } catch (error: unknown) {
      console.error('Failed to delete collection flow:', error);
      
      // If deletion failed, remove from deleting set to show it again
      setDeletingFlows(prev => {
        const newSet = new Set(prev);
        newSet.delete(flowId);
        return newSet;
      });
      
      // Show error toast if it's not a 404 (which means it was already deleted)
      if (error?.status !== 404) {
        toast({
          title: 'Delete Failed',
          description: error?.message || 'Failed to delete collection flow',
          variant: 'destructive'
        });
      }
    }
  };

  const handleViewFlowDetails = (flowId: string, phase: string) => {
    navigate(`/collection/progress/${flowId}`);
  };

  const handleManageFlows = () => {
    navigate('/collection/management');
  };

  // Mock progress milestones - in a real implementation these would be dynamic
  const progressMilestones: ProgressMilestone[] = [
    {
      id: 'form-start',
      title: 'Form Started',
      description: 'Begin adaptive data collection',
      achieved: true,
      achievedAt: new Date().toISOString(),
      weight: 0.1,
      required: true
    },
    {
      id: 'basic-complete',
      title: 'Basic Information',
      description: 'Complete core application details',
      achieved: false,
      weight: 0.3,
      required: true
    },
    {
      id: 'technical-complete',
      title: 'Technical Details',
      description: 'Complete technical architecture information',
      achieved: false,
      weight: 0.4,
      required: true
    },
    {
      id: 'validation-passed',
      title: 'Validation Passed',
      description: 'All validation checks completed successfully',
      achieved: false,
      weight: 0.2,
      required: true
    }
  ];

  // Reset the hasJustDeleted flag after auto-initialization triggers
  React.useEffect(() => {
    if (hasJustDeleted && !hasBlockingFlows && !checkingFlows) {
      // Give a small delay to ensure state updates have propagated
      const timer = setTimeout(() => {
        setHasJustDeleted(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [hasJustDeleted, hasBlockingFlows, checkingFlows]);


  // Show loading state while checking for incomplete flows
  if (checkingFlows) {
    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Initializing collection workflow"
        isLoading={true}
        loadingMessage="Checking for existing collection flows..."
        loadingSubMessage="Validating workflow state"
      >
        {/* Loading content handled by layout */}
      </CollectionPageLayout>
    );
  }

  // Show blocker if there are other incomplete flows (not including current one)
  if (hasBlockingFlows) {
    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Collection workflow blocked - manage existing flows"
      >
        <CollectionUploadBlocker
          incompleteFlows={blockingFlows}
          onContinueFlow={handleContinueFlow}
          onDeleteFlow={handleDeleteFlow}
          onViewDetails={handleViewFlowDetails}
          onManageFlows={handleManageFlows}
          onRefresh={refetchFlows}
          isLoading={isDeleting}
        />
      </CollectionPageLayout>
    );
  }

  // Show loading state while form data is being generated
  if (!formData && !hasBlockingFlows) {
    // Check if there's an error
    if (error) {
      return (
        <CollectionPageLayout
          title="Adaptive Data Collection"
          description="Error initializing collection form"
        >
          <div className="max-w-2xl mx-auto mt-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-red-800 mb-2">Collection Flow Error</h3>
              <p className="text-red-700 mb-4">{error.message}</p>
              
              {error.message?.includes('Multiple active collection flows') && (
                <div className="mt-4">
                  <p className="text-sm text-red-600 mb-3">
                    Multiple active flows detected. Please delete existing flows before proceeding.
                  </p>
                  <Button 
                    onClick={() => navigate('/collection/flow-management')} 
                    variant="outline"
                    className="mr-2"
                  >
                    Manage Flows
                  </Button>
                  <Button onClick={() => window.location.reload()} variant="outline">
                    Refresh Page
                  </Button>
                </div>
              )}
              
              {!error.message?.includes('Multiple active collection flows') && (
                <Button onClick={() => initializeFlow()} className="mt-4">
                  Retry
                </Button>
              )}
            </div>
          </div>
        </CollectionPageLayout>
      );
    }
    
    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Generating personalized collection form"
        isLoading={isLoading}
        loadingMessage={isLoading ? "CrewAI agents are analyzing your requirements..." : "Preparing collection form..."}
        loadingSubMessage={isLoading ? "Generating adaptive questionnaire based on your specific needs" : "Initializing workflow"}
      >
        {!isLoading && (
          <div className="flex justify-center mt-8">
            <Button onClick={() => initializeFlow()} size="lg">
              Start Collection Flow
            </Button>
          </div>
        )}
      </CollectionPageLayout>
    );
  }

  // Main component render
  return (
    <CollectionPageLayout
      title="Adaptive Data Collection"
      description={applicationId ? `Collecting data for application ${applicationId}` : 'New application data collection'}
    >
      <AdaptiveFormContainer
        formData={formData}
        formValues={formValues}
        validation={validation}
        milestones={progressMilestones}
        isSaving={isSaving}
        isSubmitting={isLoading}
        onFieldChange={handleFieldChange}
        onValidationChange={handleValidationChange}
        onSave={handleSave}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/collection')}
      />
    </CollectionPageLayout>
  );
};

export default AdaptiveForms;