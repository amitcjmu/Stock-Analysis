import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Filter } from 'lucide-react'
import { Plus, Search, MoreHorizontal, Play, Pause, CheckCircle2, AlertCircle, Clock, Users, Loader2 } from 'lucide-react'

import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import { useAuth } from '@/contexts/AuthContext';
import { apiCall } from '../../config/api';
import { Button } from '@/components/ui/button';
import { CardDescription } from '@/components/ui/card'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';
import { collectionFlowApi } from '@/services/api/collection-flow';

interface AssessmentFlow {
  id: string;
  status: 'initialized' | 'processing' | 'paused_for_user_input' | 'completed' | 'error';
  current_phase: string;
  progress: number;
  selected_applications: number;
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface AssessmentFlowMetrics {
  total_flows: number;
  active_flows: number;
  completed_flows: number;
  total_applications_assessed: number;
}

const READINESS_THRESHOLD = 0.7;

const AssessmentFlowOverview = (): JSX.Element => {
  const navigate = useNavigate();
  const { getAuthHeaders } = useAuth();
  const { toast } = useToast();

  const [collectionFlowId, setCollectionFlowId] = useState<string | null>(null);
  const [isEnsuringFlow, setIsEnsuringFlow] = useState<boolean>(true);
  const [isInitializingAssessment, setIsInitializingAssessment] = useState<boolean>(false);
  const [readiness, setReadiness] = useState<{
    apps_ready_for_assessment: number;
    phase_scores: { collection: number; discovery: number };
  } | null>(null);
  const readinessPasses = useMemo(() => {
    if (!readiness) return false;
    const c = readiness.phase_scores?.collection ?? 0;
    const d = readiness.phase_scores?.discovery ?? 0;
    return c >= READINESS_THRESHOLD && d >= READINESS_THRESHOLD && (readiness.apps_ready_for_assessment || 0) > 0;
  }, [readiness]);

  // Ensure-or-create a Collection flow on mount
  useEffect(() => {
    (async () => {
      try {
        const ensured = await collectionFlowApi.ensureFlow();
        if (ensured?.id) {
          setCollectionFlowId(ensured.id);
        }
      } catch (e) {
        // Non-fatal; user can still navigate manually
        console.warn('Failed to ensure collection flow', e);
      } finally {
        setIsEnsuringFlow(false);
      }
    })();
  }, []);

  // Fetch readiness for the ensured collection flow
  useEffect(() => {
    if (!collectionFlowId) return;
    (async () => {
      try {
        const r = await collectionFlowApi.getFlowReadiness(collectionFlowId);
        setReadiness({
          apps_ready_for_assessment: r.apps_ready_for_assessment || 0,
          phase_scores: r.phase_scores || { collection: 0, discovery: 0 },
        });
      } catch (e) {
        setReadiness(null);
      }
    })();
  }, [collectionFlowId]);

  // DISABLED: Legacy asset-workflow endpoint lacks multi-tenant scoping and returns 404
  // TODO: Add proper backend endpoint to get assessment-ready application IDs from collection flow
  // For now, application selection will be handled via collection flow configuration
  const { data: assessmentReadyAssets = [] } = useQuery<string[]>({
    queryKey: ['assets-assessment-ready', collectionFlowId],
    enabled: false, // Disabled - legacy endpoint returns 404
    staleTime: 30000,
    gcTime: 60000,
    refetchOnWindowFocus: false,
    queryFn: async () => {
      // Legacy endpoint: /asset-workflow/workflow/by-phase/assessment_ready
      // Returns 404 - endpoint lacks multi-tenant scoping (no client_account_id/engagement_id)
      // Application IDs should come from collection flow configuration instead
      return [];
    }
  });

  // Use useMemo to prevent infinite loops from array reference changes
  const readyAppIds = useMemo(() => {
    return assessmentReadyAssets.map((id: string) => id);
  }, [assessmentReadyAssets]);

  // Metrics placeholder (no mocks). Keep minimal non-blocking UI.
  const { data: metrics, isLoading: metricsLoading } = useQuery<AssessmentFlowMetrics>({
    queryKey: ['assessment-flow-metrics'],
    queryFn: async () => ({ total_flows: 0, active_flows: 0, completed_flows: 0, total_applications_assessed: 0 })
  });

  // Fetch assessment flows from MFO list endpoint
  const { data: flows = [], isLoading: flowsLoading } = useQuery<AssessmentFlow[]>({
    queryKey: ['assessment-flows'],
    queryFn: async () => {
      try {
        const headers = getAuthHeaders();
        const response = await apiCall('/master-flows/list', {
          method: 'GET',
          headers
        });

        return Array.isArray(response) ? response : [];
      } catch (error) {
        console.error('Failed to fetch assessment flows:', error);
        return [];
      }
    },
    staleTime: 30000,
    refetchInterval: 15000 // Refresh every 15 seconds
  });

  const getStatusIcon = (status: string): JSX.Element => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'paused_for_user_input':
        return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadge = (status: string): JSX.Element => {
    const variants = {
      processing: 'default',
      paused_for_user_input: 'secondary',
      completed: 'default',
      error: 'destructive',
      initialized: 'secondary'
    } as const;

    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  const handleStartAssessment = async (): Promise<void> => {
    if (isInitializingAssessment || !readyAppIds.length) return;
    setIsInitializingAssessment(true);
    try {
      const headers = getAuthHeaders();
      const result = await apiCall('/assessment-flow/initialize', {
        method: 'POST',
        headers,
        body: JSON.stringify({ selected_application_ids: readyAppIds })
      });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any -- Complex type requiring refactoring
      const flowId = result && typeof result === 'object' ? (result as any).flow_id : undefined;
      // Fire-and-forget UX metric event (basic scaffolding)
      try {
        await apiCall('/monitoring/business/ux-event', {
          method: 'POST',
          headers,
          body: JSON.stringify({ event: 'assessment_started', ready_apps: readyAppIds.length, source: 'assessment_overview', collection_flow_id: collectionFlowId })
        });
      } catch (err) {
        console.debug('UX event failed', err);
      }
      if (flowId) {
        toast({ title: 'Assessment initialized', description: `${readyAppIds.length} applications included.` });
        navigate(`/assessment/${flowId}/architecture`);
      } else {
        toast({ title: 'Initialization incomplete', description: 'No flow id was returned. Please retry shortly.', variant: 'destructive' });
      }
    } catch (e) {
      toast({ title: 'Failed to start assessment', description: 'Please try again after completing collection.', variant: 'destructive' });
    } finally {
      setIsInitializingAssessment(false);
    }
  };

  const showNotReadyBanner = !isEnsuringFlow && collectionFlowId && !readinessPasses;

  const formatPhase = (phase: string): unknown => {
    return phase.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatDate = (dateString: string): unknown => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>

          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Assessment Flows</h1>
                <p className="text-gray-600">
                  Start AI-powered assessment when data readiness is confirmed
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
              <Button
                onClick={handleStartAssessment}
                disabled={!readinessPasses || isInitializingAssessment}
                title={!readinessPasses ? 'Complete intelligent data enrichment first' : 'Start AI-powered assessment'}
              >
                <Plus className="h-4 w-4 mr-2" />
                Start AI-powered Assessment
              </Button>
            </div>
          </div>

          {showNotReadyBanner && (
            <div className="mb-6 p-4 rounded-md border bg-muted/30">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-amber-800">Intelligent gap analysis in progress</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Our AI is enriching your inventory. You can monitor progress and provide any required inputs on the Collection Progress page.
                  </p>
                </div>
                <Button
                  variant="outline"
                  onClick={() => navigate(`/collection/progress?flowId=${collectionFlowId}`)}
                >
                  View Collection Progress
                </Button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              {/* Metrics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Users className="h-6 w-6 text-blue-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Flows</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.total_flows || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <Play className="h-6 w-6 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Active</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.active_flows || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <CheckCircle2 className="h-6 w-6 text-purple-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Completed</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.completed_flows || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-orange-100 rounded-lg">
                        <Users className="h-6 w-6 text-orange-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Apps Assessed</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {metricsLoading ? '-' : metrics?.total_applications_assessed || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Search and Actions */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Assessment Flows</CardTitle>
                    <div className="flex items-center space-x-2">
                      <Input
                        placeholder="Search flows..."
                        className="w-64"
                        prefix={<Search className="h-4 w-4" />}
                      />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {flowsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                    </div>
                  ) : flows.length === 0 ? (
                    <div className="text-center py-8">
                      <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Assessment Flows</h3>
                      <p className="text-gray-600 mb-4">
                        Ensure Collection completes enrichment. When ready, click Start AI-powered Assessment.
                      </p>
                      <Button onClick={handleStartAssessment} disabled={!readinessPasses || isInitializingAssessment}>
                        <Plus className="h-4 w-4 mr-2" />
                        Start AI-powered Assessment
                      </Button>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Flow ID</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Phase</TableHead>
                          <TableHead>Progress</TableHead>
                          <TableHead>Applications</TableHead>
                          <TableHead>Created</TableHead>
                          <TableHead>Updated</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {flows.map((flow) => (
                          <TableRow key={flow.id}>
                            <TableCell className="font-medium">
                              <Link
                                to={`/assessment/${flow.id}/architecture`}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                {flow.id.substring(0, 8)}...
                              </Link>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(flow.status)}
                                {getStatusBadge(flow.status)}
                              </div>
                            </TableCell>
                            <TableCell>{formatPhase(flow.current_phase)}</TableCell>
                            <TableCell>
                              <div className="flex items-center space-x-2">
                                <div className="w-16 bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{ width: `${flow.progress}%` }}
                                  />
                                </div>
                                <span className="text-sm text-gray-600">{flow.progress}%</span>
                              </div>
                            </TableCell>
                            <TableCell>{flow.selected_applications}</TableCell>
                            <TableCell className="text-sm text-gray-600">
                              {formatDate(flow.created_at)}
                            </TableCell>
                            <TableCell className="text-sm text-gray-600">
                              {formatDate(flow.updated_at)}
                            </TableCell>
                            <TableCell>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="xl:col-span-1 space-y-6">
              {/* Agent Communication Panel */}
              <AgentClarificationPanel
                pageContext="assessment-overview"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Assessment overview question answered:', questionId, response);
                }}
              />

              {/* Agent Insights */}
              <AgentInsightsSection
                pageContext="assessment-overview"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Assessment overview insight action:', insightId, action);
                }}
              />

              {/* Agent Planning Dashboard */}
              <AgentPlanningDashboard pageContext="assessment-overview" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentFlowOverview;
