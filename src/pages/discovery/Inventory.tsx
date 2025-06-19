import React from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import { InventoryStateProvider } from '../../components/discovery/inventory/InventoryStateProvider';
import { InventoryContent } from '../../components/discovery/inventory/InventoryContent';
import { useInventoryLogic } from '../../hooks/discovery/useInventoryLogic';
import { useInventoryNavigation } from '../../hooks/discovery/useInventoryNavigation';
import { useAuth } from '@/contexts/AuthContext';

const Inventory = () => {
  const { client, engagement } = useAuth();
  
  // Use inventory logic hook
  const {
    // Data
    assets,
    summary,
    pagination,
    inventoryProgress,
    flowState,
    
    // Loading states
    isLoading,
    isFlowStateLoading,
    isAnalyzing,
    lastUpdated,
    
    // Errors
    error,
    flowStateError,
    
    // Filters and search
    currentPage,
    pageSize,
    filters,
    searchTerm,
    
    // Selection
    selectedAssets,
    
    // Actions
    handleTriggerInventoryBuildingCrew,
    handleBulkUpdate,
    handleAssetClassificationUpdate,
    handleFilterChange,
    handleSearchChange,
    handlePageChange,
    toggleAssetSelection,
    selectAllAssets,
    clearSelection,
    fetchAssets,
    canContinueToAppServerDependencies,
  } = useInventoryLogic();

  // Use navigation hook
  const {
    handleContinueToAppServerDependencies,
    validateInventoryCompletion,
    getInventoryCompletionMessage,
  } = useInventoryNavigation();

  // Navigation wrapper
  const handleContinueToNextPhase = () => {
    if (!client || !engagement) return;
    
    handleContinueToAppServerDependencies({
      flow_session_id: flowState?.session_id,
      inventory_progress: inventoryProgress,
      client_account_id: client.id,
      engagement_id: engagement.id,
    });
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="bg-white shadow-sm border-b p-4">
          <ContextBreadcrumbs />
          <div className="mt-2">
            <h1 className="text-2xl font-bold text-gray-800">Asset Inventory</h1>
            <p className="text-gray-600">
              Comprehensive inventory of discovered IT assets with AI-powered classification
            </p>
          </div>
        </div>
        
        <div className="flex-1 overflow-auto">
          <div className="p-6">
            
            {/* Agent Communication Panel */}
            <div className="mb-6">
              <AgentClarificationPanel refreshTrigger={0} />
            </div>

            {/* State Provider handles loading, error, and no-data states */}
            <InventoryStateProvider
              isLoading={isLoading}
              isAnalyzing={isAnalyzing}
              error={error}
              flowStateError={flowStateError}
              totalAssets={summary.total}
              onTriggerAnalysis={handleTriggerInventoryBuildingCrew}
              onRetry={fetchAssets}
            >
              {/* Main Content */}
              <InventoryContent
                assets={assets}
                summary={summary}
                inventoryProgress={inventoryProgress}
                currentPage={currentPage}
                filters={filters}
                searchTerm={searchTerm}
                selectedAssets={selectedAssets}
                lastUpdated={lastUpdated}
                onTriggerAnalysis={handleTriggerInventoryBuildingCrew}
                onFilterChange={handleFilterChange}
                onSearchChange={handleSearchChange}
                onPageChange={handlePageChange}
                onAssetSelect={toggleAssetSelection}
                onSelectAll={selectAllAssets}
                onClearSelection={clearSelection}
                onBulkUpdate={handleBulkUpdate}
                onClassificationUpdate={handleAssetClassificationUpdate}
                onContinueToAppServerDependencies={handleContinueToNextPhase}
                canContinueToAppServerDependencies={canContinueToAppServerDependencies()}
              />
            </InventoryStateProvider>

            {/* Agent Insights */}
            <div className="mt-6">
              <AgentInsightsSection />
            </div>

            {/* Agent Planning Dashboard */}
            <div className="mt-6">
              <AgentPlanningDashboard />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Inventory;
