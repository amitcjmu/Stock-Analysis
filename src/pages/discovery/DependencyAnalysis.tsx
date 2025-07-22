import React from 'react';
import Sidebar from '../../components/Sidebar';
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import { useUnifiedDiscoveryFlow } from '../../hooks/useUnifiedDiscoveryFlow';
import { useDependencyFlowDetection } from '../../hooks/discovery/useDiscoveryFlowAutoDetection';
import { useDependencyLogic } from '../../hooks/discovery/useDependencyLogic';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { 
  Network, 
  Server, 
  Database, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  RefreshCw,
  Play
} from 'lucide-react';

const DependencyAnalysisPage = () => {
  // Use the new auto-detection hook for consistent flow detection
  const {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    flowList,
    isFlowListLoading,
    hasEffectiveFlow
  } = useDependencyFlowDetection();
  
  // V2 Discovery flow hook - pass effectiveFlowId instead of urlFlowId
  const {
    flowState: flow,
    isLoading,
    error,
    executeFlowPhase: updatePhase,
    isExecutingPhase: isUpdating,
    refreshFlow: refresh,
    isPhaseComplete
  } = useUnifiedDiscoveryFlow(effectiveFlowId);
  
  // Extract flow details
  const progressPercentage = flow?.progress_percentage || 0;
  const currentPhase = flow?.current_phase || '';
  const completedPhases = flow?.phase_completion ? 
    Object.entries(flow.phase_completion)
      .filter(([_, completed]) => completed)
      .map(([phase, _]) => phase) : [];
  const nextPhase = currentPhase === 'dependencies' ? 'tech_debt' : '';

  // Use dependency logic hook for dependency-specific functionality
  const {
    dependencyData,
    isAnalyzing,
    analyzeDependencies,
    activeView,
    setActiveView,
    canContinueToNextPhase
  } = useDependencyLogic(effectiveFlowId);

  // Debug info for flow detection
  console.log('🔍 Dependency flow detection:', {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    hasEffectiveFlow,
    totalFlowsAvailable: flowList?.length || 0
  });

  // Get dependency analysis specific data from V2 flow - extract from flow state
  const isDependencyAnalysisComplete = completedPhases.includes('dependency_analysis') || completedPhases.includes('dependencies_completed');
  
  // Handle dependency analysis execution
  const handleExecuteDependencyAnalysis = async () => {
    try {
      await analyzeDependencies();
    } catch (error) {
      console.error('Failed to execute dependency analysis phase:', error);
    }
  };

  // Navigation handlers
  const handleBackToInventory = () => {
    window.history.back();
  };

  const handleContinueToTechDebt = () => {
    window.location.href = '/discovery/tech-debt';
  };

  // Extract dependency information from dependencyData
  const appServerDependencies = dependencyData?.app_server_mapping || [];
  const appAppDependencies = dependencyData?.cross_application_mapping || [];
  const dependencyRelationships = dependencyData?.dependency_relationships || [];
  const criticalDependencies = dependencyData?.critical_dependencies || [];

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
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dependency Analysis</h1>
              <p className="text-gray-600 mt-1">
                Analyze application and server dependencies to understand migration complexity
              </p>
            </div>
            <div className="flex space-x-2 mt-4 md:mt-0">
              <Button
                variant="outline"
                size="sm"
                onClick={refresh}
                disabled={isLoading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              {!isDependencyAnalysisComplete && (
                <Button
                  onClick={handleExecuteDependencyAnalysis}
                  disabled={isAnalyzing}
                >
                  <Play className="mr-2 h-4 w-4" />
                  {isAnalyzing ? 'Analyzing...' : 'Start Analysis'}
                </Button>
              )}
            </div>
          </div>

          {/* Status Card */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Network className="mr-2 h-5 w-5" />
                Analysis Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-4">
                {isDependencyAnalysisComplete ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-green-700">Dependency analysis completed</span>
                    <Badge variant="secondary">Complete</Badge>
                  </>
                ) : isAnalyzing ? (
                  <>
                    <Clock className="h-5 w-5 text-yellow-500 animate-pulse" />
                    <span className="text-yellow-700">Analysis in progress...</span>
                    <Badge variant="secondary">Running</Badge>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-5 w-5 text-gray-500" />
                    <span className="text-gray-700">Ready to start dependency analysis</span>
                    <Badge variant="outline">Pending</Badge>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Error State */}
          {error && (
            <Card className="mb-6 border-red-200">
              <CardContent className="pt-6">
                <div className="flex items-center text-red-700">
                  <AlertCircle className="mr-2 h-5 w-5" />
                  <span>Error: {error.message}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {isDependencyAnalysisComplete && dependencyData && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* App-Server Dependencies */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Server className="mr-2 h-5 w-5" />
                    Application-Server Dependencies
                  </CardTitle>
                  <CardDescription>
                    Hosting relationships and resource mappings
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appServerDependencies.length > 0 ? (
                    <div className="space-y-3">
                      {appServerDependencies.slice(0, 5).map((relationship: unknown, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium">{relationship.application || `App ${index + 1}`}</p>
                            <p className="text-sm text-gray-600">{relationship.server || `Server ${index + 1}`}</p>
                          </div>
                          <ArrowRight className="h-4 w-4 text-gray-400" />
                        </div>
                      ))}
                      {appServerDependencies.length > 5 && (
                        <p className="text-sm text-gray-600">
                          +{appServerDependencies.length - 5} more relationships
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-600">No hosting relationships found</p>
                  )}
                </CardContent>
              </Card>

              {/* App-App Dependencies */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Database className="mr-2 h-5 w-5" />
                    Application-Application Dependencies
                  </CardTitle>
                  <CardDescription>
                    Communication patterns and API dependencies
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appAppDependencies.length > 0 ? (
                    <div className="space-y-3">
                      {appAppDependencies.slice(0, 5).map((pattern: unknown, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium">{pattern.source || `Source ${index + 1}`}</p>
                            <p className="text-sm text-gray-600">{pattern.target || `Target ${index + 1}`}</p>
                          </div>
                          <Badge variant="outline">{pattern.type || 'API'}</Badge>
                        </div>
                      ))}
                      {appAppDependencies.length > 5 && (
                        <p className="text-sm text-gray-600">
                          +{appAppDependencies.length - 5} more patterns
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-gray-600">No communication patterns found</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handleBackToInventory}
            >
              Back to Asset Inventory
            </Button>
            
            {isDependencyAnalysisComplete && (
              <Button
                onClick={handleContinueToTechDebt}
                disabled={!canContinueToNextPhase()}
              >
                Continue to Tech Debt Analysis
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DependencyAnalysisPage; 