import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { RealTimeProgressIndicator } from '@/components/assessment/RealTimeProgressIndicator';
import { DependencyManagementTable } from '@/components/assessment/DependencyManagementTable';
import { DependencyGraph } from '@/components/assessment/DependencyGraph';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { assessmentDependencyApi } from '@/lib/api/assessmentDependencyApi';
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

  // Guard: redirect to overview if flowId missing
  useEffect(() => {
    if (!flowId) {
      navigate('/assess/overview', { replace: true });
    }
  }, [flowId, navigate]);

  // Fetch dependency analysis with React Query
  const { data: dependencyData, isLoading: isDependencyLoading, refetch } = useQuery({
    queryKey: ['assessment-dependency', flowId],
    queryFn: () => assessmentDependencyApi.getDependencyAnalysis(flowId),
    enabled: !!flowId && flowId !== 'XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX',
    refetchInterval: (data, query) => {
      // Stop polling if the query has failed
      if (query.state.status === 'error') {
        return false;
      }

      // BUG FIX: Use proper comparison (NOT !!status === 'completed')
      // Poll every 5s if phase is running, 15s otherwise, stop when completed/failed
      if (!data) return 5000;
      const status = data.agent_results?.status;
      if (status === 'completed' || status === 'failed') return false; // Stop polling when complete or failed

      // BUG FIX: Check for 'running' status (NOT 'processing')
      return status === 'running' ? 5000 : 15000;
    },
    staleTime: 0, // Always fresh for status checks
  });

  // Prevent rendering until flow is hydrated
  if (!flowId || state.status === 'idle') {
    return <div className="p-6 text-sm text-muted-foreground">Loading assessment...</div>;
  }

  // Extract dependency information from dependencyData
  const dependencyGraph = dependencyData?.dependency_graph;
  const appServerDependencies = dependencyData?.app_server_dependencies || [];
  const appAppDependencies = dependencyData?.app_app_dependencies || [];
  const agentResults = dependencyData?.agent_results;

  // BUG FIX: Use proper status check (status === 'completed' NOT !!status === 'completed')
  const isDependencyAnalysisComplete = agentResults?.status === 'completed';

  const handleRefresh = () => {
    console.log('[DependencyPage] Refresh dependency analysis');
    refetch();
  };

  // Use useMutation for executing dependency analysis (prevents race conditions)
  const { mutate: executeAnalysis, isPending: isAnalyzing } = useMutation({
    mutationFn: () => assessmentDependencyApi.executeDependencyAnalysis(flowId),
    onSuccess: () => {
      console.log('[DependencyPage] Dependency analysis execution started');
      // Refetch after a short delay to allow backend to update status
      setTimeout(() => {
        refetch();
      }, 2000);
    },
    onError: (error: unknown) => {
      console.error('[DependencyPage] Failed to execute dependency analysis:', error);
      alert(`Failed to execute analysis: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const handleExecuteAnalysis = () => {
    console.log('[DependencyPage] Executing dependency analysis...');
    executeAnalysis();
  };

  const handleUpdateDependencies = async (applicationId: string, dependencies: string | null) => {
    console.log('[DependencyPage] Updating dependencies:', { applicationId, dependencies });

    try {
      await assessmentDependencyApi.updateDependencies(flowId, applicationId, dependencies);
      console.log('[DependencyPage] Dependencies updated successfully');

      // Refetch to get updated dependency graph
      refetch();
    } catch (error) {
      console.error('[DependencyPage] Failed to update dependencies:', error);
      alert(`Failed to update dependencies: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
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
                disabled={isDependencyLoading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isDependencyLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleExecuteAnalysis}
                disabled={isAnalyzing || agentResults?.status === 'running'}
              >
                {isAnalyzing || agentResults?.status === 'running' ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Run Analysis
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Status Alert */}
          {state.status === 'error' && (
            <div className="flex items-center space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <p className="text-sm text-red-600">{state.error}</p>
            </div>
          )}

          {/* BUG FIX: Check for 'running' status instead of 'processing' */}
          {agentResults?.status === 'running' && (
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
          {agentResults?.status === 'running' && (
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
                ) : agentResults?.status === 'running' ? (
                  <>
                    <Badge variant="secondary">Running</Badge>
                    <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />
                    <span className="text-yellow-700">Analysis in progress...</span>
                  </>
                ) : (
                  <>
                    <Badge variant="outline">Pending</Badge>
                    <AlertCircle className="h-4 w-4 text-gray-500" />
                    <span className="text-gray-700">Analysis not yet started</span>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Dependency Statistics */}
          {dependencyGraph && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Network className="mr-2 h-5 w-5" />
                  Dependency Overview
                </CardTitle>
                <CardDescription>
                  Summary of application and server dependencies
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {dependencyGraph.metadata.dependency_count}
                    </div>
                    <div className="text-sm text-gray-600">Total Dependencies</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {dependencyGraph.metadata.app_count}
                    </div>
                    <div className="text-sm text-gray-600">Applications</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {dependencyGraph.metadata.server_count}
                    </div>
                    <div className="text-sm text-gray-600">Servers</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {dependencyGraph.metadata.node_count}
                    </div>
                    <div className="text-sm text-gray-600">Total Nodes</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Info Card - Show when no data yet */}
          {!dependencyGraph && !isDependencyLoading && (
            <Card className="border-blue-200 bg-blue-50">
              <CardContent className="pt-6">
                <div className="flex items-start">
                  <AlertCircle className="mr-2 h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-blue-900 font-medium">Dependency Analysis</p>
                    <p className="text-blue-700 text-sm mt-1">
                      The dependency analysis phase can be executed in two ways:
                    </p>
                    <ul className="text-blue-700 text-sm mt-2 list-disc list-inside space-y-1">
                      <li><strong>Auto-execution:</strong> Navigating from the complexity page triggers analysis automatically</li>
                      <li><strong>Manual execution:</strong> Click "Run Analysis" button to execute or re-run the analysis</li>
                    </ul>
                    <p className="text-blue-700 text-sm mt-2">
                      The analysis identifies:
                    </p>
                    <ul className="text-blue-700 text-sm mt-2 list-disc list-inside space-y-1">
                      <li>Application-Server dependencies (hosting relationships)</li>
                      <li>Application-Application dependencies (communication patterns)</li>
                      <li>Critical dependencies that impact migration sequencing</li>
                      <li>Dependency complexity and risk factors</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Visual Dependency Graph - Show when we have graph data */}
          {dependencyGraph && dependencyGraph.nodes.length > 0 && (
            <DependencyGraph dependencyGraph={dependencyGraph} height={600} />
          )}

          {/* Dependency Management Table */}
          {dependencyData && dependencyData.applications && dependencyData.applications.length > 0 && (
            <DependencyManagementTable
              applications={dependencyData.applications}
              onUpdateDependencies={handleUpdateDependencies}
            />
          )}

          {/* Results - Show when we have dependency data */}
          {dependencyData && appServerDependencies.length + appAppDependencies.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* App-Server Dependencies */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Server className="mr-2 h-5 w-5" />
                    Application-Server Dependencies
                  </CardTitle>
                  <CardDescription>
                    Hosting relationships ({appServerDependencies.length} total)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appServerDependencies.length > 0 ? (
                    <div className="space-y-3">
                      {appServerDependencies.slice(0, 5).map((dep: any, index: number) => (
                        <div key={dep.dependency_id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <p className="font-medium">{dep.application_name || 'Unknown Application'}</p>
                            <p className="text-sm text-gray-600">
                              {dep.server_info?.hostname || dep.server_info?.name || 'Unknown Server'}
                            </p>
                            {dep.dependency_type && (
                              <Badge variant="outline" className="mt-1 text-xs">
                                {dep.dependency_type}
                              </Badge>
                            )}
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
                    Communication patterns ({appAppDependencies.length} total)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appAppDependencies.length > 0 ? (
                    <div className="space-y-3">
                      {appAppDependencies.slice(0, 5).map((dep: any, index: number) => (
                        <div key={dep.dependency_id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <p className="font-medium">{dep.source_app_name || 'Unknown Source'}</p>
                            <p className="text-sm text-gray-600">
                              → {dep.target_app_info?.application_name || dep.target_app_info?.name || 'Unknown Target'}
                            </p>
                            {dep.dependency_type && (
                              <Badge variant="outline" className="mt-1 text-xs">
                                {dep.dependency_type}
                              </Badge>
                            )}
                          </div>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
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
