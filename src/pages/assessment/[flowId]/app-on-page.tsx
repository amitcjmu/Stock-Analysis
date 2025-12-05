import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useParams } from 'react-router-dom';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ApplicationSummaryCard } from '@/components/assessment/ApplicationSummaryCard';
import { ComponentBreakdownView } from '@/components/assessment/ComponentBreakdownView';
import { TechDebtSummaryChart } from '@/components/assessment/TechDebtSummaryChart';
// SixRDecisionRationale removed - replaced by RecommendationCard (Issue #719)
import {
  RecommendationCard,
  type SixRStrategyType,
  type EffortLevel,
  type CostRange
} from '@/components/assessment';
import { ArchitectureExceptionsPanel } from '@/components/assessment/ArchitectureExceptionsPanel';
import { DependencyVisualization } from '@/components/assessment/DependencyVisualization';
import { BusinessImpactAssessment } from '@/components/assessment/BusinessImpactAssessment';
import { ExportAndSharingControls } from '@/components/assessment/ExportAndSharingControls';
import { ApplicationTabs } from '@/components/assessment/ApplicationTabs';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Save, FileText } from 'lucide-react'
import { AlertCircle, ArrowRight, Loader2, CheckCircle, Eye, Download } from 'lucide-react'
import { cn } from '@/lib/utils';

const AppOnPagePage: React.FC = () => {
  // Bug #730 fix - Use React Router's useParams instead of Next.js props
  const { flowId } = useParams<{ flowId: string }>();

  const {
    state,
    finalizeAssessment,
    refreshApplicationData,
    toggleAutoPolling,
    resumeFlow
  } = useAssessmentFlow(flowId);

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [printMode, setPrintMode] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Set first application as selected by default
  useEffect(() => {
    if (state.selectedApplications.length > 0 && !selectedApp) {
      setSelectedApp(state.selectedApplications[0].application_id);
    }
  }, [state.selectedApplications, selectedApp]);

  // Get current application data
  const currentAppDecision = selectedApp ? state.sixrDecisions[selectedApp] : null;
  const currentAppComponents = selectedApp ? state.applicationComponents[selectedApp] || [] : [];
  const currentAppTechDebt = selectedApp ? state.techDebtAnalysis[selectedApp] || [] : [];

  const handleFinalize = async (): void => {
    setIsSubmitting(true);
    try {
      await finalizeAssessment();
    } catch (error) {
      console.error('Failed to finalize assessment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePrint = (): void => {
    setPrintMode(true);
    window.print();
    setTimeout(() => setPrintMode(false), 1000);
  };

  const handleRetryRecommendations = async (): Promise<void> => {
    setIsRetrying(true);
    try {
      await resumeFlow({
        phase: 'recommendation_generation',
        action: 'retry'
      });
      // Refresh data after retry completes
      await refreshApplicationData();
    } catch (error) {
      console.error('Failed to retry recommendation generation:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  // CC FIX: Assessment is complete when ALL selected applications have 6R decisions
  // Previous logic compared counts, but sixrDecisions may contain MORE entries (22) than selectedApplications (2)
  // because phase_results stores decisions for all processed apps, not just selected ones
  const assessmentComplete = state.selectedApplications.length > 0 &&
    state.selectedApplications.every(app => state.sixrDecisions[app.application_id]);

  // Detect failed applications (missing 6R decisions)
  const failedApplications = state.selectedApplications.filter(
    app => !state.sixrDecisions[app.application_id]
  );
  const hasFailedApps = failedApplications.length > 0;

  // Bug #730 fix: Show loading skeleton until data is fetched
  if (!state.dataFetched) {
    return (
      <AssessmentFlowLayout flowId={flowId}>
        <div className="p-6 space-y-6">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-64"></div>
            <div className="h-4 bg-gray-200 rounded w-96"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      </AssessmentFlowLayout>
    );
  }

  // CC: Fixed bug - check selectedApplications (populated) not selectedApplicationIds (may be empty)
  if (state.selectedApplications.length === 0) {
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
      <div className={cn("p-6 max-w-7xl mx-auto space-y-6", printMode && "print:max-w-none print:p-4")}>
        {/* Header */}
        <div className="space-y-4 print:mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Application Assessment Review
            </h1>
            <p className="text-gray-600 mt-1">
              Comprehensive review of all application assessments and migration strategies
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 print:hidden">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refreshApplicationData()}
                disabled={state.isLoading}
              >
                {state.isLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Refresh Data
              </Button>
              <Button
                variant={state.autoPollingEnabled ? "default" : "outline"}
                size="sm"
                onClick={toggleAutoPolling}
                className="gap-2"
              >
                {state.autoPollingEnabled ? (
                  <>
                    <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
                    Auto-refresh On
                  </>
                ) : (
                  <>Auto-refresh Off</>
                )}
              </Button>
              <Button variant="outline" onClick={handlePrint}>
                <Eye className="h-4 w-4 mr-2" />
                Print Preview
              </Button>
              <ExportAndSharingControls
                flowId={flowId || ''}
                assessmentData={{
                  applications: state.selectedApplicationIds,
                  decisions: state.sixrDecisions,
                  techDebtAnalysis: state.techDebtAnalysis,
                  architectureStandards: state.engagementStandards,
                  overrides: state.applicationOverrides
                }}
              />
          </div>

          {/* Assessment Status */}
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant={assessmentComplete ? "default" : "secondary"} className="flex items-center space-x-1">
              {assessmentComplete ? (
                <CheckCircle className="h-3 w-3" />
              ) : (
                <Loader2 className="h-3 w-3 animate-spin" />
              )}
              <span>
                {assessmentComplete ? 'Assessment Complete' : 'Assessment In Progress'}
              </span>
            </Badge>

            <Badge variant="outline">
              {Object.keys(state.sixrDecisions).length} of {state.selectedApplications.length} applications assessed
            </Badge>

            <Badge variant="outline">
              {state.appsReadyForPlanning.length} ready for planning
            </Badge>
          </div>
        </div>

        {/* Status Alert */}
        {state.status === 'error' && (
          <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg print:hidden">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-600">{state.error}</p>
          </div>
        )}

        {state.status === 'processing' && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg print:hidden">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
              <p className="text-sm text-blue-600">
                AI agents are finalizing assessment data...
              </p>
            </div>
          </div>
        )}

        {/* Failed Recommendations Warning */}
        {hasFailedApps && !isRetrying && (
          <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg print:hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-orange-600" />
                <div>
                  <p className="text-sm font-medium text-orange-900">
                    {failedApplications.length} {failedApplications.length === 1 ? 'application' : 'applications'} failed to generate recommendations
                  </p>
                  <p className="text-xs text-orange-700 mt-1">
                    Applications: {failedApplications.map(app => app.application_name).join(', ')}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetryRecommendations}
                disabled={isRetrying}
                className="border-orange-300 text-orange-700 hover:bg-orange-100"
              >
                {isRetrying ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Retrying...
                  </>
                ) : (
                  'Retry Generation'
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Application Selection */}
        {!printMode && (
          <ApplicationTabs
            applications={state.selectedApplications.map(app => app.application_id)}
            selectedApp={selectedApp}
            onAppSelect={setSelectedApp}
            getApplicationName={(appId) => {
              const app = state.selectedApplications.find(a => a.application_id === appId);
              return app?.application_name || appId;
            }}
          />
        )}

        {selectedApp && currentAppDecision && (
          <>
            {/* Application Summary Card */}
            <ApplicationSummaryCard
              applicationId={selectedApp}
              applicationName={state.selectedApplications.find(a => a.application_id === selectedApp)?.application_name}
              decision={currentAppDecision}
              components={currentAppComponents}
              techDebt={currentAppTechDebt}
              printMode={printMode}
            />

            {/* Main Content Tabs */}
            <Tabs defaultValue="overview" className={cn("space-y-4", printMode && "print:space-y-8")}>
              {!printMode && (
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="components">Components</TabsTrigger>
                  <TabsTrigger value="tech-debt">Tech Debt</TabsTrigger>
                  <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
                  <TabsTrigger value="business-impact">Business Impact</TabsTrigger>
                </TabsList>
              )}

              <TabsContent value="overview" className="space-y-6">
                {/* Enhanced 6R Recommendation Card (Issue #719 - Treatment Display Polish) */}
                <RecommendationCard
                  application_id={selectedApp}
                  application_name={
                    state.selectedApplications.find(app => app.application_id === selectedApp)?.application_name || 'Application'
                  }
                  application_version={
                    state.selectedApplications.find(app => app.application_id === selectedApp)?.version
                  }
                  recommended_strategy={(currentAppDecision?.overall_strategy || 'retain') as SixRStrategyType}
                  confidence={currentAppDecision?.confidence_score || 0}
                  effort={currentAppDecision?.effort_estimate as EffortLevel | undefined}
                  cost_range={currentAppDecision?.cost_range as CostRange | undefined}
                  rationale={currentAppDecision?.rationale || 'No rationale provided'}
                  risk_factors={currentAppDecision?.risk_factors || []}
                  alternatives={currentAppDecision?.alternative_strategies?.map(alt => ({
                    strategy: alt.strategy as SixRStrategyType,
                    confidence: alt.confidence || 0,
                    effort: alt.effort_estimate as EffortLevel | undefined,
                    cost_range: alt.cost_range as CostRange | undefined
                  }))}
                  is_accepted={state.appsReadyForPlanning.includes(selectedApp)}
                  onAccept={(appId) => {
                    console.log('Recommendation accepted for:', appId);
                    // TODO: Implement accept logic via Assessment Flow API
                  }}
                  onRequestSME={(appId) => {
                    console.log('SME review requested for:', appId);
                    alert('SME review request submitted. You will be notified when feedback is available.');
                  }}
                />

                {/* Architecture Exceptions - full width now that SixRDecisionRationale is removed */}
                <ArchitectureExceptionsPanel
                  decision={currentAppDecision}
                  standards={state.engagementStandards}
                  printMode={printMode}
                />

                <TechDebtSummaryChart
                  techDebt={currentAppTechDebt}
                  printMode={printMode}
                />
              </TabsContent>

              <TabsContent value="components" className="space-y-4">
                <ComponentBreakdownView
                  components={currentAppComponents}
                  treatments={currentAppDecision.component_treatments}
                  printMode={printMode}
                />
              </TabsContent>

              <TabsContent value="tech-debt" className="space-y-4">
                <TechDebtSummaryChart
                  techDebt={currentAppTechDebt}
                  detailed={true}
                  printMode={printMode}
                />
              </TabsContent>

              <TabsContent value="dependencies" className="space-y-4">
                <DependencyVisualization
                  components={currentAppComponents}
                  applicationId={selectedApp}
                  printMode={printMode}
                />
              </TabsContent>

              <TabsContent value="business-impact" className="space-y-4">
                <BusinessImpactAssessment
                  decision={currentAppDecision}
                  techDebt={currentAppTechDebt}
                  printMode={printMode}
                />
              </TabsContent>

              {/* Print Mode: Show All Content */}
              {printMode && (
                <div className="print:block hidden space-y-8">
                  <div className="page-break">
                    {/* Print mode uses RecommendationCard for 6R strategy display (Issue #719) */}
                    <RecommendationCard
                      application_id={selectedApp}
                      application_name={
                        state.selectedApplications.find(app => app.application_id === selectedApp)?.application_name || 'Application'
                      }
                      recommended_strategy={(currentAppDecision?.overall_strategy || 'retain') as SixRStrategyType}
                      confidence={currentAppDecision?.confidence_score || 0}
                      effort={currentAppDecision?.effort_estimate as EffortLevel | undefined}
                      cost_range={currentAppDecision?.cost_range as CostRange | undefined}
                      rationale={currentAppDecision?.rationale || 'No rationale provided'}
                      risk_factors={currentAppDecision?.risk_factors || []}
                      is_accepted={state.appsReadyForPlanning.includes(selectedApp)}
                    />
                  </div>

                  <div className="page-break">
                    <ComponentBreakdownView
                      components={currentAppComponents}
                      treatments={currentAppDecision.component_treatments}
                      printMode={printMode}
                    />
                  </div>

                  <div className="page-break">
                    <TechDebtSummaryChart
                      techDebt={currentAppTechDebt}
                      detailed={true}
                      printMode={printMode}
                    />
                  </div>

                  <div className="page-break">
                    <BusinessImpactAssessment
                      decision={currentAppDecision}
                      techDebt={currentAppTechDebt}
                      printMode={printMode}
                    />
                  </div>
                </div>
              )}
            </Tabs>
          </>
        )}

        {/* All Applications Summary (Print Mode) */}
        {printMode && (
          <div className="print:block hidden space-y-6 page-break">
            <h2 className="text-xl font-bold text-gray-900 mb-4">All Applications Summary</h2>
            {state.selectedApplications.map(app => {
              const decision = state.sixrDecisions[app.application_id];
              const components = state.applicationComponents[app.application_id] || [];
              const techDebt = state.techDebtAnalysis[app.application_id] || [];

              if (!decision) return null;

              return (
                <div key={app.application_id} className="mb-8">
                  <ApplicationSummaryCard
                    applicationId={app.application_id}
                    applicationName={app.application_name}
                    decision={decision}
                    components={components}
                    techDebt={techDebt}
                    printMode={printMode}
                    compact={true}
                  />
                </div>
              );
            })}
          </div>
        )}

        {/* Action Buttons */}
        {!printMode && (
          <div className="flex justify-between items-center pt-6 border-t border-gray-200">
            <div className="flex items-center space-x-2">
              <Button variant="outline" disabled={!assessmentComplete}>
                <Download className="h-4 w-4 mr-2" />
                Download Report
              </Button>
            </div>

            <Button
              onClick={handleFinalize}
              disabled={isSubmitting || !assessmentComplete || state.isLoading}
              size="lg"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Finalizing...
                </>
              ) : (
                <>
                  Finalize Assessment
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        )}
      </div>

      {/* Print Styles - Fixed Issue #819: Removed jsx/global attributes (Next.js-specific, not compatible with Vite) */}
      <style>{`
        @media print {
          .print\\:hidden { display: none !important; }
          .print\\:block { display: block !important; }
          .print\\:max-w-none { max-width: none !important; }
          .print\\:p-4 { padding: 1rem !important; }
          .print\\:space-y-8 > * + * { margin-top: 2rem !important; }
          .print\\:mb-8 { margin-bottom: 2rem !important; }
          .page-break { page-break-before: always; }
          .page-break:first-child { page-break-before: auto; }
        }
      `}</style>
    </AssessmentFlowLayout>
  );
};

export default AppOnPagePage;
