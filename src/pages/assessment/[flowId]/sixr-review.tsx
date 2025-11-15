import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertCircle,
  Save,
  ArrowRight,
  Loader2,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Network,
  Shield,
  TrendingUp,
  Database,
  GitBranch,
  Download
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { SixRDecision } from '@/hooks/useAssessmentFlow';

type SixRStrategy = 'rehost' | 'replatform' | 'refactor' | 'repurchase' | 'retire' | 'retain';

interface RiskFactor {
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  mitigation?: string;
}

/**
 * 6R Strategy Review Page
 *
 * Displays migration recommendations, dependency analysis, and risk assessment.
 * This page is the destination for both Dependencies and Risk Assessment phases.
 *
 * Route: /assessment/:flowId/sixr-review
 *
 * Features:
 * - 6R migration strategy recommendations per application
 * - Dependency visualization and analysis
 * - Risk assessment with severity indicators
 * - Accept/reject recommendation workflow
 * - Progress to next phase (app-on-page generation)
 */
const SixRStrategyReview: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const navigate = useNavigate();
  const { client, engagement } = useAuth();
  const {
    state,
    updateSixRDecision,
    resumeFlow,
    refreshApplicationData,
    toggleAutoPolling
  } = useAssessmentFlow(flowId);

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDraft, setIsDraft] = useState(false);
  const [acceptedRecommendations, setAcceptedRecommendations] = useState<Set<string>>(new Set());

  // Guard: redirect to overview if flowId missing
  useEffect(() => {
    if (!flowId) {
      navigate('/assess/overview', { replace: true });
    }
  }, [flowId, navigate]);

  // Set first application as selected by default
  useEffect(() => {
    if (state.selectedApplicationIds.length > 0 && !selectedApp) {
      setSelectedApp(state.selectedApplicationIds[0]);
    }
  }, [state.selectedApplicationIds, selectedApp]);

  // Get current application data - MUST be at top level before any early returns
  const currentAppDecision = selectedApp ? state.sixrDecisions[selectedApp] : null;
  const currentAppComponents = selectedApp ? state.applicationComponents[selectedApp] || [] : [];
  const currentAppTechDebt = selectedApp ? state.techDebtAnalysis[selectedApp] || [] : [];

  // Calculate risk factors from tech debt - MUST be at top level
  const riskFactors: RiskFactor[] = useMemo(() => {
    if (!currentAppTechDebt || currentAppTechDebt.length === 0) return [];

    return currentAppTechDebt.map(debt => ({
      category: debt.category,
      severity: debt.severity,
      description: debt.description,
      mitigation: debt.impact_on_migration
    }));
  }, [currentAppTechDebt]);

  // Calculate overall risk level - MUST be at top level
  const overallRiskLevel = useMemo(() => {
    const criticalCount = riskFactors.filter(r => r.severity === 'critical').length;
    const highCount = riskFactors.filter(r => r.severity === 'high').length;

    if (criticalCount > 0) return 'critical';
    if (highCount > 2) return 'high';
    if (highCount > 0) return 'medium';
    return 'low';
  }, [riskFactors]);

  // Prevent rendering until flow is hydrated (after all hooks)
  if (!flowId || state.status === 'idle') {
    return <div className="p-6 text-sm text-muted-foreground">Loading assessment...</div>;
  }

  // Show loading state while data is being fetched
  if (state.isLoading || !state.dataFetched) {
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

  const getStrategyIcon = (strategy: string) => {
    switch (strategy.toLowerCase()) {
      case 'rehost': return <Database className="h-4 w-4" />;
      case 'replatform': return <TrendingUp className="h-4 w-4" />;
      case 'refactor': return <GitBranch className="h-4 w-4" />;
      case 'repurchase': return <Shield className="h-4 w-4" />;
      case 'retire': return <XCircle className="h-4 w-4" />;
      case 'retain': return <CheckCircle className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getStrategyColor = (strategy: string) => {
    switch (strategy.toLowerCase()) {
      case 'rehost': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'replatform': return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'refactor': return 'bg-green-100 text-green-700 border-green-200';
      case 'repurchase': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'retire': return 'bg-red-100 text-red-700 border-red-200';
      case 'retain': return 'bg-gray-100 text-gray-700 border-gray-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getRiskSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-700 border-blue-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const handleAcceptRecommendation = async (appId: string) => {
    const decision = state.sixrDecisions[appId];
    if (!decision) return;

    try {
      await updateSixRDecision(appId, {
        ...decision,
        user_modifications: {
          accepted: true,
          accepted_at: new Date().toISOString()
        }
      });

      setAcceptedRecommendations(prev => new Set(prev).add(appId));
    } catch (error) {
      console.error('Failed to accept recommendation:', error);
    }
  };

  const handleSaveDraft = async (): void => {
    setIsDraft(true);
    try {
      // Draft is auto-saved via updateSixRDecision calls
      console.log('Draft auto-saved');
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsDraft(false);
    }
  };

  const handleSubmit = async (): void => {
    console.log('[SixRReview] handleSubmit called', {
      flowId,
      acceptedCount: acceptedRecommendations.size,
      totalApps: state.selectedApplicationIds.length,
      isSubmitting,
      isLoading: state.isLoading,
    });

    setIsSubmitting(true);
    try {
      console.log('[SixRReview] Resuming flow to next phase...');
      const resumeResponse = await resumeFlow({
        phase: 'risk_assessment',
        action: 'continue',
        data: {
          accepted_recommendations: Array.from(acceptedRecommendations)
        }
      });

      console.log('[SixRReview] Flow resumed successfully', {
        newPhase: resumeResponse.current_phase,
        progress: resumeResponse.progress,
      });

      // ADR-027: Map canonical phase name to frontend route
      const phaseToRouteMap: Record<string, string> = {
        'initialization': 'architecture',
        'readiness_assessment': 'architecture',
        'complexity_analysis': 'complexity',
        'dependency_analysis': 'dependency',
        'tech_debt_assessment': 'tech-debt',
        'risk_assessment': 'sixr-review',
        'recommendation_generation': 'app-on-page',
        'finalization': 'app-on-page',
      };

      const nextPhase = resumeResponse.current_phase;
      const routeName = phaseToRouteMap[nextPhase] || 'app-on-page';

      console.log('[SixRReview] Navigating to next phase', {
        currentPhase: nextPhase,
        routeName,
      });

      navigate(`/assessment/${flowId}/${routeName}`);
    } catch (error) {
      console.error('[SixRReview] Failed to continue to next phase:', error);
      alert(`Failed to continue: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const allRecommendationsReviewed = state.selectedApplicationIds.every(
    appId => acceptedRecommendations.has(appId) || !state.sixrDecisions[appId]
  );

  return (
    <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                6R Strategy Review
              </h1>
              <p className="text-gray-600">
                Review migration recommendations, dependencies, and risk assessment for selected applications
              </p>
            </div>
            <div className="flex items-center gap-2">
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
            </div>
          </div>
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
                AI agents are analyzing dependencies and assessing risks...
              </p>
            </div>
          </div>
        )}

        {/* Progress Indicator */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Review Progress</CardTitle>
              <Badge variant={allRecommendationsReviewed ? "default" : "secondary"}>
                {acceptedRecommendations.size} of {state.selectedApplicationIds.length} reviewed
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${(acceptedRecommendations.size / state.selectedApplicationIds.length) * 100}%`
                }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Application Tabs */}
        <Card>
          <CardHeader>
            <CardTitle>Select Application</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {state.selectedApplicationIds.map((appId) => {
                const isAccepted = acceptedRecommendations.has(appId);
                const hasDecision = !!state.sixrDecisions[appId];

                return (
                  <Button
                    key={appId}
                    variant={selectedApp === appId ? 'default' : 'outline'}
                    onClick={() => setSelectedApp(appId)}
                    className="relative"
                  >
                    {appId}
                    {isAccepted && (
                      <CheckCircle className="h-3 w-3 ml-2 text-green-600" />
                    )}
                    {!hasDecision && (
                      <Loader2 className="h-3 w-3 ml-2 animate-spin" />
                    )}
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {selectedApp && currentAppDecision && (
          <>
            {/* 6R Recommendation Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {getStrategyIcon(currentAppDecision.overall_strategy)}
                      Recommended Strategy: {currentAppDecision.overall_strategy}
                    </CardTitle>
                    <CardDescription>
                      Confidence Score: {Math.round((currentAppDecision.confidence_score || 0) * 100)}%
                    </CardDescription>
                  </div>
                  <Badge className={cn('text-sm', getStrategyColor(currentAppDecision.overall_strategy))}>
                    {currentAppDecision.overall_strategy.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold text-sm mb-2">Rationale</h4>
                  <p className="text-sm text-gray-700">{currentAppDecision.rationale}</p>
                </div>

                {currentAppDecision.architecture_exceptions && currentAppDecision.architecture_exceptions.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-sm mb-2">Architecture Exceptions</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {currentAppDecision.architecture_exceptions.map((exception, idx) => (
                        <li key={idx} className="text-sm text-gray-700">{exception}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {currentAppDecision.move_group_hints && currentAppDecision.move_group_hints.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-sm mb-2">Move Group Hints</h4>
                    <div className="flex flex-wrap gap-2">
                      {currentAppDecision.move_group_hints.map((hint, idx) => (
                        <Badge key={idx} variant="outline">{hint}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t">
                  <Button
                    onClick={() => handleAcceptRecommendation(selectedApp)}
                    disabled={acceptedRecommendations.has(selectedApp)}
                    className="w-full"
                  >
                    {acceptedRecommendations.has(selectedApp) ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Recommendation Accepted
                      </>
                    ) : (
                      <>
                        Accept Recommendation
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Analysis Tabs */}
            <Tabs defaultValue="components" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="components">
                  Components ({currentAppComponents.length})
                </TabsTrigger>
                <TabsTrigger value="dependencies">
                  Dependencies
                </TabsTrigger>
                <TabsTrigger value="risks">
                  Risks ({riskFactors.length})
                </TabsTrigger>
              </TabsList>

              {/* Components Tab */}
              <TabsContent value="components" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Component Treatment Strategies</CardTitle>
                    <CardDescription>
                      Individual migration strategies for application components
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {currentAppDecision.component_treatments && currentAppDecision.component_treatments.length > 0 ? (
                      <div className="space-y-4">
                        {currentAppDecision.component_treatments.map((treatment, idx) => (
                          <div key={idx} className="border rounded-lg p-4 space-y-2">
                            <div className="flex items-center justify-between">
                              <h4 className="font-semibold">{treatment.component_name}</h4>
                              <Badge className={getStrategyColor(treatment.recommended_strategy)}>
                                {treatment.recommended_strategy}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600">{treatment.component_type}</p>
                            <p className="text-sm text-gray-700">{treatment.rationale}</p>
                            {treatment.compatibility_validated && (
                              <div className="flex items-center gap-2 text-sm">
                                <CheckCircle className="h-4 w-4 text-green-600" />
                                <span className="text-green-700">Compatibility Validated</span>
                              </div>
                            )}
                            {treatment.compatibility_issues && treatment.compatibility_issues.length > 0 && (
                              <div className="mt-2">
                                <p className="text-sm font-medium text-red-700">Compatibility Issues:</p>
                                <ul className="list-disc list-inside text-sm text-red-600 ml-4">
                                  {treatment.compatibility_issues.map((issue, issueIdx) => (
                                    <li key={issueIdx}>{issue}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No component treatments available.</p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Dependencies Tab */}
              <TabsContent value="dependencies" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Network className="h-5 w-5" />
                      Dependency Analysis
                    </CardTitle>
                    <CardDescription>
                      Component dependencies and integration points
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {currentAppComponents.length > 0 ? (
                      <div className="space-y-4">
                        {currentAppComponents.map((component, idx) => (
                          <div key={idx} className="border rounded-lg p-4 space-y-2">
                            <h4 className="font-semibold">{component.component_name}</h4>
                            <p className="text-sm text-gray-600">{component.component_type}</p>
                            {component.dependencies && component.dependencies.length > 0 && (
                              <div>
                                <p className="text-sm font-medium">Dependencies:</p>
                                <div className="flex flex-wrap gap-2 mt-1">
                                  {component.dependencies.map((dep, depIdx) => (
                                    <Badge key={depIdx} variant="outline">{dep}</Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No component dependencies available.</p>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Risks Tab */}
              <TabsContent value="risks" className="space-y-4">
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Risk Assessment
                      </CardTitle>
                      <Badge className={cn('text-sm', getRiskSeverityColor(overallRiskLevel))}>
                        Overall Risk: {overallRiskLevel.toUpperCase()}
                      </Badge>
                    </div>
                    <CardDescription>
                      Identified risks and mitigation strategies
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {riskFactors.length > 0 ? (
                      <div className="space-y-4">
                        {riskFactors.map((risk, idx) => (
                          <div key={idx} className={cn('border rounded-lg p-4 space-y-2', getRiskSeverityColor(risk.severity))}>
                            <div className="flex items-center justify-between">
                              <h4 className="font-semibold">{risk.category}</h4>
                              <Badge className={getRiskSeverityColor(risk.severity)}>
                                {risk.severity.toUpperCase()}
                              </Badge>
                            </div>
                            <p className="text-sm">{risk.description}</p>
                            {risk.mitigation && (
                              <div className="mt-2 pt-2 border-t">
                                <p className="text-sm font-medium">Mitigation:</p>
                                <p className="text-sm text-gray-700">{risk.mitigation}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <CheckCircle className="h-12 w-12 mx-auto text-green-600 mb-4" />
                        <p className="text-sm text-muted-foreground">No significant risks identified.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={handleSaveDraft}
              disabled={isDraft}
            >
              <Save className="h-4 w-4 mr-2" />
              {isDraft ? 'Saving...' : 'Save Progress'}
            </Button>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || state.isLoading || !allRecommendationsReviewed}
            size="lg"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                Continue to App-on-Page Generation
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </AssessmentFlowLayout>
  );
};

export default SixRStrategyReview;
