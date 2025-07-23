/**
 * Enhanced Flow Management Dashboard
 * Comprehensive dashboard for managing flows with hybrid CrewAI + PostgreSQL persistence.
 * Provides validation, recovery, cleanup, and monitoring capabilities.
 */

import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import type { Separator } from '@/components/ui/separator';
import type { Settings, Clock } from 'lucide-react'
import { CheckCircle, XCircle, AlertTriangle, RefreshCw, Database, Trash2, Shield, Activity, HardDrive, Zap } from 'lucide-react'
import { useToast } from '@/hooks/use-toast';
import { useEnhancedFlowManagement, useFlowHealthMonitor } from '@/hooks/discovery/useEnhancedFlowManagement';

interface EnhancedFlowManagementDashboardProps {
  flowId?: string;
  flowIds?: string[];
  showHealthMonitor?: boolean;
  showCleanupTools?: boolean;
  autoRefresh?: boolean;
}

export const EnhancedFlowManagementDashboard: React.FC<EnhancedFlowManagementDashboardProps> = ({
  flowId,
  flowIds = [],
  showHealthMonitor = true,
  showCleanupTools = true,
  autoRefresh = true
}) => {
  const { toast } = useToast();
  const [selectedFlowId, setSelectedFlowId] = useState(flowId || '');
  const [cleanupOptions, setCleanupOptions] = useState({
    expirationHours: 72,
    dryRun: true
  });

  const {
    validateFlowWithRecommendations,
    performFlowRecovery,
    performFlowCleanup,
    performBulkValidation,
    usePersistenceStatus,
    usePersistenceHealth,
    isValidating,
    isRecovering,
    isCleaning,
    isBulkValidating,
    isAnyOperationPending
  } = useEnhancedFlowManagement();

  // Queries
  const persistenceStatusQuery = usePersistenceStatus(selectedFlowId, !!selectedFlowId);
  const persistenceHealthQuery = usePersistenceHealth();
  const flowHealthMonitor = useFlowHealthMonitor(flowIds, showHealthMonitor && flowIds.length > 0);

  // State for validation results
  const [validationResult, setValidationResult] = useState<{
    status: string;
    flow_id: string;
    overall_valid: boolean;
    crewai_validation: Record<string, unknown>;
    postgresql_validation: Record<string, unknown>;
    phase_executors?: Record<string, unknown>;
    validation_timestamp: string;
    recommendations?: string[];
    warningCount?: number;
    criticalIssues?: boolean;
  } | null>(null);
  const [recoveryResult, setRecoveryResult] = useState<{
    status: string;
    flow_id: string;
    recovery_successful: boolean;
    recovered_state?: Record<string, unknown>;
    recovery_strategy_used: string;
    recovery_timestamp: string;
    next_steps?: string[];
  } | null>(null);
  const [cleanupResult, setCleanupResult] = useState<{
    status: string;
    flows_cleaned: number;
    flow_ids_cleaned: string[];
    dry_run: boolean;
    cleanup_timestamp: string;
    space_recovered?: string;
  } | null>(null);

  // Handlers
  const handleValidateFlow = async () => {
    if (!selectedFlowId) {
      toast({
        title: "Flow Required",
        description: "Please enter a flow ID to validate",
        variant: "destructive"
      });
      return;
    }

    try {
      const result = await validateFlowWithRecommendations(selectedFlowId);
      setValidationResult(result);
      
      toast({
        title: result.overall_valid ? "Validation Successful" : "Validation Issues Found",
        description: result.overall_valid 
          ? "Flow state is healthy across all persistence layers" 
          : `Found ${result.warningCount} warnings and ${result.criticalIssues ? 'critical' : 'minor'} issues`,
        variant: result.overall_valid ? "default" : "destructive"
      });
    } catch (error) {
      toast({
        title: "Validation Failed",
        description: "Failed to validate flow state",
        variant: "destructive"
      });
    }
  };

  const handleRecoverFlow = async (strategy: 'postgresql' | 'hybrid' = 'postgresql') => {
    if (!selectedFlowId) {
      toast({
        title: "Flow Required",
        description: "Please enter a flow ID to recover",
        variant: "destructive"
      });
      return;
    }

    try {
      const result = await performFlowRecovery(selectedFlowId, strategy);
      setRecoveryResult(result);
      
      toast({
        title: result.recovery_successful ? "Recovery Successful" : "Recovery Failed",
        description: result.recovery_successful 
          ? "Flow state recovered successfully from PostgreSQL" 
          : "No recoverable state found for this session",
        variant: result.recovery_successful ? "default" : "destructive"
      });
    } catch (error) {
      toast({
        title: "Recovery Failed",
        description: "Failed to recover flow state",
        variant: "destructive"
      });
    }
  };

  const handleCleanupFlows = async () => {
    try {
      const result = await performFlowCleanup(cleanupOptions);
      setCleanupResult(result);
      
      toast({
        title: cleanupOptions.dryRun ? "Cleanup Preview" : "Cleanup Completed",
        description: cleanupOptions.dryRun 
          ? `Would clean ${result.flows_cleaned} expired flows` 
          : `Cleaned ${result.flows_cleaned} expired flows, recovered ${result.spaceRecovered}`,
        variant: "default"
      });
    } catch (error) {
      toast({
        title: "Cleanup Failed",
        description: "Failed to perform flow cleanup",
        variant: "destructive"
      });
    }
  };

  const handleBulkValidation = async () => {
    if (flowIds.length === 0) {
      toast({
        title: "No Flows",
        description: "No flow IDs available for bulk validation",
        variant: "destructive"
      });
      return;
    }

    try {
      const result = await performBulkValidation(flowIds);
      
      toast({
        title: "Bulk Validation Complete",
        description: `${result.summary.healthy}/${result.summary.total} flows healthy (${result.summary.healthScore}% health score)`,
        variant: result.summary.healthScore >= 80 ? "default" : "destructive"
      });
    } catch (error) {
      toast({
        title: "Bulk Validation Failed",
        description: "Failed to perform bulk validation",
        variant: "destructive"
      });
    }
  };

  // Render status badge
  const renderStatusBadge = (status: string, valid?: boolean) => {
    if (valid === true) {
      return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1" />Healthy</Badge>;
    } else if (valid === false) {
      return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Issues</Badge>;
    } else {
      return <Badge variant="secondary"><AlertTriangle className="w-3 h-3 mr-1" />Unknown</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Enhanced Flow Management</h2>
          <p className="text-muted-foreground">
            Manage flows with hybrid CrewAI + PostgreSQL persistence
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {persistenceHealthQuery.data?.status === 'healthy' && (
            <Badge variant="default" className="bg-green-100 text-green-800">
              <Activity className="w-3 h-3 mr-1" />System Healthy
            </Badge>
          )}
          {isAnyOperationPending && (
            <Badge variant="secondary">
              <RefreshCw className="w-3 h-3 mr-1 animate-spin" />Processing
            </Badge>
          )}
        </div>
      </div>

      {/* Main Dashboard */}
      <Tabs defaultValue="validation" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="validation">Flow Validation</TabsTrigger>
          <TabsTrigger value="recovery">State Recovery</TabsTrigger>
          <TabsTrigger value="cleanup">Cleanup Tools</TabsTrigger>
          <TabsTrigger value="monitoring">Health Monitor</TabsTrigger>
        </TabsList>

        {/* Flow Validation Tab */}
        <TabsContent value="validation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                Flow State Validation
              </CardTitle>
              <CardDescription>
                Validate flow integrity across CrewAI and PostgreSQL persistence layers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Enter flow ID"
                  value={selectedFlowId}
                  onChange={(e) => setSelectedFlowId(e.target.value)}
                  className="flex-1 px-3 py-2 border rounded-md"
                />
                <Button 
                  onClick={handleValidateFlow}
                  disabled={isValidating || !selectedFlowId}
                >
                  {isValidating ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                  Validate
                </Button>
              </div>

              {/* Persistence Status */}
              {persistenceStatusQuery.data && (
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">CrewAI</span>
                        {renderStatusBadge('crewai', persistenceStatusQuery.data.crewai_persistence.available)}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">PostgreSQL</span>
                        {renderStatusBadge('postgresql', persistenceStatusQuery.data.postgresql_persistence.valid)}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Bridge</span>
                        {renderStatusBadge('bridge', persistenceStatusQuery.data.bridge_status.operational)}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Validation Results */}
              {validationResult && (
                <Alert className={validationResult.overall_valid ? "border-green-200" : "border-red-200"}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Validation Results</AlertTitle>
                  <AlertDescription className="space-y-2">
                    <p>
                      Status: {validationResult.overall_valid ? "✅ Healthy" : "⚠️ Issues Found"}
                    </p>
                    {validationResult.actionableRecommendations?.length > 0 && (
                      <div>
                        <p className="font-medium">Recommendations:</p>
                        <ul className="list-disc list-inside text-sm">
                          {validationResult.actionableRecommendations.map((rec: string, idx: number) => (
                            <li key={idx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* State Recovery Tab */}
        <TabsContent value="recovery" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="w-5 h-5 mr-2" />
                Flow State Recovery
              </CardTitle>
              <CardDescription>
                Recover flow state from PostgreSQL when CrewAI persistence fails
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Button 
                  onClick={() => handleRecoverFlow('postgresql')}
                  disabled={isRecovering || !selectedFlowId}
                  variant="outline"
                >
                  {isRecovering ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Database className="w-4 h-4 mr-2" />}
                  PostgreSQL Recovery
                </Button>
                <Button 
                  onClick={() => handleRecoverFlow('hybrid')}
                  disabled={isRecovering || !selectedFlowId}
                  variant="outline"
                >
                  <Zap className="w-4 h-4 mr-2" />
                  Hybrid Recovery
                </Button>
              </div>

              {/* Recovery Results */}
              {recoveryResult && (
                <Alert className={recoveryResult.recovery_successful ? "border-green-200" : "border-yellow-200"}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Recovery Results</AlertTitle>
                  <AlertDescription className="space-y-2">
                    <p>
                      Status: {recoveryResult.recovery_successful ? "✅ Recovered" : "⚠️ No Data"}
                    </p>
                    <p>Strategy: {recoveryResult.recovery_strategy_used}</p>
                    {recoveryResult.next_steps?.length > 0 && (
                      <div>
                        <p className="font-medium">Next Steps:</p>
                        <ul className="list-disc list-inside text-sm">
                          {recoveryResult.next_steps.map((step: string, idx: number) => (
                            <li key={idx}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
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
                Flow Cleanup Tools
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
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="dryRun"
                    checked={cleanupOptions.dryRun}
                    onChange={(e) => setCleanupOptions(prev => ({ ...prev, dryRun: e.target.checked }))}
                  />
                  <label htmlFor="dryRun" className="text-sm font-medium">Dry Run (Preview Only)</label>
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

              {/* Cleanup Results */}
              {cleanupResult && (
                <Alert>
                  <HardDrive className="h-4 w-4" />
                  <AlertTitle>Cleanup Results</AlertTitle>
                  <AlertDescription>
                    <p>Flows processed: {cleanupResult.flows_cleaned}</p>
                    <p>Space recovered: {cleanupResult.space_recovered}</p>
                    <p>Mode: {cleanupResult.dry_run ? "Preview" : "Actual cleanup"}</p>
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
                Flow Health Monitor
              </CardTitle>
              <CardDescription>
                Monitor health across multiple flows and system components
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Bulk Validation */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Bulk Flow Validation ({flowIds.length} flows)</span>
                <Button 
                  onClick={handleBulkValidation}
                  disabled={isBulkValidating || flowIds.length === 0}
                  size="sm"
                >
                  {isBulkValidating ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                  Validate All
                </Button>
              </div>

              {/* Health Monitor Results */}
              {flowHealthMonitor.data && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Overall Health Score</span>
                    <Badge variant={flowHealthMonitor.data.summary.healthScore >= 80 ? "default" : "destructive"}>
                      {flowHealthMonitor.data.summary.healthScore}%
                    </Badge>
                  </div>
                  <Progress value={flowHealthMonitor.data.summary.healthScore} className="w-full" />
                  
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-green-600">{flowHealthMonitor.data.summary.healthy}</p>
                      <p className="text-sm text-muted-foreground">Healthy</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-red-600">{flowHealthMonitor.data.summary.problematic}</p>
                      <p className="text-sm text-muted-foreground">Issues</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{flowHealthMonitor.data.summary.total}</p>
                      <p className="text-sm text-muted-foreground">Total</p>
                    </div>
                  </div>
                </div>
              )}

              {/* System Health */}
              {persistenceHealthQuery.data && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-2">System Health</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">PostgreSQL Persistence</span>
                      {renderStatusBadge('postgresql', persistenceHealthQuery.data.postgresql_persistence === 'operational')}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Flow State Bridge</span>
                      {renderStatusBadge('bridge', persistenceHealthQuery.data.flow_state_bridge === 'operational')}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">CrewAI Integration</span>
                      {renderStatusBadge('crewai', persistenceHealthQuery.data.crewai_integration === 'assumed_healthy')}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}; 