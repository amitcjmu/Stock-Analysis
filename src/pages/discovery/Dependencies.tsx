import React from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { RefreshCw, Zap, Building2 } from 'lucide-react';

// Components
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
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

const Dependencies: React.FC = () => {
  const { client, engagement } = useAuth();

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
    canContinueToNextPhase
  } = useDependencyLogic(effectiveFlowId);

  // Use navigation hook - following the established pattern
  const { handleContinueToNextPhase } = useDependencyNavigation(null, dependencyData);

  // Debug info for flow detection
  console.log('🔍 Dependencies flow detection:', {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    totalFlowsAvailable: flowList?.length || 0
  });

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
            <div className="flex items-center justify-center py-8">
              <Building2 className="w-6 h-6 animate-pulse text-blue-500 mr-2" />
              <span className="text-gray-600">Please select a client and engagement to continue...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

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

          {/* Header - Following the established pattern */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Dependency Analysis</h1>
                <p className="text-gray-600">
                  {client.name} - {engagement.name}
                </p>
                <p className="text-gray-600 mt-1">
                  AI-powered dependency mapping and relationship analysis
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                variant="outline"
                size="sm"
                onClick={analyzeDependencies}
                disabled={isAnalyzing || !client || !engagement}
              >
                {isAnalyzing ? (
                  <><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Analyzing...</>
                ) : (
                  <><Zap className="mr-2 h-4 w-4" />Analyze Dependencies</>
                )}
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3 space-y-6">
              <DependencyProgress data={dependencyData} isLoading={isLoading} />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DependencyAnalysisPanel data={dependencyData} isLoading={isLoading} activeView={activeView} />
                <DependencyMappingPanel data={dependencyData} activeView={activeView} onCreateDependency={() => {}} />
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
