import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { InventoryContentFallback } from '../InventoryContentFallback';

interface LoadingStateProps {
  isExecutingPhase: boolean;
  viewMode: 'all' | 'current_flow';
}

export const LoadingState: React.FC<LoadingStateProps> = ({ isExecutingPhase, viewMode }) => {
  return (
    <>
      <div className="animate-pulse">
        <div className="h-32 bg-gray-200 rounded mb-4"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
      {isExecutingPhase && (
        <div className="text-center text-gray-600 mt-4">
          <p className="font-medium">Processing asset inventory...</p>
          <p className="text-sm mt-2">The AI agents are analyzing and classifying your assets.</p>
          <p className="text-sm">This process may take up to 6 minutes for large inventories.</p>
          <p className="text-sm mt-1 text-blue-600">
            View Mode: {viewMode === 'all' ? 'All Assets' : 'Current Flow Only'}
          </p>
          <div className="mt-4">
            <div className="inline-flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-sm text-gray-500">Processing in background...</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

interface ErrorStateProps {
  viewMode: 'all' | 'current_flow';
  refetchAssets: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ viewMode, refetchAssets }) => {
  return (
    <InventoryContentFallback
      error={`Backend service is temporarily unavailable. Please try again in a few moments. (View Mode: ${viewMode === 'all' ? 'All Assets' : 'Current Flow Only'})`}
      onRetry={() => refetchAssets()}
    />
  );
};

interface EmptyStateProps {
  flow: {
    raw_data?: unknown[];
    phases_completed?: string[];
    phase_completion?: { data_cleansing?: boolean; inventory?: boolean };
    current_phase?: string;
    status?: string;
    phase_state?: { conflict_resolution_pending?: boolean };
  } | null;
  viewMode: 'all' | 'current_flow';
  isExecutingPhase: boolean;
  hasTriggeredInventory: boolean;
  executeFlowPhase: (phase: string, params: unknown) => Promise<void>;
  refetchAssets: () => void;
  refreshFlow: () => void;
  setHasTriggeredInventory: (value: boolean) => void;
  onOpenConflictModal?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  flow,
  viewMode,
  isExecutingPhase,
  hasTriggeredInventory,
  executeFlowPhase,
  refetchAssets,
  refreshFlow,
  setHasTriggeredInventory,
  onOpenConflictModal
}) => {
  // Memory leak prevention: Track if component is mounted
  const isMountedRef = React.useRef(true);

  React.useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Check if we need to execute the asset inventory phase
  // FIX #447: Support both phases_completed array and phase_completion object
  const dataCleansingDone =
    flow?.phases_completed?.includes('data_cleansing') ||
    flow?.phase_completion?.data_cleansing === true;
  const inventoryNotDone =
    !(flow?.phases_completed?.includes('asset_inventory') ||
      flow?.phase_completion?.inventory === true);

  const shouldExecuteInventoryPhase = flow &&
    dataCleansingDone &&
    inventoryNotDone &&
    flow.current_phase !== 'asset_inventory' &&
    !isExecutingPhase;

  // Check if flow is paused for conflict resolution (PR #567 fix)
  const hasConflictsPending = flow?.phase_state?.conflict_resolution_pending === true;

  // CC FIX: Check if flow is complete with inventory phase done but 0 assets
  // This happens when all conflicts were resolved as "keep_existing" - no new assets imported
  const inventoryDone =
    flow?.phases_completed?.includes('asset_inventory') ||
    flow?.phase_completion?.inventory === true ||
    (flow?.current_phase === 'asset_inventory' && flow?.status === 'completed');
  const isFlowComplete = flow?.status === 'completed';
  const hasCompletedWithZeroAssets = inventoryDone && isFlowComplete;

  // Check if inventory processing might be starting soon
  // FIX: Don't show "Preparing" if conflicts are pending - user needs to resolve them first
  // FIX: Don't show "Preparing" if inventory is already complete (even with 0 assets)
  const mightStartProcessing = flow && flow.raw_data && flow.raw_data.length > 0 && !hasTriggeredInventory && !hasConflictsPending && !hasCompletedWithZeroAssets;

  return (
    <Card>
      <CardContent className="p-8">
        <div className="text-center">
          {hasConflictsPending ? (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Conflict Resolution Required</h3>
              <p className="text-gray-600 mb-4">
                The asset inventory phase detected duplicate assets and is paused waiting for your decision.
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Please resolve the conflicts using the banner above to continue. Once resolved, assets will be created automatically.
              </p>
              <div className="inline-flex items-center mb-4">
                <div className="rounded-full h-3 w-3 bg-yellow-600 mr-2"></div>
                <span className="text-sm text-gray-500">Flow paused for conflict resolution</span>
              </div>
              {onOpenConflictModal && (
                <div className="mt-4">
                  <Button
                    onClick={onOpenConflictModal}
                    className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    Open Conflict Resolution
                  </Button>
                </div>
              )}
            </>
          ) : mightStartProcessing ? (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Preparing Asset Inventory</h3>
              <p className="text-gray-600 mb-4">
                The system is preparing to process your asset inventory.
              </p>
              <p className="text-sm text-gray-500 mb-4">
                Processing will begin automatically in a moment...
              </p>
              <div className="inline-flex items-center mb-4">
                <div className="animate-pulse rounded-full h-3 w-3 bg-blue-600 mr-2"></div>
                <span className="text-sm text-gray-500">Initializing...</span>
              </div>
              {/* FIX #447: Manual bypass button when auto-execution is blocked */}
              {!dataCleansingDone && (
                <div className="mt-4">
                  <p className="text-sm text-amber-600 mb-3">
                    Auto-execution is waiting for data cleansing to complete. You can manually start the process:
                  </p>
                  <Button
                    onClick={async () => {
                      try {
                        console.log('📦 Manual execution of asset inventory phase...');
                        setHasTriggeredInventory(true);
                        await executeFlowPhase('asset_inventory', {
                          trigger: 'manual_bypass',
                          source: 'inventory_page_manual_bypass'
                        });
                        setTimeout(() => {
                          if (isMountedRef.current) {
                            refetchAssets();
                            refreshFlow();
                          }
                        }, 2000);
                      } catch (error) {
                        console.error('Failed to manually execute asset inventory:', error);
                        setHasTriggeredInventory(false);
                      }
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isExecutingPhase}
                  >
                    Run Asset Inventory Manually
                  </Button>
                </div>
              )}
            </>
          ) : hasCompletedWithZeroAssets ? (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No New Assets Imported</h3>
              <p className="text-gray-600 mb-4">
                The asset inventory phase completed successfully, but no new assets were created for this flow.
              </p>
              <p className="text-sm text-gray-500 mb-2">
                This typically happens when all detected items were duplicates of existing assets, and you chose to keep the existing records.
              </p>
              <p className="text-sm text-blue-600">
                💡 Switch to "All Assets" view mode to see all existing assets across all flows.
              </p>
            </>
          ) : (
            <>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Assets Found</h3>
              <p className="text-gray-600 mb-4">
                {viewMode === 'current_flow' && flow ?
                  "The asset inventory will be populated once the inventory phase is executed for this flow." :
                  viewMode === 'current_flow' && !flow ?
                  "No flow is selected or the flow has no assets yet." :
                  "No assets have been discovered yet for this client and engagement."
                }
              </p>
              <p className="text-sm text-gray-500">
                {viewMode === 'all'
                  ? "Assets are created during discovery flows or can be imported directly. Try switching to 'All Assets' mode to see assets from other flows."
                  : "Assets are created during the discovery flow process or can be imported directly. Try switching to 'All Assets' mode to see all available assets."
                }
              </p>
              {shouldExecuteInventoryPhase && (
                <div className="mt-6">
                  <p className="text-sm text-gray-600 mb-4">
                    Data cleansing is complete. Click below to create the asset inventory.
                  </p>
                  <Button
                    onClick={async () => {
                      try {
                        console.log('📦 Executing asset inventory phase...');
                        await executeFlowPhase('asset_inventory', {
                          trigger: 'user_initiated',
                          source: 'inventory_page'
                        });
                        // Refetch assets after execution
                        setTimeout(() => {
                          if (isMountedRef.current) {
                            refetchAssets();
                            refreshFlow();
                          }
                        }, 2000);
                      } catch (error) {
                        console.error('Failed to execute asset inventory phase:', error);
                      }
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isExecutingPhase}
                  >
                    Create Asset Inventory
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

interface InvalidFlowStateProps {
  flowId?: string;
}

export const InvalidFlowState: React.FC<InvalidFlowStateProps> = ({ flowId }) => {
  const navigate = useNavigate();

  return (
    <Card>
      <CardContent className="p-8">
        <div className="text-center">
          <div className="mb-4">
            <svg
              className="mx-auto h-12 w-12 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Invalid Discovery Flow</h3>
          <p className="text-gray-600 mb-4">
            The flow ID in the URL does not exist or you don't have access to it.
          </p>
          {flowId && (
            <p className="text-sm text-gray-500 mb-4 font-mono bg-gray-100 p-2 rounded">
              Flow ID: {flowId}
            </p>
          )}
          <p className="text-sm text-gray-500 mb-6">
            This flow may have been deleted, or the ID may be incorrect. Please return to the dashboard to select a valid flow.
          </p>
          <Button
            onClick={() => navigate('/discovery/dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Go to Dashboard
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
