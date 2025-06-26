import React from 'react';
import { useParams } from 'react-router-dom';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import { InventoryStateProvider } from '../../components/discovery/inventory/InventoryStateProvider';
import { InventoryContent } from '../../components/discovery/inventory/InventoryContent';
import { useInventoryLogic } from '../../hooks/discovery/useInventoryLogic';
import { useInventoryNavigation } from '../../hooks/discovery/useInventoryNavigation';
import { useInventoryFlowDetection } from '../../hooks/discovery/useDiscoveryFlowAutoDetection';
import { useAuth } from '@/contexts/AuthContext';

const Inventory = () => {
  const { client, engagement } = useAuth();
  
  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    hasEffectiveFlow
  } = useInventoryFlowDetection();
  
  // Use inventory logic hook - pass effectiveFlowId instead of urlFlowId
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
  } = useInventoryLogic(effectiveFlowId);

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
      client_account_id: typeof client.id === 'string' ? parseInt(client.id) : client.id,
      engagement_id: typeof engagement.id === 'string' ? parseInt(engagement.id) : engagement.id,
    });
  };

  // Debug info for flow detection
  console.log('🔍 Inventory flow detection:', {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    totalFlowsAvailable: flowList?.length || 0
  });

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
                <h1 className="text-3xl font-bold text-gray-900">Asset Inventory</h1>
                <p className="text-gray-600">
                  {inventoryProgress.total_assets > 0 
                    ? `${inventoryProgress.total_assets} assets discovered with ${inventoryProgress.classified_assets} classified (${Math.round(inventoryProgress.classification_accuracy)}% accuracy)` 
                    : 'Comprehensive inventory of discovered IT assets with AI-powered classification'
                  }
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              {/* Main Inventory Content with State Provider */}
              <InventoryStateProvider
                isLoading={isLoading}
                isAnalyzing={isAnalyzing}
                error={error?.message || ''}
                flowStateError={flowStateError?.message || ''}
                totalAssets={summary.total}
                onTriggerAnalysis={handleTriggerInventoryBuildingCrew}
                onRetry={fetchAssets}
              >
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
            </div>

            <div className="xl:col-span-1 space-y-6">
              {/* Agent Communication Panel */}
              <AgentClarificationPanel 
                pageContext="asset-inventory"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Inventory question answered:', questionId, response);
                  fetchAssets();
                }}
              />

              {/* Agent Insights */}
              <AgentInsightsSection 
                pageContext="asset-inventory"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Inventory insight action:', insightId, action);
                  if (action === 'apply_insight') {
                    fetchAssets();
                  }
                }}
              />

              {/* Agent Planning Dashboard */}
              <AgentPlanningDashboard pageContext="asset-inventory" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Inventory;
