import React from 'react'
import { useState } from 'react'
import { useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/components/ui/use-toast';
import { Download, CheckCircle, Database, Briefcase, Shield, TrendingUp } from 'lucide-react'
import { FileText, RefreshCw, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

// Components
import { ReadinessScoreCard } from './AssessmentReadiness/components/ReadinessScoreCard';
import { ReadinessTabs } from './AssessmentReadiness/components/ReadinessTabs';

// Hooks
import {
  useReadinessAssessment,
  useGenerateSignoffPackage,
  useSubmitForApproval
} from './AssessmentReadiness/hooks/useReadinessAssessment';

// Types
import { ReadinessAssessment, SignoffPackage } from './AssessmentReadiness/types';

// Utils
import { getReadinessColor, getRiskColor } from './AssessmentReadiness/utils';

// Error Boundary Component
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('AssessmentReadiness error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h2 className="text-lg font-medium text-red-800">Something went wrong</h2>
            <p className="text-red-700 mt-2">
              We're having trouble loading the assessment readiness data. Please try again later.
            </p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => this.setState({ hasError: false })}
            >
              Retry
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

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
    onSuccess: (data) => {
      toast({
        title: 'Signoff package generated',
        description: 'The signoff package has been successfully created.',
      });
      // Invalidate queries to refetch the latest data
      queryClient.invalidateQueries(['readinessAssessment', { clientAccountId, engagementId }]);
      setActiveTab('signoff');
    },
    onError: (error) => {
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
    onError: (error) => {
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
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center text-red-800">
          <AlertCircle className="h-5 w-5 mr-2" />
          <h3 className="font-medium">Error loading assessment data</h3>
        </div>
        <p className="mt-2 text-sm text-red-700">
          {assessmentError.message || 'Failed to load assessment data. Please try again.'}
        </p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => refetchAssessment()}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  // No data state
  if (!readinessAssessment) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 mx-auto text-gray-400" />
        <h3 className="mt-2 text-lg font-medium text-gray-900">No assessment data available</h3>
        <p className="mt-1 text-sm text-gray-500">
          The assessment readiness data has not been generated yet.
        </p>
        <Button className="mt-4">
          <RefreshCw className="h-4 w-4 mr-2" />
          Generate Assessment
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <ReadinessScoreCard readinessAssessment={readinessAssessment} />

      <div className="mt-6">
        <ReadinessTabs
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          readinessAssessment={readinessAssessment}
          onGenerateSignoff={handleGenerateSignoff}
          isGeneratingSignoff={isGeneratingSignoff}
          onSubmitForApproval={handleSubmitForApproval}
          isSubmittingApproval={isSubmittingApproval}
        />
      </div>
    </div>
  );
};

const AssessmentReadinessWithErrorBoundary = () => (
  <ErrorBoundary>
    <AssessmentReadiness />
  </ErrorBoundary>
);

export default AssessmentReadinessWithErrorBoundary;
