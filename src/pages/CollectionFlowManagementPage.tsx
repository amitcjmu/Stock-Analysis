import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Database, Settings, Clock, Zap, Play } from 'lucide-react'
import { CheckCircle, XCircle, AlertTriangle, RefreshCw, Trash2, Shield, Activity, HardDrive, BarChart3, Users } from 'lucide-react'
import { useToast } from '@/hooks/use-toast';
import { useCollectionFlowManagement } from '@/hooks/collection/useCollectionFlowManagement';
import { IncompleteCollectionFlowManager } from '@/components/collection/IncompleteCollectionFlowManager';
import { collectionFlowApi } from '@/services/api/collection-flow';
import { getErrorToastOptions } from '@/utils/errorHandling';
import { FLOW_PHASE_ROUTES } from '@/config/flowRoutes';

interface CollectionFlowManagementPageProps {
  showHealthMonitor?: boolean;
  showCleanupTools?: boolean;
  autoRefresh?: boolean;
}

const CollectionFlowManagementPage: React.FC<CollectionFlowManagementPageProps> = ({
  showHealthMonitor = true,
  showCleanupTools = true,
  autoRefresh = true
}) => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const [cleanupOptions, setCleanupOptions] = useState({
    expirationHours: 72,
    dryRun: true,
    includeFailedFlows: true,
    includeCancelledFlows: true
  });

  const [healthStatus, setHealthStatus] = useState<{
    healthy_flows: number;
    problematic_flows: number;
    total_flows: number;
    health_score: number;
  } | null>(null);
  const [cleanupRecommendations, setCleanupRecommendations] = useState<{
    total_flows: number;
    cleanup_candidates: number;
    estimated_space_recovery: string;
    recommendations: string[];
  } | null>(null);
  const [cleanupResult, setCleanupResult] = useState<{
    flows_cleaned: number;
    space_recovered?: string;
    dry_run: boolean;
    error?: string;
  } | null>(null);

  const {
    useIncompleteFlows,
    continueFlow,
    deleteFlow,
    batchDeleteFlows,
    cleanupFlows,
    isContinuing,
    isDeleting,
    isBatchDeleting,
    isCleaning,
    isOperationPending
  } = useCollectionFlowManagement();

  // Queries
  const incompleteFlowsQuery = useIncompleteFlows();

  // Load health status and recommendations on mount
  useEffect(() => {
    const loadHealthData = async (): Promise<void> => {
      try {
        const [health, recommendations] = await Promise.all([
          collectionFlowApi.getFlowHealthStatus(),
          collectionFlowApi.getCleanupRecommendations()
        ]);
        setHealthStatus(health);
        setCleanupRecommendations(recommendations);
      } catch (error: any) {
        console.error('Failed to load health data:', error);
        // Use centralized error handling for consistent messaging
        toast(getErrorToastOptions(error));
      }
    };

    loadHealthData();
  }, [toast]);

  // Auto refresh health status
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        const health = await collectionFlowApi.getFlowHealthStatus();
        setHealthStatus(health);
      } catch (error: any) {
        // Only show error on first failure to avoid spam
        console.error('Failed to refresh health status:', error);
        if (healthStatus !== null) {
          // Only show toast if we had health data before
          const errorOptions = getErrorToastOptions(error);
          toast({
            ...errorOptions,
            title: "Health Status Update Failed",
            description: "Unable to refresh health information. Data may be outdated.",
          });
        }
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, healthStatus, toast]);

  // Handlers
  const handleContinueFlow = async (flowId: string): void => {
    try {
      const result = await continueFlow(flowId);
      // Refetch incomplete flows to get updated flow state
      await incompleteFlowsQuery.refetch();

      // Get the updated flow details to determine the current phase
      const updatedFlows = await collectionFlowApi.getIncompleteFlows();
      const updatedFlow = updatedFlows.find(f => f.id === flowId);

      if (updatedFlow && updatedFlow.current_phase) {
        // Navigate to the appropriate phase page
        const phaseRoute = FLOW_PHASE_ROUTES.collection[updatedFlow.current_phase];
        if (phaseRoute) {
          const route = phaseRoute(flowId);
          navigate(route);
          toast({
            title: "Flow Resumed",
            description: `Navigating to ${updatedFlow.current_phase.replace('_', ' ')} phase...`,
            variant: "default"
          });
          return;
        }
      }

      // Fallback toast if navigation fails
      toast({
        title: "Flow Resumed",
        description: "The collection flow has been successfully resumed.",
        variant: "default"
      });
    } catch (error: any) {
      console.error('Failed to continue flow:', error);
      const errorOptions = getErrorToastOptions(error);
      toast({
        ...errorOptions,
        title: "Failed to Resume Flow",
      });
    }
  };

  const handleDeleteFlow = async (flowId: string): void => {
    try {
      await deleteFlow(flowId, false);
      await incompleteFlowsQuery.refetch();
      toast({
        title: "Flow Deleted",
        description: "The collection flow has been successfully deleted.",
        variant: "default"
      });
    } catch (error: any) {
      console.error('Failed to delete flow:', error);
      const errorOptions = getErrorToastOptions(error);
      toast({
        ...errorOptions,
        title: "Failed to Delete Flow",
      });
    }
  };

  const handleBatchDelete = async (flowIds: string[]): void => {
    try {
      await batchDeleteFlows(flowIds, false);
      await incompleteFlowsQuery.refetch();
      toast({
        title: "Flows Deleted",
        description: `Successfully deleted ${flowIds.length} collection flows.`,
        variant: "default"
      });
    } catch (error: any) {
      console.error('Failed to batch delete flows:', error);
      const errorOptions = getErrorToastOptions(error);
      toast({
        ...errorOptions,
        title: "Failed to Delete Flows",
      });
    }
  };

  const handleCleanupFlows = async (): void => {
    try {
      const result = await cleanupFlows(cleanupOptions);
      setCleanupResult(result);

      const actionType = cleanupOptions.dryRun ? "Preview" : "Cleanup";
      toast({
        title: `${actionType} Completed`,
        description: cleanupOptions.dryRun
          ? `Preview shows ${result.flows_cleaned} flows would be cleaned up.`
          : `Successfully cleaned up ${result.flows_cleaned} flows.`,
        variant: "default"
      });

      if (!cleanupOptions.dryRun) {
        // Refresh all data after actual cleanup
        try {
          await Promise.all([
            incompleteFlowsQuery.refetch(),
            collectionFlowApi.getFlowHealthStatus().then(setHealthStatus),
            collectionFlowApi.getCleanupRecommendations().then(setCleanupRecommendations)
          ]);
        } catch (refreshError: any) {
          console.error('Failed to refresh data after cleanup:', refreshError);
          const errorOptions = getErrorToastOptions(refreshError);
          toast({
            ...errorOptions,
            title: "Data Refresh Failed",
            description: "Cleanup completed but failed to refresh data. Please refresh the page.",
          });
        }
      }
    } catch (error: any) {
      console.error('Failed to cleanup flows:', error);
      const errorOptions = getErrorToastOptions(error);
      toast({
        ...errorOptions,
        title: "Cleanup Failed",
      });
    }
  };

  const handleViewDetails = (flowId: string, phase: string): void => {
    // Navigate to flow details page using the flow progress route
    console.log('Navigating to flow details:', flowId, 'phase:', phase);
    navigate(`/collection/flow/${flowId}`);
    toast({
      title: "Navigation",
      description: `Opening flow details for ${flowId}`,
      variant: "default"
    });
  };

  // Render status badge
  const renderStatusBadge = (status: string, healthy?: boolean): JSX.Element => {
    if (healthy === true) {
      return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1" />Healthy</Badge>;
    } else if (healthy === false) {
      return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Issues</Badge>;
    } else {
      return <Badge variant="secondary"><AlertTriangle className="w-3 h-3 mr-1" />Unknown</Badge>;
    }
  };

  const incompleteFlows = incompleteFlowsQuery.data || [];

  return (
    <div className="space-y-6 p-4 lg:p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Collection Flow Management</h1>
          <p className="text-gray-600 mt-1">
            Manage collection flows with comprehensive lifecycle control
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {healthStatus && healthStatus.health_score >= 80 && (
            <Badge variant="default" className="bg-green-100 text-green-800">
              <Activity className="w-3 h-3 mr-1" />System Healthy ({healthStatus.health_score}%)
            </Badge>
          )}
          {isOperationPending && (
            <Badge variant="secondary">
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />Processing
            </Badge>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      {healthStatus && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{healthStatus.total_flows}</p>
                  <p className="text-sm text-gray-600">Total Flows</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{healthStatus.healthy_flows}</p>
                  <p className="text-sm text-gray-600">Healthy</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <AlertTriangle className="h-8 w-8 text-red-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{healthStatus.problematic_flows}</p>
                  <p className="text-sm text-gray-600">Issues</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Activity className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-2xl font-bold">{healthStatus.health_score}%</p>
                  <p className="text-sm text-gray-600">Health Score</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Dashboard */}
      <Tabs defaultValue="flows" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="flows">Active Flows</TabsTrigger>
          <TabsTrigger value="cleanup">Cleanup Tools</TabsTrigger>
          <TabsTrigger value="monitoring">Health Monitor</TabsTrigger>
        </TabsList>

        {/* Active Flows Tab */}
        <TabsContent value="flows" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="w-5 h-5 mr-2" />
                Incomplete Collection Flows
              </CardTitle>
              <CardDescription>
                Manage and continue incomplete collection flows
              </CardDescription>
            </CardHeader>
            <CardContent>
              {incompleteFlowsQuery.isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin mr-2" />
                  <span>Loading collection flows...</span>
                </div>
              ) : incompleteFlowsQuery.error ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center max-w-md">
                    <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to Load Collection Flows</h3>
                    <p className="text-gray-600 mb-4">
                      {incompleteFlowsQuery.error?.message || 'Unable to load collection flow data.'}
                    </p>
                    <Button
                      onClick={() => incompleteFlowsQuery.refetch()}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Try Again
                    </Button>
                  </div>
                </div>
              ) : (
                <IncompleteCollectionFlowManager
                  flows={incompleteFlows}
                  onContinueFlow={handleContinueFlow}
                  onDeleteFlow={handleDeleteFlow}
                  onBatchDelete={handleBatchDelete}
                  onViewDetails={handleViewDetails}
                  isLoading={isOperationPending}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cleanup Tools Tab */}
        <TabsContent value="cleanup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Trash2 className="w-5 h-5 mr-2" />
                Collection Flow Cleanup Tools
              </CardTitle>
              <CardDescription>
                Clean up expired flows and manage storage space
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Expiration Hours</label>
                  <input
                    type="number"
                    value={cleanupOptions.expirationHours}
                    onChange={(e) => setCleanupOptions(prev => ({ ...prev, expirationHours: parseInt(e.target.value) }))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="dryRun"
                      checked={cleanupOptions.dryRun}
                      onChange={(e) => setCleanupOptions(prev => ({ ...prev, dryRun: e.target.checked }))}
                    />
                    <label htmlFor="dryRun" className="text-sm font-medium">Dry Run (Preview Only)</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="includeFailedFlows"
                      checked={cleanupOptions.includeFailedFlows}
                      onChange={(e) => setCleanupOptions(prev => ({ ...prev, includeFailedFlows: e.target.checked }))}
                    />
                    <label htmlFor="includeFailedFlows" className="text-sm font-medium">Include Failed Flows</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="includeCancelledFlows"
                      checked={cleanupOptions.includeCancelledFlows}
                      onChange={(e) => setCleanupOptions(prev => ({ ...prev, includeCancelledFlows: e.target.checked }))}
                    />
                    <label htmlFor="includeCancelledFlows" className="text-sm font-medium">Include Cancelled Flows</label>
                  </div>
                </div>
              </div>

              <Button
                onClick={handleCleanupFlows}
                disabled={isCleaning}
                variant={cleanupOptions.dryRun ? "outline" : "destructive"}
              >
                {isCleaning ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
                {cleanupOptions.dryRun ? "Preview Cleanup" : "Perform Cleanup"}
              </Button>

              {/* Cleanup Recommendations */}
              {cleanupRecommendations && cleanupRecommendations.recommendations.length > 0 && (
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertTitle>Cleanup Recommendations</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      {cleanupRecommendations.recommendations.map((rec: string, idx: number) => (
                        <li key={idx} className="text-sm">{rec}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {/* Cleanup Results */}
              {cleanupResult && (
                <Alert>
                  <HardDrive className="h-4 w-4" />
                  <AlertTitle>Cleanup Results</AlertTitle>
                  <AlertDescription>
                    <div className="space-y-1">
                      <p>Flows processed: {cleanupResult.flows_cleaned}</p>
                      <p>Space recovered: {cleanupResult.space_recovered}</p>
                      <p>Mode: {cleanupResult.dry_run ? "Preview" : "Actual cleanup"}</p>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Health Monitor Tab */}
        <TabsContent value="monitoring" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                Collection Flow Health Monitor
              </CardTitle>
              <CardDescription>
                Monitor health across collection flows and system components
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Health Overview */}
              {healthStatus && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Overall Health Score</span>
                    <Badge variant={healthStatus.health_score >= 80 ? "default" : "destructive"}>
                      {healthStatus.health_score}%
                    </Badge>
                  </div>
                  <Progress value={healthStatus.health_score} className="w-full" />

                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-green-600">{healthStatus.healthy_flows}</p>
                      <p className="text-sm text-muted-foreground">Healthy</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-red-600">{healthStatus.problematic_flows}</p>
                      <p className="text-sm text-muted-foreground">Issues</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{healthStatus.total_flows}</p>
                      <p className="text-sm text-muted-foreground">Total</p>
                    </div>
                  </div>
                </div>
              )}

              <Separator />

              {/* System Status */}
              <div>
                <h4 className="font-medium mb-3">System Components</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Collection Flow API</span>
                    {renderStatusBadge('api', !incompleteFlowsQuery.isError)}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Database Persistence</span>
                    {renderStatusBadge('database', true)}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">CrewAI Integration</span>
                    {renderStatusBadge('crewai', true)}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CollectionFlowManagementPage;
