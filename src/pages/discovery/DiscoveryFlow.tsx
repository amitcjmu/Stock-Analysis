import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';
import { useDiscoveryFlow } from '../../hooks/discovery/useDiscoveryFlow';

// Components
import Sidebar from '../../components/Sidebar';
import { ContextBreadcrumbs } from '../../components/context/ContextBreadcrumbs';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Progress } from '../../components/ui/progress';
import { AlertTriangle, CheckCircle, Clock, Play, Pause, RefreshCw } from 'lucide-react';

// Agent monitoring components
import AgentMonitor from '../../components/AgentMonitor';
import { FlowCrewAgentMonitor } from '../../components/FlowCrewAgentMonitor';

interface DiscoveryFlowProps {
  flowId?: string;
}

const DiscoveryFlow: React.FC<DiscoveryFlowProps> = ({ flowId: propFlowId }) => {
  const navigate = useNavigate();
  const { flowId: paramFlowId } = useParams<{ flowId: string }>();
  const { user } = useAuth();
  const [isInitializing, setIsInitializing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Determine effective flow ID
  const effectiveFlowId = propFlowId || paramFlowId;

  // Use custom discovery flow hook
  const {
    flow,
    isLoading: isFlowLoading,
    error: flowError,
    initializeFlow,
    startDiscovery,
    pauseFlow,
    resumeFlow,
    refreshFlow
  } = useDiscoveryFlow(effectiveFlowId);

  // Fallback to unified discovery flow hook if custom one fails
  const {
    flowState: unifiedFlow,
    isLoading: isUnifiedLoading,
    error: unifiedError,
    executeFlowPhase,
    refreshFlow: refreshUnifiedFlow
  } = useUnifiedDiscoveryFlow(effectiveFlowId);

  // Use the flow data from whichever hook has data
  const currentFlow = flow || unifiedFlow;
  const currentIsLoading = isFlowLoading || isUnifiedLoading;
  const currentError = flowError || unifiedError;

  // Safe access to flow properties with null checks
  const flowStatus = currentFlow?.status || 'idle';
  const progressPercentage = currentFlow?.progress_percentage || 0;
  const currentPhase = currentFlow?.current_phase || '';
  const crewResults = currentFlow?.crew_results || {};

  // Handle flow initialization
  const handleInitializeFlow = async () => {
    if (!user?.client_account_id) {
      setError('User context not available');
      return;
    }

    setIsInitializing(true);
    setError(null);

    try {
      if (initializeFlow) {
        await initializeFlow();
      } else {
        // Fallback to unified flow execution
        await executeFlowPhase('initialize');
      }
      await refreshCurrentFlow();
    } catch (err) {
      console.error('Failed to initialize flow:', err);
      setError('Failed to initialize discovery flow. Please try again.');
    } finally {
      setIsInitializing(false);
    }
  };

  // Handle starting discovery
  const handleStartDiscovery = async () => {
    if (!currentFlow) {
      await handleInitializeFlow();
      return;
    }

    try {
      if (startDiscovery) {
        await startDiscovery();
      } else {
        // Fallback to unified flow execution
        await executeFlowPhase('field_mapping');
      }
      await refreshCurrentFlow();
    } catch (err) {
      console.error('Failed to start discovery:', err);
      setError('Failed to start discovery flow. Please try again.');
    }
  };

  // Handle flow operations with null checks
  const handlePauseFlow = async () => {
    if (!currentFlow || !pauseFlow) return;

    try {
      await pauseFlow();
      await refreshCurrentFlow();
    } catch (err) {
      console.error('Failed to pause flow:', err);
      setError('Failed to pause flow. Please try again.');
    }
  };

  const handleResumeFlow = async () => {
    if (!currentFlow || !resumeFlow) return;

    try {
      await resumeFlow();
      await refreshCurrentFlow();
    } catch (err) {
      console.error('Failed to resume flow:', err);
      setError('Failed to resume flow. Please try again.');
    }
  };

  // Safe refresh function
  const refreshCurrentFlow = async () => {
    try {
      if (refreshFlow) {
        await refreshFlow();
      }
      if (refreshUnifiedFlow) {
        await refreshUnifiedFlow();
      }
    } catch (err) {
      console.error('Failed to refresh flow:', err);
    }
  };

  // Get status badge variant based on flow status
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'default';
      case 'running': case 'in_progress': return 'secondary';
      case 'failed': case 'error': return 'destructive';
      case 'paused': return 'outline';
      default: return 'outline';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'running': case 'in_progress': return <Clock className="w-4 h-4" />;
      case 'failed': case 'error': return <AlertTriangle className="w-4 h-4" />;
      case 'paused': return <Pause className="w-4 h-4" />;
      default: return <Play className="w-4 h-4" />;
    }
  };

  // Crew sequence rendering
  const renderCrewSequence = () => {
    const crews = [
      { name: 'Field Mapping', key: 'field_mapping' },
      { name: 'Data Cleansing', key: 'data_cleansing' },
      { name: 'Inventory Building', key: 'inventory_building' },
      { name: 'Dependency Analysis', key: 'dependency_analysis' }
    ];

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {crews.map((crew) => {
          const crewResult = crewResults[crew.key];
          const crewStatus = crewResult?.status || 'pending';
          const executionTime = crewResult?.execution_time;
          const progressPercentage = crewResult?.progress_percentage || 0;

          return (
            <Card key={crew.key} className="relative">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">{crew.name}</CardTitle>
                  <Badge variant={getStatusBadgeVariant(crewStatus)}>
                    {getStatusIcon(crewStatus)}
                    <span className="ml-1 capitalize">{crewStatus}</span>
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {crewStatus === 'running' || crewStatus === 'in_progress' ? (
                  <div className="space-y-2">
                    <Progress value={progressPercentage} className="w-full" />
                    <p className="text-xs text-muted-foreground">
                      {progressPercentage}% complete
                    </p>
                  </div>
                ) : crewStatus === 'completed' && executionTime ? (
                  <p className="text-xs text-muted-foreground">
                    Completed in {executionTime}s
                  </p>
                ) : crewStatus === 'failed' ? (
                  <p className="text-xs text-red-600">
                    Failed - Check logs for details
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    Waiting to start...
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    );
  };

  // Loading state
  if (currentIsLoading) {
    return (
      <div className="flex-1 flex flex-col">
        <Sidebar />
        <main className="flex-1 ml-64 p-6">
          <ContextBreadcrumbs />
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-center h-64">
              <div className="flex items-center space-x-2">
                <RefreshCw className="w-6 h-6 animate-spin" />
                <span>Loading discovery flow...</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      <Sidebar />
      <main className="flex-1 ml-64 p-6">
        <ContextBreadcrumbs />
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Discovery Flow</h1>
              <p className="text-muted-foreground">
                Orchestrate AI-powered discovery workflow with crew-based processing
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                onClick={refreshCurrentFlow}
                variant="outline"
                size="sm"
                disabled={currentIsLoading}
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Error Display */}
          {(error || currentError) && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                {error || currentError?.message || 'An error occurred'}
              </AlertDescription>
            </Alert>
          )}

          {/* Flow Status Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  {getStatusIcon(flowStatus)}
                  <span>Flow Status</span>
                </CardTitle>
                <Badge variant={getStatusBadgeVariant(flowStatus)}>
                  {flowStatus.toUpperCase()}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {currentFlow ? (
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Overall Progress</span>
                      <span>{progressPercentage}%</span>
                    </div>
                    <Progress value={progressPercentage} className="mt-2" />
                  </div>

                  {currentPhase && (
                    <p className="text-sm text-muted-foreground">
                      Current Phase: <span className="font-medium capitalize">{currentPhase}</span>
                    </p>
                  )}

                  <div className="flex items-center space-x-2">
                    {flowStatus === 'idle' && (
                      <Button onClick={handleStartDiscovery} disabled={isInitializing}>
                        <Play className="w-4 h-4 mr-1" />
                        Start Discovery
                      </Button>
                    )}

                    {flowStatus === 'running' && (
                      <Button onClick={handlePauseFlow} variant="outline">
                        <Pause className="w-4 h-4 mr-1" />
                        Pause
                      </Button>
                    )}

                    {flowStatus === 'paused' && (
                      <Button onClick={handleResumeFlow}>
                        <Play className="w-4 h-4 mr-1" />
                        Resume
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">
                    Initialize New Flow
                  </p>
                  <Button onClick={handleInitializeFlow} disabled={isInitializing}>
                    {isInitializing ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                        Initializing...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-1" />
                        Start Discovery
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Crew Sequence */}
          {currentFlow && Object.keys(crewResults).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Crew Execution Status</CardTitle>
                <p className="text-sm text-muted-foreground">
                  AI crews processing your discovery workflow
                </p>
              </CardHeader>
              <CardContent>
                {renderCrewSequence()}
              </CardContent>
            </Card>
          )}

          {/* Agent Monitoring */}
          {currentFlow && effectiveFlowId && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Agent Monitor</CardTitle>
                </CardHeader>
                <CardContent>
                  <AgentMonitor flowId={effectiveFlowId} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Flow Crew Monitor</CardTitle>
                </CardHeader>
                <CardContent>
                  <FlowCrewAgentMonitor flowId={effectiveFlowId} />
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default DiscoveryFlow;
