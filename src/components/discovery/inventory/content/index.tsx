import React, { useState, useMemo, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../../../contexts/AuthContext';
import { useUnifiedDiscoveryFlow } from '../../../../hooks/useUnifiedDiscoveryFlow';
import type { Asset } from '../../../../types/asset';
import SecureLogger from '../../../../utils/secureLogger';
import { assetConflictService } from '../../../../services/api/assetConflictService';
import type { AssetConflict } from '../../../../types/assetConflict';

// Components
import { InventoryOverview } from '../components/InventoryOverview';
import { ClassificationProgress } from '../components/ClassificationProgress';
import { ClassificationCards } from '../components/ClassificationCards';
import { AssetTable } from '../components/AssetTable';
import { NextStepCard } from '../components/NextStepCard';
import EnhancedInventoryInsights from '../EnhancedInventoryInsights';
import { ApplicationSelectionModal } from '../components/ApplicationSelectionModal';
import AssetConflictModal from '../../AssetConflictModal';

// Modularized Components
import { ViewModeToggle } from './ViewModeToggle';
import { CleansingRequiredBanner, ExecutionErrorBanner, ConflictResolutionBanner } from './ErrorBanners';
import { LoadingState, ErrorState, EmptyState } from './InventoryStates';

// Hooks
import { useInventoryProgress } from '../hooks/useInventoryProgress';
import { useAssetFilters } from '../hooks/useAssetFilters';
import { useAssetSelection } from '../hooks/useAssetSelection';
import { useInventoryData } from './hooks/useInventoryData';
import { useAutoExecution } from './hooks/useAutoExecution';
import { useInventoryActions } from './InventoryActions';

// Utils
import { exportAssets } from '../utils/exportHelpers';

// Types
import type { InventoryContentProps } from '../types/inventory.types';

const DEFAULT_COLUMNS = [
  'asset_name', 'asset_type', 'environment', 'operating_system',
  'location', 'status', 'business_criticality', 'risk_score',
  'migration_readiness', 'dependencies', 'last_updated'
];

const RECORDS_PER_PAGE = 10;

const InventoryContent: React.FC<InventoryContentProps> = ({
  className = "",
  flowId
}) => {
  const { client, engagement } = useAuth();
  const queryClient = useQueryClient();
  const { flowState: flow, executeFlowPhase, isExecutingPhase, refreshFlow } = useUnifiedDiscoveryFlow(flowId);

  // Debug logging
  console.log('🔍 InventoryContent flow state:', {
    flowId,
    currentPhase: flow?.current_phase,
    hasAssetInventory: !!flow?.asset_inventory,
    assetCount: flow?.asset_inventory?.assets?.length || 0,
    rawDataCount: flow?.raw_data?.length || 0,
    phaseCompletion: flow?.phase_completion
  });

  // Get assets from flow if available, but this should not be the only source
  const getAssetsFromFlow = () => flow?.asset_inventory?.assets || [];

  // State
  const [selectedColumns, setSelectedColumns] = useState(DEFAULT_COLUMNS);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasTriggeredInventory, setHasTriggeredInventory] = useState(false);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [showCleansingRequiredBanner, setShowCleansingRequiredBanner] = useState(false);
  const [needsClassification, setNeedsClassification] = useState(false);
  const [isReclassifying, setIsReclassifying] = useState(false);
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [viewMode, setViewMode] = useState<'all' | 'current_flow'>(!flowId ? 'all' : 'current_flow');
  const [hasFlowId, setHasFlowId] = useState<boolean>(Boolean(flowId));

  // Asset conflict resolution state
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [assetConflicts, setAssetConflicts] = useState<AssetConflict[]>([]);

  // Update hasFlowId state to prevent SSR hydration mismatch
  React.useEffect(() => {
    setHasFlowId(Boolean(flowId));
  }, [flowId]);

  // Safety: auto-revert to 'all' if flowId disappears while in 'current_flow'
  React.useEffect(() => {
    let mounted = true;
    if (!flowId && mounted) {
      setViewMode((prev) => (prev === 'current_flow' ? 'all' : prev));
    }
    return () => {
      mounted = false;
    };
  }, [flowId]);

  // Check for collectionFlowId parameter to auto-show application selection modal
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const collectionFlowId = urlParams.get('collectionFlowId');

    if (collectionFlowId) {
      console.log('🔗 Collection flow requires application selection:', collectionFlowId);
      setShowApplicationModal(true);
    }
  }, []);

  // Use inventory data hook (lines 108-348 from original)
  const { assets, assetsLoading, refetchAssets, hasBackendError } = useInventoryData({
    clientId: client?.id,
    engagementId: engagement?.id,
    viewMode,
    flowId,
    setNeedsClassification,
    setHasTriggeredInventory,
    getAssetsFromFlow
  });

  // Get all available columns
  const allColumns = useMemo(() => {
    if (assets.length === 0) return [];
    const columns = new Set<string>();
    assets.forEach(asset => {
      Object.keys(asset).forEach(key => {
        if (key !== 'id') columns.add(key);
      });
    });
    return Array.from(columns).sort();
  }, [assets]);

  // Hooks
  const inventoryProgress = useInventoryProgress(assets);
  const {
    filters,
    updateFilter,
    filteredAssets,
    uniqueEnvironments
  } = useAssetFilters(assets);
  const {
    selectedAssets,
    handleSelectAsset,
    handleSelectAll,
    clearSelection
  } = useAssetSelection();

  // Actions hook
  const { handleRefreshClassification, handleReclassifySelected } = useInventoryActions({
    executeFlowPhase,
    refetchAssets,
    refreshFlow,
    setHasTriggeredInventory,
    setExecutionError,
    setShowCleansingRequiredBanner
  });

  // Auto-execution hook (lines 523-648 from original) - CRITICAL: preserves retry state machine
  const { attemptCountRef } = useAutoExecution({
    flow,
    isExecutingPhase,
    hasTriggeredInventory,
    assetsLength: assets.length,
    executeFlowPhase,
    refetchAssets,
    refreshFlow,
    executionError,
    setHasTriggeredInventory,
    setExecutionError,
    setShowCleansingRequiredBanner
  });

  // Separate useEffect to handle classification needs without causing loops
  useEffect(() => {
    // Only show console message when classification is needed
    if (needsClassification && assets.length > 0) {
      console.log('🚨 Assets need classification - use the refresh button to trigger CrewAI processing');
    }
  }, [needsClassification, assets.length]);

  // Check for asset conflicts (duplicate detection during import)
  useEffect(() => {
    const checkForConflicts = async (): Promise<void> => {
      // CC DEBUG: Comprehensive logging for conflict detection troubleshooting
      console.log('🔍 [ConflictDetection] useEffect triggered', {
        flowId,
        hasFlow: !!flow,
        currentPhase: flow?.current_phase,
        status: flow?.status,
        phase_state: flow?.phase_state,
        conflict_resolution_pending: flow?.phase_state?.conflict_resolution_pending,
      });

      if (!flowId || !flow) {
        console.log('⚠️ [ConflictDetection] Missing flowId or flow, skipping check');
        return;
      }

      // Check if flow is paused for conflict resolution
      // Backend sets phase_state.conflict_resolution_pending = true when conflicts exist
      const has_conflicts = flow?.phase_state?.conflict_resolution_pending === true;

      console.log('🔍 [ConflictDetection] Conflict flag check', {
        has_conflicts,
        phase_state_type: typeof flow?.phase_state,
        phase_state_keys: flow?.phase_state ? Object.keys(flow.phase_state) : [],
      });

      if (has_conflicts) {
        try {
          SecureLogger.info('Conflict resolution pending, fetching conflicts', {
            flowId,
          });
          console.log('📋 [ConflictDetection] Fetching conflicts from API...');

          // Fetch pending conflicts from backend
          const conflicts = await assetConflictService.listConflicts(flowId);

          console.log('✅ [ConflictDetection] API response received', {
            conflictCount: conflicts.length,
            conflictIds: conflicts.map(c => c.conflict_id).slice(0, 3),
          });

          if (conflicts.length > 0) {
            SecureLogger.info('Found pending asset conflicts', {
              conflictCount: conflicts.length,
            });
            console.log('🚨 [ConflictDetection] Setting conflicts and showing modal');
            setAssetConflicts(conflicts);
            setShowConflictModal(true);
          } else {
            // No conflicts found, clear the pending flag
            SecureLogger.info('No conflicts found, clearing modal');
            console.log('✅ [ConflictDetection] No conflicts, clearing modal');
            setAssetConflicts([]);
            setShowConflictModal(false);
          }
        } catch (error) {
          SecureLogger.error('Failed to fetch asset conflicts', error);
          console.error('❌ [ConflictDetection] API fetch failed', error);
          // Don't show modal if fetch fails
          setShowConflictModal(false);
        }
      } else {
        console.log('ℹ️ [ConflictDetection] No conflict flag set, skipping fetch');
      }
    };

    checkForConflicts();
  }, [flowId, flow?.phase_state]);

  // Handle conflict resolution completion
  const handleConflictResolutionComplete = async (): Promise<void> => {
    SecureLogger.info('Conflict resolution completed, refreshing flow state');

    // Close modal
    setShowConflictModal(false);
    setAssetConflicts([]);

    // CC FIX: Force cache invalidation to fetch fresh data from server
    // The 2-minute staleTime in useUnifiedDiscoveryFlow prevents refetch if data is recent
    // We need fresh data to clear the conflict_resolution_pending flag
    await queryClient.invalidateQueries({
      queryKey: ['unifiedDiscoveryFlow', flowId, client?.id, engagement?.id],
      refetchType: 'active'  // Force refetch even if data is not stale
    });

    // Refresh flow state to get updated phase_state
    await refreshFlow();

    // Refresh assets list to show newly created/updated assets
    await refetchAssets();

    // If flow was paused, it should auto-resume after conflicts are resolved
    // Backend handles this automatically
  };

  // Handlers
  const handleClassificationCardClick = (assetType: string): void => {
    updateFilter('selectedAssetType', assetType);
    setCurrentPage(1);
  };

  const toggleColumn = (column: string): unknown => {
    setSelectedColumns(prev =>
      prev.includes(column)
        ? prev.filter(col => col !== column)
        : [...prev, column]
    );
  };

  const handleExportAssets = (): void => {
    exportAssets(filteredAssets, selectedColumns);
  };

  // Process selected applications for assessment
  const handleProcessForAssessment = (): void => {
    setShowApplicationModal(true);
  };

  // Get selected application IDs
  const selectedApplicationIds = useMemo(() => {
    return filteredAssets
      .filter(asset => selectedAssets.includes(asset.id) && asset.asset_type === 'Application')
      .map(asset => asset.id);
  }, [selectedAssets, filteredAssets]);

  // Check if any selected assets are applications
  const isApplicationsSelected = selectedApplicationIds.length > 0;

  // Reclassify selected assets function
  const handleReclassifySelectedWrapper = async (): Promise<void> => {
    setIsReclassifying(true);
    try {
      await handleReclassifySelected(selectedAssets, clearSelection);
    } finally {
      setIsReclassifying(false);
    }
  };

  // Render ViewModeToggle and error banners at top level, always visible regardless of state
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Asset Conflict Resolution Modal */}
      <AssetConflictModal
        conflicts={assetConflicts}
        isOpen={showConflictModal}
        onClose={() => {
          // Keep conflicts in state so user can re-open the modal via the banner
          // Conflicts are only cleared when actually resolved in handleConflictResolutionComplete
          setShowConflictModal(false);
        }}
        onResolutionComplete={handleConflictResolutionComplete}
      />

      <ViewModeToggle
        viewMode={viewMode}
        setViewMode={setViewMode}
        setCurrentPage={setCurrentPage}
        hasFlowId={hasFlowId}
        assetsLoading={assetsLoading}
        flowId={flowId}
      />

      <ConflictResolutionBanner
        conflictCount={assetConflicts.length}
        onResolveConflicts={() => setShowConflictModal(true)}
      />

      <CleansingRequiredBanner
        showCleansingRequiredBanner={showCleansingRequiredBanner}
        setShowCleansingRequiredBanner={setShowCleansingRequiredBanner}
        setExecutionError={setExecutionError}
      />

      <ExecutionErrorBanner
        executionError={executionError}
        showCleansingRequiredBanner={showCleansingRequiredBanner}
        setExecutionError={setExecutionError}
        attemptCountRef={attemptCountRef}
      />

      {/* Loading State */}
      {(assetsLoading || isExecutingPhase) && (
        <LoadingState isExecutingPhase={isExecutingPhase} viewMode={viewMode} />
      )}

      {/* Error State */}
      {hasBackendError && !assetsLoading && (
        <ErrorState viewMode={viewMode} refetchAssets={refetchAssets} />
      )}

      {/* Empty State */}
      {assets.length === 0 && !assetsLoading && !hasBackendError && (
        <EmptyState
          flow={flow}
          viewMode={viewMode}
          isExecutingPhase={isExecutingPhase}
          hasTriggeredInventory={hasTriggeredInventory}
          executeFlowPhase={executeFlowPhase}
          refetchAssets={refetchAssets}
          refreshFlow={refreshFlow}
          setHasTriggeredInventory={setHasTriggeredInventory}
          onOpenConflictModal={() => setShowConflictModal(true)}
        />
      )}

      {/* Main Content State - Only render when we have assets */}
      {assets.length > 0 && !assetsLoading && !hasBackendError && (
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid grid-cols-3 w-full max-w-md mx-auto mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="inventory">Inventory</TabsTrigger>
            <TabsTrigger value="insights">AI Insights</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <InventoryOverview inventoryProgress={inventoryProgress} />
            <ClassificationProgress
              inventoryProgress={inventoryProgress}
              onRefresh={handleRefreshClassification}
              needsClassification={needsClassification}
            />
            <ClassificationCards
              inventoryProgress={inventoryProgress}
              selectedAssetType={filters.selectedAssetType}
              onAssetTypeSelect={handleClassificationCardClick}
              flowId={flowId}
            />
            <NextStepCard inventoryProgress={inventoryProgress} />

            {/* Show filtered asset details below Next Step when a type is selected */}
            {filters.selectedAssetType !== 'all' && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">
                  {filters.selectedAssetType.charAt(0).toUpperCase() + filters.selectedAssetType.slice(1)} Assets
                </h3>
                <AssetTable
                  assets={assets}
                  filteredAssets={filteredAssets}
                  selectedAssets={selectedAssets}
                  onSelectAsset={handleSelectAsset}
                  onSelectAll={handleSelectAll}
                  searchTerm={filters.searchTerm}
                  onSearchChange={(value) => updateFilter('searchTerm', value)}
                  selectedEnvironment={filters.selectedEnvironment}
                  onEnvironmentChange={(value) => updateFilter('selectedEnvironment', value)}
                  uniqueEnvironments={uniqueEnvironments}
                  showAdvancedFilters={filters.showAdvancedFilters}
                  onToggleAdvancedFilters={() => updateFilter('showAdvancedFilters', !filters.showAdvancedFilters)}
                  onExport={handleExportAssets}
                  currentPage={currentPage}
                  recordsPerPage={RECORDS_PER_PAGE}
                  onPageChange={setCurrentPage}
                  selectedColumns={selectedColumns}
                  allColumns={allColumns}
                  onToggleColumn={toggleColumn}
                  onReclassifySelected={handleReclassifySelectedWrapper}
                  isReclassifying={isReclassifying}
                  onProcessForAssessment={handleProcessForAssessment}
                  isApplicationsSelected={isApplicationsSelected}
                />
              </div>
            )}
          </TabsContent>

          <TabsContent value="inventory">
            <AssetTable
              assets={assets}
              filteredAssets={filteredAssets}
              selectedAssets={selectedAssets}
              onSelectAsset={handleSelectAsset}
              onSelectAll={handleSelectAll}
              searchTerm={filters.searchTerm}
              onSearchChange={(value) => updateFilter('searchTerm', value)}
              selectedEnvironment={filters.selectedEnvironment}
              onEnvironmentChange={(value) => updateFilter('selectedEnvironment', value)}
              uniqueEnvironments={uniqueEnvironments}
              showAdvancedFilters={filters.showAdvancedFilters}
              onToggleAdvancedFilters={() => updateFilter('showAdvancedFilters', !filters.showAdvancedFilters)}
              onExport={handleExportAssets}
              currentPage={currentPage}
              recordsPerPage={RECORDS_PER_PAGE}
              onPageChange={setCurrentPage}
              selectedColumns={selectedColumns}
              allColumns={allColumns}
              onToggleColumn={toggleColumn}
              onReclassifySelected={handleReclassifySelectedWrapper}
              isReclassifying={isReclassifying}
              onProcessForAssessment={handleProcessForAssessment}
              isApplicationsSelected={isApplicationsSelected}
            />
          </TabsContent>

          <TabsContent value="insights">
            <EnhancedInventoryInsights flowId={flowId} />
          </TabsContent>
        </Tabs>
      )}

      {/* Application Selection Modal */}
      {showApplicationModal && (
        <ApplicationSelectionModal
          isOpen={showApplicationModal}
          onClose={() => setShowApplicationModal(false)}
          flowId={flowId}
          preSelectedApplicationIds={selectedApplicationIds}
          existingCollectionFlowId={new URLSearchParams(window.location.search).get('collectionFlowId') || undefined}
        />
      )}
    </div>
  );
};

export default InventoryContent;
