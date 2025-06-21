import React, { useState } from 'react';
import { Button } from '../../components/ui/button';
import { RefreshCw, Zap, ArrowRight, AlertTriangle, ArrowLeft, Upload } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useNavigate, useParams } from 'react-router-dom';

// Components
import ContextBreadcrumbs from '../../components/context/ContextBreadcrumbs';
import ProgressDashboard from '../../components/discovery/attribute-mapping/ProgressDashboard';
import CrewAnalysisPanel from '../../components/discovery/attribute-mapping/CrewAnalysisPanel';
import NavigationTabs from '../../components/discovery/attribute-mapping/NavigationTabs';
import AttributeMappingTabContent from '../../components/discovery/attribute-mapping/AttributeMappingTabContent';
import AttributeMappingStateProvider from '../../components/discovery/attribute-mapping/AttributeMappingStateProvider';
import AgentClarificationPanel from '../../components/discovery/AgentClarificationPanel';
import DataClassificationDisplay from '../../components/discovery/DataClassificationDisplay';
import AgentInsightsSection from '../../components/discovery/AgentInsightsSection';
import EnhancedAgentOrchestrationPanel from '../../components/discovery/EnhancedAgentOrchestrationPanel';
import Sidebar from '../../components/Sidebar';

// Hooks
import { useAttributeMappingLogic } from '../../hooks/discovery/useAttributeMappingLogic';
import { useAttributeMappingNavigation } from '../../hooks/discovery/useAttributeMappingNavigation';

const AttributeMapping: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'mappings' | 'data' | 'critical'>('critical');
  const navigate = useNavigate();
  const { sessionId: urlSessionId } = useParams<{ sessionId?: string }>();

  // Custom hooks for business logic
  const {
    agenticData,
    fieldMappings,
    crewAnalysis,
    mappingProgress,
    criticalAttributes,
    flowState,
    sessionId,
    flowId,
    availableDataImports,
    selectedDataImportId,
    isAgenticLoading,
    isFlowStateLoading,
    isAnalyzing,
    agenticError,
    flowStateError,
    handleTriggerFieldMappingCrew,
    handleApproveMapping,
    handleRejectMapping,
    handleAttributeUpdate,
    handleDataImportSelection,
    refetchAgentic,
    canContinueToDataCleansing,
  } = useAttributeMappingLogic(urlSessionId);

  // Navigation logic
  const { handleContinueToDataCleansing } = useAttributeMappingNavigation(
    flowState,
    mappingProgress
  );

  // Determine state conditions
  const isLoading = (isFlowStateLoading && !flowState) || isAgenticLoading;
  const hasError = !!(flowStateError || agenticError);
  const errorMessage = flowStateError?.message || agenticError?.message;
  const hasData = !!(agenticData?.attributes?.length);

  // 🔧 SESSION AND FLOW DISPLAY
  const sessionInfo = {
    sessionId,
    flowId,
    availableDataImports,
    selectedDataImportId,
    hasMultipleSessions: availableDataImports.length > 1
  };

  // Check if we have session data - if not, show redirect message
  const hasSessionData = sessionId || flowState;
  const hasUploadedData = agenticData?.attributes && agenticData.attributes.length > 0;

  return (
    <AttributeMappingStateProvider
      isLoading={isLoading}
      hasError={hasError}
      errorMessage={errorMessage}
      hasData={hasData}
      onTriggerAnalysis={handleTriggerFieldMappingCrew}
      isAnalyzing={isAnalyzing}
    >
      <div className="flex min-h-screen bg-gray-50">
        <div className="hidden lg:block w-64 border-r bg-white">
          <Sidebar />
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8 max-w-7xl">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Attribute Mapping</h1>
              <p className="text-gray-600">Map your data fields to standard migration attributes and verify data quality.</p>
            </div>

            {/* Show redirect message if showing old data */}
            {!sessionId && (
              <Alert className="mb-6 border-blue-200 bg-blue-50">
                <Upload className="h-5 w-5 text-blue-600" />
                <AlertDescription className="text-blue-800">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium mb-2">No Current Data Upload Session</p>
                      <p className="text-sm">
                        To start the discovery flow with new data, please begin by uploading your CMDB file on the Data Import page. 
                        The data shown below is from a previous upload session.
                      </p>
                    </div>
                    <Button 
                      onClick={() => navigate('/discovery/cmdb-import')}
                      className="ml-4 bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      <span>Start Data Upload</span>
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Session Information Panel */}
            {sessionId && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Current Session</h3>
                    <p className="text-xs text-gray-600 font-mono">{sessionId}</p>
                    {flowState && (
                      <p className="text-xs text-green-600 mt-1">✅ Discovery flow data available</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Last updated</p>
                    <p className="text-xs text-gray-900">Session active</p>
                  </div>
                </div>
              </div>
            )}

            <div className="mb-6">
              <ContextBreadcrumbs />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900">Field Mapping & Critical Attributes</h1>
                  <p className="text-gray-600">
                    {mappingProgress.total > 0 
                      ? `${mappingProgress.total} attributes analyzed with ${mappingProgress.mapped} mapped and ${mappingProgress.critical_mapped} migration-critical` 
                      : 'AI-powered field mapping and critical attribute identification'
                    }
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <Button
                  onClick={refetchAgentic}
                  disabled={isAgenticLoading}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  {isAgenticLoading ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  <span>Refresh Analysis</span>
                </Button>
                
                <Button
                  onClick={handleTriggerFieldMappingCrew}
                  disabled={isAnalyzing}
                  className="flex items-center space-x-2"
                >
                  {isAnalyzing ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Zap className="h-4 w-4" />
                  )}
                  <span>{isAnalyzing ? 'Analyzing...' : 'Trigger Field Mapping'}</span>
                </Button>
              </div>
            </div>

            <ProgressDashboard 
              progress={mappingProgress}
              isLoading={isAgenticLoading}
            />

            {flowState?.session_id && (
              <div className="mb-6">
                <EnhancedAgentOrchestrationPanel
                  sessionId={flowState.session_id}
                  flowState={flowState}
                />
              </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
              <div className="xl:col-span-3 space-y-6">
                <div className="bg-white rounded-lg shadow-md">
                  <NavigationTabs 
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                  />
                  
                  <AttributeMappingTabContent
                    activeTab={activeTab}
                    fieldMappings={fieldMappings}
                    criticalAttributes={criticalAttributes}
                    agenticData={agenticData}
                    onApproveMapping={handleApproveMapping}
                    onRejectMapping={handleRejectMapping}
                    refetchAgentic={() => refetchAgentic()}
                    onAttributeUpdate={handleAttributeUpdate}
                    sessionInfo={sessionInfo}
                  />
                </div>

                <CrewAnalysisPanel 
                  crewAnalysis={crewAnalysis}
                  isLoading={isAgenticLoading}
                />

                {/* Navigation Button */}
                {canContinueToDataCleansing() && (
                  <div className="flex justify-end">
                    <Button
                      onClick={handleContinueToDataCleansing}
                      className="flex items-center space-x-2 bg-green-600 hover:bg-green-700"
                    >
                      <span>Continue to Data Cleansing</span>
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>

              <div className="xl:col-span-1 space-y-6">
                <AgentClarificationPanel 
                  pageContext="field-mapping"
                  refreshTrigger={0}
                  onQuestionAnswered={(questionId, response) => {
                    console.log('Field mapping question answered:', questionId, response);
                    refetchAgentic();
                  }}
                />

                <DataClassificationDisplay 
                  pageContext="field-mapping"
                  refreshTrigger={0}
                  onClassificationUpdate={(itemId, newClassification) => {
                    console.log('Field mapping classification updated:', itemId, newClassification);
                    refetchAgentic();
                  }}
                />

                <AgentInsightsSection 
                  pageContext="field-mapping"
                  refreshTrigger={0}
                  onInsightAction={(insightId, action) => {
                    console.log('Field mapping insight action:', insightId, action);
                    if (action === 'apply_insight') {
                      refetchAgentic();
                    }
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </AttributeMappingStateProvider>
  );
};

export default AttributeMapping;
