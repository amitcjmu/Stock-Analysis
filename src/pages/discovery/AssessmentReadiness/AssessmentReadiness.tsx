import React from 'react'
import type { useState } from 'react'
import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/components/ui/use-toast';
import { RefreshCw } from 'lucide-react';

// Components
import { ErrorBoundary } from './components/ErrorBoundary';
import { ReadinessScoreCard } from './components/ReadinessScoreCard';
import { ReadinessTabs } from './components/ReadinessTabs';

// Hooks
import { 
  useReadinessAssessment, 
  useGenerateSignoffPackage, 
  useSubmitForApproval 
} from './hooks/useReadinessAssessment';

// Types
import type { ReadinessAssessment, SignoffPackage } from './types';

// Main component
const AssessmentReadiness: React.FC = () => {
  const { clientAccountId, engagementId } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch assessment data
  const {
    data: readinessAssessment,
    isLoading: isLoadingAssessment,
    error: assessmentError,
    refetch: refetchAssessment,
  } = useReadinessAssessment({
    clientAccountId,
    engagementId,
  });

  // Generate signoff package mutation
  const { mutate: generateSignoff, isLoading: isGeneratingSignoff } = useGenerateSignoffPackage({
    onSuccess: (data: SignoffPackage) => {
      toast({
        title: 'Signoff package generated',
        description: 'The signoff package has been successfully created.',
      });
      // Invalidate queries to refetch the latest data
      queryClient.invalidateQueries(['readinessAssessment', { clientAccountId, engagementId }]);
      setActiveTab('signoff');
    },
    onError: (error: Error) => {
      toast({
        title: 'Error generating signoff',
        description: error.message || 'Failed to generate signoff package',
        variant: 'destructive',
      });
    },
  });

  // Submit for approval mutation
  const { mutate: submitApproval, isLoading: isSubmittingApproval } = useSubmitForApproval({
    onSuccess: () => {
      toast({
        title: 'Submitted for approval',
        description: 'The assessment has been submitted for stakeholder approval.',
      });
      // Invalidate queries to refetch the latest data
      queryClient.invalidateQueries(['readinessAssessment', { clientAccountId, engagementId }]);
    },
    onError: (error: Error) => {
      toast({
        title: 'Submission failed',
        description: error.message || 'Failed to submit for approval',
        variant: 'destructive',
      });
    },
  });

  // Handle signoff generation
  const handleGenerateSignoff = () => {
    if (!readinessAssessment) return;
    generateSignoff({
      assessmentId: readinessAssessment.id,
      clientAccountId,
      engagementId,
    });
  };

  // Handle submission for approval
  const handleSubmitForApproval = () => {
    if (!readinessAssessment?.signoffPackage) return;
    
    submitApproval({
      assessmentId: readinessAssessment.id,
      signoffPackage: readinessAssessment.signoffPackage,
      clientAccountId,
      engagementId,
    });
  };

  // Loading state
  if (isLoadingAssessment) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading assessment data...</span>
      </div>
    );
  }

  // Error state
  if (assessmentError) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-lg font-medium text-red-800">Error loading assessment</h2>
          <p className="text-red-700 mt-2">
            {assessmentError.message || 'Failed to load assessment data. Please try again.'}
          </p>
          <button
            onClick={() => refetchAssessment()}
            className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No data state
  if (!readinessAssessment) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h2 className="text-lg font-medium text-blue-800">No assessment data available</h2>
          <p className="text-blue-700 mt-2">
            There is no assessment data available for the current engagement.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Readiness Score Card */}
      <ReadinessScoreCard 
        assessment={readinessAssessment} 
        onRefresh={refetchAssessment} 
        isLoading={isLoadingAssessment} 
      />
      
      {/* Readiness Tabs */}
      <ReadinessTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        assessment={readinessAssessment}
        signoffPackage={readinessAssessment.signoffPackage || null}
        isReadyForSignoff={!!readinessAssessment.overall_readiness?.readiness_score}
        isGeneratingSignoff={isGeneratingSignoff}
        isSubmittingApproval={isSubmittingApproval}
        onGenerateSignoff={handleGenerateSignoff}
        onSubmitForApproval={handleSubmitForApproval}
      />
    </div>
  );
};

// Wrap the component with ErrorBoundary
const AssessmentReadinessWithErrorBoundary: React.FC = () => (
  <ErrorBoundary>
    <AssessmentReadiness />
  </ErrorBoundary>
);

export default AssessmentReadinessWithErrorBoundary;
