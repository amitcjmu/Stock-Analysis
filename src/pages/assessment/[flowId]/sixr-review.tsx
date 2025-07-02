import React, { useState, useEffect, useMemo } from 'react';
import { GetServerSideProps } from 'next/router';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { SixRStrategyMatrix } from '@/components/assessment/SixRStrategyMatrix';
import { ComponentTreatmentEditor } from '@/components/assessment/ComponentTreatmentEditor';
import { CompatibilityValidator } from '@/components/assessment/CompatibilityValidator';
import { ConfidenceScoreIndicator } from '@/components/assessment/ConfidenceScoreIndicator';
import { ApplicationRollupView } from '@/components/assessment/ApplicationRollupView';
import { MoveGroupHintsPanel } from '@/components/assessment/MoveGroupHintsPanel';
import { BulkEditingControls } from '@/components/assessment/BulkEditingControls';
import { ApplicationTabs } from '@/components/assessment/ApplicationTabs';
import { useAssessmentFlow, SixRDecision, ComponentTreatment } from '@/hooks/useAssessmentFlow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Save, ArrowRight, Loader2, BarChart3, Target, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SixRReviewPageProps {
  flowId: string;
}

const SIX_R_STRATEGIES = [
  { value: 'rehost', label: 'Rehost (Lift & Shift)', color: 'bg-green-100 text-green-700' },
  { value: 'replatform', label: 'Replatform (Lift & Reshape)', color: 'bg-blue-100 text-blue-700' },
  { value: 'refactor', label: 'Refactor/Re-architect', color: 'bg-purple-100 text-purple-700' },
  { value: 'repurchase', label: 'Repurchase (SaaS)', color: 'bg-orange-100 text-orange-700' },
  { value: 'retire', label: 'Retire', color: 'bg-gray-100 text-gray-700' },
  { value: 'retain', label: 'Retain (Revisit)', color: 'bg-yellow-100 text-yellow-700' }
];

const SixRReviewPage: React.FC<SixRReviewPageProps> = ({ flowId }) => {
  const {
    state,
    updateSixRDecision,
    resumeFlow
  } = useAssessmentFlow(flowId);

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDraft, setIsDraft] = useState(false);
  const [editingComponent, setEditingComponent] = useState<string | null>(null);
  const [bulkEditMode, setBulkEditMode] = useState(false);
  const [selectedComponents, setSelectedComponents] = useState<string[]>([]);

  // Set first application as selected by default
  useEffect(() => {
    if (state.selectedApplicationIds.length > 0 && !selectedApp) {
      setSelectedApp(state.selectedApplicationIds[0]);
    }
  }, [state.selectedApplicationIds, selectedApp]);

  // Get current application data
  const currentAppDecision = selectedApp ? state.sixrDecisions[selectedApp] : null;
  const currentAppComponents = selectedApp ? state.applicationComponents[selectedApp] || [] : [];

  // Calculate overall statistics
  const overallStats = useMemo(() => {
    const allDecisions = Object.values(state.sixrDecisions);
    const strategyCount = SIX_R_STRATEGIES.reduce((acc, strategy) => {
      acc[strategy.value] = allDecisions.filter(d => d.overall_strategy === strategy.value).length;
      return acc;
    }, {} as Record<string, number>);

    const avgConfidence = allDecisions.length > 0 
      ? allDecisions.reduce((sum, d) => sum + d.confidence_score, 0) / allDecisions.length 
      : 0;

    const needsReview = allDecisions.filter(d => d.confidence_score < 0.8).length;
    const hasIssues = allDecisions.filter(d => 
      d.component_treatments?.some(ct => !ct.compatibility_validated)
    ).length;

    return {
      totalApps: state.selectedApplicationIds.length,
      assessed: allDecisions.length,
      avgConfidence,
      needsReview,
      hasIssues,
      strategyCount
    };
  }, [state.sixrDecisions, state.selectedApplicationIds]);

  const handleSaveDraft = async () => {
    if (!selectedApp || !currentAppDecision) return;
    
    setIsDraft(true);
    try {
      await updateSixRDecision(selectedApp, currentAppDecision);
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsDraft(false);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Save all application decisions
      for (const [appId, decision] of Object.entries(state.sixrDecisions)) {
        await updateSixRDecision(appId, decision);
      }
      
      await resumeFlow({
        sixrDecisions: state.sixrDecisions
      });
    } catch (error) {
      console.error('Failed to submit 6R strategy review:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateAppDecision = (updates: Partial<SixRDecision>) => {
    if (!selectedApp) return;
    updateSixRDecision(selectedApp, updates);
  };

  const updateComponentTreatment = (componentName: string, treatment: Partial<ComponentTreatment>) => {
    if (!selectedApp || !currentAppDecision) return;

    const updatedTreatments = currentAppDecision.component_treatments.map(ct =>
      ct.component_name === componentName ? { ...ct, ...treatment } : ct
    );

    updateSixRDecision(selectedApp, {
      ...currentAppDecision,
      component_treatments: updatedTreatments
    });
  };

  const getStrategyColor = (strategy: string) => {
    const strategyInfo = SIX_R_STRATEGIES.find(s => s.value === strategy);
    return strategyInfo?.color || 'bg-gray-100 text-gray-700';
  };

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
        {state.status === 'error' && (
          <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <p className="text-sm text-red-600">{state.error}</p>
          </div>
        )}

        {state.status === 'processing' && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
              <p className="text-sm text-blue-600">
                AI agents are analyzing 6R strategies and component treatments...
              </p>
            </div>
          </div>
        )}

        {/* Overall Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>6R Strategy Overview</span>
            </CardTitle>
            <CardDescription>
              Summary of modernization strategies across all applications
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {overallStats.assessed}/{overallStats.totalApps}
                </div>
                <div className="text-sm text-gray-600">Applications Assessed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Math.round(overallStats.avgConfidence * 100)}%
                </div>
                <div className="text-sm text-gray-600">Avg Confidence</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{overallStats.needsReview}</div>
                <div className="text-sm text-gray-600">Need Review</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{overallStats.hasIssues}</div>
                <div className="text-sm text-gray-600">Have Issues</div>
              </div>
            </div>

            {/* Strategy Distribution */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">Strategy Distribution</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {SIX_R_STRATEGIES.map(strategy => (
                  <div key={strategy.value} className={cn("p-2 rounded-lg border", strategy.color)}>
                    <div className="font-semibold">{overallStats.strategyCount[strategy.value] || 0}</div>
                    <div className="text-xs">{strategy.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

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
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Target className="h-5 w-5" />
                    <span>{selectedApp} Strategy</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStrategyColor(currentAppDecision.overall_strategy)}>
                      {SIX_R_STRATEGIES.find(s => s.value === currentAppDecision.overall_strategy)?.label || currentAppDecision.overall_strategy}
                    </Badge>
                    <ConfidenceScoreIndicator 
                      score={currentAppDecision.confidence_score}
                      size="large"
                    />
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Rationale</h4>
                      <p className="text-sm text-gray-600">{currentAppDecision.rationale}</p>
                    </div>
                    
                    {currentAppDecision.risk_factors.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">Risk Factors</h4>
                        <div className="flex flex-wrap gap-1">
                          {currentAppDecision.risk_factors.map((risk, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              {risk}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="space-y-3">
                    {currentAppDecision.architecture_exceptions.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">Architecture Exceptions</h4>
                        <div className="space-y-1">
                          {currentAppDecision.architecture_exceptions.map((exception, index) => (
                            <p key={index} className="text-xs text-orange-600 bg-orange-50 p-1 rounded">
                              {exception}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {currentAppDecision.move_group_hints.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-1">Move Group Hints</h4>
                        <div className="flex flex-wrap gap-1">
                          {currentAppDecision.move_group_hints.map((hint, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {hint}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Main Content Tabs */}
            <Tabs defaultValue="strategy-matrix" className="space-y-4">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="strategy-matrix">Strategy Matrix</TabsTrigger>
                <TabsTrigger value="component-treatments">
                  Components ({currentAppDecision.component_treatments.length})
                </TabsTrigger>
                <TabsTrigger value="compatibility">Compatibility</TabsTrigger>
                <TabsTrigger value="move-groups">Move Groups</TabsTrigger>
              </TabsList>

              <TabsContent value="strategy-matrix" className="space-y-4">
                <SixRStrategyMatrix
                  decision={currentAppDecision}
                  onDecisionChange={updateAppDecision}
                />
              </TabsContent>

              <TabsContent value="component-treatments" className="space-y-4">
                {/* Bulk Editing Controls */}
                <BulkEditingControls
                  enabled={bulkEditMode}
                  onToggle={setBulkEditMode}
                  selectedComponents={selectedComponents}
                  onSelectionChange={setSelectedComponents}
                  componentTreatments={currentAppDecision.component_treatments}
                  onBulkUpdate={(updates) => {
                    selectedComponents.forEach(componentName => {
                      updateComponentTreatment(componentName, updates);
                    });
                    setSelectedComponents([]);
                  }}
                />

                <ComponentTreatmentEditor
                  treatments={currentAppDecision.component_treatments}
                  onTreatmentChange={updateComponentTreatment}
                  editingComponent={editingComponent}
                  onEditComponent={setEditingComponent}
                  bulkEditMode={bulkEditMode}
                  selectedComponents={selectedComponents}
                  onSelectionChange={setSelectedComponents}
                />
              </TabsContent>

              <TabsContent value="compatibility" className="space-y-4">
                <CompatibilityValidator
                  treatments={currentAppDecision.component_treatments}
                  onTreatmentChange={updateComponentTreatment}
                />
              </TabsContent>

              <TabsContent value="move-groups" className="space-y-4">
                <MoveGroupHintsPanel
                  decision={currentAppDecision}
                  onDecisionChange={updateAppDecision}
                />
              </TabsContent>
            </Tabs>
          </>
        )}

        {/* Application Rollup View */}
        <ApplicationRollupView
          decisions={state.sixrDecisions}
          selectedApplicationIds={state.selectedApplicationIds}
          onApplicationSelect={setSelectedApp}
        />

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              onClick={handleSaveDraft}
              disabled={isDraft || !selectedApp}
            >
              <Save className="h-4 w-4 mr-2" />
              {isDraft ? 'Saving...' : 'Save Progress'}
            </Button>
          </div>
          
          <Button 
            onClick={handleSubmit}
            disabled={isSubmitting || state.isLoading}
            size="lg"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                Continue to Application Review
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
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