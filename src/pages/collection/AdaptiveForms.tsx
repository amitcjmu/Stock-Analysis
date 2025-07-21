import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

// Import modular components
import CollectionPageLayout from '@/components/collection/layout/CollectionPageLayout';
import AdaptiveFormContainer from '@/components/collection/forms/AdaptiveFormContainer';
import { CollectionUploadBlocker } from '@/components/collection/CollectionUploadBlocker';

// Import custom hooks
import { useAdaptiveFormFlow } from '@/hooks/collection/useAdaptiveFormFlow';
import { useIncompleteCollectionFlows } from '@/hooks/collection/useCollectionFlowManagement';

// Import types
import type { ProgressMilestone } from '@/components/collection/types';

/**
 * Adaptive Forms collection page
 * Refactored to use modular components and custom hooks for better maintainability
 */
const AdaptiveForms: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Get application ID and flow ID from URL params
  const applicationId = searchParams.get('applicationId');
  const flowId = searchParams.get('flowId');

  // Check for incomplete flows that would block new collection processes
  const { 
    data: incompleteFlows = [], 
    isLoading: checkingFlows, 
    refetch: refetchFlows 
  } = useIncompleteCollectionFlows();
  
  const hasIncompleteFlows = incompleteFlows.length > 0;

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
    handleSubmit
  } = useAdaptiveFormFlow({
    applicationId,
    flowId,
    autoInitialize: !checkingFlows && !hasIncompleteFlows
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
    try {
      // Refresh flows after deletion
      refetchFlows();
    } catch (error) {
      console.error('Failed to delete collection flow:', error);
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

  // Show blocker if there are incomplete flows
  if (hasIncompleteFlows) {
    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Collection workflow blocked - manage existing flows"
      >
        <CollectionUploadBlocker
          incompleteFlows={incompleteFlows}
          onContinueFlow={handleContinueFlow}
          onDeleteFlow={handleDeleteFlow}
          onViewDetails={handleViewFlowDetails}
          onManageFlows={handleManageFlows}
          onRefresh={refetchFlows}
          isLoading={false}
        />
      </CollectionPageLayout>
    );
  }

  // Show loading state while form data is being generated
  if (!formData) {
    return (
      <CollectionPageLayout
        title="Adaptive Data Collection"
        description="Generating personalized collection form"
        isLoading={true}
        loadingMessage="CrewAI agents are generating adaptive questionnaire..."
        loadingSubMessage="Analyzing gaps and creating personalized form fields"
      >
        {/* Loading content handled by layout */}
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