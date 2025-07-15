/**
 * Master Flow Dashboard Component
 * MFO-087: Update dashboards to show all flow types
 * 
 * Unified dashboard for viewing and managing all flow types
 * through the Master Flow Orchestrator system
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  Plus,
  Filter,
  Search
} from 'lucide-react';
import { useFlows } from '../../hooks/useFlow';
import { FlowStatus, FlowType } from '../../types/flow';
import { flowToast } from '../../utils/toast';
import { getFlowPhaseRoute } from '@/config/flowRoutes';
import { useNavigate } from 'react-router-dom';
import { useFlowDeletion } from '../../hooks/useFlowDeletion';
import { FlowDeletionModal } from './FlowDeletionModal';
import { useAuth } from '@/contexts/AuthContext';

interface MasterFlowDashboardProps {
  filterByType?: FlowType;
  showAnalytics?: boolean;
}

const FLOW_TYPE_CONFIG: Record<FlowType, { label: string; color: string; icon: React.ReactNode }> = {
  discovery: { label: 'Discovery', color: 'blue', icon: <Search className="w-4 h-4" /> },
  assessment: { label: 'Assessment', color: 'purple', icon: <Activity className="w-4 h-4" /> },
  planning: { label: 'Planning', color: 'green', icon: <Clock className="w-4 h-4" /> },
  execution: { label: 'Execution', color: 'orange', icon: <PlayCircle className="w-4 h-4" /> },
  modernize: { label: 'Modernize', color: 'indigo', icon: <RefreshCw className="w-4 h-4" /> },
  finops: { label: 'FinOps', color: 'yellow', icon: <Activity className="w-4 h-4" /> },
  observability: { label: 'Observability', color: 'cyan', icon: <Activity className="w-4 h-4" /> },
  decommission: { label: 'Decommission', color: 'red', icon: <XCircle className="w-4 h-4" /> }
};

export const MasterFlowDashboard: React.FC<MasterFlowDashboardProps> = ({
  filterByType,
  showAnalytics = true
}) => {
  const navigate = useNavigate();
  const { client, engagement, user } = useAuth();
  const [selectedType, setSelectedType] = useState<FlowType | 'all'>(filterByType || 'all');
  const [searchQuery, setSearchQuery] = useState('');

  // Use the unified flows hook with production-optimized polling
  const [state, actions] = useFlows(
    selectedType === 'all' ? undefined : selectedType,
    {
      autoRefresh: true,
      refreshInterval: 30000, // 30 seconds for production performance
      onError: (error) => flowToast.error(error)
    }
  );

  // Use the flow deletion hook with modal confirmation
  const [deletionState, deletionActions] = useFlowDeletion(
    async (result) => {
      // Refresh flows after successful deletion
      await actions.refreshFlows();
    },
    (error) => {
      flowToast.error(error);
    }
  );

  // Filter flows based on search query
  const filteredFlows = state.flows.filter(flow => 
    flow.flow_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    flow.flow_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Group flows by status
  const flowsByStatus = filteredFlows.reduce((acc, flow) => {
    const status = flow.status;
    if (!acc[status]) acc[status] = [];
    acc[status].push(flow);
    return acc;
  }, {} as Record<string, FlowStatus[]>);

  // Calculate analytics
  const analytics = {
    total: filteredFlows.length,
    byType: Object.entries(
      filteredFlows.reduce((acc, flow) => {
        acc[flow.flow_type] = (acc[flow.flow_type] || 0) + 1;
        return acc;
      }, {} as Record<string, number>)
    ),
    byStatus: Object.entries(flowsByStatus).map(([status, flows]) => ({
      status,
      count: flows.length
    })),
    activeFlows: filteredFlows.filter(f => ['running', 'paused'].includes(f.status)).length,
    completedFlows: filteredFlows.filter(f => f.status === 'completed').length,
    failedFlows: filteredFlows.filter(f => f.status === 'failed').length
  };

  // Handle flow navigation
  const handleFlowClick = (flow: FlowStatus) => {
    const route = getFlowPhaseRoute(
      flow.flow_type,
      flow.current_phase || flow.status,
      flow.flow_id
    );
    navigate(route);
  };

  // Handle flow actions
  const handlePauseFlow = async (flow: FlowStatus) => {
    try {
      await actions.pauseFlow(flow.flow_id);
      await actions.refreshFlows();
    } catch (error) {
      flowToast.error(error as Error);
    }
  };

  const handleResumeFlow = async (flow: FlowStatus) => {
    try {
      await actions.resumeFlow(flow.flow_id);
      await actions.refreshFlows();
    } catch (error) {
      flowToast.error(error as Error);
    }
  };

  const handleDeleteFlow = async (flow: FlowStatus) => {
    if (!client?.id) {
      flowToast.error(new Error('Client context is required for flow deletion'));
      return;
    }
    
    // Request deletion with modal confirmation
    await deletionActions.requestDeletion(
      [flow.flow_id],
      client.id,
      engagement?.id,
      'manual',
      user?.id
    );
  };

  // Status badge component
  const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
    const variants: Record<string, string> = {
      pending: 'secondary',
      running: 'default',
      paused: 'warning',
      completed: 'success',
      failed: 'destructive',
      cancelled: 'secondary'
    };

    return (
      <Badge variant={variants[status] as any || 'secondary'}>
        {status}
      </Badge>
    );
  };

  // Flow card component
  const FlowCard: React.FC<{ flow: FlowStatus }> = ({ flow }) => {
    const config = FLOW_TYPE_CONFIG[flow.flow_type];
    
    return (
      <Card 
        className="cursor-pointer hover:shadow-lg transition-shadow"
        onClick={() => handleFlowClick(flow)}
      >
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {config.icon}
              <CardTitle className="text-lg">{flow.flow_name}</CardTitle>
            </div>
            <StatusBadge status={flow.status} />
          </div>
          <CardDescription>
            {flow.flow_type} • {flow.flow_id}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* Progress */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Progress</span>
                <span>{flow.progress_percentage}%</span>
              </div>
              <Progress value={flow.progress_percentage} />
            </div>

            {/* Current Phase */}
            {flow.current_phase && (
              <div className="text-sm">
                <span className="text-muted-foreground">Current Phase:</span>{' '}
                <span className="font-medium">{flow.current_phase}</span>
              </div>
            )}

            {/* Timestamps */}
            <div className="text-xs text-muted-foreground">
              Created: {new Date(flow.created_at).toLocaleString()}
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-4" onClick={e => e.stopPropagation()}>
              {flow.can_pause && flow.status === 'running' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handlePauseFlow(flow)}
                >
                  <PauseCircle className="w-4 h-4 mr-1" />
                  Pause
                </Button>
              )}
              {flow.can_resume && flow.status === 'paused' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleResumeFlow(flow)}
                >
                  <PlayCircle className="w-4 h-4 mr-1" />
                  Resume
                </Button>
              )}
              {flow.can_cancel && (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleDeleteFlow(flow)}
                >
                  <XCircle className="w-4 h-4 mr-1" />
                  Delete
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Master Flow Dashboard</h1>
        <Button onClick={() => navigate('/flows/create')}>
          <Plus className="w-4 h-4 mr-2" />
          Create Flow
        </Button>
      </div>

      {/* Analytics Summary */}
      {showAnalytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Total Flows</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{analytics.total}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Active Flows</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{analytics.activeFlows}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{analytics.completedFlows}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{analytics.failedFlows}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters and Search */}
      <div className="flex gap-4 items-center">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <input
              type="text"
              placeholder="Search flows..."
              className="w-full pl-10 pr-4 py-2 border rounded-md"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        <Button variant="outline" size="icon" onClick={() => actions.refreshFlows()}>
          <RefreshCw className={`w-4 h-4 ${state.isRefreshing ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Flow Type Tabs */}
      <Tabs value={selectedType} onValueChange={(value) => setSelectedType(value as FlowType | 'all')}>
        <TabsList>
          <TabsTrigger value="all">All Flows</TabsTrigger>
          {Object.entries(FLOW_TYPE_CONFIG).map(([type, config]) => (
            <TabsTrigger key={type} value={type}>
              <div className="flex items-center gap-1">
                {config.icon}
                {config.label}
              </div>
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={selectedType} className="mt-6">
          {state.isLoading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading flows...</p>
            </div>
          ) : filteredFlows.length === 0 ? (
            <Alert>
              <AlertDescription>
                No flows found. {selectedType !== 'all' && `Try selecting "All Flows" to see flows from other types.`}
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredFlows.map(flow => (
                <FlowCard key={flow.flow_id} flow={flow} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Error Display */}
      {state.error && (
        <Alert variant="destructive">
          <AlertDescription>
            Error loading flows: {state.error.message}
          </AlertDescription>
        </Alert>
      )}

      {/* Flow Deletion Modal */}
      <FlowDeletionModal
        open={deletionState.isModalOpen}
        candidates={deletionState.candidates}
        deletionSource={deletionState.deletionSource}
        isDeleting={deletionState.isDeleting}
        onConfirm={deletionActions.confirmDeletion}
        onCancel={deletionActions.cancelDeletion}
      />
    </div>
  );
};

export default MasterFlowDashboard;