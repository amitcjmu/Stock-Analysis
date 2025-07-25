import React from 'react';
import type { GetServerSideProps } from 'next/router';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ApplicationRollupView } from '@/components/assessment/ApplicationRollupView';
import { ApplicationTabs } from '@/components/assessment/ApplicationTabs';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { AlertCircle } from 'lucide-react';
import { SixRAppDecisionSummary } from '@/components/assessment/sixr-review'
import { SixROverallStats, SixRActionButtons, SixRStatusAlert, SixRMainTabs } from '@/components/assessment/sixr-review'
import { useSixRReviewState } from '@/hooks/assessment/useSixRReviewState';
import { useSixRSubmission } from '@/hooks/assessment/useSixRSubmission';
import { useSixRStatistics } from '@/hooks/assessment/useSixRStatistics';

interface SixRReviewPageProps {
  flowId: string;
}


const SixRReviewPage: React.FC<SixRReviewPageProps> = ({ flowId }) => {
  const {
    state,
    updateSixRDecision,
    resumeFlow
  } = useAssessmentFlow(flowId);

  // Use custom hooks for modular state management
  const {
    selectedApp,
    editingComponent,
    bulkEditMode,
    selectedComponents,
    currentAppDecision,
    setSelectedApp,
    setEditingComponent,
    setBulkEditMode,
    setSelectedComponents,
    updateAppDecision,
    updateComponentTreatment,
    handleBulkComponentUpdate
  } = useSixRReviewState({
    selectedApplicationIds: state.selectedApplicationIds,
    sixrDecisions: state.sixrDecisions,
    updateSixRDecision
  });

  // Use submission hook for save/submit logic
  const {
    isSubmitting,
    isDraft,
    handleSaveDraft,
    handleSubmit
  } = useSixRSubmission({
    sixrDecisions: state.sixrDecisions,
    updateSixRDecision,
    resumeFlow,
    selectedApp,
    currentAppDecision
  });

  // Use statistics hook for calculated metrics
  const overallStats = useSixRStatistics({
    sixrDecisions: state.sixrDecisions,
    selectedApplicationIds: state.selectedApplicationIds
  });

  if (state.selectedApplicationIds.length === 0) {
    return (
      <AssessmentFlowLayout flowId={flowId}>
        <div className="p-6 text-center">
          <AlertCircle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Applications Selected</h2>
          <p className="text-gray-600">Please return to the previous step to select applications for analysis.</p>
        </div>
      </AssessmentFlowLayout>
    );
  }

  return (
    <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            6R Strategy Review
          </h1>
          <p className="text-gray-600">
            Review and modify component-level modernization strategies based on technical debt analysis
          </p>
        </div>

        {/* Status Alert */}
        <SixRStatusAlert status={state.status} error={state.error} />

        {/* Overall Statistics */}
        <SixROverallStats statistics={overallStats} />

        {/* Application Selection */}
        <ApplicationTabs
          applications={state.selectedApplicationIds}
          selectedApp={selectedApp}
          onAppSelect={setSelectedApp}
          getApplicationName={(appId) => appId} // In real implementation, get from application data
        />

        {selectedApp && currentAppDecision && (
          <>
            {/* Application Decision Summary */}
            <SixRAppDecisionSummary
              selectedApp={selectedApp}
              decision={currentAppDecision}
            />

            {/* Main Content Tabs */}
            <SixRMainTabs
              decision={currentAppDecision}
              onDecisionChange={updateAppDecision}
              onComponentTreatmentChange={updateComponentTreatment}
              editingComponent={editingComponent}
              onEditComponent={setEditingComponent}
              bulkEditMode={bulkEditMode}
              onBulkEditToggle={setBulkEditMode}
              selectedComponents={selectedComponents}
              onComponentSelectionChange={setSelectedComponents}
              onBulkComponentUpdate={handleBulkComponentUpdate}
            />
          </>
        )}

        {/* Application Rollup View */}
        <ApplicationRollupView
          decisions={state.sixrDecisions}
          selectedApplicationIds={state.selectedApplicationIds}
          onApplicationSelect={setSelectedApp}
        />

        {/* Action Buttons */}
        <SixRActionButtons
          isDraft={isDraft}
          isSubmitting={isSubmitting}
          isLoading={state.isLoading}
          selectedApp={selectedApp}
          onSaveDraft={handleSaveDraft}
          onSubmit={handleSubmit}
        />
      </div>
    </AssessmentFlowLayout>
  );
};

export const getServerSideProps: GetServerSideProps = async (context) => {
  return {
    props: {
      flowId: context.params?.flowId as string
    }
  };
};

export default SixRReviewPage;
