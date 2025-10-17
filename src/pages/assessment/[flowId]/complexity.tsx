import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ApplicationTabs } from '@/components/assessment/ApplicationTabs';
import { RealTimeProgressIndicator } from '@/components/assessment/RealTimeProgressIndicator';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ArrowRight, Loader2, BarChart3, Code2, TrendingUp, AlertTriangle } from 'lucide-react';

/**
 * Complexity Analysis Page
 *
 * Per ADR-027: complexity_analysis phase
 * Shows code complexity metrics, maintainability index, cyclomatic complexity
 */
const ComplexityPage: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const navigate = useNavigate();
  const { state, resumeFlow } = useAssessmentFlow(flowId);

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  // Prevent rendering until flow is hydrated
  if (!flowId || state.status === 'idle') {
    return <div className="p-6 text-sm text-muted-foreground">Loading assessment...</div>;
  }

  // Get current application data
  const currentApp = useMemo(() => {
    return state.selectedApplications.find(app => app.application_id === selectedApp);
  }, [selectedApp, state.selectedApplications]);

  // Calculate complexity metrics (placeholder until backend provides real data)
  const complexityMetrics = useMemo(() => {
    if (!currentApp) return null;

    // TODO: Replace with actual complexity data from backend
    return {
      cyclomaticComplexity: currentApp.complexity_score * 10 || 0,
      maintainabilityIndex: Math.max(0, 100 - (currentApp.complexity_score * 8)) || 0,
      linesOfCode: Math.floor(Math.random() * 100000) + 10000,
      technicalDebtRatio: currentApp.complexity_score * 5 || 0,
      codeSmells: Math.floor(currentApp.complexity_score * 3) || 0,
    };
  }, [currentApp]);

  const handleSubmit = async (): void => {
    console.log('[ComplexityPage] Submitting complexity analysis...');
    setIsSubmitting(true);

    try {
      const resumeResponse = await resumeFlow({
        phase: 'complexity_analysis',
        action: 'continue',
      });

      console.log('[ComplexityPage] Flow resumed successfully', {
        newPhase: resumeResponse.current_phase,
        progress: resumeResponse.progress,
      });

      // ADR-027: Map canonical phase name to frontend route
      const phaseToRouteMap: Record<string, string> = {
        'readiness_assessment': 'architecture',
        'complexity_analysis': 'complexity',
        'dependency_analysis': 'dependency',
        'tech_debt_assessment': 'tech-debt',
        'risk_assessment': 'sixr-review',
        'recommendation_generation': 'app-on-page',
      };

      const nextPhase = resumeResponse.current_phase;
      const routeName = phaseToRouteMap[nextPhase] || 'dependency';

      console.log('[ComplexityPage] Navigating to next phase', {
        currentPhase: nextPhase,
        routeName,
      });

      navigate(`/assessment/${flowId}/${routeName}`);
    } catch (error) {
      console.error('[ComplexityPage] Failed to submit complexity analysis:', error);
      alert(`Failed to continue: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getComplexityColor = (score: number): string => {
    if (score >= 8) return 'text-red-600';
    if (score >= 6) return 'text-orange-600';
    if (score >= 4) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getMaintainabilityColor = (score: number): string => {
    if (score >= 75) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    if (score >= 25) return 'text-orange-600';
    return 'text-red-600';
  };

  if (state.selectedApplicationIds.length === 0) {
    return (
      <SidebarProvider>
        <AssessmentFlowLayout flowId={flowId}>
          <div className="p-6 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No Applications Selected</h2>
            <p className="text-gray-600">Please return to the previous step to select applications for analysis.</p>
          </div>
        </AssessmentFlowLayout>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <AssessmentFlowLayout flowId={flowId}>
        <div className="p-6 max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-gray-900">
              Complexity Analysis
            </h1>
            <p className="text-gray-600">
              Analyze code complexity metrics, maintainability index, and cyclomatic complexity
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
                  AI agents are analyzing code complexity...
                </p>
              </div>
            </div>
          )}

          {/* Real-time Progress */}
          {state.status === 'processing' && (
            <RealTimeProgressIndicator
              agentUpdates={state.agentUpdates}
              currentPhase="complexity_analysis"
            />
          )}

          {/* Application Selection */}
          <ApplicationTabs
            applications={state.selectedApplicationIds}
            selectedApp={selectedApp}
            onAppSelect={setSelectedApp}
            getApplicationName={(appId) => {
              const app = state.selectedApplications.find(a => a.application_id === appId);
              return app?.application_name || appId;
            }}
          />

          {selectedApp && currentApp && complexityMetrics && (
            <>
              {/* Complexity Overview Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5" />
                    <span>Complexity Overview</span>
                  </CardTitle>
                  <CardDescription>
                    Key complexity metrics for {currentApp.application_name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Complexity Score */}
                    <div className="text-center p-4 border rounded-lg">
                      <Code2 className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                      <div className={`text-3xl font-bold ${getComplexityColor(currentApp.complexity_score)}`}>
                        {currentApp.complexity_score}/10
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Complexity Score</div>
                      <Badge variant={currentApp.complexity_score >= 7 ? 'destructive' : 'secondary'} className="mt-2">
                        {currentApp.complexity_score >= 7 ? 'High' : currentApp.complexity_score >= 4 ? 'Medium' : 'Low'}
                      </Badge>
                    </div>

                    {/* Maintainability Index */}
                    <div className="text-center p-4 border rounded-lg">
                      <TrendingUp className="h-8 w-8 mx-auto mb-2 text-green-600" />
                      <div className={`text-3xl font-bold ${getMaintainabilityColor(complexityMetrics.maintainabilityIndex)}`}>
                        {Math.round(complexityMetrics.maintainabilityIndex)}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Maintainability Index</div>
                      <Badge
                        variant={complexityMetrics.maintainabilityIndex >= 50 ? 'secondary' : 'destructive'}
                        className="mt-2"
                      >
                        {complexityMetrics.maintainabilityIndex >= 75 ? 'Excellent' :
                         complexityMetrics.maintainabilityIndex >= 50 ? 'Good' :
                         complexityMetrics.maintainabilityIndex >= 25 ? 'Fair' : 'Poor'}
                      </Badge>
                    </div>

                    {/* Cyclomatic Complexity */}
                    <div className="text-center p-4 border rounded-lg">
                      <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-orange-600" />
                      <div className="text-3xl font-bold text-orange-600">
                        {Math.round(complexityMetrics.cyclomaticComplexity)}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Cyclomatic Complexity</div>
                      <Badge variant="outline" className="mt-2">
                        Avg per Function
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Detailed Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Metrics</CardTitle>
                  <CardDescription>
                    Code quality and technical debt indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium">Lines of Code</span>
                      <span className="text-sm font-semibold">{complexityMetrics.linesOfCode.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium">Technical Debt Ratio</span>
                      <span className="text-sm font-semibold">{complexityMetrics.technicalDebtRatio.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium">Code Smells</span>
                      <span className="text-sm font-semibold">{complexityMetrics.codeSmells}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Technology Stack */}
              {currentApp.technology_stack && currentApp.technology_stack.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Technology Stack</CardTitle>
                    <CardDescription>
                      Technologies used in {currentApp.application_name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {currentApp.technology_stack.map((tech, idx) => (
                        <Badge key={idx} variant="outline">
                          {tech}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end items-center pt-6 border-t border-gray-200">
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
                  Continue to Dependency Analysis
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </div>
        </div>
      </AssessmentFlowLayout>
    </SidebarProvider>
  );
};

export default ComplexityPage;
