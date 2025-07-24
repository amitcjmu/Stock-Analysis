import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
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
    const loadHealthData = async () => {
      try {
        const [health, recommendations] = await Promise.all([
          collectionFlowApi.getFlowHealthStatus(),
          collectionFlowApi.getCleanupRecommendations()
        ]);
        setHealthStatus(health);
        setCleanupRecommendations(recommendations);
      } catch (error) {
        console.error('Failed to load health data:', error);
      }
    };

    loadHealthData();
  }, []);

  // Auto refresh health status
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        const health = await collectionFlowApi.getFlowHealthStatus();
        setHealthStatus(health);
      } catch (error) {
        console.error('Failed to refresh health status:', error);
      }
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Handlers
  const handleContinueFlow = async (flowId: string) => {
    try {
      await continueFlow(flowId);
      // Refetch incomplete flows
      await incompleteFlowsQuery.refetch();
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleDeleteFlow = async (flowId: string) => {
    try {
      await deleteFlow(flowId, false);
      await incompleteFlowsQuery.refetch();
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleBatchDelete = async (flowIds: string[]) => {
    try {
      await batchDeleteFlows(flowIds, false);
      await incompleteFlowsQuery.refetch();
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleCleanupFlows = async () => {
    try {
      const result = await cleanupFlows(cleanupOptions);
      setCleanupResult(result);
      
      if (!cleanupOptions.dryRun) {
        // Refresh all data after actual cleanup
        await Promise.all([
          incompleteFlowsQuery.refetch(),
          collectionFlowApi.getFlowHealthStatus().then(setHealthStatus),
          collectionFlowApi.getCleanupRecommendations().then(setCleanupRecommendations)
        ]);
      }
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleViewDetails = (flowId: string, phase: string) => {
    // Navigate to flow details page - implement based on your routing
    console.log('View details for flow:', flowId, 'phase:', phase);
    toast({
      title: "Navigation",
      description: `Would navigate to flow ${flowId} details`,
      variant: "default"
    });
  };

  // Render status badge
  const renderStatusBadge = (status: string, healthy?: boolean) => {
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
    <div className="space-y-6 p-6">
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