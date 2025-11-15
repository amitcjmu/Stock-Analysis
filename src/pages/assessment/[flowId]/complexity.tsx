import React, { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ApplicationTabs } from '@/components/assessment/ApplicationTabs';
import { RealTimeProgressIndicator } from '@/components/assessment/RealTimeProgressIndicator';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { apiClient } from '@/lib/api/apiClient';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, ArrowRight, Loader2, BarChart3, Code2, TrendingUp, AlertTriangle, Save } from 'lucide-react';

/**
 * Complexity Analysis Page
 *
 * Per ADR-027: complexity_analysis phase
 * Shows code complexity metrics, maintainability index, cyclomatic complexity
 */
const ComplexityPage: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const navigate = useNavigate();
  const { state, resumeFlow, toggleAutoPolling } = useAssessmentFlow(flowId, { disableAutoPolling: true });

  const [selectedApp, setSelectedApp] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Editable complexity fields (user can adjust)
  const [complexityScore, setComplexityScore] = useState<number>(1);
  const [architectureType, setArchitectureType] = useState<string>('Monolithic');
  const [customizationLevel, setCustomizationLevel] = useState<string>('Medium');
  const [isSaving, setIsSaving] = useState(false);

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

  // Get current application data - MUST be defined before useEffect that depends on it
  const currentApp = useMemo(() => {
    return state.selectedApplications.find(app => app.application_id === selectedApp);
  }, [selectedApp, state.selectedApplications]);

  // Initialize editable fields from currentApp data
  useEffect(() => {
    if (currentApp) {
      setComplexityScore(currentApp.complexity_score || 1);
      setArchitectureType(currentApp.application_type || 'Monolithic');
      setCustomizationLevel(currentApp.customization_level || 'Medium');
    }
  }, [currentApp]);

  // Prevent rendering until flow is hydrated
  if (!flowId || state.status === 'idle') {
    return <div className="p-6 text-sm text-muted-foreground">Loading assessment...</div>;
  }

  // Calculate architectural complexity metrics from CMDB/Discovery data
  // Uses editable state values that user can adjust
  const complexityMetrics = useMemo(() => {
    if (!currentApp) return null;

    // Architectural complexity based on CMDB data (NOT code metrics)
    const componentCount = currentApp.technology_stack?.length || 0;
    const hasDatabase = currentApp.technology_stack?.some((tech: string) =>
      tech.toLowerCase().includes('database') ||
      tech.toLowerCase().includes('sql') ||
      tech.toLowerCase().includes('oracle') ||
      tech.toLowerCase().includes('postgres')
    ) || false;

    // Calculate integration count from dependencies array (read-only)
    const integrationCount = (currentApp.dependencies?.length || 0) + (currentApp.dependents?.length || 0);

    return {
      architectureType: architectureType,  // From editable state
      componentCount: componentCount,
      integrationCount: integrationCount,  // Calculated from dependencies (read-only)
      customizationLevel: customizationLevel,  // From editable state
      migrationGroup: currentApp.migration_group || 'Not Assigned',
      hasDatabase: hasDatabase,
      complexityScore: complexityScore,  // From editable state
    };
  }, [currentApp, architectureType, customizationLevel, complexityScore]);

  const handleSaveMetrics = async (): Promise<void> => {
    if (!selectedApp) {
      console.warn('[ComplexityPage] No application selected');
      return;
    }

    console.log('[ComplexityPage] Saving complexity metrics...');
    setIsSaving(true);

    try {
      // CRITICAL: Use apiClient for multi-tenant security headers
      // Per CLAUDE.md - PUT requests use request body, NOT query parameters
      const result = await apiClient.put(
        `/api/v1/master-flows/${flowId}/applications/${selectedApp}/complexity-metrics`,
        {
          complexity_score: complexityScore,
          architecture_type: architectureType,
          customization_level: customizationLevel,
        }
      );

      console.log('[ComplexityPage] Metrics saved successfully', result);

      // Show success feedback
      alert('Complexity metrics saved successfully!');
    } catch (error) {
      console.error('[ComplexityPage] Failed to save metrics:', error);
      alert(`Failed to save metrics: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

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

  const getArchitectureTypeColor = (type: string): string => {
    if (type.toLowerCase().includes('microservice')) return 'text-orange-600';
    if (type.toLowerCase().includes('soa')) return 'text-yellow-600';
    return 'text-blue-600';  // Monolithic
  };

  const getCustomizationLevelColor = (level: string): string => {
    if (level.toLowerCase() === 'high') return 'text-red-600';
    if (level.toLowerCase() === 'medium') return 'text-yellow-600';
    return 'text-green-600';
  };

  // CC: Fixed bug - check selectedApplications (populated) not selectedApplicationIds (may be empty)
  // Bug #640 fix (also applies to Issue #8): Check loading state before showing error
  // Don't show "No Applications Selected" error while data is still loading
  if (state.selectedApplications.length === 0) {
    // If still loading, show loading indicator instead of error
    if (state.isLoading) {
      return <div className="p-6 text-sm text-muted-foreground">Loading application data...</div>;
    }

    // Only show error if loading is complete and still no applications
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
              Migration Complexity Analysis
            </h1>
            <p className="text-gray-600">
              Analyze architectural complexity, integration points, and migration readiness (based on CMDB data, not code scanning)
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
                  AI agents are analyzing architectural migration complexity...
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

          {/* Auto-Polling Control */}
          <div className="flex items-center justify-end gap-2 mb-4">
            <span className="text-sm text-muted-foreground">Auto-refresh:</span>
            <Button
              variant={state.autoPollingEnabled ? "default" : "outline"}
              size="sm"
              onClick={toggleAutoPolling}
              className="gap-2"
            >
              {state.autoPollingEnabled ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></span>
                  On
                </>
              ) : (
                <>Off</>
              )}
            </Button>
          </div>

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
              {/* Migration Complexity Overview Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5" />
                    <span>Migration Complexity Overview</span>
                  </CardTitle>
                  <CardDescription>
                    Architectural complexity analysis for {currentApp.application_name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Overall Migration Complexity */}
                    <div className="text-center p-4 border rounded-lg">
                      <Code2 className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                      <div className={`text-3xl font-bold ${getComplexityColor(complexityScore)}`}>
                        {complexityScore}/10
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Migration Complexity</div>
                      <Badge variant={complexityScore >= 7 ? 'destructive' : 'secondary'} className="mt-2">
                        {complexityScore >= 7 ? 'High' : complexityScore >= 4 ? 'Medium' : 'Low'}
                      </Badge>
                    </div>

                    {/* Architecture Type */}
                    <div className="text-center p-4 border rounded-lg">
                      <TrendingUp className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                      <div className={`text-2xl font-bold ${getArchitectureTypeColor(complexityMetrics.architectureType)}`}>
                        {complexityMetrics.architectureType}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Architecture Type</div>
                      <Badge variant="outline" className="mt-2">
                        {complexityMetrics.hasDatabase ? 'With Database' : 'Stateless'}
                      </Badge>
                    </div>

                    {/* Customization Level */}
                    <div className="text-center p-4 border rounded-lg">
                      <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-orange-600" />
                      <div className={`text-2xl font-bold ${getCustomizationLevelColor(complexityMetrics.customizationLevel)}`}>
                        {complexityMetrics.customizationLevel}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">Customization Level</div>
                      <Badge variant={complexityMetrics.customizationLevel === 'High' ? 'destructive' : 'outline'} className="mt-2">
                        Custom Code Impact
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Architectural Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Architectural Details</CardTitle>
                  <CardDescription>
                    Component and integration complexity indicators
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium">Technology Components</span>
                      <span className="text-sm font-semibold">{complexityMetrics.componentCount} components</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium">Integration Points</span>
                      <span className="text-sm font-semibold">{complexityMetrics.integrationCount} integrations</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm font-medium">Migration Group</span>
                      <span className="text-sm font-semibold">{complexityMetrics.migrationGroup}</span>
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

              {/* Adjust Complexity Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle>Adjust Complexity Metrics</CardTitle>
                  <CardDescription>
                    Update values below to see real-time changes in the tiles above
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Complexity Score Dropdown */}
                    <div className="space-y-2">
                      <Label htmlFor="complexity-score">Migration Complexity Score</Label>
                      <Select
                        value={complexityScore.toString()}
                        onValueChange={(value) => setComplexityScore(parseInt(value))}
                      >
                        <SelectTrigger id="complexity-score">
                          <SelectValue placeholder="Select complexity score" />
                        </SelectTrigger>
                        <SelectContent>
                          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => (
                            <SelectItem key={score} value={score.toString()}>
                              {score}/10 - {score >= 7 ? 'High' : score >= 4 ? 'Medium' : 'Low'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Architecture Type Dropdown */}
                    <div className="space-y-2">
                      <Label htmlFor="architecture-type">Architecture Type</Label>
                      <Select
                        value={architectureType}
                        onValueChange={setArchitectureType}
                      >
                        <SelectTrigger id="architecture-type">
                          <SelectValue placeholder="Select architecture type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Monolithic">Monolithic</SelectItem>
                          <SelectItem value="Microservices">Microservices</SelectItem>
                          <SelectItem value="SOA">SOA (Service-Oriented Architecture)</SelectItem>
                          <SelectItem value="Serverless">Serverless</SelectItem>
                          <SelectItem value="Event-Driven">Event-Driven</SelectItem>
                          <SelectItem value="Layered">Layered</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Customization Level Dropdown */}
                    <div className="space-y-2">
                      <Label htmlFor="customization-level">Customization Level</Label>
                      <Select
                        value={customizationLevel}
                        onValueChange={setCustomizationLevel}
                      >
                        <SelectTrigger id="customization-level">
                          <SelectValue placeholder="Select customization level" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Low">Low - Minimal custom code</SelectItem>
                          <SelectItem value="Medium">Medium - Moderate customization</SelectItem>
                          <SelectItem value="High">High - Extensive custom code</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Save Button */}
                  <div className="flex justify-end mt-4">
                    <Button
                      onClick={handleSaveMetrics}
                      disabled={isSaving || !selectedApp}
                      variant="outline"
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4 mr-2" />
                          Save Metrics
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
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
