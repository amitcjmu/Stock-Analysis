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
    if (effectiveFlowId && !showPreviewModal) {
      // Small delay to ensure UI is ready
      const timer = setTimeout(() => {
        setShowPreviewModal(true);
      }, 500);
      return () => clearTimeout(timer);
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

  // CRITICAL FIX FOR ISSUE #306: Only render when Flow ID is available
  // This prevents the race condition where API calls fire before Flow ID is set
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

  if (!hasEffectiveFlow) {
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
            <div className="flex items-center justify-center min-h-96">
              <div className="text-center max-w-md">
                <div className="mb-4">
                  <div className="mx-auto h-12 w-12 rounded-full bg-yellow-100 flex items-center justify-center">
                    <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">No Active Discovery Flow</h2>
                <p className="text-gray-600 mb-4">
                  The Asset Inventory requires an active discovery flow context. Please ensure you have:
                </p>
                <ul className="text-left text-sm text-gray-600 space-y-1 mb-4">
                  <li>• Started a discovery flow from Data Import</li>
                  <li>• Completed the Data Cleansing phase</li>
                  <li>• Navigated from the discovery workflow</li>
                </ul>
                <p className="text-sm text-gray-500">
                  Available flows: {flowList?.length || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
              {/* Main Inventory Content - now self-contained */}
              <InventoryContent className="" flowId={effectiveFlowId} />
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
