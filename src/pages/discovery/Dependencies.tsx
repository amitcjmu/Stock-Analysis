import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { RefreshCw, Zap, Building2, AlertTriangle, ArrowRight } from 'lucide-react';

// Components
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import ContextSelector from '../../components/context/ContextSelector';
import DependencyProgress from '../../components/discovery/dependencies/DependencyProgress';
import DependencyAnalysisPanel from '../../components/discovery/dependencies/DependencyAnalysisPanel';
import { DependencyGraph } from '../../components/discovery/dependencies/DependencyGraph';
import DependencyMappingPanel from '../../components/discovery/dependencies/DependencyMappingPanel';
import AgentUIMonitor from '../../components/discovery/dependencies/AgentUIMonitor';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightPanel from '../../components/discovery/AgentInsightPanel';
import Sidebar from '../../components/Sidebar';

// Hooks - Follow the established pattern
import { useDependencyLogic } from '../../hooks/discovery/useDependencyLogic';
import { useDependencyNavigation } from '../../hooks/discovery/useDependencyNavigation';
import { useDependenciesFlowDetection } from '../../hooks/discovery/useDiscoveryFlowAutoDetection';
import { useAuth } from '../../contexts/AuthContext';

// Services
import { createDependency, findAssetIdByName, type DependencyCreate } from '../../services/dependencyService';
import { toast } from '@/components/ui/use-toast';

const Dependencies: React.FC = () => {
  const { client, engagement } = useAuth();
  const navigate = useNavigate();

  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    hasEffectiveFlow
  } = useDependenciesFlowDetection();

  // Use dependency logic hook - pass effectiveFlowId instead of urlFlowId
  const {
    dependencyData,
    isLoading,
    error,
    isAnalyzing,
    analyzeDependencies,
    activeView,
    setActiveView,
    canContinueToNextPhase,
    // CRITICAL: New phase progression logic
    canAccessDependencyPhase,
    prerequisitePhases,
    isDependencyAnalysisComplete,
    inventoryData,
    flowState,
    refreshDependencies
  } = useDependencyLogic(effectiveFlowId);

  // Use navigation hook - following the established pattern
  const { handleContinueToNextPhase } = useDependencyNavigation(null, dependencyData);

  // Debug info for flow detection - removed to prevent console spam

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 py-6 max-w-7xl flex items-center justify-center">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
            <span className="text-gray-600">Loading Dependency Data...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 py-6 max-w-7xl">
            <div className="text-red-500">Error: {error.message}</div>
          </div>
        </div>
      </div>
    );
  }

  if (!client || !engagement) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 py-6 max-w-7xl">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Dependencies Analysis</h1>
              <p className="text-gray-600">Select a client and engagement to analyze application dependencies.</p>
            </div>

            <div className="max-w-2xl mx-auto">
              <ContextSelector
                onSelectionChange={() => {
                  // Refresh data after context change
                  refreshDependencies?.();
                }}
              />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // REMOVED: Restrictive prerequisites check - allow access to Dependencies page always
  // The page will provide guidance without blocking access

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

          {/* Header - Enhanced with inventory information and phase guidance */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Dependency Analysis</h1>
                <p className="text-gray-600">
                  {client.name} - {engagement.name}
                </p>
                <div className="flex items-center space-x-4 mt-2">
                  <p className="text-sm text-gray-600">
                    AI-powered dependency mapping and relationship analysis
                  </p>

                  {/* Show current status - informational, not blocking */}
                  {inventoryData.totalAssets > 0 ? (
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {inventoryData.totalAssets} Assets Available
                      </span>
                      <span className="text-xs text-gray-500">
                        {inventoryData.servers.length} Servers, {inventoryData.applications.length} Apps, {inventoryData.databases.length} DBs
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Limited Data Available
                      </span>
                      <Button
                        variant="link"
                        size="sm"
                        className="text-xs p-0 h-auto"
                        onClick={() => navigate('/discovery/inventory')}
                      >
                        Complete Asset Inventory →
                      </Button>
                    </div>
                  )}

                  {/* Show discovery progress without blocking */}
                  {prerequisitePhases.length > 0 && (
                    <div className="flex items-center space-x-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Enhanced analysis available
                      </span>
                      <Button
                        variant="link"
                        size="sm"
                        className="text-xs p-0 h-auto"
                        onClick={() => {
                          const nextPhase = prerequisitePhases[0];
                          const routes = {
                            'data_import': '/discovery/cmdb-import',
                            'field_mapping': '/discovery/attribute-mapping',
                            'data_cleansing': '/discovery/data-cleansing',
                            'asset_inventory': '/discovery/inventory'
                          };
                          navigate(routes[nextPhase] || '/discovery');
                        }}
                      >
                        Complete {prerequisitePhases.length} more phases →
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  if (isAnalyzing) return;
                  try {
                    await analyzeDependencies();
                  } finally {
                    await refreshDependencies();
                  }
                }}
                disabled={isAnalyzing || !client || !engagement}
              >
                {isAnalyzing ? (
                  <><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Analyzing Dependencies...</>
                ) : (
                  <><Zap className="mr-2 h-4 w-4" />
                    {isDependencyAnalysisComplete ? 'Re-analyze Dependencies' :
                     inventoryData.totalAssets > 0 ? 'Start Dependency Analysis' : 'Start Discovery'}
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Always show dependency analysis section */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <div className="flex items-center mb-4">
              <Building2 className="w-6 h-6 text-blue-600 mr-3" />
              <h3 className="text-lg font-semibold text-blue-800">
                {inventoryData.totalAssets > 0 ? 'Ready for Dependency Analysis' : 'Dependency Analysis'}
              </h3>
            </div>
            <p className="text-blue-700 mb-4">
              {inventoryData.totalAssets > 0
                ? `You have ${inventoryData.totalAssets} assets in your inventory. Click "Start Dependency Analysis" to discover relationships between your applications and servers, or manually create dependencies using the mapping panel below.`
                : 'Start dependency analysis to discover relationships between your applications and servers. You can also manually create dependencies using the mapping panel below.'
              }
            </p>
            <div className="flex items-center space-x-3">
              <Button
                onClick={async () => { await analyzeDependencies(); await refreshDependencies(); }}
                disabled={isAnalyzing}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isAnalyzing ? (
                  <><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Analyzing Dependencies...</>
                ) : (
                  <><Zap className="mr-2 h-4 w-4" />Start Dependency Analysis</>
                )}
              </Button>
              <span className="text-sm text-blue-600">
                Or create dependencies manually below ↓
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              <DependencyProgress data={dependencyData} isLoading={isLoading} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DependencyAnalysisPanel data={dependencyData} isLoading={isLoading} activeView={activeView} />
                <DependencyMappingPanel
                  data={dependencyData}
                  activeView={activeView}
                  onCreateDependency={async (dependency: DependencyCreate) => {
                    console.log('Creating dependency:', dependency);

                    try {
                      let sourceId: string | null = null;
                      let targetId: string | null = null;
                      let isAppToApp = false;

                      const availableApps = dependencyData.available_applications || [];
                      const availableServers = dependencyData.available_servers || [];

                      if (activeView === 'app-server') {
                        // App to Server dependency
                        sourceId = findAssetIdByName(dependency.application_name, availableApps);
                        targetId = findAssetIdByName(dependency.server_name, availableServers);
                        isAppToApp = false;
                      } else {
                        // App to App dependency
                        sourceId = findAssetIdByName(dependency.source_app, availableApps);
                        targetId = findAssetIdByName(dependency.target_app, availableApps);
                        isAppToApp = true;
                      }

                      if (!sourceId || !targetId) {
                        toast({
                          title: "Error",
                          description: "Unable to find asset IDs for the selected items",
                          variant: "destructive",
                        });
                        return;
                      }

                      const result = await createDependency({
                        source_id: sourceId,
                        target_id: targetId,
                        dependency_type: dependency.dependency_type || 'runtime',
                        is_app_to_app: isAppToApp,
                        description: dependency.description
                      });

                      toast({
                        title: "Success",
                        description: "Dependency created successfully",
                      });

                      // Refresh the dependency data
                      await refreshDependencies();
                    } catch (error: unknown) {
                      console.error('Error creating dependency:', error);
                      toast({
                        title: "Error",
                        description: error instanceof Error ? error.message : "Failed to create dependency",
                        variant: "destructive",
                      });
                    }
                  }}
                />
              </div>
              <DependencyGraph data={dependencyData} activeView={activeView} onUpdateDependency={() => {}} />

              {/* Navigation Button - Following the established pattern */}
              {canContinueToNextPhase() && (
                <div className="flex justify-end">
                  <Button
                    onClick={() => handleContinueToNextPhase()}
                    className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
                  >
                    <span>Continue to Next Phase</span>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </div>

            <div className="xl:col-span-1 space-y-6">
              <AgentUIMonitor
                pageContext="dependencies"
                className="h-fit"
                onDependencyCreated={refreshDependencies}
              />
              <DataClassificationDisplay
                pageContext="dependency-analysis"
                refreshTrigger={0}
                onClassificationUpdate={(itemId, newClassification) => {
                  console.log('Dependency classification updated:', itemId, newClassification);
                  analyzeDependencies();
                }}
              />
              <AgentInsightPanel
                pageContext="dependency-analysis"
                refreshTrigger={0}
                onInsightAction={(insightId, action) => {
                  console.log('Dependency insight action:', insightId, action);
                  if (action === 'apply_insight') {
                    analyzeDependencies();
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dependencies;
