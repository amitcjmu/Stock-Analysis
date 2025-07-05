import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';

// Components
import Sidebar from '../../../components/Sidebar';
import ContextBreadcrumbs from '../../../components/context/ContextBreadcrumbs';
import { IncompleteFlowManager } from '@/components/discovery/IncompleteFlowManager';
import FlowStatusWidget from '@/components/discovery/FlowStatusWidget';

// Custom hooks and components
import { useDashboard } from './hooks/useDashboard';
import { useFlowMetrics } from './hooks/useFlowMetrics';
import { useDashboardFilters } from './hooks/useDashboardFilters';
import { DashboardHeader } from './components/DashboardHeader';
import { FlowsOverview } from './components/FlowsOverview';
import { MetricsPanel } from './components/MetricsPanel';
import { ActivityTimeline } from './components/ActivityTimeline';
import { QuickActions } from './components/QuickActions';

// Flow Management hooks
import { 
  useIncompleteFlowDetectionV2,
  useFlowDeletionV2
} from '@/hooks/discovery/useFlowOperations';

const EnhancedDiscoveryDashboardContainer: React.FC = () => {
  const navigate = useNavigate();
  
  // Dashboard state and actions
  const {
    activeFlows,
    systemMetrics,
    crewPerformance,
    platformAlerts,
    selectedTimeRange,
    isLoading,
    lastUpdated,
    error,
    showIncompleteFlowManager,
    selectedFlowForStatus,
    fetchDashboardData,
    refreshFlow,
    setSelectedTimeRange,
    toggleFlowManager,
    setSelectedFlowForStatus
  } = useDashboard();

  // Flow metrics calculations
  const flowMetrics = useFlowMetrics(activeFlows, systemMetrics);

  // Dashboard filters
  const {
    filters,
    filteredFlows,
    setTimeRange,
    resetFilters
  } = useDashboardFilters(activeFlows);

  // V2 Flow Management hooks
  const { data: incompleteFlowsData } = useIncompleteFlowDetectionV2();
  const { mutate: deleteFlow, isPending: isDeleting } = useFlowDeletionV2();
  
  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;

  // Handle view details navigation with agentic intelligence
  const handleViewDetails = (flowId: string, phase: string) => {
    console.log(`🤖 AGENTIC NAVIGATION: Analyzing flow ${flowId} in phase "${phase}"`);
    
    // If phase is 'current', we need to find the actual phase from the flow data
    let actualPhase = phase;
    if (phase === 'current') {
      const flow = activeFlows.find(f => f.flow_id === flowId);
      if (flow) {
        actualPhase = flow.current_phase;
        console.log(`🤖 Resolved 'current' phase to actual phase: ${actualPhase}`);
      }
    }
    
    // Handle completed flows specially
    if (actualPhase === "completed") {
      console.log(`🤖 Flow marked as completed, routing to inventory`);
      navigate(`/discovery/inventory/${flowId}`);
      return;
    }
    
    // Use centralized routing configuration
    const route = getDiscoveryPhaseRoute(actualPhase, flowId);
    console.log(`🤖 AGENTIC DECISION: phase="${actualPhase}" -> route="${route}"`);
    navigate(route);
  };

  // Handle flow deletion
  const handleDeleteFlow = (flowId: string) => {
    deleteFlow({ flowId });
  };

  // Navigation handlers
  const handleNewFlow = () => {
    navigate('/discovery/cmdb-import');
  };

  const handleDataImport = () => {
    navigate('/discovery/cmdb-import');
  };

  const handleViewFlows = () => {
    toggleFlowManager(true);
  };

  const handleSystemHealth = () => {
    // Navigate to system health page when available
    console.log('System health navigation not yet implemented');
  };

  // Time range change handler
  const handleTimeRangeChange = (timeRange: string) => {
    setSelectedTimeRange(timeRange);
    setTimeRange(timeRange);
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="hidden lg:block w-64 border-r bg-white">
        <Sidebar />
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
          {/* Context Breadcrumbs */}
          <div className="mb-6">
            <ContextBreadcrumbs />
          </div>
          
          {/* Dashboard Header */}
          <DashboardHeader
            filters={filters}
            onRefresh={fetchDashboardData}
            onTimeRangeChange={handleTimeRangeChange}
            onNewFlow={handleNewFlow}
            isLoading={isLoading}
            lastUpdated={lastUpdated}
            totalFlows={flowMetrics.totalFlows}
            activeFlows={flowMetrics.runningFlows}
          />

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Dashboard Content */}
          <Tabs defaultValue="overview" className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="flows">Flows</TabsTrigger>
              <TabsTrigger value="metrics">Metrics</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <FlowsOverview
                    flows={filteredFlows.slice(0, 5)} // Show top 5 in overview
                    onViewDetails={handleViewDetails}
                    onDeleteFlow={handleDeleteFlow}
                    onSetFlowStatus={setSelectedFlowForStatus}
                    isDeleting={isDeleting}
                  />
                </div>
                <div className="space-y-6">
                  <QuickActions
                    onNewFlow={handleNewFlow}
                    onDataImport={handleDataImport}
                    onViewFlows={handleViewFlows}
                    onSystemHealth={handleSystemHealth}
                    onRefreshDashboard={fetchDashboardData}
                    isLoading={isLoading}
                  />
                  <ActivityTimeline alerts={platformAlerts.slice(0, 5)} />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="flows" className="space-y-6">
              <FlowsOverview
                flows={filteredFlows}
                onViewDetails={handleViewDetails}
                onDeleteFlow={handleDeleteFlow}
                onSetFlowStatus={setSelectedFlowForStatus}
                isDeleting={isDeleting}
              />
            </TabsContent>

            <TabsContent value="metrics" className="space-y-6">
              <MetricsPanel
                systemMetrics={systemMetrics}
                flowMetrics={flowMetrics}
              />
            </TabsContent>

            <TabsContent value="activity" className="space-y-6">
              <ActivityTimeline alerts={platformAlerts} />
            </TabsContent>
          </Tabs>

          {/* Flow Status Monitor Dialog */}
          {selectedFlowForStatus && (
            <Dialog open={!!selectedFlowForStatus} onOpenChange={() => setSelectedFlowForStatus(null)}>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Flow Status Monitor</DialogTitle>
                </DialogHeader>
                <FlowStatusWidget
                  flowId={selectedFlowForStatus}
                  onClose={() => setSelectedFlowForStatus(null)}
                />
              </DialogContent>
            </Dialog>
          )}

          {/* Incomplete Flow Manager Dialog */}
          <Dialog open={showIncompleteFlowManager} onOpenChange={toggleFlowManager}>
            <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Manage Discovery Flows</DialogTitle>
              </DialogHeader>
              <IncompleteFlowManager
                flows={incompleteFlows}
                onContinueFlow={(flowId) => {
                  // Find the flow to get its current phase
                  const flow = incompleteFlows.find(f => f.flow_id === flowId);
                  const phase = flow?.current_phase || 'data_import_validation';
                  handleViewDetails(flowId, phase);
                }}
                onDeleteFlow={handleDeleteFlow}
                onBatchDelete={(flowIds) => flowIds.forEach(handleDeleteFlow)}
                onViewDetails={(flowId, phase) => handleViewDetails(flowId, phase)}
                onClose={() => toggleFlowManager(false)}
                isLoading={isDeleting}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  );
};

export default EnhancedDiscoveryDashboardContainer;