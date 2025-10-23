import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useParams } from 'react-router-dom';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ApplicationSummaryCard } from '@/components/assessment/ApplicationSummaryCard';
import { ComponentBreakdownView } from '@/components/assessment/ComponentBreakdownView';
import { TechDebtSummaryChart } from '@/components/assessment/TechDebtSummaryChart';
import { SixRDecisionRationale } from '@/components/assessment/SixRDecisionRationale';
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
    finalizeAssessment
  } = useAssessmentFlow(flowId);

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [printMode, setPrintMode] = useState(false);

  // Set first application as selected by default
  useEffect(() => {
    if (state.selectedApplicationIds.length > 0 && !selectedApp) {
      setSelectedApp(state.selectedApplicationIds[0]);
    }
  }, [state.selectedApplicationIds, selectedApp]);

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

  const assessmentComplete = Object.keys(state.sixrDecisions).length === state.selectedApplicationIds.length;

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
      <div className={cn("p-6 max-w-7xl mx-auto space-y-6", printMode && "print:max-w-none print:p-4")}>
        {/* Header */}
        <div className="space-y-2 print:mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Application Assessment Review
              </h1>
              <p className="text-gray-600">
                Comprehensive review of all application assessments and migration strategies
              </p>
            </div>

            <div className="flex items-center space-x-2 print:hidden">
              <Button variant="outline" onClick={handlePrint}>
                <Eye className="h-4 w-4 mr-2" />
                Print Preview
              </Button>
              <ExportAndSharingControls
                assessmentData={{
                  applications: state.selectedApplicationIds,
                  decisions: state.sixrDecisions,
                  techDebtAnalysis: state.techDebtAnalysis,
                  architectureStandards: state.engagementStandards,
                  overrides: state.applicationOverrides
                }}
              />
            </div>
          </div>

          {/* Assessment Status */}
          <div className="flex items-center space-x-4">
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
              {Object.keys(state.sixrDecisions).length} of {state.selectedApplicationIds.length} applications assessed
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

        {/* Application Selection */}
        {!printMode && (
          <ApplicationTabs
            applications={state.selectedApplicationIds}
            selectedApp={selectedApp}
            onAppSelect={setSelectedApp}
            getApplicationName={(appId) => appId} // In real implementation, get from application data
          />
        )}

        {selectedApp && currentAppDecision && (
          <>
            {/* Application Summary Card */}
            <ApplicationSummaryCard
              applicationId={selectedApp}
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
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <SixRDecisionRationale
                    decision={currentAppDecision}
                    printMode={printMode}
                  />

                  <ArchitectureExceptionsPanel
                    decision={currentAppDecision}
                    standards={state.engagementStandards}
                    printMode={printMode}
                  />
                </div>

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
                    <SixRDecisionRationale
                      decision={currentAppDecision}
                      printMode={printMode}
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
            {state.selectedApplicationIds.map(appId => {
              const decision = state.sixrDecisions[appId];
              const components = state.applicationComponents[appId] || [];
              const techDebt = state.techDebtAnalysis[appId] || [];

              if (!decision) return null;

              return (
                <div key={appId} className="mb-8">
                  <ApplicationSummaryCard
                    applicationId={appId}
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

      {/* Print Styles */}
      <style jsx global>{`
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
