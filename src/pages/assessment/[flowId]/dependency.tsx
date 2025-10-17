import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { RealTimeProgressIndicator } from '@/components/assessment/RealTimeProgressIndicator';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Network,
  Server,
  Database,
  ArrowRight,
  AlertCircle,
  Loader2,
  RefreshCw,
  Play
} from 'lucide-react';

/**
 * Dependency Analysis Page
 *
 * Per ADR-027: dependency_analysis phase
 * Shows application-server and application-application dependencies
 */

// Type definitions for dependency analysis data
interface AppServerDependency {
  application: string;
  server: string;
}

interface AppAppDependency {
  source: string;
  target: string;
  type: string;
}

const DependencyPage: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const navigate = useNavigate();
  const { state, resumeFlow } = useAssessmentFlow(flowId);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Guard: redirect to overview if flowId missing
  useEffect(() => {
    if (!flowId) {
      navigate('/assess/overview', { replace: true });
    }
  }, [flowId, navigate]);

  // Prevent rendering until flow is hydrated
  if (!flowId || state.status === 'idle') {
    return <div className="p-6 text-sm text-muted-foreground">Loading assessment...</div>;
  }

  // TODO: Replace with actual dependency data from backend
  const dependencyData = null;
  const isDependencyAnalysisComplete = false;

  // Extract dependency information from dependencyData
  const appServerDependencies = dependencyData?.app_server_mapping || [];
  const appAppDependencies = dependencyData?.cross_application_mapping || [];
  const dependencyRelationships = dependencyData?.dependency_relationships || [];
  const criticalDependencies = dependencyData?.critical_dependencies || [];

  const handleRefresh = () => {
    console.log('[DependencyPage] Refresh dependency analysis');
    // TODO: Implement refresh logic
  };

  const handleExecuteDependencyAnalysis = () => {
    console.log('[DependencyPage] Execute dependency analysis');
    setIsAnalyzing(true);
    // TODO: Trigger dependency analysis
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const handleSubmit = async (): void => {
    console.log('[DependencyPage] Submitting dependency analysis...');
    setIsSubmitting(true);

    try {
      const resumeResponse = await resumeFlow({
        phase: 'dependency_analysis',
        action: 'continue',
      });

      console.log('[DependencyPage] Flow resumed successfully', {
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
      const routeName = phaseToRouteMap[nextPhase] || 'tech-debt';

      console.log('[DependencyPage] Navigating to next phase', {
        currentPhase: nextPhase,
        routeName,
      });

      navigate(`/assessment/${flowId}/${routeName}`);
    } catch (error) {
      console.error('[DependencyPage] Failed to submit dependency analysis:', error);
      alert(`Failed to continue: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
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
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <h1 className="text-2xl font-bold text-gray-900">Dependency Analysis</h1>
              <p className="text-gray-600">
                Analyze application and server dependencies to understand migration complexity
              </p>
            </div>
            <div className="flex space-x-2 mt-4 md:mt-0">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={state.isLoading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${state.isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              {!isDependencyAnalysisComplete && (
                <Button
                  onClick={handleExecuteDependencyAnalysis}
                  disabled={isAnalyzing}
                >
                  <Play className="mr-2 h-4 w-4" />
                  {isAnalyzing ? 'Analyzing...' : 'Start Analysis'}
                </Button>
              )}
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
                  AI agents are analyzing dependencies...
                </p>
              </div>
            </div>
          )}

          {/* Real-time Progress */}
          {state.status === 'processing' && (
            <RealTimeProgressIndicator
              agentUpdates={state.agentUpdates}
              currentPhase="dependency_analysis"
            />
          )}

          {/* Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Network className="mr-2 h-5 w-5" />
                Analysis Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-4">
                {isDependencyAnalysisComplete ? (
                  <>
                    <Badge variant="secondary">Complete</Badge>
                    <span className="text-green-700">Dependency analysis completed</span>
                  </>
                ) : isAnalyzing ? (
                  <>
                    <Badge variant="secondary">Running</Badge>
                    <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />
                    <span className="text-yellow-700">Analysis in progress...</span>
                  </>
                ) : (
                  <>
                    <Badge variant="outline">Pending</Badge>
                    <AlertCircle className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-700">Ready to start dependency analysis</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Placeholder Info */}
          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="pt-6">
              <div className="flex items-start">
                <AlertCircle className="mr-2 h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-blue-900 font-medium">Dependency Analysis Integration</p>
                  <p className="text-blue-700 text-sm mt-1">
                    This dependency analysis page is part of the Assessment flow (ADR-027 phase: dependency_analysis).
                    Integration with backend dependency analysis services is in progress. The page will display:
                  </p>
                  <ul className="text-blue-700 text-sm mt-2 list-disc list-inside space-y-1">
                    <li>Application-Server dependencies (hosting relationships)</li>
                    <li>Application-Application dependencies (communication patterns)</li>
                    <li>Inter-application dependencies and integration points</li>
                    <li>Critical dependencies that impact migration sequencing</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          {isDependencyAnalysisComplete && dependencyData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* App-Server Dependencies */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Server className="mr-2 h-5 w-5" />
                    Application-Server Dependencies
                  </CardTitle>
                  <CardDescription>
                    Hosting relationships and resource mappings
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appServerDependencies.length > 0 ? (
                    <div className="space-y-3">
                      {appServerDependencies.slice(0, 5).map((relationship: AppServerDependency, index: number) => (
                        <div key={`${relationship.application}-${relationship.server}-${index}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium">{relationship.application || `App ${index + 1}`}</p>
                            <p className="text-sm text-gray-600">{relationship.server || `Server ${index + 1}`}</p>
                          </div>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </div>
                      ))}
                      {appServerDependencies.length > 5 && (
                        <p className="text-sm text-gray-600">
                          +{appServerDependencies.length - 5} more relationships
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-600">No hosting relationships found</p>
                  )}
                </CardContent>
              </Card>

              {/* App-App Dependencies */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Database className="mr-2 h-5 w-5" />
                    Application-Application Dependencies
                  </CardTitle>
                  <CardDescription>
                    Communication patterns and API dependencies
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appAppDependencies.length > 0 ? (
                    <div className="space-y-3">
                      {appAppDependencies.slice(0, 5).map((pattern: AppAppDependency, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium">{pattern.source || `Source ${index + 1}`}</p>
                            <p className="text-sm text-gray-600">{pattern.target || `Target ${index + 1}`}</p>
                          </div>
                          <Badge variant="outline">{pattern.type || 'API'}</Badge>
                        </div>
                      ))}
                      {appAppDependencies.length > 5 && (
                        <p className="text-sm text-gray-600">
                          +{appAppDependencies.length - 5} more patterns
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-600">No communication patterns found</p>
                  )}
                </CardContent>
              </Card>
            </div>
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
                  Continue to Tech Debt Assessment
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

export default DependencyPage;
