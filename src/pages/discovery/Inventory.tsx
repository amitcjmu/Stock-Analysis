import type React from 'react';
import { useState, useEffect } from 'react';

import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import AgentPlanningDashboard from '../../components/discovery/AgentPlanningDashboard';
import InventoryContent from '../../components/discovery/inventory/InventoryContent';
import { AssetCreationPreviewModal } from '../../components/discovery/AssetCreationPreviewModal';
import { useInventoryFlowDetection } from '../../hooks/discovery/useDiscoveryFlowAutoDetection';
import { useAuth } from '@/contexts/AuthContext';

const Inventory = (): JSX.Element => {
  const { client, engagement } = useAuth();

  // Asset preview state (Issue #907)
  const [showPreviewModal, setShowPreviewModal] = useState(false);

  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    hasEffectiveFlow
  } = useInventoryFlowDetection();

  // Auto-show preview modal on mount if flow is available (Issue #907)
  useEffect(() => {
    console.log('🔍 Auto-open modal useEffect triggered:', {
      effectiveFlowId,
      showPreviewModal,
      willAttemptOpen: !!effectiveFlowId && !showPreviewModal
    });

    if (effectiveFlowId && !showPreviewModal) {
      console.log('✅ Scheduling modal open in 500ms for flow:', effectiveFlowId);

      // Small delay to ensure UI is ready
      const timer = setTimeout(() => {
        console.log('🚀 Opening preview modal now for flow:', effectiveFlowId);
        setShowPreviewModal(true);
      }, 500);

      return () => {
        console.log('🧹 Cleaning up modal timer');
        clearTimeout(timer);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveFlowId]); // Only trigger on effectiveFlowId availability, intentionally excluding showPreviewModal

  // Debug info for flow detection
  console.log('🔍 Inventory flow detection:', {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    totalFlowsAvailable: flowList?.length || 0
  });

  // Show loading state while detecting flows
  if (isFlowListLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Discovery Flows</h2>
            <p className="text-gray-600">Detecting active discovery flow...</p>
          </div>
        </div>
      </div>
    );
  }

  // Note: Removed blocking "No Active Discovery Flow" state
  // Inventory now supports viewing all assets without a flow context

  return (
    <>
      {/* Asset Creation Preview Modal (Issue #907) */}
      {effectiveFlowId && (
        <AssetCreationPreviewModal
          flow_id={effectiveFlowId}
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          onSuccess={() => {
            setShowPreviewModal(false);
            // Inventory will auto-refresh to show newly created assets
          }}
        />
      )}

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
                  Comprehensive inventory of discovered IT assets with AI-powered classification
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              {/* Main Inventory Content - supports optional flowId for "Show All Assets" feature */}
              <InventoryContent className="" flowId={effectiveFlowId || undefined} />
            </div>

            <div className="xl:col-span-1 space-y-6">
              {/* Agent Communication Panel */}
              <AgentClarificationPanel
                pageContext="asset-inventory"
                refreshTrigger={0}
                onQuestionAnswered={(questionId, response) => {
                  console.log('Inventory question answered:', questionId, response);
                }}
              />

              {/* Agent Insights */}
              <AgentInsightsSection
                pageContext="asset-inventory"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Inventory insight action:', insightId, action);
                }}
              />

              {/* Agent Planning Dashboard */}
              <AgentPlanningDashboard pageContext="asset-inventory" />
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  );
};

export default Inventory;
