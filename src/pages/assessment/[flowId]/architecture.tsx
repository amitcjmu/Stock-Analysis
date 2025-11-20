import React, { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AssessmentFlowLayout } from '@/components/assessment/AssessmentFlowLayout';
import { ArchitectureStandardsForm } from '@/components/assessment/ArchitectureStandardsForm';
import { TemplateSelector } from '@/components/assessment/TemplateSelector';
import { ApplicationOverrides } from '@/components/assessment/ApplicationOverrides';
import { BulkAssetMappingDialog } from '@/components/assessment/BulkAssetMappingDialog';
import { useAssessmentFlow } from '@/hooks/useAssessmentFlow';
import { assessmentFlowAPI } from '@/hooks/useAssessmentFlow/api';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Save, ArrowRight, Package, Calendar, Star, Zap, RefreshCw, Loader2, Link } from 'lucide-react';
import type { AssessmentApplication } from '@/hooks/useAssessmentFlow/types';
import { toast } from '@/hooks/use-toast';

const ArchitecturePage: React.FC = () => {
  const { flowId } = useParams<{ flowId: string }>() as { flowId: string };
  const {
    state,
    updateArchitectureStandards,
    resumeFlow,
    refreshApplicationData,
    toggleAutoPolling
  } = useAssessmentFlow(flowId, { disableAutoPolling: true });
  const navigate = useNavigate();
  const { client, engagement } = useAuth();

  const [standards, setStandards] = useState(state.engagementStandards);
  const [overrides, setOverrides] = useState(state.applicationOverrides);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(state.selectedTemplate);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDraft, setIsDraft] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isEnriching, setIsEnriching] = useState(false);
  const [showBulkMapping, setShowBulkMapping] = useState(false);
  const [enrichmentProgress, setEnrichmentProgress] = useState<{
    compliance_flags: number;
    licenses: number;
    vulnerabilities: number;
    resilience: number;
    dependencies: number;
    product_links: number;
  } | null>(null);

  // Guard: redirect to overview if flowId missing
  useEffect(() => {
    if (!flowId) {
      navigate('/assess/overview', { replace: true });
    }
  }, [flowId, navigate]);

  // Update local state when flow state changes - MUST be at top level
  // Note: Removed duplicate useEffect that directly fetched data to prevent race condition
  // The useAssessmentFlow hook is the single source of truth for architecture data
  useEffect(() => {
    setStandards(state.engagementStandards);
    setOverrides(state.applicationOverrides);

    // Determine template selection based on the hook's state
    let templateToSet = state.selectedTemplate;
    if (!templateToSet && state.engagementStandards && state.engagementStandards.length > 0) {
      // Standards exist but no template saved - mark as custom
      templateToSet = "custom";
    }
    setSelectedTemplate(templateToSet);
  }, [state.engagementStandards, state.applicationOverrides, state.selectedTemplate]);

  // Calculate unmapped assets for bulk mapping dialog - MUST be before early return
  const unmappedAssets = useMemo(() => {
    return state.selectedApplications
      .filter((app: AssessmentApplication) => {
        // Check if the application has a canonical_application_id field
        // If not present or null, it's unmapped
        const appWithCanonicalId = app as AssessmentApplication & { canonical_application_id?: string | null };
        return !appWithCanonicalId.canonical_application_id;
      })
      .map((app: AssessmentApplication) => ({
        asset_id: app.application_id,
        asset_name: app.application_name,
        asset_type: app.application_type || 'unknown',
        technology_stack: app.technology_stack || [],
      }));
  }, [state.selectedApplications]);

  // Prevent rendering until flow is hydrated
  if (!flowId || state.status === 'idle') {
    return <div className="p-6 text-sm text-muted-foreground">Loading assessment...</div>;
  }

  const handleSaveDraft = async (): void => {
    setIsDraft(true);
    try {
      await updateArchitectureStandards(standards, overrides, selectedTemplate);
      // Show success notification (fix for issue #639)
      toast({
        title: "Draft Saved",
        description: "Architecture standards have been saved successfully.",
        variant: "default"
      });
    } catch (error) {
      console.error('Failed to save draft:', error);
      // Show error notification (fix for issue #639)
      toast({
        title: "Save Failed",
        description: error instanceof Error ? error.message : "Failed to save draft. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsDraft(false);
    }
  };

  const handleSubmit = async (): void => {
    console.log('[ArchitecturePage] handleSubmit called', {
      flowId,
      hasStandards: standards.length,
      hasOverrides: Object.keys(overrides).length,
      isSubmitting,
      isLoading: state.isLoading,
      currentPhase: state.currentPhase,
    });

    setIsSubmitting(true);
    try {
      console.log('[ArchitecturePage] Updating architecture standards...');
      await updateArchitectureStandards(standards, overrides, selectedTemplate);

      // BUG FIX (#1034): Check if initialization phase needs to be completed first
      // Backend requires phases in order: initialization → readiness_assessment → complexity_analysis → ...
      // If current phase is null or 'initialization', complete initialization first
      const currentPhase = state.currentPhase;
      const needsInitialization = !currentPhase || currentPhase === 'initialization';

      console.log('[ArchitecturePage] Phase check:', {
        currentPhase,
        needsInitialization,
      });

      // Execute initialization phase first if needed
      if (needsInitialization) {
        console.log('[ArchitecturePage] Executing initialization phase...');
        try {
          await resumeFlow({
            phase: 'initialization',
            action: 'continue',
            standards,
            overrides
          });
          console.log('[ArchitecturePage] Initialization phase completed');
        } catch (initError) {
          console.warn('[ArchitecturePage] Initialization phase failed, continuing anyway:', initError);
          // Continue to readiness_assessment even if initialization fails
          // as it may be optional/implicit in some cases
        }
      }

      console.log('[ArchitecturePage] Resuming flow with readiness_assessment...');
      const resumeResponse = await resumeFlow({
        phase: 'readiness_assessment',
        action: 'continue',
        standards,
        overrides
      });

      console.log('[ArchitecturePage] Flow resumed successfully', {
        newPhase: resumeResponse.current_phase,
        progress: resumeResponse.progress,
      });

      // ADR-027: Map canonical phase name to frontend route
      // Each phase now has its own dedicated page
      const phaseToRouteMap: Record<string, string> = {
        'initialization': 'architecture',         // Initial phase redirects to architecture
        'readiness_assessment': 'architecture',
        'complexity_analysis': 'complexity',      // New page: complexity analysis metrics
        'dependency_analysis': 'dependency',      // New page: dependency mapping
        'tech_debt_assessment': 'tech-debt',      // Existing page: tech debt items
        'risk_assessment': 'sixr-review',
        'recommendation_generation': 'app-on-page',
        'finalization': 'app-on-page',            // Final phase shows recommendations
      };

      // Get next phase from backend response (not state - ADR-027)
      const nextPhase = resumeResponse.current_phase;
      const routeName = phaseToRouteMap[nextPhase] || 'tech-debt'; // fallback

      console.log('[ArchitecturePage] Navigating to next phase', {
        currentPhase: nextPhase,
        routeName,
      });

      navigate(`/assessment/${flowId}/${routeName}`);
    } catch (error) {
      console.error('[ArchitecturePage] Failed to submit architecture standards:', error);
      // Show error to user
      alert(`Failed to continue: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasChanges = (): unknown => {
    return JSON.stringify(standards) !== JSON.stringify(state.engagementStandards) ||
           JSON.stringify(overrides) !== JSON.stringify(state.applicationOverrides);
  };

  const handleRefreshApplications = async (): Promise<void> => {
    setIsRefreshing(true);
    try {
      await refreshApplicationData();
    } catch (error) {
      console.error('Failed to refresh application data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleEnrichApplications = async (): Promise<void> => {
    setIsEnriching(true);
    setEnrichmentProgress(null);

    try {
      // Start enrichment
      const response = await fetch(
        `/api/v1/master-flows/${flowId}/trigger-enrichment`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Client-Account-ID': client?.id || '',
            'X-Engagement-ID': engagement?.id || '',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Enrichment failed');
      }

      console.log('[Architecture] Enrichment started successfully');

      // Poll for status updates (GPT-5 recommendation)
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(
            `/api/v1/master-flows/${flowId}/enrichment-status`,
            {
              headers: {
                'X-Client-Account-ID': client?.id || '',
                'X-Engagement-ID': engagement?.id || '',
              },
            }
          );

          if (statusResponse.ok) {
            const status = await statusResponse.json();
            setEnrichmentProgress(status.enrichment_status);

            // Check if enrichment complete (any non-zero counts)
            const totalEnriched = Object.values(status.enrichment_status || {}).reduce(
              (sum: number, count: unknown) => sum + (typeof count === 'number' ? count : 0), 0
            );

            if (totalEnriched > 0) {
              clearInterval(pollInterval);
              clearTimeout(timeoutId); // Clear timeout to prevent memory leak (Qodo review fix)
              setIsEnriching(false);
              await refreshApplicationData();
              console.log('[Architecture] Enrichment completed:', status);
            }
          }
        } catch (pollError) {
          console.error('[Architecture] Failed to poll enrichment status:', pollError);
        }
      }, 3000); // Poll every 3 seconds

      // Timeout after 5 minutes (Qodo review fix: store timeout ID for cleanup)
      const timeoutId = setTimeout(() => {
        clearInterval(pollInterval);
        setIsEnriching(false);
      }, 300000);

    } catch (error) {
      console.error('Failed to enrich applications:', error);
      alert(`Enrichment failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsEnriching(false);
    }
  };

  return (
    <SidebarProvider>
      <AssessmentFlowLayout flowId={flowId}>
      <div className="p-6 max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">
            Architecture Standards
          </h1>
          <p className="text-gray-600">
            Define engagement-level architecture minimums and application-specific exceptions
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
            <p className="text-sm text-blue-600">
              AI agents are analyzing your architecture standards...
            </p>
          </div>
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

        {/* Template Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Template Selection</CardTitle>
            <CardDescription>
              Start with a pre-defined template or create custom standards
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TemplateSelector
              selectedTemplate={selectedTemplate}
              onTemplateSelect={(template) => {
                setStandards(template.standards);
                setSelectedTemplate(template.id);
              }}
            />
          </CardContent>
        </Card>

        {/* Architecture Standards Form */}
        <Card>
          <CardHeader>
            <CardTitle>Engagement-Level Standards</CardTitle>
            <CardDescription>
              Define the minimum architecture requirements for all applications
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ArchitectureStandardsForm
              standards={standards}
              onChange={setStandards}
            />
          </CardContent>
        </Card>

        {/* Selected Applications */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Selected Applications
                  <Badge variant="secondary">
                    {state.applicationCount || state.selectedApplications.length}
                  </Badge>
                </CardTitle>
              </div>
              <div className="flex items-center gap-2">
                {unmappedAssets.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowBulkMapping(true)}
                    className="text-xs"
                  >
                    <Link className="h-3 w-3 mr-1" />
                    Map {unmappedAssets.length} Unmapped Asset{unmappedAssets.length !== 1 ? 's' : ''}
                  </Button>
                )}
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleEnrichApplications}
                  disabled={isEnriching || state.isLoading}
                  className="text-xs"
                >
                  {isEnriching ? (
                    <>
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Enriching...
                    </>
                  ) : (
                    <>
                      <Zap className="h-3 w-3 mr-1" />
                      Enrich Applications
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefreshApplications}
                  disabled={isRefreshing}
                  className="text-xs"
                >
                  <RefreshCw className={`h-3 w-3 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </div>
            <CardDescription>
              Applications included in this assessment flow
              {isEnriching && enrichmentProgress && (
                <span className="ml-2 text-xs text-muted-foreground">
                  • Enriched: {Object.entries(enrichmentProgress).map(([key, count]) =>
                    `${key}: ${count}`
                  ).join(', ')}
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {state.selectedApplications.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {state.selectedApplications.map((app: AssessmentApplication) => (
                  <div key={app.application_id} className="border rounded-lg p-4 space-y-3">
                    <div className="space-y-1">
                      <h4 className="font-semibold text-sm">{app.application_name}</h4>
                      <p className="text-xs text-muted-foreground">{app.application_type}</p>
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <Badge variant="outline" className="text-xs">
                        {app.environment}
                      </Badge>
                      <Badge
                        variant={app.business_criticality === 'critical' ? 'destructive' :
                                app.business_criticality === 'high' ? 'secondary' : 'outline'}
                        className="text-xs"
                      >
                        {app.business_criticality}
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        <span>Complexity: {app.complexity_score}/10</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Zap className="h-3 w-3" />
                        <span>Readiness: {app.readiness_score}/10</span>
                      </div>
                    </div>

                    {app.technology_stack && app.technology_stack.length > 0 && (
                      <div className="space-y-1">
                        <p className="text-xs font-medium">Tech Stack:</p>
                        <div className="flex flex-wrap gap-1">
                          {app.technology_stack.slice(0, 3).map((tech, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {tech}
                            </Badge>
                          ))}
                          {app.technology_stack.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{app.technology_stack.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {app.discovery_completed_at && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        <span>Discovery: {new Date(app.discovery_completed_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-sm">No applications loaded yet.</p>
                <p className="text-xs mt-1">Application data will be loaded when the flow initializes.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Application Overrides */}
        <Card>
          <CardHeader>
            <CardTitle>Application-Specific Overrides</CardTitle>
            <CardDescription>
              Define exceptions for specific applications that cannot meet the engagement standards
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ApplicationOverrides
              applications={state.selectedApplicationIds}
              overrides={overrides}
              onChange={setOverrides}
            />
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            {hasChanges() && (
              <Button
                variant="outline"
                onClick={handleSaveDraft}
                disabled={isDraft}
              >
                <Save className="h-4 w-4 mr-2" />
                {isDraft ? 'Saving...' : 'Save Draft'}
              </Button>
            )}
          </div>

          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || state.isLoading}
            size="lg"
          >
            {isSubmitting ? (
              'Processing...'
            ) : (
              <>
                Continue to Next Phase
                <ArrowRight className="h-4 w-4 ml-2" />
              </>
            )}
          </Button>
        </div>

        {/* Bulk Asset Mapping Dialog */}
        {showBulkMapping && (
          <BulkAssetMappingDialog
            unmappedAssets={unmappedAssets}
            onComplete={() => {
              setShowBulkMapping(false);
              refreshApplicationData();
            }}
            onCancel={() => setShowBulkMapping(false)}
          />
        )}
      </div>
      </AssessmentFlowLayout>
    </SidebarProvider>
  );
};


export default ArchitecturePage;
