import React from 'react';
import { useNavigate } from 'react-router-dom';
import { getDiscoveryPhaseRoute } from '@/config/flowRoutes';
import { DiscoveryErrorBoundary } from '@/components/discovery/DiscoveryErrorBoundary';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Components
import Sidebar from '../../../components/Sidebar';
import ContextBreadcrumbs from '../../../components/context/ContextBreadcrumbs';
import FlowStatusWidget from '../../../components/discovery/FlowStatusWidget';
import { AgentGuidanceModal } from '../../../components/discovery/AgentGuidanceModal';

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
import { useFlowDeletion } from '@/hooks/useFlowDeletion';
import { FlowDeletionModal } from '@/components/flows/FlowDeletionModal';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';

// Type alias for the error boundary
const DashboardErrorBoundary = DiscoveryErrorBoundary;

const EnhancedDiscoveryDashboardContainer: React.FC = () => {
  const navigate = useNavigate();
  const { client, engagement, user } = useAuth();
  const { toast } = useToast();

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

  // Flow Management hooks
  // BUGFIX: Disable useIncompleteFlowDetectionV2 on dashboard to prevent race condition
  // The dashboard already fetches all flow data via useDashboard hook, so this duplicate
  // data fetching was causing state overwrites and showing "0 flows" despite having 16+ flows
  // The incomplete flow detection is handled by the dashboard service itself
  // const { data: incompleteFlowsData } = useIncompleteFlowDetectionV2();
  const incompleteFlowsData = { flows: [] }; // Temporary: Use dashboard flow data instead

  const [deletionState, deletionActions] = useFlowDeletion(
    // onDeletionComplete callback
    () => {
      // Refresh dashboard data after successful deletion
      fetchDashboardData();
    },
    // onDeletionError callback
    (error) => {
      console.error('Flow deletion error:', error);
      toast({
        title: "Deletion Failed",
        description: error.message || "Failed to delete flow",
        variant: "destructive",
      });
    }
  );

  const incompleteFlows = incompleteFlowsData?.flows || [];
  const hasIncompleteFlows = incompleteFlows.length > 0;

  // Handle view details navigation with agentic intelligence
  const handleViewDetails = (flowId: string, phase: string): void => {
    console.log(`🔍 Navigating to view details for flow ${flowId} in phase "${phase}"`);

    // If phase is 'current', we need to find the actual phase from the flow data
    let actualPhase = phase;
    if (phase === 'current') {
      const flow = activeFlows.find(f => f.flow_id === flowId);
      if (flow) {
        actualPhase = flow.current_phase;
        console.log(`✅ Resolved 'current' phase to actual phase: ${actualPhase}`);
      }
    }

    // Handle completed flows specially
    if (actualPhase === "completed") {
      console.log(`✅ Flow marked as completed, routing to inventory`);
      navigate(`/discovery/inventory/${flowId}`);
      return;
    }

    // Use centralized routing configuration instead of hardcoded mapping
    const route = getDiscoveryPhaseRoute(actualPhase, flowId);
    console.log(`✅ Navigation decision: phase="${actualPhase}" -> route="${route}"`);
    navigate(route);
  };

  // Handle flow deletion using centralized user-approval system
  const handleDeleteFlow = async (flowId: string): void => {
    if (!client?.id) {
      toast({
        title: "Error",
        description: "Client context is required for flow deletion",
        variant: "destructive",
      });
      return;
    }

    console.log('🗑️ Discovery Dashboard: Initiating flow deletion with user approval');
    await deletionActions.requestDeletion(
      [flowId],
      client.id,
      engagement?.id,
      'discovery_dashboard',
      user?.id
    );
  };

  // Handle batch deletion
  const handleBatchDelete = async (flowIds: string[]): void => {
    if (!client?.id) {
      toast({
        title: "Error",
        description: "Client context is required for flow deletion",
        variant: "destructive",
      });
      return;
    }

    console.log(`🗑️ Discovery Dashboard: Initiating batch deletion of ${flowIds.length} flows`);
    await deletionActions.requestDeletion(
      flowIds,
      client.id,
      engagement?.id,
      'bulk_cleanup',
      user?.id
    );
  };

  // Navigation handlers
  const handleNewFlow = (): void => {
    navigate('/discovery/cmdb-import');
  };

  const handleDataImport = (): void => {
    navigate('/discovery/cmdb-import');
  };

  const handleViewFlows = (): void => {
    toggleFlowManager(true);
  };

  const handleSystemHealth = (): void => {
    // Navigate to system health page when available
    console.log('System health navigation not yet implemented');
  };

  // Time range change handler
  const handleTimeRangeChange = (timeRange: string): void => {
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
                    isDeleting={deletionState.isDeleting}
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
                isDeleting={deletionState.isDeleting}
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

          {/* Flow Status Dialog - Show full FlowStatusWidget */}
          {selectedFlowForStatus && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Flow Status Monitor</h3>
                  <button
                    onClick={() => setSelectedFlowForStatus(null)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="p-6">
                  <FlowStatusWidget
                    flowId={selectedFlowForStatus}
                    flowType="discovery"
                    className="w-full"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Flow Deletion Confirmation Modal */}
          <FlowDeletionModal {...deletionState} {...deletionActions} />
        </div>
      </div>
    </div>
  );
};

const EnhancedDiscoveryDashboardWithErrorBoundary: React.FC = () => (
  <DashboardErrorBoundary>
    <EnhancedDiscoveryDashboardContainer />
  </DashboardErrorBoundary>
);

export default EnhancedDiscoveryDashboardWithErrorBoundary;
