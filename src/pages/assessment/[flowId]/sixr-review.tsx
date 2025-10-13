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

  // Show asset mapping information even if no applications loaded yet
  // This helps users understand what was selected in collection phase
  if (state.selectedApplicationIds.length === 0) {
    return (
      <AssessmentFlowLayout flowId={flowId}>
        <div className="p-6 max-w-4xl mx-auto space-y-6">
          {/* Asset/Application Mapping Info */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-6 w-6 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-amber-900 mb-2">
                  Loading Assessment Data
                </h2>
                <p className="text-amber-800 mb-4">
                  Assessment flow is being initialized from collection data. This flow was created from collection flow assets.
                </p>

                {/* Show selected application IDs if available in state */}
                {state.selectedApplications && state.selectedApplications.length > 0 ? (
                  <div className="mt-4 p-4 bg-white rounded-lg border border-amber-200">
                    <h3 className="font-medium text-sm text-gray-900 mb-3">Selected Assets from Collection:</h3>
                    <div className="space-y-2">
                      {state.selectedApplications.map((app) => (
                        <div key={app.application_id} className="flex items-center justify-between text-sm">
                          <div>
                            <span className="font-medium">{app.application_name || app.application_id}</span>
                            {app.application_type && (
                              <span className="ml-2 text-gray-500">({app.application_type})</span>
                            )}
                          </div>
                          {app.application_name && app.application_name !== app.application_id && (
                            <span className="text-gray-600">→ App: {app.application_name}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="mt-4 p-4 bg-white rounded-lg border border-amber-200">
                    <p className="text-sm text-gray-700">
                      If this persists, please check that assets were properly selected in the collection phase
                      and that they have application associations.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
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

// eslint-disable-next-line react-refresh/only-export-components
export { getServerSideProps } from './utils';

export default SixRReviewPage;
